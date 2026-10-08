"""Export readable CSV tables from the complete frozen full-run summary."""
import argparse
import csv
import json
from pathlib import Path


def write(path, rows):
    with path.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v) if isinstance(v, (list, dict)) else v for k, v in row.items()})


def export(root):
    s = json.loads((root/'frozen/summary.json').read_text())
    if not s['complete'] or not s['all_checks_passed']:
        raise ValueError('complete, numerically passed summary required')
    write(root/'benchmark_summary.csv', [{'cell': cell, **r} for cell, r in s['benchmark'].items()])
    write(root/'memory_summary.csv', [{'cell': cell, **r} for cell, r in s['memory'].items()])
    policies, contrasts, bank_effects = [], [], []
    for family, r in s['policy'].items():
        for name, m in r['metrics'].items():
            policies.append({'family': family, 'policy': name, 'banks': r['independent_banks'],
                             'histories': r['histories'], 'mean_true_net_regret': m['regret']['mean'],
                             'ci95_low': m['regret']['ci95'][0], 'ci95_high': m['regret']['ci95'][1],
                             'switches': m['switches'], 'harmful_switches': m['harmful_switches'],
                             'mean_cost': m['mean_cost']})
        for name in ['shared_minus_rectangular', 'shared_minus_point', 'factorial_interaction']:
            m = r[name]
            contrasts.append({'family': family, 'contrast': name, 'banks': m['independent_banks'],
                              'mean': m['mean'], 'ci95_low': m['ci95'][0], 'ci95_high': m['ci95'][1],
                              'ci97_5_low': m['ci97_5'][0], 'ci97_5_high': m['ci97_5'][1],
                              'banks_negative': m['banks_negative'], 'banks_positive': m['banks_positive']})
            bank_effects.extend({'family': family, 'contrast': name, 'bank': i, 'mean_difference': v}
                                for i, v in enumerate(m['bank_means']))
    write(root/'policy_summary.csv', policies)
    write(root/'paired_cluster_contrasts.csv', contrasts)
    write(root/'bank_effects.csv', bank_effects)
    print(json.dumps({'benchmark_rows': len(s['benchmark']), 'memory_rows': len(s['memory']),
                      'policy_rows': len(policies), 'contrast_rows': len(contrasts),
                      'bank_effect_rows': len(bank_effects)}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--out', type=Path, required=True)
    export(parser.parse_args().out)
