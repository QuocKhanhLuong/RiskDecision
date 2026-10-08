"""Action-local witnesses for finite-mixture minimax ES regret.

Known ingredients: RU threshold representation, affine lower hull, minimax
regret. Scope: supplied finite laws and fixed action costs, float64 arithmetic.
"""
import numpy as np

from mixture_order.core import FiniteMixture, strict_numerics, validate_interval


class OwnedHull:
    """Generic affine lower envelope with action-owner witnesses."""

    @strict_numerics
    def __init__(self, intercept, slope, owner):
        b, m = np.asarray(intercept, float), np.asarray(slope, float)
        owners = np.asarray(owner, int)
        if b.ndim != 1 or not len(b) or m.shape != b.shape or owners.shape != b.shape:
            raise ValueError('matching nonempty line arrays required')
        if not np.isfinite(b).all() or not np.isfinite(m).all():
            raise ValueError('finite coefficients required')
        # Descending slopes, lower intercept, lower owner; deterministic ties.
        order = np.lexsort((owners, b, -m))
        stack, starts = [], []
        for j in order:
            if stack and m[j] == m[stack[-1]]:
                continue
            cross = -np.inf
            while stack:
                old = stack[-1]
                cross = (b[j]-b[old])/(m[old]-m[j])
                if cross > starts[-1]:
                    break
                stack.pop()
                starts.pop()
            if not stack:
                cross = -np.inf
            stack.append(j)
            starts.append(cross)
        self.intercept, self.slope, self.owner = b[stack], m[stack], owners[stack]
        self.starts = np.asarray(starts)
        self.n_lines = len(b)

    @strict_numerics
    def at(self, q):
        q = np.asarray(q, float)
        if not np.isfinite(q).all():
            raise ValueError('finite query required')
        j = np.searchsorted(self.starts, q, side='right')-1
        return self.intercept[j]+self.slope[j]*q, self.owner[j]


def validate_bank(laws, costs, interval):
    if not laws or any(law.alpha != laws[0].alpha for law in laws):
        raise ValueError('nonempty bank with common tail probability required')
    costs = np.asarray(costs, float)
    if costs.shape != (len(laws),) or not np.isfinite(costs).all() or (costs < 0).any():
        raise ValueError('one finite nonnegative fixed cost per action required')
    validate_interval(*interval)
    return costs


@strict_numerics
def bank_hull(laws, costs):
    bs, ms, owners = [], [], []
    for i, (law, cost) in enumerate(zip(laws, costs)):
        # For threshold x[k], take moments/masses strictly before k in descending support.
        e0 = law.m0[:-1]-law.loss*law.c0[:-1]
        e1 = law.m1[:-1]-law.loss*law.c1[:-1]
        bs.append(law.loss+e0/law.alpha+cost)
        ms.append((e1-e0)/law.alpha)
        owners.append(np.full(len(law.loss), i, int))
    return OwnedHull(np.concatenate(bs), np.concatenate(ms), np.concatenate(owners))


def pack_result(regrets, qs, competitors, evaluations, hull):
    regrets = np.asarray(regrets)
    if not np.isfinite(regrets).all():
        raise FloatingPointError('nonfinite regret result')
    return {'regrets': regrets.tolist(), 'worst_q': np.asarray(qs).tolist(),
            'competitor': np.asarray(competitors, int).tolist(), 'selected': int(np.argmin(regrets)),
            'risk_evaluations': int(evaluations), 'input_lines': hull.n_lines,
            'active_hull_lines': len(hull.starts)}


@strict_numerics
def solve_local(laws, costs, interval=(0., 1.)):
    """O(K log K): global bank hull queried at each action's own knots only."""
    costs = validate_bank(laws, costs, interval)
    hull = bank_hull(laws, costs)
    own = [law.crossings(*interval) for law in laws]
    offsets = np.r_[0, np.cumsum([len(q) for q in own])]
    q_all = np.concatenate(own)
    own_risk = np.concatenate([law.es(q)+cost for law, q, cost in zip(laws, own, costs)])
    best, owner = hull.at(q_all)
    gaps = own_risk-best
    indices = [int(offsets[i]+np.argmax(gaps[offsets[i]:offsets[i+1]])) for i in range(len(laws))]
    return pack_result(gaps[indices], q_all[indices], owner[indices], len(q_all), hull)


@strict_numerics
def solve_union(laws, costs, interval=(0., 1.)):
    """Strong exact baseline: same global hull, all actions on union of own knots."""
    costs = validate_bank(laws, costs, interval)
    hull = bank_hull(laws, costs)
    q = np.unique(np.concatenate([law.crossings(*interval) for law in laws]))
    best, owner = hull.at(q)
    regrets, qs, competitors = [], [], []
    for law, cost in zip(laws, costs):
        gap = law.es(q)+cost-best
        j = int(np.argmax(gap))
        regrets.append(gap[j])
        qs.append(q[j])
        competitors.append(owner[j])
    return pack_result(regrets, qs, competitors, len(laws)*len(q), hull)


@strict_numerics
def endpoint_regrets(laws, costs, interval):
    costs = validate_bank(laws, costs, interval)
    risks = np.array([law.es(interval)+c for law, c in zip(laws, costs)])
    return np.max(risks-risks.min(axis=0), axis=1)


@strict_numerics
def risk_extrema(laws, costs, interval, endpoints_only=False):
    costs = validate_bank(laws, costs, interval)
    lows, highs = [], []
    for law, c in zip(laws, costs):
        q = interval if endpoints_only else law.crossings(*interval)
        risks = law.es(q)+c
        lows.append(float(np.min(risks)))
        highs.append(float(np.max(risks)))
    return np.asarray(lows), np.asarray(highs)


def solve_worlds(worlds, costs, intervals, solver=solve_local):
    if not worlds or len(worlds) != len(intervals) or any(len(w) != len(worlds[0]) for w in worlds):
        raise ValueError('matching nonempty worlds/intervals and common bank required')
    if any(w[0].alpha != worlds[0][0].alpha for w in worlds):
        raise ValueError('common tail probability across worlds required')
    solved = [solver(world, costs, interval) for world, interval in zip(worlds, intervals)]
    matrix = np.array([s['regrets'] for s in solved])
    indices = matrix.argmax(axis=0)
    regrets = matrix.max(axis=0)
    return {'regrets': regrets.tolist(), 'worst_world': indices.tolist(),
            'worst_q': [solved[k]['worst_q'][i] for i, k in enumerate(indices)],
            'competitor': [solved[k]['competitor'][i] for i, k in enumerate(indices)],
            'selected': int(np.argmin(regrets)), 'per_world': solved}


def make_bank(loss_matrix, components, alpha):
    """loss_matrix rows are public joint scenarios, columns fixed actions."""
    x = np.asarray(loss_matrix, float)
    p = np.asarray(components, float)
    if x.ndim != 2 or not x.shape[1] or p.shape != (2, x.shape[0]):
        raise ValueError('scenario x action matrix and two probability rows required')
    return [FiniteMixture(x[:, i], p[0], p[1], alpha) for i in range(x.shape[1])]
