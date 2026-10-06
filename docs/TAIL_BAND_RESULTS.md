# Tail-band mechanism: executed results

Freeze commit `296457e`. [Protocol](TAIL_BAND_PROTOCOL.md), [Vietnamese decision](TAIL_BAND_DECISION.md), [coverage CSV](../results/tail_band_v1/coverage.csv), [paired CSV](../results/tail_band_v1/paired.csv).

Completed 200 Gaussian IID series, 5,400 mechanism rows and 600 bounded-target rows. First completed invocation computed 200 cases in 44.51s with 2 numerical processes, one thread each. All 200 generated inputs were verified; 81,000 metrics recomputed from arrays. GMM nonconvergence 0, warnings 0. Tests: 80 passed before execution.

## Simultaneous coverage of all 855 means

Cells are covered seeds / 200, with pointwise Wilson 95% Monte Carlo intervals in percent. Oracle width swaps and population quantiles are diagnostics, not deployable methods. For reused-mixture anchors, the oracle scale is the population variance of a fixed feature evaluated at the realized threshold divided by n; it is not the exact sampling variance conditional on that data-dependent threshold. A confidence interval containing 95% does not establish a 95% guarantee.

| n / anchor | Plug-in max-t | Oracle width swap | Fixed-scale max |
|---|---:|---:|---:|
| 256 / population_quantiles_oracle | 50/200 [19.5, 31.4] | 176/200 [82.8, 91.8] | 194/200 [93.6, 98.6] |
| 256 / base_only | 43/200 [16.4, 27.7] | 174/200 [81.6, 91.0] | 194/200 [93.6, 98.6] |
| 256 / reused_mixture | 44/200 [16.8, 28.2] | 176/200 [82.8, 91.8] | 193/200 [93.0, 98.3] |
| 1024 / population_quantiles_oracle | 130/200 [58.2, 71.3] | 185/200 [88.0, 95.4] | 189/200 [90.4, 96.9] |
| 1024 / base_only | 130/200 [58.2, 71.3] | 187/200 [89.2, 96.2] | 188/200 [89.8, 96.5] |
| 1024 / reused_mixture | 133/200 [59.7, 72.7] | 185/200 [88.0, 95.4] | 188/200 [89.8, 96.5] |
| 4096 / population_quantiles_oracle | 176/200 [82.8, 91.8] | 188/200 [89.8, 96.5] | 186/200 [88.6, 95.8] |
| 4096 / base_only | 173/200 [81.1, 90.6] | 189/200 [90.4, 96.9] | 186/200 [88.6, 95.8] |
| 4096 / reused_mixture | 177/200 [83.3, 92.2] | 189/200 [90.4, 96.9] | 185/200 [88.0, 95.4] |

## Paired coverage changes

Same 200 seeds within each contrast; 5,000 paired bootstrap draws. Differences and intervals are percentage points, pointwise and unadjusted. Rescued/lost counts record changed simultaneous-coverage events. No recipe was selected or promoted after this comparison.

| n / anchor | Contrast | Difference [95% interval] | Rescued / lost |
|---|---|---:|---:|
| 256 / population_quantiles_oracle | oracle_width_swap - plugin_max_t | 63.0 [54.0, 71.5] | 143 / 17 |
| 256 / population_quantiles_oracle | fixed_scale_max - plugin_max_t | 72.0 [65.5, 78.0] | 145 / 1 |
| 256 / base_only | oracle_width_swap - plugin_max_t | 65.5 [56.5, 74.0] | 148 / 17 |
| 256 / base_only | fixed_scale_max - plugin_max_t | 75.5 [69.5, 81.5] | 152 / 1 |
| 256 / reused_mixture | oracle_width_swap - plugin_max_t | 66.0 [57.5, 74.0] | 147 / 15 |
| 256 / reused_mixture | fixed_scale_max - plugin_max_t | 74.5 [68.0, 80.5] | 149 / 0 |
| 1024 / population_quantiles_oracle | oracle_width_swap - plugin_max_t | 27.5 [19.5, 35.5] | 70 / 15 |
| 1024 / population_quantiles_oracle | fixed_scale_max - plugin_max_t | 29.5 [22.5, 36.5] | 62 / 3 |
| 1024 / base_only | oracle_width_swap - plugin_max_t | 28.5 [20.5, 36.0] | 70 / 13 |
| 1024 / base_only | fixed_scale_max - plugin_max_t | 29.0 [22.5, 35.5] | 61 / 3 |
| 1024 / reused_mixture | oracle_width_swap - plugin_max_t | 26.0 [18.0, 33.5] | 67 / 15 |
| 1024 / reused_mixture | fixed_scale_max - plugin_max_t | 27.5 [21.0, 34.0] | 56 / 1 |
| 4096 / population_quantiles_oracle | oracle_width_swap - plugin_max_t | 6.0 [1.0, 11.5] | 21 / 9 |
| 4096 / population_quantiles_oracle | fixed_scale_max - plugin_max_t | 5.0 [0.5, 9.5] | 16 / 6 |
| 4096 / base_only | oracle_width_swap - plugin_max_t | 8.0 [2.5, 13.5] | 25 / 9 |
| 4096 / base_only | fixed_scale_max - plugin_max_t | 6.5 [1.5, 11.5] | 20 / 7 |
| 4096 / reused_mixture | oracle_width_swap - plugin_max_t | 6.0 [1.0, 11.0] | 20 / 8 |
| 4096 / reused_mixture | fixed_scale_max - plugin_max_t | 4.0 [-0.5, 8.0] | 14 / 6 |

## Standard errors and width

SE ratios are sample SE / exact Gaussian hinge SE. Worst-error feature maximizes absolute mean error / exact SE, so its ratio is descriptive and selected using the evaluator. Widths are mean-over-seeds of median-over-features radius/(0.05 × unbounded Gaussian ES95). These are hinge widths, not ES confidence intervals.

| n / anchor | Mean minimum SE ratio | Mean median SE ratio | Mean SE ratio at worst error | Plug-in width | Oracle width | Fixed-scale width |
|---|---:|---:|---:|---:|---:|---:|
| 256 / population_quantiles_oracle | 0.230 | 0.966 | 1.185 | 0.246 | 0.254 | 0.394 |
| 256 / base_only | 0.207 | 0.964 | 1.200 | 0.249 | 0.255 | 0.410 |
| 256 / reused_mixture | 0.258 | 0.962 | 1.256 | 0.245 | 0.254 | 0.397 |
| 1024 / population_quantiles_oracle | 0.598 | 0.988 | 1.048 | 0.127 | 0.128 | 0.189 |
| 1024 / base_only | 0.572 | 0.987 | 1.038 | 0.127 | 0.129 | 0.197 |
| 1024 / reused_mixture | 0.603 | 0.987 | 1.073 | 0.127 | 0.129 | 0.192 |
| 4096 / population_quantiles_oracle | 0.800 | 0.996 | 1.001 | 0.064 | 0.064 | 0.094 |
| 4096 / base_only | 0.787 | 0.995 | 1.005 | 0.064 | 0.064 | 0.098 |
| 4096 / reused_mixture | 0.800 | 0.995 | 1.006 | 0.064 | 0.064 | 0.095 |

## Known-bounded-target DKW positive control

Target: ES95 of each portfolio loss clipped at ±3 population SD, under IID sampling. This is a different target from unbounded ES. DKW + a union bound over the fixed portfolio bank controls every threshold. Widths below are actual ES interval widths divided by population clipped ES95, not the hinge-width proxy above.

| n | All 285 ES covered [Wilson interval %] | epsilon | Mean relative interval width | Upper endpoint at support (%) | Clipping change in true ES (%) |
|---|---:|---:|---:|---:|---:|
| 1024 | 200/200 [98.1, 100.0] | 0.067537 | 0.814 | 100.0 | 0.371 |
| 256 | 200/200 [98.1, 100.0] | 0.135074 | 0.975 | 100.0 | 0.371 |
| 4096 | 200/200 [98.1, 100.0] | 0.033768 | 0.609 | 0.0 | 0.371 |

## Reproduction and limits

Gaussian IID only; the same covariance family that motivated the experiment. New seeds are independent simulation draws, not independent validation of a proposed market algorithm. No conclusions about heavy-tailed or dependent calibration follow. The oracle scale intervention changes widths without replacing the plug-in critical value. Fixed scaling reallocates width across quantiles. The clipped DKW control uses known support and is not an unbounded or next-period market risk certificate.

All original historical, market and earlier diagnostic artifacts remain unchanged. No market test, new dataset, neural model or candidate v3 was run. Independent review remains NOT RUN: the Orca Codex launch hit its updater then exited; a retry failed readiness before task delivery. The updater changed the CLI to 0.160.1; the coordinator did not change global agent preferences. The second terminal was released, and Orca retained the first shell with identity_unproven.

```bash
rtk proxy bash scripts/reproduce_tail_band.sh
```

Aggregate tables are generated from CSV. The analyzer checks source/protocol hashes, regenerates inputs and recomputes per-case metrics. Supplementary verification re-fits the first and last case and independently parses each table number. Local arrays remain under ignored runs/; first-execution timing is preserved across resumes.
