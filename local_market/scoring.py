"""Upper-loss joint VaR/ES scores and empirical pooled policy-tail statistic."""
import numpy as np


def score(loss, var, es, q=.95):
    finite = np.isfinite([loss, var, es]).all()
    defined = bool(finite and es > 0 and es >= var - 1e-8)
    hinge = max(loss - var, 0.)
    return {"realized_loss": float(loss), "var95": float(var), "es95": float(es),
            "var_breach": int(loss > var), "pinball95": float((q - float(loss < var)) * (loss-var)),
            "fz0": float((hinge/(1-q) + var)/es + np.log(es) - 1) if defined else None,
            "fz0_defined": defined,
            "shortfall_residual": float(var + hinge/(1-q) - es)}


def empirical_es(losses, q=.95, axis=0):
    """Fractional tail atoms: pooled OOS statistic, never conditional ES truth."""
    a = np.sort(np.asarray(losses), axis=axis)
    n = a.shape[axis]
    if not n:
        raise ValueError("Empty ES sample")
    tail = n * (1-q)
    whole = int(np.floor(tail + 1e-12))
    frac = max(0., tail-whole)
    rev = np.flip(a, axis=axis)
    total = np.take(rev, range(whole), axis=axis).sum(axis=axis)
    if frac > 1e-12:
        total = total + frac * np.take(rev, whole, axis=axis)
    return total / tail
