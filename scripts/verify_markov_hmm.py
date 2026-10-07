"""Audit saved HMM fits and targets without refitting or opening new seeds."""
import os
for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
    os.environ[key] = '1'
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
from numpy.testing import assert_allclose, assert_array_equal
from scipy.integrate import quad
from scipy.stats import norm, multivariate_normal
from tqdm import tqdm
from selection_risk.runtime import atomic_json, digest, object_hash
from markov_hmm.run import sources, dependency


def forward(x, start, transition, means, covariances):
    """Independent, row-rescaled probability filter using scipy emission PDFs."""
    logpdf = np.column_stack([multivariate_normal.logpdf(x, mean=m, cov=c) for m, c in zip(means, covariances)])
    post, likelihood = np.array(start), 0.
    for t, row in enumerate(logpdf):
        if t:
            post = post@transition
        offset = row.max()
        mass = post*np.exp(row-offset)
        denominator = mass.sum()
        likelihood += np.log(denominator)+offset
        post = mass/denominator
    return post, likelihood


def direct_objective(theta, law, tau, alpha):
    w, v = theta[:-1], theta[-1]
    value = v
    for p, mu, covariance in zip(law['p'], law['mu'], law['cov']):
        mean, sd = -np.asarray(mu)@w, np.sqrt(w@np.asarray(covariance)@w)
        integral = quad(lambda z: norm.pdf(z)*tau*np.logaddexp(0, (mean+sd*z-v)/tau),
                        -12, 12, epsabs=1e-10, epsrel=1e-10, limit=200)[0]
        value += p*integral/alpha
    return value


def verify(base):
    started = time.perf_counter()
    pilot = base/'pilot'
    audit = json.loads((base/'preflight.json').read_text())
    freeze = json.loads((pilot/'freeze.json').read_text())
    cfg = freeze['identity']['config']
    assert sources() == audit['sources'] == freeze['identity']['sources']
    assert dependency() == audit['dependency'] == freeze['identity']['environment']['hmmlearn']
    assert digest(base/'preflight.json') == freeze['identity']['inputs']['preflight_sha256']
    assert digest(base/'development/benchmark.json') == freeze['identity']['inputs']['benchmark_sha256']
    for path, expected in audit['protected_files'].items():
        assert digest(path) == expected, path
    payloads, arrays, lookup, rows = [], {}, {}, []
    errors = {'likelihood': 0., 'posterior': 0., 'objective': 0., 'truth_filter': 0.}
    restarts = 0
    for path in tqdm(sorted((pilot/'cases').glob('*.json')), desc='verify', unit='origin'):
        saved = json.loads(path.read_text())
        payload = saved['payload']
        assert saved['fingerprint'] == freeze['fingerprint'] and object_hash(payload) == saved['payload_sha256']
        assert payload['status'] == 'COMPLETE'
        seed, world, origin = payload['seed'], payload['world'], payload['origin']
        for artifact, expected in payload['artifacts'].items():
            if artifact not in arrays:
                assert digest(pilot/artifact) == expected
                with np.load(pilot/artifact, allow_pickle=False) as f:
                    arrays[artifact] = {k: f[k] for k in f.files}
                data = arrays[artifact]
                assert_array_equal(data['markov_stationary_returns'][:cfg['dgp']['shift_time']], data['markov_shift_returns'][:cfg['dgp']['shift_time']])
        x = arrays[artifact][world+'_returns'][origin-cfg['window']:origin]
        assert hashlib.sha256(x.tobytes()).hexdigest() == payload['past_sha256']
        locked = payload['locked']; hmm = locked['hmm']
        for restart in hmm['restarts']:
            restarts += 1
            if 'fitted_parameters' not in restart:
                continue
            fitted = restart['fitted_parameters']
            post, likelihood = forward(x, np.array(fitted['startprob']), np.array(fitted['transition']), fitted['means'], fitted['covariances'])
            standardized_likelihood = likelihood + len(x)*np.log(hmm['scale']).sum()
            error = abs(standardized_likelihood-restart['training_log_likelihood'])
            errors['likelihood'] = max(errors['likelihood'], error)
            assert error < 1e-7
            if restart['index'] == hmm['selected_index']:
                errors['posterior'] = max(errors['posterior'], float(np.max(np.abs(post-hmm['final_posterior']))))
                assert_allclose(post, hmm['final_posterior'], atol=1e-10)
                assert_allclose(post@fitted['transition'], hmm['next_prob'], atol=1e-10)
        if hmm['valid']:
            selected = hmm['restarts'][hmm['selected_index']]
            assert selected['training_log_likelihood'] == max(r['training_log_likelihood'] for r in hmm['restarts'] if r['admissible'])
            assert hmm['converged'] == (-cfg['hmm']['negative_gain_tol'] <= selected['final_gain'] <= cfg['hmm']['tol'])
        forecast = locked['forecast_distributions']
        assert_allclose(forecast['gaussian_iid']['mu'][0], x.mean(axis=0), atol=1e-12)
        assert_allclose(forecast['gaussian_iid']['cov'][0], np.cov(x, rowvar=False), atol=1e-12)
        if 'hmm_stationary' in forecast:
            p = np.array(forecast['hmm_stationary']['p'])
            assert_allclose(p@hmm['transition'], p, atol=1e-12)
        # Independent observed-window truth recursion, including change timing.
        transition0, transition1 = np.array(cfg['dgp']['transition0']), np.array(cfg['dgp']['transition1'])
        marginal = np.array([transition0[1, 0], transition0[0, 1]])/(transition0[1, 0]+transition0[0, 1])
        law = payload['evaluation']['conditional']
        emission = np.column_stack([multivariate_normal.logpdf(x, mean=m, cov=c) for m, c in zip(law['mu'], law['cov'])])
        start = origin-len(x)
        for t in range(start+1):
            marginal = marginal@(transition1 if world == 'markov_shift' and t >= cfg['dgp']['shift_time'] else transition0)
        for offset, logpdf in enumerate(emission):
            posterior = marginal*np.exp(logpdf-logpdf.max()); posterior /= posterior.sum()
            t = start+offset+1
            marginal = posterior@(transition1 if world == 'markov_shift' and t >= cfg['dgp']['shift_time'] else transition0)
        errors['truth_filter'] = max(errors['truth_filter'], float(np.max(np.abs(marginal-law['p']))))
        assert_allclose(marginal, law['p'], atol=1e-11)
        for policy, result in locked['policies'].items():
            theta = np.array(result['theta'])
            assert_allclose(theta[:-1].sum(), 1, atol=1e-9)
            assert theta[:-1].min() >= -1e-9 and theta[:-1].max() <= cfg['fit']['weight_cap']+1e-9
            for name, distribution in forecast.items():
                expected = direct_objective(theta, distribution, cfg['model']['tau'], cfg['fit']['alpha'])
                error = abs(expected-result['estimates'][name]); errors['objective'] = max(errors['objective'], error)
                assert error < 2e-7
            target = direct_objective(theta, law, cfg['model']['tau'], cfg['fit']['alpha'])
            raw = theta[-1] + np.mean(cfg['model']['tau']*np.logaddexp(0, (-x@theta[:-1]-theta[-1])/cfg['model']['tau']))/cfg['fit']['alpha']
            assert_allclose(raw, result['estimates']['raw'], atol=1e-11)
            for row in [r for r in payload['rows'] if r['policy'] == policy]:
                assert_allclose(row['conditional_objective'], target, atol=2e-7)
                if row['estimate'] is not None:
                    assert_allclose(row['conditional_squared_relative_error'], (row['estimate']/row['conditional_objective']-1)**2, atol=1e-12)
        payloads.append(payload); rows.extend(payload['rows']); lookup[seed, world, origin] = payload
    for seed in range(cfg['seeds']['start'], cfg['seeds']['stop']):
        for origin in cfg['origins']:
            if origin <= cfg['dgp']['shift_time']:
                a = lookup[seed, 'markov_stationary', origin]['locked']
                b = lookup[seed, 'markov_shift', origin]['locked']
                assert a['forecast_distributions'] == b['forecast_distributions']
                assert a['policies'] == b['policies']
    seeds = list(range(cfg['seeds']['start'], cfg['seeds']['stop']))
    assert len(payloads) == len(seeds)*len(cfg['worlds'])*len(cfg['origins'])
    cells = {(r['world'], r['seed'], r['origin'], r['policy'], r['method']): r for r in rows}
    assert len(cells) == len(rows) == len(payloads)*len(cfg['policies'])*len(cfg['methods'])
    paired = list(csv.DictReader((pilot/'paired.csv').open()))
    indices = np.random.default_rng(cfg['bootstrap_seed']).integers(len(seeds), size=(cfg['bootstrap_reps'], len(seeds)))
    for contrast in paired:
        origins = [o for o in cfg['origins'] if contrast['period'] == 'all' or (o < cfg['dgp']['shift_time']) == (contrast['period'] == 'before')]
        values = []
        for seed in seeds:
            differences = []
            for origin in origins:
                key = contrast['world'], seed, origin, contrast['policy']
                a = cells[*key, contrast['method']][contrast['metric']]
                b = cells[*key, contrast['baseline']][contrast['metric']]
                differences.append(None if a is None or b is None else a-b)
            values.append(None if None in differences else np.mean(differences))
        if None in values:
            assert contrast['status'] == 'INCOMPLETE'
        else:
            values = np.array(values)
            lo, hi = np.quantile(values[indices].mean(axis=1), [.025, .975])
            assert_allclose([float(contrast[k]) for k in ['mean', 'ci_low', 'ci_high']], [values.mean(), lo, hi], atol=1e-12)
    result = dict(status='PASS', cases=len(payloads), rows=len(rows), path_clusters=len(seeds),
                  restart_scores_checked=restarts, paired_contrasts_checked=len(paired), max_errors=errors,
                  protected_files_unchanged=len(audit['protected_files']), seconds=time.perf_counter()-started,
                  verifier_sha256=digest(__file__), scope='numerical/software audit, no refitting; not independent peer review')
    atomic_json(base/'verification.json', result)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    verify(parser.parse_args().out)
