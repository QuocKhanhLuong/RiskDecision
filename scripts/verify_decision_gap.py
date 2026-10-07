"""Independently reconstruct case metrics and parse every report table value."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from decision_gap_audit.run import contract
from coverage_audit.core import generate, bank, truth, conditional
from correction_audit.mechanism import fit
from local_market.data import sha256, atomic_json
from numpy.testing import assert_allclose
from threadpoolctl import threadpool_limits
from build_decision_gap_report import load, summarize, comparisons, wilson
import numpy as np
import json

ROOT = Path(__file__).resolve().parents[1]


def main():
    p, identity = contract(); w = bank(p["bank_seed"])
    src = ROOT/"runs/decision_gap_v1"; dst = ROOT/"results/decision_gap_v1"
    metrics = 0; refits = 0; cases = 0
    with threadpool_limits(limits=1):
        for f in p["families"]:
            for seed in p["seeds"]:
                path = src/"cases"/f"{f}_{seed}.json"; v = json.loads(path.read_text())
                assert v["identity"] == identity and v["arrays_sha256"] == sha256(path.with_suffix(".npz"))
                a = np.load(path.with_suffix(".npz"))
                x, pars, states = generate(seed, f, 512+p["gap"]+max(p["sizes"]))
                assert_allclose(a["returns"], x, atol=0, rtol=0)
                ids = a["ids"]; marginal = truth(w, pars)[1]
                if seed in [p["seeds"][0], p["seeds"][-1]]:
                    _, chosen, _, _, _ = fit(x[:512], w, seed)
                    assert list(ids) == [chosen[m] for m in ["historical_se_penalty", "support_mix50", "support_band50", "filtered_historical"]]
                    refits += 1
                for n in p["sizes"]:
                    end = 512+p["gap"]+n; y = -x[512+p["gap"]:end] @ w[ids].T
                    sorted_loss = np.sort(y, axis=0)
                    count = n*.05; full = int(np.floor(count)); frac = count-full
                    es = (sorted_loss[-full:].sum(0)+frac*sorted_loss[-full-1])/count
                    eta = np.quantile(y, .95, axis=0, method="inverted_cdf")
                    h = np.maximum(y-eta, 0)/.05; h -= h.mean(0)
                    b = 1 if f in ["gaussian", "student_t4", "asymmetric_crash"] else 16
                    k = n//b
                    z = np.random.default_rng(seed+100000+n).normal(size=(999,k)) @ h.reshape(k,b,4).sum(1) * np.sqrt(k/(k-1))/n
                    absolute = 2*np.quantile(np.abs(z).max(1), .95, method="higher")
                    paired = np.quantile(np.abs(z[:,1:]-z[:,:1]).max(1), .95, method="higher")
                    no_band = np.quantile(np.abs((z[:,1:]-z[:,:1])[:,[0,2]]).max(1), .95, method="higher")
                    radii = np.array([0., absolute, paired, no_band]); delta = es[1:]-es[0]
                    choices = np.array([np.argmin(delta)+1 if delta.min()+r < -1e-12 else 0 for r in radii])
                    j = [0,2][int(np.argmin(delta[[0,2]]))]
                    choices[3] = j+1 if delta[j]+no_band < -1e-12 else 0
                    assert paired <= absolute+1e-12
                    assert_allclose(a[f"n{n}_es"], es, atol=1e-12)
                    assert_allclose(a[f"n{n}_radii"], radii, atol=1e-12)
                    assert np.array_equal(a[f"n{n}_choices"], choices)
                    for estimand, pp in [("marginal", pars), ("next_conditional", conditional(f, pars, x[end-1], states[end-1]))]:
                        te = truth(w, pp)[1]; assert_allclose(a[f"n{n}_{estimand}_truth"], te)
                        for j, recipe in enumerate(["point", "absolute", "paired", "paired_no_band"]):
                            row = next(r for r in v["rows"] if r["n"] == n and r["estimand"] == estimand and r["recipe"] == recipe)
                            slot = choices[j]; pid = ids[slot]
                            menu = [0,2] if recipe == "paired_no_band" else [0,1,2]
                            expected = {"switched": int(slot != 0), "selected_slot": slot, "portfolio_id": pid,
                                        "harm": int(te[pid] > te[ids[0]]+1e-10),
                                        "relative_delta": (te[pid]-te[ids[0]])/marginal[ids[0]],
                                        "relative_regret": (te[pid]-te.min())/marginal.min(),
                                        "all_contrasts_covered": int(np.all(np.abs((delta-(te[ids[1:]]-te[ids[0]]))[menu]) <= radii[j]+1e-10)),
                                        "radius": radii[j]}
                            for key,value in expected.items(): assert_allclose(row[key], value, atol=1e-11)
                            metrics += len(expected)
                        for row in v["controls"]:
                            if row["n"] == n and row["estimand"] == estimand:
                                pid = row["portfolio_id"]
                                assert_allclose(row["relative_delta"], (te[pid]-te[ids[0]])/marginal[ids[0]])
                                assert_allclose(row["relative_regret"], (te[pid]-te.min())/marginal.min())
                                metrics += 2
                    if seed in [p["seeds"][0], p["seeds"][-1]]:
                        _, chosen, _, _, _ = fit(x[end-512:end], w, seed+200000+n)
                        for m in ["historical_se_penalty", "support_mix50", "support_band50", "filtered_historical"]:
                            rr = next(r for r in v["controls"] if r["n"] == n and r["method"] == "recent_"+m)
                            assert rr["portfolio_id"] == chosen[m]
                        refits += 1
                cases += 1
    raw = load(src/"rows.csv"); controls = load(src/"controls.csv")
    for expected, name in [(summarize(raw), "summary.csv"), (comparisons(raw, controls), "comparisons.csv")]:
        got = load(dst/name); assert len(got) == len(expected)
        for a,b in zip(expected,got):
            for k,value in a.items():
                if isinstance(value,(int,float)): assert_allclose(float(b[k]),value,equal_nan=True)
                else: assert str(value) == b[k]
    # Match every numeric and string table cell to an aggregate CSV row.
    datasets = [load(dst/f) for f in ["summary.csv", "comparisons.csv", "forecasts.csv"]]
    headers = None; cells = 0
    for line in (ROOT/"docs/DECISION_GAP_RESULTS.md").read_text().splitlines():
        if not line.startswith("|"):
            headers=None; continue
        vals = line.strip("|").split("|")
        if all(v == "---" for v in vals): continue
        if headers is None: headers=vals; continue
        def matches(row):
            for key,value in zip(headers,vals):
                if key not in row: return False
                try:
                    if not np.isclose(float(value),float(row[key]),atol=5.01e-7,rtol=0,equal_nan=True): return False
                except ValueError:
                    if value != row[key]: return False
            return True
        assert any(matches(r) for d in datasets for r in d), (headers,vals)
        cells += len(vals)
    assert cases == 1000 and len(raw) == 16000 and len(controls) == 40000
    receipt = json.loads((src/"first_execution_receipt.json").read_text())
    for name, digest in receipt["csv_hashes"].items(): assert sha256(src/f"{name}.csv") == digest
    for name,digest in receipt["case_hashes"].items(): assert sha256(src/"cases"/name) == digest
    audit = {"passed":True,"cases":cases,"recomputed_metrics":metrics,"model_refits":refits,
             "report_table_cells":cells,"source_identity":identity,"source_guard":True,
             "report_sha256":sha256(ROOT/"docs/DECISION_GAP_RESULTS.md")}
    atomic_json(dst/"audit.json",audit); print(json.dumps(audit,indent=2))


if __name__ == "__main__": main()
