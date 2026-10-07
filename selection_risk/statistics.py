"""Paired seed-cluster summaries; a portfolio bank is never a sample of markets."""
from collections import defaultdict
import numpy as np


def cluster_values(rows, metric, families):
    cells = {}
    for row in rows:
        key = (row["family"], int(row["seed"]))
        if key in cells:
            raise ValueError("Duplicate family/seed observation")
        cells[key] = float(row[metric])
    seeds = sorted({s for _, s in cells})
    if not seeds or set(cells) != {(f, s) for f in families for s in seeds}:
        raise ValueError("Unbalanced/missing family cells; do not silently drop cases")
    x = np.array([[cells[f, s] for f in families] for s in seeds]).mean(axis=1)
    if not np.isfinite(x).all():
        raise ValueError("Nonfinite metric")
    return seeds, x


def interval(values, reps, seed):
    values = np.asarray(values)
    if len(values) < 2:
        return float(values.mean()), None, None
    rng = np.random.default_rng(seed)
    indices = rng.integers(len(values), size=(reps, len(values)))
    lower, upper = np.quantile(values[indices].mean(axis=1), [.025, .975])
    return float(values.mean()), float(lower), float(upper)


def summarize_crossed(rows, config):
    groups = defaultdict(list)
    for row in rows:
        groups[row["forecaster"], row["selector"]].append(row)
    summaries, contrasts = [], []
    scopes = [("overall", config["families"])] + [(f, [f]) for f in config["families"]]
    metrics = ["relative_error", "signed_relative_error", "true_es", "relative_regret", "hhi"]
    for scope, families in scopes:
        for (forecaster, selector), values in groups.items():
            subset = [r for r in values if r["family"] in families]
            for metric in metrics:
                seeds, x = cluster_values(subset, metric, families)
                mean, lo, hi = interval(x, config["bootstrap_reps"], config["bootstrap_seed"])
                summaries.append(dict(scope=scope, forecaster=forecaster, selector=selector,
                                      metric=metric, n_clusters=len(seeds), mean=mean, ci_low=lo, ci_high=hi))
            if forecaster == "historical":
                continue
            baseline = [r for r in groups["historical", selector] if r["family"] in families]
            seeds, x = cluster_values(subset, "relative_error", families)
            bs, y = cluster_values(baseline, "relative_error", families)
            if seeds != bs:
                raise ValueError("Unpaired seed sets")
            mean, lo, hi = interval(x-y, config["bootstrap_reps"], config["bootstrap_seed"])
            contrasts.append(dict(scope=scope, forecaster=forecaster, baseline="historical",
                                  selector=selector, metric="relative_error_difference",
                                  n_clusters=len(seeds), mean=mean, ci_low=lo, ci_high=hi))
    return summaries, contrasts


def summarize_split(rows, config):
    result = []
    scopes = [("overall", config["families"])] + [(f, [f]) for f in config["families"]]
    for scope, families in scopes:
        subset = [r for r in rows if r["family"] in families]
        for fold in ("A_to_B", "B_to_A", "two_fold_policy_mean"):
            for metric in ("signed_relative_error", "relative_error", "squared_relative_error",
                           "threshold_gap", "relative_regret", "heldout_es_relative_error"):
                values = {}
                for method in ("resubstitution", "independent_split"):
                    rr = [r for r in subset if r["estimator"] == method and
                          (fold == "two_fold_policy_mean" or r["fold"] == fold)]
                    if fold == "two_fold_policy_mean":
                        pairs = defaultdict(list)
                        for r in rr:
                            pairs[r["family"], r["seed"]].append(r)
                        if any(len(v) != 2 or {r["fold"] for r in v} != {"A_to_B", "B_to_A"}
                               for v in pairs.values()):
                            raise ValueError("Missing split fold")
                        # Average fold metrics, not a fictional deployable portfolio.
                        rr = [dict(family=f, seed=s, **{metric: np.mean([r[metric] for r in pair])})
                              for (f,s), pair in pairs.items()]
                    seeds, values[method] = cluster_values(rr, metric, families)
                    mean, lo, hi = interval(values[method], config["bootstrap_reps"], config["bootstrap_seed"])
                    result.append(dict(scope=scope, fold=fold, estimator=method, metric=metric,
                                       n_clusters=len(seeds), mean=mean, ci_low=lo, ci_high=hi,
                                       primary=False))
                mean, lo, hi = interval(values["independent_split"]-values["resubstitution"],
                                        config["bootstrap_reps"], config["bootstrap_seed"])
                result.append(dict(scope=scope, fold=fold, estimator="split_minus_resubstitution",
                                   metric=metric, n_clusters=len(seeds), mean=mean, ci_low=lo, ci_high=hi,
                                   primary=scope=="overall" and fold=="A_to_B" and metric=="squared_relative_error"))
    return result
