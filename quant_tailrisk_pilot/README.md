# Quant tail-risk pilot — 2026-10-05

## What this package contains

A **synthetic, reproducible mechanism study**, not a market backtest. It tests adaptive portfolio-tail moment calibration of a Gaussian-mixture scenario model. The implementation is a statistical-ML prototype related to entropy pooling and decision calibration; it is **not claimed to be a new published algorithm, a new theorem, or a validated trading strategy**.

Main result: adaptive correction improves absolute risk-estimation error relative to the original 256-observation GMM, but does not establish superiority over an equal-information 512-observation GMM and loses in true selected-portfolio risk to historical CVaR in the crash-mixture experiment. The adaptive-vs-random calibration distinction is not established in that stress family.

## Run

Python 3.11+ is expected; measured environment was Python 3.13. Exact package versions are in `requirements.txt` and `environment.json`.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python src/run_pilot.py --sanity-only
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python src/run_pilot.py --start 100 --stop 105
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python src/run_pilot.py --start 105 --stop 130
python src/summarize.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python src/audit.py
```

The two execution ranges reproduce the exact file layout used in the supplied analysis. `all_results.csv` contains 480 method-level rows: 8 methods, 30 independent repetitions, 2 populations. `search_size_sensitivity.csv` is an exploratory descriptive analysis of nested portfolio banks added after the main run; no method was changed using it.

## Scope and safeguards

- Eight assets, long-only, fully invested, maximum 50% per asset.
- 285 common portfolio candidates: equal weight, all 28 two-asset 50/50 portfolios, and 256 random portfolios satisfying the cap.
- One additional shrinkage control averages the nominal selected weights with equal weights and can lie outside this finite bank; its comparison with the finite-bank oracle is not a continuum regret certificate.
- Confidence level 95%; losses and risks measured in percentage points of one-period wealth.
- 256 base-fit observations and 256 separate moment-fitting observations.
- GMM base uses only the first 256; candidate correction sees the other 256 as well. **The fair pooled GMM and historical CVaR controls see all 512.**
- Three-component full-covariance GMM with regularized covariance; 2,048 generated scenarios are integration support, NOT 2,048 independent historical observations.
- 12 fixed calibration rounds. Same number of moments for adaptive and random-direction calibration.
- Configuration and fitting code were fixed before viewing main results. This is an in-session exploratory freeze, not an external preregistration.
- Analytic population ES is evaluated only after every decision is fixed. No oracle parameter is passed to any fitting function.
- Gaussian control plus an asymmetric three-state Gaussian mixture. The mixture has crash components but **not power-law tails**, no volatility clustering, no time-varying regime process and no transaction costs.
- No equity/FX data were used. Federal Reserve H.10 retrieval into the execution container failed (network/DNS/download error). Its website and usage policy were reviewed separately.
- No neural network, flow, diffusion, DCC-GARCH or full DRO benchmark was trained.
- Measured main per-seed wall time summed to about 19.75 seconds in the ChatGPT CPU container; this excludes research, code authoring, summary, checks and plotting. This was not run on the user's Mac.

## Files

- `src/run_pilot.py`: simulator, exact ES evaluator, models, candidate and random-control correction.
- `src/summarize.py`: summary and pointwise paired bootstrap intervals (10,000 resamples over seeds).
- `src/audit.py`: reconstruction of 480 result rows and independent large Monte Carlo check of the population formula.
- `config.json`: frozen configuration.
- `docs/METHOD.md`: exact implemented method, design argument, limitations.
- `docs/RESULTS_VI.md`: Vietnamese report.
- `docs/SOURCES.md`: primary literature and source links.
- `results/*.npz`: complete candidate risk surfaces.
- `results/all_results.csv`: all method outcomes.
- `results/paired_CI.csv`: pointwise paired comparisons; not multiplicity-adjusted.
- `results/audit_receipt.json`: recomputation and numerical warnings.

## Numerical warning

One **intermediate** entropy-dual optimization (random control, crash-mixture seed 111, zero-based round 1) reported `ABNORMAL` line-search termination. All final dual solves and all GMM fits reported convergence. The warning was retained, not erased, and the result package documents it. These checks are an internal software audit, not independent scientific review.

## Data and use

Only synthetic outputs created for this study are included. No proprietary market data, credentials, or uploaded credit records are present. External methods and literature must retain their original attribution. This package supports research inspection, not investment recommendations.
