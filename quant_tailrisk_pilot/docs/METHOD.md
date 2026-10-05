# Adaptive Portfolio-Tail Calibration (candidate prototype)

## Objective

Repair a scenario model on portfolio-tail directions relevant to optimization rather than merely inflating all predicted risks. The name is descriptive; no novelty claim is established.

For return vector R and feasible weights w, loss L(w,R)=-w^T R. Confidence q=0.95.

CVaR_q^P(w) = min_eta [ eta + E_P max(-w^T R-eta,0)/(1-q) ].

For a finite scenario bank z_i, use nonnegative weights p_i summing to one. The same distribution is used for ALL portfolios. Thus the risk surface is a genuine CVaR surface, not an arbitrary portfolio-dependent MLP correction.

## Base fit

Fit a 3-component GaussianMixture to 256 observations; sample 2048 scenarios. Uniform p0. No test or population parameters enter fitting.

## Moment targets

For candidate direction w_j, set eta_j to the BASE model's VaR95. Freeze eta_j for this prototype. Define h_j(z)=max(-w_j^T z-eta_j,0).

Use a separate 256-observation moment-fitting block C. This is additional TRAINING data for the correction, not an untouched inferential calibration/certification set.

- b0_j = mean_i h_j(z_i)
- bC_j = mean_{x in C} h_j(x)
- b_j = 0.5 b0_j + 0.5 bC_j
- s_j = max(sample_SD_C(h_j)/sqrt(256), 0.025)

The fixed half-shrinkage reduces sensitivity to the small tail sample but does not have an optimality claim. The floor is in the pilot's percentage-point loss units. It must not be transferred unchanged to decimal market-return units.

## Adaptive direction mining

Start from uniform p0. For 12 rounds:

1. Every third round, add the current minimum-risk portfolio if not already selected.
2. Otherwise choose the unselected candidate with largest absolute standardized stop-loss moment discrepancy |b_j - sum_i p_i h_j(z_i)| / s_j.
3. Refit scenario probabilities using all accumulated moments.

A matched ablation chooses the same number of moment directions randomly from the same bank.

## Convex probability update

Let A_ij=h_j(z_i)/s_j and B_j=b_j/s_j for chosen moments.

min_{p in simplex} KL(p || p0) + (1/(2*rho)) ||A^T p-B||_2^2, rho=1.

The implemented dual minimizes:

log sum_i p0_i exp(-A_i^T v) + B^T v + rho ||v||^2/2.

Then p_i is proportional to p0_i exp(-A_i^T v). No scenario outcome is moved. This is related to established entropy-pooling/moment-projection methods; adaptive direction selection is the candidate component under evaluation.

## Inference

After the probability update, compute weighted CVaR for every candidate using fractional quantile-atom mass. Select the portfolio with minimum predicted CVaR. The goal is risk minimization under fixed full exposure, not return maximization or a market-neutral trading strategy.

## Why match stop-loss moments?

Let P be the true distribution and Q an estimated distribution. Suppose finite first moments and a threshold domain containing the relevant quantile minimizers, and suppose

sup_{w,eta} | E_P h(w,eta,R) - E_Q h(w,eta,R) | <= epsilon.

Then by the CVaR variational representation,

sup_w | CVaR_P(w)-CVaR_Q(w) | <= epsilon/(1-q).

For exact minimizers w_Q and w_P over the SAME feasible set,

CVaR_P(w_Q)-CVaR_P(w_P) <= 2 epsilon/(1-q).

The proof is the standard bound for differences of infima followed by two uniform-error applications. This is a DESIGN ARGUMENT / elementary consequence, not a new theorem.

## What the implementation does NOT establish

- It tests 285 portfolios and fixed base-VaR hinges, not all w and eta.
- Empirical calibration targets contain sampling error and were adaptively used to choose directions.
- No population uniform epsilon, finite-sample certificate or conditional/time-series validity was estimated.
- Pure reweighting cannot create tail support absent from the scenario bank.
- The Gaussian-mixture pilot is unconditional and stationary within each repetition.
- Constant half-shrinkage and 12 rounds are fixed engineering settings, not optimized or theoretically optimal.
- A continuous-portfolio/context-conditioned neural version has NOT been implemented.

## Novelty gate

Must distinguish this from entropy pooling, decision calibration, decision-focused scenario generation, regularized CVaR and DRO. The current pilot does NOT justify claiming a superior new algorithm. In particular, the candidate does not outperform equal-information historical CVaR on true selected-portfolio risk in the crash-mixture condition.
