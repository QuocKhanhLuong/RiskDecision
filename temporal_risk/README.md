# Q2 temporal risk baseline pilot

This module implements the [frozen protocol](PROTOCOL.md) after Q1. Historical
modules and measured artifacts are unchanged. `dgp.py` is simulation/evaluation
only; `models.py` takes observed past, fitting settings and resampling RNG only.
It receives no world name, transition matrix, change time, latent state or future.

The primary target is expected **next-step smoothed objective** at the same
locked full512 decision, stationary AR(1), past-fitted AR Gaussian minus iid OIC
squared relative error. It is not a calibrated VaR/ES pair or economic utility.
Marginal error, conditional mismatch, fixed-portfolio control, purged holdout,
HAC and circular-block optimism are reported separately. A stationary Markov
control is coupled with a structural transition-shift world. Its observed-history
parameter oracle and hidden-state diagnostic have distinct information labels.

## Run sequence

Use the project's Python environment with NumPy, SciPy, pytest and tqdm:

```bash
rtk proxy .venv/bin/python -m pytest -q tests quant_research_v2/tests
rtk proxy .venv/bin/python -m temporal_risk.run preflight --out runs/temporal_risk/20261008_q2
rtk proxy .venv/bin/python -m temporal_risk.run development --out runs/temporal_risk/20261008_q2
rtk proxy .venv/bin/python -m temporal_risk.run pilot --out runs/temporal_risk/20261008_q2 --max-new-cases 5
rtk proxy .venv/bin/python -m temporal_risk.run pilot --out runs/temporal_risk/20261008_q2
rtk proxy .venv/bin/python scripts/verify_temporal_risk.py --out runs/temporal_risk/20261008_q2
```

`preflight` audits seeds and hashes all previously tracked files. Development
chooses block length from past ACFs using the predeclared rule, stores the full
selection receipt and checks numerical/compute gates. No pilot runs if those
gates fail or the factor-two timing estimate exceeds 600 seconds. The observed
choice is b=16, HAC lag=15, holdout gap=16. It is not tuned on pilot errors.

The pilot has 32 path clusters, three coupled worlds and eight overlapping
origins, with 16 bootstrap refits each for full512 and fixed-equal512 decisions.
Each forecast holds for one next observation; origin stride 64 is not horizon 64.
The outer inference resamples whole path clusters, never individual origins.

## Resume and evidence

Repeating the stage resumes hashed, atomic checkpoints under a file lock.
Source/config/environment/input changes are rejected. Saved failures are kept
and make affected analyses incomplete; they are not silently retried or dropped.
Progress JSONL records completed cases, warnings, actual timings and ETA;
terminal logs retain tqdm. Final CSV columns and LF serialization are stable.

All pilot seeds are now seen. Reproduction is not fresh confirmation. A new
scientific evaluation requires a separately frozen protocol/run with new seeds.
The compact publication contains estimate/diagnostic exports and verification
receipts; some large exports may be gzip-compressed with their original hashes.
Full synthetic NPZ path files and case checkpoints remain local. A compact
clone alone cannot resume or execute the array-based verifier without those
payloads. The full local run can resume directly with its recorded environment.

The verifier recalculates Bartlett HAC with a dense kernel, restores every
bootstrap index stream, checks saved replicate objectives without portfolio
refitting, redoes statistical coefficients, uses an independent odds filter and
direct quadrature, and reproduces all path-cluster paired intervals.
This is numerical/statistical verification, not independent peer review.

Full-text access to the original Newey–West paper returned HTTP 403 in this
session; official statsmodels/arch documentation was read. No claim of temporal
OIC theorem reproduction, market evidence, calibrated VaR/ES, continuous
population-optimal regret or new-model superiority is made.
