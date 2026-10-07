"""Frozen HMM development/pilot with per-origin atomic resume and progress."""
import os
for _key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[_key] = '1'

import argparse
import gzip
import hashlib
import importlib.metadata
import json
from pathlib import Path
import re
import subprocess
import time
import warnings

import hmmlearn
import numpy as np
from tqdm import tqdm
from selection_risk.runtime import ROOT, Run, atomic_json, digest, object_hash, utc
from continuous_cvar.evaluation import population_smooth
from temporal_risk.dgp import generate, laws
from temporal_risk.run import write_csv
from .model import fit_forecasts
from .analysis import aggregate


def config():
    return json.loads((ROOT/'markov_hmm/config.json').read_text())


def sources():
    paths = list((ROOT/'markov_hmm').glob('*.py'))
    paths += [ROOT/p for p in ['markov_hmm/PROTOCOL.md', 'markov_hmm/requirements.txt',
              'selection_risk/runtime.py', 'continuous_cvar/model.py', 'continuous_cvar/evaluation.py',
              'continuous_cvar_face/model.py', 'temporal_risk/dgp.py', 'temporal_risk/models.py',
              'temporal_risk/analysis.py', 'temporal_risk/run.py']]
    return {str(p.relative_to(ROOT)): digest(p) for p in sorted(paths)}


def dependency():
    package = Path(hmmlearn.__file__).parent
    return {'version': importlib.metadata.version('hmmlearn'),
            'files': {str(p.relative_to(package)): digest(p) for p in sorted(package.rglob('*'))
                      if p.suffix in {'.py', '.so'}}}


class HMMRun(Run):
    def __init__(self, out, cfg, inputs):
        super().__init__(out, cfg, inputs)
        self.identity['sources'] = sources()
        self.identity['environment']['hmmlearn'] = dependency()
        self.fingerprint = object_hash(self.identity)


def preflight(base):
    cfg = config()
    if (base/'preflight.json').exists():
        old = json.loads((base/'preflight.json').read_text())
        if old['sources'] != sources() or old['config_sha256'] != object_hash(cfg) or old['dependency'] != dependency():
            raise ValueError('Changed preflight identity; use a new run')
        return old
    candidates = set(range(cfg['seeds']['start'], cfg['seeds']['stop'])) | set(cfg['development_seeds'])
    pattern = re.compile(r'(?<!\d)('+'|'.join(map(str, sorted(candidates)))+r')(?!\d)')
    files, collisions = {}, []
    for path in ROOT.rglob('*'):
        rel = path.relative_to(ROOT)
        if any(part in {'.git', '.venv', '__pycache__', '.pytest_cache', 'data', '.semble'} for part in rel.parts):
            continue
        if not path.is_file() or rel.parts[0] == 'markov_hmm' or base.resolve() in path.resolve().parents:
            continue
        if pattern.search(path.name):
            collisions.append(str(rel))
        if path.suffix not in {'.json', '.csv', '.py', '.gz'}:
            continue
        if path.suffix == '.gz':
            with gzip.open(path, 'rt', errors='replace') as stream:
                # Stream large exports without imposing a seed-audit size cap.
                hit = any(pattern.search(line) for line in stream)
        else:
            with path.open(errors='replace') as stream:
                hit = any(pattern.search(line) for line in stream)
        files[str(rel)] = digest(path)
        if hit:
            collisions.append(str(rel))
    if collisions:
        raise ValueError(f'Seed collision in local records: {collisions}')
    tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')[:-1]
    receipt = {'utc': utc(), 'sources': sources(), 'config_sha256': object_hash(cfg), 'dependency': dependency(),
               'base_sha': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
               'protected_files': {p: digest(ROOT/p) for p in tracked}, 'candidate_seeds': sorted(candidates),
               'scanned_files': files, 'scanned_file_count': len(files), 'collisions': collisions,
               'scope': 'available local filenames/source/JSON/CSV/gzip; no unavailable external records'}
    atomic_json(base/'preflight.json', receipt)
    return receipt


def one_case(run, world, seed, origin, cfg, cache):
    started = time.perf_counter()
    if seed not in cache:
        generated = generate(seed, cfg)
        array = run.out/'paths'/f'path_{seed}.npz'
        array.parent.mkdir(parents=True, exist_ok=True)
        arrays = {f'{w}_{k}': v for w in cfg['worlds'] for k, v in generated[w].items()}
        if array.exists():
            with np.load(array, allow_pickle=False) as saved:
                for k, v in arrays.items():
                    np.testing.assert_array_equal(saved[k], v)
        else:
            tmp = array.with_suffix('.tmp')
            with tmp.open('wb') as stream:
                np.savez_compressed(stream, **arrays)
            tmp.replace(array)
        cache[seed] = generated, array, digest(array)
    generated, array, array_sha = cache[seed]
    data = generated[world]
    past = data['returns'][origin-cfg['window']:origin].copy()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        locked = fit_forecasts(past, cfg['fit'], cfg['model'], cfg['hmm'])
        # Truth enters only after all decisions and estimates have been locked.
        conditional, marginal, latent = laws(past, world, origin, cfg, len(past), int(data['states'][origin-1]))
        rows = []
        for policy, result in locked['policies'].items():
            diag = result['fit_diagnostics']
            if diag['convex_gap_bound'] > cfg['fit']['gap_tol'] or diag.get('feasibility', 0) > cfg['fit']['feasibility_tol']:
                raise ValueError('Portfolio numerical gate failed')
            theta = np.array(result['theta'])
            target, reference, hidden = [population_smooth(theta, law, cfg['model']['tau'], cfg['fit']['alpha'])[0]
                                         for law in [conditional, marginal, latent]]
            if min(target, reference) <= 1e-10:
                raise ValueError('Undefined relative error target')
            for method, estimate in result['estimates'].items():
                error = None if estimate is None else estimate/target - 1
                rows.append(dict(world=world, seed=seed, origin=origin, policy=policy, method=method,
                                 estimate=estimate, conditional_objective=target, marginal_objective=reference,
                                 latent_objective=hidden, conditional_signed_relative_error=error,
                                 conditional_squared_relative_error=None if error is None else error**2,
                                 marginal_squared_relative_error=None if estimate is None else (estimate/reference-1)**2,
                                 latent_information_gap=(hidden-target)/target, weights=json.dumps(theta[:-1].tolist()),
                                 threshold=float(theta[-1]), information_start=origin-len(past), information_stop=origin,
                                 information_n=len(past), holding_horizon=1,
                                 hmm_converged=locked['hmm']['converged']))
    return dict(status='COMPLETE', world=world, seed=seed, origin=origin, rows=rows, locked=locked,
                evaluation={label: {k: v.tolist() for k, v in law.items()} for label, law in
                            [('conditional', conditional), ('marginal', marginal), ('latent', latent)]},
                warnings=[str(w.message) for w in caught], seconds=time.perf_counter()-started,
                past_sha256=hashlib.sha256(past.tobytes()).hexdigest(),
                artifacts={str(array.relative_to(run.out)): array_sha})


def execute(stage, base, limit=0):
    cfg = config()
    audit = json.loads((base/'preflight.json').read_text())
    if audit['sources'] != sources() or audit['config_sha256'] != object_hash(cfg) or audit['dependency'] != dependency():
        raise ValueError('Frozen preflight identity changed')
    inputs = {'preflight_sha256': digest(base/'preflight.json')}
    if stage == 'pilot':
        benchmark = json.loads((base/'development/benchmark.json').read_text())
        if benchmark['sources'] != sources() or benchmark['config_sha256'] != object_hash(cfg):
            raise ValueError('Changed development identity')
        if not benchmark['numerical_gate'] or benchmark['estimated_pilot_seconds'] > cfg['compute_cap_seconds']:
            raise ValueError('Pilot NOT_RUN: development numerical/compute gate failed')
        inputs['benchmark_sha256'] = digest(base/'development/benchmark.json')
    seeds = cfg['development_seeds'] if stage == 'development' else list(range(cfg['seeds']['start'], cfg['seeds']['stop']))
    jobs = [(w, s, o) for s in seeds for w in cfg['worlds'] for o in cfg['origins']]
    np.random.default_rng(cfg['job_order_seed']).shuffle(jobs)
    run = HMMRun(base/stage, dict(cfg, stage=stage), inputs)
    cache = {}
    with run.session():
        payloads, new, resumed = [], 0, 0
        with tqdm(total=len(jobs), desc=stage, unit='origin') as bar:
            for world, seed, origin in jobs:
                key = f'{world}_{seed}_{origin}'
                payload = run.case(key)
                if payload is None:
                    if limit and new >= limit:
                        break
                    started = time.perf_counter()
                    try:
                        payload = one_case(run, world, seed, origin, cfg, cache)
                    except Exception as exc:
                        payload = dict(status='FAILED', world=world, seed=seed, origin=origin, rows=[],
                                       error=repr(exc), seconds=time.perf_counter()-started)
                    run.save(key, payload)
                    new += 1
                    run.event('case_complete', world=world, seed=seed, origin=origin, status=payload['status'],
                              seconds=payload['seconds'], completed=len(payloads)+1, total=len(jobs),
                              eta_seconds=(len(jobs)-len(payloads)-1)*sum(p['seconds'] for p in payloads+[payload])/(len(payloads)+1))
                else:
                    resumed += 1
                    run.event('case_resumed', world=world, seed=seed, origin=origin)
                payloads.append(payload)
                bar.update(1)
        complete = len(payloads) == len(jobs)
        failures = [p for p in payloads if p['status'] != 'COMPLETE']
        rows = [r for p in payloads for r in p['rows']]
        write_csv(run.out/'estimates.csv', rows)
        write_csv(run.out/'case_index.csv', [{k: p.get(k) for k in ['world', 'seed', 'origin', 'status', 'seconds', 'past_sha256', 'error']} for p in payloads])
        atomic_json(run.out/'diagnostics.json', [{k: v for k, v in p.items() if k not in {'rows', 'artifacts'}} for p in payloads])
        if complete and not failures and stage == 'pilot':
            for name, table in zip(['summary', 'paired', 'shift_effect'], aggregate(rows, cfg, seeds)):
                write_csv(run.out/f'{name}.csv', table)
        if complete and stage == 'development':
            numerical = not failures and all(r['estimate'] is not None for r in rows)
            numerical = numerical and all(p['locked']['hmm']['converged'] for p in payloads if p['status'] == 'COMPLETE')
            seconds = sum(p['seconds'] for p in payloads)
            atomic_json(run.out/'benchmark.json', dict(sources=sources(), config_sha256=object_hash(cfg), numerical_gate=numerical,
                        development_origins=len(jobs), observed_case_seconds=seconds,
                        estimated_pilot_seconds=seconds/len(jobs)*len(cfg['worlds'])*len(cfg['origins'])*(cfg['seeds']['stop']-cfg['seeds']['start'])*cfg['compute_gate_margin'],
                        metrics_used_to_select_model=False))
        receipt = dict(status=('COMPLETE' if not failures else 'INCOMPLETE_FAILED_CASES') if complete else 'PARTIAL_RESUMABLE',
                       cases_present=len(payloads), new_cases=new, resumed_cases=resumed, failed_cases=len(failures), rows=len(rows),
                       fingerprint=run.fingerprint, session_seconds=time.perf_counter()-run.started, finished_utc=utc())
        atomic_json(run.out/'receipt.json', receipt)
        run.event('session_end', **receipt)
        print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['preflight', 'development', 'pilot'])
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--max-new-cases', type=int, default=0)
    args = parser.parse_args()
    if args.max_new_cases < 0:
        parser.error('negative case limit')
    if args.stage == 'preflight':
        receipt = preflight(args.out)
        print(json.dumps({k: receipt[k] for k in ['scanned_file_count', 'collisions', 'config_sha256']}))
    else:
        execute(args.stage, args.out, args.max_new_cases)
