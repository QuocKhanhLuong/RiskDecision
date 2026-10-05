"""Instrument the v2 correction without changing its optimization recipe."""
from local_market.models import Risk, entropy_solve, gmm_fit, filter_returns
import numpy as np
from threadpoolctl import threadpool_limits

METHODS = ["historical", "historical_se_penalty", "support_mix50",
           "support_band50", "support_point50", "random_band50", "filtered_historical"]


def prepare(z, cal, w):
    support = np.vstack([z, cal])
    p0 = np.r_[np.full(len(z), .5/len(z)), np.full(len(cal), .5/len(cal))]
    risk = Risk(support, w)
    eta, es = risk.eval(p0)
    h = np.maximum(risk.loss-eta, 0)
    hc = np.maximum(-cal @ w.T-eta, 0)
    b = hc.mean(0)
    se = hc.std(0, ddof=1)/np.sqrt(len(cal))
    floor = .025*np.maximum(np.std(-cal @ w.T, axis=0), .05)
    scale = np.maximum(se, floor)
    return {"risk": risk, "p0": p0, "eta": eta, "prior_es": es,
            "h": h, "b": b, "A": h/scale, "B": b/scale,
            "scale": scale, "floor_active": floor >= se}


def trace_correction(state, band=1., random_seed=None):
    """Exact frozen adaptive ordering or a fixed random 8-direction control."""
    rb, p0, A, B = (state[k] for k in ("risk", "p0", "A", "B"))
    p, selected, steps = p0.copy(), [], []
    order = None if random_seed is None else np.random.default_rng(random_seed).permutation(A.shape[1])
    for it in range(8):
        if order is not None:
            j = int(order[it])
        else:
            best = int(np.argmin(rb.eval(p)[1]))
            dis = np.maximum(np.abs(B-A.T @ p)-band, 0)
            if selected:
                dis[selected] = -np.inf
            j = best if it % 3 == 0 and best not in selected else int(np.argmax(dis))
        selected.append(j)
        p, diag = entropy_solve(A[:, selected], B[selected], p0, band)
        steps.append(diag)
    risks = rb.eval(p)
    before, after = np.abs(B-A.T @ p0), np.abs(B-A.T @ p)
    fixed_f = state["eta"]+(p @ state["h"])/.05
    diag = {"converged": all(s["converged"] for s in steps), "steps": steps,
            "directions": selected, "prior_all_within_band": bool(np.max(before) <= band),
            "prior_max_standardized_residual": float(np.max(before)),
            "prior_outside_band_n": int(np.sum(before > band)),
            "posterior_outside_band_n": int(np.sum(after > band)),
            "posterior_max_standardized_residual": float(np.max(after)),
            "tv_from_prior": float(np.abs(p-p0).sum()/2),
            "kl_from_prior": float(np.sum(p*np.log(np.maximum(p, 1e-300)/p0))),
            "ess": float(1/(p @ p)),
            "scale_floor_fraction": float(np.mean(state["floor_active"])),
            "max_abs_es_change": float(np.max(np.abs(risks[1]-state["prior_es"]))),
            "unchanged_surface": bool(np.max(np.abs(risks[1]-state["prior_es"])) <= 1e-10),
            "same_selection_as_mix": bool(np.argmin(risks[1]) == np.argmin(state["prior_es"])),
            "max_posterior_anchor_gap": float(np.max(fixed_f-risks[1]))}
    return risks, diag, p


def fit(x, w, seed):
    """Only training observations enter fitting. Truth/outcomes are separate."""
    if x.shape != (512, 8) or w.shape != (285, 8) or not np.isfinite(x).all():
        raise ValueError("Training/bank contract violated")
    with threadpool_limits(limits=1):
        hist = Risk(x, w).eval()
        z, base_diag = gmm_fit(x[:256], seed)
        state = prepare(z, x[256:], w)
        risks = {"historical": hist, "historical_se_penalty": hist,
                 "support_mix50": (state["eta"], state["prior_es"])}
        diagnostics, probabilities = {}, {"support_mix50": state["p0"]}
        for name, band, random_seed in [("support_band50", 1., None),
                                         ("support_point50", 0., None),
                                         ("random_band50", 1., seed+900000)]:
            risks[name], diagnostics[name], probabilities[name] = trace_correction(state, band, random_seed)
            diagnostics[name]["converged"] &= base_diag["converged"]
        res, vol = filter_returns(x)
        risks["filtered_historical"] = Risk(res*vol, w).eval()
        diagnostics["base_gmm"] = base_diag
        for name, (v, e) in risks.items():
            if not np.isfinite([v, e]).all() or np.any(e < v-1e-8):
                raise FloatingPointError("Invalid risk surface: "+name)
        se = (np.maximum(-x @ w.T-hist[0], 0)/.05).std(0, ddof=1)/np.sqrt(len(x))
        chosen = {name: int(np.argmin(risk[1])) for name, risk in risks.items()}
        chosen["historical_se_penalty"] = int(np.argmin(hist[1]+se))
    return risks, chosen, diagnostics, state, probabilities


def anchor_decomposition(state, p, estimated_es, reference_es, reference_hinge, j):
    """Reference may be empirical calibration or known synthetic population.

    Exact identity, NOT a confidence bound or proof that calibration generalizes.
    """
    eta, b = state["eta"][j], state["b"][j]
    predicted_hinge = float(p @ state["h"][:, j])
    terms = {"fitted_moment_residual": (predicted_hinge-b)/.05,
             "target_sampling_error": (b-reference_hinge)/.05,
             "reference_anchor_gap": eta+reference_hinge/.05-reference_es,
             "posterior_anchor_gap": eta+predicted_hinge/.05-estimated_es}
    terms["es_error"] = estimated_es-reference_es
    terms["identity_residual"] = terms["es_error"]-(terms["fitted_moment_residual"]+
        terms["target_sampling_error"]+terms["reference_anchor_gap"]-terms["posterior_anchor_gap"])
    return {k: float(v) for k, v in terms.items()}
