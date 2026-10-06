"""Supplementary reproduction and explicitly post-hoc failure localization."""
from pathlib import Path
import sys
import csv
import json
import hashlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from coverage_audit.core import *
from coverage_audit.run import contract
from local_market.stats import write_csv
from local_market.data import sha256, atomic_json

protocol, identity = contract()
directory = ROOT/"runs/coverage_audit_v1/cases"
out = ROOT/"results/coverage_audit_v1"
refits = []
for family, seed in [("gaussian", 62000), ("markov_volatility", 62099)]:
    with np.load(directory/f"{family}_{seed}.npz") as a:
        w = bank(2026)
        z, diag = gmm_fit(a["returns"][:256], seed)
        np.testing.assert_array_equal(z, a["scenarios"])
        for n in [256, 1024]:
            for j, anchor in enumerate(ANCHORS):
                key = f"n{n}_{anchor}"
                eta, h, heuristic, selected = features(z, a["returns"][256:256+n], w, anchor)
                np.testing.assert_array_equal(eta, a[key+"_eta"])
                np.testing.assert_array_equal(heuristic, a[key+"_v2_heuristic_radius"])
                assert selected == a[key+"_selected"]
                for method, block in zip(PROCEDURES[1:], [1, *protocol["blocks"][str(n)]]):
                    radius, _, _ = multiplier(h, block, 499, np.random.SeedSequence([seed, FAMILIES.index(family), n, j, block, 900000]))
                    np.testing.assert_array_equal(radius, a[key+"_"+method+"_radius"])
    refits.append({"family": family, "seed": seed, "status": "exact GMM, anchors, selector and all radii match"})

# Defined after looking at aggregate coverage to localize a surprising failure.
# Descriptive only: no new hyperparameters, confirmatory endpoints or recipe changes.
rows = []
for n in [256, 1024]:
    for anchor in ANCHORS:
        stats = []
        for seed in protocol["seeds"]:
            with np.load(directory/f"gaussian_{seed}.npz") as a:
                key = f"n{n}_{anchor}"
                delta = a[key+"_center"] - a[key+"_stationary_marginal"]
                radius = a[key+"_iid_max_t_radius"]
                stats.append(np.stack([delta < -radius-1e-12, delta > radius+1e-12, radius == 0]).reshape(3, 285, 3))
        s = np.array(stats)
        for j, q in enumerate(QUANTILES):
            rows.append({"status": "posthoc Gaussian localization, no recipe changes", "n": n, "anchor": anchor, "quantile": q,
                         "cases_upper_endpoint_below_truth": int(s[:, 0, :, j].any(1).sum()),
                         "cases_lower_endpoint_above_truth": int(s[:, 1, :, j].any(1).sum()),
                         "cases_any_zero_radius": int(s[:, 2, :, j].any(1).sum()),
                         "mean_failed_features_below_truth": float(s[:, 0, :, j].sum(1).mean()),
                         "mean_failed_features_above_truth": float(s[:, 1, :, j].sum(1).mean())})
write_csv(out/"gaussian_failure_localization.csv", rows)

table = json.loads((out/"table_receipt.json").read_text())
assert table["coverage_csv_sha256"] == sha256(out/"coverage.csv")
assert table["report_sha256"] == sha256(ROOT/"docs/SIMULTANEOUS_CALIBRATION_RESULTS.md")
receipt = {"status": "PASS", "identity": identity, "refits": refits, "numeric_report_values_bound_to_csv": table["numeric_table_values_from_csv"],
           "posthoc_localization_sha256": sha256(out/"gaussian_failure_localization.csv"),
           "scope": "Coordinator checks, not independent review. Two exact refits plus frozen full-case artifact audit."}
atomic_json(out/"supplementary_audit.json", receipt)
print("PASS: two complete refits, all report table hashes, posthoc Gaussian localization")
