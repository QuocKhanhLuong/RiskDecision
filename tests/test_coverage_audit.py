import numpy as np
import pytest
from scipy.stats import norm
from coverage_audit.core import (generate, conditional, features, multiplier, population_hinge,
                                 evaluate, counterexample, bank, FAMILIES)
from coverage_audit.analyze import wilson, summarize


@pytest.mark.parametrize("family", FAMILIES)
def test_stationary_generator_repeats_and_conditional_parameters(family):
    x, p, states = generate(12, family)
    y, _, s2 = generate(12, family)
    np.testing.assert_array_equal(x, y)
    np.testing.assert_array_equal(states, s2)
    assert x.shape == (1280, 8) and np.isfinite(x).all()
    q = conditional(family, p, x[-1], states[-1])
    if family == "ar1":
        np.testing.assert_allclose(q["mu"][0], .6*x[-1])
        np.testing.assert_allclose(q["cov"], .64*p["cov"])
    elif family == "markov_volatility":
        transition = np.array([[.985, .015], [.12, .88]])
        np.testing.assert_allclose(p["p"] @ transition, p["p"])
        np.testing.assert_allclose(q["p"], transition[states[-1]])
    else:
        assert q is p


def test_base_anchor_excludes_calibration_and_reuse_changes_it():
    rng = np.random.default_rng(42)
    z, cal, w = rng.normal(size=(1500, 8)), rng.normal(size=(256, 8)), bank(2026)
    a, h, _, _ = features(z, cal, w, "base_only")
    b, _, _, _ = features(z, cal-10, w, "base_only")
    np.testing.assert_array_equal(a, b)
    c, _, _, _ = features(z, cal-10, w, "reused_mixture")
    assert not np.array_equal(a, c)
    np.testing.assert_allclose(h[:, 1], np.maximum(-cal @ w[0]-a[1], 0))
    assert h.shape == (256, 855)


def test_multiplier_against_independent_scalar_formula():
    h = np.arange(48, dtype=float).reshape(16, 3)**1.2
    radius, critical, zero = multiplier(h, 4, 99, 27)
    sums = np.array([h[i:i+4].sum(0)-4*h.mean(0) for i in range(0, 16, 4)])
    se = np.sqrt(4/3*np.sum(sums**2, axis=0))/16
    weights = np.random.default_rng(27).normal(size=(99, 4))
    maxima = [max(abs(sum(g[k]*sums[k, j] for k in range(4))*np.sqrt(4/3)/16/se[j]) for j in range(3)) for g in weights]
    q = np.quantile(maxima, .95, method="higher")
    np.testing.assert_allclose(radius, q*se, rtol=1e-12)
    assert critical == pytest.approx(q) and zero == 0


def test_zero_variance_is_not_hidden_and_blocks_must_partition():
    h = np.ones((16, 3))
    radius, critical, zero = multiplier(h, 4, 99, 42)
    assert zero == 3 and critical == 0
    assert not radius.any()
    with pytest.raises(ValueError):
        multiplier(h, 3, 99, 42)
    metrics = evaluate(np.ones(3), radius, np.ones(3)*2, np.ones(1), 0)
    assert metrics["all_covered"] == 0


def test_conditional_hinge_closed_form_and_counterexample():
    x, p, states = generate(5, "ar1")
    q = conditional("ar1", p, x[-1], states[-1])
    w = bank(2026)[:1]; eta = np.array([.5])
    mean = -float(w[0] @ q["mu"][0])
    sd = np.sqrt(w[0] @ q["cov"][0] @ w[0])
    z = (.5-mean)/sd
    np.testing.assert_allclose(population_hinge(w, eta, q), (mean-.5)*norm.sf(z)+sd*norm.pdf(z))
    c = counterexample()
    assert c["marginal_es95"] == pytest.approx(4)
    assert c["after_high_es95"] == 10
    assert c["after_low_es95"] == pytest.approx(.8163265306122449)
    assert .98*c["low_to_high"]+.02*c["high_to_high"] == pytest.approx(.02)


def test_wilson_and_duplicate_seed_guard():
    lo, hi = wilson(95, 100)
    assert lo == pytest.approx(.88824953) and hi == pytest.approx(.97845632)
    with pytest.raises(ValueError):
        wilson(0, 0)
    row = {"family": "g", "n": 256, "anchor": "b", "procedure": "p", "estimand": "m", "seed": 1}
    with pytest.raises(ValueError, match="duplicated"):
        summarize([row, row], expected=2)
