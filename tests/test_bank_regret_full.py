import copy
import gzip
import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

from bank_regret.study import public_design
from bank_regret_full.analysis import interval, summarize
from bank_regret_full.run import (BASE, configuration, freeze, memory_child, perform,
                                 read_case, save_case, tasks)
from bank_regret_full.verify import check_input
from mixture_order.run import digest

CFG = json.loads((Path(__file__).parents[1]/'bank_regret_full/config.json').read_text())
CFG['seed_namespace'] += '/unit-tests'


def test_full_factorial_counts_and_interval_alpha_balance():
    matrix = tasks(CFG)
    assert {k: len(v) for k, v in matrix.items()} == {'benchmark': 240, 'memory': 30, 'policy': 3072}
    assert len({t['id'] for ts in matrix.values() for t in ts}) == 3342
    for alpha in CFG['benchmark_alphas']:
        selected = [t for t in matrix['benchmark'] if t['alpha'] == alpha]
        assert sum(t['replicate'] % 2 == 0 for t in selected) == 30
        for task in selected:
            assert configuration(CFG, task)['benchmark_alphas'] == [alpha]


def test_independent_designs_disjoint_from_pilot_without_model_changes():
    a = configuration(CFG, {'kind': 'policy', 'bank': 0})
    b = configuration(CFG, {'kind': 'policy', 'bank': 1})
    assert a['seed_namespace'] != b['seed_namespace'] != BASE['seed_namespace']
    assert {k: v for k, v in a.items() if k != 'seed_namespace'} == {k: v for k, v in BASE.items() if k != 'seed_namespace'}
    assert not np.array_equal(public_design(a)['loss_matrix'], public_design(b)['loss_matrix'])


def test_gzip_checkpoint_identity_and_rehashed_wrong_decision_rejected(tmp_path):
    task = {'id': 't', 'kind': 'policy'}
    r = {'decision': {'selected': 1}, 'decision_lock_sha256': digest({'selected': 1}), 'kind': 'policy'}
    body = {'fingerprint': 'frozen', 'task': task, 'result': r}
    path = tmp_path/'case.json.gz'
    save_case(path, body)
    original = path.read_bytes()
    assert read_case(path, 'frozen', task) == body
    save_case(path, body)
    assert path.read_bytes() == original
    with pytest.raises(ValueError):
        read_case(path, 'wrong', task)
    body['result']['decision']['selected'] = 2
    save_case(path, body)
    with pytest.raises(ValueError, match='decision lock'):
        read_case(path, 'frozen', task)


def test_freeze_rejects_changed_config_and_layout(tmp_path):
    cfg = dict(CFG, banks=1, histories_per_bank_family=1)
    fp = freeze(tmp_path, cfg)
    assert freeze(tmp_path, cfg) == fp
    with pytest.raises(ValueError):
        freeze(tmp_path, dict(cfg, banks=2))
    (tmp_path/'layout.json').write_text('{}')
    with pytest.raises(ValueError, match='layout'):
        freeze(tmp_path, cfg)


def test_cluster_interval_uses_banks_and_degenerate_interaction_is_exact():
    result = interval([-1., 0., 1.], CFG, 'test')
    assert result['independent_banks'] == 3 and result['mean'] == 0
    zero = interval([0.]*24, CFG, 'zero')
    assert zero['ci95'] == [0., 0.] and zero['ci97_5'] == [0., 0.]


def test_incomplete_policy_stage_does_not_publish_inferential_intervals():
    records = [{'task': {'id': 'a'}, 'elapsed_seconds': .1, 'captured_warnings': [],
                'result': {'kind': 'policy', 'passed': True, 'family': 'stationary', 'bank': 0,
                           'union_verification': {'max_error': 0, 'choice_agrees': True}}}]
    result = summarize(records, CFG, 3342)
    assert result['policy']['stationary'] == {'histories': 1, 'complete': False, 'bank_counts': {0: 1}}


def test_real_development_policy_replay_and_truth_tamper():
    task = {'id': 'fixture', 'kind': 'policy', 'bank': 0, 'family': 'stationary', 'index': 0}
    record = perform(CFG, task, 'fixture')
    assert record['result']['passed']
    assert check_input(CFG, record)['deep']
    broken = copy.deepcopy(record)
    broken['result']['truth_q_evaluator_only'] += .01
    with pytest.raises(AssertionError):
        check_input(CFG, broken)


def test_memory_and_benchmark_same_input_and_exact_result():
    task = {'id': 'small', 'kind': 'benchmark', 'm': 8, 'n': 16, 'alpha': .2, 'replicate': 0}
    bench = perform(CFG, task, 'test')['result']
    memory = memory_child(CFG, dict(task, kind='memory', solver='local'))
    assert memory['input_sha256'] == bench['input_sha256']
    assert memory['regrets_sha256'] == digest(bench['local']['regrets'])
    assert memory['peak_rss_bytes'] >= memory['pre_input_peak_bytes'] > 0


def test_real_cli_partial_full_noop_resume(tmp_path):
    cfg = dict(CFG, banks=1, histories_per_bank_family=1, benchmark_banks=[8],
               benchmark_supports=[16], benchmark_alphas=[.2],
               benchmark_replicates_per_alpha=1, timing_repetitions=1,
               policy_workers=2, bootstrap_repetitions=20)
    config = tmp_path/'config.json'
    config.write_text(json.dumps(cfg))
    out = tmp_path/'output'
    env = dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', VECLIB_MAXIMUM_THREADS='1')
    command = [sys.executable, '-m', 'bank_regret_full.run', 'run', '--config', str(config), '--out', str(out)]
    first = subprocess.run(command+['--max-new-cases', '1'], capture_output=True, text=True, env=env)
    assert first.returncode == 3, first.stderr
    original = {p.name: p.read_bytes() for p in (out/'cases').glob('*.json.gz')}
    second = subprocess.run(command, capture_output=True, text=True, env=env)
    assert second.returncode == 0, second.stderr
    assert len(list((out/'cases').glob('*.json.gz'))) == 5
    assert all((out/'cases'/p).read_bytes() == data for p, data in original.items())
    complete = {p.name: p.read_bytes() for p in (out/'cases').glob('*.json.gz')}
    third = subprocess.run(command, capture_output=True, text=True, env=env)
    assert third.returncode == 0, third.stderr
    assert all((out/'cases'/p).read_bytes() == data for p, data in complete.items())
    invocations = [json.loads(s) for s in (out/'invocations.jsonl').read_text().splitlines()]
    assert [(r['resumed'], r['new_cases']) for r in invocations] == [(0, 1), (1, 4), (5, 0)]
