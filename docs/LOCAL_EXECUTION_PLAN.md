# RiskDecision: local execution handoff

This file is a new handoff, not a replacement for historical protocols.

1. Complete the original archive import before editing imported source. Use `archives_manifest.json` and `scripts/import_chat_archives.py`. Exact original snapshots must not be regenerated and relabeled as imported history.
2. Run the existing v2 tests in a compatible isolated Python environment. The original `fetch_probe.py` is a historical network probe with a container-specific path and an extra requests dependency; use `market_data.py` for local official downloads.
3. Preserve `quant_research_v2/results/`, its selection freeze and source hashes. Synthetic reruns and full audit should use a separate copy/output directory because original scripts overwrite receipts. The source `research.py` defines the effective constants; the archived config file is not automatically consumed by every script.
4. Download official ECB FX first; verify current use terms and archive provenance. Preserve actual raw bytes, HTTP metadata where available, SHA256, observations, quote convention and release-time assumptions. No fallback synthetic market file or unofficial mirror.
5. Audit before running: publication timing versus observation date; missing-date bridging after complete-case filtering; one-day versus stride-five sampling; numerical percent-point units; optimizer/convergence failures; raw and scored target timestamps.
6. Extend the market harness without rewriting historical experiment definitions. Add the pure support-mixture baseline and preserve diagnostics discarded by the current prototype runner.
7. Split forecasting and decision evaluation. Forecast-quality scores require the SAME realized portfolio loss target across estimators (at least equal-weight and one fixed reference policy). Separately evaluate each model's selected portfolio. Scores across model-specific selected losses do not constitute a clean same-target forecast tournament.
8. Real market data have no analytic population ES. Use appropriate joint VaR/ES scores and calibration/backtesting with dependence-aware uncertainty. Never replace true ES with one realized return, or reuse synthetic relative-error/regret as a market ground-truth metric.
9. Freeze empirical dates, weights, models, primary endpoints, gap rules, fallbacks and inference budget before test. Full one-session forecasts use stride one; stride five is only a sparse-date sensitivity/smoke test.
10. Bank of Canada FX is a secondary source/base-currency sensitivity, not an independent asset class. Zero-coupon curves require a separate fixed-income loss definition and provider publication lag. Do not pass yield levels to the FX return function.
11. Commit code, provider/citation manifests and aggregate results; keep new raw market data, per-date arrays and fitted artifacts local unless publication permission and scope are explicit. Push a research branch, not force-push main.

Read `prompts/ASTRA_LOCAL_MARKET_EXPERIMENTS.md` for the full executable research assignment.
