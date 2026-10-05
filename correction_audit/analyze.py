"""Recompute diagnostic tables and paired exploratory intervals from local artifacts."""
from .mechanism import METHODS
from .run import contract, jobs_for
from local_market.models import bank
from local_market.data import sha256, atomic_json
from local_market.stats import write_csv, summary, block_indices
from local_market.scoring import empirical_es, score
import argparse
import csv
import json
from pathlib import Path
import numpy as np

REFERENCES = ["support_mix50", "historical_se_penalty", "support_point50", "random_band50"]
TARGETS = [("A", "equal_weight"), ("A", "historical_se_reference"), ("B", "own_selection")]


def paired(rows, source, protocol):
    output = []
    spec = protocol["uncertainty"]
    for track, target in TARGETS:
        rr = [r for r in rows if (r["track"], r["target"]) == (track, target)]
        lookup = {(r["date"], r["method"]): r for r in rr}
        dates = sorted({r["date"] for r in rr})
        if len(lookup) != len(rr) or len(rr) != len(dates)*len(METHODS):
            raise ValueError("Unpaired rows")
        if source == "ecb":
            metric = "fz0" if track == "A" else "realized_loss"
            values = np.array([[lookup[d, m][metric] for m in METHODS] for d in dates], dtype=float)
            if not np.isfinite(values).all():
                raise ValueError("Undefined paired endpoint; report it before inference")
            reducer = (lambda a, axis: np.mean(a, axis=axis)) if track == "A" else empirical_es
            estimate = reducer(values, axis=0)
            blocks = spec["ecb_blocks"]
        else:
            metric = "relative_error" if track == "A" else "relative_regret"
            # One bootstrap unit per seed, preserving all four paired families.
            seeds = protocol["synthetic"]["seeds"]
            values = np.array([[np.mean([r[metric] for r in rr if r["seed"] == s and r["method"] == m])
                                for m in METHODS] for s in seeds])
            reducer = lambda a, axis: np.mean(a, axis=axis)
            estimate, blocks = values.mean(0), [0]
        for block in blocks:
            rng = np.random.default_rng(spec["seed"])
            draws = []
            for offset in range(0, spec["replicates"], 100):
                count = min(100, spec["replicates"]-offset)
                ix = block_indices(rng, len(values), block, count) if block else rng.integers(len(values), size=(count, len(values)))
                draws.append(reducer(values[ix], axis=1))
            draws = np.concatenate(draws)
            c = METHODS.index("support_band50")
            for ref in REFERENCES:
                j = METHODS.index(ref)
                low, high = np.quantile(draws[:, c]-draws[:, j], [.025, .975])
                output.append({"track": track, "target": target, "candidate": "support_band50", "reference": ref,
                               "metric": "pooled_es95_pp" if source == "ecb" and track == "B" else metric,
                               "n_pairs": len(dates), "bootstrap_units": len(values), "block": block,
                               "difference": float(estimate[c]-estimate[j]), "ci_low": float(low), "ci_high": float(high),
                               "status": "development-only pointwise exploratory interval"})
    return output


def analyze(run, out):
    run, out = Path(run), Path(out)
    protocol = contract()
    receipt = json.loads((run/"receipt.json").read_text())
    if sha256(run/"forecasts.csv") != receipt["forecasts_sha256"]:
        raise ValueError("Forecast checksum mismatch")
    paths = sorted((run/"windows").glob("*.json"))
    if {p.name: sha256(p) for p in paths} != receipt["window_sha256"]:
        raise ValueError("Window checksum mismatch")
    values = [json.loads(p.read_text()) for p in paths]
    rows = [r for v in values for r in v["rows"]]
    source = receipt["source"]
    prepared, _ = jobs_for(source, protocol)
    originals = {meta["date"]: (meta, x, outcome) for meta, x, outcome in prepared}
    with (run/"forecasts.csv").open() as f:
        csv_rows = list(csv.DictReader(f))
    csv_lookup = {(r["date"], r["track"], r["target"], r["method"]): r for r in csv_rows}
    assert len(csv_lookup) == len(csv_rows) == len(rows)
    assert len(values) == len(originals)
    identity_max, common_groups, score_checks = 0., 0, 0
    for v in values:
        if v["identity"] != receipt["identity"] or len(v["rows"]) != len(METHODS)*3:
            raise ValueError("Window identity/row count mismatch")
        meta, _, outcome = originals[v["metadata"]["date"]]
        assert meta == v["metadata"]
        weights = bank(meta["bank_seed"])
        if source == "synthetic":
            with np.load(Path(__file__).resolve().parents[1]/meta["archive_path"]) as archive:
                original_truth = archive["true_es"].copy()
        for r in v["rows"]:
            csv_row = csv_lookup[r["date"], r["track"], r["target"], r["method"]]
            for key, value in r.items():
                expected = json.dumps(value) if key == "weights" else "" if value is None else str(value)
                assert csv_row[key] == expected
            np.testing.assert_array_equal(r["weights"], weights[r["portfolio_id"]])
            if source == "ecb":
                assert abs(r["realized_loss"]+outcome @ weights[r["portfolio_id"]]) < 1e-12
            else:
                te = original_truth[r["portfolio_id"]]
                assert abs(r["true_es"]-te) < 1e-10
                assert abs(r["relative_error"]-abs(r["predicted_es"]-te)/te) < 1e-10
                assert abs(r["relative_regret"]-(te/original_truth.min()-1)) < 1e-10
        if source == "ecb":
            m = v["metadata"]
            assert protocol["ecb"]["from"] <= m["date"] <= protocol["ecb"]["through"]
            assert m["last_training_available"] < m["origin"]
            for r in v["rows"]:
                calculated = score(r["realized_loss"], r["var95"], r["es95"])
                for key, value in calculated.items():
                    assert r[key] == value
                score_checks += 1
        for target in protocol["common_targets"]:
            rr = [r for r in v["rows"] if r["track"] == "A" and r["target"] == target]
            assert len(rr) == len(METHODS)
            assert all(r["weights"] == rr[0]["weights"] for r in rr)
            key = "realized_loss" if source == "ecb" else "true_es"
            assert all(r[key] == rr[0][key] for r in rr)
            common_groups += 1
        identity_max = max(identity_max, max(abs(d["identity_residual"]) for d in v["decomposition"]))
    if source == "ecb":
        for r in rows:
            r["fz0"] = np.nan if r["fz0"] is None else r["fz0"]
        tables = summary(rows)
        annual = [{"year": year, **r} for year in sorted({r["date"][:4] for r in rows})
                  for r in summary([r for r in rows if r["date"].startswith(year)])]
        write_csv(out/"annual.csv", annual)
    else:
        tables = []
        for family in ["all"]+protocol["synthetic"]["families"]:
            for track, target in TARGETS:
                for method in METHODS:
                    rr = [r for r in rows if r["track"] == track and r["target"] == target and r["method"] == method
                          and (family == "all" or r["family"] == family)]
                    tables.append({"family": family, "track": track, "target": target, "method": method, "n": len(rr),
                                   "mean_relative_error": float(np.mean([r["relative_error"] for r in rr])),
                                   "mean_relative_regret": float(np.mean([r["relative_regret"] for r in rr])),
                                   "mean_true_es": float(np.mean([r["true_es"] for r in rr]))})
    write_csv(out/"summary.csv", tables)
    write_csv(out/"paired_differences.csv", paired(rows, source, protocol))
    diagnostics, decompositions = [], []
    groups = ["all"]+ (protocol["synthetic"]["families"] if source == "synthetic" else sorted({v["metadata"]["date"][:4] for v in values}))
    for group in groups:
        vv = [v for v in values if group == "all" or v["metadata"].get("family", v["metadata"]["date"][:4]) == group]
        for method in ["support_band50", "support_point50", "random_band50"]:
            dd = [v["diagnostics"][method] for v in vv]
            row = {"group": group, "method": method, "n": len(dd)}
            for key in ["prior_all_within_band", "unchanged_surface", "same_selection_as_mix", "converged"]:
                row[key+"_n"] = sum(d[key] for d in dd)
            for key in ["tv_from_prior", "kl_from_prior", "max_abs_es_change", "prior_max_standardized_residual",
                        "posterior_max_standardized_residual", "scale_floor_fraction", "max_posterior_anchor_gap"]:
                row["mean_"+key] = float(np.mean([d[key] for d in dd]))
            diagnostics.append(row)
        for track, target in TARGETS:
            for method in ["support_mix50", "support_band50", "support_point50", "random_band50"]:
                dd = [d for v in vv for d in v["decomposition"] if (d["track"], d["target"], d["method"]) == (track, target, method)]
                row = {"group": group, "track": track, "target": target, "method": method, "n": len(dd), "reference": dd[0]["reference"]}
                for key in ["es_error", "fitted_moment_residual", "target_sampling_error", "reference_anchor_gap", "posterior_anchor_gap"]:
                    row["mean_"+key] = float(np.mean([d[key] for d in dd]))
                    row["mean_abs_"+key] = float(np.mean([abs(d[key]) for d in dd]))
                decompositions.append(row)
    write_csv(out/"mechanism.csv", diagnostics)
    write_csv(out/"decomposition.csv", decompositions)
    audit = {"status": "PASS", "source": source, "windows": len(values), "rows": len(rows),
             "csv_rows_matched_to_windows": len(csv_rows), "original_targets_recomputed": len(rows),
             "common_target_groups_checked": common_groups, "score_rows_recomputed": score_checks,
             "max_decomposition_identity_residual": identity_max,
             "base_gmm_nonconverged": sum(not v["diagnostics"]["base_gmm"]["converged"] for v in values),
             "base_gmm_warning_windows": sum(bool(v["diagnostics"]["base_gmm"]["warnings"]) for v in values),
             "max_archive_surface_error": max((max(v["diagnostics"]["archive_surface_max_errors"].values()) for v in values), default=0.) if source == "synthetic" else None,
             "review": "coordinator artifact checks; not independent review"}
    atomic_json(out/"audit.json", audit)
    # Public receipt contains hashes/counts only, never raw market rows or per-date weights.
    atomic_json(out/"provenance.json", {"receipt": {k: v for k, v in receipt.items() if k != "window_sha256"},
                                        "config": json.loads((run/"config.json").read_text()),
                                        "csv_sha256": {p.name: sha256(p) for p in sorted(out.glob("*.csv"))}})
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    analyze(**vars(ap.parse_args()))
