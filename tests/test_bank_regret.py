import json
from pathlib import Path

import numpy as np
import pytest
from numpy.testing import assert_allclose
from scipy.optimize import linprog

from bank_regret.core import (OwnedHull, bank_hull, make_bank, risk_extrema,
                              solve_local, solve_union, solve_worlds)
from bank_regret.run import execute, freeze
from bank_regret.study import (choose_policies, evaluate, fit_observed,
                               generate_history, observed_posterior_seed, public_design)
from mixture_order.core import FiniteMixture, paired_certificate
from mixture_order.run import atomic_json, digest

CFG = json.loads((Path(__file__).parents[1]/'bank_regret/config.json').read_text())


def small_bank(alpha=.05):
    rng = np.random.default_rng(8230)
    return [FiniteMixture(rng.normal(size=9), rng.dirichlet(np.ones(9)),
                          rng.dirichlet(np.ones(9)), alpha) for _ in range(5)]


@pytest.mark.parametrize('alpha', [.01, .05, .2, 1.])
def test_local_union_and_all_pairwise_certificates(alpha):
    laws = small_bank(alpha)
    costs = np.arange(len(laws))*.03
    expected = [max(paired_certificate(a, b)['upper']+costs[i]-costs[j]
                    for j, b in enumerate(laws)) for i, a in enumerate(laws)]
    a, b = solve_local(laws, costs), solve_union(laws, costs)
    assert_allclose(a['regrets'], expected, atol=1e-12)
    assert_allclose(a['regrets'], b['regrets'], atol=1e-12)
    for i, (q, j, gap) in enumerate(zip(a['worst_q'], a['competitor'], a['regrets'])):
        assert_allclose(gap, laws[i].es(q)+costs[i]-laws[j].es(q)-costs[j], atol=1e-12)
    assert a['risk_evaluations'] <= b['risk_evaluations']


def test_competitor_kinks_not_needed_for_action_local_maximum():
    a = FiniteMixture([0, 10], [1, 0], [0, 1], .05)
    b = FiniteMixture([1], [1], [1], .05)
    hull = bank_hull([a, b], [0, 0])
    # Global best curve switches at .005, which is not A's own knot .05.
    assert any(np.isclose(hull.starts, .005))
    assert not any(np.isclose(a.crossings(), .005))
    answer = solve_local([a, b], [0, 0])
    assert_allclose(answer['regrets'], [9, 1])


def test_witness_against_independent_tail_risk_envelope_lp():
    laws = small_bank(.2)
    costs = np.linspace(0, .05, len(laws))
    solved = solve_local(laws, costs, [.07, .92])
    for i, q in enumerate(solved['worst_q']):
        risks = []
        for law in laws:
            p = (1-q)*law.p0+q*law.p1
            lp = linprog(-law.loss, A_eq=np.ones((1, len(p))), b_eq=[1],
                         bounds=list(zip(np.zeros(len(p)), p/law.alpha)), method='highs')
            assert lp.success
            risks.append(-lp.fun)
        net = np.array(risks)+costs
        assert_allclose(solved['regrets'][i], net[i]-net.min(), atol=1e-10)


def test_duplicate_support_parallel_lines_zero_atoms_and_ties():
    law = FiniteMixture([1, 1, 2, 999], [.4, .6, 0, 0], [.1, .2, .7, 0], .2)
    result = solve_local([law, law], [0, 0])
    assert_allclose(result['regrets'], [0, 0], atol=1e-12)
    assert result['selected'] == 0
    hull = OwnedHull([1, 1, 2], [3, 3, 3], [1, 0, 2])
    value, owner = hull.at([0, .5, 1])
    assert_allclose(value, [1, 2.5, 4])
    assert_allclose(owner, 0)


def test_costs_and_mixture_label_symmetry_and_singleton_interval():
    laws = small_bank(.2)
    costs = np.arange(len(laws))*.04
    flipped = [FiniteMixture(x.loss, x.p1, x.p0, x.alpha) for x in laws]
    assert_allclose(solve_local(laws, costs, [.1, .6])['regrets'],
                    solve_local(flipped, costs, [.4, .9])['regrets'], atol=1e-12)
    q = .4
    expected = np.array([law.es(q) for law in laws])+costs
    assert_allclose(solve_local(laws, costs, [q, q])['regrets'], expected-expected.min(), atol=1e-12)
    translated = [FiniteMixture(3*x.loss+7, x.p0, x.p1, x.alpha) for x in laws]
    assert_allclose(solve_local(translated, 3*costs)['regrets'],
                    3*np.array(solve_local(laws, costs)['regrets']), atol=1e-11)


def test_multiworld_uses_one_common_world_for_both_actions():
    law0, law10, law11 = [FiniteMixture([v], [1], [1], .05) for v in [0, 10, 11]]
    worlds = [[law0, law0], [law10, law11]]
    result = solve_worlds(worlds, [0, 0], [[0, 1], [0, 1]])
    assert_allclose(result['regrets'], [0, 1])
    # Independent model-wise max/min would claim 10 for action 0 despite uniform dominance.
    lo, hi = zip(*(risk_extrema(w, [0, 0], [0, 1]) for w in worlds))
    assert_allclose(np.max(hi, axis=0)-np.min(lo), [10, 11])


def test_overflow_and_bad_inputs_fail_closed():
    with pytest.raises(ValueError):
        solve_local([], [])
    laws = small_bank()
    for costs in [[0], np.full(len(laws), np.nan), -np.ones(len(laws))]:
        with pytest.raises(ValueError):
            solve_local(laws, costs)
    with pytest.raises(ValueError):
        solve_worlds([laws], np.zeros(len(laws)), [])
    huge = FiniteMixture([1e308, -1e308], [.5, .5], [.3, .7], .01)
    with pytest.raises(FloatingPointError):
        solve_local([huge], [0])


def test_public_bank_constraints_and_observed_fit_counts():
    design = public_design(CFG)
    w = design['weights']
    assert w.shape == (128, 8) and (w >= 0).all() and (w <= .5).all()
    assert_allclose(w.sum(axis=1), 1)
    history = generate_history(CFG, design, 'stationary', 321, True)
    fit = fit_observed(CFG, history['z'], history['categories'], 713)
    emission = np.array(fit['emission_counts_plus_prior'])
    transition = np.array(fit['transition_counts_plus_prior'])
    assert_allclose(emission.sum(), 512+2*32*.5)
    assert_allclose(transition.sum(), 511+4*.5)
    row = transition[history['z'][-1]]
    assert_allclose(fit['q_mean'], row[1]/row.sum())
    assert_allclose(np.array(fit['worlds']).sum(axis=2), 1)


def test_truth_mutation_cannot_change_fit_or_selected_policy():
    cfg = dict(CFG, policy_bank_size=8, posterior_draw_worlds=1)
    design = public_design(cfg)
    h = generate_history(cfg, design, 'component_shift', 91, True)
    a = fit_observed(cfg, h['z'], h['categories'], 923)
    decision = choose_policies(cfg, design, a, h['categories'])
    locked = digest(decision)
    h['truth']['q'] = 1-h['truth']['q']
    h['truth']['components'] = h['truth']['components'][::-1]
    evaluate(cfg, design, decision, h['truth'])
    b = fit_observed(cfg, h['z'], h['categories'], 923)
    assert digest(a) == digest(b)
    assert digest(decision) == locked
    assert digest(choose_policies(cfg, design, b, h['categories'])) == locked


def test_identical_history_with_different_family_metadata_has_same_policy(monkeypatch):
    from bank_regret import run
    cfg = dict(CFG, policy_bank_size=8, posterior_draw_worlds=1)
    design = public_design(cfg)
    history = generate_history(cfg, design, 'stationary', 999, True)
    monkeypatch.setattr(run, 'generate_history', lambda *args: history)
    a = run.run_policy(cfg, 'stationary', 0, True)
    b = run.run_policy(cfg, 'component_shift', 12345, False)
    assert digest(a['fit']) == digest(b['fit'])
    assert a['decision_lock_sha256'] == b['decision_lock_sha256']
    assert a['fit']['posterior_seed'] == observed_posterior_seed(cfg, history['z'], history['categories'], design)


def test_nearly_parallel_hull_values_at_boundaries_match_direct_lines():
    b = np.array([1., 1.+1e-12, 1.-1e-12, .3])
    m = np.array([1., 1.-2e-12, 1.+2e-12, 2.4])
    hull = OwnedHull(b, m, np.arange(4))
    points = np.r_[0, 1, .5, hull.starts[np.isfinite(hull.starts)]]
    expected = (b[:, None]+m[:, None]*points).min(axis=0)
    value, owner = hull.at(points)
    assert_allclose(value, expected, atol=1e-12)
    assert_allclose(b[owner]+m[owner]*points, expected, atol=1e-12)


def test_resume_and_immutable_checkpoint(tmp_path):
    cfg = dict(CFG, benchmark_banks=[4], benchmark_supports=[4], benchmark_replicates=1,
               timing_repetitions=1, policy_histories_per_family=1, policy_bank_size=4,
               posterior_draw_worlds=1, policy_window=24, shift_at=18, policy_atoms=8,
               bootstrap_repetitions=20)
    pre = {'passed': True, 'fingerprint': 'test'}
    pre['sha256'] = digest(pre)
    atomic_json(tmp_path/'preflight.json', pre)
    first = execute(cfg, 'test', tmp_path, 1)
    assert not first['complete'] and first['cases_done'] == 1
    files = list((tmp_path/'cases').glob('*.json'))
    original = files[0].read_bytes()
    final = execute(cfg, 'test', tmp_path)
    assert final['complete'] and final['all_checks_passed']
    assert files[0].read_bytes() == original
    execute(cfg, 'test', tmp_path)
    assert files[0].read_bytes() == original
    corrupted = json.loads(original)
    corrupted['body']['result']['input_sha256'] = 'wrong'
    corrupted['sha256'] = digest(corrupted['body'])
    atomic_json(files[0], corrupted)
    with pytest.raises(ValueError, match='input recipe'):
        execute(cfg, 'test', tmp_path)


def test_frozen_contract_and_partial_cli_status(tmp_path, monkeypatch):
    cfg, fp = freeze(tmp_path)
    assert freeze(tmp_path)[1] == fp
    value = json.loads((tmp_path/'freeze.json').read_text())
    value['contract']['numpy'] = 'different'
    atomic_json(tmp_path/'freeze.json', value)
    with pytest.raises(ValueError):
        freeze(tmp_path)
    import sys
    from bank_regret import run
    monkeypatch.setattr(sys, 'argv', ['run', 'run', '--out', str(tmp_path), '--max-new-cases', '1'])
    monkeypatch.setattr(run, 'freeze', lambda _: (cfg, fp))
    monkeypatch.setattr(run, 'execute', lambda *args: {'complete': False, 'all_checks_passed': True})
    with pytest.raises(SystemExit) as exit_info:
        run.main()
    assert exit_info.value.code == 3
