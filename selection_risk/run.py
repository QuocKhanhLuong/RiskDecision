"""Run: python -m selection_risk.run {preflight,q0,micro,pilot} --out PATH."""
import os
for _name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_name] = "1"

import argparse
import csv
import hashlib
import json
from pathlib import Path
import time
import warnings

import numpy as np
from tqdm import tqdm

from .core import (Surface, assert_common_surfaces, crossed_rows, evaluate_split,
                   fit_frozen_suite, legacy, lock_selectors, lock_split)
from .preflight import preflight
from .runtime import ROOT, Run, atomic_json, digest, object_hash, source_hashes, write_csv
from .statistics import summarize_crossed, summarize_split


def array_hash(x):
    return hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest()


def load_config(kind):
    return json.loads((ROOT / "selection_risk/configs" / ("review.json" if kind == "q0" else "pilot.json")).read_text())


def historical_inputs(snapshot, config):
    base = snapshot / "quant_research_v2/results"
    files = [base / "test.csv", base / "selection_freeze.json"]
    for family in config["families"]:
        for seed in range(config["seeds"]["start"], config["seeds"]["stop"]):
            files.extend(base / "test" / f"{family}_{seed}.{ext}" for ext in ("npz", "json"))
    return {str(p.relative_to(snapshot)): digest(p) for p in files}


def historical_case(snapshot, family, seed, config, csv_rows):
    started = time.perf_counter()
    path = snapshot / "quant_research_v2/results/test" / f"{family}_{seed}.npz"
    with np.load(path, allow_pickle=False) as data:
        w, past, true_es = data["weights"], data["returns"], data["true_es"]
        if w.shape != (285, 8) or past.shape != (512, 8):
            raise ValueError("Unexpected historical bank/sample shape")
        surfaces = {name: Surface(w, data[name+"_var"], data[name+"_es"]) for name in config["forecasters"]}
        assert_common_surfaces(surfaces)
        locked = lock_selectors(surfaces, past, config["selectors"])
        diagnostics = json.loads(path.with_suffix(".json").read_text())
        if array_hash(past) != diagnostics["x_sha256"]:
            raise ValueError("Past data hash disagrees with historical receipt")
        if not np.array_equal(w, legacy.bank(seed)):
            raise ValueError("Historical bank differs from frozen generator")
        # Read existing historical scalars, do not refit any candidate.
        for name in config["selectors"]:
            row = csv_rows[family, seed, name]
            if int(row["portfolio_id"]) != locked[name]:
                raise ValueError("Historical selection differs from stored CSV")
            surface = surfaces["historical" if name == "equal_weight" else name]
            j = locked[name]
            for key, expected in {"predicted_es": surface.es[j], "true_es": true_es[j],
                                  "relative_error": abs(surface.es[j] / true_es[j]-1),
                                  "relative_regret": true_es[j] / true_es.min()-1,
                                  "hhi": w[j] @ w[j]}.items():
                np.testing.assert_allclose(float(row[key]), expected, atol=1e-11, rtol=1e-11)
        rows = crossed_rows(surfaces, locked, true_es, family, seed)
    return {"crossed": rows, "split": [], "diagnostics": diagnostics,
            "family": family, "seed": seed, "source_npz_sha256": digest(path),
            "returns_sha256": array_hash(past), "weights_sha256": array_hash(w),
            "assertions": {"historical_penalty_exact_surface_identity": True,
                           "same_bank_all_forecasters": True, "all_285_targets_finite": True,
                           "historical_csv_selectors_matched": len(locked)},
            "seconds": time.perf_counter()-started,
            "evidence": "EXPLORATORY_REUSE; existing truth/surfaces; no model refit"}


def pilot_case(out, family, seed, config):
    started = time.perf_counter()
    past, evaluator_parameters = legacy.generate(seed, family)
    w = legacy.bank(seed)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        surfaces, diagnostics = fit_frozen_suite(past, w, seed)
        locked = lock_selectors(surfaces, past, config["selectors"])
        split_locked = lock_split(past, w)
    # This is the sole boundary through which population information enters.
    true_var, true_es = legacy.truth(w, evaluator_parameters)
    rows = crossed_rows(surfaces, locked, true_es, family, seed)
    split_rows = evaluate_split(split_locked, w, evaluator_parameters, true_es, family, seed)
    arrays = out / "arrays" / f"{family}_{seed}.npz"
    arrays.parent.mkdir(parents=True, exist_ok=True)
    tmp = arrays.with_name(arrays.name + ".tmp")
    with tmp.open("wb") as stream:
        np.savez_compressed(stream, returns=past, weights=w, true_es=true_es, true_var=true_var,
                            **{name+"_es": surface.es for name, surface in surfaces.items()},
                            **{name+"_var": surface.var for name, surface in surfaces.items()})
    tmp.replace(arrays)
    diagnostics["runtime_warnings"] = [str(w.message) for w in caught]
    return {"crossed": rows, "split": split_rows, "split_decisions": split_locked,
            "diagnostics": diagnostics, "family": family, "seed": seed,
            "returns_sha256": array_hash(past), "weights_sha256": array_hash(w),
            "artifacts": {str(arrays.relative_to(out)): digest(arrays)},
            "assertions": {"historical_penalty_exact_surface_identity": True,
                           "same_bank_all_forecasters": True, "decisions_locked_before_truth": True},
            "seconds": time.perf_counter()-started, "evidence": "FRESH_IID_PILOT"}


def publish_tables(run, payloads, config, complete):
    crossed = [r for p in payloads for r in p["crossed"]]
    split = [r for p in payloads for r in p["split"]]
    write_csv(run.out / "crossed_rows.csv", crossed)
    index = [{"family": p["family"], "seed": p["seed"], "seconds": p["seconds"],
              "returns_sha256": p["returns_sha256"], "weights_sha256": p["weights_sha256"],
              "case_sha256": digest(run.out / "cases" / f'{p["family"]}_{p["seed"]}.json')}
             for p in payloads]
    write_csv(run.out / "case_index.csv", index)
    atomic_json(run.out / "diagnostics.json", [{"family": p["family"], "seed": p["seed"],
                                                "diagnostics": p["diagnostics"], "assertions": p["assertions"]}
                                               for p in payloads])
    if split:
        write_csv(run.out / "split_rows.csv", split)
    if complete:
        summaries, contrasts = summarize_crossed(crossed, config)
        write_csv(run.out / "crossed_summary.csv", summaries)
        write_csv(run.out / "crossed_paired.csv", contrasts)
        if split:
            write_csv(run.out / "split_summary.csv", summarize_split(split, config))
    return crossed


def execute(kind, base, max_new_cases=0):
    config = load_config(kind)
    if kind == "q0":
        snapshot = base / "historical_snapshot"
        inputs = historical_inputs(snapshot, config)
        with (snapshot / "quant_research_v2/results/test.csv").open() as stream:
            raw = list(csv.DictReader(stream))
        lookup = {(r["family"], int(r["seed"]), r["method"]): r for r in raw}
        if len(raw) != 5760 or len(lookup) != 5760:
            raise ValueError("Historical rows missing/duplicated")
        jobs = [(f,s) for s in range(config["seeds"]["start"], config["seeds"]["stop"]) for f in config["families"]]
    else:
        audit = json.loads((base / "seed_audit.json").read_text())
        if audit["config_sha256"] != object_hash(config) or audit["collisions"]:
            raise ValueError("Pilot configuration is not covered by seed audit")
        inputs = {"seed_audit": digest(base / "seed_audit.json")}
        seeds = [config["microbenchmark_seed"]] if kind == "micro" else list(range(config["seeds"]["start"], config["seeds"]["stop"]))
        jobs = [(f,s) for s in seeds for f in config["families"]]
        if kind == "pilot":
            micro = json.loads((base / "micro/benchmark.json").read_text())
            if micro["source_hashes"] != source_hashes() or micro["config_sha256"] != object_hash(config):
                raise ValueError("Microbenchmark identity mismatch")
            if micro["estimated_pilot_seconds_with_margin"] > config["compute_cap_seconds"]:
                raise ValueError("Pilot NOT_RUN: microbenchmark exceeds frozen compute cap")
            inputs["microbenchmark"] = digest(base / "micro/benchmark.json")
            np.random.default_rng(config["job_order_seed"]).shuffle(jobs)
        config = dict(config, execution_stage=kind)
    run = Run(base / kind, config, inputs)
    with run.session():
        payloads, executed, resumed = [], 0, 0
        with tqdm(total=len(jobs), desc=kind, unit="instance", mininterval=.5) as bar:
            for family, seed in jobs:
                key = f"{family}_{seed}"
                payload = run.case(key)
                if payload is not None:
                    resumed += 1
                    run.event("case_resumed", family=family, seed=seed)
                else:
                    if max_new_cases and executed >= max_new_cases:
                        break
                    if kind == "q0":
                        payload = historical_case(snapshot, family, seed, config, lookup)
                    else:
                        payload = pilot_case(run.out, family, seed, config)
                    run.save(key, payload)
                    executed += 1
                    run.event("case_complete", family=family, seed=seed,
                              seconds=payload["seconds"], completed=len(payloads)+1, total=len(jobs),
                              eta_seconds=(len(jobs)-len(payloads)-1)*sum(p["seconds"] for p in payloads+[payload])/(len(payloads)+1))
                payloads.append(payload)
                bar.update(1)
        complete = len(payloads) == len(jobs)
        rows = publish_tables(run, payloads, config, complete)
        if kind == "micro" and complete:
            original = load_config("pilot")
            estimate = sum(p["seconds"] for p in payloads) / len(payloads) * 2 * 64 * 1.5
            atomic_json(run.out / "benchmark.json", {"source_hashes": source_hashes(),
                        "config_sha256": object_hash(original), "cases": len(payloads),
                        "observed_compute_seconds": sum(p["seconds"] for p in payloads),
                        "estimated_pilot_seconds_with_margin": estimate,
                        "cap_seconds": original["compute_cap_seconds"],
                        "metrics_used_to_select_methods": False})
        receipt = run.finish(rows, len(payloads), executed, resumed, complete)
        print(json.dumps(receipt, indent=2), flush=True)
        return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=["preflight", "q0", "micro", "pilot"])
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--archive-dir", type=Path)
    parser.add_argument("--max-new-cases", type=int, default=0,
                        help="Stop after this many new checkpoints, for interruption/resume validation")
    args = parser.parse_args()
    if args.max_new_cases < 0:
        parser.error("--max-new-cases must be nonnegative")
    if args.stage == "preflight":
        if args.archive_dir is None:
            parser.error("preflight needs --archive-dir")
        receipt = preflight(args.out, args.archive_dir, load_config("pilot"))
        print(json.dumps({"archives_verified": len(receipt["archives"]), "files_verified": len(receipt["imported_files"])}))
    else:
        execute(args.stage, args.out, args.max_new_cases)


if __name__ == "__main__":
    main()
