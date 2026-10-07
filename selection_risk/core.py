"""Past-only forecasters/selectors; population information enters evaluation only."""
from dataclasses import dataclass
import hashlib
import importlib.util
from pathlib import Path

import numpy as np
from scipy.special import ndtr
from scipy.stats import norm

ROOT = Path(__file__).resolve().parents[1]
HISTORICAL_SOURCE = ROOT / "quant_research_v2/src/research.py"
HISTORICAL_SHA256 = "8b8d0e5ca2540e3e8ceed8d27cce77185bc318b8266c929ca2dbb329c0e98700"


def historical_module():
    if hashlib.sha256(HISTORICAL_SOURCE.read_bytes()).hexdigest() != HISTORICAL_SHA256:
        raise ValueError("Frozen historical source changed")
    spec = importlib.util.spec_from_file_location("selection_historical_v2", HISTORICAL_SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


legacy = historical_module()


def validate_weights(weights):
    w = np.asarray(weights, dtype=float)
    if w.ndim != 2 or not len(w) or not np.isfinite(w).all():
        raise ValueError("Invalid portfolio bank")
    if (w < -1e-12).any() or (w > .5 + 1e-12).any():
        raise ValueError("Bank violates long-only/cap")
    if not np.allclose(w.sum(axis=1), 1, atol=1e-12, rtol=0):
        raise ValueError("Bank violates budget")
    return w


@dataclass(frozen=True)
class Surface:
    weights: np.ndarray
    var: np.ndarray
    es: np.ndarray

    def __post_init__(self):
        w = validate_weights(self.weights)
        for a in (self.var, self.es):
            if np.shape(a) != (len(w),) or not np.isfinite(a).all():
                raise ValueError("Missing/nonfinite surface: no per-method masks allowed")
        if np.any(self.es < self.var - 1e-10):
            raise ValueError("ES below VaR")

    def risk(self, weights):
        """Stored forecaster can answer exact bank queries; never interpolates."""
        indices = []
        for row in np.atleast_2d(weights):
            matches = np.flatnonzero(np.all(self.weights == row, axis=1))
            if len(matches) != 1:
                raise ValueError("Query must identify exactly one stored portfolio")
            indices.append(int(matches[0]))
        return self.var[indices], self.es[indices]


class EmpiricalForecaster:
    def fit(self, past):
        x = np.asarray(past, dtype=float)
        if x.ndim != 2 or len(x) < 2 or not np.isfinite(x).all():
            raise ValueError("Invalid past observations")
        self.past = x.copy()
        return self

    def risk(self, weights):
        return legacy.Risk(self.past, validate_weights(weights)).eval()


def empirical_surface(past, weights):
    return Surface(weights, *EmpiricalForecaster().fit(past).risk(weights))


def choose(surface, past_only=None, penalty=False):
    """Exact finite argmin; penalty changes the decision, never the forecast."""
    objective = surface.es.copy()
    if penalty:
        x = np.asarray(past_only, dtype=float)
        if x.ndim != 2 or len(x) < 2 or not np.isfinite(x).all():
            raise ValueError("SE selection needs past observations")
        hinges = np.maximum(-x @ surface.weights.T - surface.var, 0) / .05
        objective += hinges.std(axis=0, ddof=1) / np.sqrt(len(x))
    return int(np.argmin(objective))


def assert_common_surfaces(surfaces):
    first = next(iter(surfaces.values())).weights
    for surface in surfaces.values():
        if not np.array_equal(surface.weights, first):
            raise ValueError("Forecasters must use the identical bank/order")
    a, b = surfaces["historical"], surfaces["historical_se_penalty"]
    if not (np.array_equal(a.es, b.es) and np.array_equal(a.var, b.var)):
        raise ValueError("Historical/penalty forecast identity violated")


def lock_selectors(surfaces, past, names):
    assert_common_surfaces(surfaces)
    if not np.allclose(next(iter(surfaces.values())).weights[0], 1 / past.shape[1]):
        raise ValueError("Equal-weight portfolio must be bank index zero")
    return {name: 0 if name == "equal_weight" else
            choose(surfaces[name], past, name == "historical_se_penalty")
            for name in names}


def fit_frozen_suite(past, weights, seed):
    """Exactly frozen v2 historical / pure-mixture / support-band settings."""
    if np.shape(past) != (512, 8):
        raise ValueError("Frozen suite requires 512 x 8 observations")
    historical = empirical_surface(past, weights)
    z, gmm_diag = legacy.gmm(past[:256], seed)
    scenarios = np.vstack([z, past[256:]])
    probabilities = np.r_[np.full(len(z), .5 / len(z)), np.full(256, .5 / 256)]
    mix = Surface(weights, *legacy.Risk(scenarios, weights).eval(probabilities))
    risk, aptc_diag = legacy.calibrate(z, past[256:], weights, beta=.5, band=1, seed=seed)
    surfaces = {"historical": historical, "historical_se_penalty": historical,
                "support_mix50": mix, "support_band50": Surface(weights, *risk)}
    return surfaces, {"gmm": gmm_diag, "support_band50": aptc_diag}


def crossed_rows(surfaces, locked, true_es, family, seed):
    """Same portfolio target for all forecasters, plus within-instance bank mean."""
    assert_common_surfaces(surfaces)
    w = next(iter(surfaces.values())).weights
    truth = np.asarray(true_es)
    if truth.shape != (len(w),) or not np.isfinite(truth).all() or (truth <= 0).any():
        raise ValueError("Invalid evaluator truth/relative-error denominator")
    rows = []
    targets = dict(locked, fixed_bank=None)
    for selector, index in targets.items():
        if index is not None and (not isinstance(index, (int, np.integer)) or not 0 <= index < len(w)):
            raise ValueError("Invalid locked selection")
        ii = np.arange(len(w)) if index is None else np.array([index])
        for name, surface in surfaces.items():
            error = surface.es[ii] - truth[ii]
            rows.append({"family": family, "seed": int(seed), "forecaster": name,
                         "selector": selector, "portfolio_id": -1 if index is None else index,
                         "own_selected": name == selector, "n_targets": len(ii),
                         "predicted_es": float(surface.es[ii].mean()),
                         "true_es": float(truth[ii].mean()),
                         "absolute_error": float(np.abs(error).mean()),
                         "relative_error": float((np.abs(error) / truth[ii]).mean()),
                         "signed_relative_error": float((error / truth[ii]).mean()),
                         "relative_regret": float((truth[ii] / truth.min() - 1).mean()),
                         "hhi": float(np.square(w[ii]).sum(axis=1).mean())})
    return rows


def lock_split(past, weights):
    """Only past data enter this function. Each fold locks both weight and VaR."""
    if np.shape(past) != (512, 8):
        raise ValueError("Split protocol requires 512 x 8 observations")
    result = []
    for fold, train_slice, eval_slice in [("A_to_B", slice(0, 256), slice(256, 512)),
                                         ("B_to_A", slice(256, 512), slice(0, 256))]:
        train, held = past[train_slice], past[eval_slice]
        surface = empirical_surface(train, weights)
        j = choose(surface)
        v = float(surface.var[j])
        loss = -held @ weights[j]
        held_objective = float(np.mean(v + np.maximum(loss - v, 0) / .05))
        holdout_es = float(EmpiricalForecaster().fit(held).risk(weights[j:j+1])[1][0])
        result.append({"fold": fold, "portfolio_id": j, "threshold": v,
                       "train_objective": float(surface.es[j]),
                       "heldout_objective": held_objective,
                       "heldout_empirical_es": holdout_es})
    return result


def frozen_objective_truth(weights, threshold, parameters):
    """Evaluator only: analytic Gaussian-mixture E[h(w,v; X)] at frozen v."""
    if parameters["kind"] != "mix":
        raise ValueError("IID pilot evaluator supports Gaussian mixtures only")
    m = -weights @ parameters["mu"].T
    sd = np.sqrt(np.einsum("i,kij,j->k", weights, parameters["cov"], weights))
    z = (threshold - m) / sd
    stoploss = (m - threshold) * ndtr(-z) + sd * norm.pdf(z)
    return float(threshold + parameters["p"] @ stoploss / .05)


def evaluate_split(locked, weights, parameters, true_es, family, seed):
    result = []
    for decision in locked:
        j = decision["portfolio_id"]
        target = frozen_objective_truth(weights[j], decision["threshold"], parameters)
        common = {"family": family, "seed": seed, "fold": decision["fold"],
                  "portfolio_id": j, "threshold": decision["threshold"],
                  "true_es": float(true_es[j]), "true_objective": target,
                  "threshold_gap": target - float(true_es[j]),
                  "relative_regret": float(true_es[j] / min(true_es) - 1),
                  "hhi": float(weights[j] @ weights[j])}
        for method, key in [("resubstitution", "train_objective"),
                            ("independent_split", "heldout_objective")]:
            value = decision[key]
            error = (value - target) / target
            result.append(dict(common, estimator=method, estimate=value,
                               signed_relative_error=error, relative_error=abs(error),
                               squared_relative_error=error**2,
                               heldout_empirical_es=decision["heldout_empirical_es"],
                               heldout_es_relative_error=abs(decision["heldout_empirical_es"] / true_es[j] - 1)))
    return result
