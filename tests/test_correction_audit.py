import json
import numpy as np
import pytest
from correction_audit.mechanism import prepare, trace_correction, anchor_decomposition
from correction_audit.run import population_hinge, contract
from local_market.models import calibrate, entropy_solve, Risk, bank
from research import generate, truth


def test_band_no_update_condition_and_active_case():
    a = np.array([[0.], [2.]])
    prior = np.array([.5, .5])
    inside, _ = entropy_solve(a, np.array([1.5]), prior, band=1.)
    outside, _ = entropy_solve(a, np.array([3.]), prior, band=1.)
    np.testing.assert_allclose(inside, prior, atol=1e-14)
    assert np.max(abs(outside-prior)) > .01


@pytest.mark.parametrize("band", [0., 1.])
def test_instrumentation_matches_frozen_recipe(band):
    rng = np.random.default_rng(123)
    z, cal = rng.normal(size=(1536, 8)), rng.normal(size=(256, 8))
    w = bank(2026)
    result, diag, p = trace_correction(prepare(z, cal, w), band)
    original, orig_diag = calibrate(z, cal, w, band=band)
    np.testing.assert_allclose(result, original, atol=1e-11, rtol=0)
    assert diag["directions"] == orig_diag["directions"]
    assert p.sum() == pytest.approx(1)


def test_random_control_is_reproducible_unique_and_budget_matched():
    rng = np.random.default_rng(11)
    state = prepare(rng.normal(size=(1536, 8)), rng.normal(size=(256, 8)), bank(2026))
    a, d, _ = trace_correction(state, random_seed=42)
    b, e, _ = trace_correction(state, random_seed=42)
    np.testing.assert_array_equal(a, b)
    assert len(set(d["directions"])) == len(d["steps"]) == 8
    assert d["directions"] == e["directions"]


def test_matching_one_hinge_does_not_identify_es():
    # Same support, same hinge moment at a prior 95% VaR, different ES.
    loss = np.array([0., 1., 3., 11.])
    q = np.array([.90, .05, .05, 0.])
    p = np.array([.99, 0., 0., .01])
    rb = Risk(-loss[:, None], np.ones((1, 1)))
    eta = rb.eval(q)[0][0]
    assert eta == 1
    assert q @ np.maximum(loss-eta, 0) == pytest.approx(p @ np.maximum(loss-eta, 0))
    assert rb.eval(q)[1][0] == pytest.approx(3.)
    assert rb.eval(p)[1][0] == pytest.approx(2.2)


@pytest.mark.parametrize("family", ["gaussian", "student_t4", "asymmetric_crash", "markov_volatility"])
def test_population_hinge_agrees_with_es_at_population_var(family):
    _, pars = generate(999, family)
    w = bank(2026)
    v, e = truth(w, pars)
    np.testing.assert_allclose(v+population_hinge(w, v, pars)/.05, e, atol=1e-10)


def test_error_decomposition_identity():
    rng = np.random.default_rng(40)
    state = prepare(rng.normal(size=(1536, 8)), rng.normal(size=(256, 8)), bank(2026))
    risk, _, p = trace_correction(state)
    terms = anchor_decomposition(state, p, risk[1][0], 2., .035, 0)
    assert abs(terms["identity_residual"]) < 1e-12


def test_development_boundary_cannot_be_reopened(tmp_path, monkeypatch):
    import correction_audit.run as run
    protocol = contract()
    protocol["ecb"]["through"] = "2025-12-31"
    path = tmp_path/"bad.json"
    path.write_text(json.dumps(protocol))
    monkeypatch.setattr(run, "PROTOCOL", path)
    with pytest.raises(ValueError, match="Development boundary"):
        contract()


def test_paired_ecb_intervals_preserve_constant_differences():
    from correction_audit.analyze import paired, TARGETS
    from correction_audit.mechanism import METHODS
    protocol = contract()
    protocol["uncertainty"]["replicates"] = 20
    rows = []
    for i in range(65):
        for track, target in TARGETS:
            for method in METHODS:
                offset = -.25 if method == "support_band50" else 0.
                rows.append({"date": str(i).zfill(3), "track": track, "target": target, "method": method,
                             "fz0": i/100+offset, "realized_loss": i/100+offset})
    result = paired(rows, "ecb", protocol)
    assert len(result) == 48
    for r in result:
        np.testing.assert_allclose([r["difference"], r["ci_low"], r["ci_high"]], -.25, atol=1e-12)


def test_single_window_has_same_targets_and_no_market_truth(tmp_path):
    from correction_audit.run import job_run
    rng = np.random.default_rng(400)
    path = tmp_path/"window.json"
    meta = {"date": "2010-01-01", "source": "ecb", "seed": 444, "bank_seed": 2026}
    job_run((meta, rng.normal(size=(512, 8)), rng.normal(size=8), path, "test"))
    value = json.loads(path.read_text())
    assert len(value["rows"]) == 21
    for target in ["equal_weight", "historical_se_reference"]:
        rows = [r for r in value["rows"] if r["track"] == "A" and r["target"] == target]
        assert len({r["realized_loss"] for r in rows}) == 1
        assert len({r["portfolio_id"] for r in rows}) == 1
        assert all("true_es" not in r for r in rows)
    assert all(d["reference"] == "empirical_training_calibration" for d in value["decomposition"])
