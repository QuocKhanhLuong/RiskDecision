# Quant portfolio-tail risk research v2

**Synthetic test results, not a market backtest.** Read RESULTS_VI.md first.

## Results
- Four DGPs;80 validation and320 unseen synthetic test instances.
-18 configurations/controls;7,200 aggregate measurements.
- Candidate frozen on validation: support_band50.
- Strongest validation-selected equal-information baseline: historical_se_penalty.
- Candidate does NOT beat the baseline on the primary endpoint.
-26 tests passed; see numerical audit and convergence warnings.

## Setup and repeat
Python3.11+ recommended. Measured environment in results/environment.json.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m pytest -q
# Existing result files are included. Regeneration overwrites stage results.
python src/research.py --stage validation --workers 3
# selection_freeze.json is immutable; included receipt matches this validation.
# For a fresh study, use a new directory rather than overwrite the freeze.
python src/research.py --stage test --workers 3
python src/summarize.py
python src/audit.py
```

## Official FX data: not downloaded in this run
```bash
python src/market_data.py --source ecb --out data/ecb
# or with an unmodified official archive:
python src/market_data.py --source ecb --raw-file /path/eurofxref-hist.zip --out data/ecb
python src/run_market_risk.py --levels data/ecb/levels.csv --out results/ecb_risk --stride 5
```

The rolling runner was tested only with synthetic fixtures. Its output concerns reference-price risk factors, not executable profit/Sharpe. Read docs/MARKET_PROTOCOL_NOT_RUN.md and DATASET_AUDIT.md before use. Do not feed yield levels into the FX-return runner. No fallback or fabricated market data are generated after download failure.

## Reproducibility
`src/research.py` contains the frozen synthetic protocol. `selection_freeze.json` was written before test. Results retain all methods, even losers. `audit.py` rechecks cached surfaces, returns, population tails and aggregate values. The first candidate selection and metadata are preserved; plotting/reporting do not retune models.

## Prior work
See docs/METHOD_V2.md. Entropy pooling, historical/filtered simulation, covariance shrinkage and robust optimization are established ideas. This package claims neither a new theorem nor a superior published algorithm.
