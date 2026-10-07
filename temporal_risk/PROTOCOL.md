# Q2 protocol and applicability audit — before development/pilot, 2026-10-08

Decision: run a bounded temporal baseline pilot after the completed Q1 work.
This is not new-method search. All prior measured code/config/results remain
unchanged. No Q1 seeds or temporal outcomes are used as fresh confirmation.

## Questions, units and primary

Can a past-fitted statistical conditional model explain error that an iid
optimism correction cannot? Distinguish marginal estimation/selection error
from reference-to-next conditional mismatch at the **same locked decision**.

Primary: on stationary AR(1), full512 decision, mean squared relative error for
the next-step expected smoothed objective, diagonal Gaussian AR estimator minus
iid OIC. Average the eight origins within each path first, then use a paired
10,000-replicate bootstrap of **32 independent path-seed clusters**. This is a
feasibility pilot, not powered universal-superiority evidence. Secondary CIs
are unadjusted. No pooling origins/worlds as independent samples; no interim
metric inspection or extra seeds after observing results.

Fresh seed range 2026109000:2026109032, audited against local observed use before
freeze. Development seeds 2026108998/99 excluded. Job order randomized once.
Any missing method cell makes its registered contrast INCOMPLETE, not a
complete-case comparison. Failed cases, nulls, warnings and negative corrections
are retained. Every origin predicts **one next observation**; stride 64 is
spacing between evaluation origins, not a 64-step holding horizon.

## DGPs and information

Eight assets, common fixed mean/covariance in config. Three worlds share the
seed's Gaussian innovations; the two Markov worlds also share state uniforms:

1. Stationary Gaussian AR(1), phi=.6, initialized from its stationary law.
2. Two-state Gaussian Markov volatility, stationary transition P0 throughout.
3. Matched Markov transition shift, P0 before index 768 and P1 from index 768.
   Emissions remain fixed; transition and marginal state occupancy change.

The two Markov paths are byte-identical before the break. Transition at time t
maps state(t-1) to state(t). This is a controlled synthetic nonstationarity, not
an identified change point in market data. Shift time/P matrices/hidden states
are never passed to learned estimators.

Origins 512,576,640,704,768,832,896,960 use exactly observed rows [t-512,t).
The true target is E[h_tau(theta;X_t)|this observed window], with known DGP
parameters only in the evaluator. AR has an analytic conditional Gaussian.
Markov target uses a forward Bayesian filter initialized at the known marginal
state prior at the window start. It does not observe hidden state or data before
the allowed window. A separate latent-state reference uses state(t-1), not
state(t); it is an unequal-information diagnostic, never a learned baseline.
The filter knows true parameters and the shift schedule: it is a **parameter
oracle**, not an equally learned competitor.

## Shared decisions and estimates

Same feasible set as Q1: long-only, sum(w)=1, cap=.5, threshold [-50,50]; tau=.1,
alpha=.05 fixed. No smoothing sweep or new portfolio selector.

- full512: original smooth empirical optimizer using all 512 observations.
- equal512: fixed equal weights, only the smooth threshold fitted on 512.
  This is a portfolio-fixed control, not a no-selection threshold control.
- older256: same optimizer on the older half. All forecasts for this policy
  share theta; chronological evaluation uses the newer 256. Purged evaluation
  drops the first b newer observations, leaving 256-b, to create a temporal gap.
  It is not claimed independent under finite dependence or a distribution shift.

Full/equal estimates: raw, iid OIC, HAC-adjusted local optimism, circular block
bootstrap optimism, past Gaussian, diagonal AR Gaussian, EWMA Gaussian.
Older256: raw/iid OIC/HAC on fitting half; chronological/purged holdout; the
same three statistical models fitted on the complete observable 512 rows.
Total information budget is 512 throughout; fitting/evaluation sample sizes
and origin ranges are reported. No score compares different method-selected
portfolios as if they were the same target.

AR is coordinatewise OLS with intercept, coefficients clipped to [-.98,.98]
(counts recorded), full residual covariance. EWMA uses normalized exponential
weights lambda=.94 on demeaned observations, with the past-window mean. These
are fixed statistical assumptions, not true DGP coefficients. No learned HMM
or hidden-state access is used.

## Corrections and prior art

On a strict stable face, projected scores u_i=g_i N and reduced Hessian R give
the Q1 iid correction. The stationary-dependent local expansion substitutes
the long-run score covariance S for the iid covariance: `trace(R^-1 S)/n`.
We estimate S with centered scores and Bartlett lag weights through lag b-1.
This is a **documented HAC adaptation**, conditional on mixing, stable face and
curvature, not a proved conditional-risk correction. At lag zero it agrees
with centered iid scores. No clipping/ridge is used to force its acceptance.

[Newey–West, NBER technical paper 55](https://www.nber.org/papers/t0055)
is the HAC prior-art source; the official
[statsmodels HAC reference](https://www.statsmodels.org/stable/generated/statsmodels.stats.sandwich_covariance.cov_hac.html)
describes Bartlett weighting and equally spaced observations. We implement and
check the lag-sum against a dense Bartlett-kernel calculation independently.
NBER metadata was found, but full-page/PDF access returned HTTP 403 in this
session; no full-text verification is claimed. The official implementation
documentation was accessible. Kunsch's original full text was also not
available through the retrieved landing page, so it is not claimed as read.

Circular block bootstrap uses contiguous b-length blocks with wrap-around,
as documented in [arch's implementation](https://arch.readthedocs.io/en/latest/bootstrap/generated/arch.bootstrap.CircularBlockBootstrap.html).
For each of 16 fixed replicates, refit theta* on the resampled past and compute
`mean_original h(theta*) - mean_resampled h(theta*)`; add the replicate mean to
the original fitted objective. Keep Monte Carlo SE, refit convergence/gap,
negative values and nulls. This is an optimism diagnostic for a stationary
marginal objective, not independent future validation. No theorem guarantee
is claimed across the structural break. The package is not required at runtime.

## Development selection and numerical gates

Window 512, tau, model definitions and 16 bootstrap refits fixed here.
Choose b from {8,16,32} using **past-only development autocorrelations**, never
population prediction error: for each development window and its equal-weight
return and squared-return series, find the first lag k in 1..30 followed by
three absolute ACFs <.1; use 32 if absent. Take the maximum k across windows,
round up to the smallest candidate at least k. Log every ACF/cutoff and selected
b. Use HAC lag b-1 and purged-holdout gap b. Freeze the resulting effective
config before generating any pilot data. This heuristic has no optimality claim.

Tests: coupled-world equality before break; correct transition/filter timing;
filter vs exhaustive short-state enumeration; no hidden/future dependence of
fitting; conditional/marginal laws; HAC PSD and dense-kernel identity; block
index structure; bootstrap determinism; same-decision rows; decomposition
identity and path-cluster inference. Development must pass numerical/quality
gates, with estimated pilot wall time (factor-two margin) <=600 seconds.

## Evaluation and interpretation

For each theta define R_ref as the expectation under the average **unconditional
marginal laws over that policy's fitting dates**, and R_next as the observed-
history conditional next-step target. Report exactly

`estimate-R_next = (estimate-R_ref) + (R_ref-R_next)`.

The first term is finite-sample estimation/selection error, not an isolated
causal selection effect. The second includes conditional-state information and
distribution shift; stationary AR can have it without any structural change.
Equal-weight controls help assess portfolio selection but still fit a threshold.
All rows include true conditional ES separately; no adjusted VaR/ES pair is
fabricated. Comparing shift and stationary worlds is a coupled pipeline
diagnostic, not a common-portfolio forecast contest across worlds.

## NOT_RUN

Market data, trading/utility, full Q3 matrix, learned HMM, new APTC/neural models,
unsmoothed OIC, general weak-face directional correction, temporal theorem
proofs, continuous population-optimal regret and calibrated joint VaR/ES scoring.
