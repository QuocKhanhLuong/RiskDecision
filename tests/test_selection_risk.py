import json

import numpy as np
import pytest
from numpy.testing import assert_allclose

from selection_risk.core import (EmpiricalForecaster, Surface, assert_common_surfaces,
                                 crossed_rows, empirical_surface, evaluate_split,
                                 frozen_objective_truth, legacy, lock_selectors, lock_split)
from selection_risk.run import array_hash, historical_case
from selection_risk.runtime import Run, atomic_json, digest
from selection_risk.statistics import cluster_values, interval, summarize_crossed, summarize_split


def bank():
    return np.array([[.25, .25, .25, .25], [.5, .5, 0, 0]])


def surfaces():
    w = bank()
    h = Surface(w, np.array([1., 1.5]), np.array([2., 3.]))
    a = Surface(w, np.array([1., 1.5]), np.array([4., 2.]))
    return {"historical": h, "historical_se_penalty": h, "candidate": a}


def test_crossed_uses_common_locked_targets_and_separate_regret():
    rows = crossed_rows(surfaces(), {"historical": 0, "candidate": 1}, np.array([2.5, 4.]), "f", 1)
    by_key = {(r["forecaster"], r["selector"]): r for r in rows}
    h = by_key["historical", "candidate"]
    assert h["predicted_es"] == 3 and h["true_es"] == 4
    assert h["relative_error"] == .25 and h["relative_regret"] == pytest.approx(.6)
    assert not h["own_selected"]
    fixed = by_key["historical", "fixed_bank"]
    assert fixed["relative_error"] == pytest.approx((.2+.25)/2)
    assert fixed["n_targets"] == 2 and fixed["portfolio_id"] == -1


@pytest.mark.parametrize("field", ["var", "es"])
def test_penalty_identity_checks_entire_surface(field):
    ss = surfaces()
    old = ss["historical"]
    v, e = old.var.copy(), old.es.copy()
    (v if field == "var" else e)[-1] += .01
    ss["historical_se_penalty"] = Surface(old.weights, v, e)
    with pytest.raises(ValueError, match="identity"):
        assert_common_surfaces(ss)


def test_bank_order_and_nonfinite_fail_closed():
    ss = surfaces()
    old = ss["candidate"]
    ss["candidate"] = Surface(old.weights[::-1], old.var, old.es)
    with pytest.raises(ValueError, match="identical bank"):
        assert_common_surfaces(ss)
    with pytest.raises(ValueError, match="nonfinite"):
        Surface(bank(), np.array([1., np.nan]), np.array([2., 3.]))
    with pytest.raises(ValueError, match="denominator"):
        crossed_rows(surfaces(), {"historical": 0}, np.array([0., 1.]), "f", 1)


def test_empirical_and_stored_risk_interfaces():
    x = np.arange(160, dtype=float).reshape(40, 4) / 100
    fitted = EmpiricalForecaster().fit(x)
    before = fitted.risk(bank())
    x[:] = 0
    assert_allclose(before, fitted.risk(bank()))
    ss = surfaces()["historical"]
    assert_allclose(ss.risk(bank()[1:]), ([1.5], [3.]))
    with pytest.raises(ValueError, match="exactly one"):
        ss.risk([[.3, .3, .2, .2]])


def test_split_holdout_cannot_change_first_fold_decision():
    x, _ = legacy.generate(91001, "gaussian")
    w = legacy.bank(91001)
    first = lock_split(x, w)[0]
    changed = x.copy()
    changed[256:] -= 10
    second = lock_split(changed, w)[0]
    assert first["portfolio_id"] == second["portfolio_id"]
    assert first["threshold"] == second["threshold"]
    assert first["train_objective"] == second["train_objective"]
    assert first["heldout_objective"] != second["heldout_objective"]
    j, v = first["portfolio_id"], first["threshold"]
    expected = np.mean(v + np.maximum(-x[256:] @ w[j] - v, 0) / .05)
    assert first["heldout_objective"] == pytest.approx(expected)


def test_population_frozen_objective_is_not_es_at_wrong_threshold():
    from scipy.stats import norm
    p = {"kind": "mix", "p": np.array([1.]), "mu": np.zeros((1, 2)), "cov": np.array([np.eye(2)])}
    w = np.array([.5, .5])
    sd = np.sqrt(.5)
    v, es = legacy.truth(w[None], p)
    assert frozen_objective_truth(w, v[0], p) == pytest.approx(es[0], rel=1e-12)
    at_zero = frozen_objective_truth(w, 0, p)
    assert at_zero == pytest.approx(sd * norm.pdf(0) / .05)
    assert at_zero > es[0]


def test_fixed_objective_matches_independent_monte_carlo():
    _, p = legacy.generate(91002, "asymmetric_crash")
    w = legacy.bank(91002)[0]
    rng = np.random.default_rng(8871)
    n = 200000
    states = rng.choice(len(p["p"]), n, p=p["p"])
    means = -p["mu"] @ w
    sd = np.sqrt(np.einsum("i,kij,j->k", w, p["cov"], w))
    loss = means[states] + sd[states] * rng.standard_normal(n)
    v = 2.
    h = v + np.maximum(loss-v, 0)/.05
    assert abs(h.mean()-frozen_objective_truth(w, v, p)) < 4*h.std()/np.sqrt(n)


def test_split_evaluator_targets_frozen_objective_after_lock():
    x, p = legacy.generate(91003, "gaussian")
    w = legacy.bank(91003)
    locked = lock_split(x, w)
    true = legacy.truth(w, p)[1]
    rows = evaluate_split(locked, w, p, true, "gaussian", 91003)
    assert len(rows) == 4
    for row in rows:
        assert row["threshold_gap"] >= -1e-10
        assert row["squared_relative_error"] == pytest.approx(row["signed_relative_error"]**2)
    assert rows[0]["portfolio_id"] == rows[1]["portfolio_id"]
    assert rows[0]["true_objective"] == rows[1]["true_objective"]


def test_cluster_mean_is_seed_level_not_portfolio_or_family_pseudoreplication():
    rows = [dict(family=f, seed=s, value=v) for f,s,v in [("a",1,1),("b",1,3),("a",2,5),("b",2,7)]]
    seeds, values = cluster_values(rows, "value", ["a", "b"])
    assert seeds == [1, 2]
    assert_allclose(values, [2,6])
    with pytest.raises(ValueError, match="Duplicate"):
        cluster_values(rows + rows[:1], "value", ["a", "b"])
    with pytest.raises(ValueError, match="Unbalanced"):
        cluster_values(rows[:-1], "value", ["a", "b"])
    assert interval(np.array([0., 0.]), 100, 1) == (0., 0., 0.)


def test_paired_summary_identity_has_exact_zero_interval():
    rows = []
    for seed in (1, 2):
        rows += crossed_rows(surfaces(), {"historical": 0}, np.array([2.5, 4.]), "f", seed)
    cfg = dict(families=["f"], bootstrap_reps=100, bootstrap_seed=1)
    _, paired = summarize_crossed(rows, cfg)
    alias = [r for r in paired if r["forecaster"] == "historical_se_penalty"]
    assert all(r["mean"] == r["ci_low"] == r["ci_high"] == 0 for r in alias)


def test_primary_split_contrast_is_paired_on_first_fold_only():
    rows = []
    for seed in (1, 2):
        for fold in ("A_to_B", "B_to_A"):
            for method in ("resubstitution", "independent_split"):
                error = (1 if method == "resubstitution" else 2) * (1 if fold == "A_to_B" else 10)
                rows.append(dict(family="f", seed=seed, fold=fold, estimator=method,
                                 signed_relative_error=error, relative_error=error,
                                 squared_relative_error=error**2, threshold_gap=0,
                                 relative_regret=0, heldout_es_relative_error=0))
    summary = summarize_split(rows, dict(families=["f"], bootstrap_reps=100, bootstrap_seed=1))
    primary = [r for r in summary if r["primary"]]
    assert len(primary) == 1 and primary[0]["mean"] == 3


def test_resume_refuses_configuration_or_input_change(tmp_path):
    run = Run(tmp_path, {"seed": 1}, {"data": "abc"})
    with run.session():
        run.save("case", {"value": 4})
    same = Run(tmp_path, {"seed": 1}, {"data": "abc"})
    with same.session():
        assert same.case("case") == {"value": 4}
    for cfg, inp in [({"seed": 2}, {"data": "abc"}), ({"seed": 1}, {"data": "def"})]:
        with pytest.raises(ValueError, match="Resume rejected"):
            with Run(tmp_path, cfg, inp).session():
                pass


def test_resume_refuses_corrupt_payload_and_array(tmp_path):
    run = Run(tmp_path, {}, {})
    (tmp_path / "array").write_bytes(b"original")
    with run.session():
        run.save("x", {"artifacts": {"array": digest(tmp_path / "array")}})
        (tmp_path / "array").write_bytes(b"different")
        with pytest.raises(ValueError, match="artifact"):
            run.case("x")
        run.save("y", {"value": 1})
        path = tmp_path / "cases/y.json"
        data = json.loads(path.read_text())
        data["payload"]["value"] = 2
        atomic_json(path, data)
        with pytest.raises(ValueError, match="checkpoint"):
            run.case("y")


def test_historical_loader_verifies_fixture_scalars_without_refit(tmp_path, monkeypatch):
    seed, family = 4000, "gaussian"
    x, p = legacy.generate(seed, family)
    w = legacy.bank(seed)
    h = empirical_surface(x, w)
    ss = {"historical": h, "historical_se_penalty": h}
    cfg = {"forecasters": list(ss), "selectors": ["equal_weight", *ss]}
    locked = lock_selectors(ss, x, cfg["selectors"])
    tv, te = legacy.truth(w, p)
    dest = tmp_path / "quant_research_v2/results/test"
    dest.mkdir(parents=True)
    np.savez(dest / f"{family}_{seed}.npz", weights=w, returns=x, true_es=te, true_var=tv,
             **{k+"_es": v.es for k,v in ss.items()}, **{k+"_var": v.var for k,v in ss.items()})
    atomic_json(dest / f"{family}_{seed}.json", {"x_sha256": array_hash(x)})
    raw = {}
    for name, j in locked.items():
        raw[family,seed,name] = dict(portfolio_id=j, predicted_es=h.es[j], true_es=te[j],
                                    relative_error=abs(h.es[j]/te[j]-1), relative_regret=te[j]/te.min()-1,
                                    hhi=w[j]@w[j])
    monkeypatch.setattr(legacy, "gmm", lambda *a, **k: pytest.fail("Q0 must not refit"))
    result = historical_case(tmp_path, family, seed, cfg, raw)
    assert result["assertions"]["historical_csv_selectors_matched"] == 3
    raw[family,seed,"historical"]["portfolio_id"] = -1
    with pytest.raises(ValueError, match="selection differs"):
        historical_case(tmp_path, family, seed, cfg, raw)
