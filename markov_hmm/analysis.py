"""Paired path-cluster inference, retaining every origin and null cell."""
import numpy as np
from temporal_risk.analysis import interval, selected_origins


def aggregate(rows, cfg, seeds):
    lookup = {(r['world'], r['seed'], r['origin'], r['policy'], r['method']): r for r in rows}
    expected = {(w, s, o, p, m) for w in cfg['worlds'] for s in seeds for o in cfg['origins']
                for p in cfg['policies'] for m in cfg['methods']}
    if len(lookup) != len(rows) or set(lookup) != expected:
        raise ValueError('Missing or duplicated evaluation cells')

    def values(world, policy, method, metric, origins):
        result = []
        for seed in seeds:
            cells = [lookup[world, seed, o, policy, method][metric] for o in origins]
            if any(v is None or not np.isfinite(v) for v in cells):
                return None
            result.append(np.mean(cells))
        return np.array(result)

    def stats(x):
        mean, lo, hi = interval(x, cfg) if x is not None else (None, None, None)
        return dict(mean=mean, ci_low=lo, ci_high=hi, status='COMPLETE' if x is not None else 'INCOMPLETE', n_clusters=len(seeds))

    summaries, paired, shift = [], [], []
    metrics = ['conditional_squared_relative_error', 'conditional_signed_relative_error',
               'marginal_squared_relative_error', 'latent_information_gap']
    for world in cfg['worlds']:
        for policy in cfg['policies']:
            for period in ['all', 'before', 'after']:
                origins = selected_origins(cfg, period)
                cache = {}
                for method in cfg['methods']:
                    for metric in metrics:
                        cache[method, metric] = values(world, policy, method, metric, origins)
                        summaries.append(dict(world=world, policy=policy, period=period, method=method,
                                              metric=metric, **stats(cache[method, metric])))
                for baseline in [m for m in cfg['methods'] if m != 'hmm_filtered']:
                    for metric in metrics[:3]:
                        key = dict(world=world, policy=policy, period=period, method='hmm_filtered', baseline=baseline, metric=metric)
                        a, b = cache['hmm_filtered', metric], cache[baseline, metric]
                        paired.append(dict(key, primary=key == cfg['primary'], **stats(None if a is None or b is None else a-b)))
    for policy in cfg['policies']:
        for period in ['all', 'before', 'after']:
            for method in cfg['methods']:
                origins = selected_origins(cfg, period)
                metric = 'conditional_squared_relative_error'
                a = values('markov_shift', policy, method, metric, origins)
                b = values('markov_stationary', policy, method, metric, origins)
                shift.append(dict(policy=policy, period=period, method=method, metric=metric,
                                  interpretation='coupled pipeline shift effect; portfolios may differ across worlds',
                                  **stats(None if a is None or b is None else a-b)))
    return summaries, paired, shift
