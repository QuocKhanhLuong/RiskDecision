"""Frozen paired Gaussian isolation experiment; no market-test access."""
from .core import *
from coverage_audit.run import sources as previous_sources
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
PROTOCOL = ROOT/"configs/tail_band_v1.json"
FREEZE = ROOT/"configs/tail_band_freeze.json"


def sources():
    return {**previous_sources(), **{str(p.relative_to(ROOT)): sha256(p) for p in sorted((ROOT/"tail_band_audit").glob("*.py"))}}


def contract():
    p, f = json.loads(PROTOCOL.read_text()), json.loads(FREEZE.read_text())
    if f["source_hashes"] != sources() or f["protocol_sha256"] != sha256(PROTOCOL):
        raise ValueError("Frozen source/protocol mismatch")
    if p["anchors"] != ANCHORS or p["recipes"] != RECIPES:
        raise ValueError("Recipe mismatch")
    return p, content_hash(f)


def job(arg):
    seed, p, identity, directory = arg
    start = time.perf_counter()
    with threadpool_limits(limits=1):
        x, pars, _ = generate(seed, "gaussian", n=256+max(p["sizes"]))
        w = bank(p["bank_seed"])
        sd = np.sqrt(np.einsum("ij,jk,ik->i", w, pars["cov"][0], w))
        es = sd*norm.pdf(norm.ppf(.95))/.05
        z, diag = gmm_fit(x[:256], seed)
        if not np.isfinite(z).all():
            raise ValueError("Nonfinite scenario support")
        base_scale = np.repeat(np.maximum((-x[:256] @ w.T).std(0, ddof=1), .05), 3)
        arrays, rows, bounded = {"returns": x, "scenarios": z, "sd": sd, "es": es, "base_scale": base_scale}, [], []
        for n in p["sizes"]:
            cal = x[256:256+n]
            loss = -cal @ w.T
            # Common random multipliers across anchors and recipes within n.
            g = np.random.default_rng(np.random.SeedSequence([seed, n, 920000])).standard_normal((p["draws"], n))
            for anchor in ANCHORS:
                if anchor == "population_quantiles_oracle":
                    eta = (sd[:, None]*norm.ppf(QUANTILES)).ravel()
                    h = np.maximum(np.repeat(loss, 3, axis=1)-eta, 0)
                else:
                    eta, h, _, _ = features(z, cal, w, anchor)
                target, var = normal_hinge_moments(eta, np.repeat(sd, 3))
                exact_se = np.sqrt(var/n)
                rr, plugin_se, critical = radii(h, exact_se, base_scale, g)
                key = f"n{n}_{anchor}"
                arrays.update({key+"_eta": eta, key+"_center": h.mean(0), key+"_target": target,
                               key+"_exact_se": exact_se, key+"_plugin_se": plugin_se})
                for recipe, radius in rr.items():
                    if not np.isfinite(radius).all():
                        raise ValueError("Nonfinite radius")
                    arrays[key+"_"+recipe] = radius
                    rows.append({"seed": seed, "n": n, "anchor": anchor, "recipe": recipe,
                                 "plugin_critical": critical, **metrics(h.mean(0), radius, target, exact_se, plugin_se, h, es)})
            cap = p["bounded_control"]["cap_sigma"]*sd
            clipped = np.clip(loss, -cap, cap)
            lo, hi, eps = dkw_es(clipped, -cap, cap)
            true_es = clipped_normal_es(sd, p["bounded_control"]["cap_sigma"])
            key = f"n{n}_dkw"
            arrays.update({key+"_lo": lo, key+"_hi": hi, key+"_truth": true_es})
            covered = (lo <= true_es+1e-12) & (true_es <= hi+1e-12)
            bounded.append({"seed": seed, "n": n, "epsilon": eps, "all_covered": int(covered.all()),
                            "equal_covered": int(covered[0]), "width_relative_median": float(np.median((hi-lo)/true_es)),
                            "upper_at_support_fraction": float(np.isclose(hi, cap, atol=1e-10, rtol=0).mean()),
                            "clipping_es_relative_change": float(np.median((es-true_es)/es))})
    path = Path(directory)/str(seed)
    tmp = path.with_suffix(".tmp.npz")
    np.savez_compressed(tmp, **arrays); tmp.replace(path.with_suffix(".npz"))
    atomic_json(path.with_suffix(".json"), {"identity": identity, "seed": seed, "rows": rows, "bounded": bounded,
                "gmm": diag, "arrays_sha256": sha256(path.with_suffix(".npz")), "seconds": time.perf_counter()-start})
    return seed


def run(out, workers=2):
    start = time.perf_counter()
    p, identity = contract()
    out = Path(out); cases = out/"cases"; cases.mkdir(parents=True, exist_ok=True)
    jobs, expected = [], []
    for seed in p["seeds"]:
        path = cases/f"{seed}.json"; expected.append(path)
        if path.exists():
            old = json.loads(path.read_text())
            if old["identity"] != identity or old["seed"] != seed or len(old["rows"]) != 27 or len(old["bounded"]) != 3 or old["arrays_sha256"] != sha256(path.with_suffix(".npz")):
                raise ValueError("Invalid cached case")
        else:
            jobs.append((seed, p, identity, str(cases)))
    print("cases", len(expected), "remaining", len(jobs), flush=True)
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for i, seed in enumerate(pool.map(job, jobs), 1):
            if i % 20 == 0 or i == len(jobs):
                print(i, len(jobs), seed, round(time.perf_counter()-start, 2), flush=True)
    values = [json.loads(path.read_text()) for path in expected]
    rows = [r for v in values for r in v["rows"]]
    bounded = [r for v in values for r in v["bounded"]]
    write_csv(out/"cases.csv", rows); write_csv(out/"bounded.csv", bounded)
    receipt = {"identity": identity, "protocol_sha256": sha256(PROTOCOL), "source_hashes": sources(),
               "status": "complete", "cases": len(values), "rows": len(rows), "bounded_rows": len(bounded),
               "workers": workers, "numerical_threads_per_worker": 1, "computed_this_invocation": len(jobs),
               "wall_seconds": time.perf_counter()-start, "finished_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
               "gmm_nonconverged": sum(not v["gmm"]["converged"] for v in values),
               "gmm_warnings": sum(len(v["gmm"]["warnings"]) for v in values),
               "case_sha256": {path.name: sha256(path) for path in expected},
               "cases_csv_sha256": sha256(out/"cases.csv"), "bounded_csv_sha256": sha256(out/"bounded.csv")}
    atomic_json(out/"receipt.json", receipt)
    if not (out/"first_execution_receipt.json").exists():
        atomic_json(out/"first_execution_receipt.json", receipt)
    print("DONE", len(values), len(rows), len(bounded), flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=ROOT/"runs/tail_band_v1")
    ap.add_argument("--workers", type=int, choices=[1,2], default=2)
    run(**vars(ap.parse_args()))
