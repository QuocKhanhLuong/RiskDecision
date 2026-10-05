"""Atomic/resumable two-track rolling FX experiment. Final horizon is one session."""
from __future__ import annotations

from .models import METHODS, bank, forecast
from .scoring import score
from .data import load_panel, sha256, atomic_json
import argparse
from concurrent.futures import ProcessPoolExecutor
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SPLITS = {"ecb": {"development": ["2010-01-01", "2015-12-31"], "validation": ["2016-01-01", "2019-12-31"], "test": ["2020-01-01", "2025-12-31"]},
          "boc": {"development": ["2017-01-01", "2020-12-31"], "validation": ["2021-01-01", "2022-12-31"], "test": ["2023-01-01", "2025-12-31"]}}


def content_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def source_hashes():
    paths = sorted((ROOT / "local_market").glob("*.py")) + [ROOT / "quant_research_v2/src/research.py", ROOT / "requirements-local.lock"]
    return {str(p.relative_to(ROOT)): sha256(p) for p in paths}


def training_indices(index, valid, window=512, gap=1):
    end = index - gap
    if end < window or not valid[index] or not valid[end-window:end].all():
        return None
    return np.arange(end-window, end)


def evaluate(x, y, seed):
    """Fit before scoring. Every A row in a target group has identical weights/loss."""
    w = bank(2026)
    risks, chosen, diagnostics = forecast(x, w, seed)
    rows = []
    targets = {"equal_weight": 0, "historical_se_reference": chosen["historical_se_penalty"]}
    for method in METHODS:
        v, e = risks[method]
        for target, j in targets.items():
            rows.append({"track": "A", "target": target, "method": method, "portfolio_id": j,
                         "weights": w[j].tolist(), **score(float(-y @ w[j]), float(v[j]), float(e[j])),
                         "fallback": diagnostics[method]["fallback"], "converged": diagnostics[method]["converged"]})
        j = chosen[method]
        rows.append({"track": "B", "target": "own_selection", "method": method, "portfolio_id": j,
                     "weights": w[j].tolist(), **score(float(-y @ w[j]), float(v[j]), float(e[j])),
                     "fallback": diagnostics[method]["fallback"], "converged": diagnostics[method]["converged"]})
    return rows, diagnostics


def window_job(job):
    x, y, metadata, out, identity = job
    start = time.perf_counter()
    rows, diag = evaluate(x, y, metadata["seed"])
    for row in rows:
        row.update(metadata)
    value = {"identity": identity, "metadata": metadata, "rows": rows, "diagnostics": diag,
             "elapsed_seconds": time.perf_counter()-start}
    atomic_json(out, value)
    return metadata["date"], value["elapsed_seconds"]


def validate_freeze(path, source, manifest):
    path = Path(path)
    if sha256(path) != path.with_suffix(".sha256").read_text().strip():
        raise ValueError("Protocol checksum mismatch")
    freeze = json.loads(path.read_text())
    if freeze["source_hashes"] != source_hashes():
        raise ValueError("Source changed after protocol freeze")
    declared = freeze["datasets"][source]
    for key in ("raw_sha256", "levels_sha256", "columns", "cutoff"):
        if declared[key] != manifest[key]:
            raise ValueError("Data changed after protocol freeze: " + key)
    if freeze["methods"] != METHODS or freeze["splits"] != SPLITS:
        raise ValueError("Frozen methods/splits mismatch")
    return freeze


def run(dataset, out, split, workers=2, stride=1, limit=0, protocol=None):
    start = time.perf_counter()
    dates, r, valid, manifest = load_panel(dataset)
    source = manifest["source"]
    if split != "development":
        if stride != 1 or limit != 0 or protocol is None:
            raise ValueError("Held-out runs require frozen protocol, full stride 1 and no limit")
        validate_freeze(protocol, source, manifest)
    lo, hi = SPLITS[source][split]
    requested = [i for i, d in enumerate(dates[1:]) if lo <= d <= hi]
    eligible = [i for i in requested if training_indices(i, valid) is not None][::stride]
    if limit:
        eligible = eligible[:limit]
    if not eligible:
        raise ValueError("No eligible windows")
    config = {"version": 1, "source": source, "split": split, "from": lo, "to": hi, "window": 512,
              "gap": 1, "horizon": "one consecutive reference session", "stride": stride, "limit": limit,
              "bank_seed": 2026, "seed_rule": "7000 + raw return index", "methods": METHODS,
              "source_hashes": source_hashes(), "raw_sha256": manifest["raw_sha256"],
              "levels_sha256": manifest["levels_sha256"], "manifest_sha256": sha256(Path(dataset)/"manifest.json"),
              "protocol_sha256": sha256(protocol) if protocol else None}
    identity = content_hash(config)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    if (out / "config.json").exists() and json.loads((out / "config.json").read_text()) != config:
        raise ValueError("Output belongs to another configuration/source/data hash")
    atomic_json(out / "config.json", config)
    windows = out / "windows"
    windows.mkdir(exist_ok=True)
    jobs = []
    for i in eligible:
        ix = training_indices(i, valid)
        metadata = {"date": dates[i+1], "return_index": i, "seed": 7000+i,
                    "source": source, "split": split, "training_first_date": dates[int(ix[0])+1],
                    "training_last_date": dates[int(ix[-1])+1], "n_train": 512,
                    "last_training_available_utc": dates[int(ix[-1])+1] + "T23:59:59+00:00",
                    "information_cutoff_utc": dates[i] + "T00:00:00+00:00",
                    "forecast_origin_utc": dates[i] + "T00:00:00+00:00",
                    "target_start_date": dates[i], "target_end_date": dates[i+1],
                    "calendar_days": (dt.date.fromisoformat(dates[i+1])-dt.date.fromisoformat(dates[i])).days,
                    "gap_observations": 1, "training_sha256": hashlib.sha256(r[ix].tobytes()).hexdigest()}
        assert metadata["last_training_available_utc"] < metadata["information_cutoff_utc"]
        path = windows / (dates[i+1] + ".json")
        if path.exists():
            old = json.loads(path.read_text())
            if old["identity"] != identity or old["metadata"] != metadata or len(old["rows"]) != 3*len(METHODS):
                raise ValueError("Invalid cached window")
            continue
        jobs.append((r[ix].copy(), r[i].copy(), metadata, path, identity))
    print(json.dumps({"source": source, "split": split, "eligible": len(eligible), "remaining": len(jobs), "workers": workers}), flush=True)
    if workers == 1:
        completed = map(window_job, jobs)
        for k, (date, elapsed) in enumerate(completed, 1):
            if k % 50 == 0 or k == len(jobs):
                print(k, len(jobs), date, "wall_s", round(time.perf_counter()-start, 2), flush=True)
    else:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            for k, (date, elapsed) in enumerate(pool.map(window_job, jobs), 1):
                if k % 50 == 0 or k == len(jobs):
                    print(k, len(jobs), date, "wall_s", round(time.perf_counter()-start, 2), flush=True)
    rows, durations, diagnostics = [], [], []
    for i in eligible:
        value = json.loads((windows / (dates[i+1]+".json")).read_text())
        rows.extend(value["rows"])
        durations.append(value["elapsed_seconds"])
        diagnostics.append({"date": dates[i+1], **value["diagnostics"]})
    tmppath = out / "forecasts.csv.tmp"
    with tmppath.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows({**row, "weights": json.dumps(row["weights"])} for row in rows)
    tmppath.replace(out / "forecasts.csv")
    atomic_json(out / "diagnostics.json", diagnostics)
    receipt = {"identity": identity, "source": source, "split": split, "complete": True,
               "finished_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "windows": len(eligible),
               "requested_dates": len(requested), "warmup_excluded": sum(i < 513 for i in requested),
               "invalid_gap_windows_excluded": sum(i >= 513 and training_indices(i, valid) is None for i in requested),
               "rows": len(rows), "first": rows[0]["date"], "last": rows[-1]["date"],
               "workers": workers, "numerical_threads_per_worker": 1, "computed_this_invocation": len(jobs),
               "wall_seconds_this_invocation": time.perf_counter()-start,
               "sum_window_seconds": sum(durations), "mean_window_seconds": float(np.mean(durations)),
               "forecasts_sha256": sha256(out/"forecasts.csv"), "diagnostics_sha256": sha256(out/"diagnostics.json")}
    atomic_json(out / "receipt.json", receipt)
    print(json.dumps(receipt, indent=2), flush=True)
    return receipt


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dataset", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--split", choices=["development", "validation", "test"], required=True)
    p.add_argument("--workers", type=int, default=2)
    p.add_argument("--stride", type=int, default=1)
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--protocol", type=Path)
    args = p.parse_args()
    if args.workers < 1 or args.stride < 1 or args.limit < 0:
        p.error("Invalid workers/stride/limit")
    run(**vars(args))


if __name__ == "__main__":
    main()
