"""Reconcile forecast CSVs, source data, window artifacts and public aggregate CSVs."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import numpy as np
from numpy.testing import assert_allclose

from .data import load_panel, sha256, atomic_json
from .models import METHODS, bank
from .runner import training_indices, evaluate, validate_freeze, content_hash
from .scoring import score
from .stats import read_rows


def audit(run, dataset, aggregates, protocol, refit=False):
    run, aggregates = Path(run), Path(aggregates)
    dates, returns, valid, manifest = load_panel(dataset)
    validate_freeze(protocol, manifest["source"], manifest)
    config = json.loads((run/"config.json").read_text())
    receipt = json.loads((run/"receipt.json").read_text())
    assert receipt["identity"] == content_hash(config)
    assert sha256(run/"forecasts.csv") == receipt["forecasts_sha256"]
    assert sha256(run/"diagnostics.json") == receipt["diagnostics_sha256"]
    rows = read_rows(run/"forecasts.csv")
    bydate = {}
    wbank = bank(2026)
    for row in rows:
        bydate.setdefault(row["date"], []).append(row)
        i = int(row["return_index"])
        ix = training_indices(i, valid)
        assert ix is not None and len(ix) == 512
        assert row["date"] == dates[i+1] and row["target_start_date"] == dates[i]
        assert row["training_last_date"] == dates[int(ix[-1])+1]
        assert row["training_sha256"] == hashlib.sha256(returns[ix].tobytes()).hexdigest()
        assert row["last_training_available_utc"] < row["information_cutoff_utc"] == row["forecast_origin_utc"]
        assert_allclose(row["weights"], wbank[int(row["portfolio_id"])], atol=0, rtol=0)
        assert_allclose(row["realized_loss"], -returns[i] @ row["weights"], atol=1e-12)
        recalculated = score(row["realized_loss"], row["var95"], row["es95"])
        for metric in ("var_breach", "pinball95", "shortfall_residual", "fz0"):
            expected = recalculated[metric]
            assert_allclose(row[metric], np.nan if expected is None else expected, atol=1e-12, equal_nan=True)
    assert len(rows) == receipt["rows"] == len(bydate)*3*len(METHODS)
    assert len(bydate) == receipt["windows"]
    for date, rr in bydate.items():
        original = json.loads((run/"windows"/(date+".json")).read_text())
        assert original["identity"] == receipt["identity"]
        assert len(rr) == len(original["rows"]) == 33
        for csvrow, jrow in zip(rr, original["rows"]):
            assert (csvrow["track"], csvrow["target"], csvrow["method"]) == (jrow["track"], jrow["target"], jrow["method"])
            for metric in ["weights", "realized_loss", "var95", "es95"]:
                assert_allclose(csvrow[metric], jrow[metric], atol=0, rtol=0)
        for target in ["equal_weight", "historical_se_reference"]:
            common = [r for r in rr if r["track"] == "A" and r["target"] == target]
            assert {r["method"] for r in common} == set(METHODS)
            assert len({tuple(r["weights"]) for r in common}) == 1
            assert len({r["realized_loss"] for r in common}) == 1
    count = 0
    for filename in ("summary.csv", "annual.csv"):
        with (aggregates/filename).open() as f:
            table = list(csv.DictReader(f))
        for agg in table:
            rr = [r for r in rows if all(r[k] == agg[k] for k in ["track", "target", "method"])
                  and ("year" not in agg or r["date"].startswith(agg["year"]))]
            assert len(rr) == int(agg["n"])
            losses = np.array([r["realized_loss"] for r in rr])
            # Independent descending-tail integral with fractional boundary weight.
            ordered = sorted(losses, reverse=True)
            tail = .05*len(ordered)
            masses = np.clip(tail - np.arange(len(ordered)), 0, 1)
            es = float(np.dot(ordered, masses)/tail)
            assert_allclose(float(agg["pooled_es95_pp"]), es, atol=1e-12)
            assert_allclose(float(agg["mean_loss_pp"]), losses.mean(), atol=1e-12)
            assert int(agg["breaches"]) == sum(r["realized_loss"] > r["var95"] for r in rr)
            assert int(agg["fallback_n"]) == sum(r["fallback"] for r in rr)
            assert int(agg["nonconverged_n"]) == sum(not r["converged"] for r in rr)
            assert int(agg["fz0_undefined_n"]) == sum(not np.isfinite(r["fz0"]) for r in rr)
            if agg["track"] == "A":
                assert_allclose(float(agg["mean_fz0"]), np.nanmean([r["fz0"] for r in rr]), atol=1e-12)
                assert_allclose(float(agg["mean_pinball95"]), np.mean([r["pinball95"] for r in rr]), atol=1e-12)
            count += 1
    refit_dates = []
    if refit:
        ordered_dates = sorted(bydate)
        for date in [ordered_dates[0], ordered_dates[-1]]:
            old = bydate[date]
            i = int(old[0]["return_index"])
            new, _ = evaluate(returns[training_indices(i, valid)], returns[i], int(old[0]["seed"]))
            for a, b in zip(old, new):
                for key in ("weights", "var95", "es95", "realized_loss"):
                    assert_allclose(a[key], b[key], atol=1e-10, rtol=1e-10)
            refit_dates.append(date)
    result = {"status": "PASS", "run": str(run), "forecast_rows_checked": len(rows), "date_windows": len(bydate),
              "aggregate_rows_recomputed": count, "refit_dates": refit_dates,
              "forecasts_sha256": sha256(run/"forecasts.csv"), "protocol_sha256": sha256(protocol),
              "checks": ["CSV-window identity", "same-target pairing", "training and availability ordering", "realized loss recomputation",
                         "bank weights", "score recomputation", "independent fractional pooled ES", "annual counts", "failure counts"],
              "review_type": "coordinator numerical/artifact audit; independent agent review NOT RUN"}
    atomic_json(aggregates/"artifact_audit.json", result)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run", type=Path, required=True)
    p.add_argument("--dataset", type=Path, required=True)
    p.add_argument("--aggregates", type=Path, required=True)
    p.add_argument("--protocol", type=Path, required=True)
    p.add_argument("--refit", action="store_true")
    print(json.dumps(audit(**vars(p.parse_args())), indent=2))


if __name__ == "__main__":
    main()
