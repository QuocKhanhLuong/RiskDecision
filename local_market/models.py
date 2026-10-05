"""Frozen v2 recipes with observable solver diagnostics; training data only."""
from __future__ import annotations

import os
for _name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_name] = "1"

import sys
from pathlib import Path
import warnings
import numpy as np
from scipy.optimize import minimize, minimize_scalar
from scipy.special import logsumexp, gammaln
from scipy.stats import t as tdist
from sklearn.mixture import GaussianMixture
from sklearn.covariance import LedoitWolf
from threadpoolctl import threadpool_limits

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "quant_research_v2/src"))
from research import Risk, bank, gaussian, filter_returns

METHODS = ["historical", "historical_se_penalty", "gaussian_LW", "student_t_LW",
           "gmm_pooled", "gmm_base", "aptc_v1", "support_mix50", "support_band50",
           "filtered_historical", "equal_weight"]


def optimizer_diag(opt):
    return {"converged": bool(opt.success), "status": int(opt.status), "message": str(opt.message),
            "iterations": int(getattr(opt, "nit", 0)), "objective": float(opt.fun)}


def gmm_fit(x, seed):
    scale = np.maximum(x.std(0), .05)
    mu = x.mean(0)
    mod = GaussianMixture(3, covariance_type="full", reg_covar=.01, n_init=2,
                          max_iter=150, random_state=seed)
    with warnings.catch_warnings(record=True) as ww:
        warnings.simplefilter("always")
        mod.fit((x - mu) / scale)
    z, _ = mod.sample(1536)
    return z * scale + mu, {"converged": bool(mod.converged_), "iterations": int(mod.n_iter_),
                           "lower_bound": float(mod.lower_bound_), "warnings": [str(w.message) for w in ww]}


def student(x, w):
    f = LedoitWolf().fit(x)
    cov, d, y = f.covariance_, x.shape[1], x - f.location_
    mah = np.einsum("ij,jk,ik->i", y, np.linalg.inv(cov), y)
    ld = np.linalg.slogdet(cov)[1]
    def nll(nu):
        a = (nu - 2) / nu
        ll = gammaln((nu + d) / 2) - gammaln(nu / 2) - .5 * (d * np.log(nu * np.pi) + ld + d * np.log(a)) - .5 * (nu + d) * np.log1p(mah / (a * nu))
        return -float(ll.mean())
    fit = minimize_scalar(nll, bounds=(3., 50.), method="bounded")
    nu = fit.x
    sd = np.sqrt(np.einsum("ij,jk,ik->i", w, cov * ((nu - 2) / nu), w))
    m, z = -w @ f.location_, tdist.ppf(.95, nu)
    return (m + z * sd, m + sd * (nu + z*z) / (nu - 1) * tdist.pdf(z, nu) / .05), {**optimizer_diag(fit), "df": float(nu)}


def entropy_solve(A, B, p0, band):
    m = A.shape[1]
    logp = np.log(np.maximum(p0, 1e-300))
    if band == 0:
        def fg(v):
            logits = logp - A @ v
            l = logsumexp(logits)
            p = np.exp(logits - l)
            return float(l + B @ v + .5 * (v @ v)), B - A.T @ p + v
        opt = minimize(fg, np.zeros(m), jac=True, method="L-BFGS-B",
                       options={"maxiter": 160, "ftol": 1e-10, "gtol": 1e-7})
        v = opt.x
    else:
        def fg(u):
            v = u[:m] - u[m:]
            logits = logp - A @ v
            l = logsumexp(logits)
            p = np.exp(logits - l)
            g = B - A.T @ p + v
            return float(l + B @ v + band * u.sum() + .5 * (v @ v)), np.r_[g + band, -g + band]
        opt = minimize(fg, np.zeros(2*m), jac=True, bounds=[(0, None)] * (2*m), method="L-BFGS-B",
                       options={"maxiter": 200, "ftol": 1e-10, "gtol": 1e-7})
        v = opt.x[:m] - opt.x[m:]
    p = np.exp(logp - A @ v - logsumexp(logp - A @ v))
    return p, optimizer_diag(opt)


def calibrate(z, cal, w, beta=.5, band=1., old=False):
    if beta:
        p0 = np.r_[np.full(len(z), (1-beta)/len(z)), np.full(len(cal), beta/len(cal))]
        z = np.vstack([z, cal])
    else:
        p0 = np.full(len(z), 1/len(z))
    rb = Risk(z, w)
    v, _ = rb.eval(p0)
    h = np.maximum(rb.loss - v, 0)
    hc = np.maximum(-cal @ w.T - v, 0)
    b = hc.mean(0)
    if old:
        b = .5*b + .5*(p0 @ h)
    scales = np.maximum(hc.std(0, ddof=1)/np.sqrt(len(cal)), .025*np.maximum(np.std(-cal @ w.T, axis=0), .05))
    A, B, sel, p, steps = h/scales, b/scales, [], p0.copy(), []
    for it in range(8):
        best = int(np.argmin(rb.eval(p)[1]))
        dis = np.maximum(np.abs(B - A.T @ p) - band, 0)
        if sel:
            dis[sel] = -np.inf
        j = best if it % 3 == 0 and best not in sel else int(np.argmax(dis))
        sel.append(j)
        p, diag = entropy_solve(A[:, sel], B[sel], p0, band)
        steps.append(diag)
    return rb.eval(p), {"converged": all(s["converged"] for s in steps), "steps": steps,
                        "ess": float(1/(p @ p)), "directions": sel}


def forecast(x, w, seed):
    """No outcomes, population parameters, split labels or market test metrics."""
    x, w = np.asarray(x), np.asarray(w)
    if x.shape != (512, 8) or w.shape != (285, 8) or not np.isfinite(x).all():
        raise ValueError("Frozen training/weight shape or finite-domain violation")
    with threadpool_limits(limits=1):
        hist = Risk(x, w).eval()
        risks = {"historical": hist, "historical_se_penalty": hist, "equal_weight": hist}
        diag = {name: {"fallback": False, "converged": True, "warnings": []} for name in risks}
        def put(name, fn):
            try:
                with warnings.catch_warnings(record=True) as ww:
                    warnings.simplefilter("always")
                    risk, info = fn()
                if not all(np.isfinite(a).all() and a.shape == (len(w),) for a in risk):
                    raise FloatingPointError("Nonfinite or malformed risk surface")
                if np.any(risk[1] < risk[0] - 1e-8):
                    raise FloatingPointError("ES below VaR")
                risks[name] = risk
                diag[name] = {"fallback": False, "converged": True, **info,
                              "warnings": info.get("warnings", []) + [str(a.message) for a in ww]}
            except Exception as exc:
                risks[name] = hist
                diag[name] = {"fallback": True, "fallback_to": "historical", "converged": False,
                              "error": repr(exc), "warnings": []}
        put("gaussian_LW", lambda: (gaussian(x, w), {}))
        put("student_t_LW", lambda: student(x, w))
        def pooled():
            z, d = gmm_fit(x, seed)
            return Risk(z, w).eval(), d
        put("gmm_pooled", pooled)
        try:
            z, base_diag = gmm_fit(x[:256], seed)
            if not np.isfinite(z).all():
                raise FloatingPointError("Nonfinite base GMM scenarios")
            put("gmm_base", lambda: (Risk(z, w).eval(), base_diag))
            def correction(beta, band, old=False):
                risk, info = calibrate(z, x[256:], w, beta, band, old)
                info["base_gmm"] = base_diag
                info["converged"] = info["converged"] and base_diag["converged"]
                return risk, info
            put("aptc_v1", lambda: correction(0, 0, True))
            put("support_band50", lambda: correction(.5, 1))
            put("support_mix50", lambda: (Risk(np.vstack([z, x[256:]]), w).eval(
                np.r_[np.full(len(z), .5/len(z)), np.full(256, .5/256)]), {"base_gmm": base_diag, "converged": base_diag["converged"]}))
        except Exception as exc:
            for name in ("gmm_base", "aptc_v1", "support_mix50", "support_band50"):
                risks[name] = hist
                diag[name] = {"fallback": True, "fallback_to": "historical", "converged": False,
                              "error": repr(exc), "warnings": []}
        def filtered():
            res, vol = filter_returns(x)
            return Risk(res*vol, w).eval(), {"initialization_observations": 50, "residuals": len(res)}
        put("filtered_historical", filtered)
        vh, eh = hist
        se = (np.maximum(-x @ w.T - vh, 0)/.05).std(0, ddof=1)/np.sqrt(len(x))
        chosen = {m: int(np.argmin(risks[m][1])) for m in METHODS}
        chosen["historical_se_penalty"] = int(np.argmin(eh + se))
        chosen["equal_weight"] = 0
    return risks, chosen, diag
