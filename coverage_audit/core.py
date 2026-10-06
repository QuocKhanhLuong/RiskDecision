"""Stationary generators, finite feature maps and empirical uncertainty recipes."""
from local_market.models import bank, gmm_fit, Risk
from correction_audit.run import population_hinge
from research import covariance, truth
import numpy as np

FAMILIES = ["gaussian", "student_t4", "asymmetric_crash", "ar1", "markov_volatility"]
ANCHORS = ["base_only", "reused_mixture"]
PROCEDURES = ["v2_heuristic", "iid_max_t", "block_short_max_t", "block_long_max_t"]
QUANTILES = [.90, .95, .975]


def generate(seed, family, n=1280):
    """New Cholesky-based draws. Fixed parameters, stationary initial states.

    This does not reproduce or replace the archived v2 random samples.
    """
    r = np.random.default_rng(np.random.SeedSequence([seed, FAMILIES.index(family), 62000]))
    c, s = covariance(np.random.default_rng(62000), 8)
    marginal = {"kind": "mix", "p": np.array([1.]), "mu": np.zeros((1, 8)), "cov": c[None]}
    states = np.zeros(n, dtype=int)
    if family == "student_t4":
        marginal = {"kind": "t", "df": 4., "mean": np.zeros(8), "shape": c/2}
        x = (r.standard_normal((n, 8)) @ np.linalg.cholesky(c/2).T) / np.sqrt(r.chisquare(4, n)/4)[:, None]
    elif family == "ar1":
        eps = r.standard_normal((n, 8)) @ np.linalg.cholesky(c).T
        x = np.empty_like(eps)
        x[0] = eps[0]
        for i in range(1, n):
            x[i] = .6*x[i-1] + .8*eps[i]
    else:
        if family == "asymmetric_crash":
            perm = np.random.default_rng(62000).permutation(8)
            a, b = np.full(8, -.45), np.full(8, -.35)
            a[perm[:4]], b[perm[4:]] = -3.5, -4.5
            p = np.array([.92, .05, .03])
            mu = np.array([np.zeros(8), a, b]); mu -= p @ mu
            cc = np.outer(s, s)*(.65*np.ones((8, 8))+.35*np.eye(8))
            marginal = {"kind": "mix", "p": p, "mu": mu, "cov": np.array([c, 1.65**2*cc, 1.9**2*cc])}
            states = r.choice(3, n, p=p)
        elif family == "markov_volatility":
            transition = np.array([[.985, .015], [.12, .88]])
            cc = np.outer(s, s)*(.70*np.ones((8, 8))+.30*np.eye(8))*6.25
            marginal = {"kind": "mix", "p": np.array([8/9, 1/9]), "mu": np.zeros((2, 8)), "cov": np.array([c, cc])}
            states[0] = r.choice(2, p=marginal["p"])
            for i in range(1, n):
                states[i] = r.choice(2, p=transition[states[i-1]])
        elif family != "gaussian":
            raise ValueError(family)
        x = np.empty((n, 8))
        for k in range(len(marginal["p"])):
            ix = np.flatnonzero(states == k)
            x[ix] = marginal["mu"][k] + r.standard_normal((len(ix), 8)) @ np.linalg.cholesky(marginal["cov"][k]).T
    return x, marginal, states


def conditional(family, marginal, last_x, last_state):
    if family == "ar1":
        return {"kind": "mix", "p": np.array([1.]), "mu": (.6*last_x)[None], "cov": .64*marginal["cov"]}
    if family == "markov_volatility":
        return {**marginal, "p": np.array([[.985, .015], [.12, .88]])[last_state]}
    return marginal


def features(z, cal, w, anchor):
    """Portfolio-major order: j*3+k. All thresholds are fixed in bootstrap."""
    if anchor not in ANCHORS:
        raise ValueError(anchor)
    support = z if anchor == "base_only" else np.vstack([z, cal])
    p = (np.full(len(z), 1/len(z)) if anchor == "base_only" else
         np.r_[np.full(len(z), .5/len(z)), np.full(len(cal), .5/len(cal))])
    risk = Risk(support, w)
    eta = np.column_stack([risk.eval(p, q=q)[0] for q in QUANTILES]).ravel()
    loss = -cal @ w.T
    h = np.maximum(np.repeat(loss, 3, axis=1) - eta, 0)
    prior = p @ np.maximum(np.repeat(risk.loss, 3, axis=1) - eta, 0)
    floor = np.repeat(.025*np.maximum(loss.std(0), .05), 3)
    heuristic = np.maximum(h.std(0, ddof=1)/np.sqrt(len(cal)), floor)
    selected = int(np.argmax(np.abs(prior-h.mean(0))/heuristic))
    return eta, h, heuristic, selected


def multiplier(h, block, draws, seed):
    """Studentized nonoverlapping block Gaussian multiplier, no theorem claimed.

    k equal blocks, centered block sums S. SE=sqrt(k/(k-1)*sum S^2)/n.
    Draw errors = sqrt(k/(k-1)) * G @ S / n, with G iid standard normal.
    Radius = empirical 95% ('higher') quantile of max |error/SE| times SE.
    Zero-SE features get zero radius and remain in the coverage assessment.
    """
    n, m = h.shape
    if n % block or n//block < 2:
        raise ValueError("Equal complete blocks with at least two blocks required")
    k = n//block
    sums = (h-h.mean(0)).reshape(k, block, m).sum(1)
    se = np.sqrt((sums*sums).sum(0)*k/(k-1))/n
    g = np.random.default_rng(seed).standard_normal((draws, k))
    noise = (g @ sums)*np.sqrt(k/(k-1))/n
    scaled = np.divide(noise, se, out=np.zeros_like(noise), where=se > 0)
    critical = float(np.quantile(np.max(np.abs(scaled), axis=1), .95, method="higher"))
    return critical*se, critical, int(np.count_nonzero(se == 0))


def evaluate(center, radius, population, es, selected):
    covered = np.abs(center-population) <= radius + 1e-12
    ratio = radius/(.05*np.repeat(es, 3))
    return {"all_covered": int(covered.all()), "equal_q95_covered": int(covered[1]),
            "selected_covered": int(covered[selected]), "feature_coverage": float(covered.mean()),
            "width_ratio_median": float(np.median(ratio)), "width_ratio_max": float(ratio.max())}


def counterexample():
    """Perfect stationary moments do not identify next-state conditional ES."""
    p, persistence, alpha = .02, .8, .05
    switch = p*(1-persistence)/(1-p)
    return {"stationary_high_probability": p, "high_to_high": persistence,
            "low_to_high": switch, "marginal_es95": 10*min(p/alpha, 1),
            "after_high_es95": 10*min(persistence/alpha, 1),
            "after_low_es95": 10*min(switch/alpha, 1)}
