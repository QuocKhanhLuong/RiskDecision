# Continuous CVaR / OIC benchmark

This is the separate continuous-optimization part of Q1. It does not change
bank285, historical APTC, or their results. See the
[consolidated report](../docs/experiments/20261007_continuous_cvar_oic.md) and
[pre-implementation applicability audit](OIC_APPLICABILITY.md).

The measured runner completed 128 cases, but the registered overall primary
comparison is **INCOMPLETE**: four full512 fits at primary tau fail the OIC
active-set gate. Invalid corrections remain null. Gaussian bias reduction is
secondary evidence, not proof of MSE superiority.

## Implemented contract

- `model.py`: past-only smooth empirical CVaR optimization, KKT-derived influence
  correction, diagnostics, and unsmoothed empirical CVaR LP reference.
- `evaluation.py`: analytic Gaussian-mixture hinge risk, localized smoothing
  quadrature, true ES, and continuous population-optimal ES reference.
- `run.py`: fixed protocol, seed audit, source/config freeze, atomic checkpoints,
  artifact hashes, file lock, tqdm, ETA, warning retention and resume.
- `../scripts/verify_continuous_cvar.py`: independent augmented KKT solve and
  direct quadrature audit; checks retained failures and unchanged previous fits.

Every continuous method uses `sum(w)=1`, `0<=w<=.5`, `-50<=v<=50`.
`raw` and `oic_kkt` evaluate the same locked decision; half-sample `independent`
evaluates it on the other 256 observations. Full512 and half256 policies have
different fitting budgets. The estimate is expected fixed **smoothed objective**
at `(w,v)`, not an adjusted coherent VaR/ES pair. Exact LP gets no OIC label.
Population parameters enter only after all data-based fitting and corrections.

## Run and resume

Use the project's virtual environment with NumPy, SciPy, pytest and tqdm.
Measured environment is in the run's `source_receipt.json`. The fixed config
records 64 seed clusters, two iid families, primary tau=.1 and sensitivity .05/.2.
The 128 instances are synthetic; the two families sharing a seed are clustered
together in 10,000 bootstrap replicates. Development is excluded from inference.

On a checkout with no previous observed uses of the registered seeds:

```bash
rtk proxy .venv/bin/python -m pytest -q
rtk proxy .venv/bin/python -m continuous_cvar.run preflight --out runs/continuous_cvar/reproduction
rtk proxy .venv/bin/python -m continuous_cvar.run development --out runs/continuous_cvar/reproduction
rtk proxy .venv/bin/python -m continuous_cvar.run pilot --out runs/continuous_cvar/reproduction --max-new-cases 3
rtk proxy .venv/bin/python -m continuous_cvar.run pilot --out runs/continuous_cvar/reproduction
```

The pilot refuses a failed development gate or predicted cost over 600 seconds.
The estimate includes a factor-two margin. Repeating `pilot` resumes a partial
run and checks frozen source/config and case/array hashes. A completed resume
reuses all cases. An interrupted unsaved case can be recomputed; a saved FAILED
case stays failed rather than being silently replaced.

These published seeds are now **seen**. Reproduction is not fresh confirmation,
even on a clean machine. Locally the audit rejects previously observed seeds
unless an explicit, matching replay is declared. The final measured run used:

```bash
rtk proxy .venv/bin/python -m continuous_cvar.run preflight --out runs/continuous_cvar/20261007_oic_v3 --replay-from runs/continuous_cvar/20261007_oic_v2
rtk proxy .venv/bin/python -m continuous_cvar.run development --out runs/continuous_cvar/20261007_oic_v3
rtk proxy .venv/bin/python -m continuous_cvar.run pilot --out runs/continuous_cvar/20261007_oic_v3 --max-new-cases 3
rtk proxy .venv/bin/python -m continuous_cvar.run pilot --out runs/continuous_cvar/20261007_oic_v3
rtk proxy .venv/bin/python scripts/verify_continuous_cvar.py --out runs/continuous_cvar/20261007_oic_v3 --previous runs/continuous_cvar/20261007_oic_v2
```

This explicit replay is restricted to unchanged config/fitter/generator after
the documented population-evaluator repair. It does not add independent cases.
Do not change this measured config to obtain a favorable primary result.

## Evidence and limits

Published compact evidence includes CSVs, full final diagnostics, freeze,
preflight hashes, progress and terminal logs, tests, verifier and resume receipts,
plus earlier failure receipts. `publication_manifest.json` lists exact files.
Full NPZ/checkpoint payloads and downloaded paper HTML remain local. A compact
Git checkout alone cannot resume the measured run or rerun the NPZ verifier;
it can inspect all estimates/diagnostics, or regenerate a separately labelled
software replay. The local complete tree can resume directly.

No active-set degeneracy remedy was fitted to these outcomes. No unsmoothed OIC,
temporal benchmark, market evaluation, utility experiment or neural model was
run in this continuation. Numerical tests do not establish the paper's
asymptotic assumptions or scientific superiority.
