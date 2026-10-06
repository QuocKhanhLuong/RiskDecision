# Simultaneous tail-moment coverage: executed feasibility audit

Freeze commit: `77ba092`. Protocol and code were committed and pushed before the500-case run. [Protocol](SIMULTANEOUS_CALIBRATION_PROTOCOL.md), [decision](CALIBRATION_RESEARCH_DECISION.md), [aggregate CSV](../results/coverage_audit_v1/coverage.csv). No new method was fitted, tuned or promoted.

Completed **500 series / 16,000 rows / 160 strata**. The recorded invocation computed 500 cases in44.58s with2 numerical processes (remaining cases, if any, were verified cached results). Audit regenerated500 inputs and recomputed96,000 metrics from local arrays. GMM nonconvergence:0; warnings:0. 70 tests passed before execution. All931 historical files were reverified unchanged.

## Simultaneous coverage of all855 features

Entries are covered cases out of100, followed by the pointwise Wilson95% Monte Carlo interval in percent. The bootstrap recipes target95%; v2 heuristic has no95% nominal guarantee. IID target rows repeat across the two estimands by construction. Neither individual intervals nor160 correlated strata constitute a multiple-testing-adjusted claim.

### stationary_marginal, n=256

| Family / anchor | v2 heuristic | IID max-t | Block short | Block long |
|---|---:|---:|---:|---:|
| gaussian / base_only | 46 [36.6, 55.7] | 22 [15.0, 31.1] | 23 [15.8, 32.2] | 18 [11.7, 26.7] |
| gaussian / reused_mixture | 44 [34.7, 53.8] | 24 [16.7, 33.2] | 24 [16.7, 33.2] | 22 [15.0, 31.1] |
| student_t4 / base_only | 3 [1.0, 8.5] | 23 [15.8, 32.2] | 23 [15.8, 32.2] | 21 [14.2, 30.0] |
| student_t4 / reused_mixture | 3 [1.0, 8.5] | 22 [15.0, 31.1] | 20 [13.3, 28.9] | 18 [11.7, 26.7] |
| asymmetric_crash / base_only | 15 [9.3, 23.3] | 53 [43.3, 62.5] | 51 [41.3, 60.6] | 48 [38.5, 57.7] |
| asymmetric_crash / reused_mixture | 16 [10.1, 24.4] | 54 [44.3, 63.4] | 55 [45.2, 64.4] | 49 [39.4, 58.7] |
| ar1 / base_only | 3 [1.0, 8.5] | 4 [1.6, 9.8] | 9 [4.8, 16.2] | 9 [4.8, 16.2] |
| ar1 / reused_mixture | 4 [1.6, 9.8] | 8 [4.1, 15.0] | 10 [5.5, 17.4] | 10 [5.5, 17.4] |
| markov_volatility / base_only | 15 [9.3, 23.3] | 41 [31.9, 50.8] | 41 [31.9, 50.8] | 42 [32.8, 51.8] |
| markov_volatility / reused_mixture | 13 [7.8, 21.0] | 42 [32.8, 51.8] | 44 [34.7, 53.8] | 43 [33.7, 52.8] |

### stationary_marginal, n=1024

| Family / anchor | v2 heuristic | IID max-t | Block short | Block long |
|---|---:|---:|---:|---:|
| gaussian / base_only | 99 [94.6, 99.8] | 63 [53.2, 71.8] | 61 [51.2, 70.0] | 53 [43.3, 62.5] |
| gaussian / reused_mixture | 99 [94.6, 99.8] | 67 [57.3, 75.4] | 62 [52.2, 70.9] | 59 [49.2, 68.1] |
| student_t4 / base_only | 82 [73.3, 88.3] | 57 [47.2, 66.3] | 58 [48.2, 67.2] | 54 [44.3, 63.4] |
| student_t4 / reused_mixture | 82 [73.3, 88.3] | 64 [54.2, 72.7] | 63 [53.2, 71.8] | 61 [51.2, 70.0] |
| asymmetric_crash / base_only | 59 [49.2, 68.1] | 87 [79.0, 92.2] | 86 [77.9, 91.5] | 85 [76.7, 90.7] |
| asymmetric_crash / reused_mixture | 56 [46.2, 65.3] | 91 [83.8, 95.2] | 89 [81.4, 93.7] | 88 [80.2, 93.0] |
| ar1 / base_only | 80 [71.1, 86.7] | 38 [29.1, 47.8] | 46 [36.6, 55.7] | 46 [36.6, 55.7] |
| ar1 / reused_mixture | 80 [71.1, 86.7] | 41 [31.9, 50.8] | 52 [42.3, 61.5] | 54 [44.3, 63.4] |
| markov_volatility / base_only | 56 [46.2, 65.3] | 65 [55.3, 73.6] | 70 [60.4, 78.1] | 71 [61.5, 79.0] |
| markov_volatility / reused_mixture | 55 [45.2, 64.4] | 64 [54.2, 72.7] | 75 [65.7, 82.5] | 77 [67.8, 84.2] |

### next_conditional, n=256

| Family / anchor | v2 heuristic | IID max-t | Block short | Block long |
|---|---:|---:|---:|---:|
| gaussian / base_only | 46 [36.6, 55.7] | 22 [15.0, 31.1] | 23 [15.8, 32.2] | 18 [11.7, 26.7] |
| gaussian / reused_mixture | 44 [34.7, 53.8] | 24 [16.7, 33.2] | 24 [16.7, 33.2] | 22 [15.0, 31.1] |
| student_t4 / base_only | 3 [1.0, 8.5] | 23 [15.8, 32.2] | 23 [15.8, 32.2] | 21 [14.2, 30.0] |
| student_t4 / reused_mixture | 3 [1.0, 8.5] | 22 [15.0, 31.1] | 20 [13.3, 28.9] | 18 [11.7, 26.7] |
| asymmetric_crash / base_only | 15 [9.3, 23.3] | 53 [43.3, 62.5] | 51 [41.3, 60.6] | 48 [38.5, 57.7] |
| asymmetric_crash / reused_mixture | 16 [10.1, 24.4] | 54 [44.3, 63.4] | 55 [45.2, 64.4] | 49 [39.4, 58.7] |
| ar1 / base_only | 0 [0.0, 3.7] | 0 [0.0, 3.7] | 3 [1.0, 8.5] | 1 [0.2, 5.4] |
| ar1 / reused_mixture | 0 [0.0, 3.7] | 0 [0.0, 3.7] | 3 [1.0, 8.5] | 3 [1.0, 8.5] |
| markov_volatility / base_only | 13 [7.8, 21.0] | 38 [29.1, 47.8] | 50 [40.4, 59.6] | 51 [41.3, 60.6] |
| markov_volatility / reused_mixture | 10 [5.5, 17.4] | 46 [36.6, 55.7] | 61 [51.2, 70.0] | 62 [52.2, 70.9] |

### next_conditional, n=1024

| Family / anchor | v2 heuristic | IID max-t | Block short | Block long |
|---|---:|---:|---:|---:|
| gaussian / base_only | 99 [94.6, 99.8] | 63 [53.2, 71.8] | 61 [51.2, 70.0] | 53 [43.3, 62.5] |
| gaussian / reused_mixture | 99 [94.6, 99.8] | 67 [57.3, 75.4] | 62 [52.2, 70.9] | 59 [49.2, 68.1] |
| student_t4 / base_only | 82 [73.3, 88.3] | 57 [47.2, 66.3] | 58 [48.2, 67.2] | 54 [44.3, 63.4] |
| student_t4 / reused_mixture | 82 [73.3, 88.3] | 64 [54.2, 72.7] | 63 [53.2, 71.8] | 61 [51.2, 70.0] |
| asymmetric_crash / base_only | 59 [49.2, 68.1] | 87 [79.0, 92.2] | 86 [77.9, 91.5] | 85 [76.7, 90.7] |
| asymmetric_crash / reused_mixture | 56 [46.2, 65.3] | 91 [83.8, 95.2] | 89 [81.4, 93.7] | 88 [80.2, 93.0] |
| ar1 / base_only | 0 [0.0, 3.7] | 0 [0.0, 3.7] | 0 [0.0, 3.7] | 0 [0.0, 3.7] |
| ar1 / reused_mixture | 0 [0.0, 3.7] | 0 [0.0, 3.7] | 0 [0.0, 3.7] | 0 [0.0, 3.7] |
| markov_volatility / base_only | 4 [1.6, 9.8] | 9 [4.8, 16.2] | 26 [18.4, 35.4] | 35 [26.4, 44.7] |
| markov_volatility / reused_mixture | 4 [1.6, 9.8] | 7 [3.4, 13.7] | 27 [19.3, 36.4] | 35 [26.4, 44.7] |

## Radius size

Mean across100 seeds of the median across855 features of radius/(0.05×stationary ES95). This is a hinge uncertainty scale, **not an ES confidence interval**. Width is identical for the marginal/conditional target because only the evaluator changes.

| Family / n / anchor | v2 heuristic | IID max-t | Block short | Block long |
|---|---:|---:|---:|---:|
| gaussian / 256 / base_only | 0.241 | 0.244 | 0.240 | 0.239 |
| gaussian / 256 / reused_mixture | 0.241 | 0.242 | 0.239 | 0.237 |
| gaussian / 1024 / base_only | 0.242 | 0.126 | 0.125 | 0.124 |
| gaussian / 1024 / reused_mixture | 0.242 | 0.125 | 0.125 | 0.124 |
| student_t4 / 256 / base_only | 0.218 | 0.414 | 0.403 | 0.393 |
| student_t4 / 256 / reused_mixture | 0.218 | 0.413 | 0.404 | 0.395 |
| student_t4 / 1024 / base_only | 0.219 | 0.222 | 0.220 | 0.219 |
| student_t4 / 1024 / reused_mixture | 0.219 | 0.222 | 0.220 | 0.220 |
| asymmetric_crash / 256 / base_only | 0.170 | 0.406 | 0.398 | 0.395 |
| asymmetric_crash / 256 / reused_mixture | 0.168 | 0.410 | 0.402 | 0.397 |
| asymmetric_crash / 1024 / base_only | 0.161 | 0.215 | 0.214 | 0.213 |
| asymmetric_crash / 1024 / reused_mixture | 0.161 | 0.218 | 0.216 | 0.216 |
| ar1 / 256 / base_only | 0.239 | 0.241 | 0.293 | 0.294 |
| ar1 / 256 / reused_mixture | 0.239 | 0.233 | 0.277 | 0.278 |
| ar1 / 1024 / base_only | 0.242 | 0.129 | 0.171 | 0.172 |
| ar1 / 1024 / reused_mixture | 0.242 | 0.126 | 0.165 | 0.165 |
| markov_volatility / 256 / base_only | 0.207 | 0.372 | 0.431 | 0.452 |
| markov_volatility / 256 / reused_mixture | 0.206 | 0.389 | 0.449 | 0.473 |
| markov_volatility / 1024 / base_only | 0.211 | 0.222 | 0.289 | 0.304 |
| markov_volatility / 1024 / reused_mixture | 0.211 | 0.230 | 0.302 | 0.320 |

## Pointwise and selected-feature coverage

The CSV also records fixed equal-weight/q95 coverage, coverage of the feature selected by empirical prior/calibration discrepancy, average feature coverage, widths, critical values and zero-SE counts. These are secondary diagnostics; selecting one successful feature cannot validate the simultaneous claim.

| Family / n / base_only | IID equal q95 | IID selected | Short-block equal q95 | Short-block selected |
|---|---:|---:|---:|---:|
| gaussian / 256 | 98 | 91 | 98 | 88 |
| gaussian / 1024 | 100 | 100 | 100 | 100 |
| student_t4 / 256 | 89 | 89 | 88 | 88 |
| student_t4 / 1024 | 99 | 98 | 97 | 98 |
| asymmetric_crash / 256 | 96 | 89 | 97 | 89 |
| asymmetric_crash / 1024 | 99 | 98 | 99 | 98 |
| ar1 / 256 | 93 | 69 | 95 | 72 |
| ar1 / 1024 | 97 | 92 | 98 | 97 |
| markov_volatility / 256 | 77 | 75 | 80 | 74 |
| markov_volatility / 1024 | 92 | 89 | 94 | 93 |

## Limits and reproducibility

A supplementary check refits Gaussian seed62000 and Markov seed62099, reconstructing GMM scenarios, anchors, selections and every radius exactly. [Post-hoc Gaussian localization](../results/coverage_audit_v1/gaussian_failure_localization.csv) examines which quantiles fail and on which side. That analysis was added after viewing coverage, is descriptive, and changes no frozen recipe.

These are synthetic stationary processes with exact evaluator distributions,100 seeds per stratum and499 multipliers. Student t4, unbounded hinges, random thresholds, studentization and dependent contiguous fitting/calibration blocks require assumptions beyond a generic block-bootstrap citation. The three-threshold grid does not imply all-threshold ES or selection-regret guarantees. Markov conditional targets use a latent-state oracle. Stationary marginal calibration is not next-period conditional calibration.

Independent review: **NOT RUN**. Orca Claude launch failed with `zsh: command not found: claude`; the task was never reviewed. The abandoned dispatch's shell was retained by Orca with `identity_unproven`. No CPU worker is counted as an independent agent.

No market data were downloaded again, no market validation/final test rerun, and no candidate/hyperparameter was selected from this experiment. Raw FX and generated per-case arrays remain local. No trading profit or Sharpe claim.

```bash
rtk proxy bash scripts/reproduce_coverage_audit.sh
```

The runner verifies frozen source/protocol hashes and rejects changed or incomplete cached cases. On this pinned platform generated case arrays are reproducible; cross-platform GMM/BLAS bit identity is not promised. The report builder maps all table values from the audited CSV; local audit checks population formulas and per-case coverage, but does not re-bootstrap every case.
