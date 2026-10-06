# Tail-band mechanism experiment: frozen before execution

Parent `29646c9a0f5b724265d4a6b3c44fa53d3bcda5de`. This follows the exposed coverage audit; it is a new **mechanism experiment**, not an independent confirmation of a selected forecasting method. No market final tests are reopened.

## Questions and fixed interventions

The earlier Gaussian IID result already rules out temporal dependence and heavy tails as necessary explanations of undercoverage. This experiment isolates three remaining issues on the same samples: estimated tail standard errors, anchor construction, and the width needed by an actually valid bounded-target control.

Use only the fixed Gaussian DGP from `coverage_audit`, 200 new seeds 71000–71199, 8 assets, base sample 256 and nested calibration samples 256/1024/4096. The portfolio bank remains 285 fixed weights, seed 2026. No covariance parameter or seed is selected after this experiment. Three quantiles per portfolio (0.90/0.95/0.975) give 855 hinge features.

Anchors: (a) exact population Gaussian quantiles, an **oracle diagnostic** removing anchor-estimation noise; (b) the existing base-only GMM support; (c) the existing half-GMM/half-calibration mixture. The latter deliberately reuses calibration data. All anchor thresholds are held fixed within bootstrap draws.

Three radius recipes share exactly the same 499 Gaussian multiplier vectors within each seed/sample size, also shared across anchor constructions:

1. `plugin_max_t`: the prior audit's IID max-t recipe, including the n/(n−1) factor and zero-SE treatment.
2. `oracle_width_swap`: retain the **same plug-in critical value**, but replace each plug-in SE in the final radius with the exact Gaussian hinge SE. This isolates a width intervention, not a full oracle covariance bootstrap or a feasible estimator. A paired gain is evidence that changing those widths helps; it does not quantify an additive causal share or prove oracle calibration.
3. `fixed_scale_max`: take the maximum multiplier mean error after dividing by each portfolio's SD estimated on the **independent base sample**, repeated across its three quantiles. Radius is that common critical value times the base SD. It uses no population variance, and gives positive radius to an individually zero-variance feature if other features vary. It changes how width is allocated across thresholds, not just whether the scale is estimated. It is an unstudentized diagnostic using a fixed scale, not a new bootstrap method.

No floor, quantile, block size or critical level is tuned. Exact-normal quantities appear only in the explicitly labelled oracle controls, truth evaluator and known bounded-target definition.

For a zero-mean Gaussian loss with SD s, threshold a and z=a/s:

`E h = s φ(z) − a Φ̄(z)`;

`E h² = (s²+a²) Φ̄(z) − a s φ(z)`;

`SE = sqrt((E h² − (E h)²)/n)`.

These standard Gaussian truncated-moment identities are tested against numerical integration. They are not novel results.

## A positive control with an explicit guarantee

Separately, define **a different target** for each fixed portfolio: `Y_w = clip(L_w, −3s_w, 3s_w)`, where the Gaussian population SD is part of the known synthetic target specification. This is not the ES of the original unbounded loss. It is not an implementable market decision rule or asset-level clipping strategy.

For M=285 fixed portfolio marginals and n independent vector observations, use

`epsilon = sqrt(log(2M/0.05)/(2n))`.

The two-sided Dvoretzky–Kiefer–Wolfowitz–Massart inequality and a union bound give simultaneous CDF coverage at least 95%. Independence between portfolios is not needed. On this event, for **every** threshold inside the known bounds, the true CDF lies between `max(F_n−epsilon,0)` and `min(F_n+epsilon,1)`.

The extremal upper-loss distribution transfers epsilon probability mass from the bottom of the empirical distribution to the known upper endpoint. The lower-loss distribution transfers epsilon mass from the top to the known lower endpoint. Compute their ES95 exactly by quantile integration with partial atoms. Stochastic ordering then bounds the true **clipped** ES95 simultaneously on the entire fixed bank, including a subsequently selected member. This controls all thresholds; it does not depend on the three-feature grid. This is a standard corollary of DKW and ES monotonicity, not a new theorem.

If epsilon ≥ 0.05, the upper distribution has enough mass at the support endpoint that its ES95 is exactly that endpoint. Thus a formally valid interval can carry little tail information. Report that saturation, width relative to true clipped ES, coverage and the population difference induced by clipping. Gaussian clipped ES95 is computed analytically by subtracting `E[(L−3s)+]/0.05` from Gaussian ES95. No realized loss is treated as true ES.

Primary source for DKW and related local refinements: [Reeve, 2024](https://arxiv.org/pdf/2403.16651), especially its introduction and Corollary 2. We implement the classical two-sided bound, not Reeve's local refinement. Variance-sensitive bounded-function inference and selection also have established results: [Maurer and Pontil, 2009](https://www.cs.mcgill.ca/~colt2009/papers/012.pdf); their boundedness requirement cannot silently be applied to unbounded hinges.

## Endpoints and interpretation locked before running

Primary: simultaneous coverage of all 855 means. Report 95% Wilson intervals across the 200 independent seeds and paired coverage differences against plug-in max-t (5,000 paired bootstrap replicates, seed 20261007). Secondary: coverage at each of the three quantiles across all 285 portfolios, equal-weight/q95, under/over failures, minimum/median plug-in-to-true SE ratio, SE ratio at the maximum oracle-standardized mean error, minimum exceedance count and normalized width. DKW control is reported separately as actual clipped-ES interval coverage and width.

Hypotheses are diagnostic: improvement after an oracle width swap supports width estimation as a contributor; persistence with population anchors shows anchor fitting is not necessary for the failure; fixed-scale improvement may trade off wider high-quantile radii. None alone validates a generic 95% guarantee. Pointwise intervals are not adjusted across endpoints, the n values and recipes are paired, and no method is promoted from these data.

## Novelty boundary

[Li, Peng and Song, Econometric Theory 2023](https://www.cambridge.org/core/services/aop-cambridge-core/content/view/36337B7E7E1CDC09EEC7045AD07965C7/S0266466622000275a.pdf/div-class-title-simultaneous-confidence-bands-for-conditional-value-at-risk-and-expected-shortfall-div.pdf) already construct simultaneous conditional VaR/ES bands across tail levels, using location-scale filtering, heavy-tail assumptions and EVT. Their uniformity is over tail levels for the specified return process; it is not automatically a uniform guarantee over a portfolio bank selected from the same sample. Neither their title nor an unverified “portfolio extension” establishes a novelty gap. No replication or theorem transfer is claimed here. This targeted literature addition supplements the earlier maxent and block-bootstrap comparisons.

## Execution contract

M4 Pro, 12 CPUs, 24 GiB RAM rechecked. Use the existing pinned Python environment; 2 processes with one numerical thread each. Original historical files, `local_market`, `correction_audit`, `coverage_audit` and their frozen outputs remain unchanged. Finite GMM nonconvergence is retained; exceptions/nonfinite outputs abort; no seed deletion. Local per-case evidence includes returns, support, thresholds, means, SEs and radii; publish only aggregate CSVs, checksums and receipts. Preserve the first execution receipt across cache resumes. Commit/push freeze before running cases.

Independent Orca review is attempted separately, not assumed to succeed. On the first launch Codex's update prompt consumed startup input and ran its updater, then exited asking for restart; observed version changed from 0.160.0 to 0.160.1. A retry reached an idle CLI but Orca reported `agent_readiness: timeout` before task delivery. This is an orchestration failure, not a review. The first shell was retained by Orca as `identity_unproven`; the second terminal was released. No global runtime setting was changed by the coordinator to bypass this failure.
