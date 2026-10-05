# APTC v2: support augmentation and uncertainty-tolerant moment fitting

This is a tested **candidate implementation**, not an established novel algorithm. The estimator remains GMM/statistical ML with convex probability fitting; no neural-network training is claimed.

## Why change the previous prototype?

The previous pilot did not beat equal-information historical CVaR. Pure reweighting cannot create a tail scenario missing from the generated support; a correction block supplies noisy tail targets, not oracle moments. The new study tests these two issues explicitly and adds stationary heavy tails and latent volatility dynamics.

## Inputs and shared budget

Every equal-information procedure may use 512 returns, dimension 8. GMM-base fits first256; the remaining256 are **training for correction**, not an untouched certification set. Pooled GMM, historical CVaR, Gaussian/Student shrinkage and regularized historical controls see all512. All models choose from the same285 portfolios (long-only, sum1, cap.5). Scenario banks contain1536 generated points; generated points are not additional empirical observations.

## Support-augmented prior

Fit a three-component full-covariance GMM on the first block. Combine generated points z with actual correction rows x:

p0 = (1-beta) Uniform(z) + beta Uniform(x_correction).

Beta in {.25,.50}; validation selected .50. This inserts observed scenarios into the available support, but does not ensure support for an unseen true tail. A pure mixture with no correction is a mandatory ablation.

## Moment loss and uncertainty band

For each portfolio w, use a fixed prior VaR eta and hinge
h_j(z)=max(-w_j' z-eta_j,0).
The new target is the empirical correction-block mean b_j (v1 used half prior/half empirical). Scale by the larger of plug-in standard error and a scale-relative .025-times-portfolio-SD floor. Standard errors are heuristic in the dependent regime DGP, not confidence guarantees.

Let A_ij=h_j(z_i)/s_j, B_j=b_j/s_j. The new primal is

min_{p in simplex} KL(p||p0) + (1/(2rho)) sum_j [max(|A_j' p-B_j|-delta,0)]^2.

rho=1 and delta=1 were fixed. The dead-zone does not force a noisy tail estimate to be matched exactly. All moments/scales/selection depend only on observed training blocks.

The dual minimized by the implementation is

log sum_i p0_i exp(-A_i'v) + B'v + rho ||v||²/2 + delta ||v||_1.

Positive/negative split variables allow bounded smooth optimization. Every third mining step adds the current minimum-risk portfolio if new; other steps select the largest standardized discrepancy beyond delta. Eight steps were predeclared. Reconstruct p by normalized exponential tilting, then compute weighted CVaR with quantile-atom mass handled correctly.

No population parameters enter either optimization. The resulting p is one probability distribution for all candidate portfolios.

## Other controlled variants

- Pure support mixtures beta .25/.50.
- Band .25/.50.
- Point calibration beta .50, delta0.
- EWMA-filtered support/band: residual i uses variance through i-1, lambda .94, first50 initialization; fitted residual scenarios are rescaled to current volatility.
- FHS-type and filtered Gaussian controls use the same filtering convention.
- Historical SE-penalty: choose argmin_w empiricalES(w)+SE[(L-empiricalVaR(w))+/.05]. Reported ES remains the unpenalized risk estimate; the penalty is NOT a statistical upper confidence bound.

The v1 comparator is a controlled reimplementation with eight rounds and scale-relative floor. It is not a literal rerun of the earlier 12-round/absolute-floor study.

## Selection and evaluation

Validation:20 seed clusters x4 families; selected candidate by mean |predictedES-trueES|/trueES, equal family weights. Test:80 new seed clusters x4 families. Both candidate and strongest baseline frozen before test. Per-family best test rows are descriptive only, never a post-test routing policy.

Population ES is analytic for Gaussian mixtures/t distributions. Markov target conditions on the last actual latent state, which is evaluator-only; this is not the observed-information Bayes oracle. Excess risk therefore includes an information/filtering gap. Finite285-bank oracle is not a continuous global optimum.

## Relation to prior work

- Entropy pooling already changes scenario probabilities through relative entropy: Meucci (2008), https://arxiv.org/abs/1012.2848 .
- Volatility filtering and rescaled empirical scenarios are established FHS ideas: https://www.filteredhistoricalsimulation.com/ . Here EWMA is a lightweight adaptation, not a full replication of the authors' nonlinear econometric specification.
- Distributionally robust portfolio optimization has stronger established frameworks, e.g. Esfahani & Kuhn, https://doi.org/10.1007/s10107-017-1172-1 . It has not been reproduced in full in this study.
- VaR/ES joint forecast scoring for a future empirical study: Patton, Ziegel & Chen (2019), https://doi.org/10.1016/j.jeconom.2018.10.008 .

Consequently, a positive ablation does not establish algorithmic novelty. The current main candidate did not beat the strongest simple baseline on the frozen selection endpoint.
