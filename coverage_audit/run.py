"""Execute the pre-frozen synthetic finite-grid coverage experiment."""
from .core import (FAMILIES, ANCHORS, PROCEDURES, bank, gmm_fit, generate, conditional,
                   features, multiplier, population_hinge, truth, evaluate, counterexample)
from local_market.data import atomic_json, sha256
from local_market.stats import write_csv
from local_market.runner import content_hash
from threadpoolctl import threadpool_limits
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import argparse
import datetime as dt
import hashlib
import json
import time
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT/"configs/coverage_audit_v1.json"
FREEZE = ROOT/"configs/coverage_audit_freeze.json"


def sources():
    paths = list((ROOT/"coverage_audit").glob("*.py"))
    paths += list((ROOT/"local_market").glob("*.py"))
    paths += list((ROOT/"correction_audit").glob("*.py"))
    paths += [ROOT/"quant_research_v2/src/research.py", ROOT/"requirements-local.lock"]
    return {str(p.relative_to(ROOT)): sha256(p) for p in sorted(paths)}


def contract():
    p = json.loads(PROTOCOL.read_text())
    freeze = json.loads(FREEZE.read_text())
    if freeze["protocol_sha256"] != sha256(PROTOCOL) or freeze["source_hashes"] != sources():
        raise ValueError("Coverage sources/protocol differ from pre-experiment freeze")
    if p["families"] != FAMILIES or p["anchors"] != ANCHORS or p["procedures"] != PROCEDURES:
        raise ValueError("Recipe mismatch")
    return p, content_hash(freeze)


def job(arg):
    family, seed, protocol, identity, directory = arg
    start = time.perf_counter()
    with threadpool_limits(limits=1):
        x, marginal, states = generate(seed, family)
        w = bank(protocol["bank_seed"])
        z, diag = gmm_fit(x[:256], seed)
        if not np.isfinite(z).all():
            raise ValueError("Nonfinite base scenarios")
        arrays = {"returns": x, "states": states, "scenarios": z}
        rows = []
        es = truth(w, marginal)[1]  # evaluator only, used to normalize widths
        for n in protocol["calibration_sizes"]:
            cal = x[256:256+n]
            future = conditional(family, marginal, cal[-1], states[255+n])
            for a, anchor in enumerate(ANCHORS):
                eta, h, heuristic, selected = features(z, cal, w, anchor)
                key = f"n{n}_{anchor}"
                center = h.mean(0)
                targets = {"stationary_marginal": marginal, "next_conditional": future}
                populations = {name: population_hinge(np.repeat(w, 3, axis=0), eta, pars) for name, pars in targets.items()}
                arrays[key+"_eta"] = eta
                arrays[key+"_center"] = center
                arrays[key+"_es_marginal"] = es
                arrays[key+"_selected"] = np.array(selected)
                for name, target in populations.items():
                    arrays[key+"_"+name] = target
                blocks = [0, 1, protocol["blocks"][str(n)][0], protocol["blocks"][str(n)][1]]
                for procedure, block in zip(PROCEDURES, blocks):
                    if block == 0:
                        radius, critical, zeros = heuristic, 1., 0
                    else:
                        rng_seed = np.random.SeedSequence([seed, FAMILIES.index(family), n, a, block, 900000])
                        radius, critical, zeros = multiplier(h, block, protocol["bootstrap_draws"], rng_seed)
                    arrays[key+"_"+procedure+"_radius"] = radius
                    for estimand, population in populations.items():
                        rows.append({"family": family, "seed": seed, "n": n, "anchor": anchor,
                                     "procedure": procedure, "estimand": estimand, "block": block,
                                     "critical": critical, "zero_se_features": zeros,
                                     "selected_feature": selected, "gmm_converged": int(diag["converged"]),
                                     "last_latent_state": int(states[255+n]),
                                     **evaluate(center, radius, population, es, selected)})
    path = Path(directory)/f"{family}_{seed}"
    # NPZ is local per-case evidence. JSON is published only through aggregation.
    temp = path.with_suffix(".tmp.npz")
    np.savez_compressed(temp, **arrays)
    temp.replace(path.with_suffix(".npz"))
    atomic_json(path.with_suffix(".json"), {"identity": identity, "family": family, "seed": seed,
                "rows": rows, "gmm": diag, "seconds": time.perf_counter()-start,
                "arrays_sha256": sha256(path.with_suffix(".npz")),
                "returns_sha256": hashlib.sha256(x.tobytes()).hexdigest()})
    return family, seed


def run(out, workers=2):
    start = time.perf_counter()
    p, identity = contract()
    out = Path(out)
    cases = out/"cases"
    cases.mkdir(parents=True, exist_ok=True)
    config = {"identity": identity, "protocol_sha256": sha256(PROTOCOL), "source_hashes": sources()}
    if (out/"config.json").exists() and json.loads((out/"config.json").read_text()) != config:
        raise ValueError("Output identity mismatch")
    atomic_json(out/"config.json", config)
    jobs, expected = [], []
    for family in p["families"]:
        for seed in p["seeds"]:
            path = cases/f"{family}_{seed}.json"
            expected.append(path)
            if path.exists():
                old = json.loads(path.read_text())
                if old["identity"] != identity or len(old["rows"]) != 32 or old["arrays_sha256"] != sha256(path.with_suffix(".npz")):
                    raise ValueError("Invalid cached case")
            else:
                jobs.append((family, seed, p, identity, str(cases)))
    print("cases", len(expected), "remaining", len(jobs), flush=True)
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for k, result in enumerate(pool.map(job, jobs), 1):
            if k % 20 == 0 or k == len(jobs):
                print(k, len(jobs), result, round(time.perf_counter()-start, 2), flush=True)
    values = [json.loads(path.read_text()) for path in expected]
    rows = [r for value in values for r in value["rows"]]
    write_csv(out/"cases.csv", rows)
    atomic_json(out/"receipt.json", {**config, "status": "complete", "cases": len(values), "rows": len(rows),
                "computed_this_invocation": len(jobs), "workers": workers, "numerical_threads_per_worker": 1,
                "wall_seconds": time.perf_counter()-start, "finished_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                "cases_csv_sha256": sha256(out/"cases.csv"),
                "case_sha256": {path.name: sha256(path) for path in expected}, "counterexample": counterexample(),
                "gmm_nonconverged": sum(not v["gmm"]["converged"] for v in values),
                "gmm_warnings": sum(len(v["gmm"]["warnings"]) for v in values)})
    print("DONE", len(values), len(rows), flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=ROOT/"runs/coverage_audit_v1")
    ap.add_argument("--workers", type=int, choices=[1, 2], default=2)
    run(**vars(ap.parse_args()))
