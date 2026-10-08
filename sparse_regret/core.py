"""Full-simplex edge reduction; historical two-component solvers stay immutable."""
from itertools import combinations

import numpy as np
from scipy.optimize import linprog

from bank_regret.core import make_bank, solve_local, solve_union


class SimplexBank:
    def __init__(self, losses, components, alpha, costs):
        self.x = np.array(losses, dtype=float, copy=True)
        self.p = np.array(components, dtype=float, copy=True)
        self.costs = np.array(costs, dtype=float, copy=True)
        self.alpha = float(alpha)
        if (self.x.ndim != 2 or min(self.x.shape) < 1 or self.p.ndim != 2
                or self.p.shape[0] < 1 or self.p.shape[1] != self.x.shape[0]
                or self.costs.shape != (self.x.shape[1],)):
            raise ValueError('scenario/action matrix, component probability rows and costs required')
        if not all(np.isfinite(a).all() for a in (self.x, self.p, self.costs)):
            raise ValueError('finite inputs required')
        if ((self.p < 0).any() or np.max(abs(self.p.sum(axis=1)-1)) > 1e-12
                or (self.costs < 0).any() or not 0 < self.alpha <= 1):
            raise ValueError('probabilities, alpha or fixed costs invalid')
        self.r, self.m = len(self.p), self.x.shape[1]

    def risks(self, q):
        """Independent fractional-tail sum, no RU hull or edge reduction."""
        q = np.asarray(q, float)
        if (q.shape != (self.r,) or not np.isfinite(q).all() or (q < -1e-10).any()
                or abs(q.sum()-1) > 1e-9):
            raise ValueError('full-simplex q required')
        mass = np.maximum(q, 0) @ self.p
        risks = []
        for i in range(self.m):
            order = np.argsort(-self.x[:, i], kind='stable')
            before = np.r_[0., np.cumsum(mass[order])[:-1]]
            used = np.minimum(mass[order], np.maximum(0., self.alpha-before))
            risks.append(float(used @ self.x[order, i]/self.alpha+self.costs[i]))
        return np.array(risks)


def _pack(regrets, qs, competitors, **meta):
    if not np.isfinite(regrets).all():
        raise FloatingPointError('nonfinite regret')
    return dict(regrets=np.asarray(regrets).tolist(), worst_q=np.asarray(qs).tolist(),
                competitor=np.asarray(competitors, int).tolist(), selected=int(np.argmin(regrets)), **meta)


def solve_edges(bank, method='local'):
    """Exact for the FULL simplex only; no constrained-region argument accepted.

    Worst regret for every action has an at-most-two-component witness. For
    alpha=1 the risks are affine and component vertices suffice. Complexity
    otherwise is O(R^2 K log K), K <= M*S, with one shared bank hull per edge.
    """
    if method not in ('local', 'union'):
        raise ValueError('local or union required')
    if bank.alpha == 1:
        risk = bank.p @ bank.x + bank.costs
        gaps = risk-risk.min(axis=1, keepdims=True)
        index = gaps.argmax(axis=0)
        return _pack(gaps[index, np.arange(bank.m)], np.eye(bank.r)[index],
                     risk.argmin(axis=1)[index], edges=0, risk_evaluations=bank.r*bank.m,
                     mean_shortcut=True)
    regrets = np.full(bank.m, -np.inf)
    qs, competitors = np.zeros((bank.m, bank.r)), np.zeros(bank.m, int)
    edges, evaluations = 0, 0
    pairs = combinations(range(bank.r), 2) if bank.r > 1 else [(0, 0)]
    for a, b in pairs:
        laws = make_bank(bank.x, bank.p[[a, b]], bank.alpha)
        result = (solve_local if method == 'local' else solve_union)(laws, bank.costs)
        new = np.asarray(result['regrets'])
        improve = new > regrets
        regrets[improve] = new[improve]
        for i in np.flatnonzero(improve):
            w = result['worst_q'][i]
            qs[i] = 0.
            qs[i, a] += 1-w
            qs[i, b] += w
            competitors[i] = result['competitor'][i]
        edges += 1
        evaluations += result['risk_evaluations']
    return _pack(regrets, qs, competitors, edges=edges, risk_evaluations=evaluations,
                 mean_shortcut=False)


def solve_lp(bank):
    """Independent full-simplex LP enumeration, with no edge/support assumption.

    Each ES_j = min_s a_js.q. Thus max_q (ES_i-min_j ES_j) equals
    max_(j,s) max_(q,z) z-a_js.q, z<=a_it.q for every t. We solve each
    concave piece with HiGHS over all R coordinates. Fixed costs are already
    included in every coefficient. Same-action pairs contribute zero exactly.
    """
    lines = []
    for i in range(bank.m):
        thresholds = np.unique(bank.x[:, i])
        excess = np.maximum(bank.x[:, i, None]-thresholds[None, :], 0)
        lines.append((bank.p @ excess/bank.alpha + thresholds + bank.costs[i]).T)
    regrets, qs, competitors = np.zeros(bank.m), np.zeros((bank.m, bank.r)), np.arange(bank.m)
    qs[:, 0] = 1.
    calls, max_violation = 0, 0.
    for i, own in enumerate(lines):
        matrix = np.column_stack([-own, np.ones(len(own))])
        for j, other in enumerate(lines):
            if i == j:
                continue
            for row in other:
                solved = linprog(np.r_[row, -1.], A_ub=matrix, b_ub=np.zeros(len(own)),
                                 A_eq=np.array([np.r_[np.ones(bank.r), 0.]]), b_eq=[1.],
                                 bounds=[(0., None)]*bank.r+[(None, None)], method='highs',
                                 options={'dual_feasibility_tolerance': 1e-9,
                                          'primal_feasibility_tolerance': 1e-9})
                calls += 1
                if not solved.success:
                    raise ArithmeticError(f'LP failure: {solved.message}')
                violation = max(0., float(np.max(matrix @ solved.x)),
                                abs(float(solved.x[:-1].sum())-1), -float(solved.x[:-1].min()))
                max_violation = max(max_violation, violation)
                if -solved.fun > regrets[i]:
                    regrets[i] = -solved.fun
                    qs[i], competitors[i] = solved.x[:-1], j
    if max_violation > 2e-8:
        raise ArithmeticError(f'LP primal residual {max_violation}')
    return _pack(regrets, qs, competitors, lp_calls=calls, max_primal_violation=max_violation)


def witness_error(bank, result):
    errors = []
    for i, q in enumerate(result['worst_q']):
        risks = bank.risks(q)
        errors.append(abs(risks[i]-risks.min()-result['regrets'][i]))
        errors.append(abs(risks[result['competitor'][i]]-risks.min()))
    return float(max(errors))
