# Independent generation: conditional post-selection tail risk

**Stage:** independent generation, before external literature search

**Date:** 2026-10-08 (Asia/Ho_Chi_Minh)

**Contributor/origin:** `independent_a`, AI-assisted; generated from the focal
question and the frozen repository constraints, without exposing another
agent's ideas. These are proposals, not findings or novelty claims.

## Scope held fixed

Focal question: *What narrowly defensible method or theory could improve
conditional post-selection tail-risk assessment for dependent observations,
beyond OIC, sample splitting, HMM/GARCH/FHS, DRO, and standard calibration?*

The proposed method must receive only the common past-512 information window,
use the same locked portfolio set/constraints, make no test-based model
selection, and never use an unobserved latent state. The target is a
conditional next-step tail-risk quantity or a selection-aware reserve; a
single realized loss is not treated as ES truth. The current HMM improvement in
the correctly specified Gaussian Markov simulation is treated as a standard
control, not a novelty premise.

## Independent ideas

### A — Predictable-transport information criterion (PT-OIC)

**Idea.** Extend the optimizer's information correction to a one-step target
under serial dependence by adding a future-score/past-score transport term. The
technical object is the cross-covariance created because the next loss is not
independent of the data that selected the portfolio. This is intended as a
small-sample asymptotic correction for a smooth continuous benchmark, with the
finite bank reported separately.

Let `ell_t(theta)` be a differentiable tail objective (for example, the
predeclared smoothed CVaR objective), `s_t = grad ell_t(theta_0)`,
`H = E[grad^2 ell_t(theta_0)]`, and
`theta_hat = argmin_theta T^{-1} sum_t ell_t(theta)`. Define the long-run
score covariance and future-score transport matrix

```
Omega = sum_h Cov(s_0, s_h),
C_+   = sum_{j>=0} E[s_{T-j} grad ell_{T+1}(theta_0)^T].
```

Under stationary mixing, an interior identifiable optimum, finite fourth
moments, and a valid estimator of the conditional score law, a first-order
candidate correction is

```
PT-OIC_T = T^{-1} { tr(H^{-1} Omega) - tr(H^{-1} C_+) }.
```

The first term is the dependent-data analogue of the usual optimism term; the
second term is zero for an independent future and transports the correction to
the conditional next-step target. In a real implementation `Omega`, `C_+`,
and `H` would be estimated from past-only, block/cross-fitted score residuals
with settings frozen before the held-out assessment. The sign and terms must
be derived and unit-tested on a scalar AR(1) and a two-state Gaussian Markov
calculation before calling this more than a conjectured expansion.

**Predicted observation.** When the same marginal distribution has different
serial persistence, PT-OIC should differ from iid OIC in the direction and
magnitude predicted by `C_+`; it should reduce conditional squared relative
error for the selected portfolio without changing the common risk surface.

**Assumptions.** Stationarity or locally stationary dependence; a smooth
interior optimizer; a tail objective with a valid gradient/Hessian; enough
past data to estimate lagged score covariance; a conditional forecasting
model for the score transport that is fit without future outcomes. No latent
state or oracle parameters are available to the method.

**Falsifiers.** (i) In an iid DGP the correction must reduce to the frozen OIC
term; failure falsifies the derivation. (ii) In an AR(1) or Markov DGP with
known finite-sample simulations, the signed transport term must not worsen the
predeclared primary metric against dependent OIC/HAC and blocked split
controls. (iii) If `C_+` is estimated noisily, the method may be no better than
OIC; a null or adverse result is retained. (iv) Discrete bank argmin,
active-set changes, drift, or non-smooth hinge behavior can invalidate the
expansion; a failure there is a boundary, not evidence for smoothing away the
problem.

**Why it might be distinct.** The proposed object targets dependence between
the selector's score and the *next* loss, rather than only replacing iid
variance by HAC or validating a conditional forecaster. This distinction is a
hypothesis pending the literature check; time-series TIC, dependent
information criteria, and selective-inference work may already contain it.

### B — State-indexed selection shadow (SISS)

**Idea.** Estimate selection optimism with causal, contiguous block-delete
perturbations, but condition the perturbation effect on the current observed
history. For each past block `b`, refit the selector on the remaining past,
record `Delta_b = J_hat(w_hat^{(-b)}) - J_hat(w_hat)`, and map the block's
effect to the current context `z_T` using a predeclared kernel or a finite
partition of observable lag summaries. The proposed reserve is the
context-weighted average of `Delta_b`, with the same conditional tail model
used to score every common portfolio.

```
R_SISS(z_T) = sum_b K(z_T,z_b) Delta_b / sum_b K(z_T,z_b),
w_hat^SISS = argmin_w { J_hat(w) + R_SISS(z_T,w) }.
```

`Delta_b` is recomputed as a portfolio-wise surface so the correction cannot
be credited to a different selected loss series. Blocks are contiguous,
predeclared, and only earlier-than-assessment contexts are used. The intended
mechanism is that selection optimism is larger in the observable volatility or
tail context currently being forecast, while a global HAC penalty averages
across incompatible regimes.

**Predicted observation.** In a stationary but heteroskedastic Markov process,
context weighting should improve conditional selected-risk error over global
block jackknife/HAC and over rolling sample splitting at equal information.
The gain should disappear when block effects are context-independent.

**Assumptions.** Observable lag summaries are sufficiently predictive of the
selection-effect heterogeneity; block-delete perturbations approximate the
selector's influence; kernel bandwidth/partition is frozen in development;
contexts do not use future returns or latent states.

**Falsifiers.** (i) Randomly permuting context labels should remove the gain.
(ii) On iid data SISS should not beat OIC or ordinary delete-a-block jackknife.
(iii) If changing block length or partition reverses the result, the method is
an unstable tuning procedure. (iv) If a conditional HMM/GARCH/rolling split
already matches SISS, this candidate adds no defensible method contribution.

**Why it might be distinct.** It treats post-selection optimism as a
context-dependent functional and keeps the portfolio risk surface common. The
likely collapse is to state-conditioned cross-validation, delete-a-group
jackknife, or regime-weighted bootstrap already present in the literature.

### C — Tangent-cone tail selection confidence sequence (TC-TSCS)

**Idea.** Replace a point optimism correction with a simultaneous, dependent
confidence reserve for the selected portfolio. Construct a block-multiplier
process for the tail score over the feasible portfolio tangent cone at
`w_hat`; use its conditional quantile as a reserve that remains valid after
the data-driven argmin. The reserve is evaluated at the selected `w_hat`, but
the multiplier supremum is over local feasible directions, so selection is
accounted for without a held-out test set.

For a tail score `psi_t(w,q)` and selected portfolio `w_hat`, let
`T_W(w_hat)` be the feasible tangent cone and `xi_b` mean-zero multipliers on
predeclared contiguous blocks. A candidate one-step reserve is

```
r_T(delta) = q_{1-delta} [ sup_{v in T_W(w_hat), ||v||_H<=1}
       T^{-1/2} sum_b xi_b sum_{t in block b} v^T psi_t(w_hat,q_hat) ],
ES_upper(w_hat) = ES_hat(w_hat) + r_T(delta).
```

The multiplier dependence, block length, and cone norm are fixed before
assessment; an optional predictable state forecast shifts the center but does
not alter the confidence event. The claim to test is coverage of a
conditional-next-step tail functional uniformly over the local selection
directions, under a beta-mixing or martingale approximation condition.

**Predicted observation.** At fixed nominal coverage, TC-TSCS should maintain
coverage after selection more reliably than a point OIC correction and use a
smaller reserve than a global supremum over all portfolios. It should show no
advantage when the optimizer is fixed in advance or when dependence is iid.

**Assumptions.** A valid tail-score representation; feasible-set tangent cone
and local curvature are estimable; block multiplier approximation holds under
the chosen dependence class; conditional coverage target is defined before
outcomes; finite-tail moments and anti-concentration conditions hold.

**Falsifiers.** (i) Empirical coverage below the predeclared tolerance on
dependent test paths falsifies the claimed guarantee. (ii) Coverage failure
only after active-set changes or heavy tails marks the boundary and cannot be
hidden by changing delta. (iii) If a uniform conformal/empirical-likelihood
bound or PAC-Bayes bound gives the same reserve with fewer assumptions, TC-TSCS
is not a useful new method. (iv) With a fixed portfolio, the tangent-cone
term should reduce to an ordinary dependent tail confidence bound.

**Why it might be distinct.** It targets post-selection *coverage/reserve*
rather than expected optimism, and it exposes optimizer geometry through the
tangent cone. It may nevertheless be a repackaging of selective inference,
simultaneous empirical-process bounds, or dependent conformal risk control.

## Initial independent-round decision status

No candidate is selected at this stage. A, B, and C are `IDEA` only; all
equations are hypotheses requiring derivation and finite checks. Search must
test whether each mechanism is already a named method, whether the proposed
conditional target is identifiable from past-only information, and whether a
simple baseline dominates. The post-search round must preserve rejected ideas
and record any revisions rather than retroactively presenting them as
literature-derived.

## Post-search target clarification

The relevant conditional target is a terminal, observed-history target. Let
`F_T = sigma(Y_1, ..., Y_T)` be the information available at the decision time,
let `theta_hat_T = A(Y_1:T)` be the selected parameter or portfolio, and let
`rho_{T+1}` be the next-period loss. The target for this review is

```
R_{T+1}(theta_hat_T | F_T) = E[rho_{T+1}(theta_hat_T) | F_T].
```

This is a random conditional quantity after the history has been observed. It
is different from an integrated contextual target of the form
`E_Z E_{xi|Z}[h(x*(theta,Z);xi)]`, where a fresh iid context is integrated out
and the decision rule is evaluated over that context distribution. The latter
is the target used by the contextual extension in OIC v4 section 3.4. It is a
close threat to any generic claim about context-aware OIC, but it does not by
itself establish a result for a terminal next-step conditional ES target.

Likewise, a covariance or long-run covariance penalty is not treated as a new
mechanism here. Conditional covariance penalties, one-step predictive
criteria, state-space pseudo-DIC, and dependence-aware resampling already
cover those ingredients in adjacent settings. The possible remaining gap is
the exact combination of (i) a same-history selected portfolio, (ii) a
terminal next-period conditional tail-risk target, and (iii) a finite-window,
past-only correction whose estimand is explicit. The bounded search located no
direct source proving that combination is new; this is a gap report, not a
novelty claim.

## Adversarial primary-source search

The search used ten focused batches and retained primary papers, official
proceedings, publisher pages, and author or arXiv versions. The query log is in
`../a_queries.json`. Access labels below describe the version actually
inspected, not the existence of an abstract somewhere else.

| Source and access | Actual overlap | Narrow remaining gap, if any |
| --- | --- | --- |
| **OIC v4**, arXiv `2306.10081v4`, [HTML](https://arxiv.org/html/2306.10081v4), [PDF](https://arxiv.org/pdf/2306.10081); open full text, arXiv revision dated 2025-07-21 | Risk-OIC derives optimizer optimism for iid samples, and section 3.4 derives Context-OIC for iid `(z, xi)` pairs. CVaR portfolio allocation is among the examples. This directly covers generic optimizer-aware covariance corrections and an integrated contextual target. | No direct terminal observed-history, serially dependent, one-step conditional ES result was located in this source. A claim that merely replaces iid covariance by a long-run covariance or calls a fresh context “conditional” would overlap. |
| **Safken & Kneib**, *Conditional covariance penalties for mixed models*, DOI [10.1111/sjos.12437](https://doi.org/10.1111/sjos.12437); Wiley full text was accessible | Conditional prediction error can condition on random effects or clusters; conditional covariance penalties, bootstrap, cross-validation, and Stein-type estimates are all established. This is a direct threat to “conditional covariance penalty” as a novelty label. | The setting is mixed-model prediction rather than same-history portfolio selection with a next-period conditional CVaR/ES target. The gap is a problem-and-estimand combination, not the penalty idea. |
| **Ing & Yu**, *A New Class of One-step Ahead Predictors*, DOI [10.1111/1467-9892.00313](https://doi.org/10.1111/1467-9892.00313); publisher abstract/metadata, full article not freely inspected | One-step predictive risk under dependent autoregressive data and finite-sample predictor corrections are close to the scalar quadratic special case of PT-OIC. | No evidence was located for a portfolio ES selector or a same-sample tail-score correction. The scalar mean or squared-error extension must therefore be treated as an established neighboring baseline, not novelty. |
| **Hurvich & Tsai**, *A corrected Akaike information criterion for autoregressive model selection*, DOI [10.1093/biomet/76.2.297](https://doi.org/10.1093/biomet/76.2.297); Oxford abstract, article access marked purchase | Finite-sample prediction-criterion correction under serial autoregressive dependence is established. | It does not supply the terminal conditional CVaR/ES portfolio-selection construction. Any finite-window correction still needs to beat this type of baseline in a matched quadratic forecast check. |
| **Millar & McKechnie**, *A pseudo-DIC for Bayesian state-space models*, DOI [10.1111/biom.12237](https://doi.org/10.1111/biom.12237); Oxford abstract/summary, article access marked purchase | Pseudo-DIC targets one-step-ahead predictive fit conditional on the previous state in state-space models. This is a close threat to state-conditional selection language. | The paper does not address post-selection ES/CVaR or the optimizer-induced tail-risk gap for a locked portfolio bank. |
| **Patton, Ziegel & Chen**, *Dynamic semiparametric models for expected shortfall and value-at-risk*, [arXiv 1707.05108](https://arxiv.org/abs/1707.05108), [journal DOI](https://doi.org/10.1016/j.jeconom.2018.10.008); arXiv/author full text and journal record | Joint dynamic VaR/ES scoring and serially dependent tail forecasting are established, including GARCH-style conditional tail models. This is a direct forecasting baseline for conditional tail risk. | The models score a specified forecast; they do not provide an optimizer-aware correction for selecting a portfolio/model on the same past history. Combining their score with a penalty remains a proposed experiment, not a prior-art-free theorem. |
| **Xu & Xie**, *Sequential Predictive Conformal Inference for Time Series*, [arXiv 2212.03463](https://arxiv.org/abs/2212.03463); open full text and ICML version | Dependence-aware sequential calibration and asymptotic conditional coverage for future time-series predictions are established. This overlaps the operational goal of conditional validity. | SPCI wraps a fixed point predictor and does not establish same-history optimizer selection for ES. It is a required calibration comparator for any reserve claim. |
| **Farinhas et al.**, *Non-Exchangeable Conformal Risk Control*, [arXiv 2310.01262](https://arxiv.org/abs/2310.01262), [ICLR 2024 paper](https://proceedings.iclr.cc/paper_files/paper/2024/file/de04896f011beff76c91e094f72727f4-Paper-Conference.pdf); open full text | Controls expected bounded monotone loss under nonexchangeability using relevance weights and total-variation drift terms, including time-series settings. This directly threatens SISS and TC-TSCS as generic dependence-aware risk-control ideas. | The guarantee controls a monotone loss or reserve construction, rather than the conditional ES forecast error of a portfolio chosen from the same history. The gap is narrow and must be stated as such. |
| **Angelopoulos et al.**, *Conformal Risk Control*, [arXiv 2208.02814](https://arxiv.org/abs/2208.02814); open full text | Expected monotone-loss control is a prior art for the reserve/coverage side of C. | The base result is not a same-history optimizer correction under serial dependence; it supplies a baseline and a falsifier, not a novelty license. |
| **Ye et al.**, *Finite-Sample Conformal Inference for VaR and ES*, [Mathematics 14(15), 2847](https://www.mdpi.com/2227-7390/14/15/2847); open HTML/PDF, 2026 journal article | A joint VaR/ES black-box forecast is combined with nonexchangeable conformal risk control, total-variation or swap bounds, beta-mixing calibration costs, and heavy-tail transfer. This is a particularly close threat to a conformal conditional ES-reserve proposal. | The paper's guarantee is on a normalized exceedance-severity surrogate and does not directly claim same-sample portfolio-optimizer post-selection error control. Any remaining gap is the selection mechanism and estimand, not conformal calibration itself. |
| **Lee et al.**, *Exact post-selection inference, with application to the lasso*, [arXiv 1311.6238](https://arxiv.org/abs/1311.6238); open full text | Selective inference after a data-dependent optimization event is established. It threatens a generic “tangent cone makes post-selection inference new” claim. | The Gaussian selective-inference event is not a serial conditional ES target and does not supply a dependent tail-risk reserve. C would need a theorem and a clear improvement over dependent conformal/empirical-process bounds. |

The source set therefore leaves only a narrow, unverified intersection. No
source in this bounded search was found that simultaneously uses a terminal
observed-history conditional ES target, a same-history selected portfolio, and
the finite-window transport correction below. That absence is evidence about
the search boundary only; it is not evidence of novelty.

## Finite analytical falsifier for idea A

The infinite-lag PT-OIC expression is too optimistic as a finite-window test
even in a one-dimensional Gaussian case. Use the stationary AR(1) process

```
X_t = phi X_{t-1} + eps_t,       Var(X_t) = v,       |phi| < 1,
ell_t(theta) = 0.5 (theta - X_t)^2,
theta_hat_T = T^{-1} sum_{t=1}^T X_t.
```

For this special case the terminal conditional target is known exactly:

```
r_T = E[(theta_hat_T - X_{T+1})^2 | F_T]
    = (theta_hat_T - phi X_T)^2 + Var(eps_{T+1}),
```

so a claimed conditional correction can be falsified without training a tail
model. Its unconditional train-to-next-step gap is also exact:

```
Delta_T(phi)
 = v/T^2 [ T + 2 sum_{h=1}^{T-1} (T-h) phi^h ]
   - v/T sum_{h=1}^{T} phi^h.
```

Writing `s_t = partial_theta ell_t(theta_0)`, `H = E[partial^2_theta
ell_t(theta_0)]`, and

```
Omega_T = T Var(T^{-1} sum_t s_t),
C_T     = sum_{t=1}^T Cov(s_t, s_{T+1}),
FW-PT_T = T^{-1} { tr(H^{-1} Omega_T) - tr(H^{-1} C_T) },
```

gives `Delta_T` in the quadratic case. The infinite-lag expression
`v/[T(1-phi)]` is the large-`T` limit of this difference when `v` is the
stationary variance. It is not the finite-window answer.

The executed exact check (with `v=1`) gave:

| `T` | `phi` | exact `Delta_T` | infinite-lag `v/[T(1-phi)]` | excess of infinite-lag |
| ---: | ---: | ---: | ---: | ---: |
| 32 | 0.0 | 0.031250000000 | 0.031250000000 | 0 |
| 32 | 0.5 | 0.058593750008 | 0.062500000000 | 0.00390625 |
| 32 | 0.9 | 0.152411758085 | 0.312500000000 | 0.16008824 |
| 128 | 0.5 | 0.015380859375 | 0.015625000000 | 0.00024414 |
| 128 | 0.9 | 0.067138784887 | 0.078125000000 | 0.01098622 |
| 512 | 0.5 | 0.003890991211 | 0.003906250000 | 0.00001526 |
| 512 | 0.9 | 0.018844604492 | 0.019531250000 | 0.00068665 |

This is a concrete rejection gate. A finite-window or estimated transport
correction fails idea A if it cannot recover the exact `Delta_T` within a
predeclared tolerance on this Gaussian AR(1) family, or if its corrected
`bar{ell}_T + correction` has larger conditional-target MSE than ordinary
finite-sample predictive criteria. A second gate uses the displayed `r_T` on
the same paths and requires the proposed conditional risk estimate to be
evaluated against `r_T`, not against a realized single loss. The check is
deliberately scalar and non-tail: failure here rejects a claimed general
conditional ES method before any expensive training; passing it proves only
an algebraic prerequisite.

## Post-search verdicts and minimum experiment

**A, revised to FW-PT:** A possible candidate survives only as a narrowly
specified finite-window terminal transport correction for a smooth tail-score
objective. Its contribution would have to be the explicit terminal
observed-history estimand and a past-only estimator of `C_T` that improves
conditional next-step ES assessment for a locked portfolio bank. The finite
window is essential: the AR(1) check rejects simply substituting an
infinite-lag HAC/long-run covariance. Even here, OIC, conditional covariance
penalties, one-step criteria, and dynamic ES scoring are established
ingredients. The nontriviality gate is strict: if the proposed derivation is
only Säfken-Kneib's conditional optimism/covariance penalty applied to a
temporal cluster, or an ordinary one-step predictive criterion with a tail
score substituted for squared error, A is rejected as a known-baseline
adaptation. Status: `PROPOSED`, not novel or validated.

**B, SISS:** The context-indexed block-delete selector is useful as a control
but does not survive the novelty screen. Contiguous block deletion, rolling or
conditional cross-validation, state-space pseudo-DIC, and nonexchangeable
conformal risk control already supply the mechanism. A state label or a
weighting rule would not make the method new without a theorem tied to the
terminal conditional ES target and a strict finite-sample advantage. Status:
`BASELINE/CONTROL`, likely collapses to known dependence-aware resampling.

**C, TC-TSCS:** The tangent-cone reserve is also a control or extension
direction, not a surviving new method. Selective inference, multiplier
empirical-process bounds, and conformal risk control cover the components.
For a fixed portfolio the tangent-cone term should reduce to an ordinary
dependent tail bound; if it does not, the derivation is suspect. Status:
`BASELINE/CONTROL`, likely collapses to selective/conformal calibration.

The minimum meaningful experiment for A is therefore small and fully matched:

1. Freeze the existing past-512 information and locked portfolio bank. Add no
   latent state, test-based model selection, or future information.
2. First run the scalar AR(1) analytic gate above for `phi` in `{0, .5, .9}`
   and several `T`, comparing finite FW-PT, infinite-lag PT/OIC, HAC, and the
   direct predictive baseline against the exact `r_T` and `Delta_T`.
3. Only if that gate passes, use synthetic Markov and stochastic-volatility
   paths with a predeclared train/selection/test split fixed across methods.
   Compare common-target forecast error, selected decision quality, and reserve
   utility separately. Use Patton-Ziegel-Chen dynamic ES, the standard HMM
   already executed, rolling/block CV, and nonexchangeable conformal risk
   control as controls.
4. Report paired paths and uncertainty over independent simulated histories.
   A lower error on the selected portfolio alone is not evidence of a better
   forecaster; the target must be common across methods.

The strongest candidate from this independent round is therefore **FW-PT as a
conditional finite-window transport formulation**, subject to the scalar
falsifier and the literature threats above. The claim should remain at
`PROPOSED / no direct evidence located`; no established novelty, peer-review,
or real-market result follows from this review.

## Append-only arithmetic and estimand clarification

The earlier display of `r_T` wrote the conditional expectation of the
*unscaled* squared error, while the stated loss is
`ell_t(theta)=0.5*(theta-X_t)^2`. The target for that stated loss is therefore

```
r_T^(1/2) = E[ell_{T+1}(theta_hat_T) | F_T]
           = 0.5*((theta_hat_T - phi X_T)^2 + v*(1-phi^2)).
```

The `Delta_T` table is already on the half-loss scale, so its iid value
`v/T` is consistent with this corrected convention.

There is a stronger finite Gaussian check than matching the mean gap. Let
`X=(X_1,...,X_T)'`, `u=1/T` times the all-ones vector, `e_T` be the final
coordinate vector, `a=u-phi e_T`, and

```
A = 0.5*(a a' - I/T + u u'),
c = 0.5*v*(1-phi^2),
Sigma_ij = v*phi^|i-j|.
```

Then the realized train-to-next-step half-loss gap is the random quadratic
form

```
G_T = E[ell_{T+1}(theta_hat_T) | F_T] - bar{ell}_T(theta_hat_T)
    = X' A X + c,
E[G_T] = tr(A Sigma) + c = Delta_T,
Var(G_T) = 2 tr(A Sigma A Sigma).
```

The pure-Python finite check verified `E[G_T]=Delta_T` to numerical precision
for `(T,phi)=(32,0),(32,.5),(32,.9),(128,.9)`, with positive variances
`0.015625`, `0.049401177288`, `0.199682819024`, and `0.319287525665`,
respectively. Thus even an oracle that knows the exact finite expected
correction `Delta_T` cannot recover the realized terminal conditional gap: the
gap has nonzero history-dependent variation. FW-PT is consequently a
deterministic correction for an integrated expected bias, not a terminal
conditional risk estimator. It must be retained as a falsifier/control unless a
future method adds a separately justified conditional transition or
calibration component. If that component reduces to the existing
Säfken-Kneib conditional covariance penalty, the novelty claim is rejected.

This clarification supersedes the earlier shorthand calling FW-PT the
strongest *conditional* candidate: after the quadratic-form check, the
strongest independent result is the no-go boundary itself. FW-PT is retained
as the most informative integrated-bias control and falsifier; a genuinely
conditional method remains `NOT_ESTABLISHED`.
