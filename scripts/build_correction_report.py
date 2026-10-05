#!/usr/bin/env python3
"""Render all reported diagnostic numbers directly from audited public CSVs."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/"results/correction_diagnostic_v1"


def read(source, name):
    with (BASE/source/(name+".csv")).open() as f:
        return list(csv.DictReader(f))


def number(value):
    return f"{float(value):.6f}"


def render():
    text = ["# Correction mechanism — development results", "",
            "Generated from audited CSVs by `scripts/build_correction_report.py`. All evidence below is development-only, after the earlier market final tests were seen. No new method or superiority claim is selected from these tables.", "",
            "Read [protocol](CORRECTION_DIAGNOSTIC_PROTOCOL.md), [identifiability analysis](CORRECTION_IDENTIFIABILITY.md) and [primary-source novelty audit](NOVELTY_AUDIT_2026_10.md).", ""]
    for source in ["synthetic", "ecb"]:
        audit = json.loads((BASE/source/"audit.json").read_text())
        provenance = json.loads((BASE/source/"provenance.json").read_text())
        rows = read(source, "summary")
        if source == "synthetic":
            rows = [r for r in rows if r["family"] == "all"]
        lookup = {(r["track"], r["target"], r["method"]): r for r in rows}
        text += [f"## {source.upper()}", "", f"{audit['windows']} windows; {audit['rows']} forecast/selection rows. Artifact audit: **{audit['status']}**. Invocation wall time: {provenance['receipt']['wall_seconds']:.2f}s; {provenance['receipt']['computed_this_invocation']} windows computed this invocation, with two numerical processes. These processes are not independent agents.", ""]
        if source == "synthetic":
            text += ["Archived validation inputs are exposed development:20 seed clusters ×4 families. Local GMM scenario draws can differ across platform linear algebra implementations; this is a local diagnostic refit, not an overwrite or bitwise reproduction of the original snapshot.", "",
                     "| Method | Same equal target relative ES error | Same historical-SE target relative ES error | Own-selection relative population regret |", "|---|---:|---:|---:|"]
        else:
            text += ["All eligible2010–2015 ECB development origins, one reference session per target. Reference changes are not executable returns. Latest-vintage and assumed-availability limitations remain.", "",
                     "| Method | Same equal target FZ0 | Same historical-SE target FZ0 | Own-selection pooled ES95 (pp) |", "|---|---:|---:|---:|"]
        methods = ["historical", "historical_se_penalty", "support_mix50", "support_band50", "support_point50", "random_band50", "filtered_historical"]
        for method in methods:
            eq = lookup["A", "equal_weight", method]
            ref = lookup["A", "historical_se_reference", method]
            own = lookup["B", "own_selection", method]
            akey, bkey = ("mean_relative_error", "mean_relative_regret") if source == "synthetic" else ("mean_fz0", "pooled_es95_pp")
            text.append(f"| {method} | {number(eq[akey])} | {number(ref[akey])} | {number(own[bkey])} |")
        note = "Lower is better within each column."
        if source == "synthetic":
            note += " Synthetic relative quantities are fractions, not percentages. Population regret uses the finite285-bank oracle; Markov truth additionally conditions on an evaluator-only latent state."
        text += ["", note, "",
                 "| Correction | Unchanged ES surface | Same selection as mixture | All prior moments inside band | Mean total variation from prior | Converged |", "|---|---:|---:|---:|---:|---:|"]
        for r in read(source, "mechanism"):
            if r["group"] == "all":
                text.append(f"| {r['method']} | {r['unchanged_surface_n']}/{r['n']} | {r['same_selection_as_mix_n']}/{r['n']} | {r['prior_all_within_band_n']}/{r['n']} | {number(r['mean_tv_from_prior'])} | {r['converged_n']}/{r['n']} |")
        text += ["", "| Target / endpoint | Band minus reference | Difference | Pointwise95% CI |", "|---|---|---:|---:|"]
        for r in read(source, "paired_differences"):
            if int(r["block"]) == (17 if source == "ecb" else 0):
                text.append(f"| {r['target']} / {r['metric']} | {r['reference']} | {number(r['difference'])} | [{number(r['ci_low'])}, {number(r['ci_high'])}] |")
        text += ["", "Negative differences favor band. These are exploratory intervals; no multiplicity adjustment. ECB uses paired moving blocks17 here, with5/20/60 all in CSV. Synthetic resamples20 seed clusters with all four families kept together.", "",
                 f"Full CSVs: [summary](../results/correction_diagnostic_v1/{source}/summary.csv), [mechanism](../results/correction_diagnostic_v1/{source}/mechanism.csv), [decomposition](../results/correction_diagnostic_v1/{source}/decomposition.csv), [paired differences](../results/correction_diagnostic_v1/{source}/paired_differences.csv).", ""]
    text += ["## Interpretation limits and reproduction", "",
             "ECB decomposition uses the training calibration block as its reference, not true ES. Synthetic decomposition has an analytical population evaluator. Reported mean absolute components are descriptive, correlated terms; they are not additive shares of total absolute error and do not identify causal contributions.", "",
             "Finite nonconvergence is retained; no model-specific date deletion. Independent Orca review did not execute because worker readiness failed. No market validation/test rerun, new dataset, new method promotion, profit or Sharpe.", "",
             "Reproduce with the existing verified cache and pinned `.venv`:", "", "```bash", "rtk proxy bash scripts/reproduce_correction_diagnostic.sh", "```", "",
             "The source/config freeze rejects changed diagnostic code. Original market source and history remain unchanged. Per-date market outputs are local under ignored `runs/correction_diagnostic_v1/`.", ""]
    return "\n".join(text)


if __name__ == "__main__":
    (ROOT/"docs/CORRECTION_DIAGNOSTIC_RESULTS.md").write_text(render())
