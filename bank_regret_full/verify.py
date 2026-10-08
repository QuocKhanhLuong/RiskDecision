"""All-input provenance replay plus preregistered deep subset and LP checks."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
import multiprocessing
from pathlib import Path
import sys
import time

import numpy as np
from scipy.optimize import linprog
from tqdm import tqdm

from bank_regret.run import benchmark_input
from bank_regret.study import arrays_hash, generate_history, public_design
from mixture_order.run import atomic_json, digest, utc
from .analysis import summarize
from .run import ROOT, configuration, freeze, policy_case, read_case, tasks


def check_input(cfg, body):
    task, r = body['task'], body['result']
    actual = configuration(cfg, task)
    if task['kind'] != 'policy':
        inp = benchmark_input(actual, task['m'], task['n'], task['replicate'])
        assert r['input_sha256'] == inp['sha256']
        return {'deep': False, 'lp_solves': 0, 'lp_error': 0.}
    design = public_design(actual)
    history = generate_history(actual, design, task['family'], task['index'])
    assert r['history']['context'] == history['z'].tolist()
    assert r['history']['category'] == history['categories'].tolist()
    assert r['truth_q_evaluator_only'] == history['truth']['q']
    assert r['truth_components_evaluator_only'] == history['truth']['components'].tolist()
    assert r['input_sha256'] == arrays_hash(history['z'], history['categories'], design['loss_matrix'], design['weights'])
    deep = task['index'] < cfg['verification_histories_per_bank_family']
    count, error = 0, 0.
    if deep:
        regenerated = policy_case(cfg, task)
        assert digest(regenerated) == digest(r)
        # All distinct selected actions plus the evaluator's bank-best action.
        indices = set(r['decision']['selected'].values())
        indices.add(int(np.argmin(r['evaluation']['true_net_regrets'])))
        p = (1-history['truth']['q'])*history['truth']['components'][0]+history['truth']['q']*history['truth']['components'][1]
        for i in indices:
            loss = design['loss_matrix'][:, i]
            lp = linprog(-loss, A_eq=np.ones((1, len(p))), b_eq=[1],
                         bounds=list(zip(np.zeros(len(p)), p/actual['policy_alpha'])), method='highs')
            assert lp.success
            error = max(error, abs(-lp.fun-r['evaluation']['true_risks'][i]))
            count += 1
        assert error <= cfg['numeric_atol']
    return {'deep': deep, 'lp_solves': count, 'lp_error': error}


def check_saved(args):
    cfg, path, fp, task = args
    return check_input(cfg, read_case(Path(path), fp, task))


def verify(root):
    start = time.perf_counter()
    out = root/'frozen'
    cfg = json.loads((ROOT/'bank_regret_full/config.json').read_text())
    fp = freeze(out, cfg)
    layout = tasks(cfg)
    jobs = [t for values in layout.values() for t in values]
    assert {p.name for p in (out/'cases').glob('*.json.gz')} == {t['id']+'.json.gz' for t in jobs}
    records = [read_case(out/'cases'/(t['id']+'.json.gz'), fp, t) for t in jobs]
    summary = summarize(sorted(records, key=lambda r: r['task']['id']), cfg, len(jobs))
    assert summary['complete'] and summary['all_checks_passed']
    assert digest(summary) == digest(json.loads((out/'summary.json').read_text()))
    assert digest(summary) == digest(json.loads((root/'initial_completion.json').read_text()))
    by_key = {(r['result']['m'], r['result']['n'], r['result']['alpha'], r['result']['replicate']): r['result']
              for r in records if r['task']['kind'] == 'benchmark'}
    memory_checks = 0
    for body in records:
        t, r = body['task'], body['result']
        if t['kind'] == 'memory':
            bench = by_key[t['m'], t['n'], t['alpha'], t['replicate']]
            assert r['regrets_sha256'] == digest(bench[t['solver']]['regrets'])
            assert r['selected'] == bench[t['solver']]['selected']
            memory_checks += 1
    args = [(cfg, str(out/'cases'/(t['id']+'.json.gz')), fp, t) for t in jobs]
    with ProcessPoolExecutor(max_workers=cfg['policy_workers'], mp_context=multiprocessing.get_context('spawn')) as pool:
        checks = list(tqdm(pool.map(check_saved, args, chunksize=4), total=len(args),
                           desc='verify input recipes and fixed deep subset', unit='case'))
    before = json.loads((root/'start_receipt.json').read_text())
    protected = before['protected_files']
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest() == h for p, h in protected.items())
    unchanged = {}
    for label in ['partial', 'complete']:
        files = json.loads((root/f'{label}_checkpoint_hashes.json').read_text())
        assert all(hashlib.sha256((out/'cases'/p).read_bytes()).hexdigest() == h for p, h in files.items())
        unchanged[label] = len(files)
    assert unchanged == {'partial': 5, 'complete': len(jobs)}
    invocations = [json.loads(s) for s in (out/'invocations.jsonl').read_text().splitlines()]
    assert [(r['resumed'], r['new_cases']) for r in invocations[:3]] == [(0, 5), (5, len(jobs)-5), (len(jobs), 0)]
    assert all(r['new_cases'] == 0 for r in invocations[3:])
    receipt = {'utc': utc(), 'fingerprint': fp, 'passed': True, 'cases': len(jobs),
               'all_input_recipes_and_saved_truth_checked': True, 'summary_recomputed': True,
               'deep_refit_histories': sum(r['deep'] for r in checks),
               'independent_lp_solves': sum(r['lp_solves'] for r in checks),
               'independent_lp_max_error': max(r['lp_error'] for r in checks),
               'memory_cases_match_benchmark': memory_checks, 'protected_files_unchanged': len(protected),
               'resume_checkpoint_bytes_unchanged': unchanged, 'elapsed_seconds': time.perf_counter()-start,
               'scope': 'Same-case verification. Independent LP implementation, not independent scientific data or human review.'}
    atomic_json(root/'verification.json', receipt)
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--out', type=Path, required=True)
    verify(parser.parse_args().out)
