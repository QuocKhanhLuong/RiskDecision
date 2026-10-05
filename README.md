# RiskDecision

Research on portfolio tail-risk estimation after portfolio optimization.

**Current evidence: synthetic experiments only. No ECB, Bank of Canada, BIS, or other market backtest has been completed in the imported studies.** APTC remains a candidate prototype, not an established superior algorithm.

## Research question

Can a model estimate the tail risk of the portfolio selected by an optimizer reliably, rather than merely fit average distributional properties?

Forecast accuracy and the actual risk of the selected portfolio are separate outcomes. The optimizer's curse, entropy pooling, CVaR regularization and filtered historical simulation are prior art, not claimed inventions here.

## Project layout

- `quant_research_v2/`: current implementation, source documentation, tests and selected aggregate result snapshots.
- `quant_tailrisk_pilot/`: original v1 implementation and research documentation, kept separately.
- `prompts/ASTRA_LOCAL_MARKET_EXPERIMENTS.md`: next-stage local execution prompt.
- `docs/LOCAL_EXECUTION_PLAN.md`: handoff and publication-time/evaluation checks.
- `scripts/import_chat_archives.py`: verify and restore complete historical archives locally, without overwriting differing files.
- `archives_manifest.json`: exact archive names, sizes and SHA256 checksums.

## Evidence boundaries

The v2 report records 80 synthetic validation instances and 320 held-out synthetic test instances, four simulation families and 18 methods/configurations. The validation-selected baseline is `historical_se_penalty`; the selected candidate is `support_band50`.

Reported mean relative selected-portfolio ES error: baseline about 14.30%; candidate about 15.01%. These are risk-estimation errors, not portfolio losses or investment returns. The candidate did not establish superiority over strong equal-information controls.

## Local setup

```bash
cd quant_research_v2
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
```

Use a Python version compatible with the pinned dependencies; do not assume the original broad `3.11+` recommendation satisfies every package version. Record the actual environment and any justified lockfile changes.

## Official market-data starter commands

These commands exist in the imported source. They are a starting point, not a certified empirical protocol.

```bash
python src/market_data.py --source ecb --out ../data/raw/ecb
python src/run_market_risk.py \
  --levels ../data/raw/ecb/levels.csv \
  --out ../runs/ecb_smoke --stride 5 --limit 20
```

Read the prompt and market protocol first. `--stride 5` samples one-day forecast dates; it is NOT a five-day investment horizon. ECB reciprocal quotes, source publication times, gaps and correct VaR/ES scoring must be checked before final evaluation. The current runner has only been tested using synthetic fixtures.

## Full historical artifacts

The complete ChatGPT-delivered archives include per-seed arrays, detailed CSVs, figures and original manifests. Large historical files are not silently replaced with regenerated results. Consult `docs/IMPORT_STATUS.md` for exactly what has been published and what still requires the local archive import.

```bash
# From repository root, after downloading the original ZIPs into ~/Downloads:
python3 scripts/import_chat_archives.py --archive-dir "$HOME/Downloads"
```

This restores the exact archived trees and checks their files against the archive bytes. It does not download market data, invent experimental results or push anything automatically.

## Repository safety

Keep newly downloaded market data, credentials, local environments and future run caches outside tracked paths. Do not overwrite historical results or change their reported decisions. Run new empirical experiments in a new branch and output directory. No project-wide license is inferred for third-party datasets; usage and publication terms must be checked at the provider.
