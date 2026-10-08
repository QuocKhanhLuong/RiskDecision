"""Exact finite-law structure, evaluated in float64 (no numerical coverage claim).

ES uses positive losses and upper-tail mass alpha. The RU lower envelope is an
established baseline. The mass-crossing implementation is a specialization of it.
"""
from dataclasses import dataclass
from fractions import Fraction
from functools import wraps

import numpy as np


def strict_numerics(function):
    """Fail closed on overflow/NaN instead of returning a false risk bound."""
    @wraps(function)
    def call(*args, **kwargs):
        with np.errstate(over='raise', invalid='raise', divide='raise'):
            return function(*args, **kwargs)
    return call


@dataclass
class FiniteMixture:
    loss: np.ndarray
    p0: np.ndarray
    p1: np.ndarray
    alpha: float

    @strict_numerics
    def __post_init__(self):
        x, p0, p1 = (np.array(v, dtype=float, copy=True) for v in (self.loss, self.p0, self.p1))
        if x.ndim != 1 or not len(x) or p0.shape != x.shape or p1.shape != x.shape:
            raise ValueError('nonempty matching one-dimensional arrays required')
        if not all(np.isfinite(v).all() for v in (x, p0, p1)):
            raise ValueError('finite inputs required')
        if not np.isfinite(self.alpha) or not 0 < self.alpha <= 1:
            raise ValueError('tail probability alpha must be in (0,1]')
        for p in (p0, p1):
            if (p < 0).any() or abs(p.sum() - 1) > 1e-12:
                raise ValueError('state probabilities must be nonnegative and sum to one')
        keep = (p0 + p1) > 0
        order = np.argsort(-x[keep], kind='stable')
        self.loss, self.p0, self.p1 = (v[keep][order] for v in (x, p0, p1))
        self.c0 = np.r_[0., np.cumsum(self.p0)]
        self.c1 = np.r_[0., np.cumsum(self.p1)]
        self.c0[-1] = self.c1[-1] = 1.
        self.m0 = np.r_[0., np.cumsum(self.p0 * self.loss)]
        self.m1 = np.r_[0., np.cumsum(self.p1 * self.loss)]

    @strict_numerics
    def es(self, q):
        """Fractional-atom tail mean at K q values in O(K log S)."""
        q = np.asarray(q, dtype=float)
        if not np.isfinite(q).all() or ((q < 0) | (q > 1)).any():
            raise ValueError('mixture probabilities must lie in [0,1]')
        left = np.zeros(q.shape, dtype=int)
        right = np.full(q.shape, len(self.loss) - 1, dtype=int)
        while np.any(left < right):
            mid = (left + right) // 2
            cumulative = (1-q) * self.c0[mid+1] + q * self.c1[mid+1]
            right = np.where(cumulative >= self.alpha, mid, right)
            left = np.where(cumulative < self.alpha, mid+1, left)
        k = left
        mass_above = (1-q)*self.c0[k] + q*self.c1[k]
        moment_above = (1-q)*self.m0[k] + q*self.m1[k]
        result = (moment_above + (self.alpha-mass_above)*self.loss[k]) / self.alpha
        return float(result) if q.ndim == 0 else result

    @strict_numerics
    def crossings(self, lo=0., hi=1.):
        validate_interval(lo, hi)
        d = self.c1[1:-1] - self.c0[1:-1]
        changing = d != 0
        q = (self.alpha-self.c0[1:-1][changing]) / d[changing]
        return np.unique(np.r_[lo, q[(q > lo) & (q < hi)], hi])


def validate_interval(lo, hi):
    if not np.isfinite([lo, hi]).all() or not 0 <= lo <= hi <= 1:
        raise ValueError('interval must satisfy 0 <= lo <= hi <= 1')


@strict_numerics
def paired_certificate(a, b, lo=0., hi=1.):
    """Max ES(A;q)-ES(B;q) for the *same* q, fixed actions and supplied laws."""
    validate_interval(lo, hi)
    if a.alpha != b.alpha:
        raise ValueError('both actions must use the same tail probability')
    q = np.union1d(a.crossings(lo, hi), b.crossings(lo, hi))
    ra, rb = a.es(q), b.es(q)
    d = ra-rb
    index = int(np.argmax(d))
    return {'upper': float(d[index]), 'argmax': float(q[index]),
            'endpoint_upper': float(max(d[0], d[-1])),
            'independent_upper': float(ra.max()-rb.min()),
            'knots': q.tolist(), 'differences': d.tolist()}


class LowerEnvelope:
    """Generic minimum of affine lines, sorted-slope convex hull baseline."""

    @strict_numerics
    def __init__(self, intercepts, slopes):
        intercepts, slopes = np.asarray(intercepts), np.asarray(slopes)
        if (intercepts.ndim != 1 or not len(intercepts) or slopes.shape != intercepts.shape
                or not np.isfinite(intercepts).all() or not np.isfinite(slopes).all()):
            raise ValueError('nonempty finite matching line coefficients required')
        lines = sorted(zip(slopes, intercepts), key=lambda mb: (-mb[0], mb[1]))
        hull, starts = [], []
        for m, b in lines:
            if hull and m == hull[-1][0]:
                continue  # sorting kept the lower of parallel lines
            cross = -np.inf
            while hull:
                old_m, old_b = hull[-1]
                cross = (b-old_b)/(old_m-m)
                if cross > starts[-1]:
                    break
                hull.pop()
                starts.pop()
            if not hull:
                cross = -np.inf
            hull.append((m, b))
            starts.append(cross)
        self.slopes, self.intercepts = np.array(hull).T
        self.starts = np.array(starts)

    @strict_numerics
    def __call__(self, q):
        q = np.asarray(q)
        i = np.searchsorted(self.starts, q, side='right')-1
        return self.intercepts[i] + self.slopes[i]*q


@strict_numerics
def ru_envelope(mixture):
    """RU costs at all thresholds; independent ascending-support construction."""
    # Input construction already sorted descending; do not sort a second time.
    x, p0, p1 = (v[::-1] for v in (mixture.loss, mixture.p0, mixture.p1))
    # Strictly/weakly above ties give the same excess because x-t=0 at a tie.
    w0, w1 = (np.cumsum(p[::-1])[::-1] for p in (p0, p1))
    v0, v1 = (np.cumsum((p*x)[::-1])[::-1] for p in (p0, p1))
    e0, e1 = v0-x*w0, v1-x*w1
    return LowerEnvelope(x+e0/mixture.alpha, (e1-e0)/mixture.alpha)


@strict_numerics
def hull_certificate(a, b, lo=0., hi=1.):
    validate_interval(lo, hi)
    if a.alpha != b.alpha:
        raise ValueError('both actions must use the same tail probability')
    ea, eb = ru_envelope(a), ru_envelope(b)
    points = np.r_[ea.starts, eb.starts]
    points = np.unique(np.r_[lo, points[(points > lo) & (points < hi)], hi])
    d = ea(points)-eb(points)
    index = int(np.argmax(d))
    return {'upper': float(d[index]), 'argmax': float(points[index]),
            'knots': points.tolist(), 'differences': d.tolist()}


def rational_witness():
    """Independent exact RU enumeration on the pre-derived witness."""
    f = Fraction
    alpha = f(1, 20)
    def ru(x, p):
        return min(t + sum(m*max(v-t, 0) for v, m in zip(x, p))/alpha for t in x)
    values = []
    for q in (f(0), alpha, f(1)):
        ra = ru([f(0), f(10)], [1-q, q])
        rb = ru([f(0), f(1), f(11)], [q*(1-alpha), 1-q, q*alpha])
        values.append({'q': str(q), 'es_a': str(ra), 'es_b': str(rb), 'difference': str(ra-rb)})
    return values


@strict_numerics
def ar_analytic(length, phi, variance=1.):
    """Exact Gaussian quadratic-form moments, all using half squared loss."""
    if not isinstance(length, (int, np.integer)) or length < 1:
        raise ValueError('positive integer length required')
    if not np.isfinite([phi, variance]).all() or abs(phi) >= 1 or variance <= 0:
        raise ValueError('stationary AR coefficient and positive variance required')
    t = length
    h = np.arange(1, t)
    var_mean = variance * (t+2*np.sum((t-h)*phi**h)) / t**2
    cov_next = variance * np.sum(phi**np.arange(1, t+1)) / t
    delta = var_mean-cov_next
    u = np.full(t, 1/t)
    a = u.copy()
    a[-1] -= phi
    sigma = variance * phi**np.abs(np.arange(t)[:, None]-np.arange(t))
    matrix = .5*(np.outer(a, a)-np.eye(t)/t+np.outer(u, u))
    product = matrix @ sigma
    trace_mean = np.trace(product)+.5*variance*(1-phi**2)
    residual_mse = 2*np.einsum('ij,ji->', product, product)
    infinite = variance/(t*(1-phi))
    corrections = {'none': 0., 'iid': variance/t, 'finite': delta, 'infinite': infinite}
    return {'length': t, 'phi': phi, 'variance': variance, 'delta': float(delta),
            'trace_delta': float(trace_mean), 'gap_variance': float(residual_mse),
            'corrections': corrections,
            'conditional_mse': {k: float(residual_mse+(v-delta)**2) for k, v in corrections.items()},
            'oracle_conditional_mse': 0.}
