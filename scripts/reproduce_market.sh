#!/usr/bin/env bash
# Run from repository root. Keep original raw bytes in data/raw/{ecb,boc}.
set -euo pipefail
rtk proxy .venv/bin/python -m pytest -q tests quant_research_v2/tests
for provider in ecb boc; do
  rtk proxy .venv/bin/python -m local_market.data --source "$provider" --out "data/raw/$provider"
  for split in validation test; do
    rtk proxy .venv/bin/python -m local_market.runner \
      --dataset "data/raw/$provider" --out "runs/reproduction-v1/${provider}_${split}" \
      --split "$split" --workers 2 --protocol configs/market_protocol_v1.json
    rtk proxy .venv/bin/python -m local_market.stats \
      --run "runs/reproduction-v1/${provider}_${split}" \
      --out "local_artifacts/reproduction-v1/${provider}_${split}" \
      --protocol configs/market_protocol_v1.json
    rtk proxy .venv/bin/python -m local_market.audit \
      --run "runs/reproduction-v1/${provider}_${split}" --dataset "data/raw/$provider" \
      --aggregates "local_artifacts/reproduction-v1/${provider}_${split}" \
      --protocol configs/market_protocol_v1.json --refit
  done
done
