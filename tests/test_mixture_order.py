import json
from pathlib import Path

import numpy as np
import pytest
from numpy.testing import assert_allclose
from scipy.optimize import linprog

from mixture_order.core import (FiniteMixture, LowerEnvelope, ar_analytic,
                                hull_certificate, paired_certificate, rational_witness, ru_envelope)
from mixture_order.run import atomic_json, digest, execute, freeze, read_checkpoint


def witness():
    return (FiniteMixture([0, 10], [1, 0], [0, 1], .05),
            FiniteMixture([0, 1, 11], [0, 1, 0], [.95, 0, .05], .05))


def lp_tail(x, p, alpha):
    # Independent risk-envelope LP: sup sum z_i*x_i, 0<=z_i<=p_i/alpha, sum z=1.
    solution = linprog(-np.array(x), A_eq=np.ones((1, len(x))), b_eq=[1],
                       bounds=list(zip(np.zeros(len(x)), np.array(p)/alpha)), method='highs')
    assert solution.success
    return -solution.fun


def test_exact_witness_and_interior_reversal():
    assert [r['difference'] for r in rational_witness()] == ['-1', '17/2', '-1']
    a, b = witness()
    cert = paired_certificate(a, b)
    assert_allclose([cert['upper'], cert['argmax'], cert['endpoint_upper']], [8.5, .05, -1])
    assert_allclose(hull_certificate(a, b)['upper'], 8.5)
    assert_allclose(cert['independent_upper'], 9)
    # Common-q is materially less conservative than separate max/min.
    assert cert['upper'] < cert['independent_upper']


@pytest.mark.parametrize('alpha', [.01, .05, .3, 1.])
def test_atoms_zero_masses_and_ties_against_independent_lp(alpha):
    law = FiniteMixture([-4, 2, 2, 10, 999], [.7, .1, .2, 0, 0], [0, .05, .9, .05, 0], alpha)
    for q in [0, .002, .3, .9, 1]:
        expected = lp_tail(law.loss, (1-q)*law.p0+q*law.p1, alpha)
        assert_allclose(law.es(q), expected, atol=1e-10)
        assert_allclose(ru_envelope(law)(q), expected, atol=1e-10)


def test_generic_hull_against_all_pair_intersections():
    rng = np.random.default_rng(701)
    b, m = rng.normal(size=(2, 24))
    # Add duplicate/parallel lines and inactive lines deliberately.
    b, m = np.r_[b, b[0], b[0]+20], np.r_[m, m[0], m[0]]
    hull = LowerEnvelope(b, m)
    q = np.r_[np.linspace(-10, 10, 81), hull.starts[np.isfinite(hull.starts)]]
    assert_allclose(hull(q), (b[:, None]+m[:, None]*q).min(axis=0), atol=1e-10)


def test_certificate_global_against_all_ru_line_intersections():
    rng = np.random.default_rng(991)
    a, b = [FiniteMixture(rng.normal(size=11), rng.dirichlet(np.ones(11)),
                          rng.dirichlet(np.ones(11)), .2) for _ in range(2)]
    candidates = [0., 1.]
    raw_lines = []
    for law in (a, b):
        # Independent O(S^2) direct RU threshold costs, including inactive lines.
        b0 = np.array([t + np.maximum(law.loss-t, 0)@law.p0/law.alpha for t in law.loss])
        b1 = np.array([t + np.maximum(law.loss-t, 0)@law.p1/law.alpha for t in law.loss])
        slope = b1-b0
        raw_lines.append((b0, slope))
        for i in range(len(b0)):
            for j in range(i):
                if slope[i] != slope[j]:
                    q = (b0[j]-b0[i])/(slope[i]-slope[j])
                    if 0 <= q <= 1:
                        candidates.append(q)
    q = np.array(candidates)
    risks = [(c[:, None]+m[:, None]*q).min(axis=0) for c, m in raw_lines]
    assert_allclose(paired_certificate(a, b)['upper'], max(risks[0]-risks[1]), atol=1e-10)
    assert_allclose(hull_certificate(a, b)['upper'], max(risks[0]-risks[1]), atol=1e-10)


def test_state_label_permutation_scaling_translation_and_degenerate_interval():
    a, b = witness()
    swapped = [FiniteMixture(x.loss, x.p1, x.p0, x.alpha) for x in (a, b)]
    assert_allclose(paired_certificate(*swapped)['upper'], 8.5)
    assert_allclose(paired_certificate(*swapped)['argmax'], .95)
    transformed = [FiniteMixture(3*x.loss-7, x.p0, x.p1, x.alpha) for x in (a, b)]
    assert_allclose(paired_certificate(*transformed)['upper'], 3*8.5)
    cert = paired_certificate(a, b, .1, .1)
    assert_allclose(cert['upper'], a.es(.1)-b.es(.1))
    assert len(cert['knots']) == 1
    assert_allclose(paired_certificate(a, a)['upper'], 0)


def test_identical_states_and_single_atom():
    law = FiniteMixture([2, -1], [.2, .8], [.2, .8], .3)
    assert_allclose(law.crossings(), [0, 1])
    assert_allclose(law.es([0, .5, 1]), [1, 1, 1])
    one = FiniteMixture([5], [1], [1], 1.)
    assert_allclose(one.es([0, .5, 1]), 5)


def test_fixed_threshold_affine_null_and_difference_is_not_es_of_difference():
    a, b = witness()
    q = np.linspace(0, 1, 101)
    # Locked v_A=v_B=1: expectation of the RU objective remains affine.
    values = []
    for law in (a, b):
        excess = np.maximum(law.loss-1, 0)
        values.append(1+((1-q)*(excess@law.p0)+q*(excess@law.p1))/law.alpha)
    diff = values[0]-values[1]
    assert_allclose(diff.max(), max(diff[0], diff[-1]))
    # At q=.05, joint scenarios: (0,1), (10,0), (10,11).
    contrast = FiniteMixture([-1, 10, -1], [.95, .0475, .0025], [.95, .0475, .0025], .05)
    assert_allclose(contrast.es(0), 9.45)
    assert not np.isclose(contrast.es(0), a.es(.05)-b.es(.05))


@pytest.mark.parametrize('args', [([], [], [], .05), ([1], [1], [1], 0),
                                  ([1], [1], [1], 1.1), ([1], [-1], [1], .05),
                                  ([1], [.9], [1], .05), ([np.nan], [1], [1], .05),
                                  ([[1]], [[1]], [[1]], .05)])
def test_reject_invalid_laws(args):
    with pytest.raises(ValueError):
        FiniteMixture(*args)


def test_reject_invalid_queries():
    a, b = witness()
    for q in [-.01, 1.01, np.nan]:
        with pytest.raises(ValueError):
            a.es(q)
    for interval in [(-1, 1), (.9, .1), (0, np.inf)]:
        with pytest.raises(ValueError):
            paired_certificate(a, b, *interval)
    with pytest.raises(ValueError):
        paired_certificate(a, FiniteMixture([1], [1], [1], .1))


def test_extreme_finite_losses_fail_closed_on_intermediate_overflow():
    law = FiniteMixture([1e308, -1e308], [.5, .5], [.4, .6], .01)
    with pytest.raises(FloatingPointError):
        hull_certificate(law, law)
    with pytest.raises(ValueError):
        LowerEnvelope([np.inf], [0.])


@pytest.mark.parametrize('length,phi', [(1, 0), (8, -.8), (32, 0), (32, .5), (32, .9), (512, .9)])
def test_ar_finite_bias_and_conditional_variance(length, phi):
    r = ar_analytic(length, phi)
    assert_allclose(r['trace_delta'], r['delta'], atol=1e-12)
    assert r['gap_variance'] > 0
    assert r['conditional_mse']['finite'] <= r['conditional_mse']['infinite']+1e-14
    assert r['conditional_mse']['finite'] > r['oracle_conditional_mse']
    if phi == 0:
        assert_allclose(r['delta'], 1/length)
        # Independent Gaussian mean and sample variance: [1+(T-1)]/(2T^2).
        assert_allclose(r['gap_variance'], 1/(2*length))


def test_ar_half_loss_identity_on_arbitrary_history():
    x = np.array([1., -2., .3, 2.5])
    phi = .7
    t = len(x)
    u = np.full(t, 1/t)
    a = u.copy()
    a[-1] -= phi
    matrix = .5*(np.outer(a, a)-np.eye(t)/t+np.outer(u, u))
    gap = .5*((x.mean()-phi*x[-1])**2+1-phi**2)-.5*np.mean((x-x.mean())**2)
    assert_allclose(gap, x@matrix@x+.5*(1-phi**2))


def test_resume_preserves_completed_cases_and_rejects_corruption(tmp_path):
    config = json.loads((Path(__file__).parents[1]/'mixture_order/config.json').read_text())
    config.update(mixture_cases=2, ar_lengths=[], ar_phi=[])
    pre = {'passed': True, 'fingerprint': 'unit-test'}
    pre['sha256'] = digest(pre)
    atomic_json(tmp_path/'preflight.json', pre)
    first = execute(config, 'unit-test', tmp_path, max_new_cases=1)
    assert not first['complete'] and first['cases_done'] == 1
    checkpoint = tmp_path/'cases/mixture-0000.json'
    original = checkpoint.read_bytes()
    second = execute(config, 'unit-test', tmp_path)
    assert second['complete'] and second['cases_done'] == 2
    assert checkpoint.read_bytes() == original
    snapshots = {p.name: p.read_bytes() for p in (tmp_path/'cases').glob('*.json')}
    execute(config, 'unit-test', tmp_path)
    assert snapshots == {p.name: p.read_bytes() for p in (tmp_path/'cases').glob('*.json')}
    with pytest.raises(ValueError, match='identity'):
        read_checkpoint(checkpoint, 'changed', 'mixture-0000')
    data = json.loads(original)
    data['body']['result']['certificate']['upper'] += 1
    atomic_json(checkpoint, data)
    with pytest.raises(ValueError, match='hash mismatch'):
        execute(config, 'unit-test', tmp_path)
    # Even recomputing the outer hash cannot substitute a different seed's laws.
    data = json.loads(original)
    data['body']['result']['inputs']['laws'][0]['loss'][0] += 1
    data['sha256'] = digest(data['body'])
    atomic_json(checkpoint, data)
    with pytest.raises(ValueError, match='inputs differ'):
        execute(config, 'unit-test', tmp_path)


def test_incomplete_cli_is_distinct_from_success(monkeypatch, tmp_path):
    import sys
    from mixture_order import run
    monkeypatch.setattr(sys, 'argv', ['run', 'run', '--out', str(tmp_path), '--max-new-cases', '1'])
    monkeypatch.setattr(run, 'freeze', lambda out: ({}, 'test'))
    monkeypatch.setattr(run, 'execute', lambda *args: {'complete': False, 'all_checks_passed': True})
    with pytest.raises(SystemExit) as status:
        run.main()
    assert status.value.code == 3


def test_freeze_rejects_altered_contract(tmp_path):
    _, fingerprint = freeze(tmp_path)
    _, same = freeze(tmp_path)
    assert fingerprint == same
    receipt = json.loads((tmp_path/'freeze.json').read_text())
    receipt['contract']['numpy'] = 'tampered'
    atomic_json(tmp_path/'freeze.json', receipt)
    with pytest.raises(ValueError, match='changed'):
        freeze(tmp_path)
