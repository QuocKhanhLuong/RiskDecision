"""Freeze source/data/protocol using development data only, before held-out runs."""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import numpy as np

from .data import load_panel, atomic_json, sha256
from .models import METHODS
from .runner import SPLITS, source_hashes


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path, default=Path("configs/market_protocol_v1.json"))
    args = p.parse_args()
    if args.out.exists():
        raise ValueError("Freeze already exists; never silently replace it")
    datasets, blocks = {}, {}
    for source in ["ecb", "boc"]:
        dates, returns, valid, manifest = load_panel(Path("data/raw")/source)
        end = SPLITS[source]["development"][1]
        dev = returns[np.array([d <= end for d in dates[1:]]) & valid]
        n = len(dev)
        # Conventional sample-size rule, transparent heuristic; sensitivity predeclared.
        length = max(5, min(60, int(np.ceil(n**(1/3)))))
        squared = np.mean(dev, axis=1)**2
        acf = [float(np.corrcoef(squared[:-lag], squared[lag:])[0, 1]) for lag in [1, 5, 20, 60]]
        blocks[source] = {"development_return_count": n, "development_end": end,
                          "development_returns_sha256": hashlib.sha256(dev.tobytes()).hexdigest(),
                          "primary_block_length": length, "squared_equal_exposure_acf_lags_1_5_20_60": acf}
        datasets[source] = {k: manifest[k] for k in ["raw_sha256", "levels_sha256", "columns", "cutoff", "first", "last", "valid_returns"]}
    freeze = {"protocol_version": 1, "frozen_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
              "heldout_performance_seen": False, "external_preregistration": False,
              "selected_candidate_from_synthetic": "support_band50", "selected_baseline_from_synthetic": "historical_se_penalty",
              "methods": METHODS, "splits": SPLITS, "datasets": datasets, "source_hashes": source_hashes(),
              "training": {"observations": 512, "gap_observations": 1, "all_training_returns_must_be_valid": True,
                           "horizon": "one consecutive published reference session", "final_stride": 1,
                           "origin": "00:00 UTC on target start date, before both reference endpoints",
                           "assumed_availability": "23:59:59 UTC on each observation date; unknown revisions/delays not reconstructed"},
              "models": {"q": .95, "bank_seed": 2026, "bank_size": 285, "cap": .5, "gmm_components": 3,
                         "gmm_base_observations": 256, "pooled_observations": 512, "scenarios": 1536,
                         "correction_steps": 8, "beta": .5, "band": 1., "rho": 1., "ewma_lambda": .94,
                         "seed_rule": "7000 + return index", "hyperparameter_tuning_budget": 0},
              "fallback": "Retain finite nonconverged outputs and flag every solver step. Exceptions/nonfinite/ES-below-VaR surfaces use historical estimate/selection, flagged; no model-specific date deletion.",
              "track_A": {"primary_target": "equal_weight", "secondary_target": "past-only historical_se_penalty reference",
                          "primary_score": "mean FZ0 upper-loss positive-ES domain; same target only",
                          "secondary": ["pinball95", "exceedance rate/count", "mean predicted ES", "shortfall identification residual"],
                          "undefined": "ES<=0 or invalid domain: no clipping; report denominator; paired contrasts use same finite dates"},
              "track_B": {"endpoint": "empirical pooled ES95 of selected one-session exposure losses",
                          "secondary": ["mean/sd/max loss", "HHI", "half L1 changes in target weights", "annual diagnostics"],
                          "interpretation": "policy exposure risk; no conditional ES truth, profit, Sharpe, execution or cost claim"},
              "bootstrap": {"method": "paired overlapping moving blocks of consecutive eligible observation dates; no circular wrap",
                            "block_rule": "ceil(n_development_valid_returns**(1/3)), bounded [5,60]; heuristic",
                            "by_source": blocks, "sensitivity_blocks": [5, 20, 60], "replicates": 5000, "seed": 20261005,
                            "ci": "95% pointwise percentile, stationarity approximation; no multiplicity-adjusted significance",
                            "primary_contrasts": ["support_band50 minus historical_se_penalty", "support_band50 minus support_mix50"]},
              "subperiods": "each calendar year in each split, all reported; small tail counts descriptive",
              "not_run": ["full selector-estimator cross-evaluation", "99% tail sensitivity", "yield curves", "neural models", "GARCH/DRO replication", "independent agent review"]}
    atomic_json(args.out, freeze)
    args.out.with_suffix(".sha256").write_text(sha256(args.out) + "\n")
    print(json.dumps({"path": str(args.out), "sha256": sha256(args.out), "bootstrap": blocks}, indent=2))


if __name__ == "__main__":
    main()
