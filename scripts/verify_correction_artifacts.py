#!/usr/bin/env python3
"""Separate CSV-only aggregate recomputation; no fitting and no held-out reads."""
from pathlib import Path
import csv
import json
import math
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from local_market.data import atomic_json, sha256


def read(path):
    with path.open() as f:
        return list(csv.DictReader(f))


def mean(rows, field):
    return math.fsum(float(r[field]) for r in rows)/len(rows)


def tail(rows):
    ordered = sorted((float(r["realized_loss"]) for r in rows), reverse=True)
    mass = len(ordered)*.05
    return math.fsum(value*min(1., max(0., mass-i)) for i, value in enumerate(ordered))/mass


def verify():
    receipts = {}
    for source in ["synthetic", "ecb"]:
        directory = ROOT/"results/correction_diagnostic_v1"/source
        rows = read(ROOT/"runs/correction_diagnostic_v1"/source/"forecasts.csv")
        checked = 0
        tables = read(directory/"summary.csv")
        if source == "ecb":
            tables += read(directory/"annual.csv")
        for table in tables:
            rr = [r for r in rows if all(r[k] == table[k] for k in ["track", "target", "method"])
                  and ("year" not in table or r["date"][:4] == table["year"])
                  and (table.get("family", "all") == "all" or r["family"] == table["family"])]
            assert len(rr) == int(table["n"])
            if source == "ecb":
                expected = {"pooled_es95_pp": tail(rr), "mean_loss_pp": mean(rr, "realized_loss"),
                            "mean_predicted_es95_pp": mean(rr, "es95"),
                            "breach_rate": mean(rr, "var_breach")}
                if table["track"] == "A":
                    expected.update(mean_fz0=mean(rr, "fz0"), mean_pinball95=mean(rr, "pinball95"))
            else:
                expected = {"mean_relative_error": mean(rr, "relative_error"),
                            "mean_relative_regret": mean(rr, "relative_regret"), "mean_true_es": mean(rr, "true_es")}
            for key, value in expected.items():
                assert abs(float(table[key])-value) < 1e-11, (source, key)
                checked += 1
        for table in read(directory/"paired_differences.csv"):
            rr = [r for r in rows if r["track"] == table["track"] and r["target"] == table["target"]]
            a = [r for r in rr if r["method"] == table["candidate"]]
            b = [r for r in rr if r["method"] == table["reference"]]
            assert len(a) == len(b) == int(table["n_pairs"])
            if table["metric"] == "pooled_es95_pp":
                delta = tail(a)-tail(b)
            else:
                delta = mean(a, table["metric"])-mean(b, table["metric"])
            assert abs(delta-float(table["difference"])) < 1e-11
            assert float(table["ci_low"]) <= float(table["ci_high"])
            checked += 1
        receipt = {"status": "PASS", "forecast_rows": len(rows), "aggregate_numeric_cells_recomputed": checked,
                   "forecast_sha256": sha256(ROOT/"runs/correction_diagnostic_v1"/source/"forecasts.csv"),
                   "checks": ["all summary and annual mean endpoints", "independent fractional-tail integration", "all paired central estimates"],
                   "limitation": "Bootstrap endpoints are produced by the frozen analysis and tested pairing; this receipt independently recomputes central estimates, not interval coverage."}
        atomic_json(directory/"table_audit.json", receipt)
        receipts[source] = receipt
    import importlib.util
    spec = importlib.util.spec_from_file_location("report", ROOT/"scripts/build_correction_report.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert (ROOT/"docs/CORRECTION_DIAGNOSTIC_RESULTS.md").read_text() == module.render()
    print(json.dumps(receipts, indent=2))


if __name__ == "__main__":
    verify()
