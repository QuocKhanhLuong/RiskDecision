"""Verify the frozen compositional pilot; this is replay, not new evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

import numpy as np
from scipy.optimize import linprog
from tqdm import tqdm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bank_regret.core import make_bank, solve_union, solve_worlds
from bank_regret.run import benchmark_input, freeze, jobs, preflight, read_case, summarize
from bank_regret.study import evaluate, generate_history, public_design
from mixture_order.run import atomic_json, digest, utc


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def lp_es(loss, probability, alpha):
    result = linprog(-np.asarray(loss), A_eq=np.ones((1, len(loss))), b_eq=[1],
                     bounds=list(zip(np.zeros(len(loss)), np.asarray(probability)/alpha)),
                     method='highs')
    if not result.success:
        raise AssertionError(result.message)
    return -result.fun


def verify(root):
    started = time.perf_counter()
    out = root/'frozen'
    cfg, fingerprint = freeze(out)
    assert preflight(cfg, fingerprint, out)['passed']
    tasks = jobs(cfg)
    assert {p.stem for p in (out/'cases').glob('*.json')} == {n for n, _ in tasks}
    records = []
    for name, args in tqdm(tasks, desc='validate observed-input replay', unit='case'):
        records.append(read_case(out/'cases'/f'{name}.json', fingerprint, name, cfg, args))
    records.sort(key=lambda x: x['case_id'])
    summary = summarize(records, cfg)
    assert digest(summary) == digest(json.loads((out/'summary.json').read_text()))
    assert digest(summary) == digest(json.loads((root/'initial_completion.json').read_text()))
    assert summary['complete'] and summary['all_checks_passed']

    resume_counts = {}
    for label in ['partial', 'complete']:
        saved = json.loads((root/f'{label}_checkpoint_hashes.json').read_text())
        assert len(saved) == (5 if label == 'partial' else 96)
        assert all(file_hash(out/'cases'/name) == value for name, value in saved.items())
        resume_counts[label] = len(saved)
    invocations = [json.loads(s) for s in (out/'invocations.jsonl').read_text().splitlines()]
    assert [(x['resumed'], x['new_cases']) for x in invocations[:3]] == [(0, 5), (5, 91), (96, 0)]
    assert all(x['new_cases'] == 0 for x in invocations[3:])
    original = json.loads((root/'start_receipt.json').read_text())
    changed = [name for name, value in original['protected_files'].items()
               if not (ROOT/name).is_file() or file_hash(ROOT/name) != value]
    assert not changed, changed
    ancestry = subprocess.run(['git', 'merge-base', '--is-ancestor', 'origin/main', 'HEAD'],
                              cwd=ROOT, capture_output=True)
    assert ancestry.returncode == 0

    design = public_design(cfg)
    union_error = evaluation_error = 0.
    diagnostic = {family: {'histories': 0, 'shared_endpoint_choice_differences': 0,
                          'rectangular_endpoint_choice_differences': 0,
                          'nominal_vs_point_choice_differences': 0,
                          'histories_with_shared_surface_difference': 0,
                          'histories_with_rectangular_surface_difference': 0,
                          'max_shared_surface_difference': 0.,
                          'max_rectangular_surface_difference': 0.,
                          'world_action_curves_with_interior_knots': 0,
                          'world_action_curves_total': 0}
                  for family in cfg['policy_families']}
    policies = [r['result'] for r in records if r['result']['kind'] == 'policy']
    for r in tqdm(policies, desc='all learned worlds vs union baseline', unit='history'):
        fit, decision = r['fit'], r['decision']
        generated = generate_history(cfg, design, r['family'], r['index'])
        assert r['history']['context'] == generated['z'].tolist()
        assert r['history']['category'] == generated['categories'].tolist()
        assert r['truth_q_evaluator_only'] == generated['truth']['q']
        assert r['truth_components_evaluator_only'] == generated['truth']['components'].tolist()
        worlds = [make_bank(design['loss_matrix'], p, cfg['policy_alpha']) for p in fit['worlds']]
        solved = solve_worlds(worlds, decision['costs'], [fit['interval']]*len(worlds), solver=solve_union)
        err = float(np.max(np.abs(np.array(solved['regrets'])-decision['shared_certificate']['regrets'])))
        union_error = max(union_error, err)
        assert err <= cfg['numeric_atol']
        assert solved['selected'] == decision['selected']['shared_full']
        truth = {'components': r['truth_components_evaluator_only'], 'q': r['truth_q_evaluator_only']}
        ev = evaluate(cfg, design, decision, truth)
        assert digest(ev) == digest(r['evaluation'])
        for i, value in enumerate(ev['true_risks']):
            p = (1-truth['q'])*np.array(truth['components'][0])+truth['q']*np.array(truth['components'][1])
            direct = lp_es(design['loss_matrix'][:, i], p, cfg['policy_alpha'])
            evaluation_error = max(evaluation_error, abs(direct-value))
        d = diagnostic[r['family']]
        d['histories'] += 1
        selected = decision['selected']
        for kind in ['shared', 'rectangular']:
            d[f'{kind}_endpoint_choice_differences'] += int(selected[kind+'_full'] != selected[kind+'_endpoints'])
            surfaces = decision['regret_surfaces']
            delta = float(np.max(np.abs(np.array(surfaces[kind+'_full'])-surfaces[kind+'_endpoints'])))
            d[f'histories_with_{kind}_surface_difference'] += int(delta > cfg['numeric_atol'])
            d[f'max_{kind}_surface_difference'] = max(d[f'max_{kind}_surface_difference'], delta)
        d['nominal_vs_point_choice_differences'] += int(selected['nominal_components'] != selected['point'])
        for world in worlds:
            d['world_action_curves_with_interior_knots'] += sum(len(law.crossings(*fit['interval'])) > 2 for law in world)
            d['world_action_curves_total'] += len(world)

    lp_error, lp_count = 0., 0
    benchmarks = [r['result'] for r in records if r['result']['kind'] == 'benchmark']
    for r in tqdm(benchmarks, desc='independent LP witness audit', unit='bank'):
        inp = benchmark_input(cfg, r['m'], r['n'], r['replicate'])
        # All actions/competitors for the smallest banks. For larger banks,
        # audit the saved selected action and its claimed worst competitor.
        indices = range(r['m']) if r['m'] == min(cfg['benchmark_banks']) else [r['local']['selected']]
        for i in indices:
            q, owner = r['local']['worst_q'][i], r['local']['competitor'][i]
            check = range(r['m']) if r['m'] == min(cfg['benchmark_banks']) else sorted({i, owner})
            risks = {}
            for j in check:
                p = (1-q)*inp['p0'][j]+q*inp['p1'][j]
                risks[j] = lp_es(inp['x'][j], p, inp['alpha'])+inp['costs'][j]
                lp_count += 1
            gap = risks[i]-min(risks.values())
            lp_error = max(lp_error, abs(gap-r['local']['regrets'][i]))
    assert max(lp_error, evaluation_error) <= cfg['numeric_atol']
    receipt = {'utc': utc(), 'fingerprint': fingerprint, 'verified_cases': len(records),
               'protected_files_unchanged': len(original['protected_files']),
               'origin_main_is_ancestor': True, 'resume_unchanged_checkpoints': resume_counts,
               'summary_recomputed': True, 'observed_fit_decision_replay_histories': len(policies),
               'saved_history_and_evaluator_truth_match_generator': True,
               'learned_world_union_max_error': union_error,
               'independent_benchmark_lp_solves': lp_count, 'independent_benchmark_lp_max_error': lp_error,
               'independent_truth_lp_solves': len(policies)*cfg['policy_bank_size'],
               'independent_truth_lp_max_error': evaluation_error,
               'posthoc_diagnostics_not_used_for_selection': diagnostic,
               'elapsed_seconds': time.perf_counter()-started,
               'scope': 'Verification and diagnostics on the same saved cases, not independent scientific replication.',
               'passed': True}
    atomic_json(root/'verification.json', receipt)
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--out', type=Path, default=ROOT/'runs/compositional_risk/20261008')
    verify(parser.parse_args().out)
