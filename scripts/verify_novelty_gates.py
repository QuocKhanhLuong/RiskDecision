"""Verify published finite gates; no model training, no market evaluation."""
import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
from scipy.optimize import linprog
from tqdm import tqdm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from mixture_order.run import (ar_case, atomic_json, digest, jobs, read_checkpoint,
                               summarize, utc, validate_expected_case)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify(out):
    started = time.perf_counter()
    gates = out/'finite_gates'
    freeze = json.loads((gates/'freeze.json').read_text())
    assert digest(freeze['contract']) == freeze['fingerprint']
    assert all(sha(ROOT/path) == value for path, value in freeze['contract']['sources'].items())
    config = freeze['config']
    assert config == json.loads((ROOT/'mixture_order/config.json').read_text())
    preflight = json.loads((gates/'preflight.json').read_text())
    assert preflight['sha256'] == digest({k: v for k, v in preflight.items() if k != 'sha256'})
    assert preflight['passed'] and preflight['fingerprint'] == freeze['fingerprint']
    records = []
    expected = jobs(config)
    assert {p.name for p in (gates/'cases').glob('*.json')} == {f'{name}.json' for name, _ in expected}
    for name, args in tqdm(expected, desc='verify saved cases', unit='case'):
        body = read_checkpoint(gates/'cases'/f'{name}.json', freeze['fingerprint'], name)
        validate_expected_case(body, config, args)
        records.append(body)
    records.sort(key=lambda r: r['case_id'])
    summary = json.loads((gates/'summary.json').read_text())
    assert summary['complete'] and summary['all_checks_passed']
    assert digest(summary) == digest(summarize(records, config))
    # Independent LP formulation at endpoints and claimed worst-q, first full 16-case cycle.
    lp_checks, max_lp_error = 0, 0.
    for body in tqdm([r for r in records if r['result']['kind'] == 'mixture'][:16],
                     desc='independent tail LP', unit='case'):
        result = body['result']
        for q in [*result['inputs']['interval'], result['certificate']['argmax']]:
            risks = []
            for law in result['inputs']['laws']:
                x = np.array(law['loss'])
                p = (1-q)*np.array(law['p0'])+q*np.array(law['p1'])
                solved = linprog(-x, A_eq=np.ones((1, len(x))), b_eq=[1],
                                 bounds=list(zip(np.zeros(len(x)), p/law['alpha'])), method='highs')
                assert solved.success
                risks.append(-solved.fun)
                lp_checks += 1
            reported = np.interp(q, result['certificate']['knots'], result['certificate']['differences'])
            error = abs((risks[0]-risks[1])-reported)
            max_lp_error = max(max_lp_error, error)
            assert error < config['numeric_atol']
    reproduced_histories = 0
    for body in tqdm([r for r in records if r['result']['kind'] == 'ar'],
                     desc='reproduce AR receipts', unit='cell'):
        result = body['result']
        replay = ar_case(config, result['analytic']['length'], result['analytic']['phi'])
        assert digest(replay) == digest(result)
        reproduced_histories += result['independent_histories']
    original = json.loads((out/'start_receipt.json').read_text())
    changed = [p for p, value in original['protected_files'].items() if sha(ROOT/p) != value]
    assert not changed, changed
    resume = {}
    for receipt in ('partial_checkpoint_hashes.json', 'complete_checkpoint_hashes.json'):
        previous = json.loads((out/receipt).read_text())
        assert all(sha(gates/'cases'/name) == value for name, value in previous.items())
        resume[receipt] = len(previous)
    invocations = [json.loads(line) for line in (gates/'invocations.jsonl').read_text().splitlines()]
    assert invocations[-1]['new_cases'] == 0 and invocations[-1]['resumed_cases'] == len(expected)
    assert invocations[-1]['complete'] and invocations[-1]['all_checks_passed']
    git = lambda *args: subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()
    main_ancestor = subprocess.run(['git', 'merge-base', '--is-ancestor', 'origin/main', 'HEAD'],
                                   cwd=ROOT).returncode == 0
    result = {'utc': utc(), 'verified': True, 'source_fingerprint': freeze['fingerprint'],
              'complete_cases': len(records), 'independent_lp_solves': lp_checks,
              'max_lp_error': max_lp_error, 'reproduced_ar_histories': reproduced_histories,
              'reproduction_is_fresh_evidence': False, 'protected_files_unchanged': len(original['protected_files']),
              'resume_unchanged_checkpoints': resume, 'origin_main': git('rev-parse', 'origin/main'),
              'local_main': git('rev-parse', 'main'), 'main_is_ancestor': main_ancestor,
              'branch': git('branch', '--show-current'), 'elapsed_seconds': time.perf_counter()-started,
              'numpy': np.__version__, 'verifier_sha256': sha(__file__),
              'not_run': ['market evaluation', 'new learned model', 'estimated component uncertainty',
                          'reserve utility', 'human peer review']}
    atomic_json(out/'verification.json', result)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--out', type=Path, required=True)
    verify(parser.parse_args().out)
