# Correction mechanism — development results

Generated from audited CSVs by `scripts/build_correction_report.py`. All evidence below is development-only, after the earlier market final tests were seen. No new method or superiority claim is selected from these tables.

Read [protocol](CORRECTION_DIAGNOSTIC_PROTOCOL.md), [identifiability analysis](CORRECTION_IDENTIFIABILITY.md) and [primary-source novelty audit](NOVELTY_AUDIT_2026_10.md).

## SYNTHETIC

80 windows; 1680 forecast/selection rows. Artifact audit: **PASS**. Invocation wall time: 6.00s; 80 windows computed this invocation, with two numerical processes. These processes are not independent agents.

Archived validation inputs are exposed development:20 seed clusters ×4 families. Local GMM scenario draws can differ across platform linear algebra implementations; this is a local diagnostic refit, not an overwrite or bitwise reproduction of the original snapshot.

| Method | Same equal target relative ES error | Same historical-SE target relative ES error | Own-selection relative population regret |
|---|---:|---:|---:|
| historical | 0.214178 | 0.165555 | 0.031451 |
| historical_se_penalty | 0.214178 | 0.165555 | 0.039551 |
| support_mix50 | 0.220225 | 0.169172 | 0.034769 |
| support_band50 | 0.217173 | 0.165871 | 0.033018 |
| support_point50 | 0.253119 | 0.195226 | 0.048572 |
| random_band50 | 0.220610 | 0.166471 | 0.035463 |
| filtered_historical | 0.223070 | 0.191612 | 0.059312 |

Lower is better within each column. Synthetic relative quantities are fractions, not percentages. Population regret uses the finite285-bank oracle; Markov truth additionally conditions on an evaluator-only latent state.

| Correction | Unchanged ES surface | Same selection as mixture | All prior moments inside band | Mean total variation from prior | Converged |
|---|---:|---:|---:|---:|---:|
| support_band50 | 56/80 | 73/80 | 56/80 | 0.001451 | 80/80 |
| support_point50 | 0/80 | 26/80 | 0/80 | 0.027756 | 80/80 |
| random_band50 | 70/80 | 77/80 | 56/80 | 0.000883 | 80/80 |

| Target / endpoint | Band minus reference | Difference | Pointwise95% CI |
|---|---|---:|---:|
| equal_weight / relative_error | support_mix50 | -0.003052 | [-0.020767, 0.013275] |
| equal_weight / relative_error | historical_se_penalty | 0.002995 | [-0.019016, 0.021263] |
| equal_weight / relative_error | support_point50 | -0.035946 | [-0.053175, -0.017898] |
| equal_weight / relative_error | random_band50 | -0.003437 | [-0.009444, 0.001244] |
| historical_se_reference / relative_error | support_mix50 | -0.003302 | [-0.016427, 0.007356] |
| historical_se_reference / relative_error | historical_se_penalty | 0.000316 | [-0.016101, 0.012983] |
| historical_se_reference / relative_error | support_point50 | -0.029356 | [-0.044883, -0.014945] |
| historical_se_reference / relative_error | random_band50 | -0.000601 | [-0.002991, 0.001654] |
| own_selection / relative_regret | support_mix50 | -0.001752 | [-0.008870, 0.004678] |
| own_selection / relative_regret | historical_se_penalty | -0.006533 | [-0.015097, 0.001636] |
| own_selection / relative_regret | support_point50 | -0.015554 | [-0.025415, -0.005345] |
| own_selection / relative_regret | random_band50 | -0.002445 | [-0.009192, 0.002694] |

Negative differences favor band. These are exploratory intervals; no multiplicity adjustment. ECB uses paired moving blocks17 here, with5/20/60 all in CSV. Synthetic resamples20 seed clusters with all four families kept together.

Full CSVs: [summary](../results/correction_diagnostic_v1/synthetic/summary.csv), [mechanism](../results/correction_diagnostic_v1/synthetic/mechanism.csv), [decomposition](../results/correction_diagnostic_v1/synthetic/decomposition.csv), [paired differences](../results/correction_diagnostic_v1/synthetic/paired_differences.csv).

## ECB

1537 windows; 32277 forecast/selection rows. Artifact audit: **PASS**. Invocation wall time: 96.28s; 1537 windows computed this invocation, with two numerical processes. These processes are not independent agents.

All eligible2010–2015 ECB development origins, one reference session per target. Reference changes are not executable returns. Latest-vintage and assumed-availability limitations remain.

| Method | Same equal target FZ0 | Same historical-SE target FZ0 | Own-selection pooled ES95 (pp) |
|---|---:|---:|---:|
| historical | -0.226623 | -0.324187 | 0.714746 |
| historical_se_penalty | -0.226623 | -0.324187 | 0.713415 |
| support_mix50 | -0.233855 | -0.319933 | 0.715408 |
| support_band50 | -0.230840 | -0.319409 | 0.693913 |
| support_point50 | -0.226260 | -0.300614 | 0.651895 |
| random_band50 | -0.233248 | -0.322866 | 0.718419 |
| filtered_historical | -0.247354 | -0.422573 | 0.642585 |

Lower is better within each column.

| Correction | Unchanged ES surface | Same selection as mixture | All prior moments inside band | Mean total variation from prior | Converged |
|---|---:|---:|---:|---:|---:|
| support_band50 | 253/1537 | 1198/1537 | 253/1537 | 0.009000 | 1535/1537 |
| support_point50 | 0/1537 | 682/1537 | 0/1537 | 0.054027 | 1536/1537 |
| random_band50 | 878/1537 | 1430/1537 | 253/1537 | 0.002934 | 1532/1537 |

| Target / endpoint | Band minus reference | Difference | Pointwise95% CI |
|---|---|---:|---:|
| equal_weight / fz0 | support_mix50 | 0.003015 | [-0.014281, 0.024371] |
| equal_weight / fz0 | historical_se_penalty | -0.004217 | [-0.018302, 0.010635] |
| equal_weight / fz0 | support_point50 | -0.004580 | [-0.045646, 0.033442] |
| equal_weight / fz0 | random_band50 | 0.002408 | [-0.006378, 0.012759] |
| historical_se_reference / fz0 | support_mix50 | 0.000523 | [-0.014853, 0.019607] |
| historical_se_reference / fz0 | historical_se_penalty | 0.004778 | [-0.007857, 0.020149] |
| historical_se_reference / fz0 | support_point50 | -0.018795 | [-0.068099, 0.027688] |
| historical_se_reference / fz0 | random_band50 | 0.003456 | [-0.006130, 0.014803] |
| own_selection / pooled_es95_pp | support_mix50 | -0.021495 | [-0.049254, -0.001907] |
| own_selection / pooled_es95_pp | historical_se_penalty | -0.019502 | [-0.043690, 0.003790] |
| own_selection / pooled_es95_pp | support_point50 | 0.042018 | [0.009767, 0.075238] |
| own_selection / pooled_es95_pp | random_band50 | -0.024506 | [-0.052764, -0.005366] |

Negative differences favor band. These are exploratory intervals; no multiplicity adjustment. ECB uses paired moving blocks17 here, with5/20/60 all in CSV. Synthetic resamples20 seed clusters with all four families kept together.

Full CSVs: [summary](../results/correction_diagnostic_v1/ecb/summary.csv), [mechanism](../results/correction_diagnostic_v1/ecb/mechanism.csv), [decomposition](../results/correction_diagnostic_v1/ecb/decomposition.csv), [paired differences](../results/correction_diagnostic_v1/ecb/paired_differences.csv).

## Interpretation limits and reproduction

ECB decomposition uses the training calibration block as its reference, not true ES. Synthetic decomposition has an analytical population evaluator. Reported mean absolute components are descriptive, correlated terms; they are not additive shares of total absolute error and do not identify causal contributions.

Finite nonconvergence is retained; no model-specific date deletion. Independent Orca review did not execute because worker readiness failed. No market validation/test rerun, new dataset, new method promotion, profit or Sharpe.

Reproduce with the existing verified cache and pinned `.venv`:

```bash
rtk proxy bash scripts/reproduce_correction_diagnostic.sh
```

The source/config freeze rejects changed diagnostic code. Original market source and history remain unchanged. Per-date market outputs are local under ignored `runs/correction_diagnostic_v1/`.
