# Exact local reproduction

Run commands from repository root. Python3.13/macOS arm64 local versions are locked without changing original study pins:

```bash
rtk proxy uv --cache-dir /private/tmp/riskdecision-uv-cache venv --python 3.13 .venv
rtk proxy uv --cache-dir /private/tmp/riskdecision-uv-cache pip install --python .venv/bin/python -r requirements-local.lock
rtk proxy .venv/bin/python -m pytest -q tests quant_research_v2/tests
```

Official downloads/verification (existing raw files are reused without overwrite):

```bash
rtk proxy .venv/bin/python -m local_market.data --source ecb --out data/raw/ecb
rtk proxy .venv/bin/python -m local_market.data --source boc --out data/raw/boc
```

Exact frozen-vintage reproduction requires the original raw bytes with hashes in `docs/market_data_metadata/`. They remain on this machine in `data/raw/`; public Git intentionally does not contain raw/processed market data or per-date forecasts. A future fresh official download may change the raw hash even if the pre-cutoff levels do not change. The runner rejects such a mismatch. Do not overwrite the protocol/hash to make a new vintage appear to be the original run; a new vintage is a separately declared replication.

Complete reproduction into separate ignored output directories, using the existing frozen source/data:

```bash
rtk proxy bash scripts/reproduce_market.sh
```

Exact original ECB command sequence:

```bash
rtk proxy .venv/bin/python -m local_market.runner --dataset data/raw/ecb --out runs/ecb_dev_smoke_v1_final --split development --stride 5 --limit 20 --workers 2
# Freeze was written once and committed as 9e70a57 before held-out evaluation.
rtk proxy .venv/bin/python -m local_market.runner --dataset data/raw/ecb --out runs/ecb_validation_v1 --split validation --workers 2 --protocol configs/market_protocol_v1.json
rtk proxy .venv/bin/python -m local_market.stats --run runs/ecb_validation_v1 --out results/local_market/ecb_validation --protocol configs/market_protocol_v1.json
rtk proxy .venv/bin/python -m local_market.audit --run runs/ecb_validation_v1 --dataset data/raw/ecb --aggregates results/local_market/ecb_validation --protocol configs/market_protocol_v1.json --refit
rtk proxy .venv/bin/python -m local_market.runner --dataset data/raw/ecb --out runs/ecb_test_v1 --split test --workers 2 --protocol configs/market_protocol_v1.json
rtk proxy .venv/bin/python -m local_market.stats --run runs/ecb_test_v1 --out results/local_market/ecb_test --protocol configs/market_protocol_v1.json
rtk proxy .venv/bin/python -m local_market.audit --run runs/ecb_test_v1 --dataset data/raw/ecb --aggregates results/local_market/ecb_test --protocol configs/market_protocol_v1.json --refit
```

BoC uses the same commands with `ecb` replaced by `boc` and `runs/boc_dev_smoke_v1` for its development smoke. Every validation/test origin is evaluated at stride1, including all model warnings/fallbacks. The CLI refuses limit/stride overrides on held-out splits. New output folders have unique configuration identities; a restart resumes only compatible, complete window files.

Public results are `summary.csv`, `annual.csv`, paired differences, pointwise intervals, diagnostic counts and provenance/audit receipts. All displayed report tables are generated from those CSV files. Scores and risk statistics are exposure/reference-factor outcomes, never realized conditional true ES, trading profit or Sharpe.
