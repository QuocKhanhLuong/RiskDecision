"""Fixed mathematical diagnostics, separate from the frozen speed matrix.

Predeclared here before execution: 32 mixture points for normal and Student-t3
component laws, R in {3,5}, eight points each, three actions. Construct the fixed
quantile polytope for each action and check a support-two vertex has no smaller
regret. Numerical diagnostics do not replace the arbitrary-law proof.
"""
from fractions import Fraction as F
import hashlib
import importlib.util
from itertools import combinations
import json
from pathlib import Path
import sys
import time

import numpy as np
from scipy.optimize import brentq
from scipy.stats import norm, t as student
from tqdm import tqdm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from mixture_order.run import atomic_json


def risk(q, mu, sigma, family, alpha=.2):
    law = norm if family == 'normal' else student(3)
    def tails(threshold):
        z = (threshold-mu)/sigma
        sf = law.sf(z)
        if family == 'normal':
            excess = sigma*(law.pdf(z)-z*sf)
        else:
            excess = sigma*((3+z*z)/2*law.pdf(z)-z*sf)
        return sf, excess
    threshold = brentq(lambda x: q @ tails(x)[0]-alpha, float(np.min(mu-100*sigma)),
                      float(np.max(mu+100*sigma)), xtol=1e-12)
    sf, excess = tails(threshold)
    return float(threshold+q @ excess/alpha), threshold, sf


def main():
    out = ROOT/'runs/sparse_regret_audit/20261008'
    if (out/'extensions.json').exists():
        raise FileExistsError('do not overwrite extension result')
    start = time.perf_counter()
    seed = int(hashlib.sha256(b'sparse-regret/20261008/continuous-diagnostic-v1').hexdigest()[:16], 16)
    rng = np.random.default_rng(seed)
    records = []
    for family, r in tqdm([(f, r) for f in ('normal', 'student3') for r in (3, 5)], desc='integrable-law checks'):
        mu, sigma = rng.normal(0, 2, (3, r)), rng.uniform(.1, 2., (3, r))
        for index in range(8):
            q = rng.dirichlet(np.ones(r))
            risks = [risk(q, mu[i], sigma[i], family) for i in range(3)]
            base = np.array([v[0] for v in risks])
            for i in range(3):
                sf = risks[i][2]
                candidates = []
                for a, b in combinations(range(r), 2):
                    if sf[a] == sf[b]:
                        continue
                    w = (.2-sf[a])/(sf[b]-sf[a])
                    if 0 <= w <= 1:
                        v = np.zeros(r)
                        v[a], v[b] = 1-w, w
                        candidates.append(v)
                assert candidates
                values = []
                for v in candidates:
                    es = np.array([risk(v, mu[j], sigma[j], family)[0] for j in range(3)])
                    values.append(es[i]-es.min())
                best = int(np.argmax(values))
                gap = values[best]-(base[i]-base.min())
                assert gap >= -2e-9
                records.append(dict(family=family, r=r, point=index, action=i, mu=mu.tolist(),
                                    sigma=sigma.tolist(), q=q.tolist(), witness=candidates[best].tolist(),
                                    regret_at_q=float(base[i]-base.min()), regret_at_witness=values[best],
                                    gain=gap, quantile=risks[i][1]))
    fixture_path = out/'reviews/j2_sharpness_check.py'
    spec = importlib.util.spec_from_file_location('fixture', fixture_path)
    fixture = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture)
    vertices = fixture.vertices()
    scores = [(fixture.spectral(q), q) for q in vertices]
    maximum = max(v for v, _ in scores)
    winners = [q for v, q in scores if v == maximum]
    edge = max(v for v, q in scores if sum(x > 0 for x in q) <= 2)
    assert len(winners) == 1 and sum(x > 0 for x in winners[0]) == 3 and maximum > edge
    body = dict(passed=True, source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                seed=seed, mixture_points=32, action_quantile_checks=len(records),
                minimum_gain=min(v['gain'] for v in records), records=records,
                spectral_sharpness=dict(best=str(maximum), edge=str(edge), gap=str(maximum-edge),
                                        q=list(map(str, winners[0])), unique=True, vertices=len(vertices),
                                        fixture_sha256=hashlib.sha256(fixture_path.read_bytes()).hexdigest()),
                elapsed_seconds=time.perf_counter()-start)
    atomic_json(out/'extensions.json', body)
    print(json.dumps({k: v for k, v in body.items() if k != 'records'}, indent=2))


if __name__ == '__main__':
    main()
