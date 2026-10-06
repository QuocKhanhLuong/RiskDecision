"""Recompute metrics from local arrays; aggregate paired experimental results."""
from .run import ROOT, contract
from .core import *
from coverage_audit.analyze import wilson
from local_market.data import sha256, atomic_json
from local_market.stats import write_csv
from collections import defaultdict
from pathlib import Path
import argparse
import csv
import json

EVENTS = ["all_covered", "equal_q95_covered", "q90_all_covered", "q95_all_covered", "q975_all_covered", "under_cases", "over_cases"]
MEANS = ["features_covered_fraction", "zero_se_features", "se_ratio_min", "se_ratio_median", "se_ratio_at_worst_error", "tail_count_min", "width_ratio_median", "width_ratio_max"]


def group_summary(rows, keys, events, means, expected):
    groups = defaultdict(list)
    for r in rows:
        groups[tuple(str(r[k]) for k in keys)].append(r)
    result = []
    for key, values in sorted(groups.items()):
        if len(values) != expected or len({int(r["seed"]) for r in values}) != expected:
            raise ValueError("Missing/duplicated seed")
        out = dict(zip(keys, key)); out["replications"] = expected
        for event in events:
            count = sum(int(v[event]) for v in values)
            lo, hi = wilson(count, expected)
            out.update({event+"_count": count, event+"_rate": count/expected, event+"_lo": lo, event+"_hi": hi})
        for mean in means:
            out[mean+"_mean"] = float(np.mean([float(v[mean]) for v in values]))
        result.append(out)
    return result


def paired(rows, seeds):
    index = {(int(r["n"]), r["anchor"], r["recipe"], int(r["seed"])): r for r in rows}
    rng = np.random.default_rng(20261007)
    boot = rng.integers(len(seeds), size=(5000, len(seeds)))
    result = []
    for n in [256,1024,4096]:
        for anchor in ANCHORS:
            base = np.array([int(index[n, anchor, "plugin_max_t", s]["all_covered"]) for s in seeds])
            for recipe in RECIPES[1:]:
                other = np.array([int(index[n, anchor, recipe, s]["all_covered"]) for s in seeds])
                diff = other-base
                lo, hi = np.quantile(diff[boot].mean(1), [.025,.975])
                result.append({"n": n, "anchor": anchor, "contrast": recipe+" - plugin_max_t",
                               "coverage_difference": float(diff.mean()), "lo": float(lo), "hi": float(hi),
                               "rescued": int(((base == 0)&(other == 1)).sum()),
                               "lost": int(((base == 1)&(other == 0)).sum()), "replications": len(seeds)})
    return result


def analyze(run, out):
    p, identity = contract()
    run, out = Path(run), Path(out)
    receipt = json.loads((run/"receipt.json").read_text())
    if receipt["identity"] != identity:
        raise ValueError("Run identity mismatch")
    for name in ["cases", "bounded"]:
        if sha256(run/(name+".csv")) != receipt[name+"_csv_sha256"]:
            raise ValueError("CSV checksum mismatch")
    with (run/"cases.csv").open() as f: rows = list(csv.DictReader(f))
    with (run/"bounded.csv").open() as f: bounded = list(csv.DictReader(f))
    expected = {f"{s}.json" for s in p["seeds"]}
    if set(receipt["case_sha256"]) != expected or len(rows) != 5400 or len(bounded) != 600:
        raise ValueError("Incomplete run")
    rebuilt, rebuilt_bounded, metric_cells = [], [], 0
    w = bank(p["bank_seed"])
    for filename in sorted(expected):
        path = run/"cases"/filename
        if sha256(path) != receipt["case_sha256"][filename]: raise ValueError("Case checksum mismatch")
        value = json.loads(path.read_text())
        if value["identity"] != identity or sha256(path.with_suffix(".npz")) != value["arrays_sha256"]:
            raise ValueError("Case identity mismatch")
        x, pars, _ = generate(value["seed"], "gaussian", n=4352)
        sd = np.sqrt(np.einsum("ij,jk,ik->i", w, pars["cov"][0], w))
        with np.load(path.with_suffix(".npz")) as a:
            np.testing.assert_array_equal(x, a["returns"])
            np.testing.assert_allclose(sd, a["sd"], atol=1e-12, rtol=0)
            for r in value["rows"]:
                n, anchor = r["n"], r["anchor"]; key = f"n{n}_{anchor}"
                h = np.maximum(np.repeat(-x[256:256+n] @ w.T, 3, axis=1)-a[key+"_eta"], 0)
                target, var = normal_hinge_moments(a[key+"_eta"], np.repeat(sd, 3))
                exact_se, plugin_se = np.sqrt(var/n), h.std(0, ddof=1)/np.sqrt(n)
                for actual, name in [(h.mean(0),"center"),(target,"target"),(exact_se,"exact_se"),(plugin_se,"plugin_se")]:
                    np.testing.assert_allclose(actual, a[key+"_"+name], atol=1e-12, rtol=0)
                mm = metrics(h.mean(0), a[key+"_"+r["recipe"]], target, exact_se, plugin_se, h, a["es"])
                for name, val in mm.items():
                    np.testing.assert_allclose(val, r[name], atol=1e-12, rtol=0); metric_cells += 1
                rebuilt.append(r)
            for r in value["bounded"]:
                n = r["n"]; cap = p["bounded_control"]["cap_sigma"]*sd
                lo, hi, eps = dkw_es(np.clip(-x[256:256+n] @ w.T,-cap,cap), -cap, cap)
                true = clipped_normal_es(sd)
                for actual, name in [(lo,"lo"),(hi,"hi"),(true,"truth")]:
                    np.testing.assert_allclose(actual, a[f"n{n}_dkw_"+name], atol=1e-12, rtol=0)
                assert int(((lo<=true+1e-12)&(true<=hi+1e-12)).all()) == r["all_covered"]
                assert np.isclose(eps, r["epsilon"])
                rebuilt_bounded.append(r)
    def compare_csv(a,b,keys):
        index = lambda r: tuple(str(r[k]) for k in keys)
        for x,y in zip(sorted(a,key=index), sorted(b,key=index)):
            assert index(x)==index(y)
            for key,val in y.items():
                if isinstance(val,(float,int)): np.testing.assert_allclose(float(x[key]),val,atol=1e-12,rtol=0)
                else: assert x[key]==val
    compare_csv(rows, rebuilt, ["seed","n","anchor","recipe"])
    compare_csv(bounded, rebuilt_bounded, ["seed","n"])
    out.mkdir(parents=True, exist_ok=True)
    summary = group_summary(rows,["n","anchor","recipe"],EVENTS,MEANS,200)
    bs = group_summary(bounded,["n"],["all_covered","equal_covered"],["epsilon","width_relative_median","upper_at_support_fraction","clipping_es_relative_change"],200)
    write_csv(out/"coverage.csv",summary); write_csv(out/"bounded.csv",bs); write_csv(out/"paired.csv",paired(rows,p["seeds"]))
    original = json.loads((run/"first_execution_receipt.json").read_text())
    if original["identity"] != identity: raise ValueError("First execution identity mismatch")
    atomic_json(out/"provenance.json",{k:v for k,v in original.items() if k != "case_sha256"})
    atomic_json(out/"audit.json",{"status":"PASS","identity":identity,"cases":200,"rows":5400,"bounded_rows":600,
                "metrics_recomputed":metric_cells,"inputs_regenerated":200,"aggregate_sha256":{name:sha256(out/name) for name in ["coverage.csv","bounded.csv","paired.csv"]}})
    print("PASS",metric_cells,"metrics; 200 regenerated inputs; 600 bounded ES intervals rechecked")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run",type=Path,default=ROOT/"runs/tail_band_v1")
    ap.add_argument("--out",type=Path,default=ROOT/"results/tail_band_v1")
    analyze(**vars(ap.parse_args()))
