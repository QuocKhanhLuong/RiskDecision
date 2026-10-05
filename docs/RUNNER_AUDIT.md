# Pre-test empirical runner audit

Prepared before opening validation/test performance, 2026-10-05. Historical source and all 931 archive files are unchanged. New code lives in `local_market/`; tests include numerical compatibility with the original calibration. The archived `run_market_risk.py` remains a prototype and is not the final entrypoint.

## Resolved defects and contracts

- Track A: every estimator forecasts identical equal weights, plus a secondary common reference chosen by historical ES+SE using training only. Historical and historical+penalty therefore have identical risk estimates in Track A; the penalty changes selection only.
- Track B: each model selects from identical deterministic bank285, seed2026, cap0.5, no cash. Equal-weight is a policy reference. Report exposure losses, pooled empirical ES95, HHI and half-L1 changes in target weights. These weight changes are a stability proxy, not traded turnover after price drift.
- Added mandatory pure `support_mix50`. Retained historical, historical+SE, Gaussian/Ledoit-Wolf, Student-t/shrinkage, pooled GMM512, diagnostic GMM256, controlled APTC v1, support_band50 and EWMA filtered historical. No model/hyperparameter selection using market test performance.
- Instrumented each of eight correction solves, Student-t optimizer, GMM warnings/iterations/convergence. Finite nonconvergence stays in the sample and is flagged. Exceptions, invalid/nonfinite risk surfaces or ES below VaR fall back to historical, explicitly flagged. The fallback rule precedes test evaluation. No date is removed because a model loses.
- `stride=5` samples origins only; development smoke uses20 windows. Held-out runs enforce stride1 and no limit. Target is one consecutive reference-session change; weekends/holidays can span several calendar days.
- Every row has data source/order, weights, seed, return index, training hash, first/last training dates, availability assumption, information cutoff, origin and target endpoints. Training uses512 past returns excluding the immediately previous return. Any invalid return inside the training window excludes that window for every model, with counts.
- Origin is00:00UTC on target start date, before that day's reference observations. The last training endpoint is one observation earlier, assumed available by23:59:59UTC that earlier day. This is a delayed-information, forward-start reference-change forecast, not a same-close trading strategy. Historical vintages and actual delayed releases are not reconstructed.
- Parser no longer silently bridges incomplete dates. Unknown missing weekdays or incomplete provider rows invalidate a spanning return. Weekends and recognized provider closures remain one session. No price fill.
- Window JSON writes are atomic. Resume requires identical config, code hashes, raw/derived data hashes, training metadata and complete rows. Held-out entrypoints verify frozen source/data hashes. Output folders cannot mix configurations.

## Scoring and inference

For upper loss L, q=.95, tail alpha=.05, VaR v and ES e>0:

`FZ0(L,v,e) = [v + max(L-v,0)/alpha]/e + log(e) - 1`.

Smaller is better only on a common target. It is the upper-loss sign conversion of the joint scoring family discussed by [Patton, Ziegel and Chen](https://arxiv.org/abs/1707.05108). Nonpositive ES is undefined, counted and never clipped. Pinball is `(q - 1[L<v])*(L-v)`. The shortfall identification residual is `v + max(L-v,0)/alpha - e`; its mean is a calibration diagnostic conditional on the VaR/ES pair being correct, not a realized conditional ES label.

The original weighted-CVaR variational calculation correctly includes fractional quantile-atom mass. Unit tests use hand-computed weighted/discrete examples and check score minimization at known Gaussian VaR/ES. Independent aggregate audit uses a descending-tail integral rather than relabeling a single realized loss as true ES.

Paired moving blocks resample date vectors jointly across models. Primary block length is ceil(cube root of development valid-return count), clipped to[5,60];5,20,60 are fixed sensitivities.5000 replicates, fixed seed,95% pointwise percentile intervals. This heuristic and approximate stationarity may be inadequate for regime changes; intervals do not prove conditional calibration or account for model/metric multiplicity. No iid Kupiec/binomial p-values are presented as valid under arbitrary serial dependence. Annual diagnostics are all reported, with effective tail counts.

## Review boundary

Orca runtime was available, but all three Tasks failed at `agent_readiness` before prompt dispatch; an explicit-workspace retry also failed. Receipts said the Tasks never ran. All four owned terminals were released through Orca. No independent agent or human review occurred; CPU processes are numerical workers only. Coordinator implemented and audited the code. No orchestration configuration was changed to bypass the failure.

Pre-test evidence: original26 tests passed locally; extended suite and development smoke receipts are recorded in `LOCAL_ENVIRONMENT.md` and the frozen protocol. The test suite is engineering validation, not scientific peer review.
