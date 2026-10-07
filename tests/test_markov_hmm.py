import copy
import itertools
import json
from pathlib import Path

import numpy as np
import pytest
from numpy.testing import assert_allclose, assert_array_equal
from scipy.special import logsumexp
from scipy.stats import multivariate_normal

from markov_hmm.model import fit_hmm, fit_forecasts, stationary_weights
from markov_hmm.analysis import aggregate
from temporal_risk.dgp import generate

CFG = json.loads((Path(__file__).resolve().parents[1]/'markov_hmm/config.json').read_text())


def independent_filter(past, start, transition, means, covariances):
    emissions = np.column_stack([multivariate_normal.logpdf(past, mean=m, cov=c) for m, c in zip(means, covariances)])
    logprob = np.log(start)
    total = 0.
    for index, emission in enumerate(emissions):
        if index:
            with np.errstate(divide='ignore'):
                logprob = logsumexp(logprob[:, None] + np.log(transition), axis=0)
        logprob += emission
        scale = logsumexp(logprob)
        logprob -= scale
        total += scale
    return np.exp(logprob), total


def test_last_filter_and_next_prediction_against_enumeration():
    from hmmlearn.hmm import GaussianHMM
    start = np.array([.3, .7]); trans = np.array([[.8, .2], [.1, .9]])
    means = np.array([[-1.], [1.]]); covs = np.array([[[.7]], [[1.3]]])
    x = np.array([[.2], [-.7], [.4], [1.2]])
    model = GaussianHMM(2, covariance_type='full', init_params='')
    model.startprob_, model.transmat_, model.means_, model.covars_ = start, trans, means, covs
    score, post = model.score_samples(x)
    terminal = np.zeros(2)
    for states in itertools.product(range(2), repeat=len(x)):
        mass = start[states[0]]
        for t, state in enumerate(states):
            mass *= multivariate_normal.pdf(x[t], mean=means[state], cov=covs[state])
            if t:
                mass *= trans[states[t-1], state]
        terminal[states[-1]] += mass
    assert_allclose(score, np.log(terminal.sum()))
    assert_allclose(post[-1], terminal/terminal.sum())
    assert_allclose(post[-1]@trans, (terminal/terminal.sum())@trans)
    assert not np.allclose(post[-1], post[-1]@trans)


def test_fitted_likelihood_filter_and_training_only_restart_choice():
    x = generate(CFG['development_seeds'][0], CFG)['markov_stationary']['returns'][:512]
    forecasts, diag = fit_hmm(x, CFG['hmm'])
    assert diag['valid'] and diag['converged']
    admissible = [r for r in diag['restarts'] if r['admissible']]
    assert diag['training_log_likelihood'] == max(r['training_log_likelihood'] for r in admissible)
    posterior, loglik = independent_filter(x, np.array(diag['startprob']), np.array(diag['transition']),
                                           diag['means'], diag['covariances'])
    # Training was in standardized coordinates, so include the Jacobian.
    assert_allclose(loglik + len(x)*np.log(diag['scale']).sum(), diag['training_log_likelihood'], atol=1e-8)
    assert_allclose(posterior, diag['final_posterior'], atol=1e-11)
    assert_allclose(posterior@diag['transition'], forecasts['hmm_filtered']['p'], atol=1e-11)
    p = forecasts['hmm_stationary']['p']
    assert_allclose(p@diag['transition'], p, atol=1e-12)
    for forecast in forecasts.values():
        assert np.linalg.eigvalsh(forecast['cov']).min() > 0


def test_iteration_cap_is_not_automatically_convergence():
    x = generate(CFG['development_seeds'][0], CFG)['markov_stationary']['returns'][:512]
    settings = dict(CFG['hmm'], maxiter=1, tol=1e-12)
    forecast, diag = fit_hmm(x, settings)
    assert forecast and diag['valid'] and not diag['converged']
    assert all(r['at_iteration_cap'] for r in diag['restarts'])


def test_forecasts_invariant_to_future_and_latent_state_mutation():
    world = generate(CFG['development_seeds'][0], CFG)['markov_stationary']
    x = world['returns'][:512].copy()
    a = fit_forecasts(x, CFG['fit'], CFG['model'], CFG['hmm'])
    world['returns'][512:] = 1e6; world['states'][:] = 99
    b = fit_forecasts(world['returns'][:512], CFG['fit'], CFG['model'], CFG['hmm'])
    assert a['policies'] == b['policies']
    assert a['forecast_distributions'] == b['forecast_distributions']
    for policy in CFG['policies']:
        assert set(a['policies'][policy]['estimates']) == set(CFG['methods'])
        assert all(v is not None for v in a['policies'][policy]['estimates'].values())
    assert_array_equal(a['policies']['equal512']['theta'][:-1], np.full(8, .125))


def test_reducible_transition_has_no_unique_stationary_control():
    with pytest.raises(ValueError, match='unique'):
        stationary_weights(np.eye(2))


def test_all_invalid_restarts_keep_null_hmm_without_substitution():
    x = generate(CFG['development_seeds'][0], CFG)['markov_stationary']['returns'][:512]
    result = fit_forecasts(x, CFG['fit'], CFG['model'], dict(CFG['hmm'], min_eigenvalue=1e10))
    assert not result['hmm']['valid']
    assert all(p['estimates']['hmm_filtered'] is None for p in result['policies'].values())
    assert all(p['estimates']['gaussian_iid'] is not None for p in result['policies'].values())


def test_path_cluster_aggregation_and_no_complete_case_dropping():
    cfg = copy.deepcopy(CFG); cfg['origins'] = [512, 768]; cfg['bootstrap_reps'] = 30
    rows = []
    for world in cfg['worlds']:
        for seed in [1, 2]:
            for origin in cfg['origins']:
                for policy in cfg['policies']:
                    for method in cfg['methods']:
                        value = seed*(1 if origin == 512 else 3) if method == 'hmm_filtered' else 0.
                        rows.append(dict(world=world, seed=seed, origin=origin, policy=policy, method=method,
                                         conditional_squared_relative_error=value, conditional_signed_relative_error=value,
                                         marginal_squared_relative_error=value, latent_information_gap=0.))
    _, paired, _ = aggregate(rows, cfg, [1, 2])
    primary = next(r for r in paired if r['primary'])
    assert primary['mean'] == 3. and primary['n_clusters'] == 2
    for r in rows:
        if (r['world'], r['seed'], r['origin'], r['policy'], r['method']) == ('markov_stationary', 1, 512, 'full512', 'hmm_filtered'):
            r['conditional_squared_relative_error'] = None
    _, paired, _ = aggregate(rows, cfg, [1, 2])
    assert next(r for r in paired if r['primary'])['status'] == 'INCOMPLETE'
    with pytest.raises(ValueError, match='Missing'):
        aggregate(rows[1:], cfg, [1, 2])


def test_preflight_rejects_seen_seed_in_compressed_export(tmp_path, monkeypatch):
    import gzip
    import markov_hmm.run as runner
    cfg = copy.deepcopy(CFG); cfg['seeds'] = {'start': 77777, 'stop': 77778}; cfg['development_seeds'] = []
    monkeypatch.setattr(runner, 'ROOT', tmp_path)
    monkeypatch.setattr(runner, 'config', lambda: cfg)
    with gzip.open(tmp_path/'old.csv.gz', 'wt') as stream:
        stream.write('seed\n77777\n')
    with pytest.raises(ValueError, match='collision'):
        runner.preflight(tmp_path/'out')


def test_resume_identity_rejects_changed_hmm_settings(tmp_path):
    from markov_hmm.run import HMMRun
    run = HMMRun(tmp_path, CFG, {})
    with run.session():
        run.save('case', {'value': 1})
    changed = copy.deepcopy(CFG); changed['hmm']['tol'] *= 2
    other = HMMRun(tmp_path, changed, {})
    with pytest.raises(ValueError, match='identity changed'):
        with other.session():
            pass
