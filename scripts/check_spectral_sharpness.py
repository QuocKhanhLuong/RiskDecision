"""Exploratory exact constructions and independent LP checks for all-J sharpness.

This is separate from the frozen one-level assessment. No stochastic inference.
Existing cases are validated and resumed without rewriting their bytes.
"""
from __future__ import annotations

import argparse
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import sys
import time
import warnings

import numpy as np
import scipy
from scipy.optimize import linprog
from tqdm import tqdm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from sparse_regret.rational import linear_solve


def digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()


def dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def construct(j, family):
    n = j+2
    z = list(map(F, range(n)))
    if family == 'uniform':
        alpha = [F(n-k, n) for k in range(1, j+1)]
        weights = [F(1, j)]*j
        pstar = [F(1, n)]*n
    else:
        alpha = [F(j+1-k, j+1) for k in range(1, j+1)]
        weights = [F(2*k, j*(j+1)) for k in range(1, j+1)]
        pstar = [1-alpha[0]]+[alpha[k-1]-alpha[k] for k in range(1, j)]
        pstar += [alpha[-1]/3, 2*alpha[-1]/3]
    planes = [[[t+max(x-t, 0)/a for x in z] for t in z] for a in alpha]
    h = [[planes[k][k][s]-planes[k][k+1][s] for s in range(n)] for k in range(j)]
    g = [sum(weights[k]*(planes[k][k][s]+planes[k][k+1][s])/2 for k in range(j)) for s in range(n)]
    matrix = [[F(1)]*n, g]+h
    v = [linear_solve(matrix, [F(0), F(0)]+[F(k == l) for k in range(j)]) for l in range(j)]
    assert all(row is not None for row in v)
    v.append(tuple(-sum(v[k][s] for k in range(j)) for s in range(n)))
    epsilon = min(pstar)/(2*max(F(1), max(abs(x) for row in v for x in row)))
    p = [[pstar[s]+epsilon*row[s] for s in range(n)] for row in v]
    assert all(sum(row) == 1 and min(row) > 0 for row in p)
    assert all(sum(row[s] for row in p)/len(p) == pstar[s] for s in range(n))
    for l, row in enumerate(v[:-1]):
        assert sum(row) == 0 and dot(g, row) == 0
        assert all(dot(h[k], row) == int(k == l) for k in range(j))
    assert g[-1]-g[-2] == sum(w/a for w, a in zip(weights, alpha))
    optimum = sum(w*min(dot(line, pstar) for line in level) for w, level in zip(weights, planes))
    assert optimum == dot(g, pstar)
    assert all(dot(row, pstar) == 0 for row in h)
    # A conservative strict gap valid for every simplex boundary point.
    gap_lower = epsilon*min(weights)/(2*j)
    return z, alpha, weights, pstar, p, planes, optimum, epsilon, gap_lower


def run_case(task):
    started = time.monotonic()
    j, family = task['j'], task['family']
    z, alpha, weights, pstar, p, planes, optimum, epsilon, gap_lower = construct(j, family)
    r = j+1
    # Maximize the complete spectral risk with J separate RU epigraph variables.
    # No support bound or quantile-cell restriction enters this LP.
    coeff = [0.]*r+[-float(w) for w in weights]
    inequalities = []
    for level, lines in enumerate(planes):
        for line in lines:
            row = [-float(dot(line, component)) for component in p]+[0.]*j
            row[r+level] = 1.
            inequalities.append(row)
    reports, captured = [], []
    with warnings.catch_warnings(record=True) as seen:
        warnings.simplefilter('always')
        for omitted in [None]+list(range(r)):
            bounds = [(0, 0) if k == omitted else (0, None) for k in range(r)]+[(None, None)]*j
            result = linprog(coeff, A_ub=inequalities, b_ub=np.zeros(len(inequalities)),
                             A_eq=[[1.]*r+[0.]*j], b_eq=[1.], bounds=bounds, method='highs',
                             options={'dual_feasibility_tolerance': 1e-9,
                                      'primal_feasibility_tolerance': 1e-9})
            assert result.success, result.message
            primal = max(float(np.max(np.array(inequalities) @ result.x)),
                         abs(sum(result.x[:r])-1), max(0., -min(result.x[:r])))
            if omitted is not None:
                primal = max(primal, abs(result.x[omitted]))
            assert primal < 2e-8
            value = -result.fun
            if omitted is None:
                assert abs(value-float(optimum)) < 2e-8
                assert max(abs(x-1/r) for x in result.x[:r]) < 2e-6
            else:
                assert float(optimum)-value >= float(gap_lower)-2e-8
            reports.append(dict(omitted_component=omitted, value=value,
                                q=list(result.x[:r]), primal_residual=primal))
        captured = [str(w.message) for w in seen]
    return dict(task=task, scope='exploratory construction; mathematical identities exact; LP numerical diagnostic',
                atoms=list(map(str, z)), alpha=list(map(str, alpha)), weights=list(map(str, weights)),
                pstar=list(map(str, pstar)), components=[list(map(str, row)) for row in p],
                epsilon=str(epsilon), exact_maximum=str(optimum), exact_boundary_gap_lower_bound=str(gap_lower),
                lp_results=reports, lp_solves=len(reports), numerical_warnings=captured,
                elapsed_seconds=time.monotonic()-started, passed=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, default=ROOT/'runs/sparse_regret_audit/20261008/sharpness_family')
    parser.add_argument('--max-cases', type=int)
    args = parser.parse_args()
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    tasks = [dict(j=j, family=family) for family in ['uniform', 'unequal'] for j in range(1, 9)]
    freeze = dict(tasks=tasks, scope='exploratory analytic construction, not pre-registered stochastic experiment',
                  source={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in [Path(__file__), ROOT/'sparse_regret/rational.py']},
                  environment=dict(python=sys.version, numpy=np.__version__, scipy=scipy.__version__))
    frozen = out/'freeze.json'
    if frozen.exists():
        assert json.loads(frozen.read_text()) == freeze, 'source/environment changed; use a new run directory'
    else:
        frozen.write_text(json.dumps(freeze, indent=2)+'\n')
    frozen_hash = digest(freeze)
    started = time.monotonic()
    new = resumed = 0
    results = []
    for task in tqdm(tasks, desc='spectral sharpness', unit='case'):
        path = out/f"{task['family']}-{task['j']}.json"
        if path.exists():
            saved = json.loads(path.read_text())
            assert saved['freeze_sha256'] == frozen_hash and digest(saved['result']) == saved['result_sha256']
            assert saved['result']['task'] == task and saved['result']['passed']
            results.append(saved['result'])
            resumed += 1
            continue
        if args.max_cases is not None and new >= args.max_cases:
            continue
        result = run_case(task)
        payload = dict(freeze_sha256=frozen_hash, result_sha256=digest(result), result=result)
        tmp = path.with_suffix('.tmp')
        tmp.write_text(json.dumps(payload, indent=2)+'\n')
        tmp.replace(path)
        results.append(result)
        new += 1
        with (out/'progress.jsonl').open('a') as f:
            f.write(json.dumps(dict(task=task, elapsed_seconds=result['elapsed_seconds'], passed=True))+'\n')
    receipt = dict(completed=len(results), total=len(tasks), new=new, resumed=resumed,
                   lp_solves=sum(row['lp_solves'] for row in results),
                   elapsed_seconds=time.monotonic()-started,
                   warnings=sum(len(row['numerical_warnings']) for row in results),
                   freeze_sha256=frozen_hash, passed=len(results) == len(tasks))
    with (out/'invocations.jsonl').open('a') as f:
        f.write(json.dumps(receipt)+'\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
