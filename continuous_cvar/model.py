"""Past-only convex fitting, KKT diagnostics and local optimism correction."""
from dataclasses import dataclass

import numpy as np
from scipy.linalg import null_space
from scipy.optimize import Bounds, LinearConstraint, linprog, minimize
from scipy.special import expit


def validate_data(x):
    x = np.asarray(x, dtype=float)
    if x.ndim != 2 or len(x) <= x.shape[1] or not np.isfinite(x).all():
        raise ValueError("Expected finite past observations, n > dimension")
    return x


def probabilities(n, p=None):
    p = np.full(n, 1/n) if p is None else np.asarray(p, dtype=float)
    if p.shape != (n,) or not np.isfinite(p).all() or (p < 0).any() or not np.isclose(p.sum(), 1):
        raise ValueError("Invalid sample probabilities")
    return p


def smooth_terms(x, theta, tau, alpha=.05, p=None):
    if tau <= 0 or not 0 < alpha < 1:
        raise ValueError("Positive fixed smoothing and valid tail probability required")
    x = validate_data(x)
    theta = np.asarray(theta, dtype=float)
    if theta.shape != (x.shape[1]+1,) or not np.isfinite(theta).all():
        raise ValueError("Invalid decision")
    p = probabilities(len(x), p)
    a = np.column_stack((-x, -np.ones(len(x))))
    z = (a @ theta)/tau
    s = expit(z)
    values = theta[-1] + tau*np.logaddexp(0, z)/alpha
    scores = s[:,None]*a/alpha
    scores[:,-1] += 1
    curvature = p*expit(z)*expit(-z)/(alpha*tau)
    return float(p @ values), p @ scores, a.T @ (curvature[:,None]*a), scores, values


def bounds(config, dim):
    return np.r_[np.zeros(dim), config["threshold_bounds"][0]], np.r_[np.full(dim, config["weight_cap"]), config["threshold_bounds"][1]]


def active_geometry(theta, config):
    dim = len(theta)-1
    lo, hi = bounds(config, dim)
    lower = np.flatnonzero(theta-lo <= config["active_tol"])
    upper = np.flatnonzero(hi-theta <= config["active_tol"])
    normals = [np.r_[np.ones(dim), 0.]]
    for j in lower:
        normals.append(-np.eye(dim+1)[j])
    for j in upper:
        normals.append(np.eye(dim+1)[j])
    c = np.array(normals)
    return c, null_space(c), lower, upper


def linear_minimum(gradient, config):
    """Min g.theta on the common capped simplex and threshold interval."""
    cap = config["weight_cap"]
    remaining, result = 1., 0.
    for j in np.argsort(gradient[:-1]):
        allocation = min(remaining, cap)
        result += allocation*gradient[j]
        remaining -= allocation
        if remaining <= 1e-14:
            break
    if remaining > 1e-12:
        raise ValueError("Infeasible cap/budget")
    v = config["threshold_bounds"][0 if gradient[-1] >= 0 else 1]
    return float(result+v*gradient[-1])


def geometry_diagnostics(theta, gradient, hessian, config):
    c, n, lower, upper = active_geometry(theta, config)
    multipliers = np.linalg.lstsq(c.T, -gradient, rcond=None)[0]
    residual = float(np.max(np.abs(gradient+c.T@multipliers)))
    lo, hi = bounds(config, len(theta)-1)
    feasibility = max(abs(theta[:-1].sum()-1), float(np.maximum(lo-theta, 0).max()), float(np.maximum(theta-hi, 0).max()))
    reduced = n.T @ hessian @ n
    eigen = np.linalg.eigvalsh(reduced) if n.shape[1] else np.array([1.])
    condition = float(eigen[-1]/eigen[0]) if eigen[0] > 0 else None
    bound_mult = multipliers[1:]
    slacks = np.r_[theta[lower]-lo[lower], hi[upper]-theta[upper]]
    dual_violation = float(max(0., -bound_mult.min())) if len(bound_mult) else 0.
    gap = float(gradient @ theta-linear_minimum(gradient, config))
    diag = {"feasibility": float(feasibility), "stationarity": residual,
            "dual_violation": dual_violation,
            "complementarity": float(np.max(np.abs(bound_mult*slacks))) if len(slacks) else 0.,
            "convex_gap_bound": max(0., gap), "raw_gap_bound": gap,
            "constraint_rank": int(np.linalg.matrix_rank(c)), "constraint_rows": len(c),
            "tangent_dimension": n.shape[1], "min_tangent_eigenvalue": float(eigen[0]),
            "tangent_condition": condition, "active_lower": lower.tolist(), "active_upper": upper.tolist(),
            "multipliers": multipliers.tolist(),
            "min_active_multiplier": float(bound_mult.min()) if len(bound_mult) else None,
            "weak_active_set": bool(len(bound_mult) and bound_mult.min() <= config["weak_multiplier_tol"]),
            "threshold_bound_active": bool(len(theta)-1 in lower or len(theta)-1 in upper),
            "projected_score_mean_norm": float(np.linalg.norm(n.T @ gradient))}
    diag["numerical_gate"] = bool(feasibility <= config["feasibility_tol"] and
        residual <= config["stationarity_tol"] and dual_violation <= config["stationarity_tol"] and
        -1e-8 <= gap <= config["gap_tol"] and eigen[0] >= config["min_eigenvalue"] and
        condition is not None and condition <= config["max_condition"] and
        diag["constraint_rank"] == len(c) and not diag["threshold_bound_active"])
    return diag, n, reduced


def polish(theta, objective, config):
    """Projected Newton steps on the current active face, with feasible line search."""
    theta = theta.copy()
    lo, hi = bounds(config, len(theta)-1)
    for _ in range(config["newton_polish_steps"]):
        value, gradient, hessian = objective(theta)[:3]
        _, n, _, _ = active_geometry(theta, config)
        if n.shape[1] == 0 or np.linalg.norm(n.T@gradient) < 1e-11:
            break
        try:
            direction = -n @ np.linalg.solve(n.T@hessian@n, n.T@gradient)
        except np.linalg.LinAlgError:
            break
        descent = float(gradient @ direction)
        if descent >= 0:
            break
        scale = 1.
        for j, d in enumerate(direction):
            if d > 1e-14:
                scale = min(scale, max(0., (hi[j]-theta[j])/d))
            elif d < -1e-14:
                scale = min(scale, max(0., (lo[j]-theta[j])/d))
        accepted = False
        for _ in range(25):
            trial = theta+scale*direction
            if objective(trial)[0] <= value + 1e-4*scale*descent + 1e-14:
                theta = trial
                accepted = True
                break
            scale *= .5
        if not accepted:
            break
    return theta


@dataclass
class Fit:
    theta: np.ndarray
    objective: float
    correction: float | None
    diagnostics: dict


def fit_smooth(past, tau, config, p=None, initial=None):
    x = validate_data(past)
    dim = x.shape[1]
    prob = probabilities(len(x), p)
    objective = lambda theta: smooth_terms(x, theta, tau, config["alpha"], prob)
    theta0 = np.r_[np.full(dim, 1/dim), np.quantile(-x.mean(axis=1), 1-config["alpha"])] if initial is None else np.asarray(initial).copy()
    lo, hi = bounds(config, dim)
    theta0[-1] = np.clip(theta0[-1], lo[-1], hi[-1])
    budget = np.r_[np.ones(dim), 0.][None,:]
    opt = minimize(lambda t: objective(t)[:2], theta0, jac=True, method="SLSQP",
                   bounds=Bounds(lo, hi), constraints=[LinearConstraint(budget, 1, 1)],
                   options={"ftol": config["slsqp_ftol"], "maxiter": config["maxiter"]})
    theta = polish(opt.x, objective, config)
    value, gradient, hessian, scores, _ = objective(theta)
    diag, n, reduced = geometry_diagnostics(theta, gradient, hessian, config)
    diag.update({"optimizer_success": bool(opt.success), "optimizer_status": int(opt.status),
                 "optimizer_message": str(opt.message), "optimizer_iterations": int(opt.nit),
                 "n_fit": len(x), "tau": tau, "probability_weighted_fit": p is not None})
    correction = None
    if diag["numerical_gate"]:
        projected = scores @ n
        correction = float(np.sum(prob[:,None]*projected*np.linalg.solve(reduced, projected.T).T)/len(x))
        # Formula discrepancy diagnostic only, never the implemented estimator.
        projection = n @ n.T
        bracketed = projection @ np.linalg.pinv(hessian) @ projection
        diag["bracketed_inverse_correction_diagnostic"] = float(np.sum(prob[:,None]*scores*(scores@bracketed))/len(x))
        diag["influence_residual"] = float(np.linalg.norm(reduced @ np.linalg.solve(reduced, projected.T)-projected.T, ord=np.inf))
        if not np.isfinite(correction) or correction < -1e-12:
            diag["numerical_gate"] = False
            correction = None
    return Fit(theta, value, correction, diag)


def local_influence(past, fit, tau, config):
    _, _, hessian, scores, _ = smooth_terms(past, fit.theta, tau, config["alpha"])
    _, n, _, _ = active_geometry(fit.theta, config)
    centered = scores-scores.mean(axis=0)
    return -np.linalg.solve(n.T@hessian@n, (centered@n).T).T @ n.T


def fit_empirical_lp(past, config):
    x = validate_data(past)
    n, dim = x.shape
    c = np.r_[np.zeros(dim), 1., np.full(n, 1/(n*config["alpha"]))]
    a = np.column_stack((-x, -np.ones(n), -np.eye(n)))
    budget = np.r_[np.ones(dim), np.zeros(n+1)][None,:]
    opt = linprog(c, A_ub=a, b_ub=np.zeros(n), A_eq=budget, b_eq=[1.],
                  bounds=[(0, config["weight_cap"])]*dim+[tuple(config["threshold_bounds"])]+[(0,None)]*n,
                  method="highs", options={"primal_feasibility_tolerance": 1e-9, "dual_feasibility_tolerance": 1e-9})
    if not opt.success:
        raise RuntimeError(f"CVaR LP failed: {opt.message}")
    residual = c-a.T@opt.ineqlin.marginals-budget.T@opt.eqlin.marginals-opt.lower.marginals-opt.upper.marginals
    diag = {"optimizer_success": bool(opt.success), "optimizer_status": int(opt.status),
            "optimizer_message": opt.message, "optimizer_iterations": int(opt.nit),
            "primal_residual": float(max(np.maximum(a@opt.x, 0).max(), abs((budget@opt.x)[0]-1))),
            "dual_stationarity": float(np.max(np.abs(residual))), "objective": float(opt.fun),
            "oic": "NOT_RUN for unsmoothed hinge LP"}
    return Fit(opt.x[:dim+1], float(opt.fun), None, diag)
