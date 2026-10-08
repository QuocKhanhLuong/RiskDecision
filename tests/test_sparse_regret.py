from fractions import Fraction as F

import numpy as np
import pytest

from sparse_regret.core import SimplexBank, solve_edges, solve_lp, witness_error
from sparse_regret.rational import enumerate_cells


def test_exact_sharpness_and_duplicate_components():
    x = [[0, 1], [10, 11], [10, 0]]
    p = [[1, 0, 0], [0, .05, .95], [1, 0, 0], [0, .05, .95]]
    bank = SimplexBank(x, p, .05, [0, 0])
    edge, lp = solve_edges(bank), solve_lp(bank)
    assert edge['regrets'][0] == pytest.approx(8.5)
    assert lp['regrets'] == pytest.approx(edge['regrets'], abs=1e-10)
    assert witness_error(bank, edge) < 1e-10
    assert max(sum(v > 0 for v in q) for q in edge['worst_q']) <= 2


@pytest.mark.parametrize('alpha', [.01, .2, 1.])
@pytest.mark.parametrize('r', [1, 3, 5])
def test_against_unrestricted_simplex_lp(alpha, r):
    rng = np.random.default_rng(108+r)
    x = rng.integers(-3, 5, (7, 4)).astype(float)
    p = rng.integers(0, 6, (r, 7)).astype(float)
    p /= p.sum(axis=1, keepdims=True)
    bank = SimplexBank(x, p, alpha, [0., .05, .2, .1])
    edge, union, lp = solve_edges(bank), solve_edges(bank, 'union'), solve_lp(bank)
    assert edge['regrets'] == pytest.approx(lp['regrets'], abs=1e-8)
    assert edge['regrets'] == pytest.approx(union['regrets'], abs=1e-10)
    assert witness_error(bank, edge) < 1e-9
    assert witness_error(bank, lp) < 1e-8


def test_full_rational_vertex_enumeration():
    x = [[-2, 1], [0, 0], [3, 2], [3, -1]]
    p = [[F(1, 4)]*4, [F(1, 2), 0, 0, F(1, 2)], [0, 0, F(1, 3), F(2, 3)]]
    exact = enumerate_cells(x, p, F(1, 5), [0, F(1, 10)])
    edge = solve_edges(SimplexBank(x, p, .2, [0, .1]))
    assert edge['regrets'] == pytest.approx([float(F(v)) for v in exact['regrets']], abs=1e-10)
    assert exact['max_support'] <= 2


def test_costs_single_action_and_translation():
    bank = SimplexBank([[1], [-2]], [[.4, .6], [.8, .2]], .5, [3])
    assert solve_edges(bank)['regrets'] == pytest.approx([0])
    assert solve_lp(bank)['regrets'] == [0]
    base = SimplexBank([[1, 3], [4, -2]], [[.4, .6], [.8, .2]], .5, [0, .1])
    shifted = SimplexBank(base.x+7, base.p, .5, base.costs)
    assert solve_edges(base)['regrets'] == pytest.approx(solve_edges(shifted)['regrets'], abs=1e-10)


def test_reject_invalid_or_constrained_inputs():
    for p, alpha, cost in [([[.3, .4]], .2, [0]), ([[1., 0]], 0., [0]),
                           ([[1., 0]], .2, [-1]), ([[float('nan'), 0]], .2, [0])]:
        with pytest.raises(ValueError):
            SimplexBank([[1], [2]], p, alpha, cost)
    bank = SimplexBank([[1], [2]], [[.5, .5]], .2, [0])
    with pytest.raises(TypeError):
        solve_edges(bank, constraints={'q1': .2})
    with pytest.raises(ValueError):
        bank.risks([.5])


def test_resume_receipt_detects_corruption_and_never_overwrites(tmp_path):
    import gzip
    import json
    from sparse_regret.run import save_case, read_case
    from mixture_order.run import digest
    path = tmp_path/'case.json.gz'
    task, inp = {'id': 'unit'}, {'p': [1]}
    result = {'task': task, 'input': inp, 'input_sha256': digest(inp)}
    save_case(path, 'freeze', result)
    original = path.read_bytes()
    assert read_case(path, 'freeze', task) == result
    assert path.read_bytes() == original
    with pytest.raises(FileExistsError):
        save_case(path, 'freeze', result)
    with pytest.raises(ValueError):
        read_case(path, 'different', task)
    payload = json.loads(gzip.decompress(original))
    payload['body']['result']['input']['p'] = [0]
    path.write_bytes(gzip.compress(json.dumps(payload).encode()))
    with pytest.raises(ValueError):
        read_case(path, 'freeze', task)
