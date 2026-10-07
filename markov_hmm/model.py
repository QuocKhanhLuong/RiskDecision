"""Forecast API: observed past and frozen settings only, no simulation imports."""
import logging
import time
import warnings

import numpy as np
from hmmlearn.hmm import GaussianHMM

from continuous_cvar.model import validate_data
from continuous_cvar_face.model import fit_smooth
from continuous_cvar.evaluation import population_smooth
from temporal_risk.models import fixed_weight_fit, statistical_models


class CaptureLog(logging.Handler):
    def __init__(self):
        super().__init__(logging.WARNING)
        self.messages = []

    def emit(self, record):
        self.messages.append(record.getMessage())


def finite_diagnostics(value):
    """Keep invalid-fit evidence serializable without turning it into estimates."""
    if isinstance(value, dict):
        return {k: finite_diagnostics(v) for k, v in value.items()}
    if isinstance(value, list):
        return [finite_diagnostics(v) for v in value]
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value


def stationary_weights(transition):
    a, b = transition[0, 1], transition[1, 0]
    if a + b <= 1e-12:
        raise ValueError('No unique stationary distribution')
    return np.array([b, a]) / (a + b)


def fit_hmm(past, settings):
    """Fit all fixed starts; select by past log likelihood, never evaluation truth."""
    x = validate_data(past)
    if settings['n_components'] != 2:
        raise ValueError('This frozen baseline requires two states')
    center, scale = x.mean(axis=0), x.std(axis=0)
    if np.any(scale < settings['min_scale']):
        raise ValueError('Degenerate feature scale')
    z = (x - center) / scale
    radius = np.sum(z*z, axis=1)
    records, candidates = [], []
    for index, quantile in enumerate(settings['initial_quantiles']):
        started = time.perf_counter()
        record = {'index': index, 'initial_quantile': quantile}
        handler = CaptureLog()
        logger = logging.getLogger('hmmlearn.base')
        logger.addHandler(handler)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            try:
                groups = radius > np.quantile(radius, quantile)
                model = GaussianHMM(
                    n_components=2, covariance_type='full', n_iter=settings['maxiter'],
                    tol=settings['tol'], implementation='scaling', init_params='',
                    params='stmc', startprob_prior=1., transmat_prior=1.,
                    means_weight=0., covars_prior=0., covars_weight=0., random_state=0)
                model.startprob_ = np.full(2, .5)
                persistence = settings['initial_self_transition']
                model.transmat_ = np.array([[persistence, 1-persistence], [1-persistence, persistence]])
                model.means_ = np.array([z[groups == k].mean(axis=0) for k in range(2)])
                model.covars_ = np.array([
                    np.cov(z[groups == k], rowvar=False, bias=True)
                    + settings['initial_covariance_ridge']*np.eye(z.shape[1]) for k in range(2)])
                model.fit(z)
                score, posterior = model.score_samples(z)
                history = np.array(list(model.monitor_.history) + [score])
                gain = np.diff(history)
                eigenvalue = float(np.linalg.eigvalsh(model.covars_).min())
                finite = all(np.isfinite(a).all() for a in
                             [history, model.startprob_, model.transmat_, model.means_, model.covars_, posterior])
                normalized = (np.all(model.startprob_ >= 0) and np.all(model.transmat_ >= 0)
                              and np.isclose(model.startprob_.sum(), 1)
                              and np.allclose(model.transmat_.sum(axis=1), 1))
                monotone = bool(gain.min() >= -settings['negative_gain_tol'])
                admissible = bool(finite and normalized and monotone and eigenvalue > settings['min_eigenvalue'])
                converged = bool(admissible and -settings['negative_gain_tol'] <= gain[-1] <= settings['tol'])
                record.update(admissible=admissible, converged=converged,
                              training_log_likelihood=float(score), iterations=int(model.monitor_.iter),
                              at_iteration_cap=bool(model.monitor_.iter == settings['maxiter']),
                              history=history.tolist(), final_gain=float(gain[-1]),
                              min_gain=float(gain.min()), min_eigenvalue=eigenvalue,
                              effective_occupancy=posterior.sum(axis=0).tolist(),
                              fitted_parameters={'startprob': model.startprob_.tolist(),
                                                 'transition': model.transmat_.tolist(),
                                                 'means': (model.means_*scale + center).tolist(),
                                                 'covariances': (model.covars_*scale[None, :, None]*scale[None, None, :]).tolist()})
                if admissible:
                    candidates.append((score, index, model, posterior[-1]))
            except Exception as exc:
                record.update(admissible=False, converged=False, error=repr(exc))
            finally:
                logger.removeHandler(handler)
                record['warnings'] = [str(w.message) for w in caught] + handler.messages
                record['seconds'] = time.perf_counter() - started
                records.append(finite_diagnostics(record))
    diagnostics = {'restarts': records, 'center': center.tolist(), 'scale': scale.tolist(),
                   'selection_rule': 'maximum admissible past training likelihood', 'selected_index': None}
    if not candidates:
        diagnostics.update(valid=False, converged=False)
        return {}, diagnostics
    score, selected, model, final_posterior = max(candidates, key=lambda item: (item[0], -item[1]))
    mean = model.means_*scale + center
    covariance = model.covars_*scale[None, :, None]*scale[None, None, :]
    next_prob = final_posterior @ model.transmat_
    # A reducible fit may forecast, but stationary control then remains missing.
    forecasts = {'hmm_filtered': {'p': next_prob, 'mu': mean, 'cov': covariance}}
    try:
        forecasts['hmm_stationary'] = {'p': stationary_weights(model.transmat_), 'mu': mean, 'cov': covariance}
    except ValueError as exc:
        diagnostics['stationary_error'] = str(exc)
    diagnostics.update(valid=True, converged=records[selected]['converged'], selected_index=selected,
                       startprob=model.startprob_.tolist(), transition=model.transmat_.tolist(),
                       means=mean.tolist(), covariances=covariance.tolist(),
                       final_posterior=final_posterior.tolist(), next_prob=next_prob.tolist(),
                       training_log_likelihood=float(score))
    return forecasts, diagnostics


def fit_forecasts(past, fit_settings, model_settings, hmm_settings):
    x = validate_data(past)
    distributions, stat_diagnostics = statistical_models(x, model_settings)
    learned, hmm_diagnostics = fit_hmm(x, hmm_settings)
    distributions.update(learned)
    policies = {}
    for policy in ['full512', 'equal512']:
        fit = (fit_smooth(x, model_settings['tau'], fit_settings) if policy == 'full512'
               else fixed_weight_fit(x, model_settings['tau'], fit_settings))
        estimates = {'raw': fit.objective, 'iid_oic': None if fit.correction is None else fit.objective + fit.correction,
                     'hmm_filtered': None, 'hmm_stationary': None}
        for name, distribution in distributions.items():
            estimates[name] = population_smooth(fit.theta, distribution, model_settings['tau'], fit_settings['alpha'])[0]
        policies[policy] = {'theta': fit.theta.tolist(), 'estimates': estimates, 'fit_diagnostics': fit.diagnostics}
    return {'policies': policies, 'hmm': hmm_diagnostics, 'statistical': stat_diagnostics,
            'forecast_distributions': {name: {k: v.tolist() for k, v in params.items()}
                                       for name, params in distributions.items()}}
