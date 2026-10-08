"""Frozen, sequential computational audit with atomic checkpoints and resume."""
import argparse
from fractions import Fraction as F
import fcntl
import gzip
import hashlib
import itertools
import json
import os
from pathlib import Path
import platform
import sys
import time
import warnings

import numpy as np
import scipy
from tqdm import tqdm

from mixture_order.run import atomic_json, digest, utc
from .core import SimplexBank, solve_edges, solve_lp, witness_error
from .rational import enumerate_cells

ROOT = Path(__file__).resolve().parents[1]
MODULE = Path(__file__).resolve().parent
THREADS = ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS')


def seed(cfg, text):
    return int(hashlib.sha256((cfg['seed_namespace']+'/'+text).encode()).hexdigest()[:16], 16)


def tasks(cfg):
    result = []
    for kind in ['lp', 'scale']:
        for m, s, r, a, rep in itertools.product(cfg[kind+'_actions'], cfg[kind+'_scenarios'],
                cfg['components'], cfg['alphas'], range(cfg['replicates'])):
            result.append(dict(id=f'{kind}-{m}-{s}-{r}-{a}-{rep}', kind=kind,
                               m=m, s=s, r=r, alpha=a, replicate=rep))
    for r, rep in itertools.product([3, 4], range(cfg['rational_replicates'])):
        result.append(dict(id=f'rational-{r}-{rep}', kind='rational', m=3, s=6,
                           r=r, alpha=.2, replicate=rep))
    order = np.random.default_rng(seed(cfg, 'layout')).permutation(len(result))
    return [result[i] for i in order]


def make_input(cfg, task, development=False):
    name = ('development/' if development else 'assessment/')+task['id']
    rng = np.random.default_rng(seed(cfg, name))
    m, s, r = (task[k] for k in ('m', 's', 'r'))
    if task['kind'] == 'rational':
        x = rng.integers(-3, 6, (s, m))
        masses = rng.integers(0, 6, (r, s))
        masses[:, 0] += 1
        p = [[str(F(int(v), int(row.sum()))) for v in row] for row in masses]
        costs = [str(F(int(v), 100)) for v in rng.integers(0, 20, m)]
        return dict(x=x.tolist(), p=p, costs=costs, alpha='1/5', seed=seed(cfg, name))
    x = np.round(rng.normal(0, .3, (s, 3)) @ rng.normal(0, .3, (3, m))
                 + rng.normal(0, .1, (s, m)), 2)
    p = rng.gamma(.7, 1., (r, s))
    p[rng.random((r, s)) < .1] = 0.
    p[:, 0] += .01
    p /= p.sum(axis=1, keepdims=True)
    if seed(cfg, name) % 3 == 0:
        p[-1] = p[0]
    return dict(x=x.tolist(), p=p.tolist(), costs=rng.uniform(0, .01, m).tolist(),
                alpha=task['alpha'], seed=seed(cfg, name))


def as_bank(inp):
    return SimplexBank(inp['x'], [[float(F(v)) for v in row] for row in inp['p']],
                       float(F(inp['alpha'])), [float(F(v)) for v in inp['costs']])


def perform(cfg, task, development=False):
    before = time.perf_counter()
    inp = make_input(cfg, task, development)
    bank = as_bank(inp)
    results, timings = {}, {'local': [], 'union': []}
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        with np.errstate(over='raise', invalid='raise', divide='raise'):
            for repeat in range(cfg['timing_repetitions']):
                methods = ['local', 'union']
                if (seed(cfg, task['id'])+repeat) % 2:
                    methods.reverse()
                for method in methods:
                    start = time.perf_counter()
                    answer = solve_edges(bank, method)
                    timings[method].append(time.perf_counter()-start)
                    if method in results and results[method] != answer:
                        raise ArithmeticError('nondeterministic edge output')
                    results[method] = answer
            if task['kind'] in ('lp', 'rational'):
                start = time.perf_counter()
                results['lp'] = solve_lp(bank)
                timings['lp'] = [time.perf_counter()-start]
            if task['kind'] == 'rational':
                start = time.perf_counter()
                results['rational'] = enumerate_cells(inp['x'], inp['p'], inp['alpha'], inp['costs'])
                timings['rational'] = [time.perf_counter()-start]
    reference = np.array(results['local']['regrets'])
    errors = {name: float(np.max(abs(reference-[float(F(v)) for v in answer['regrets']])))
              for name, answer in results.items()}
    witnesses = {name: witness_error(bank, answer) for name, answer in results.items() if name != 'rational'}
    choices = {name: answer['selected'] for name, answer in results.items() if name != 'rational'}
    return dict(task=task, input=inp, input_sha256=digest(inp), results=results,
                timings=timings, max_errors=errors, witness_errors=witnesses,
                argmin_disagrees=len(set(choices.values())) > 1,
                passed=max([*errors.values(), *witnesses.values()]) <= cfg['numeric_atol'],
                elapsed_seconds=time.perf_counter()-before, warnings=[str(w.message) for w in caught])


def freeze(out, cfg):
    files = sorted(MODULE.glob('*.py'))+[MODULE/'config.json', MODULE/'PROTOCOL.md', ROOT/'tests/test_sparse_regret.py']
    files += sorted((ROOT/'bank_regret').glob('*.py'))+sorted((ROOT/'mixture_order').glob('*.py'))
    contract = dict(files={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
                    config=cfg, python=sys.version, numpy=np.__version__, scipy=scipy.__version__,
                    platform=platform.platform(), threads={k: os.environ.get(k) for k in THREADS})
    fp = digest(contract)
    path = out/'freeze.json'
    if path.exists():
        old = json.loads(path.read_text())
        if old['fingerprint'] != fp or digest(old['contract']) != fp:
            raise ValueError('frozen source/config/runtime changed; use a new run directory')
    else:
        atomic_json(path, dict(utc=utc(), fingerprint=fp, contract=contract))
        atomic_json(out/'layout.json', tasks(cfg))
    if json.loads((out/'layout.json').read_text()) != tasks(cfg):
        raise ValueError('task layout changed')
    return fp


def preflight(out, cfg, fp):
    path = out/'preflight.json'
    if path.exists():
        old = json.loads(path.read_text())
        if old['fingerprint'] != fp or digest(old['body']) != old['sha256']:
            raise ValueError('preflight changed')
        return old['body']
    cases = [dict(kind='lp', m=2, s=8, r=3, alpha=.05, replicate=0, id='dev-small'),
             dict(kind='lp', m=8, s=24, r=12, alpha=.2, replicate=0, id='dev-large'),
             dict(kind='scale', m=256, s=128, r=12, alpha=.2, replicate=0, id='dev-scale')]
    rows = [perform(cfg, t, True) for t in tqdm(cases, desc='development preflight', unit='case')]
    # Conservative: largest measured cell times every task of its kind.
    projection = 72*rows[1]['elapsed_seconds']+72*rows[2]['elapsed_seconds']+24*3.
    body = dict(cases=rows, projected_seconds=projection,
                passed=all(r['passed'] for r in rows) and projection <= cfg['preflight_projection_limit_seconds'])
    atomic_json(path, dict(fingerprint=fp, sha256=digest(body), body=body))
    return body


def read_case(path, fp, task):
    saved = json.loads(gzip.decompress(path.read_bytes()))
    body = saved['body']
    if (saved['sha256'] != digest(body) or body['fingerprint'] != fp or body['result']['task'] != task
            or body['result']['input_sha256'] != digest(body['result']['input'])):
        raise ValueError('checkpoint corrupted or incompatible')
    return body['result']


def save_case(path, fp, result):
    if path.exists():
        raise FileExistsError('never overwrite checkpoint')
    body = dict(fingerprint=fp, result=result, utc=utc())
    payload = gzip.compress(json.dumps(dict(body=body, sha256=digest(body)), sort_keys=True,
                                       allow_nan=False).encode(), mtime=0)
    temp = path.with_suffix('.tmp')
    temp.write_bytes(payload)
    os.replace(temp, path)


def summarize(rows, total):
    return dict(completed=len(rows), expected=total, complete=len(rows) == total,
                all_checks_passed=all(r['passed'] for r in rows),
                max_error=max((max(r['max_errors'].values()) for r in rows), default=0),
                max_witness_error=max((max(r['witness_errors'].values()) for r in rows), default=0),
                argmin_disagreements=sum(r['argmin_disagrees'] for r in rows),
                warning_count=sum(len(r['warnings']) for r in rows),
                lp_calls=sum(r['results'].get('lp', {}).get('lp_calls', 0) for r in rows),
                rational_systems=sum(r['results'].get('rational', {}).get('linear_systems', 0) for r in rows))


def execute(out, cfg, fp, limit):
    start = time.perf_counter()
    if not preflight(out, cfg, fp)['passed']:
        raise ValueError('preflight gate failed; full run NOT RUN')
    layout, rows, pending = tasks(cfg), [], []
    folder = out/'cases'
    folder.mkdir(exist_ok=True)
    if {p.name for p in folder.glob('*.json.gz')}-{t['id']+'.json.gz' for t in layout}:
        raise ValueError('unknown checkpoint present')
    for task in tqdm(layout, desc='validate resume', unit='case'):
        path = folder/(task['id']+'.json.gz')
        if path.exists():
            result = read_case(path, fp, task)
            if result['input'] != make_input(cfg, task):
                raise ValueError('checkpoint input recipe changed')
            if not result['passed']:
                raise ValueError('retained failed checkpoint; no silent retry')
            rows.append(result)
        else:
            pending.append(task)
    resumed, new = len(rows), 0
    with (out/'progress.jsonl').open('a', buffering=1) as log:
        log.write(json.dumps(dict(event='resume', utc=utc(), validated=resumed, pending=len(pending)))+'\n')
        with tqdm(total=len(layout), initial=resumed, desc='simplex audit', unit='case') as bar:
            for task in pending if limit is None else pending[:limit]:
                try:
                    result = perform(cfg, task)
                    save_case(folder/(task['id']+'.json.gz'), fp, result)
                    rows.append(result)
                    new += 1
                    elapsed = time.perf_counter()-start
                    log.write(json.dumps(dict(event='case', utc=utc(), id=task['id'], new=new,
                                             elapsed_seconds=elapsed, eta_seconds=elapsed/new*(len(pending)-new),
                                             passed=result['passed'], warnings=result['warnings']))+'\n')
                    bar.update(1)
                    if not result['passed']:
                        raise ArithmeticError('numerical gate failed; checkpoint retained')
                except Exception as exc:
                    log.write(json.dumps(dict(event='error', utc=utc(), id=task['id'], error=repr(exc)))+'\n')
                    raise
    summary = summarize(rows, len(layout))
    atomic_json(out/'summary.json', summary)
    receipt = dict(utc=utc(), resumed=resumed, new=new, elapsed_seconds=time.perf_counter()-start, **summary)
    with (out/'invocations.jsonl').open('a') as f:
        f.write(json.dumps(receipt)+'\n')
    print(json.dumps(receipt, indent=2))
    return summary


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--max-new-cases', type=int)
    parser.add_argument('--preflight-only', action='store_true')
    args = parser.parse_args()
    if any(os.environ.get(k) != '1' for k in THREADS):
        parser.error('all three BLAS thread variables must be 1')
    if args.max_new_cases is not None and args.max_new_cases < 0:
        parser.error('nonnegative max-new-cases required')
    cfg = json.loads((MODULE/'config.json').read_text())
    args.out.mkdir(parents=True, exist_ok=True)
    with (args.out/'.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        fp = freeze(args.out, cfg)
        if args.preflight_only:
            data = preflight(args.out, cfg, fp)
            print(json.dumps({k: v for k, v in data.items() if k != 'cases'}, indent=2))
            if not data['passed']:
                raise SystemExit(1)
        else:
            result = execute(args.out, cfg, fp, args.max_new_cases)
            if not result['complete']:
                raise SystemExit(3)


if __name__ == '__main__':
    main()
