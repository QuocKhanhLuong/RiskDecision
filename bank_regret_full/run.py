"""Immutable full-matrix execution, stage timing isolation, gzip resume receipts."""
import argparse
from concurrent.futures import ProcessPoolExecutor, wait, FIRST_COMPLETED
import fcntl
import gzip
import hashlib
import json
import multiprocessing
import os
from pathlib import Path
import platform
import resource
import subprocess
import sys
import time
import warnings

import numpy as np
import scipy
from tqdm import tqdm

from bank_regret.core import make_bank, solve_local, solve_union, solve_worlds
from bank_regret.run import benchmark_input, run_benchmark, run_policy
from bank_regret.study import public_design, seed
from mixture_order.core import FiniteMixture
from mixture_order.run import atomic_json, digest, utc
from .analysis import summarize

ROOT = Path(__file__).resolve().parents[1]
MODULE = Path(__file__).resolve().parent
BASE = json.loads((ROOT/'bank_regret/config.json').read_text())
THREADS = ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS']


def configuration(cfg, task, development=False):
    out = dict(BASE)
    ns = cfg['seed_namespace']+('/development' if development else '/assessment')
    if task['kind'] == 'policy':
        out['seed_namespace'] = ns+f"/bank-{task['bank']:03d}"
    else:
        out['seed_namespace'] = ns+f"/benchmark-alpha-{task['alpha']}"
        out['benchmark_alphas'] = [task['alpha']]
        out['timing_repetitions'] = cfg['timing_repetitions']
    return out


def tasks(cfg):
    stages = {'benchmark': [], 'memory': [], 'policy': []}
    for m in cfg['benchmark_banks']:
        for n in cfg['benchmark_supports']:
            for a in cfg['benchmark_alphas']:
                for r in range(cfg['benchmark_replicates_per_alpha']):
                    stages['benchmark'].append({'id': f'benchmark-{m}-{n}-{a}-{r}',
                        'kind': 'benchmark', 'm': m, 'n': n, 'alpha': a, 'replicate': r})
            for solver in ['local', 'union']:
                stages['memory'].append({'id': f'memory-{m}-{n}-{solver}', 'kind': 'memory',
                    'm': m, 'n': n, 'alpha': cfg['memory_alpha'], 'replicate': 0, 'solver': solver})
    for b in range(cfg['banks']):
        for family in BASE['policy_families']:
            for i in range(cfg['histories_per_bank_family']):
                stages['policy'].append({'id': f'policy-{b:03d}-{family}-{i:03d}',
                                        'kind': 'policy', 'bank': b, 'family': family, 'index': i})
    for name, items in stages.items():
        order = np.random.default_rng(seed(cfg, 'layout/'+name)).permutation(len(items))
        stages[name] = [items[i] for i in order]
    return stages


def freeze(out, cfg):
    files = sorted(p for directory in ['bank_regret_full', 'bank_regret', 'mixture_order']
                   for p in (ROOT/directory).glob('*.py'))
    files += [MODULE/'PROTOCOL.md', ROOT/'bank_regret/config.json', MODULE/'config.json']
    contract = {'files': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
                'config': cfg, 'python': sys.version, 'numpy': np.__version__, 'scipy': scipy.__version__,
                'platform': platform.platform(), 'python_binary': hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest(),
                'threads': {k: os.environ.get(k) for k in THREADS}}
    fp = digest(contract)
    path = out/'freeze.json'
    if path.exists():
        old = json.loads(path.read_text())
        if old['fingerprint'] != fp or digest(old['contract']) != fp:
            raise ValueError('changed frozen source/config/environment; use a new run directory')
    else:
        atomic_json(path, {'utc': utc(), 'fingerprint': fp, 'contract': contract})
        atomic_json(out/'layout.json', tasks(cfg))
    if json.loads((out/'layout.json').read_text()) != tasks(cfg):
        raise ValueError('changed task layout')
    return fp


def save_case(path, body):
    payload = {'body': body, 'sha256': digest(body)}
    encoded = gzip.compress(json.dumps(payload, sort_keys=True, allow_nan=False, separators=(',', ':')).encode(), mtime=0)
    temp = path.with_suffix(path.suffix+'.tmp')
    temp.write_bytes(encoded)
    os.replace(temp, path)


def read_case(path, fp, task):
    saved = json.loads(gzip.decompress(path.read_bytes()))
    body = saved['body']
    if saved['sha256'] != digest(body) or body['fingerprint'] != fp or body['task'] != task:
        raise ValueError('checkpoint payload, freeze or task identity mismatch')
    if task['kind'] != body['result']['kind']:
        raise ValueError('checkpoint result kind mismatch')
    if task['kind'] == 'policy' and digest(body['result']['decision']) != body['result']['decision_lock_sha256']:
        raise ValueError('checkpoint decision lock mismatch')
    return body


def policy_case(cfg, task, development=False):
    actual = configuration(cfg, task, development)
    r = run_policy(actual, task['family'], task['index'], development)
    r['bank'] = task['bank']
    design = public_design(actual)
    worlds = [make_bank(design['loss_matrix'], p, actual['policy_alpha']) for p in r['fit']['worlds']]
    reference = solve_worlds(worlds, r['decision']['costs'], [r['fit']['interval']]*len(worlds), solver=solve_union)
    error = float(np.max(np.abs(np.array(reference['regrets'])-r['decision']['shared_certificate']['regrets'])))
    agrees = reference['selected'] == r['decision']['selected']['shared_full']
    r['union_verification'] = {'max_error': error, 'choice_agrees': agrees, 'worlds_checked': len(worlds)}
    r['passed'] = bool(r['passed'] and error <= cfg['numeric_atol'] and agrees)
    return r


def peak_bytes():
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(value if sys.platform == 'darwin' else value*1024)


def memory_child(cfg, task):
    baseline = peak_bytes()
    actual = configuration(cfg, task)
    inp = benchmark_input(actual, task['m'], task['n'], task['replicate'])
    laws = [FiniteMixture(x, p0, p1, inp['alpha']) for x, p0, p1 in zip(inp['x'], inp['p0'], inp['p1'])]
    start = time.perf_counter()
    answer = (solve_local if task['solver'] == 'local' else solve_union)(laws, inp['costs'], inp['interval'])
    return {'kind': 'memory', 'm': task['m'], 'n': task['n'], 'solver': task['solver'],
            'alpha': inp['alpha'], 'input_sha256': inp['sha256'], 'peak_rss_bytes': peak_bytes(),
            'pre_input_peak_bytes': baseline, 'incremental_high_water_bytes': max(0, peak_bytes()-baseline),
            'solver_seconds': time.perf_counter()-start, 'selected': answer['selected'],
            'regrets_sha256': digest(answer['regrets']), 'passed': True,
            'scope': 'Fresh subprocess process peak RSS, not isolated native allocation measurement.'}


def perform(cfg, task, fp, development=False):
    before = time.perf_counter()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        if task['kind'] == 'policy':
            r = policy_case(cfg, task, development)
        elif task['kind'] == 'benchmark':
            r = run_benchmark(configuration(cfg, task, development), task['m'], task['n'], task['replicate'], development)
        else:
            args = json.dumps({'config': cfg, 'task': task})
            child = subprocess.run([sys.executable, '-m', 'bank_regret_full.run', 'memory-child', '--payload', args],
                                   cwd=ROOT, capture_output=True, text=True, check=True)
            r = json.loads(child.stdout)
            if child.stderr.strip():
                r['child_stderr'] = child.stderr
    return {'fingerprint': fp, 'task': task, 'utc': utc(), 'result': r,
            'elapsed_seconds': time.perf_counter()-before, 'captured_warnings': [str(w.message) for w in caught]}


def preflight(cfg, fp, out):
    file = out/'preflight.json'
    if file.exists():
        saved = json.loads(file.read_text())
        if saved['fingerprint'] != fp or saved['sha256'] != digest({k: v for k, v in saved.items() if k != 'sha256'}):
            raise ValueError('preflight identity mismatch')
        return saved
    started = time.perf_counter()
    cells = [t for t in tasks(cfg)['benchmark'] if t['replicate'] == 0]
    dev = dict(cfg, timing_repetitions=1)
    receipts = []
    for task in tqdm(cells, desc='preflight strata', unit='stratum'):
        record = perform(dev, task, fp, True)
        r = record['result']
        receipts.append({'task': task, 'elapsed_seconds': record['elapsed_seconds'], 'passed': r['passed'],
                         'max_regret_error': r['max_regret_error'], 'warnings': record['captured_warnings']})
        atomic_json(out/'preflight_progress.json', {'utc': utc(), 'done': len(receipts), 'expected': len(cells),
                                                  'elapsed_seconds': time.perf_counter()-started})
    begin_policy = time.perf_counter()
    dev_tasks = [{'kind': 'policy', 'id': f'dev-{i}', 'bank': i, 'family': 'stationary', 'index': 0}
                 for i in range(cfg['policy_workers'])]
    with ProcessPoolExecutor(max_workers=cfg['policy_workers'], mp_context=multiprocessing.get_context('spawn')) as pool:
        futures = [pool.submit(perform, cfg, t, fp, True) for t in dev_tasks]
        policies = [f.result() for f in futures]
    policy_wall = time.perf_counter()-begin_policy
    layout = tasks(cfg)
    projected_benchmark = sum(r['elapsed_seconds'] for r in receipts)*cfg['timing_repetitions']*cfg['benchmark_replicates_per_alpha']
    projected_policy = policy_wall/len(dev_tasks)*len(layout['policy'])
    projected_memory = sum(r['elapsed_seconds']+1. for r in receipts if r['task']['alpha'] == cfg['memory_alpha'])*2
    projection = projected_benchmark+projected_policy+projected_memory
    data = {'utc': utc(), 'fingerprint': fp, 'strata': receipts,
            'development_policy_count': len(policies), 'development_policy_wall_seconds': policy_wall,
            'development_policy_effectiveness_not_inspected_or_saved': True,
            'projected_benchmark_seconds': projected_benchmark, 'projected_policy_seconds': projected_policy,
            'projected_memory_seconds': projected_memory, 'projected_total_seconds': projection,
            'elapsed_seconds': time.perf_counter()-started,
            'passed': bool(all(r['passed'] for r in receipts) and all(r['result']['passed'] for r in policies)
                           and projection <= cfg['preflight_projected_seconds_limit'])}
    data['sha256'] = digest(data)
    atomic_json(file, data)
    return data


def execute(cfg, fp, out, max_new=None):
    started = time.perf_counter()
    if not preflight(cfg, fp, out)['passed']:
        raise ValueError('preflight failed; full matrix NOT RUN')
    layout = tasks(cfg)
    flattened = [t for stage in layout.values() for t in stage]
    folder = out/'cases'
    folder.mkdir(exist_ok=True)
    expected = {t['id']+'.json.gz' for t in flattened}
    if {p.name for p in folder.glob('*.json.gz')}-expected:
        raise ValueError('unknown checkpoint')
    records, completed = [], set()
    for task in tqdm(flattened, desc='validate saved checkpoints', unit='case'):
        path = folder/(task['id']+'.json.gz')
        if path.exists():
            records.append(read_case(path, fp, task))
            completed.add(task['id'])
    initial, new, stages = len(records), 0, {}
    with (out/'progress.jsonl').open('a', buffering=1) as log:
        log.write(json.dumps({'event': 'resume', 'utc': utc(), 'validated': initial})+'\n')
        for name, jobs in layout.items():
            pending = [t for t in jobs if t['id'] not in completed]
            if max_new is not None:
                pending = pending[:max(0, max_new-new)]
            before = time.perf_counter()
            done = 0
            with tqdm(total=len(jobs), initial=len(jobs)-sum(t['id'] not in completed for t in jobs),
                      desc=name, unit='case') as bar:
                def save(record):
                    nonlocal new, done
                    save_case(folder/(record['task']['id']+'.json.gz'), record)
                    records.append(record)
                    new += 1
                    done += 1
                    elapsed = time.perf_counter()-before
                    log.write(json.dumps({'event': 'case', 'utc': utc(), 'stage': name,
                                          'id': record['task']['id'], 'new_done': done, 'new_expected': len(pending),
                                          'elapsed_seconds': elapsed, 'eta_seconds': elapsed/done*(len(pending)-done),
                                          'passed': record['result']['passed']})+'\n')
                    bar.update(1)
                    if not record['result']['passed']:
                        raise ValueError('numerical check failed; checkpoint retained')
                try:
                    if name == 'policy' and pending:
                        with ProcessPoolExecutor(max_workers=cfg['policy_workers'], mp_context=multiprocessing.get_context('spawn')) as pool:
                            iterator = iter(pending)
                            active = {pool.submit(perform, cfg, t, fp): t for t in list(next(iterator, None) for _ in range(min(len(pending), cfg['policy_workers']*2))) if t is not None}
                            while active:
                                finished, _ = wait(active, timeout=10, return_when=FIRST_COMPLETED)
                                if not finished:
                                    log.write(json.dumps({'event': 'heartbeat', 'utc': utc(), 'stage': name,
                                                          'done': done, 'remaining': len(pending)-done})+'\n')
                                for future in finished:
                                    task = active.pop(future)
                                    save(future.result())
                                    next_task = next(iterator, None)
                                    if next_task is not None:
                                        active[pool.submit(perform, cfg, next_task, fp)] = next_task
                    else:
                        for task in pending:
                            save(perform(cfg, task, fp))
                except Exception as exc:
                    log.write(json.dumps({'event': 'error', 'utc': utc(), 'stage': name, 'error': repr(exc)})+'\n')
                    raise
            stages[name] = {'new_cases': done, 'wall_seconds': time.perf_counter()-before}
    summary = summarize(sorted(records, key=lambda r: r['task']['id']), cfg, len(flattened))
    atomic_json(out/'summary.json', summary)
    invocation = {'utc': utc(), 'resumed': initial, 'new_cases': new, 'stages': stages,
                  'complete': summary['complete'], 'all_checks_passed': summary['all_checks_passed'],
                  'outer_wall_seconds': time.perf_counter()-started}
    with (out/'invocations.jsonl').open('a') as f:
        f.write(json.dumps(invocation)+'\n')
    print(json.dumps(invocation, indent=2))
    return summary


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('stage', choices=['preflight', 'run', 'memory-child'])
    parser.add_argument('--out', type=Path)
    parser.add_argument('--config', type=Path, default=MODULE/'config.json')
    parser.add_argument('--payload')
    parser.add_argument('--max-new-cases', type=int)
    args = parser.parse_args()
    if args.stage == 'memory-child':
        p = json.loads(args.payload)
        print(json.dumps(memory_child(p['config'], p['task'])))
        return
    if args.out is None or (args.max_new_cases is not None and args.max_new_cases < 0):
        parser.error('--out required and --max-new-cases must be nonnegative')
    if any(os.environ.get(k) != '1' for k in THREADS):
        parser.error('set OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=VECLIB_MAXIMUM_THREADS=1')
    cfg = json.loads(args.config.read_text())
    args.out.mkdir(parents=True, exist_ok=True)
    with (args.out/'.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        fp = freeze(args.out, cfg)
        r = preflight(cfg, fp, args.out) if args.stage == 'preflight' else execute(cfg, fp, args.out, args.max_new_cases)
    if args.stage == 'preflight':
        print(json.dumps({k: v for k, v in r.items() if k != 'strata'}, indent=2))
    if not r.get('passed', r.get('all_checks_passed', False)):
        raise SystemExit(1)
    if args.stage == 'run' and not r['complete']:
        raise SystemExit(3)


if __name__ == '__main__':
    main()
