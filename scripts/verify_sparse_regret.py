"""Post-run independent receipts/witness audit; never edits measured checkpoints."""
import gzip
import hashlib
import json
from fractions import Fraction as F
from pathlib import Path
import sys

import numpy as np
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mixture_order.run import atomic_json, digest
from sparse_regret.core import witness_error
from sparse_regret.rational import exact_risks
from sparse_regret.run import as_bank, make_input, read_case, summarize, tasks


def main():
    root = Path(__file__).resolve().parents[1]
    out = root/'runs/sparse_regret_audit/20261008'
    frozen = out/'frozen'
    freeze = json.loads((frozen/'freeze.json').read_text())
    cfg, fp = freeze['contract']['config'], freeze['fingerprint']
    assert digest(freeze['contract']) == fp
    for name, sha in freeze['contract']['files'].items():
        assert hashlib.sha256((root/name).read_bytes()).hexdigest() == sha, name
    rows, max_error, exact_witnesses = [], 0., 0
    for task in tqdm(tasks(cfg), desc='independent saved-witness audit', unit='case'):
        row = read_case(frozen/'cases'/(task['id']+'.json.gz'), fp, task)
        assert row['input'] == make_input(cfg, task)
        bank = as_bank(row['input'])
        for name, result in row['results'].items():
            if name == 'rational':
                inp = row['input']
                p = [list(map(F, line)) for line in inp['p']]
                for i, rawq in enumerate(result['worst_q']):
                    q = list(map(F, rawq))
                    assert all(v >= 0 for v in q) and sum(q) == 1
                    risks = exact_risks(inp['x'], p, F(inp['alpha']), list(map(F, inp['costs'])), q)
                    assert risks[i]-min(risks) == F(result['regrets'][i])
                    exact_witnesses += 1
            else:
                error = witness_error(bank, result)
                max_error = max(max_error, error)
                assert error <= cfg['numeric_atol']
                for q in result['worst_q']:
                    assert min(q) >= -1e-10 and abs(sum(q)-1) < 1e-9
                if name in ('local', 'union'):
                    assert max(sum(v > 1e-12 for v in q) for q in result['worst_q']) <= (1 if task['alpha'] == 1 else 2)
                assert result['selected'] == int(np.argmin(result['regrets']))
        rows.append(row)
    assert summarize(rows, len(tasks(cfg))) == json.loads((frozen/'summary.json').read_text())
    prior = json.loads((out/'start_receipt.json').read_text())
    # Locate the pre-existing tracked-file hash mapping by its actual shape.
    mappings = [v for v in prior.values() if isinstance(v, dict) and len(v) > 100]
    assert len(mappings) == 1
    oldfiles = mappings[0]
    for name, sha in oldfiles.items():
        assert hashlib.sha256((root/name).read_bytes()).hexdigest() == sha, name
    partial = json.loads((out/'partial_checkpoint_hashes.json').read_text())
    for name, sha in partial.items():
        assert hashlib.sha256((out/name).read_bytes()).hexdigest() == sha
    summary = dict(passed=True, source_fingerprint=fp, cases=len(rows), exact_rational_witnesses=exact_witnesses,
                   max_saved_witness_error=max_error, preserved_prior_files=len(oldfiles),
                   preserved_partial_checkpoints=len(partial), all_input_recipes_verified=True,
                   scope='Saved inputs, full regret vectors, rational and floating witnesses; no retiming or new model selection.')
    atomic_json(out/'verification.json', summary)
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
