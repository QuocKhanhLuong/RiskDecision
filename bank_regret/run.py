"""Prospective compositional audit, bounded compute and verified resume."""
import argparse
import fcntl
import hashlib
import json
import os
import platform
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import scipy
from tqdm import tqdm

from mixture_order.core import FiniteMixture
from mixture_order.run import atomic_json, digest, utc
from .core import make_bank, solve_local, solve_union, solve_worlds
from .study import (arrays_hash, choose_policies, evaluate, fit_observed,
                    generate_history, observed_posterior_seed, public_design, seed)

ROOT = Path(__file__).resolve().parents[1]
MODULE = Path(__file__).resolve().parent


def freeze(out):
    cfg = json.loads((MODULE/'config.json').read_text())
    sources = sorted(MODULE.glob('*.py'))+[MODULE/'config.json', MODULE/'PROTOCOL.md',
                                         ROOT/'mixture_order/core.py', ROOT/'mixture_order/run.py',
                                         ROOT/'mixture_order/__init__.py']
    contract = {'files': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
                'python': sys.version, 'numpy': np.__version__, 'scipy': scipy.__version__,
                'platform': platform.platform(),
                'python_binary': hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest(),
                'thread_environment': {k: os.environ.get(k) for k in
                                       ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS']}}
    fingerprint = digest(contract)
    file = out/'freeze.json'
    if file.exists():
        prior = json.loads(file.read_text())
        if prior['fingerprint'] != fingerprint or digest(prior['contract']) != fingerprint or prior['config'] != cfg:
            raise ValueError('changed source/config/environment; create a fresh run directory')
    else:
        atomic_json(file, {'utc': utc(), 'contract': contract, 'fingerprint': fingerprint, 'config': cfg})
    return cfg, fingerprint


def benchmark_input(cfg, m, n, rep, development=False):
    name = f"{'development' if development else 'benchmark'}-{m}-{n}-{rep}"
    case_seed = seed(cfg, name)
    rng = np.random.default_rng(case_seed)
    x = rng.standard_t(5, (m, n))
    p0, p1 = rng.dirichlet(np.full(n, .3), size=(2, m))
    costs = rng.uniform(0, .1, m)
    interval = [0., 1.] if rep % 2 == 0 else sorted(rng.uniform(0, 1, 2).tolist())
    alpha = cfg['benchmark_alphas'][rep % len(cfg['benchmark_alphas'])]
    return {'seed': case_seed, 'x': x, 'p0': p0, 'p1': p1, 'costs': costs,
            'interval': interval, 'alpha': alpha,
            'sha256': arrays_hash(x, p0, p1, costs, np.array(interval), np.array([alpha]))}


def run_benchmark(cfg, m, n, rep, development=False):
    inp = benchmark_input(cfg, m, n, rep, development)
    start = time.perf_counter()
    laws = [FiniteMixture(x, p0, p1, inp['alpha']) for x, p0, p1 in zip(inp['x'], inp['p0'], inp['p1'])]
    preprocessing = time.perf_counter()-start
    timings = {'local': [], 'union': []}
    answers = {}
    for repeat in range(cfg['timing_repetitions']):
        methods = [('local', solve_local), ('union', solve_union)]
        if repeat % 2:
            methods.reverse()
        for label, fn in methods:
            start = time.perf_counter()
            answers[label] = fn(laws, inp['costs'], inp['interval'])
            timings[label].append(time.perf_counter()-start)
    local, union = answers['local'], answers['union']
    error = float(np.max(np.abs(np.array(local['regrets'])-union['regrets'])))
    witness_error = 0.
    for i, (q, j, claimed) in enumerate(zip(local['worst_q'], local['competitor'], local['regrets'])):
        observed = laws[i].es(q)+inp['costs'][i]-laws[j].es(q)-inp['costs'][j]
        witness_error = max(witness_error, abs(observed-claimed))
    ordered = np.sort(local['regrets'])
    margin = float(ordered[1]-ordered[0]) if len(ordered) > 1 else None
    return {'kind': 'benchmark', 'm': m, 'n': n, 'replicate': rep, 'alpha': inp['alpha'],
            'seed': inp['seed'], 'input_sha256': inp['sha256'], 'interval': inp['interval'],
            'local': local, 'union': union, 'max_regret_error': error, 'max_witness_error': float(witness_error),
            'choice_agrees': local['selected'] == union['selected'], 'choice_margin': margin,
            'preprocessing_seconds': preprocessing, 'timing_seconds': timings,
            'passed': bool(error <= cfg['numeric_atol'] and witness_error <= cfg['numeric_atol'] and
                           (local['selected'] == union['selected'] or margin <= cfg['numeric_atol']))}


def run_policy(cfg, family, index, development=False):
    design = public_design(cfg)
    generated = generate_history(cfg, design, family, index, development)
    posterior_seed = observed_posterior_seed(cfg, generated['z'], generated['categories'], design)
    fit = fit_observed(cfg, generated['z'], generated['categories'], posterior_seed)
    decision = choose_policies(cfg, design, fit, generated['categories'])
    locked_hash = digest(decision)
    # Only after all choices are locked does evaluation receive the true law.
    evaluation = evaluate(cfg, design, decision, generated['truth'])
    assert digest(decision) == locked_hash
    # Structural factorial order under the *same supplied stress set*.
    surfaces = decision['regret_surfaces']
    tol = cfg['numeric_atol']
    passed = (np.all(np.array(surfaces['shared_full'])+tol >= surfaces['shared_endpoints']) and
              np.all(np.array(surfaces['rectangular_full'])+tol >= surfaces['shared_full']))
    return {'kind': 'policy', 'family': family, 'index': index, 'seed': generated['seed'],
            'input_sha256': arrays_hash(generated['z'], generated['categories'], design['loss_matrix'], design['weights']),
            'history': {'context': generated['z'].tolist(), 'category': generated['categories'].tolist()},
            'fit': fit, 'decision': decision, 'decision_lock_sha256': locked_hash,
            'evaluation': evaluation, 'truth_q_evaluator_only': float(generated['truth']['q']),
            'truth_components_evaluator_only': generated['truth']['components'].tolist(),
            'passed': bool(passed),
            'warnings': ['Finite posterior worlds do not provide true-law coverage.']}


def jobs(cfg):
    cases = [(f'benchmark-{m}-{n}-{r}', ('benchmark', m, n, r)) for m in cfg['benchmark_banks']
             for n in cfg['benchmark_supports'] for r in range(cfg['benchmark_replicates'])]
    cases += [(f'policy-{f}-{i:03d}', ('policy', f, i)) for f in cfg['policy_families']
              for i in range(cfg['policy_histories_per_family'])]
    order = np.random.default_rng(seed(cfg, 'processing-order')).permutation(len(cases))
    return [cases[i] for i in order]


def preflight(cfg, fingerprint, out):
    path = out/'preflight.json'
    if path.exists():
        data = json.loads(path.read_text())
        if data['sha256'] != digest({k: v for k, v in data.items() if k != 'sha256'}) or data['fingerprint'] != fingerprint:
            raise ValueError('preflight integrity mismatch')
        return data
    # Largest cell, alpha=.2: a compute gate, not selection on policy accuracy.
    start = time.perf_counter()
    benchmark = run_benchmark(cfg, max(cfg['benchmark_banks']), max(cfg['benchmark_supports']), 2, True)
    bs = time.perf_counter()-start
    start = time.perf_counter()
    policy = run_policy(cfg, 'stationary', 0, True)
    ps = time.perf_counter()-start
    design = public_design(cfg)
    worlds = [make_bank(design['loss_matrix'], p, cfg['policy_alpha']) for p in policy['fit']['worlds']]
    reference = solve_worlds(worlds, policy['decision']['costs'],
                             [policy['fit']['interval']]*len(worlds), solver=solve_union)
    policy_error = float(np.max(np.abs(np.array(reference['regrets'])-
                                       policy['decision']['shared_certificate']['regrets'])))
    tasks = jobs(cfg)
    projection = bs*sum(a[0] == 'benchmark' for _, a in tasks)+ps*sum(a[0] == 'policy' for _, a in tasks)
    data = {'utc': utc(), 'fingerprint': fingerprint, 'benchmark_seconds': bs, 'policy_seconds': ps,
            'projected_seconds': projection,
            'passed': bool(benchmark['passed'] and policy['passed'] and policy_error <= cfg['numeric_atol']
                           and projection <= cfg['preflight_seconds_limit']),
            'benchmark_numerical_error': benchmark['max_regret_error'],
            'development_policy_local_union_error': policy_error,
            'development_policy_outcomes_not_used_for_tuning': True}
    data['sha256'] = digest(data)
    atomic_json(path, data)
    return data


def paired_interval(values, cfg, label):
    values = np.asarray(values, float)
    rng = np.random.default_rng(seed(cfg, f'bootstrap-{label}'))
    sample = rng.integers(0, len(values), (cfg['bootstrap_repetitions'], len(values)))
    draws = values[sample].mean(axis=1)
    return {'mean': float(values.mean()), 'ci95': np.quantile(draws, [.025, .975]).tolist(),
            'independent_histories': len(values), 'exploratory_pilot': True}


def summarize(records, cfg):
    benchmarks = [r['result'] for r in records if r['result']['kind'] == 'benchmark']
    policies = [r['result'] for r in records if r['result']['kind'] == 'policy']
    result = {'cases_done': len(records), 'cases_expected': len(jobs(cfg)), 'complete': len(records) == len(jobs(cfg)),
              'all_checks_passed': all(r['result']['passed'] for r in records),
              'failed_cases': [r['case_id'] for r in records if not r['result']['passed']],
              'case_seconds': sum(r['elapsed_seconds'] for r in records),
              'numerical_warnings': [w for r in records for w in r['captured_warnings']],
              'novelty_priority_established': False, 'true_law_coverage_guarantee': False,
              'benchmarks': {}, 'policy': {}}
    if benchmarks:
        result['max_regret_error'] = max(r['max_regret_error'] for r in benchmarks)
        result['max_witness_error'] = max(r['max_witness_error'] for r in benchmarks)
        result['selected_index_disagreements'] = sum(not r['choice_agrees'] for r in benchmarks)
    for m in cfg['benchmark_banks']:
        for n in cfg['benchmark_supports']:
            cell = [r for r in benchmarks if r['m'] == m and r['n'] == n]
            if not cell:
                continue
            local = float(np.median([np.median(r['timing_seconds']['local']) for r in cell]))
            union = float(np.median([np.median(r['timing_seconds']['union']) for r in cell]))
            result['benchmarks'][f'{m}x{n}'] = {
                'cases': len(cell), 'local_seconds': local, 'union_seconds': union,
                'union_over_local': union/local,
                'local_risk_evaluations': [r['local']['risk_evaluations'] for r in cell],
                'union_risk_evaluations': [r['union']['risk_evaluations'] for r in cell]}
    for family in cfg['policy_families']:
        cell = [r for r in policies if r['family'] == family]
        if not cell:
            continue
        names = list(cell[0]['evaluation']['policies'])
        metrics = {}
        for name in names:
            entries = [r['evaluation']['policies'][name] for r in cell]
            metrics[name] = {'mean_true_net_regret': float(np.mean([x['true_net_regret'] for x in entries])),
                             'switches': sum(x['switched'] for x in entries),
                             'harmful_switches': sum(x['harmful_switch'] for x in entries),
                             'mean_cost': float(np.mean([x['cost'] for x in entries]))}
        values = lambda name: np.array([r['evaluation']['policies'][name]['true_net_regret'] for r in cell])
        interaction = values('shared_full')-values('shared_endpoints')-values('rectangular_full')+values('rectangular_endpoints')
        result['policy'][family] = {'histories': len(cell), 'metrics': metrics,
            'shared_minus_rectangular': paired_interval(values('shared_full')-values('rectangular_full'), cfg, family+'-primary'),
            'shared_minus_point': paired_interval(values('shared_full')-values('point'), cfg, family+'-point'),
            'factorial_interaction': paired_interval(interaction, cfg, family+'-interaction'),
            'stress_bound_underestimates': sum(r['evaluation']['stress_bound_underestimates_true_regret'] for r in cell),
            'nominal_common_bank_forecast_mse': float(np.mean([r['evaluation']['same_target_forecast_mse'] for r in cell])),
            'historical_common_bank_forecast_mse': float(np.mean([r['evaluation']['historical_same_target_forecast_mse'] for r in cell]))}
    return result


def read_case(path, fingerprint, case_id, cfg, args):
    saved = json.loads(path.read_text())
    body = saved['body']
    if saved['sha256'] != digest(body) or body['fingerprint'] != fingerprint or body['case_id'] != case_id:
        raise ValueError('checkpoint payload/identity mismatch')
    record = body['result']
    if record['kind'] != args[0]:
        raise ValueError('case kind mismatch')
    if args[0] == 'benchmark':
        inp = benchmark_input(cfg, *args[1:])
        expected = inp['sha256']
    else:
        design = public_design(cfg)
        generated = generate_history(cfg, design, *args[1:])
        expected = arrays_hash(generated['z'], generated['categories'], design['loss_matrix'], design['weights'])
        if digest(record['decision']) != record['decision_lock_sha256']:
            raise ValueError('decision lock mismatch')
        posterior_seed = observed_posterior_seed(cfg, generated['z'], generated['categories'], design)
        fit = fit_observed(cfg, generated['z'], generated['categories'], posterior_seed)
        if digest(fit) != digest(record['fit']):
            raise ValueError('fitted worlds differ from observed-input recipe')
        decision = choose_policies(cfg, design, fit, generated['categories'])
        if digest(decision) != record['decision_lock_sha256']:
            raise ValueError('decisions differ from observed-input recipe')
    if record['input_sha256'] != expected:
        raise ValueError('checkpoint does not match frozen input recipe')
    return body


def execute(cfg, fingerprint, out, max_new=None):
    if not preflight(cfg, fingerprint, out)['passed']:
        raise ValueError('preflight failed; full execution NOT RUN')
    folder = out/'cases'
    folder.mkdir(exist_ok=True)
    tasks = jobs(cfg)
    expected = {name+'.json' for name, _ in tasks}
    if {p.name for p in folder.glob('*.json')}-expected:
        raise ValueError('unknown checkpoints in run directory')
    records, completed = [], set()
    for name, args in tasks:
        p = folder/(name+'.json')
        if p.exists():
            records.append(read_case(p, fingerprint, name, cfg, args))
            completed.add(name)
    initial = len(records)
    new = 0
    start = time.perf_counter()
    with (out/'progress.jsonl').open('a') as log, tqdm(total=len(tasks), initial=initial,
                                                    desc='compositional research', unit='case') as bar:
        log.write(json.dumps({'event': 'resume', 'utc': utc(), 'validated': initial})+'\n')
        log.flush()
        for name, args in tasks:
            if name in completed:
                continue
            if max_new is not None and new >= max_new:
                break
            before = time.perf_counter()
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter('always')
                try:
                    result = run_benchmark(cfg, *args[1:]) if args[0] == 'benchmark' else run_policy(cfg, *args[1:])
                except Exception as exc:
                    log.write(json.dumps({'event': 'error', 'utc': utc(), 'case_id': name, 'error': repr(exc)})+'\n')
                    log.flush()
                    raise
            body = {'case_id': name, 'fingerprint': fingerprint, 'utc': utc(), 'result': result,
                    'elapsed_seconds': time.perf_counter()-before,
                    'captured_warnings': [str(w.message) for w in caught]}
            atomic_json(folder/(name+'.json'), {'body': body, 'sha256': digest(body)})
            records.append(body)
            new += 1
            remaining = len(tasks)-len(records)
            elapsed = time.perf_counter()-start
            log.write(json.dumps({'event': 'complete_case', 'utc': utc(), 'case_id': name,
                                  'done': len(records), 'remaining': remaining, 'elapsed_seconds': elapsed,
                                  'eta_seconds': elapsed/new*remaining, 'passed': result['passed']})+'\n')
            log.flush()
            bar.update(1)
    summary = summarize(sorted(records, key=lambda r: r['case_id']), cfg)
    atomic_json(out/'summary.json', summary)
    invocation = {'utc': utc(), 'resumed': initial, 'new_cases': new, 'complete': summary['complete'],
                  'all_checks_passed': summary['all_checks_passed'], 'wall_seconds': time.perf_counter()-start}
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
        parser.error('max-new-cases must be nonnegative')
    args.out.mkdir(parents=True, exist_ok=True)
    with (args.out/'.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        cfg, fingerprint = freeze(args.out)
        result = preflight(cfg, fingerprint, args.out) if args.stage == 'preflight' else execute(cfg, fingerprint, args.out, args.max_new_cases)
        if args.stage == 'preflight':
            print(json.dumps(result, indent=2))
        if not result.get('passed', result.get('all_checks_passed', False)):
            raise SystemExit(1)
        if args.stage == 'run' and not result['complete']:
            raise SystemExit(3)


if __name__ == '__main__':
    main()
