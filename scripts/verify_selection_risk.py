#!/usr/bin/env python3
"""Read-only numerical verification of run artifacts; no forecaster fitting.

Run from the repository root with --out runs/selection_risk/<run_id>.
Uses direct array arithmetic and numerical survival integration, independently
of the new evaluator and summary functions. This is not independent peer review.
"""
import argparse
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import time

import numpy as np
from scipy.integrate import quad
from scipy.special import ndtr

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_csv(path):
    with path.open() as stream:
        return list(csv.DictReader(stream))


def verify(base):
    start = time.perf_counter()
    preflight = json.loads((base / "preflight.json").read_text())
    for name, expected in preflight["protected_tracked_files"].items():
        assert sha(ROOT / name) == expected, name
    for name, expected in preflight["imported_files"].items():
        assert sha(base / "historical_snapshot" / name) == expected, name
    spec = importlib.util.spec_from_file_location("historical_truth_only", ROOT / "quant_research_v2/src/research.py")
    old = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(old)
    counts, max_quadrature_discrepancy = {}, 0.
    for stage, expected_cases, expected_rows in [("q0", 320, 11200), ("pilot", 128, 3072)]:
        directory = base / stage
        freeze = json.loads((directory / "freeze.json").read_text())
        for name, expected in freeze["identity"]["sources"].items():
            assert sha(ROOT / name) == expected, name
        rows = read_csv(directory / "crossed_rows.csv")
        assert len(rows) == expected_rows
        cases = {}
        for row in rows:
            cases.setdefault((row["family"], int(row["seed"])), []).append(row)
        assert len(cases) == expected_cases
        split = read_csv(directory / "split_rows.csv") if stage == "pilot" else []
        for (family, seed), case_rows in cases.items():
            path = (base / "historical_snapshot/quant_research_v2/results/test" if stage == "q0" else directory / "arrays") / f"{family}_{seed}.npz"
            with np.load(path, allow_pickle=False) as a:
                w, x, te = a["weights"], a["returns"], a["true_es"]
                assert w.shape == (285, 8) and x.shape == (512, 8)
                for suffix in ("es", "var"):
                    np.testing.assert_array_equal(a["historical_"+suffix], a["historical_se_penalty_"+suffix])
                # Independent empirical quantile formula, no use of core.py.
                losses = -x @ w.T
                vh = np.quantile(losses, .95, axis=0, method="inverted_cdf")
                eh = vh + np.maximum(losses-vh, 0).mean(axis=0)/.05
                np.testing.assert_allclose(eh, a["historical_es"], rtol=1e-12, atol=1e-12)
                seh = (np.maximum(losses-vh, 0)/.05).std(axis=0, ddof=1)/np.sqrt(512)
                for row in case_rows:
                    selector, forecaster = row["selector"], row["forecaster"]
                    j = int(row["portfolio_id"])
                    if selector == "fixed_bank":
                        ii = np.arange(285)
                        assert j == -1
                    else:
                        want = 0 if selector == "equal_weight" else int(np.argmin(eh+seh)) if selector == "historical_se_penalty" else int(np.argmin(a[selector+"_es"]))
                        assert j == want
                        ii = [j]
                    pred = a[forecaster+"_es"][ii]
                    expected = {"predicted_es": pred.mean(), "true_es": te[ii].mean(),
                                "relative_error": (np.abs(pred-te[ii])/te[ii]).mean(),
                                "signed_relative_error": ((pred-te[ii])/te[ii]).mean(),
                                "relative_regret": (te[ii]/te.min()-1).mean(),
                                "hhi": (w[ii]**2).sum(axis=1).mean()}
                    for key, value in expected.items():
                        np.testing.assert_allclose(float(row[key]), value, rtol=1e-12, atol=1e-12)
                if stage == "pilot":
                    regenerated, pars = old.generate(seed, family)
                    np.testing.assert_array_equal(x, regenerated)
                    for row in [r for r in split if r["family"] == family and int(r["seed"]) == seed]:
                        train, held = (x[:256], x[256:]) if row["fold"] == "A_to_B" else (x[256:], x[:256])
                        losses = -train @ w.T
                        v = np.quantile(losses, .95, axis=0, method="inverted_cdf")
                        e = v + np.maximum(losses-v, 0).mean(axis=0)/.05
                        j = int(np.argmin(e))
                        assert j == int(row["portfolio_id"])
                        np.testing.assert_allclose(v[j], float(row["threshold"]), rtol=1e-12, atol=1e-12)
                        observed = train if row["estimator"] == "resubstitution" else held
                        objective = v[j] + np.maximum(-observed @ w[j]-v[j], 0).mean()/.05
                        np.testing.assert_allclose(objective, float(row["estimate"]), rtol=1e-12, atol=1e-12)
                        m = -pars["mu"] @ w[j]
                        sd = np.sqrt(np.einsum("i,kij,j->k", w[j], pars["cov"], w[j]))
                        stoploss, error = quad(lambda z: float(pars["p"] @ ndtr((m-z)/sd)), v[j], np.inf,
                                               epsabs=1e-10, epsrel=1e-10)
                        assert error < 1e-8
                        target = v[j] + stoploss/.05
                        discrepancy = abs(target-float(row["true_objective"]))
                        max_quadrature_discrepancy = max(max_quadrature_discrepancy, discrepancy)
                        assert discrepancy < 1e-8
                        np.testing.assert_allclose(((objective-target)/target)**2,
                                                   float(row["squared_relative_error"]), atol=1e-10, rtol=1e-10)
        # Verify each summary mean by family-balanced seed clusters directly.
        summaries = read_csv(directory / "crossed_summary.csv")
        for r in summaries:
            subset = [s for s in rows if s["forecaster"] == r["forecaster"] and s["selector"] == r["selector"]
                      and (r["scope"] == "overall" or s["family"] == r["scope"])]
            np.testing.assert_allclose(np.mean([float(s[r["metric"]]) for s in subset]), float(r["mean"]), atol=1e-12)
        counts[stage] = {"cases": len(cases), "crossed_rows": len(rows), "split_rows": len(split),
                         "summary_means": len(summaries)}
    sr = read_csv(base / "pilot/split_rows.csv")
    lookup = {(r["family"], int(r["seed"]), r["estimator"]): float(r["squared_relative_error"])
              for r in sr if r["fold"] == "A_to_B"}
    seeds = sorted({seed for _,seed,_ in lookup})
    differences = np.array([np.mean([lookup[f,s,"independent_split"]-lookup[f,s,"resubstitution"]
                                    for f in ("gaussian", "asymmetric_crash")]) for s in seeds])
    draws = np.random.default_rng(871032).integers(64, size=(10000,64))
    ci = np.quantile(differences[draws].mean(axis=1), [.025, .975])
    primary = [r for r in read_csv(base / "pilot/split_summary.csv") if r["primary"] == "True"]
    assert len(primary) == 1
    np.testing.assert_allclose([differences.mean(), *ci], [float(primary[0][k]) for k in ("mean", "ci_low", "ci_high")], atol=1e-12)
    return {"status": "PASS", "verifier_sha256": sha(__file__), "counts": counts,
            "protected_tracked_files_unchanged": len(preflight["protected_tracked_files"]),
            "imported_original_files_unchanged": len(preflight["imported_files"]),
            "max_frozen_objective_quadrature_discrepancy": max_quadrature_discrepancy,
            "primary_paired_cluster_interval_reproduced": True, "seconds": time.perf_counter()-start,
            "scope": "Separate numerical verification; not independent reviewer, market validation or OIC reproduction"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.out)
    (args.out / "verification.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
