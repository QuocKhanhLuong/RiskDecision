"""Small exact-geometry sanity checks for sparse_theory_b.md.

This is an independent review aid, not production code. It enumerates vertices
of finite quantile cells in simplex coordinates and checks support bounds.
"""

from __future__ import annotations

from itertools import combinations, product

import numpy as np


TOL = 1e-9


def merge_components(component_laws):
    values = sorted({float(x) for law in component_laws for x, _ in law})
    rows = []
    for law in component_laws:
        d = {float(x): float(p) for x, p in law}
        rows.append(np.array([d.get(x, 0.0) for x in values], dtype=float))
    return np.array(values), np.array(rows)


def mixture_law(actions, q):
    d = {}
    for qr, law in zip(q, actions):
        for x, p in law:
            d[float(x)] = d.get(float(x), 0.0) + float(qr) * float(p)
    return sorted(d.items())


def es(actions, q, alpha):
    remain = float(alpha)
    total = 0.0
    for x, p in reversed(mixture_law(actions, q)):
        take = min(remain, p)
        total += take * x
        remain -= take
        if remain <= TOL:
            break
    assert remain <= 2e-8, (remain, q, alpha)
    return total / alpha


def action_es_bank(bank, q, alpha):
    return np.array([es(action, q, alpha) for action in bank])


def affine_in_simplex_coords(values, probs):
    """Return c, a for c + a @ x, x=q[:-1], q_last=1-sum(x)."""
    del values
    full = np.asarray(probs, dtype=float).reshape(-1)
    c = float(full[-1])
    a = full[:-1] - full[-1]
    return c, a


def cell_constraints(component_laws, alpha, k):
    values, probs = merge_components(component_laws)
    beta = 1.0 - alpha
    cumulative = np.cumsum(probs, axis=1)
    prev = np.zeros(probs.shape[0]) if k == 0 else cumulative[:, k - 1]
    cur = cumulative[:, k]
    c_prev, a_prev = affine_in_simplex_coords(np.array([1.0]), prev[:, None])
    c_cur, a_cur = affine_in_simplex_coords(np.array([1.0]), cur[:, None])
    # c_prev + a_prev @ x <= beta; beta <= c_cur + a_cur @ x.
    return [
        (a_prev, beta - c_prev, f"C{k}-prev"),
        (-a_cur, c_cur - beta, f"C{k}"),
    ]


def simplex_constraints(r):
    d = r - 1
    out = []
    for j in range(d):
        a = np.zeros(d)
        a[j] = -1.0
        out.append((a, 0.0, f"q{j}=0"))
    out.append((np.ones(d), 1.0, "q_last=0"))
    return out


def cell_vertices(component_laws, alpha, k):
    values, probs = merge_components(component_laws)
    r = probs.shape[0]
    constraints = simplex_constraints(r) + cell_constraints(component_laws, alpha, k)
    d = r - 1
    vertices = []
    for ids in combinations(range(len(constraints)), d):
        A = np.vstack([constraints[j][0] for j in ids])
        b = np.array([constraints[j][1] for j in ids])
        if np.linalg.matrix_rank(A, tol=1e-10) < d:
            continue
        x = np.linalg.solve(A, b)
        if any(float(a @ x - rhs) > 2e-8 for a, rhs, _ in constraints):
            continue
        q = np.r_[x, 1.0 - float(x.sum())]
        if np.min(q) < -2e-8:
            continue
        q = np.maximum(q, 0.0)
        q /= q.sum()
        if not any(np.max(np.abs(q - old)) < 2e-7 for old in vertices):
            vertices.append(q)
    return vertices


def regret(bank, q, alpha):
    vals = action_es_bank(bank, q, alpha)
    return vals - vals.min()


def sharpness_fixture():
    alpha = 0.05
    bank = [
        [[(0.0, 1.0)], [(10.0, 1.0)]],
        [[(1.0, 1.0)], [(11.0, 0.05), (0.0, 0.95)]],
    ]
    q0 = np.array([0.0, 1.0])
    qstar = np.array([0.95, 0.05])
    q1 = np.array([1.0, 0.0])
    assert abs(regret(bank, q0, alpha)[0]) < 1e-10
    assert abs(regret(bank, qstar, alpha)[0] - 8.5) < 1e-10
    assert abs(regret(bank, q1, alpha)[0]) < 1e-10
    print("sharpness_ok", regret(bank, qstar, alpha).tolist())


def constrained_fixture():
    alpha = 0.05
    bank = [
        [[(1.0, 1.0)], [(0.0, 1.0)], [(0.0, 1.0)]],
        [[(0.0, 1.0)], [(0.0, 1.0)], [(0.0, 1.0)]],
    ]
    q = np.array([0.04, 0.86, 0.10])
    assert abs(regret(bank, q, alpha)[0] - 0.8) < 1e-10
    assert np.all(q > 0.0)
    print("constrained_counterexample_ok", regret(bank, q, alpha).tolist())


def random_bank(rng, r=4, m=3, s=4):
    bank = []
    for i in range(m):
        values = np.arange(s, dtype=float) + 10.0 * i
        bank.append([
            [(float(x), float(p)) for x, p in zip(values, rng.dirichlet(np.ones(s)))]
            for _ in range(r)
        ])
    return bank


def check_single_level():
    rng = np.random.default_rng(20261008)
    alpha = 0.2
    bank = random_bank(rng)
    all_vertices = []
    for action in bank:
        action_vertices = []
        values, probs = merge_components(action)
        for k in range(len(values)):
            action_vertices.extend(cell_vertices(action, alpha, k))
        assert action_vertices
        max_support = max(int(np.sum(q > 2e-7)) for q in action_vertices)
        assert max_support <= 2, max_support
        all_vertices.extend(action_vertices)
    vertex_max = max(float(regret(bank, q, alpha).max()) for q in all_vertices)
    sample_max = -np.inf
    for _ in range(20000):
        q = rng.dirichlet(np.ones(4))
        sample_max = max(sample_max, float(regret(bank, q, alpha).max()))
    assert sample_max <= vertex_max + 2e-8, (sample_max, vertex_max)
    print("single_level_R4_ok", "vertex_max", vertex_max, "sample_max", sample_max)


def check_weighted_two_level():
    rng = np.random.default_rng(20261009)
    bank = random_bank(rng, r=4, m=2, s=3)
    alphas = (0.2, 0.5)
    weights = (0.4, 0.6)
    for action in bank:
        values, _ = merge_components(action)
        vertices = []
        # Every product of level cells is one affine cell for the weighted sum.
        cell_lists = [
            [cell_constraints(action, alpha, k) for k in range(len(values))]
            for alpha in alphas
        ]
        for ks in product(*[range(len(values)) for _ in alphas]):
            constraints = simplex_constraints(4)
            for level, k in enumerate(ks):
                constraints += cell_lists[level][k]
            d = 3
            for ids in combinations(range(len(constraints)), d):
                A = np.vstack([constraints[j][0] for j in ids])
                b = np.array([constraints[j][1] for j in ids])
                if np.linalg.matrix_rank(A, tol=1e-10) < d:
                    continue
                x = np.linalg.solve(A, b)
                if any(float(a @ x - rhs) > 2e-8 for a, rhs, _ in constraints):
                    continue
                q = np.r_[x, 1.0 - float(x.sum())]
                if np.min(q) < -2e-8:
                    continue
                q = np.maximum(q, 0.0)
                q /= q.sum()
                if not any(np.max(np.abs(q - old)) < 2e-7 for old in vertices):
                    vertices.append(q)
        assert vertices
        max_support = max(int(np.sum(q > 2e-7)) for q in vertices)
        assert max_support <= 3, max_support
    print("weighted_J2_R4_ok", "max_support", max_support)


if __name__ == "__main__":
    sharpness_fixture()
    constrained_fixture()
    check_single_level()
    check_weighted_two_level()
    print("all_checks_passed")
