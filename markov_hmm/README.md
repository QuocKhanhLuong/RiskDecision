# Learned HMM control, Q2 extension

This is the standard two-state Gaussian HMM control requested after the first
temporal pilot. See [prospective protocol](PROTOCOL.md). It fits full emission
covariances and transitions from the permitted past512 window; it receives no
world label, latent state, true parameters or future observations. The selected
restart maximizes past training likelihood, not evaluation accuracy.

The primary is stationary Markov, full512 locked portfolio, HMM minus Gaussian
iid conditional squared relative objective error. EWMA, AR, raw, iid OIC,
same-fit stationary-mixture and fixed-weight controls are reported separately.
All inference averages origins within each of 32 paths before resampling paths.
The model family matches the stationary DGP; improvement here is not novelty,
market profitability, universal dominance or a calibrated VaR/ES result.

## Reproduction

Use the existing project NumPy/SciPy/sklearn environment plus pinned hmmlearn:

```bash
rtk proxy uv pip install --python .venv/bin/python -r markov_hmm/requirements.txt
rtk proxy .venv/bin/python -m pytest -q tests quant_research_v2/tests
rtk proxy .venv/bin/python -m markov_hmm.run preflight --out runs/markov_hmm/20261008_q2_hmm
rtk proxy .venv/bin/python -m markov_hmm.run development --out runs/markov_hmm/20261008_q2_hmm
rtk proxy .venv/bin/python -m markov_hmm.run pilot --out runs/markov_hmm/20261008_q2_hmm --max-new-cases 5
rtk proxy .venv/bin/python -m markov_hmm.run pilot --out runs/markov_hmm/20261008_q2_hmm
rtk proxy .venv/bin/python scripts/verify_markov_hmm.py --out runs/markov_hmm/20261008_q2_hmm
```

These seeds become seen when the recorded pilot is opened. Reproduction is not
fresh confirmation; a new study requires a new protocol/config/run/seed audit.
Development is a numerical/compute gate, not a forecast-error tuning stage.
The runner refuses pilot execution if the gate fails. It has no automatic
hyperparameter search, fallback substitution or retry of failed cases.

## Resume and receipts

Progress JSONL and terminal tqdm contain ETA and actual timings. Per-origin
checkpoints are atomic and hash both payload and referenced synthetic arrays.
Resume requires identical source, config, package binary/source hashes,
environment and frozen inputs. A different platform/package version is a new
execution environment, not a byte-identical resume. Current git commit is
recorded as provenance but is not used to invalidate a documentation-only commit.

The selected fit's explicit likelihood convergence is recorded separately from
the library monitor's iteration-cap status. All three starts keep histories,
parameters, warnings, occupancies and scores. Finite capped selected fits remain
flagged; invalid estimates stay null and make affected contrasts incomplete.

Published compressed exports preserve original hashes and are lossless. The
checkpoint payload archive contains synthetic paths and full case checkpoints;
its manifest identifies every member. Restore into a fresh location or check
existing file hashes before extraction. Never overwrite differing local files.
The verifier uses saved parameters/paths, independent probability filtering,
direct scalar quadrature and path-cluster interval recomputation; no model
refitting or independent peer-review claim is involved.
