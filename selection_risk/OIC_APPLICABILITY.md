# OIC applicability gate — 2026-10-07, before implementation

Decision: **OIC NOT_RUN for bank285 in this run.** Implement independent splitting;
do not label the historical SE decision penalty as OIC. This is an applicability
decision, not evidence that OIC cannot work for CVaR.

## VERIFIED_SOURCE

Primary source read: Iyengar, Lam and Wang, *Optimizer's Information Criterion:
Dissecting and Correcting Bias in Data-Driven Optimization*, arXiv preprint
[2306.10081v4, 21 July 2025](https://arxiv.org/html/2306.10081v4).
Read the full-text formulation and assumptions in Sections 1–2, Definition 2.7–2.8,
Theorems 2.6/2.9, Appendix 6.1–6.2, Example 6.4 and Appendix 7.3.3; this is not a
line-by-line verification of every proof.

The target is expected out-of-sample objective performance of a data-derived
decision under iid sampling. Example 6.4 includes the CVaR hinge and its optimized
threshold. Nonsmoothness alone does not disqualify CVaR: the population objective
and influence-function expansion require regularity. The correction uses an
estimated influence function. Constraints require active-set projection,
Lagrangian curvature and additional recovery conditions. Numerical solutions
must meet the paper's asymptotic accuracy requirement. The result does not supply
a calibrated VaR/ES pair or a time-series guarantee. These observations are from
the cited version, not an official-code reproduction.

## Repository inference and unresolved assumptions

| Item | Current bank285 | Gate |
|---|---|---|
| Decision | Exact argmin over 285 fixed weights, ties resolved by first index | Discontinuous at switches; no verified differentiable decision map or applicable influence expansion |
| CVaR | Empirical hinge and empirical quantile | Sample Hessian is zero away from knots; inverting it is not population curvature estimation |
| Constraints | Long-only, sum=1, cap=.5, further restricted to finite bank | Continuous constrained formula cannot be copied onto discrete indices |
| Solver | Finite enumeration is exact for its bank | Does not establish continuous KKT, strict complementarity, Hessian recovery or asymptotic solver accuracy |
| Information | 512 past observations, no population parameters during fitting | Satisfiable on iid Gaussian/crash pilot; not established for old Markov case |
| Output | Forecast surface versus selection penalty | Optimism-adjusted objective is not an arbitrary ES forecast paired with the old VaR |

**ASSUMED, NOT PROVED:** Gaussian/crash DGP draws are iid conditional on the
seed-defined parameters. Independent halves can therefore evaluate a decision
and threshold locked on the other half. Finite moments hold for these Gaussian
mixtures. The pilot tests software and bias/variance behavior, not an OIC theorem.

The split evaluator estimates `E[v_A + (L(w_A)-v_A)+ / .05]` with both `w_A` and
`v_A` locked on A. Conditional independence makes its sample mean unbiased for
that frozen objective. This objective is at least population ES; their difference
is threshold estimation error. Recomputing a quantile on B instead estimates ES
with finite-sample quantile bias and is reported separately. No B outcome chooses
a model or portfolio. Swapping A/B gives a two-fold policy-performance diagnostic,
not the evaluation of the full-512 selected portfolio.

## PROPOSED / NOT_RUN

A separate continuous CVaR benchmark needs a common capped simplex for every
compared method, population/estimated curvature at the hinge, active-set and KKT
receipts, influence-function derivation and consistency audit. If smoothing is
used, declare its scale and sensitivity before outcomes. Continuous regret must
stay separate from bank285 regret. That benchmark, OIC correction, temporal
extension, reserve utility and market assessment are **NOT_RUN** here.
