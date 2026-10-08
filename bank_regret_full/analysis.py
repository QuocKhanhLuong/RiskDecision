"""Bank-cluster summaries; never count portfolios as independent histories."""
import numpy as np
from bank_regret.study import seed


def interval(bank_values, cfg, label):
    x = np.asarray(bank_values, float)
    rng = np.random.default_rng(seed(cfg, 'cluster-bootstrap/'+label))
    draws = x[rng.integers(0, len(x), (cfg['bootstrap_repetitions'], len(x)))].mean(axis=1)
    return {'mean': float(x.mean()), 'ci95': np.quantile(draws, [.025, .975]).tolist(),
            'ci97_5': np.quantile(draws, [.0125, .9875]).tolist(),
            'independent_banks': len(x), 'bank_means': x.tolist(),
            'banks_negative': int((x < 0).sum()), 'banks_positive': int((x > 0).sum())}


def summarize(records, cfg, expected):
    rs = [r['result'] for r in records]
    result = {'cases_done': len(rs), 'cases_expected': expected, 'complete': len(rs) == expected,
              'all_checks_passed': all(r['passed'] for r in rs),
              'failed_cases': [r['task']['id'] for r in records if not r['result']['passed']],
              'sum_case_seconds_not_wall_time': sum(r['elapsed_seconds'] for r in records),
              'numerical_warnings': [w for r in records for w in r['captured_warnings']],
              'true_law_coverage_guarantee': False, 'novelty_priority_established': False,
              'benchmark': {}, 'memory': {}, 'policy': {}}
    benchmarks = [r for r in rs if r['kind'] == 'benchmark']
    if benchmarks:
        result['benchmark_max_regret_error'] = max(r['max_regret_error'] for r in benchmarks)
        result['benchmark_max_witness_error'] = max(r['max_witness_error'] for r in benchmarks)
        result['benchmark_choice_disagreements'] = sum(not r['choice_agrees'] for r in benchmarks)
    for m in cfg['benchmark_banks']:
        for n in cfg['benchmark_supports']:
            for alpha in cfg['benchmark_alphas']:
                cell = [r for r in benchmarks if (r['m'], r['n'], r['alpha']) == (m, n, alpha)]
                if not cell:
                    continue
                local = np.array([np.median(r['timing_seconds']['local']) for r in cell])
                union = np.array([np.median(r['timing_seconds']['union']) for r in cell])
                result['benchmark'][f'{m}x{n}/alpha={alpha}'] = {
                    'replicates': len(cell), 'local_seconds': float(np.median(local)),
                    'union_seconds': float(np.median(union)),
                    'median_paired_speed_ratio': float(np.median(union/local)),
                    'speed_ratios': (union/local).tolist(),
                    'local_queries': [r['local']['risk_evaluations'] for r in cell],
                    'union_queries': [r['union']['risk_evaluations'] for r in cell]}
    for r in rs:
        if r['kind'] == 'memory':
            result['memory'][f"{r['m']}x{r['n']}/{r['solver']}"] = r
    policies = [r for r in rs if r['kind'] == 'policy']
    if policies:
        result['policy_union_max_error'] = max(r['union_verification']['max_error'] for r in policies)
        result['policy_union_choice_disagreements'] = sum(not r['union_verification']['choice_agrees'] for r in policies)
    for family in ['stationary', 'component_shift']:
        cell = [r for r in policies if r['family'] == family]
        if not cell:
            continue
        banks = sorted(set(r['bank'] for r in cell))
        counts = {b: sum(r['bank'] == b for r in cell) for b in banks}
        # Never publish inferential intervals from an incomplete/imbalanced stage.
        complete = len(banks) == cfg['banks'] and set(counts.values()) == {cfg['histories_per_bank_family']}
        if not complete:
            result['policy'][family] = {'histories': len(cell), 'complete': False, 'bank_counts': counts}
            continue
        names = list(cell[0]['evaluation']['policies'])
        metrics, means = {}, {}
        for name in names:
            means[name] = [float(np.mean([r['evaluation']['policies'][name]['true_net_regret']
                                         for r in cell if r['bank'] == b])) for b in banks]
            entries = [r['evaluation']['policies'][name] for r in cell]
            metrics[name] = {'regret': interval(means[name], cfg, family+'/'+name),
                             'switches': sum(x['switched'] for x in entries),
                             'harmful_switches': sum(x['harmful_switch'] for x in entries),
                             'mean_cost': float(np.mean([x['cost'] for x in entries]))}
        contrast = lambda a, b: np.array(means[a])-means[b]
        result['policy'][family] = {
            'complete': True, 'histories': len(cell), 'independent_banks': len(banks),
            'metrics': metrics,
            'shared_minus_rectangular': interval(contrast('shared_full', 'rectangular_full'), cfg, family+'/primary'),
            'shared_minus_point': interval(contrast('shared_full', 'point'), cfg, family+'/secondary'),
            'factorial_interaction': interval(contrast('shared_full', 'shared_endpoints')-
                                             contrast('rectangular_full', 'rectangular_endpoints'), cfg, family+'/interaction'),
            'shared_endpoint_choice_differences': sum(r['decision']['selected']['shared_full'] !=
                                                      r['decision']['selected']['shared_endpoints'] for r in cell),
            'rectangular_endpoint_choice_differences': sum(r['decision']['selected']['rectangular_full'] !=
                                                           r['decision']['selected']['rectangular_endpoints'] for r in cell),
            'stress_bound_underestimates': sum(r['evaluation']['stress_bound_underestimates_true_regret'] for r in cell),
            'nominal_common_bank_forecast_mse': float(np.mean([r['evaluation']['same_target_forecast_mse'] for r in cell])),
            'historical_common_bank_forecast_mse': float(np.mean([r['evaluation']['historical_same_target_forecast_mse'] for r in cell]))}
    return result
