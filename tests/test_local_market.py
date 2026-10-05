import csv
import datetime as dt
import io
import json
import zipfile
import numpy as np
from numpy.testing import assert_allclose
import pytest

from local_market import data, models, runner, scoring


def ecb_raw(rows):
    s = io.StringIO()
    writer = csv.writer(s)
    writer.writerow(["Date"] + data.PANELS["ecb"])
    writer.writerows(rows)
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w") as z:
        z.writestr("eurofxref-hist.csv", s.getvalue())
    return b.getvalue()


def test_loader_missing_observation_does_not_bridge():
    raw = ecb_raw([["2020-01-06"]+[2]*8, ["2020-01-07"]+["N/A"]+[2]*7, ["2020-01-08"]+[4]*8])
    points, audit = data.parse(raw, "ecb")
    assert audit["incomplete_dates"] == ["2020-01-07"]
    assert_allclose(points[0][1], .5)
    _, valid = data.session_returns([r[0] for r in points], np.array([r[1] for r in points]), audit["incomplete_dates"])
    assert not valid.any()


def test_unrecognized_weekday_gap_is_blocked():
    points, audit = data.parse(ecb_raw([["2020-01-06"]+[2]*8, ["2020-01-08"]+[3]*8]), "ecb")
    assert audit["unresolved_missing_weekdays"] == ["2020-01-07"]
    _, valid = data.session_returns([r[0] for r in points], np.array([r[1] for r in points]), audit["unresolved_missing_weekdays"])
    assert not valid.any()


def test_weekend_is_one_session_not_one_calendar_day():
    points, audit = data.parse(ecb_raw([["2020-01-03"]+[2]*8, ["2020-01-06"]+[4]*8]), "ecb")
    r, valid = data.session_returns([r[0] for r in points], np.array([r[1] for r in points]), audit["unresolved_missing_weekdays"])
    assert valid.all()
    assert_allclose(r, -50)


@pytest.mark.parametrize("raw", [b"<html>Not a ZIP</html>", b"PKxxbogus"])
def test_html_or_bad_magic_rejected(raw):
    with pytest.raises(ValueError):
        data.parse(raw, "ecb")


def test_duplicate_rejected():
    with pytest.raises(ValueError, match="Duplicate"):
        data.parse(ecb_raw([["2020-01-01"]+[1]*8]*2), "ecb")


def test_boc_direction_and_schema():
    series = ["FX"+c+"CAD" for c in data.PANELS["boc"]]
    obj = {"seriesDetail": {s: {} for s in series}, "observations": [
        {"d": day, **{s: {"v": "1.5"} for s in series}} for day in ["2020-01-06", "2020-01-07"]]}
    points, _ = data.parse(json.dumps(obj).encode(), "boc")
    assert_allclose(points[0][1], 1.5)
    obj["seriesDetail"].pop(series[0])
    with pytest.raises(ValueError, match="schema"):
        data.parse(json.dumps(obj).encode(), "boc")


def test_calendar_special_dates():
    assert dt.date(2001, 12, 31) in data.holiday_candidates("ecb", 2001)
    assert dt.date(2025, 5, 19) in data.holiday_candidates("boc", 2025)
    assert dt.date(2021, 12, 28) in data.holiday_candidates("boc", 2021)


def test_upper_loss_fz0_and_residual():
    s = scoring.score(3, 1, 2)
    assert_allclose(s["fz0"], (40+1)/2 + np.log(2)-1)
    assert_allclose(s["shortfall_residual"], 39)
    assert_allclose(s["pinball95"], 1.9)
    assert scoring.score(-1, -2, 0)["fz0"] is None
    assert scoring.score(2, 2, 1)["fz0"] is None


def test_fz0_expected_score_minimum_at_normal_truth():
    from scipy.stats import norm
    # Deterministic quadrature grid, not a market performance test.
    losses = norm.ppf((np.arange(100000)+.5)/100000)
    v, e = norm.ppf(.95), norm.pdf(norm.ppf(.95))/.05
    def mean_score(v, e):
        return np.mean((np.maximum(losses-v, 0)/.05+v)/e+np.log(e)-1)
    proper = mean_score(v, e)
    assert all(mean_score(v+dv, e*scale) > proper for dv, scale in [(.3, 1), (-.3, 1), (0, .8), (0, 1.2)])


def test_fractional_empirical_es():
    assert_allclose(scoring.empirical_es([0, 1, 2, 10], q=.6), (10+.6*2)/1.6)
    assert_allclose(scoring.empirical_es(np.array([[0, 0], [1, 2], [2, 4], [10, 20]]), q=.6), [7, 14])


def test_training_index_gap_and_invalid_history():
    valid = np.ones(600, dtype=bool)
    ix = runner.training_indices(551, valid)
    assert ix[0] == 38 and ix[-1] == 549
    assert 550 not in ix and 551 not in ix
    assert runner.training_indices(512, valid) is None
    valid[100] = False
    assert runner.training_indices(551, valid) is None


def test_new_calibration_compatible_with_frozen_original():
    from research import calibrate, gmm
    x = np.random.default_rng(34).normal(size=(512, 8))
    w = models.bank(2026)
    z, _ = gmm(x[:256], 50)
    for beta, band, old in [(0, 0, True), (.5, 1, False)]:
        expected, _ = calibrate(z, x[256:], w, beta=beta, band=band, old=old)
        actual, diag = models.calibrate(z, x[256:], w, beta, band, old)
        assert_allclose(actual, expected, atol=1e-10)
        assert len(diag["steps"]) == 8


def test_same_target_and_penalty_unpenalized_and_future_separation():
    x = np.random.default_rng(50).normal(size=(512, 8))
    rows, _ = runner.evaluate(x, np.ones(8), 51)
    other, _ = runner.evaluate(x, np.full(8, -100), 51)
    for a, b in zip(rows, other):
        assert a["weights"] == b["weights"]
        assert a["es95"] == b["es95"]
    for target in ["equal_weight", "historical_se_reference"]:
        rr = [r for r in rows if r["track"] == "A" and r["target"] == target]
        assert len({r["realized_loss"] for r in rr}) == 1
        assert len({tuple(r["weights"]) for r in rr}) == 1
        assert rr[0]["es95"] == rr[1]["es95"]


def test_gmm_exception_fallback_retains_all_methods(monkeypatch):
    def fail(*args):
        raise RuntimeError("injected failure")
    monkeypatch.setattr(models, "gmm_fit", fail)
    x = np.random.default_rng(60).normal(size=(512, 8))
    risks, chosen, diag = models.forecast(x, models.bank(2026), 61)
    assert set(risks) == set(models.METHODS)
    for name in ["gmm_base", "gmm_pooled", "support_band50", "support_mix50", "aptc_v1"]:
        assert diag[name]["fallback"]
        assert_allclose(risks[name], risks["historical"])


def test_finite_nonconvergence_kept(monkeypatch):
    original = models.gmm_fit
    def flagged(*args):
        z, diag = original(*args)
        diag["converged"] = False
        return z, diag
    monkeypatch.setattr(models, "gmm_fit", flagged)
    x = np.random.default_rng(65).normal(size=(512, 8))
    _, _, diag = models.forecast(x, models.bank(2026), 66)
    assert not diag["support_mix50"]["converged"]
    assert not diag["support_mix50"]["fallback"]


def test_heldout_requires_freeze(tmp_path):
    with pytest.raises(FileNotFoundError):
        runner.validate_freeze(tmp_path/"absent.json", "ecb", {})


def test_atomic_resume_and_config_mismatch(tmp_path):
    days = [str(dt.date(2008, 1, 1) + dt.timedelta(days=i)) for i in range(1100)]
    days = [d for d in days if dt.date.fromisoformat(d).weekday() < 5]
    values = 2*np.exp(np.random.default_rng(90).normal(0, .001, (len(days), 8)).cumsum(0))
    source = tmp_path/"fixture.zip"
    source.write_bytes(ecb_raw([[d]+list(v) for d, v in zip(days, values)]))
    dataset = tmp_path/"dataset"
    data.prepare("ecb", dataset, source)
    out = tmp_path/"run"
    first = runner.run(dataset, out, "development", workers=1, stride=5, limit=2)
    second = runner.run(dataset, out, "development", workers=1, stride=5, limit=2)
    assert first["forecasts_sha256"] == second["forecasts_sha256"]
    assert second["computed_this_invocation"] == 0
    assert not list(out.rglob("*.tmp"))
    with pytest.raises(ValueError, match="another configuration"):
        runner.run(dataset, out, "development", workers=1, stride=1, limit=2)
    with pytest.raises(ValueError, match="frozen protocol"):
        runner.run(dataset, tmp_path/"test", "test", workers=1)
