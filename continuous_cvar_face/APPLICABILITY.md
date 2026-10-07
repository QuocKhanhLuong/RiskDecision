# Stable-face correction: pre-implementation audit, 2026-10-08

Decision: conditional GO for a geometry-specific extension of the previous
smooth CVaR benchmark. Same objective, optimizer, data, feasible set and tau
schedule. No change to historical code/config/results. This is a local
derivation and numerical audit, not a new OIC theorem or authors-code reproduction.

## VERIFIED_SOURCE / REPORTED

Re-read [OIC v4](https://arxiv.org/html/2306.10081v4), Appendix 7.3.3 and its
constrained assumptions. The paper motivates an influence-function correction
under regularity; the previous implementation already derived the reduced
Hessian formula. The published pilot's four primary nulls identify a redundant
active-normal representation at capped-simplex vertices. Those results remain
INCOMPLETE. Their outcomes are seen and are not fresh confirmation here.

## DERIVED HERE: certify the feasible face without unique multipliers

Let q be the empirical objective gradient in w, and lambda the budget multiplier.
KKT stationarity is q_j+lambda-mu_lower_j+mu_upper_j=0. The threshold is interior.
At free weights F, lambda=-mean(q_F), with all q_F equal at stationarity.
Lower weights L require q_L+lambda>0; upper weights U require
-(q_U+lambda)>0. The minimum of these strict margins certifies a stable face.

At a vertex F is empty. For this cap=.5/budget=1 geometry there are both upper
and lower weights. A strictly complementary certificate exists exactly when

`max(q_U) < min(q_L)`.

Choose `lambda=-(max(q_U)+min(q_L))/2`. All bound multipliers are then strictly
positive despite the redundant budget row. A negative least-squares multiplier
from the old representation is not evidence that no nonnegative certificate
exists. The gap has a geometric meaning: every unit of feasible transfer from
an upper weight to a lower weight has a positive first-order cost.

The critical cone consists of feasible tangent directions d with gradient.d=0.
With the strict margins above it equals the linear tangent space of the minimal
face: active coordinates fixed, free weight directions summing to zero, and a
free threshold. Choose an orthonormal basis N directly from these free coordinates.
At the two-upper vertex, portfolio directions vanish, but the threshold remains
free. Positive reduced curvature and strict margins allow the implicit derivative
of this face-restricted problem. Its multipliers stay positive locally, so it
also solves the original constrained convex problem locally.

`IF_i = -N (N.T H N)^-1 N.T (g_i-mean(g))`

`correction = mean[(g_i N)(N.T H N)^-1(N.T g_i)] / n`.

The formula depends on the feasible face, not redundant/rescaled/reordered
constraint rows. At a stable vertex it reduces to threshold-score variance
divided by n times threshold curvature (up to numerical stationarity residual).
This does NOT mean the portfolio can never change under a finite sample change.
Finite changes can cross a face boundary, beyond this local derivative.

## Falsifiers and gates declared before fresh outcomes

- Keep the original optimizer unchanged and check exact identical theta/raw
  values. No fitting or hyperparameter improvement is attempted.
- Require feasibility, global convex gap and reduced curvature at previous
  tolerances; require the original weak-multiplier tolerance 1e-5 as a strict
  positive margin. Threshold-bound cases remain invalid. No ridge or clipping.
- Weak/zero margin can give a genuinely one-sided critical cone and nonlinear
  directional derivative. Reject it; do not substitute a face-linear OIC.
- Test duplicate/positive-rescaled/permuted active normals, an independent
  rank-reduced KKT solve, vertex threshold-only identity, and positive/negative
  probability perturbations at eps 1e-5 and 1e-6 (rtol .004, atol .002).
- Include a weak-margin quadratic counterexample with opposite perturbations:
  its derivatives are not negatives of each other. The gate must reject it.
- Development uses a constructed dominated-asset fixture, seed 2026107998,
  and old seen vertex seeds 2026107101/06/54/58. No development population risk
  is used to choose a correction, tau or tolerance. Old 128-case arrays may be
  audited for regression; no historical aggregate is promoted to fresh evidence.

Pilot protocol retains 64 paired seed clusters, Gaussian/crash, n512, primary
tau=.1, sensitivities .05/.2, and 10,000 cluster bootstrap replicates. New seed
range 2026108000:2026108064 is checked against local observed use before freeze.
Primary is full512 OIC_FACE-minus-raw squared relative smoothed-objective error.
Half A/B raw/OIC/independent controls remain secondary; no model selection.
Any null primary case makes that comparison INCOMPLETE without complete-case
aggregation. No combining old and new samples. Compute gate remains 600 seconds
after development microbenchmark with factor-two margin.

## ASSUMED / NOT_RUN

The finite strict-face certificate does not establish population face recovery
or asymptotic calibration at small sample size. General nonlinear constraints,
weak-face directional OIC, unsmoothed CVaR, discrete bank285 OIC, temporal/market
evaluation, utility and new model search remain outside this run.
