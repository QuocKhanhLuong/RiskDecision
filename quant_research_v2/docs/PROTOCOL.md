# Frozen pre-evaluation protocol (2026-10-05)
Scientific target: improve selected-portfolio tail-risk estimation without hiding data/compute advantages. This is an internal design freeze, not external preregistration.

- 8 assets, weights nonnegative, sum one, max weight 0.5. Shared finite candidate bank: equal weight, 28 pairs, 256 Dirichlet points. No cash or leverage. Percent-point return units.
- 512 observed returns for all equal-information controls. Base GMM sees 256; correction data are additional training, not untouched calibration.
- Four synthetic DGPs: Gaussian, asymmetric-crash Gaussian mixture, Student t df4, persistent Markov volatility regime. Last latent state is evaluator-only. Markov target: next-return conditional distribution given the actual last state; state is unavailable to models (oracle evaluation, not a claim of observed-information Bayes regret).
- Existing v1 is a controlled reimplementation (8 rounds and scale-relative floor; historical script had 12 rounds and absolute floor). Do not compare its new numbers directly with old table as a literal rerun.
- Fixed candidate family: mix weight 0.25/0.5, uncertainty-band threshold 1, point-calibrated weight .5, filtered support-band .5. Other recipe constants fixed before main runs.
- Validation: seeds 2000–2019 per family. Select ONE candidate by equal-family mean relative absolute ES error at its selected portfolio. Tie-break by simpler model/runtime. Also freeze best baseline under the same metric.
- Test: seeds 4000–4079 per family, only after selection freeze. Keep all results; ablation/test-table winners are descriptive, not newly deployable selections. Population risk is exact Gaussian-mixture or t formula and accessed only after all predictions.
- Report error, selected true ES, regret versus exact finite-bank oracle, concentration, selection optimism, paired seed bootstrap CIs. No arbitrary aggregate of prediction error and economic risk.
- New method: empirical support augmentation + KL moment reweighting with uncertainty dead-zone. Known mechanisms (entropy pooling, filtered historical simulation); no established new-algorithm/theorem claim.
- Real datasets: require verified terms, unmodified authoritative bytes or verified provenance, date cutoff 2025-12-31. Direct downloads presently fail. No fabricated market observations or results. Online-ready loader supplied separately.
