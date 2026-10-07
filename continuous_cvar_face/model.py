"""Same empirical optimizer; geometry-specific strict-face correction gate."""
import numpy as np
from scipy.linalg import null_space

from continuous_cvar.model import (Fit, bounds, fit_smooth as original_fit,
                                  geometry_diagnostics, probabilities,
                                  smooth_terms, validate_data)


def face_geometry(theta, gradient, hessian, cfg):
    """Certify a stable face of the capped simplex, without unique multipliers."""
    theta = np.asarray(theta)
    dim = len(theta)-1
    lo, hi = bounds(cfg, dim)
    lower = np.flatnonzero(theta[:-1]-lo[:-1] <= cfg['active_tol'])
    upper = np.flatnonzero(hi[:-1]-theta[:-1] <= cfg['active_tol'])
    free = np.setdiff1d(np.arange(dim), np.r_[lower, upper])
    if np.intersect1d(lower, upper).size:
        raise ValueError('Ambiguous lower/upper bound classification')
    # No redundant normal rows are needed to build the minimal-face tangent.
    weight_basis = null_space(np.ones((1,len(free)))) if len(free) else np.empty((0,0))
    n = np.zeros((dim+1, weight_basis.shape[1]+1))
    n[free,:weight_basis.shape[1]] = weight_basis
    n[-1,-1] = 1.
    q = gradient[:-1]
    if len(free):
        lam = -float(q[free].mean())
    elif len(lower) and len(upper):
        lam = -float((q[lower].min()+q[upper].max())/2)
    else:
        raise ValueError('Unsupported singleton/budget-bound geometry')
    lower_mult, upper_mult = q[lower]+lam, -(q[upper]+lam)
    margins = np.r_[lower_mult, upper_mult]
    margin = float(margins.min()) if len(margins) else None
    residual = gradient.copy()
    residual[:-1] += lam
    residual[lower] -= lower_mult
    residual[upper] += upper_mult
    feasibility = float(max(abs(theta[:-1].sum()-1),np.maximum(lo-theta,0).max(),np.maximum(theta-hi,0).max()))
    reduced = n.T@hessian@n
    eigen = np.linalg.eigvalsh(reduced)
    condition = float(eigen[-1]/eigen[0]) if eigen[0]>0 else None
    stationarity = float(np.max(np.abs(residual)))
    original, _, _ = geometry_diagnostics(theta,gradient,hessian,cfg)
    threshold_bound = bool(theta[-1]-lo[-1]<=cfg['active_tol'] or hi[-1]-theta[-1]<=cfg['active_tol'])
    strict = margin is None or margin>cfg['face_margin_tol']
    diag = dict(original)
    diag.update({'original_geometry_gate':original['numerical_gate'],
                 'original_dual_violation':original['dual_violation'],
                 'original_weak_active_set':original['weak_active_set'],
                 'face_free_weights':free.tolist(),'face_dimension':n.shape[1],
                 'face_budget_multiplier':lam,'face_margin':margin,
                 'face_lower_multipliers':lower_mult.tolist(),'face_upper_multipliers':upper_mult.tolist(),
                 'face_strict':strict,'weak_active_set':not strict,
                 'face_stationarity':stationarity,'face_min_eigenvalue':float(eigen[0]),
                 'face_condition':condition,'face_projected_score_mean_norm':float(np.linalg.norm(n.T@gradient)),
                 'face_threshold_bound_active':threshold_bound})
    diag['numerical_gate'] = bool(strict and not threshold_bound and
        feasibility<=cfg['feasibility_tol'] and stationarity<=cfg['stationarity_tol'] and
        -1e-8<=original['raw_gap_bound']<=cfg['gap_tol'] and
        eigen[0]>=cfg['min_eigenvalue'] and condition is not None and condition<=cfg['max_condition'])
    return diag,n,reduced


def correct_locked(past, fit, tau, cfg, p=None):
    """Evaluate a frozen decision; never change the optimizer's theta or objective."""
    x=validate_data(past);prob=probabilities(len(x),p)
    value,gradient,hessian,scores,_=smooth_terms(x,fit.theta,tau,cfg['alpha'],prob)
    if not np.isclose(value,fit.objective,rtol=1e-12,atol=1e-12):
        raise ValueError('Frozen objective mismatch')
    face,n,reduced=face_geometry(fit.theta,gradient,hessian,cfg)
    diag=dict(fit.diagnostics,**face)
    diag.update({'legacy_correction':fit.correction,
                 'legacy_numerical_gate':fit.diagnostics.get('numerical_gate'),
                 'correction_method':'stable_face_kkt',
                 'decision_unchanged':True})
    correction=None
    if diag['numerical_gate']:
        projected=scores@n
        correction=float(np.sum(prob[:,None]*projected*np.linalg.solve(reduced,projected.T).T)/len(x))
        if not np.isfinite(correction) or correction<0:
            diag['numerical_gate']=False;correction=None
    return Fit(fit.theta.copy(),fit.objective,correction,diag)


def fit_smooth(past,tau,config,p=None,initial=None):
    fit=original_fit(past,tau,config,p=p,initial=initial)
    return correct_locked(past,fit,tau,config,p)


def local_influence(past,fit,tau,cfg):
    _,gradient,hessian,scores,_=smooth_terms(past,fit.theta,tau,cfg['alpha'])
    diag,n,reduced=face_geometry(fit.theta,gradient,hessian,cfg)
    if not diag['numerical_gate']:
        raise ValueError('No linear influence on an uncertified/weak face')
    return -np.linalg.solve(reduced,((scores-scores.mean(axis=0))@n).T).T@n.T
