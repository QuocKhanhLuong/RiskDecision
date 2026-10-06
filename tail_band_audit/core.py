from coverage_audit.core import generate, features, bank, gmm_fit, QUANTILES
from scipy.stats import norm
import numpy as np

ANCHORS = ["population_quantiles_oracle", "base_only", "reused_mixture"]
RECIPES = ["plugin_max_t", "oracle_width_swap", "fixed_scale_max"]


def normal_hinge_moments(eta, sd):
    """Exact first/second raw moments for L~N(0,sd²), evaluator only."""
    z = eta/sd
    mean = sd*norm.pdf(z)-eta*norm.sf(z)
    second = (sd*sd+eta*eta)*norm.sf(z)-eta*sd*norm.pdf(z)
    variance = np.maximum(second-mean*mean, 0)
    return mean, variance


def radii(h, exact_se, base_scale, multipliers):
    """Share identical multiplier errors across all three diagnostic recipes.

    oracle_width_swap changes only the radius scale, leaving plugin critical
    value fixed. It is not a feasible procedure or a complete oracle bootstrap.
    fixed_scale_max uses independent base SD and never the population SE.
    """
    n = len(h)
    plugin_se = h.std(0, ddof=1)/np.sqrt(n)
    noise = multipliers @ (h-h.mean(0))/np.sqrt(n*(n-1))
    t = np.divide(noise, plugin_se, out=np.zeros_like(noise), where=plugin_se > 0)
    critical = float(np.quantile(np.abs(t).max(1), .95, method="higher"))
    fixed_critical = float(np.quantile(np.abs(noise/base_scale).max(1), .95, method="higher"))
    return {"plugin_max_t": critical*plugin_se,
            "oracle_width_swap": critical*exact_se,
            "fixed_scale_max": fixed_critical*base_scale}, plugin_se, critical


def weighted_es_sorted(values, weights, q=.95):
    """Exact upper-tail integral, including partial atoms at VaR."""
    values, weights = np.asarray(values), np.asarray(weights)
    if values.ndim == 1:
        values = values[:, None]
    if weights.ndim == 1:
        weights = weights[:, None]
    if np.any(np.diff(values, axis=0) < -1e-12) or np.any(weights < -1e-12):
        raise ValueError("Need sorted values and nonnegative weights")
    if not np.allclose(weights.sum(0), 1):
        raise ValueError("Weights must sum to one")
    cum = np.cumsum(weights, axis=0)
    previous = cum-weights
    tail = np.maximum(cum-np.maximum(previous, q), 0)
    return np.sum(tail*values, axis=0)/(1-q)


def dkw_es(loss, lower, upper, delta=.05):
    """Simultaneous ES bounds on a FIXED bounded portfolio bank, IID only.

    DKW + union bound over portfolios gives epsilon. Extremal distributions
    transfer epsilon empirical mass bottom->known upper or top->known lower.
    These are genuine bounded-target ES intervals; unbounded-loss coverage is
    not asserted. The finite-bank bound controls all thresholds and quantiles.
    """
    n, m = loss.shape
    lower, upper = np.asarray(lower), np.asarray(upper)
    if np.any(lower >= upper) or np.any(loss < lower-1e-12) or np.any(loss > upper+1e-12):
        raise ValueError("Known support bounds violated")
    eps = min(float(np.sqrt(np.log(2*m/delta)/(2*n))), 1.)
    values = np.vstack([lower, np.sort(loss, axis=0), upper])
    # Keep empirical quantile mass on [eps,1] for the upper law;
    # keep [0,1-eps] for the lower law. Atoms at endpoints restore unit mass.
    p0, p1 = np.arange(n)/n, np.arange(1,n+1)/n
    upper_mass = np.maximum(p1-np.maximum(p0, eps), 0)
    lower_mass = np.maximum(np.minimum(p1, 1-eps)-p0, 0)
    upper_weights = np.r_[0., upper_mass, eps]
    lower_weights = np.r_[eps, lower_mass, 0.]
    return weighted_es_sorted(values, lower_weights), weighted_es_sorted(values, upper_weights), eps


def clipped_normal_es(sd, cap_sigma=3., q=.95):
    """Population ES of clip(N(0,sd²),-cap*sd,cap*sd); q within caps."""
    if not norm.cdf(-cap_sigma) < q < norm.cdf(cap_sigma):
        raise ValueError("Quantile must lie inside clipping bounds")
    remainder = normal_hinge_moments(cap_sigma*sd, sd)[0]
    return sd*norm.pdf(norm.ppf(q))/(1-q)-remainder/(1-q)


def metrics(center, radius, target, exact_se, plugin_se, h, es):
    error = center-target
    covered = np.abs(error) <= radius+1e-12
    normalized = radius/(.05*np.repeat(es, 3))
    ratios = plugin_se/exact_se
    under = error < -radius-1e-12
    return {"all_covered": int(covered.all()), "equal_q95_covered": int(covered[1]),
            "q90_all_covered": int(covered.reshape(-1,3)[:,0].all()),
            "q95_all_covered": int(covered.reshape(-1,3)[:,1].all()),
            "q975_all_covered": int(covered.reshape(-1,3)[:,2].all()),
            "features_covered_fraction": float(covered.mean()),
            "under_cases": int(under.any()), "over_cases": int((error > radius+1e-12).any()),
            "zero_se_features": int((plugin_se == 0).sum()),
            "se_ratio_min": float(ratios.min()), "se_ratio_median": float(np.median(ratios)),
            "se_ratio_at_worst_error": float(ratios[np.argmax(np.abs(error)/exact_se)]),
            "tail_count_min": int((h>0).sum(0).min()),
            "width_ratio_median": float(np.median(normalized)), "width_ratio_max": float(normalized.max())}
