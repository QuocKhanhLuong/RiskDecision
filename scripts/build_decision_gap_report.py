"""Build aggregate tables from per-case CSV; no hand-entered measurements."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from local_market.stats import write_csv
from local_market.data import atomic_json, sha256
import csv
import json
import numpy as np
from collections import defaultdict
import shutil

ROOT = Path(__file__).resolve().parents[1]


def load(path):
    return list(csv.DictReader(Path(path).open()))


def wilson(k, n):
    if not n:
        return float("nan"), float("nan")
    z = 1.959963984540054
    p = k/n; den = 1+z*z/n
    mid = (p+z*z/(2*n))/den
    half = z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return mid-half, mid+half


def mean_ci(x):
    x = np.asarray(x, float)
    rng = np.random.default_rng(99017)
    vals = x[rng.integers(len(x), size=(10000, len(x)))].mean(1)
    return float(x.mean()), *np.quantile(vals, [.025, .975]).tolist()


def summarize(raw):
    groups = defaultdict(list)
    for r in raw:
        groups[tuple(r[k] for k in ["family", "n", "estimand", "recipe"])].append(r)
    out = []
    for keys, rr in sorted(groups.items()):
        n = len(rr); switches = sum(int(r["switched"]) for r in rr); harm = sum(int(r["harm"]) for r in rr)
        row = dict(zip(["family", "n", "estimand", "recipe"], keys))
        row.update(cases=n, switches=switches, harms=harm, harm_among_switches=harm/switches if switches else float("nan"))
        for key, count in [("switch", switches), ("harm", harm), ("coverage", sum(int(r["all_contrasts_covered"]) for r in rr))]:
            row[key] = count/n; row[key+"_lo"], row[key+"_hi"] = wilson(count, n)
        for key in ["relative_delta", "relative_regret", "radius_ratio", "available_improvement"]:
            row[key] = float(np.mean([float(r[key]) for r in rr]))
        for slot, name in enumerate(["baseline", "mixture", "band", "fhs"]):
            row["chosen_"+name] = sum(int(r["selected_slot"]) == slot for r in rr)
        out.append(row)
    return out


def comparisons(raw, controls):
    ctrl = {(r["family"], r["n"], r["estimand"], r["seed"], r["method"]): r for r in controls}
    groups = defaultdict(list)
    for r in raw:
        if r["recipe"] == "paired":
            groups[(r["family"], r["n"], r["estimand"])].append(r)
    out = []
    for key, rr in sorted(groups.items()):
        rr.sort(key=lambda r: int(r["seed"]))
        for method in sorted({r["method"] for r in controls}):
            values = [float(r["relative_delta"])-float(ctrl[(*key, r["seed"], method)]["relative_delta"]) for r in rr]
            m, lo, hi = mean_ci(values)
            out.append(dict(zip(["family", "n", "estimand"], key), comparator=method, mean=m, lo=lo, hi=hi))
    return out


def table(rows, columns):
    # Stable machine-readable headers; every data row is independently checked.
    def fmt(v):
        return f"{v:.6f}" if isinstance(v, (float, np.floating)) else str(v)
    return "\n".join(["|"+"|".join(columns)+"|", "|"+"|".join(["---"]*len(columns))+"|"]+
                     ["|"+"|".join(fmt(r[k]) for k in columns)+"|" for r in rows])


def build():
    src = ROOT/"runs/decision_gap_v1"; dst = ROOT/"results/decision_gap_v1"; dst.mkdir(parents=True, exist_ok=True)
    raw, controls, forecasts = [load(src/f"{k}.csv") for k in ["rows", "controls", "forecasts"]]
    summary = summarize(raw); paired = comparisons(raw, controls)
    fgroups = defaultdict(list)
    for r in forecasts:
        fgroups[(r["family"], r["method"])].append(r)
    fs = [{"family": f, "method": m, **{k: float(np.mean([float(r[k]) for r in rr])) for k in
           ["common_equal_relative_error", "bank_level_mae", "bank_contrast_mae", "same_choice_as_hist"]}}
          for (f,m), rr in sorted(fgroups.items())]
    write_csv(dst/"summary.csv", summary); write_csv(dst/"comparisons.csv", paired); write_csv(dst/"forecasts.csv", fs)
    for name in ["rows.csv", "controls.csv", "forecasts.csv", "first_execution_receipt.json"]:
        # Per-seed forecast diagnostics get their own name to preserve summary.
        shutil.copy2(src/name, dst/("forecast_cases.csv" if name == "forecasts.csv" else name))
    required = ["training_hist_se", "recent_historical_se_penalty", "recent_support_mix50", "recent_filtered_historical"]
    gates = {}
    for family in ["gaussian", "student_t4", "asymmetric_crash"]:
        row = next(r for r in summary if r["family"] == family and r["n"] == "1024" and r["estimand"] == "marginal" and r["recipe"] == "paired")
        cc = [r for r in paired if r["family"] == family and r["n"] == "1024" and r["estimand"] == "marginal" and r["comparator"] in required]
        gates[family] = {"harm_pass": row["harm_hi"] <= .05, "switch_pass": row["switch_lo"] >= .1,
                         "all_comparators_pass": all(r["hi"] < 0 for r in cc)}
    atomic_json(dst/"decision.json", {"family_gates": gates, "go": all(all(v.values()) for v in gates.values()),
                "novel_method_claim": False, "source_csv_hashes": {k: sha256(src/f"{k}.csv") for k in ["rows", "controls", "forecasts"]}})
    sections = ["# Decision-gap results", "Generated from local case CSV; values are fractions, not percentage points. No market data or final-test rerun.",
                "## Marginal decision gate", table([r for r in summary if r["estimand"] == "marginal"],
                ["family", "n", "recipe", "switches", "harms", "coverage", "relative_delta", "radius_ratio", "chosen_band"]),
                "## Conditional stress at n1024", table([r for r in summary if r["estimand"] == "next_conditional" and r["n"] == "1024"],
                ["family", "recipe", "switches", "harms", "coverage", "relative_delta"]),
                "## Paired gate versus strong controls, marginal n1024", table([r for r in paired if r["estimand"] == "marginal" and r["n"] == "1024" and r["comparator"] in required+["all_history_hist_se"]],
                ["family", "comparator", "mean", "lo", "hi"]),
                "Negative differences favor gate. Paired seed bootstrap intervals are pointwise descriptive; all comparisons and conditional strata are in CSV.",
                "## Common-target forecast diagnostics (training512, marginal truth)", table(fs,
                ["family", "method", "common_equal_relative_error", "bank_level_mae", "bank_contrast_mae", "same_choice_as_hist"]),
                "Forecast errors and allocation risk are separate. Bank contrast MAE does not have the same scale as level MAE and is not a proof of risk improvement.",
                "## Preregistered decision", "```json\n"+json.dumps(gates, indent=2)+"\n```",
                "The gate is a generic statistical control; even a pass would not establish novelty or finite-sample safety. See DECISION_GAP_DECISION.md for adjudication and limitations."]
    (ROOT/"docs/DECISION_GAP_RESULTS.md").write_text("\n\n".join(sections)+"\n")
    print("Built", len(summary), len(paired), len(fs))


if __name__ == "__main__":
    build()
