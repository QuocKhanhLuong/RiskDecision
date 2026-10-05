"""Paired moving-block inference; all intervals pointwise, never conditional ES truth."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import numpy as np

from .data import atomic_json, sha256
from .models import METHODS
from .scoring import empirical_es


def read_rows(path):
    with Path(path).open() as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        for key in ("realized_loss", "var95", "es95", "pinball95", "fz0", "shortfall_residual"):
            r[key] = float(r[key]) if r[key] else np.nan
        r["weights"] = np.array(json.loads(r["weights"]))
        for key in ("fallback", "converged", "fz0_defined"):
            r[key] = r[key] == "True"
        r["var_breach"] = int(r["var_breach"])
    return rows


def write_csv(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def summary(rows):
    result = []
    keys = sorted({(r["track"], r["target"], r["method"]) for r in rows})
    for track, target, method in keys:
        rr = sorted([r for r in rows if (r["track"], r["target"], r["method"]) == (track, target, method)], key=lambda r: r["date"])
        losses = np.array([r["realized_loss"] for r in rr])
        weights = np.array([r["weights"] for r in rr])
        fz = np.array([r["fz0"] for r in rr])
        n = len(rr)
        result.append({"track": track, "target": target, "method": method, "n": n,
                       "first": rr[0]["date"], "last": rr[-1]["date"],
                       "mean_loss_pp": float(losses.mean()), "sd_loss_pp": float(losses.std(ddof=1)) if n>1 else 0.,
                       "pooled_es95_pp": float(empirical_es(losses)), "tail_mass_n": .05*n,
                       "max_loss_pp": float(losses.max()), "breaches": sum(r["var_breach"] for r in rr),
                       "breach_rate": float(np.mean([r["var_breach"] for r in rr])),
                       "mean_predicted_es95_pp": float(np.mean([r["es95"] for r in rr])),
                       "mean_pinball95": float(np.mean([r["pinball95"] for r in rr])) if track == "A" else "",
                       "mean_fz0": float(np.nanmean(fz)) if track == "A" and np.isfinite(fz).any() else "",
                       "fz0_defined_n": int(np.isfinite(fz).sum()), "fz0_undefined_n": int((~np.isfinite(fz)).sum()),
                       "mean_shortfall_residual_pp": float(np.mean([r["shortfall_residual"] for r in rr])),
                       "mean_hhi": float(np.mean((weights*weights).sum(1))),
                       "mean_half_l1_weight_change": float(np.abs(np.diff(weights, axis=0)).sum(1).mean()/2) if n>1 else 0.,
                       "weight_change_count": int(np.any(np.diff(weights, axis=0) != 0, axis=1).sum()),
                       "fallback_n": sum(r["fallback"] for r in rr), "nonconverged_n": sum(not r["converged"] for r in rr)})
    return result


def block_indices(rng, n, length, reps):
    if not 1 <= length <= n:
        raise ValueError("Invalid moving block length")
    starts = rng.integers(0, n-length+1, size=(reps, (n+length-1)//length))
    return (starts[:, :, None] + np.arange(length)[None, None, :]).reshape(reps, -1)[:, :n]


def bootstrap(rows, block, replicates=5000, seed=20261005):
    intervals, pairs = [], []
    for track, target in [("A", "equal_weight"), ("A", "historical_se_reference"), ("B", "own_selection")]:
        group = [r for r in rows if r["track"] == track and r["target"] == target]
        dates = sorted({r["date"] for r in group})
        lookup = {(r["date"], r["method"]): r for r in group}
        if len(lookup) != len(group) or len(group) != len(dates)*len(METHODS):
            raise ValueError("Unpaired/duplicate rows")
        fields = ["fz0", "pinball95", "var_breach", "shortfall_residual"] if track == "A" else ["realized_loss"]
        data = {key: np.array([[lookup[d, m][key] for m in METHODS] for d in dates]) for key in fields}
        rng = np.random.default_rng(seed)
        samples = {key: [] for key in fields}
        if track == "B":
            samples["pooled_es95_pp"] = []
        for offset in range(0, replicates, 100):
            ix = block_indices(rng, len(dates), min(block, len(dates)), min(100, replicates-offset))
            for key, a in data.items():
                samples[key].append(np.nanmean(a[ix], axis=1))
            if track == "B":
                samples["pooled_es95_pp"].append(empirical_es(data["realized_loss"][ix], axis=1))
        samples = {k: np.concatenate(v) for k, v in samples.items()}
        for metric, draws in samples.items():
            estimates = empirical_es(data["realized_loss"], axis=0) if metric == "pooled_es95_pp" else np.nanmean(data[metric], axis=0)
            for j, method in enumerate(METHODS):
                low, high = np.nanquantile(draws[:, j], [.025, .975])
                intervals.append({"track": track, "target": target, "method": method, "metric": metric,
                                  "block_length": block, "replicates": replicates, "n": len(dates),
                                  "estimate": float(estimates[j]), "ci_low": float(low), "ci_high": float(high)})
        c = METHODS.index("support_band50")
        for reference in ["historical_se_penalty", "support_mix50"]:
            j = METHODS.index(reference)
            for metric in (["fz0", "pinball95"] if track == "A" else ["pooled_es95_pp"]):
                if metric == "pooled_es95_pp":
                    diff = samples[metric][:, c] - samples[metric][:, j]
                    est = empirical_es(data["realized_loss"], axis=0)
                    estimate, n_pair = est[c]-est[j], len(dates)
                else:
                    # Identical finite date denominator for each paired contrast.
                    delta = data[metric][:, c] - data[metric][:, j]
                    n_pair = int(np.isfinite(delta).sum())
                    estimate = np.nanmean(delta)
                    pair_rng = np.random.default_rng(seed)
                    diff = np.concatenate([np.nanmean(delta[block_indices(pair_rng, len(dates), min(block, len(dates)), min(100, replicates-offset))], axis=1)
                                           for offset in range(0, replicates, 100)])
                low, high = np.nanquantile(diff, [.025, .975])
                pairs.append({"track": track, "target": target, "candidate": "support_band50", "reference": reference,
                              "metric": metric, "block_length": block, "replicates": replicates, "n_pair": n_pair,
                              "difference": float(estimate), "ci_low": float(low), "ci_high": float(high),
                              "interpretation": "candidate minus reference; smaller better; pointwise descriptive CI"})
    return intervals, pairs


def analyze(run, out, protocol):
    run, out = Path(run), Path(out)
    rows = read_rows(run / "forecasts.csv")
    receipt = json.loads((run / "receipt.json").read_text())
    if sha256(run/"forecasts.csv") != receipt["forecasts_sha256"]:
        raise ValueError("Forecast checksum mismatch")
    freeze = json.loads(Path(protocol).read_text())
    block = freeze["bootstrap"]["by_source"][receipt["source"]]["primary_block_length"]
    summary_rows = summary(rows)
    write_csv(out / "summary.csv", summary_rows)
    annual = []
    for year in sorted({r["date"][:4] for r in rows}):
        annual.extend({"year": year, **r} for r in summary([r for r in rows if r["date"].startswith(year)]))
    write_csv(out / "annual.csv", annual)
    all_ci, all_pair = [], []
    for b in sorted(set([block] + freeze["bootstrap"]["sensitivity_blocks"])):
        ci, pair = bootstrap(rows, b, freeze["bootstrap"]["replicates"], freeze["bootstrap"]["seed"])
        all_ci.extend(ci)
        all_pair.extend(pair)
        print(receipt["source"], receipt["split"], "bootstrap block", b, "complete", flush=True)
    write_csv(out / "intervals.csv", all_ci)
    write_csv(out / "paired_differences.csv", all_pair)
    diagnostics = json.loads((run / "diagnostics.json").read_text())
    counts = {}
    for m in METHODS:
        dd = [d[m] for d in diagnostics]
        counts[m] = {"dates": len(dd), "fallback_dates": sum(d["fallback"] for d in dd),
                     "nonconverged_dates": sum(not d["converged"] for d in dd),
                     "warning_dates": sum(bool(d.get("warnings") or d.get("base_gmm", {}).get("warnings")) for d in dd),
                     "failed_correction_steps": sum(not step["converged"] for d in dd for step in d.get("steps", []))}
    atomic_json(out / "diagnostic_counts.json", counts)
    atomic_json(out / "provenance.json", {"run_receipt": receipt, "config": json.loads((run/"config.json").read_text()),
                                          "protocol_sha256": sha256(protocol), "primary_block_length": block,
                                          "aggregate_sha256": {p.name: sha256(p) for p in sorted(out.glob("*.csv"))},
                                          "limitations": "Pointwise moving-block percentile intervals; stationarity approximation; no multiplicity-adjusted superiority or conditional calibration guarantee. B scores not a forecast tournament."})


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--protocol", required=True, type=Path)
    analyze(**vars(p.parse_args()))


if __name__ == "__main__":
    main()
