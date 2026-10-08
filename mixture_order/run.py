"""Bounded synthetic audit with frozen inputs, progress, and verified resume."""
import argparse
import fcntl
import hashlib
import json
import os
import platform
import sys
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from tqdm import tqdm

from .core import FiniteMixture, ar_analytic, hull_certificate, paired_certificate, rational_witness, ru_envelope

ROOT = Path(__file__).resolve().parents[1]
MODULE = Path(__file__).resolve().parent


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix+'.tmp')
    with temp.open('wb') as stream:
        stream.write(json.dumps(value, indent=2, sort_keys=True, allow_nan=False).encode()+b'\n')
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temp, path)


def utc():
    return datetime.now(timezone.utc).isoformat()


def freeze(out):
    config = json.loads((MODULE/'config.json').read_text())
    paths = sorted(MODULE.glob('*.py')) + [MODULE/'config.json', MODULE/'PROTOCOL.md']
    contract = {'sources': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
                'python': sys.version, 'numpy': np.__version__, 'platform': platform.platform(),
                'python_binary_sha256': hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest(),
                'thread_environment': {k: os.environ.get(k) for k in
                                       ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS')}}
    fingerprint = digest(contract)
    receipt = out/'freeze.json'
    if receipt.exists():
        saved = json.loads(receipt.read_text())
        if saved['fingerprint'] != fingerprint or digest(saved['contract']) != fingerprint:
            raise ValueError('source/config/environment changed; use a new run directory')
    else:
        atomic_json(receipt, {'utc': utc(), 'fingerprint': fingerprint, 'contract': contract,
                              'config': config})
    return config, fingerprint


def case_seed(config, case_id):
    raw = f"{config['seed_namespace']}/{case_id}".encode()
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], 'big')


def mixture_input(config, index, prefix='mixture'):
    seed = case_seed(config, f'{prefix}-{index:04d}')
    rng = np.random.default_rng(seed)
    sizes, alphas = config['support_sizes'], config['tail_probabilities']
    size = sizes[index % len(sizes)]
    alpha = alphas[(index // len(sizes)) % len(alphas)]
    laws = []
    for n in (size, size+3):
        laws.append({'loss': rng.standard_t(5, n).tolist(),
                     'p0': rng.dirichlet(np.full(n, .3)).tolist(),
                     'p1': rng.dirichlet(np.full(n, .3)).tolist(), 'alpha': alpha})
    interval = [0., 1.] if index % 2 == 0 else sorted(rng.uniform(0, 1, 2).tolist())
    return {'seed': seed, 'size': size, 'alpha': alpha, 'interval': interval, 'laws': laws}


def mixture_case(config, index, prefix='mixture'):
    inp = mixture_input(config, index, prefix)
    lo, hi = inp['interval']
    a, b = (FiniteMixture(**law) for law in inp['laws'])
    cert, hull = paired_certificate(a, b, lo, hi), hull_certificate(a, b, lo, hi)
    q = np.union1d(cert['knots'], hull['knots'])
    ea, eb = ru_envelope(a), ru_envelope(b)
    curve_error = float(np.max(np.abs((a.es(q)-b.es(q))-(ea(q)-eb(q)))))
    upper_error = abs(cert['upper']-hull['upper'])
    samples = {'crossings': [], 'generic_ru_hull': []}
    for repeat in range(config['timing_repetitions']):
        # Alternate call order; both include input validation, sorting and preprocessing.
        methods = [('crossings', paired_certificate), ('generic_ru_hull', hull_certificate)]
        if repeat % 2:
            methods.reverse()
        for name, method in methods:
            start = time.perf_counter()
            aa, bb = (FiniteMixture(**law) for law in inp['laws'])
            method(aa, bb, lo, hi)
            samples[name].append(time.perf_counter()-start)
    tol = config['numeric_atol']
    return {'kind': 'mixture', 'inputs': inp, 'certificate': cert, 'hull': hull,
            'max_curve_error': curve_error, 'upper_error': upper_error,
            'endpoint_underestimate': cert['upper']-cert['endpoint_upper'],
            'endpoint_false_safe': bool(cert['endpoint_upper'] < -tol and cert['upper'] > tol),
            'independent_bound_slack': cert['independent_upper']-cert['upper'],
            'timing_samples_seconds': samples,
            'passed': bool(max(curve_error, upper_error) <= tol and
                           cert['independent_upper']+tol >= cert['upper'])}


def ar_case(config, length, phi, prefix='ar', paths=None):
    count = config['ar_paths_per_case'] if paths is None else paths
    seed = case_seed(config, f'{prefix}-{length}-{phi}')
    rng = np.random.default_rng(seed)
    result = ar_analytic(length, phi)
    gaps = []
    for offset in range(0, count, config['ar_batch_size']):
        n = min(config['ar_batch_size'], count-offset)
        x = rng.normal(size=n)  # stationary initial variance=1
        total, squares = x.copy(), x*x
        for _ in range(1, length):
            x = phi*x+np.sqrt(1-phi**2)*rng.normal(size=n)
            total += x
            squares += x*x
        mean = total/length
        train = .5*(squares/length-mean*mean)
        conditional = .5*((mean-phi*x)**2+1-phi**2)
        gaps.append(conditional-train)
    gaps = np.concatenate(gaps)
    mse = {}
    checks = [abs(result['delta']-result['trace_delta']) <= config['numeric_atol']]
    for name, correction in result['corrections'].items():
        errors = (gaps-correction)**2
        se = float(errors.std(ddof=1)/np.sqrt(count))
        expected = result['conditional_mse'][name]
        z = float((errors.mean()-expected)/se) if se else 0.
        mse[name] = {'observed': float(errors.mean()), 'analytic': expected, 'se': se, 'z': z}
        checks.append(abs(z) <= config['monte_carlo_se_limit'])
    mean_se = float(gaps.std(ddof=1)/np.sqrt(count))
    mean_z = float((gaps.mean()-result['delta'])/mean_se)
    checks.append(abs(mean_z) <= config['monte_carlo_se_limit'])
    return {'kind': 'ar', 'seed': seed, 'independent_histories': count, 'analytic': result,
            'mean_gap': float(gaps.mean()), 'mean_gap_se': mean_se, 'mean_gap_z': mean_z,
            'conditional_mse': mse, 'passed': bool(all(checks)),
            'terminal_recovery_by_constant_correction': False,
            'warning': 'Oracle parameters; quadratic non-tail falsifier, not learned forecast evidence.'}


def preflight(config, fingerprint, out):
    target = out/'preflight.json'
    if target.exists():
        saved = json.loads(target.read_text())
        payload = {k: v for k, v in saved.items() if k != 'sha256'}
        if saved.get('sha256') != digest(payload) or saved['fingerprint'] != fingerprint:
            raise ValueError('preflight integrity/fingerprint mismatch')
        return saved
    start = time.perf_counter()
    mixture = []
    for i in range(4):
        before = time.perf_counter()
        case = mixture_case(config, i*4+3, 'preflight')
        mixture.append({'passed': case['passed'], 'seconds': time.perf_counter()-before})
    before = time.perf_counter()
    ar = ar_case(config, 128, .5, 'preflight', paths=2048)
    ar_seconds = time.perf_counter()-before
    projected = (max(c['seconds'] for c in mixture)*config['mixture_cases'] +
                 ar_seconds*(config['ar_paths_per_case']/2048)*
                 sum(config['ar_lengths'])/128*len(config['ar_phi']))
    witness = rational_witness()
    passed = (all(c['passed'] for c in mixture) and ar['passed'] and
              [r['difference'] for r in witness] == ['-1', '17/2', '-1'] and
              projected <= config['preflight_total_seconds_limit'])
    record = {'utc': utc(), 'fingerprint': fingerprint, 'passed': bool(passed),
              'mixture_microbenchmarks': mixture, 'ar_microbenchmark_seconds': ar_seconds,
              'ar_microbenchmark': ar, 'projected_seconds': projected,
              'actual_seconds': time.perf_counter()-start, 'rational_witness': witness,
              'warnings': ['Known witness is development evidence.',
                           'Local CPU microbenchmark only; no asymptotic speed advantage claimed.']}
    record['sha256'] = digest(record)
    atomic_json(target, record)
    return record


def jobs(config):
    result = [(f'mixture-{i:04d}', ('mixture', i)) for i in range(config['mixture_cases'])]
    result += [(f'ar-{t}-{phi}', ('ar', t, phi)) for t in config['ar_lengths'] for phi in config['ar_phi']]
    return result


def read_checkpoint(path, fingerprint, case_id):
    envelope = json.loads(Path(path).read_text())
    body = envelope['body']
    if digest(body) != envelope['sha256']:
        raise ValueError(f'checkpoint payload hash mismatch: {path}')
    if body['fingerprint'] != fingerprint or body['case_id'] != case_id:
        raise ValueError(f'checkpoint identity mismatch: {path}')
    return body


def validate_expected_case(body, config, args):
    """Bind resume to deterministic inputs, in addition to accidental-corruption hashes."""
    result = body['result']
    if result['kind'] != args[0] or not isinstance(result['passed'], bool):
        raise ValueError('checkpoint result schema mismatch')
    if args[0] == 'mixture':
        expected = mixture_input(config, args[1])
        if digest(result['inputs']) != digest(expected):
            raise ValueError('checkpoint inputs differ from frozen seed recipe')
        a, b = (FiniteMixture(**law) for law in expected['laws'])
        recomputed = paired_certificate(a, b, *expected['interval'])
        if digest(recomputed) != digest(result['certificate']):
            raise ValueError('checkpoint risk certificate differs from input laws')
    else:
        _, length, phi = args
        expected_seed = case_seed(config, f'ar-{length}-{phi}')
        if (result['seed'] != expected_seed or result['independent_histories'] != config['ar_paths_per_case']
                or result['analytic']['length'] != length or result['analytic']['phi'] != phi):
            raise ValueError('checkpoint AR inputs differ from frozen protocol')


def summarize(records, config):
    mixture = [r['result'] for r in records if r['result']['kind'] == 'mixture']
    ars = [r['result'] for r in records if r['result']['kind'] == 'ar']
    expected = len(jobs(config))
    summary = {'cases_done': len(records), 'cases_expected': expected,
               'complete': len(records) == expected,
               'all_checks_passed': all(r['result']['passed'] for r in records),
               'failed_cases': [r['case_id'] for r in records if not r['result']['passed']],
               'mixture_cases': len(mixture), 'ar_cases': len(ars),
               'total_case_seconds': sum(r['elapsed_seconds'] for r in records),
               'warnings': [w for r in records for w in r['warnings']],
               'novelty_established': False,
               'conditional_recovery_by_constant_correction': False}
    if mixture:
        summary['mixture'] = {
            'max_curve_error': max(r['max_curve_error'] for r in mixture),
            'max_upper_error': max(r['upper_error'] for r in mixture),
            'endpoint_underestimates': sum(r['endpoint_underestimate'] > config['numeric_atol'] for r in mixture),
            'endpoint_false_safe': sum(r['endpoint_false_safe'] for r in mixture),
            'max_endpoint_underestimate': max(r['endpoint_underestimate'] for r in mixture),
            'mean_independent_bound_slack': float(np.mean([r['independent_bound_slack'] for r in mixture])),
            'benchmark_by_support': {}}
        for size in config['support_sizes']:
            subset = [r for r in mixture if r['inputs']['size'] == size]
            if subset:
                medians = {k: float(np.median([np.median(r['timing_samples_seconds'][k]) for r in subset]))
                           for k in ('crossings', 'generic_ru_hull')}
                summary['mixture']['benchmark_by_support'][str(size)] = {
                    'n_cases': len(subset), **medians,
                    'hull_over_crossings_ratio': medians['generic_ru_hull']/medians['crossings']}
    summary['ar'] = ars
    return summary


def execute(config, fingerprint, out, max_new_cases=None):
    pre = preflight(config, fingerprint, out)
    if not pre['passed']:
        raise ValueError('preflight failed; full execution NOT RUN')
    case_dir = out/'cases'
    case_dir.mkdir(exist_ok=True)
    todo = jobs(config)
    allowed = {f'{name}.json' for name, _ in todo}
    unknown = {p.name for p in case_dir.glob('*.json')}-allowed
    if unknown:
        raise ValueError(f'unknown checkpoints: {sorted(unknown)}')
    records = []
    done = set()
    for name, args in todo:
        path = case_dir/f'{name}.json'
        if path.exists():
            body = read_checkpoint(path, fingerprint, name)
            validate_expected_case(body, config, args)
            records.append(body)
            done.add(name)
    initial_done = len(done)
    start = time.perf_counter()
    completed_new = 0
    with (out/'progress.jsonl').open('a') as log, tqdm(total=len(todo), initial=initial_done,
                                                    desc='finite research gates', unit='case') as bar:
        log.write(json.dumps({'event': 'resume', 'utc': utc(), 'validated_cases': initial_done})+'\n')
        log.flush()
        for name, args in todo:
            if name in done:
                continue
            if max_new_cases is not None and completed_new >= max_new_cases:
                break
            before = time.perf_counter()
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter('always')
                try:
                    result = mixture_case(config, args[1]) if args[0] == 'mixture' else ar_case(config, *args[1:])
                except Exception as exc:
                    log.write(json.dumps({'event': 'error', 'utc': utc(), 'case_id': name,
                                          'error': repr(exc), 'elapsed_seconds': time.perf_counter()-before})+'\n')
                    log.flush()
                    raise
            body = {'case_id': name, 'fingerprint': fingerprint, 'result': result, 'utc': utc(),
                    'elapsed_seconds': time.perf_counter()-before,
                    'warnings': [str(w.message) for w in caught]}
            atomic_json(case_dir/f'{name}.json', {'sha256': digest(body), 'body': body})
            records.append(body)
            completed_new += 1
            elapsed = time.perf_counter()-start
            remaining = len(todo)-initial_done-completed_new
            log.write(json.dumps({'event': 'case_done', 'utc': utc(), 'case_id': name,
                                  'done': len(records), 'remaining': remaining,
                                  'elapsed_seconds': elapsed, 'eta_seconds': elapsed/completed_new*remaining,
                                  'passed': result['passed']})+'\n')
            log.flush()
            bar.update(1)
    summary = summarize(sorted(records, key=lambda r: r['case_id']), config)
    atomic_json(out/'summary.json', summary)
    invocation = {'utc': utc(), 'fingerprint': fingerprint, 'resumed_cases': initial_done,
                  'new_cases': completed_new, 'wall_seconds': time.perf_counter()-start,
                  'complete': summary['complete'], 'all_checks_passed': summary['all_checks_passed']}
    with (out/'invocations.jsonl').open('a') as stream:
        stream.write(json.dumps(invocation)+'\n')
    print(json.dumps(invocation, indent=2))
    return summary


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('stage', choices=['preflight', 'run'])
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--max-new-cases', type=int)
    args = parser.parse_args()
    if args.max_new_cases is not None and args.max_new_cases < 0:
        parser.error('--max-new-cases must be nonnegative')
    args.out.mkdir(parents=True, exist_ok=True)
    with (args.out/'.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        config, fingerprint = freeze(args.out)
        if args.stage == 'preflight':
            result = preflight(config, fingerprint, args.out)
            print(json.dumps(result, indent=2))
        else:
            result = execute(config, fingerprint, args.out, args.max_new_cases)
        if not result.get('passed', result.get('all_checks_passed', False)):
            raise SystemExit(1)
        if args.stage == 'run' and not result['complete']:
            raise SystemExit(3)  # intentional partial run; must not be mistaken for completion


if __name__ == '__main__':
    main()
