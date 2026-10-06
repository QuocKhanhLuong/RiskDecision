"""Render every numeric coverage-table cell directly from audited aggregate CSV."""
import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from local_market.data import sha256, atomic_json

OUT = ROOT/"results/coverage_audit_v1"
with (OUT/"coverage.csv").open() as f:
    rows = list(csv.DictReader(f))
audit = json.loads((OUT/"audit.json").read_text())
receipt = json.loads((OUT/"provenance.json").read_text())
assert audit["status"] == "PASS" and audit["coverage_csv_sha256"] == sha256(OUT/"coverage.csv")
families = ["gaussian", "student_t4", "asymmetric_crash", "ar1", "markov_volatility"]
procedures = ["v2_heuristic", "iid_max_t", "block_short_max_t", "block_long_max_t"]
anchors = ["base_only", "reused_mixture"]
indexed = {(r["family"], int(r["n"]), r["anchor"], r["procedure"], r["estimand"]): r for r in rows}
assert len(indexed) == 160
lines = ["# Simultaneous tail-moment coverage: executed feasibility audit", "",
         "Freeze commit: `77ba092`. Protocol and code were committed and pushed before the500-case run. "
         "[Protocol](SIMULTANEOUS_CALIBRATION_PROTOCOL.md), [decision](CALIBRATION_RESEARCH_DECISION.md), "
         "[aggregate CSV](../results/coverage_audit_v1/coverage.csv). No new method was fitted, tuned or promoted.", "",
         f"Completed **{receipt['cases']} series / {receipt['rows']:,} rows / {audit['strata']} strata**. The recorded invocation computed "
         f"{receipt['computed_this_invocation']} cases in{receipt['wall_seconds']:.2f}s with2 numerical processes (remaining cases, if any, were verified cached results). "
         f"Audit regenerated{audit['synthetic_inputs_regenerated_and_equal']} inputs and recomputed"
         f"{audit['metrics_recomputed_from_arrays']:,} metrics from local arrays. "
         f"GMM nonconvergence:{receipt['gmm_nonconverged']}; warnings:{receipt['gmm_warnings']}. "
         "70 tests passed before execution. All931 historical files were reverified unchanged.", "",
         "## Simultaneous coverage of all855 features", "",
         "Entries are covered cases out of100, followed by the pointwise Wilson95% Monte Carlo interval in percent. "
         "The bootstrap recipes target95%; v2 heuristic has no95% nominal guarantee. IID target rows repeat across the two estimands by construction. "
         "Neither individual intervals nor160 correlated strata constitute a multiple-testing-adjusted claim.", ""]
numeric_cells = 0
for estimand in ["stationary_marginal", "next_conditional"]:
    for n in [256, 1024]:
        lines += [f"### {estimand}, n={n}", "", "| Family / anchor | v2 heuristic | IID max-t | Block short | Block long |",
                  "|---|---:|---:|---:|---:|"]
        for family in families:
            for anchor in anchors:
                cells = []
                for procedure in procedures:
                    r = indexed[family, n, anchor, procedure, estimand]
                    cells.append(f"{int(r['all_covered_count'])} [{100*float(r['all_covered_lo']):.1f}, {100*float(r['all_covered_hi']):.1f}]")
                    numeric_cells += 3
                lines.append(f"| {family} / {anchor} | " + " | ".join(cells) + " |")
        lines.append("")
lines += ["## Radius size", "",
          "Mean across100 seeds of the median across855 features of radius/(0.05×stationary ES95). "
          "This is a hinge uncertainty scale, **not an ES confidence interval**. Width is identical for the marginal/conditional target because only the evaluator changes.", "",
          "| Family / n / anchor | v2 heuristic | IID max-t | Block short | Block long |", "|---|---:|---:|---:|---:|"]
for family in families:
    for n in [256, 1024]:
        for anchor in anchors:
            cells = [f"{float(indexed[family,n,anchor,p,'stationary_marginal']['width_ratio_median_mean']):.3f}" for p in procedures]
            numeric_cells += 4
            lines.append(f"| {family} / {n} / {anchor} | " + " | ".join(cells) + " |")
lines += ["", "## Pointwise and selected-feature coverage", "",
          "The CSV also records fixed equal-weight/q95 coverage, coverage of the feature selected by empirical prior/calibration discrepancy, "
          "average feature coverage, widths, critical values and zero-SE counts. These are secondary diagnostics; selecting one successful feature cannot validate the simultaneous claim.", "",
          "| Family / n / base_only | IID equal q95 | IID selected | Short-block equal q95 | Short-block selected |", "|---|---:|---:|---:|---:|"]
for family in families:
    for n in [256, 1024]:
        cells = []
        for procedure in ["iid_max_t", "block_short_max_t"]:
            r = indexed[family,n,"base_only",procedure,"stationary_marginal"]
            cells.extend(str(int(r[c+"_count"])) for c in ["equal_q95_covered", "selected_covered"])
        numeric_cells += 4
        lines.append(f"| {family} / {n} | " + " | ".join(cells) + " |")
lines += ["", "## Limits and reproducibility", "",
          "A supplementary check refits Gaussian seed62000 and Markov seed62099, reconstructing GMM scenarios, anchors, selections and every radius exactly. "
          "[Post-hoc Gaussian localization](../results/coverage_audit_v1/gaussian_failure_localization.csv) examines which quantiles fail and on which side. "
          "That analysis was added after viewing coverage, is descriptive, and changes no frozen recipe.", "",
          "These are synthetic stationary processes with exact evaluator distributions,100 seeds per stratum and499 multipliers. "
          "Student t4, unbounded hinges, random thresholds, studentization and dependent contiguous fitting/calibration blocks require assumptions beyond a generic block-bootstrap citation. "
          "The three-threshold grid does not imply all-threshold ES or selection-regret guarantees. Markov conditional targets use a latent-state oracle. "
          "Stationary marginal calibration is not next-period conditional calibration.", "",
          "Independent review: **NOT RUN**. Orca Claude launch failed with `zsh: command not found: claude`; the task was never reviewed. "
          "The abandoned dispatch's shell was retained by Orca with `identity_unproven`. No CPU worker is counted as an independent agent.", "",
          "No market data were downloaded again, no market validation/final test rerun, and no candidate/hyperparameter was selected from this experiment. "
          "Raw FX and generated per-case arrays remain local. No trading profit or Sharpe claim.", "",
          "```bash", "rtk proxy bash scripts/reproduce_coverage_audit.sh", "```", "",
          "The runner verifies frozen source/protocol hashes and rejects changed or incomplete cached cases. "
          "On this pinned platform generated case arrays are reproducible; cross-platform GMM/BLAS bit identity is not promised. "
          "The report builder maps all table values from the audited CSV; local audit checks population formulas and per-case coverage, but does not re-bootstrap every case.", ""]
report = ROOT/"docs/SIMULTANEOUS_CALIBRATION_RESULTS.md"
report.write_text("\n".join(lines))
atomic_json(OUT/"table_receipt.json", {"coverage_csv_sha256": sha256(OUT/"coverage.csv"),
            "report_sha256": sha256(report), "numeric_table_values_from_csv": numeric_cells,
            "strata_present": len(indexed), "builder_sha256": sha256(Path(__file__))})
print("Rendered", numeric_cells, "numeric table values from CSV")
