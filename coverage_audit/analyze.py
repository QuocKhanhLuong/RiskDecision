"""Verify local per-feature evidence and publish only aggregate coverage tables."""
from .run import ROOT, contract
from .core import ANCHORS, PROCEDURES, generate, conditional, population_hinge, bank, truth, evaluate
from local_market.data import sha256, atomic_json
from local_market.stats import write_csv
from collections import defaultdict
from pathlib import Path
import argparse
import csv
import json
import numpy as np

KEYS = ["family", "n", "anchor", "procedure", "estimand"]
ENDPOINTS = ["all_covered", "equal_q95_covered", "selected_covered"]


def wilson(k, n):
    if not 0 <= k <= n or n <= 0:
        raise ValueError("Invalid binomial counts")
    z = 1.959963984540054
    center = (k/n + z*z/(2*n))/(1+z*z/n)
    half = z*np.sqrt((k/n)*(1-k/n)/n+z*z/(4*n*n))/(1+z*z/n)
    return max(0., center-half), min(1., center+half)


def summarize(rows, expected=100):
    groups = defaultdict(list)
    for row in rows:
        groups[tuple(str(row[k]) for k in KEYS)].append(row)
    output = []
    for key, values in sorted(groups.items()):
        if len(values) != expected or len({int(v["seed"]) for v in values}) != expected:
            raise ValueError("Missing or duplicated seed within a stratum")
        out = dict(zip(KEYS, key)); out["replications"] = len(values)
        for endpoint in ENDPOINTS:
            k = sum(int(v[endpoint]) for v in values)
            lo, hi = wilson(k, len(values))
            out.update({endpoint+"_count": k, endpoint+"_rate": k/len(values),
                        endpoint+"_lo": lo, endpoint+"_hi": hi})
        for name in ["feature_coverage", "width_ratio_median", "width_ratio_max", "critical", "zero_se_features"]:
            out[name+"_mean"] = float(np.mean([float(v[name]) for v in values]))
        out["width_ratio_median_p95"] = float(np.quantile([float(v["width_ratio_median"]) for v in values], .95))
        output.append(out)
    return output


def analyze(run, out):
    p, identity = contract()
    run, out = Path(run), Path(out)
    receipt = json.loads((run/"receipt.json").read_text())
    if receipt["identity"] != identity or receipt["cases_csv_sha256"] != sha256(run/"cases.csv"):
        raise ValueError("Receipt mismatch")
    with (run/"cases.csv").open() as f:
        rows = list(csv.DictReader(f))
    expected_cases = {f"{family}_{seed}.json" for family in p["families"] for seed in p["seeds"]}
    if set(receipt["case_sha256"]) != expected_cases or len(rows) != 16000:
        raise ValueError("Incomplete experiment")
    w = bank(p["bank_seed"])
    rebuilt, cells = [], 0
    for filename in sorted(expected_cases):
        path = run/"cases"/filename
        if sha256(path) != receipt["case_sha256"][filename]:
            raise ValueError("Case checksum mismatch")
        value = json.loads(path.read_text())
        if value["identity"] != identity or sha256(path.with_suffix(".npz")) != value["arrays_sha256"]:
            raise ValueError("Case identity mismatch")
        x, marginal, states = generate(value["seed"], value["family"])
        es = truth(w, marginal)[1]
        with np.load(path.with_suffix(".npz")) as arrays:
            np.testing.assert_array_equal(x, arrays["returns"])
            np.testing.assert_array_equal(states, arrays["states"])
            for row in value["rows"]:
                n, anchor = row["n"], row["anchor"]
                key = f"n{n}_{anchor}"
                eta, center = arrays[key+"_eta"], arrays[key+"_center"]
                calc_center = np.maximum(np.repeat(-x[256:256+n] @ w.T, 3, axis=1)-eta, 0).mean(0)
                np.testing.assert_allclose(center, calc_center, atol=1e-12, rtol=0)
                target = (marginal if row["estimand"] == "stationary_marginal" else
                          conditional(value["family"], marginal, x[255+n], states[255+n]))
                population = population_hinge(np.repeat(w, 3, axis=0), eta, target)
                np.testing.assert_allclose(population, arrays[key+"_"+row["estimand"]], atol=1e-12, rtol=0)
                np.testing.assert_allclose(es, arrays[key+"_es_marginal"], atol=1e-12, rtol=0)
                metrics = evaluate(calc_center, arrays[key+"_"+row["procedure"]+"_radius"], population, es, int(arrays[key+"_selected"]))
                for name, v in metrics.items():
                    np.testing.assert_allclose(v, row[name], atol=1e-12, rtol=0)
                    cells += 1
                rebuilt.append(row)
    index = lambda r: (r["family"], int(r["seed"]), int(r["n"]), r["anchor"], r["procedure"], r["estimand"])
    for a, b in zip(sorted(rows, key=index), sorted(rebuilt, key=index)):
        if index(a) != index(b):
            raise ValueError("CSV row mismatch")
        for key, val in b.items():
            if isinstance(val, (int, float)):
                np.testing.assert_allclose(float(a[key]), val, atol=1e-12, rtol=0)
            elif a[key] != val:
                raise ValueError("CSV content mismatch")
    summary = summarize(rows)
    if len(summary) != 160:
        raise ValueError("Missing aggregate stratum")
    out.mkdir(parents=True, exist_ok=True)
    write_csv(out/"coverage.csv", summary)
    # Raw synthetic cases stay local; public receipts contain hashes and counts.
    public = {k: v for k, v in receipt.items() if k != "case_sha256"}
    public["case_manifest_sha256"] = sha256(run/"receipt.json")
    atomic_json(out/"provenance.json", public)
    atomic_json(out/"audit.json", {"status": "PASS", "cases": 500, "rows": len(rows), "strata": len(summary),
                "metrics_recomputed_from_arrays": cells, "synthetic_inputs_regenerated_and_equal": 500,
                "coverage_csv_sha256": sha256(out/"coverage.csv"), "identity": identity,
                "limits": "Checks feature means, analytic populations, coverage and normalization; does not refit GMM or re-bootstrap all cases."})
    print("PASS", len(rows), "rows;", cells, "metrics recomputed;", len(summary), "strata")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run", type=Path, default=ROOT/"runs/coverage_audit_v1")
    ap.add_argument("--out", type=Path, default=ROOT/"results/coverage_audit_v1")
    analyze(**vars(ap.parse_args()))
