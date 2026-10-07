# RiskDecision

**Portfolio tail-risk learning after optimization. Current measured evidence is synthetic only. No market backtest has been completed in the imported studies.**

## Start here

- [Astra local execution prompt](prompts/ASTRA_LOCAL_MARKET_EXPERIMENTS.md)
- [Import status and complete historical snapshots](docs/IMPORT_STATUS.md)
- [Local execution plan](docs/LOCAL_EXECUTION_PLAN.md)
- [v2 results in Vietnamese](quant_research_v2/RESULTS_VI.md)
- [v2 method](quant_research_v2/docs/METHOD_V2.md)
- [Dataset provenance audit](quant_research_v2/docs/DATASET_AUDIT.md)
- [Original pilot method](quant_tailrisk_pilot/docs/METHOD.md)

## Research question and current decision

Does optimizing a portfolio amplify optimism in its estimated tail risk, and can distributional correction improve the selected portfolio's risk estimate without sacrificing decision quality?

The optimizer's curse, entropy pooling, CVaR regularization and filtered historical simulation are prior art. APTC is a candidate prototype, not a proven new algorithm.

The v2 synthetic study reports 80 validation instances and 320 held-out test instances across four simulation families and 18 configurations. Validation selected `historical_se_penalty` as the leading baseline and `support_band50` as the candidate. Mean relative selected-portfolio ES error is approximately 14.30% versus 15.01%. These are estimation errors, not portfolio losses or investment returns. The candidate has not established superiority over strong equal-information controls.

## Layout

```text
quant_tailrisk_pilot/       Original v1 study (separate from v2)
quant_research_v2/          Current synthetic engine, tests, data loaders, reports
prompts/                   Complete Astra assignment for local market experiments
docs/                      Import receipts and local evaluation requirements
scripts/import_chat_archives.py
archives_manifest.json     Original archive checksums and counts
```

The direct GitHub import contains executable research code, tests, documentation and selected result files. It is NOT the complete 931-file historical snapshot: full per-seed arrays, detailed tables, figures and some ancillary files remain in the two original ZIPs. Restore them before running the historical full-artifact audit. No missing result is replaced with a regenerated or fabricated file.

## Complete the historical import

Download the original ChatGPT attachments with these exact names:

- `Quant_Tail_Risk_Method_and_Pilot.zip`
- `Quant_Risk_v2_Code_Results.zip`

Then, from this repository root:

```bash
python3 scripts/import_chat_archives.py --archive-dir "$HOME/Downloads" --verify-only
python3 scripts/import_chat_archives.py --archive-dir "$HOME/Downloads"
```

The importer checks both complete archive SHA256 values, 931 member files, CRCs and existing file equality. It rejects path escapes, symlinks and differing existing files. It does not download market data, overwrite different content, modify Git refs or push automatically. Commit restored historical files separately from later method changes.

## Set up and test

Use a Python version compatible with the pinned dependencies. Python 3.13 matches the original reported environment; verify local package availability rather than silently changing pins.

```bash
cd quant_research_v2
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
```

The current handoff reran the v2 suite: 26 tests passed. This is not a new empirical experiment or independent scientific review. Historical reruns/audits write result files; use an isolated copy under `work/` to preserve original snapshots.

## Official data starter commands

Run from `quant_research_v2/` after reading the local prompt:

```bash
python src/market_data.py --source ecb --out ../data/raw/ecb
python src/run_market_risk.py \
  --levels ../data/raw/ecb/levels.csv \
  --out ../runs/ecb_smoke --from-date 2010-01-01 --to-date 2015-12-31 \
  --stride 5 --limit 20
```

These are prototype starter commands, not a certified market protocol. Stride five samples one-period forecast dates; it is NOT a five-day holding horizon. Final evaluation must audit publication times, incomplete-date gaps, VaR/ES scoring and solver warnings. Separate forecasting on common portfolio losses from evaluating each model's own selected portfolio.

Reference FX moves do not include execution prices, carry, spread or funding. Do not report trading profit or Sharpe from them. Yield curves need separate fixed-income loss construction; never pass yield levels into the FX return function.

## Data and publication policy

Keep new market raw data, per-date caches, credentials and local environments out of Git unless usage terms and publication scope explicitly permit them. The historical synthetic snapshots may be imported as requested. No third-party dataset license is inferred from this repository being public. Preserve sources/citations and report negative results and NOT RUN boundaries.
