"""Held-out ES contrasts with shared block multipliers; no guarantee claimed."""
from local_market.models import Risk
import numpy as np

CANDIDATES = ["support_mix50", "support_band50", "filtered_historical"]
RECIPES = ["point", "absolute", "paired", "paired_no_band"]


def intervals(x, weights, block, draws, seed):
    """Columns: frozen training baseline, then three frozen candidates.

    Reestimate each VaR on the assessment sample, then exact empirical ES.
    Centered hinge/alpha is the first-order ES influence approximation.
    The same Gaussian block multipliers are used for absolute and contrast
    maxima. These are asymptotic recipes, not finite-sample certificates.
    """
    n = len(x)
    if n % block or n // block < 2:
        raise ValueError("Complete blocks required")
    v, e = Risk(x, weights).eval()
    h = np.maximum(-x @ weights.T - v, 0) / .05
    h -= h.mean(0)
    k = n // block
    sums = h.reshape(k, block, len(weights)).sum(1)
    g = np.random.default_rng(seed).standard_normal((draws, k))
    noise = g @ sums * np.sqrt(k / (k - 1)) / n
    contrast = noise[:, 1:] - noise[:, :1]
    ar = float(np.quantile(np.abs(noise).max(1), .95, method="higher"))
    pr = float(np.quantile(np.abs(contrast).max(1), .95, method="higher"))
    # Absolute intervals imply difference radii r_j+r_baseline = 2*ar.
    delta = e[1:] - e[0]
    radii = {"point": 0., "absolute": 2 * ar, "paired": pr}
    # Tie => baseline. Both controls choose minimum assessed ES among admitted.
    choices = {name: (int(np.argmin(delta)) + 1 if delta.min() + r < -1e-12 else 0)
               for name, r in radii.items()}
    # Remove APTC from both the candidate menu and the simultaneous maximum.
    nr = float(np.quantile(np.abs(contrast[:, [0, 2]]).max(1), .95, method="higher"))
    j = [0, 2][int(np.argmin(delta[[0, 2]]))]
    radii["paired_no_band"] = nr
    choices["paired_no_band"] = j+1 if delta[j]+nr < -1e-12 else 0
    return {"es": e, "delta": delta, "radii": radii, "choices": choices,
            "absolute_radius": ar, "paired_radius": pr,
            "paired_to_absolute_radius": pr / (2 * ar) if ar else 0.}


def historical_choice(x, w):
    v, e = Risk(x, w).eval()
    se = (np.maximum(-x @ w.T-v, 0)/.05).std(0, ddof=1)/np.sqrt(len(x))
    return int(np.argmin(e+se))


def assess(result, target, ids, baseline_scale, regret_scale):
    """Truth enters only here, after candidate choices and gate are fixed."""
    t = target[ids]
    delta = t[1:]-t[0]
    rows = []
    for name, radius in result["radii"].items():
        selected = result["choices"][name]
        menu = [0, 2] if name == "paired_no_band" else [0, 1, 2]
        rows.append({"recipe": name, "switched": int(selected != 0),
                     "selected_slot": selected, "portfolio_id": int(ids[selected]),
                     "harm": int(t[selected] > t[0]+1e-10),
                     "relative_delta": float((t[selected]-t[0])/baseline_scale),
                     "relative_regret": float((t[selected]-target.min())/regret_scale),
                     "all_contrasts_covered": int(np.all(np.abs(result["delta"][menu]-delta[menu]) <= radius+1e-10)),
                     "radius": radius, "radius_ratio": result["paired_to_absolute_radius"],
                     "available_improvement": float(max(0., t[0]-t[1:].min())/baseline_scale),
                     "best_candidate_slot": int(np.argmin(t[1:]))+1})
    return rows
