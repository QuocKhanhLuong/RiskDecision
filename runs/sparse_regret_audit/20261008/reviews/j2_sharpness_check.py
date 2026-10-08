"""Exact rational J=2 spectral-ES support-three sharpness check."""

from __future__ import annotations

from fractions import Fraction as F
from itertools import combinations


ALPHAS = (F(1, 5), F(3, 5))
WEIGHTS = (F(1, 2), F(1, 2))

# Components have finite rational laws. The comparison action is zero loss.
LAWS = [
    [(0, F(309, 1000)), (3, F(235, 1000)), (9, F(147, 1000)), (14, F(309, 1000))],
    [(0, F(58, 1000)), (7, F(790, 1000)), (14, F(130, 1000)), (16, F(22, 1000))],
    [(0, F(685, 1000)), (10, F(161, 1000)), (18, F(88, 1000)), (20, F(66, 1000))],
]


def merged_values():
    return sorted({x for law in LAWS for x, _ in law})


def component_masses():
    values = merged_values()
    return values, [[dict(law).get(x, F(0)) for x in values] for law in LAWS]


def mixture_law(q):
    d = {}
    for qr, law in zip(q, LAWS):
        for x, p in law:
            d[x] = d.get(x, F(0)) + qr * p
    return sorted(d.items())


def es(q, alpha):
    remain = alpha
    total = F(0)
    for x, p in reversed(mixture_law(q)):
        take = min(remain, p)
        total += take * x
        remain -= take
        if remain == 0:
            break
    assert remain == 0, (q, alpha, remain)
    return total / alpha


def spectral(q):
    return sum(w * es(q, a) for w, a in zip(WEIGHTS, ALPHAS))


def affine_cumulative(weights):
    # C(q)=c+a1*q1+a2*q2, with q3=1-q1-q2.
    c = weights[2]
    return c, weights[0] - weights[2], weights[1] - weights[2]


def constraints_for_cell(alpha, k):
    values, rows = component_masses()
    idx = ALPHAS.index(alpha)
    del idx
    cum = []
    for row in rows:
        running = []
        total = F(0)
        for p in row:
            total += p
            running.append(total)
        cum.append(running)
    prev = [F(0) for _ in rows] if k == 0 else [row[k - 1] for row in cum]
    cur = [row[k] for row in cum]
    beta = 1 - alpha
    cp, ap1, ap2 = affine_cumulative(prev)
    cc, ac1, ac2 = affine_cumulative(cur)
    # a1*q1+a2*q2 <= rhs, with an explanatory label.
    return [
        (ap1, ap2, beta - cp, f"prev@{k}"),
        (-ac1, -ac2, cc - beta, f"cur@{k}"),
    ]


def base_constraints():
    return [
        (F(-1), F(0), F(0), "q1=0"),
        (F(0), F(-1), F(0), "q2=0"),
        (F(1), F(1), F(1), "q3=0"),
    ]


def solve_pair(c1, c2):
    a, b, d, _ = c1
    e, f, g, _ = c2
    det = a * f - b * e
    if det == 0:
        return None
    return ((d * f - b * g) / det, (a * g - d * e) / det)


def feasible(q, constraints):
    q1, q2 = q
    return all(a * q1 + b * q2 <= d for a, b, d, _ in constraints)


def vertices():
    values = merged_values()
    out = {}
    for k1 in range(len(values)):
        for k2 in range(len(values)):
            constraints = base_constraints()
            constraints += constraints_for_cell(ALPHAS[0], k1)
            constraints += constraints_for_cell(ALPHAS[1], k2)
            for i, j in combinations(range(len(constraints)), 2):
                q12 = solve_pair(constraints[i], constraints[j])
                if q12 is None or not feasible(q12, constraints):
                    continue
                q1, q2 = q12
                q3 = 1 - q1 - q2
                if min(q1, q2, q3) < 0:
                    continue
                q = (q1, q2, q3)
                out[q] = (k1, k2)
    return out


if __name__ == "__main__":
    vs = vertices()
    ranked = sorted(((spectral(q), q, cells) for q, cells in vs.items()), reverse=True)
    edge = max(value for value, q, _ in ranked if sum(x > 0 for x in q) <= 2)
    best_value, best_q, best_cells = ranked[0]
    target_q = (F(29412, 97937), F(26879, 97937), F(41646, 97937))
    assert best_q == target_q, (best_q, target_q)
    assert sum(x > 0 for x in best_q) == 3
    assert best_value > edge
    print("j2_best_q", best_q)
    print("j2_best_value", best_value)
    print("j2_best_cells", best_cells)
    print("j2_edge_max", edge)
    print("j2_gap", best_value - edge)
    print("j2_vertices", len(vs))
    print("all_checks_passed")
