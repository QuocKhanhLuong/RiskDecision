"""Exhaustive rational cell-polytope vertices: no support-two shortcut."""
from fractions import Fraction as F
from itertools import combinations


def linear_solve(a, b):
    a = [list(row)+[value] for row, value in zip(a, b)]
    n = len(b)
    for k in range(n):
        pivot = next((i for i in range(k, n) if a[i][k]), None)
        if pivot is None:
            return None
        a[k], a[pivot] = a[pivot], a[k]
        scale = a[k][k]
        a[k] = [x/scale for x in a[k]]
        for i in range(n):
            if i != k:
                scale = a[i][k]
                a[i] = [x-scale*y for x, y in zip(a[i], a[k])]
    return tuple(row[-1] for row in a)


def exact_risks(x, p, alpha, costs, q):
    mass = [sum(w*row[s] for w, row in zip(q, p)) for s in range(len(x))]
    return [min(t+sum(prob*max(row[i]-t, 0) for row, prob in zip(x, mass))/alpha
                for t in {row[i] for row in x})+costs[i] for i in range(len(costs))]


def enumerate_cells(losses, probabilities, alpha, costs):
    x = [[F(v) for v in row] for row in losses]
    p = [[F(v) for v in row] for row in probabilities]
    alpha, costs = F(alpha), list(map(F, costs))
    r, m = len(p), len(costs)
    best, witnesses = [F(0)]*m, [tuple([F(1)]+[F(0)]*(r-1)) for _ in costs]
    vertices, systems, max_support = 0, 0, 0
    for i in range(m):
        for t in sorted({row[i] for row in x}):
            above = [sum(row[s] for s in range(len(x)) if x[s][i] > t) for row in p]
            at_least = [sum(row[s] for s in range(len(x)) if x[s][i] >= t) for row in p]
            # All inequalities a.q <= b; enumerate EVERY set of r-1 active
            # inequalities, including both quantile bounds and all nonnegativity.
            inequalities = [tuple(-F(j == k) for j in range(r)) for k in range(r)]
            inequalities += [tuple(above), tuple(-v for v in at_least)]
            rhs = [F(0)]*r+[alpha, -alpha]
            seen = set()
            for active in combinations(range(r+2), r-1):
                systems += 1
                q = linear_solve([tuple([F(1)]*r)]+[inequalities[k] for k in active],
                                 [F(1)]+[rhs[k] for k in active])
                if q is None or q in seen:
                    continue
                if any(sum(a*b for a, b in zip(row, q)) > value for row, value in zip(inequalities, rhs)):
                    continue
                seen.add(q)
                vertices += 1
                max_support = max(max_support, sum(v > 0 for v in q))
                risks = exact_risks(x, p, alpha, costs, q)
                gap = risks[i]-min(risks)
                if gap > best[i]:
                    best[i], witnesses[i] = gap, q
    return {'regrets': list(map(str, best)), 'worst_q': [list(map(str, q)) for q in witnesses],
            'vertices': vertices, 'linear_systems': systems, 'max_support': max_support}
