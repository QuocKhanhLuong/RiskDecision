"""Population evaluation only. No function here is called during data-only fitting."""
import numpy as np
from scipy.integrate import quad
from scipy.optimize import Bounds, LinearConstraint, minimize
from scipy.special import ndtr
from scipy.stats import norm

from .model import Fit, bounds, geometry_diagnostics, polish


def population_hinge(theta, parameters, alpha=.05):
    w, v = theta[:-1], theta[-1]
    p, mu, covariance = parameters["p"], parameters["mu"], parameters["cov"]
    cov_w = covariance @ w
    variance = cov_w @ w
    sd = np.sqrt(variance)
    mean = -mu @ w
    z = (v-mean)/sd
    survival, density = ndtr(-z), norm.pdf(z)/sd
    stoploss = (mean-v)*survival+sd*norm.pdf(z)
    value = v+float(p @ stoploss)/alpha
    conditional_mean = mu-cov_w*((v-mean)/variance)[:,None]
    gradient = np.r_[p @ (-mu*survival[:,None]+cov_w*(norm.pdf(z)/sd)[:,None])/alpha,
                     1-p@survival/alpha]
    hessian = np.zeros((len(theta), len(theta)))
    for k in range(len(p)):
        cond_cov = covariance[k]-np.outer(cov_w[k], cov_w[k])/variance[k]
        moment = np.outer(np.r_[conditional_mean[k], 1.], np.r_[conditional_mean[k], 1.])
        moment[:-1,:-1] += cond_cov
        hessian += p[k]*density[k]*moment/alpha
    return float(value), gradient, hessian


def population_smooth(theta, parameters, tau, alpha=.05):
    """Exact hinge plus localized softplus smoothing excess; adaptive quadrature."""
    hard = population_hinge(theta, parameters, alpha)[0]
    w, v = theta[:-1], theta[-1]
    p, mu, covariance = parameters["p"], parameters["mu"], parameters["cov"]
    mean = -mu @ w
    sd = np.sqrt(np.einsum("i,kij,j->k", w, covariance, w))
    def integrand(u):
        density = norm.pdf((v+tau*u-mean)/sd)/sd+norm.pdf((v-tau*u-mean)/sd)/sd
        return float(np.logaddexp(0, -u)*(p@density))
    value, error = quad(integrand, 0, 40, epsabs=1e-10, epsrel=1e-10)
    excess = tau*tau*value/alpha
    return float(hard+excess), {"hinge_objective": hard, "smoothing_excess": excess,
                                "quadrature_error": float(tau*tau*error/alpha), "truncation_at": 40}


def population_es(w, parameters, alpha=.05):
    mean = -parameters["mu"] @ w
    sd = np.sqrt(np.einsum("i,kij,j->k", w, parameters["cov"], w))
    lo, hi = float((mean-18*sd).min()), float((mean+18*sd).max())
    for _ in range(70):
        mid = (lo+hi)/2
        if parameters["p"] @ ndtr((mid-mean)/sd) < 1-alpha:
            lo = mid
        else:
            hi = mid
    var = (lo+hi)/2
    return var, population_hinge(np.r_[w,var], parameters, alpha)[0]


def continuous_oracle(parameters, config):
    dim = parameters["mu"].shape[1]
    w = np.full(dim, 1/dim)
    v = population_es(w, parameters, config["alpha"])[0]
    objective = lambda t: population_hinge(t, parameters, config["alpha"])
    lo, hi = bounds(config, dim)
    opt = minimize(lambda t: objective(t)[:2], np.r_[w,v], jac=True, method="SLSQP",
                   bounds=Bounds(lo,hi), constraints=[LinearConstraint(np.r_[np.ones(dim),0][None,:],1,1)],
                   options={"ftol":config["slsqp_ftol"],"maxiter":config["maxiter"]})
    theta = polish(opt.x, objective, config)
    value, gradient, hessian = objective(theta)
    diag, _, _ = geometry_diagnostics(theta, gradient, hessian, config)
    diag.update(optimizer_success=bool(opt.success), optimizer_status=int(opt.status), optimizer_message=str(opt.message))
    # A redundant representation of active constraints blocks our OIC gate, but
    # does not invalidate this convex oracle's global supporting-plane certificate.
    diag['oracle_global_gap_gate']=bool(diag['feasibility']<=config['feasibility_tol'] and
                                       -1e-8<=diag['raw_gap_bound']<=config['gap_tol'])
    if not diag['oracle_global_gap_gate']:
        raise RuntimeError(f"Population oracle gate failed: {diag}")
    return Fit(theta, value, None, diag)
