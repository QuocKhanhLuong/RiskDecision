# Market protocol v1 — frozen before validation and final test

Machine contract: [`configs/market_protocol_v1.json`](../configs/market_protocol_v1.json). SHA256:

`741fb298702c77cef204f0aa33f6129b9681d5004a69e076cf7886451a1291be`

Freeze follows actual official downloads, pre-test runner audit,47passing tests and development-only smoke runs. This is an internal timestamped source/data freeze, not external preregistration. No held-out model performance had been computed or inspected when it was written. No market hyperparameter search is authorized in this evaluation; budget0. Rolling refitting on prior observations is allowed.

| Source | Development | Validation | Final test |
|---|---|---|---|
| ECB |history through2015; smoke from2010|2016–2019|2020–2025|
| BoC |history through2020|2021–2022|2023–2025|

Cutoff2025-12-31.512valid consecutive observed changes for training, one excluded observation, final stride1. Eight named risk factors in provider order. Bank285 seed2026, cap0.5. Scenario seed7000+return index. All model recipes fixed to the synthetic benchmark; `gmm_base` uses256observations and is diagnostic only. No future/population parameters enter fitting.

TrackA primary equal-weight target, secondary past-only historical-SE-selected target; all estimators face exactly the same loss within each target/date. Primary mean upper-loss FZ0, secondary pinball95, exceedances and residual calibration. Historical+penalty reports unpenalized ES. TrackB compares each model's selected exposure using pooled realized ES95, concentration and weight stability; it does not rank conditional forecast accuracy across different losses.

Keep finite nonconvergence flagged, use flagged historical fallback on exception/invalid output, and never remove a date based on relative performance. FZ0 requires positive ES; undefined values are counted and never clipped. Full local rows/diagnostics survive all summaries.

Moving-block bootstrap uses joint date vectors and5000replicates, seed20261005. Development sample-size rule sets ECB block17 from4352changes, BoC block10 from999; fixed sensitivities5/20/60.95% percentile intervals are pointwise, descriptive and rely on approximate stationarity. Primary contrasts: candidate minus historical+penalty and candidate minus pure mixture, separately for TrackA and TrackB. Annual diagnostics cover every year. No multiple-comparison-adjusted or conditional-calibration guarantee.

The availability convention is documented in the data manifest and runner audit: latest-vintage retrospective reference changes, origin before target start reference, conservative end-of-day availability assumption plus a full observation gap. Actual historical release logs/revisions remain unknown. No executable price, carry, cost, Sharpe or trading-profit claim.

After final-test opening, method/source/config changes require a separately labeled research extension; these test years cannot be called fresh confirmation again. Yield curves require their own loader/loss/publication-lag protocol and remain NOT RUN.
