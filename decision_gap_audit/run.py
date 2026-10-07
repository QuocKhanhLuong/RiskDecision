"""Preregistered synthetic decision experiment; never reads market data."""
from .core import *
from coverage_audit.core import generate, conditional, FAMILIES, bank, truth
from correction_audit.mechanism import fit
from tail_band_audit.run import sources as prior_sources
from local_market.data import sha256, atomic_json
from local_market.runner import content_hash
from local_market.stats import write_csv
from threadpoolctl import threadpool_limits
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import argparse
import datetime as dt
import json
import time

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "configs/decision_gap_v1.json"
FREEZE = ROOT / "configs/decision_gap_freeze.json"


def sources():
    return {**prior_sources(), **{str(p.relative_to(ROOT)): sha256(p)
            for p in sorted((ROOT / "decision_gap_audit").glob("*.py"))}}


def contract(smoke=False):
    p = json.loads(PROTOCOL.read_text())
    if smoke:
        p = {**p, "seeds": [80000, 80001], "families": ["gaussian"]}
        return p, content_hash({"protocol": p, "source_hashes": sources()})
    f = json.loads(FREEZE.read_text())
    if f["source_hashes"] != sources() or f["protocol_sha256"] != sha256(PROTOCOL):
        raise ValueError("Frozen source/protocol mismatch")
    return p, content_hash(f)


def job(args):
    family, seed, p, identity, directory = args
    start = time.perf_counter()
    with threadpool_limits(limits=1):
        x, marginal, states = generate(seed, family, 512+p["gap"]+max(p["sizes"]))
        w = bank(p["bank_seed"])
        risk, chosen, diag, _, _ = fit(x[:512], w, seed)
        ids = np.array([chosen["historical_se_penalty"]]+[chosen[m] for m in CANDIDATES])
        arrays = {"returns": x, "ids": ids}
        rows, controls, forecasts, failures = [], [], [], []
        failures.append({"phase": "training", "gmm": diag["base_gmm"],
                         "band_converged": diag["support_band50"]["converged"]})
        marginal_es = truth(w, marginal)[1]
        # Same target/weights for all model surfaces, distinct from selection.
        for m in ["historical_se_penalty"]+CANDIDATES:
            e = risk[m][1]
            delta_error = (e-e[chosen["historical_se_penalty"]]) - (marginal_es-marginal_es[chosen["historical_se_penalty"]])
            forecasts.append({"family": family, "seed": seed, "method": m,
                              "common_equal_relative_error": float(abs(e[0]-marginal_es[0])/marginal_es[0]),
                              "bank_level_mae": float(np.mean(abs(e-marginal_es))),
                              "bank_contrast_mae": float(np.mean(abs(delta_error))),
                              "same_choice_as_hist": int(chosen[m] == ids[0])})
        for n in p["sizes"]:
            end = 512+p["gap"]+n
            assessment = x[512+p["gap"]:end]
            block = 1 if family in FAMILIES[:3] else p["dependent_block"]
            result = intervals(assessment, w[ids], block, p["draws"], seed+100000+n)
            recent_risk, recent_chosen, recent_diag, _, _ = fit(x[end-512:end], w, seed+200000+n)
            failures.append({"phase": f"recent_{n}", "gmm": recent_diag["base_gmm"],
                             "band_converged": recent_diag["support_band50"]["converged"]})
            controls_ids = {"training_hist_se": ids[0], **{f"training_{m}": chosen[m] for m in CANDIDATES},
                            "equal_weight": 0, "all_history_hist_se": historical_choice(x[:end], w),
                            **{f"recent_{m}": recent_chosen[m] for m in ["historical_se_penalty"]+CANDIDATES}}
            arrays[f"n{n}_es"] = result["es"]
            arrays[f"n{n}_radii"] = np.array([result["radii"][r] for r in RECIPES])
            arrays[f"n{n}_choices"] = np.array([result["choices"][r] for r in RECIPES])
            for estimand, pars in [("marginal", marginal), ("next_conditional", conditional(family, marginal, x[end-1], states[end-1]))]:
                target = truth(w, pars)[1]
                arrays[f"n{n}_{estimand}_truth"] = target
                common = {"family": family, "seed": seed, "n": n, "block": block, "estimand": estimand}
                rows.extend([{**common, **r} for r in assess(result, target, ids, marginal_es[ids[0]], marginal_es.min())])
                for method, j in controls_ids.items():
                    controls.append({**common, "method": method, "portfolio_id": int(j),
                                     "relative_delta": float((target[j]-target[ids[0]])/marginal_es[ids[0]]),
                                     "relative_regret": float((target[j]-target.min())/marginal_es.min()),
                                     "harm": int(target[j] > target[ids[0]]+1e-10)})
    path = Path(directory)/f"{family}_{seed}"
    tmp = path.with_suffix(".tmp.npz"); np.savez_compressed(tmp, **arrays); tmp.replace(path.with_suffix(".npz"))
    atomic_json(path.with_suffix(".json"), {"identity": identity, "family": family, "seed": seed,
                "rows": rows, "controls": controls, "forecasts": forecasts, "diagnostics": failures,
                "arrays_sha256": sha256(path.with_suffix(".npz")), "seconds": time.perf_counter()-start})
    return family, seed


def run(out, workers=2, smoke=False):
    start = time.perf_counter(); p, identity = contract(smoke)
    out = Path(out); cases = out/"cases"; cases.mkdir(parents=True, exist_ok=True)
    jobs, paths = [], []
    for family in p["families"]:
        for seed in p["seeds"]:
            path = cases/f"{family}_{seed}.json"; paths.append(path)
            if path.exists():
                old = json.loads(path.read_text())
                if old["identity"] != identity or old["arrays_sha256"] != sha256(path.with_suffix(".npz")):
                    raise ValueError("Invalid cache")
            else:
                jobs.append((family, seed, p, identity, str(cases)))
    print("cases", len(paths), "remaining", len(jobs), flush=True)
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for i, done in enumerate(pool.map(job, jobs), 1):
            if i % 50 == 0 or i == len(jobs):
                print(i, len(jobs), done, round(time.perf_counter()-start, 2), flush=True)
    values = [json.loads(path.read_text()) for path in paths]
    for key in ["rows", "controls", "forecasts"]:
        write_csv(out/f"{key}.csv", [r for v in values for r in v[key]])
    diagnostics = [d for v in values for d in v["diagnostics"]]
    receipt = {"identity": identity, "protocol_sha256": sha256(PROTOCOL), "source_hashes": sources(),
               "cases": len(paths), "computed_this_invocation": len(jobs), "workers": workers,
               "numerical_threads": 1, "wall_seconds": time.perf_counter()-start,
               "finished_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
               "gmm_nonconverged": sum(not d["gmm"]["converged"] for d in diagnostics),
               "gmm_warnings": sum(len(d["gmm"]["warnings"]) for d in diagnostics),
               "band_nonconverged": sum(not d["band_converged"] for d in diagnostics),
               "case_hashes": {path.name: sha256(path) for path in paths},
               "csv_hashes": {key: sha256(out/f"{key}.csv") for key in ["rows", "controls", "forecasts"]}}
    atomic_json(out/"receipt.json", receipt)
    if not (out/"first_execution_receipt.json").exists():
        atomic_json(out/"first_execution_receipt.json", receipt)
    print("DONE", len(paths), flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=ROOT/"runs/decision_gap_v1")
    ap.add_argument("--workers", type=int, choices=[1, 2], default=2)
    ap.add_argument("--smoke", action="store_true")
    run(**vars(ap.parse_args()))
