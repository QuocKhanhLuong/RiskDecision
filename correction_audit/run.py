"""Run fixed development-only diagnostics with atomic, content-bound resume."""
from .mechanism import METHODS, fit, anchor_decomposition
from local_market.models import bank
from local_market.data import load_panel, atomic_json, sha256
from local_market.runner import training_indices, content_hash, validate_freeze
from local_market.scoring import score
from local_market.stats import write_csv
from research import generate, truth
import argparse
from concurrent.futures import ProcessPoolExecutor
import datetime as dt
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from scipy.stats import norm, t

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT/"configs/correction_diagnostic_v1.json"


def sources():
    paths = list((ROOT/"correction_audit").glob("*.py"))
    paths += list((ROOT/"local_market").glob("*.py"))
    paths += [ROOT/"quant_research_v2/src/research.py", ROOT/"requirements-local.lock"]
    return {str(p.relative_to(ROOT)): sha256(p) for p in sorted(paths)}


def contract():
    p = json.loads(PROTOCOL.read_text())
    if p["ecb"]["through"] > "2015-12-31" or p["ecb"]["stride"] != 1:
        raise ValueError("Development boundary cannot be expanded by this runner")
    if p["methods"] != METHODS or p["correction"]["tuning_budget"] != 0:
        raise ValueError("Method/tuning contract changed")
    return p


def population_hinge(w, eta, pars):
    """Analytical evaluator only; never passed into the fit function."""
    if pars["kind"] == "t":
        nu = pars["df"]
        mu = -w @ pars["mean"]
        sd = np.sqrt(np.einsum("ij,jk,ik->i", w, pars["shape"], w))
        z = (eta-mu)/sd
        return (mu-eta)*t.sf(z, nu)+sd*(nu+z*z)/(nu-1)*t.pdf(z, nu)
    mu = -w @ pars["mu"].T
    sd = np.sqrt(np.einsum("ij,kjl,il->ik", w, pars["cov"], w))
    z = (eta[:, None]-mu)/sd
    return (pars["p"]*((mu-eta[:, None])*norm.sf(z)+sd*norm.pdf(z))).sum(1)


def job_run(job):
    start = time.perf_counter()
    meta, x, outcome, path, identity = job
    w = bank(meta["bank_seed"])
    risks, chosen, diag, state, probabilities = fit(x, w, meta["seed"])
    # Population parameters / future return enter ONLY after fitting is complete.
    synthetic = meta["source"] == "synthetic"
    if synthetic:
        _, true_es = truth(w, outcome)
        ref_hinge = population_hinge(w, state["eta"], outcome)
        ref_es = true_es
        with np.load(ROOT/meta["archive_path"]) as old:
            errors = {m: float(np.max(np.abs(risks[m][1]-old[m+"_es"])))
                      for m in ["support_mix50", "support_band50", "support_point50"]}
            # NumPy multivariate-normal SVD draws can differ across BLAS platforms.
            # Report this honestly; immutable archive outcomes are never replaced.
        diag["archive_surface_max_errors"] = errors
    else:
        from local_market.models import Risk
        ref_es = Risk(x[256:], w).eval()[1]
        ref_hinge = state["b"]
    targets = {"equal_weight": 0, "historical_se_reference": chosen["historical_se_penalty"]}
    rows, decomposition = [], []
    for method in METHODS:
        v, e = risks[method]
        for track, target, j in [("A", target, j) for target, j in targets.items()]+[("B", "own_selection", chosen[method])]:
            row = {"date": meta["date"], "source": meta["source"], "family": meta.get("family", "ecb"),
                   "seed": meta["seed"], "track": track, "target": target, "method": method,
                   "portfolio_id": j, "weights": w[j].tolist(),
                   "converged": diag.get(method, diag["base_gmm"] if method == "support_mix50" else {}).get("converged", True)}
            if synthetic:
                row.update(predicted_es=float(e[j]), true_es=float(true_es[j]),
                           relative_error=float(abs(e[j]-true_es[j])/true_es[j]),
                           relative_regret=float(true_es[j]/true_es.min()-1))
            else:
                row.update(score(float(-outcome @ w[j]), float(v[j]), float(e[j])))
                row["fallback"] = False
            rows.append(row)
            if method in probabilities:
                terms = anchor_decomposition(state, probabilities[method], e[j], ref_es[j], ref_hinge[j], j)
                if abs(terms["identity_residual"]) > 1e-9:
                    raise AssertionError("Anchor decomposition identity failed")
                decomposition.append({"track": track, "target": target, "method": method,
                                      "reference": "synthetic_population" if synthetic else "empirical_training_calibration",
                                      **terms})
    value = {"identity": identity, "metadata": meta, "rows": rows, "diagnostics": diag,
             "decomposition": decomposition, "seconds": time.perf_counter()-start}
    atomic_json(path, value)
    return meta["date"]


def jobs_for(source, protocol):
    jobs, inputs = [], {}
    if source == "ecb":
        directory = ROOT/"data/raw/ecb"
        dates, returns, valid, manifest = load_panel(directory)
        validate_freeze(ROOT/"configs/market_protocol_v1.json", "ecb", manifest)
        if sha256(directory/"levels.csv") != protocol["ecb"]["levels_sha256"]:
            raise ValueError("ECB panel changed")
        inputs["manifest_sha256"] = sha256(directory/"manifest.json")
        inputs["levels_sha256"] = sha256(directory/"levels.csv")
        for i, date in enumerate(dates[1:]):
            if not protocol["ecb"]["from"] <= date <= protocol["ecb"]["through"]:
                continue
            ix = training_indices(i, valid)
            if ix is None:
                raise ValueError("Unexpected invalid development window")
            x = returns[ix].copy()
            meta = {"date": date, "source": "ecb", "seed": 7000+i, "bank_seed": 2026,
                    "return_index": i, "training_last_date": dates[int(ix[-1])+1],
                    "training_first_date": dates[int(ix[0])+1], "origin": dates[i]+"T00:00:00+00:00",
                    "last_training_available": dates[int(ix[-1])+1]+"T23:59:59+00:00",
                    "target_start_date": dates[i], "training_sha256": hashlib.sha256(x.tobytes()).hexdigest()}
            if not meta["last_training_available"] < meta["origin"]:
                raise ValueError("Availability ordering failed")
            jobs.append((meta, x, returns[i].copy()))
    elif source == "synthetic":
        for family in protocol["synthetic"]["families"]:
            for seed in protocol["synthetic"]["seeds"]:
                archive = Path("quant_research_v2/results/validation")/f"{family}_{seed}.npz"
                inputs[str(archive)] = sha256(ROOT/archive)
                _, pars = generate(seed, family)
                with np.load(ROOT/archive) as old:
                    x = old["returns"].copy()
                    if not np.array_equal(bank(seed), old["weights"]):
                        raise ValueError("Original synthetic bank mismatch")
                    np.testing.assert_allclose(truth(bank(seed), pars)[1], old["true_es"], atol=1e-10, rtol=0)
                meta = {"date": f"{family}_{seed}", "source": "synthetic", "family": family,
                        "seed": seed, "bank_seed": seed, "archive_path": str(archive),
                        "training_sha256": hashlib.sha256(x.tobytes()).hexdigest()}
                jobs.append((meta, x, pars))
    else:
        raise ValueError("Only ECB development and exposed synthetic validation are allowed")
    return jobs, inputs


def run(source, out, workers=2):
    start = time.perf_counter()
    protocol = contract()
    freeze_path = ROOT/"configs/correction_diagnostic_freeze.json"
    freeze = json.loads(freeze_path.read_text())
    if freeze["source_hashes"] != sources() or freeze["protocol_sha256"] != sha256(PROTOCOL):
        raise ValueError("Diagnostic source/protocol changed after freeze")
    prepared, inputs = jobs_for(source, protocol)
    config = {"source": source, "protocol_sha256": sha256(PROTOCOL), "source_hashes": sources(), "inputs": inputs}
    identity = content_hash(config)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    if (out/"config.json").exists() and json.loads((out/"config.json").read_text()) != config:
        raise ValueError("Output identity mismatch")
    atomic_json(out/"config.json", config)
    windows = out/"windows"
    windows.mkdir(exist_ok=True)
    jobs = []
    for meta, x, outcome in prepared:
        path = windows/(meta["date"]+".json")
        if path.exists():
            value = json.loads(path.read_text())
            if value["identity"] != identity or value["metadata"] != meta or len(value["rows"]) != 3*len(METHODS):
                raise ValueError("Invalid cached window")
        else:
            jobs.append((meta, x, outcome, path, identity))
    print(source, "windows", len(prepared), "remaining", len(jobs), flush=True)
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for k, date in enumerate(pool.map(job_run, jobs), 1):
            if k % 50 == 0 or k == len(jobs):
                print(k, len(jobs), date, round(time.perf_counter()-start, 2), flush=True)
    values = [json.loads((windows/(m["date"]+".json")).read_text()) for m, _, _ in prepared]
    rows = [{**r, "weights": json.dumps(r["weights"])} for v in values for r in v["rows"]]
    write_csv(out/"forecasts.csv", rows)
    receipt = {"source": source, "status": "complete", "evidence": "development_only",
               "identity": identity, "windows": len(values), "rows": len(rows), "workers": workers,
               "computed_this_invocation": len(jobs), "wall_seconds": time.perf_counter()-start,
               "finished_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
               "forecasts_sha256": sha256(out/"forecasts.csv"),
               "window_sha256": {p.name: sha256(p) for p in sorted(windows.glob("*.json"))}}
    atomic_json(out/"receipt.json", receipt)
    print(source, "DONE", len(values), len(rows), flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", choices=["ecb", "synthetic"], required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--workers", type=int, default=2)
    args = ap.parse_args()
    if args.workers < 1:
        ap.error("workers must be positive")
    run(**vars(args))
