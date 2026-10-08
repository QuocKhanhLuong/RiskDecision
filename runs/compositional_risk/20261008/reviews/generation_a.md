# Independent composition generation A

**Date:** 2026-10-08
**Origin:** AI-assisted independent generation, written before the new
literature search
**Focal question:** What useful, falsifiable compositional contribution can be
built around learned conditional tail risk, selection or decision quality, and
limited information, given the earlier negative novelty gates?

This round deliberately searches for a useful interaction of modest known
components. It does not assume that the interaction is a new theory. Every
candidate uses the same observed history `F_T`, the same locked portfolio bank
`J`, and no latent-state oracle, future data, or test-based model selection.
The three components below were recorded before any new external search.

## A. Pairwise Conditional Tail-Margin Gate (PCTMG)

For every locked portfolio `j`, fit the same learned conditional tail model
from `F_T` and obtain

```
r_hat_j,T = ES_alpha(L_{j,T+1} | F_T),
d_hat_jk,T = r_hat_j,T - r_hat_k,T.
```

Estimate a one-sided dependence-aware error radius `b_jk,T(delta)` for the
*pairwise* contrast, using a predeclared block or sequential calibration rule.
Select `j` only when it is certified against every alternative:

```
U_jk,T = d_hat_jk,T + b_jk,T(delta) <= 0  for every k != j.
```

If no portfolio is certified, retain a predeclared incumbent or abstain. The
decision utility then has three separately reported terms: common-target tail
forecast error, selected decision quality, and the cost of abstention or
incumbent fallback.

**Known components.** Conditional VaR/ES forecasting and proper tail scoring;
pairwise forecast comparison; block or conformal uncertainty under dependence;
and reject-option or selective prediction are each established components.

**Interaction that might add value.** The uncertainty object is attached to
the *ordering used for the decision*, rather than to each ES forecast in
isolation. Shared forecast errors can cancel in `d_hat_jk,T`, and abstention
turns an uncertain tail forecast into a controlled decision. This targets
selected decision regret under limited information while retaining the same
conditional tail model.

**Assumptions.** The score or contrast process is stationary enough for the
chosen block rule; the one-sided radius has its stated conditional or marginal
coverage; the fallback utility is fixed before observing the test path; and
the portfolio bank is locked before evaluating the gate.

**Strongest matched control.** Use the identical learned conditional ES
surface with pointwise `argmin_j r_hat_j,T`; then compare a predeclared
block-bootstrap or split-sample winner gate. This isolates the value of
pairwise uncertainty plus abstention from the forecaster.

**Cheap mathematical falsifier.** Let the true pairwise ES difference be
`d>0` (portfolio A is worse than B) and suppose the estimated contrast error is
exactly `Z ~ N(0,s^2)`. With `b=z_{1-delta}s`, certifying the wrong A requires
`d+Z+b <= 0`, so

```
P(wrong A is certified) = Phi(-d/s - z_{1-delta}).
```

For `d=0`, the two symmetric false-certification probabilities are at most
`delta` each. A claimed gate that exceeds this exact probability, or that
beats the point selector on true regret in a no-signal equal-risk DGP without
paying abstention cost, is rejected. The temporal version uses the exact
finite-sample long-run variance of an AR(1) contrast; no fitted tail model is
needed for this first check.

**Initial status:** `IDEA`; likely useful as a decision-safety composition,
with novelty depending entirely on whether the pairwise conditional tail
ordering and fallback utility are already covered by selective/conformal
prediction literature.

## B. Common-Mode Tail Contrast (CMTC)

Model the portfolio-loss vector with a predictable common tail factor and
portfolio-specific residuals:

```
L_{j,T+1} = m_{j,T} + b_{j,T} Z_{T+1} + e_{j,T+1},
d_jk,T = (m_j-m_k) + (b_j-b_k) ES_alpha(Z_{T+1}|F_T)
          + ES_alpha(e_j|F_T) - ES_alpha(e_k|F_T).
```

Estimate the pairwise contrast with a shared-factor control variate or an
orthogonalized joint VaR/ES score, rather than fitting and ranking unrelated
portfolio tails. Select using the resulting contrast uncertainty and report
individual forecast quality separately.

**Known components.** Factor or multivariate volatility models; joint VaR/ES
scoring; control variates and orthogonal moments; and paired forecast
comparisons are established.

**Interaction that might add value.** If portfolios share a large predictable
tail factor, common-mode estimation noise can cancel in the contrast even when
individual ES forecasts remain noisy. That could improve ranking and selected
decision quality with the same `F_T`, without pretending that an improved
ranking is an improved absolute ES forecast.

**Assumptions.** The factor is learned only from observed histories; residual
tail scores remain valid after factor estimation; factor loadings are stable
over the decision window; and the contrast score accounts for estimation of
the common factor.

**Strongest matched control.** Use the same multivariate tail forecaster but
rank portfolios from independently fitted marginal ES forecasts. A paired
block bootstrap of the loss-difference process is the second control.

**Cheap mathematical falsifier.** In the exact Gaussian construction
`L_A=Z+e_A`, `L_B=Z+e_B`, with the same loading and a common `Z`, the true
contrast contains no `Z` term. The contrast estimator should reduce to the
residual process. If CMTC reports a gain when the common factor already
cancels exactly, or its radius is smaller than the residual-only oracle, the
factor adjustment is leaking information or double-counting cancellation.
If the residuals are also identical, any nonzero selected advantage is
strictly impossible.

**Initial status:** `IDEA`; most likely a control-variate or paired-forecast
repackaging unless the decision-specific tail contrast has a proved finite-
sample benefit.

## C. Information-Budgeted Tail Decision (IBTD)

Keep the learned conditional tail surface but constrain how much the final
portfolio index can adapt to the limited history. Given a prior `pi` over the
locked bank, choose a randomized decision rule `q_T` by

```
min_{q in Delta(J)}  sum_j q_j [r_hat_j,T + u_j,T]
subject to           KL(q || pi) <= kappa,
```

where `u_j,T` is a calibrated tail-risk uncertainty reserve. A deterministic
deployment can use the posterior mean or certify a single index only when its
margin exceeds the uncertainty and information-budget penalty. The budget is
fixed before the held-out evaluation.

**Known components.** PAC-Bayes or mutual-information generalization bounds;
Gibbs or entropy-regularized selection; DRO uncertainty sets; and conditional
tail forecasting are established.

**Interaction that might add value.** The information budget is attached to
the decision index, not imposed as a blanket restriction on the conditional
tail forecaster. It offers an explicit knob between a stable incumbent and an
aggressive tail-risk selector when only `F_T` is available. The proposed
benefit is decision regret control, not a claim that the conditional ES model
itself is better.

**Assumptions.** The prior and `kappa` are fixed without looking at the test
path; the uncertainty reserve has a valid risk interpretation; and randomized
or fallback decisions are operationally allowed.

**Strongest matched control.** Compare pointwise argmin, a standard DRO
portfolio, and the same Gibbs rule with `u_j,T=0`, all using the identical
conditional tail surface and information history.

**Cheap mathematical falsifier.** Under a no-signal DGP with equal true tail
risk for all `j`, the true decision risk is invariant to `q_T`; for two
portfolios with `r_A=r_B=r`, any claimed strict reduction in true risk from
the information budget is impossible. At `kappa=0`, `q_T=pi` exactly. For
independent Gaussian score noise, the unconstrained point selector has
expected empirical minimum `r-sigma E[max_j Z_j]` but true risk remains `r`;
the composition must not mistake that optimism for a true decision gain.

**Initial status:** `IDEA`; probably collapses to PAC-Bayes/DRO or entropy-
regularized decision making unless the conditional-tail-specific regret bound
adds something measurable.

## Initial choice for bounded search

PCTMG is the strongest composition to audit first. Its proposed interaction
is concrete and falsifiable: pairwise conditional tail uncertainty is used to
certify a decision ordering and to trigger abstention, while the learned tail
surface and portfolio bank remain fixed. The search will test whether this is
already a named selective/conformal, confidence-sequence, forecast-comparison,
or risk-sensitive portfolio procedure. It will not search CMTC or IBTD broadly
unless PCTMG is clearly ruled out.

No candidate is selected as novel at this stage. The next section will be
appended only after the bounded primary-source search; it must preserve any
rejection of PCTMG rather than relabeling a known component as an interaction
contribution.

## Bounded primary-source search for PCTMG

The post-generation search used eight focused queries, retained primary papers
or official proceedings, and did not run a model or reread project benchmark
outcomes. The associated query log is `queries_a.json`. The most relevant
sources and the access level actually inspected are below.

| Source and access | Actual overlap | Remaining gap or limitation |
| --- | --- | --- |
| **Bai & Jin, Conformal Selective Prediction with General Risk Control**, [arXiv:2603.24704](https://arxiv.org/abs/2603.24704); open arXiv HTML/PDF, 2026 preprint | SCoRE combines selection or abstention with finite-sample conformal risk control for a user-defined bounded continuous risk. This is a direct threat to presenting “risk gate plus abstention” as a new interaction. | It selects test cases to trust a trained model under exchangeability; it does not rank a locked portfolio bank by a dependent conditional ES contrast. No portfolio or serial-dependence theorem was located in the inspected version. |
| **Xu, Guo & Wei, Selective Conformal Risk Control**, [arXiv:2512.12844](https://arxiv.org/abs/2512.12844); open arXiv HTML/PDF, v2 preprint | SCRC explicitly has a selection stage followed by conformal risk control on accepted cases, with exact exchangeable and PAC-style variants. This overlaps PCTMG's accept-or-abstain structure. | The selected unit is a prediction case, not the best among portfolios, and the source is exchangeable rather than a dependent conditional-tail ranking procedure. |
| **Bao et al., CAP: A General Algorithm for Online Selective Conformal Prediction with FCR Control**, [JMLR 26 (2025), 24-0452](https://www.jmlr.org/beta/papers/v26/24-0452.html); official open HTML/PDF | CAP handles post-selection predictive inference online, constructs calibration after an adaptive pick, and proves selection-conditional coverage plus long-run FCR extensions. This is the closest temporal selective-calibration threat. | CAP calibrates an interval after an adaptive pick of a current individual. It does not select the minimum conditional ES among a locked portfolio bank or use pairwise ES regret margins. |
| **Howard & Ramdas, Sequential estimation of quantiles with applications to A/B-testing and best-arm identification**, [arXiv:1906.09712](https://arxiv.org/abs/1906.09712), [Bernoulli DOI](https://doi.org/10.3150/21-BEJ1388); open full text and published record | Uniform confidence sequences for quantiles and approximate best-quantile arm selection are established. This directly covers the margin-certification idea in a simpler ranking-and-selection setting. | The guarantee is built for iid streams and bandit arm sampling. PCTMG would need to justify a dependent, same-history, learned conditional ES contrast; merely replacing a mean or quantile by ES is not a new theorem. |
| **Bauer & Kazak, Conditional Method Confidence Set**, [arXiv:2505.21278](https://arxiv.org/abs/2505.21278); open arXiv HTML/PDF, preprint only | CMCS selects a subset of forecasting methods with equal predictive ability conditional on an economic regime and demonstrates an Expected Shortfall application. This is a direct threat to conditional risk-model selection language. | It is a test-based confidence-set procedure for forecasting methods, whereas the present protocol forbids test-based model selection and concerns portfolio decision quality. The distinction is a constraint and estimand, not a claim that conditional selection is new. |
| **Amendola et al., Combining VaR and ES forecasts via the Model Confidence Set**, [arXiv:2406.06235](https://arxiv.org/abs/2406.06235); open arXiv HTML/PDF, v2 preprint | Uses a joint VaR-ES score and MCS to select or combine tail-risk forecasts under estimation and misspecification uncertainty. This covers tail-score model comparison and combination. | It evaluates or combines forecasts, not a same-history locked portfolio ordering with a reject option and pairwise decision-regret target. No dependent conditional portfolio-selection guarantee was located. |
| **Sun & Cheng, Bootstrapping the Expected Shortfall**, [DOI 10.4236/tel.2018.84046](https://doi.org/10.4236/tel.2018.84046); official publisher HTML/PDF accessible | Establishes moving-block bootstrap asymptotics for ES under stationary strong mixing. This is prior art for constructing a dependence-aware ES uncertainty radius. | It estimates the sampling distribution of ES and does not address conditional learned forecasts, selection among portfolios, or abstention. |
| **Lan, Nelson & Staum, A Confidence Interval Procedure for Expected Shortfall Risk Measurement via Two-Level Simulation**, [DOI 10.1287/opre.1090.0792](https://doi.org/10.1287/opre.1090.0792); publisher record/abstract inspected, full article access not verified | Combines ES confidence intervals with ranking-and-selection ideas in a simulation setting. This is a direct conceptual threat to “ES interval plus winner selection.” | Two-level simulation supplies fresh scenarios and is not the same as estimating a next-period conditional ES from one dependent history. Full-text details were not available in this audit. |
| **Lee et al., Exact post-selection inference, with application to the lasso**, [arXiv:1311.6238](https://arxiv.org/abs/1311.6238); open arXiv full text | Shows that inference must account for a data-dependent selection event. It rules out using marginal ES intervals after selecting the lowest estimated risk without a simultaneous or selective argument. | The Gaussian selection-event machinery is not a dependent tail-risk or portfolio method. It is a required conceptual control, not direct PCTMG prior art. |
| **Farinhas et al., Non-Exchangeable Conformal Risk Control**, [arXiv:2310.01262](https://arxiv.org/abs/2310.01262); open arXiv/ICLR full text, source previously located in the project audit | Controls expected monotone loss under nonexchangeability using weights and total-variation drift terms, including time-series settings. This is a direct dependence-aware risk-control comparator. | It controls a bounded monotone loss or reserve and does not directly state pairwise conditional ES portfolio-regret control. The gap is narrow and should not be called a new conformal principle. |

The search therefore rejects a broad novelty claim for PCTMG. Selection with
abstention, ES intervals, conditional forecast comparison, confidence-based
ranking, and nonexchangeable risk control are all present separately or in
nearby combinations. The only defensible residual contribution is a
protocol-level composition: use a fixed learned conditional ES surface, build
pairwise dependence-aware margins, and measure the value of abstention against
selected decision regret. A theorem for this exact portfolio/conditional-ES
intersection was not located, but that absence is bounded-search evidence only.

## Cheap dependent mathematical falsifier

The first check can be done without a learned model. Let the pairwise loss or
tail-score contrast process be

```
D_t = d + eps_t,
eps_t = phi eps_{t-1} + eta_t,
Var(eps_t)=v, |phi|<1,
hat d_T = T^{-1} sum_{t=1}^T D_t.
```

Here `d=r_A-r_B`; `d>0` means A is worse than B. The exact Gaussian estimation
error is `Z=hat d_T-d ~ N(0,s_T^2)`, where

```
s_T^2 = v/T^2 [ T + 2 sum_{h=1}^{T-1} (T-h) phi^h ].
```

For a one-sided radius `b=z_{1-delta}s_T`, PCTMG certifies the wrong A only
when `hat d_T+b <= 0`, hence

```
P(wrong A is certified) = Phi(-d/s_T - z_{1-delta}).
```

For the concrete analytic check `v=1`, `d=.25`, `delta=.05`, the exact values
are:

| `T` | `phi` | `s_T` | exact wrong-certification probability |
| ---: | ---: | ---: | ---: |
| 32 | 0.0 | 0.176776695 | 0.001110137 |
| 32 | 0.9 | 0.651156296 | 0.021240045 |
| 128 | 0.9 | 0.370744099 | 0.010192824 |

These are algebraic values from the AR(1) law, not benchmark outcomes. A
candidate implementation fails immediately if its empirical wrong-certification
frequency exceeds the exact value under this construction, or if it claims a
true-regret gain in the `d=0` equal-risk case without accounting for abstention
cost. At `d=0`, symmetry also requires the two directions to have the same
false-certification probability. Matching this check only validates the gate's
calibration algebra; it says nothing about the learned ES surface.

## Verdicts, controls, and minimum experiment

**PCTMG is the strongest useful composition, but not an established new
method.** Its testable value is decision-level: pairwise margins can be
smaller than separate ES intervals because shared forecast error cancels, and
abstention can trade selection frequency for lower tail-regret. The matched
control must keep the learned conditional ES model, information window, and
locked portfolio bank identical while comparing pointwise argmin, a block
bootstrap winner gate, and PCTMG with a fixed fallback. Report common-target
forecast error, selected decision regret, certification/abstention rate, and
fallback utility separately.

The minimum experiment is first the exact AR(1) contrast gate above, including
`d=0` and several positive margins. Only if it passes should one run synthetic
conditional-tail paths with the same past-512 information, no latent-state
leakage, and no test-based model selection. The primary result should be a
paired decision-regret and abstention-utility comparison against the point
selector and dependence-aware interval controls; any lower error on the
selected portfolio alone is insufficient.

**CMTC collapses** to factor modeling, control variates, orthogonal scores, and
paired forecast comparison unless it proves a decision-specific finite-sample
benefit. The exact equal-loading Gaussian construction is its cheapest
falsifier: common-factor cancellation is already complete, so an extra claimed
gain is impossible.

**IBTD collapses** toward PAC-Bayes, Gibbs selection, entropy regularization,
or DRO. In a no-signal equal-risk bank, true decision risk is invariant to the
information budget; any apparent gain is optimizer optimism. It should remain a
control unless a conditional-tail-specific regret bound is derived.

Final status: `PROPOSED COMPOSITION / NO NOVELTY CLAIM`. The bounded search
supports a useful, falsifiable protocol around learned conditional tail risk
and selection quality, while showing that its ingredients and closest
interactions are already known. This is an AI review, not human peer review.

## Read-only implementation audit of the computational composition

**Audit scope.** I read `bank_regret/PROTOCOL.md`, `bank_regret/core.py`,
`bank_regret/study.py`, `bank_regret/run.py`, and the imported finite-mixture
solver. I did not run tests, open frozen-run outputs, train a model, or inspect
test outcomes. The findings below are source-level findings only.

### What is mathematically sound under the stated finite-law scope

The action-local reduction is valid for fixed finite laws, fixed nonnegative
action costs, a common `alpha`, and a common scalar `q` interval. Each action's
RU ES is the minimum of affine threshold lines and is therefore concave. The
bank minimum `g=min_i f_i` is also concave. On an interval where action `i` is
affine, `f_i-g` is convex, so its maximum on that closed interval is attained at
an endpoint. `FiniteMixture.crossings` supplies the support-mass crossings and
the interval endpoints; `solve_local` queries the shared lower hull only at
those action-local points (`bank_regret/core.py:86-98`). The owner stored on the
active hull line is a valid competing action witness, including deterministic
tie behavior.

`solve_union` evaluates the same shared hull on the union of all action knots
(`bank_regret/core.py:101-115`). Under the theorem, this is an exact reference
for the local reduction, although it is not an independent implementation of
the RU calculation. `solve_worlds` correctly takes a per-action maximum over
the supplied finite worlds after each world's same-`q` regret has been solved
(`bank_regret/core.py:137-149`). The result is an absolute ES-difference
regret under the supplied stress set, with costs included in both the action
and the same-`q` benchmark.

### Exactness and runtime blockers

1. **The planned independent exactness check is not implemented in this
   runner.** `run_benchmark` compares `solve_local` and `solve_union`, but both
   call the same `bank_hull` and `FiniteMixture.es` implementation
   (`bank_regret/run.py:60-91`). The protocol also promises a direct pairwise
   RU/LP enumeration, yet `run.py` imports only `FiniteMixture` from
   `mixture_order.core`; it does not call `paired_certificate` or an
   independently constructed direct solver. Local-versus-union agreement can
   therefore miss a shared hull or RU bug. Before calling the theorem
   computationally verified, add a small independent reference covering
   duplicate losses, `alpha=1`, one-point supports, degenerate intervals,
   endpoint crossings, and near ties. This is a concrete evidence blocker, not
   a theorem objection.

2. **The policy path does not compare local and union solvers.** Every policy
   world in `choose_policies` uses the default `solve_local`
   (`bank_regret/study.py:94-127`); the union solver is used only by synthetic
   benchmark cases. If the policy certificate is reported as exact, at least a
   development-only local/union cross-check on the actual 128-action posterior
   worlds is needed, with any disagreement retained.

3. **Hull arithmetic has no tolerance for nearly parallel lines.**
   `OwnedHull` removes exactly equal slopes and computes intersections with
   floating division (`bank_regret/core.py:22-41`). `strict_numerics` rejects
   NaN, overflow, and divide-by-zero, but it does not detect cancellation in a
   very small slope difference or nearly coincident breakpoints. A targeted
   finite-law check should assert value and witness stability under duplicate
   support points, equal or nearly equal slopes, and queries exactly at hull
   starts. The `1e-9` policy tolerance is not a substitute for such a
   condition-number check.

### Observed-context policy and leakage review

The intended sequencing is otherwise clear. `generate_history` owns the
evaluator truth and passes only `z` and categorical observations to
`fit_observed` (`bank_regret/study.py:46-65`). `fit_observed` uses the fixed
512-observation window, counts observed contexts/transitions, and draws the
finite emission stress worlds from those counts (`study.py:68-91`).
`run_policy` calls `choose_policies` before `evaluate`; the evaluator-only
truth is passed after the decision hash is made (`bank_regret/run.py:94-117`).
No future realized loss is used as an ES target. The explicit warning that the
finite posterior stress set is not a true-law coverage set is correct.

There is one **high-severity information-scope blocker**:

```
posterior_seed = seed(cfg, f'{prefix}-posterior-{family}-{index}')
```

at `bank_regret/run.py:97-100` uses the hidden evaluator family label to seed
the posterior emission draws. `family` is `stationary` or `component_shift`,
and the latter encodes an unobserved component change beginning at t=448,
inside the shared 512-observation window. Although
`fit_observed` accepts only `z` and `categories` as statistical inputs, its
randomized stress worlds and therefore its selected action depend on this
unobserved family label through `posterior_seed`. The protocol promises “same
fit in both families” and no latent or future information
(`bank_regret/PROTOCOL.md:66-74`), so this violates the promised policy scope.
The fact that two independently generated histories are usually different does
not cure the structural leak: the policy function should be identical for the
same observed history regardless of which hidden family generated it.

Use a seed derived only from a canonical hash of the observed `z/categories`
arrays and public design, or a fixed predeclared seed independent of family and
index. Then add a same-history cross-family invariance check. Until that is
done, a family-level decision comparison is confounded by a hidden RNG input.

The evaluator truth fields are stored in each policy result
(`truth_q_evaluator_only` and `truth_components_evaluator_only`). That is safe
only because `run_policy` evaluates after locking the decision; downstream
aggregation must preserve the evaluator-only boundary and never use those
fields to regenerate or tune the fit.

### Stress-set scope and ablation interpretation

`shared_full` is exact only for the Cartesian finite stress construction that
combines each of five emission worlds with the shared Beta-quantile interval
for `q`. It is not a posterior credible set, simultaneous confidence set, or
coverage guarantee for the unknown transition/emission law. In particular,
the four Dirichlet draws are finite random support points, and the evaluator's
shifted emission law can lie outside them. The metric
`stress_bound_underestimates_true_regret` is therefore a useful misspecification
diagnostic, not a proof that the minimax solver failed or that a true-law
certificate was violated. Reports should call this a finite stress certificate
throughout.

The ablations are structurally sensible: endpoint-only `q` checks, fixed
posterior-mean `q`, nominal emissions, zero costs, historical unconditional
ES, rectangular worst-case selection, and incumbent fallback all share the
same public bank and cost recipe (`study.py:94-127`). `rectangular_full` is a
shifted version of the action-wise worst-case absolute ES objective because
`low.min()` is common to all actions; its selected index is the meaningful
comparison. Differences in selected true net regret should be reported as
decision outcomes, while differences between the shifted stress surfaces
should not be described as forecast improvements.

The `component_shift` family is a deliberate misspecification stress: the
history after `shift_at=448` is generated from swapped emission laws while the
fit remains stationary. Keep stationary and shifted families separate, as the
protocol requests. The 32 histories share one public scenario dictionary and
one bank, so the bootstrap uncertainty is conditional on that design and does
not establish performance over random banks, market regimes, or real PnL.

### Resume and provenance blockers

The checkpoint envelope, source fingerprint, input hash, and decision lock are
good basic safeguards (`bank_regret/run.py:214-233`). However, policy resume
validation reconstructs only the observed-history/design hash and checks that
the stored decision hashes to its own `decision_lock_sha256`; it does not
recompute `posterior_seed`, `fit_observed`, or `choose_policies`. A stale
checkpoint with the same history hash but different posterior worlds can pass
the current checks if its body and self-lock are internally consistent. Bind a
deterministic fit hash (including the seed and worlds) to the input recipe and
recompute or independently verify the decision before accepting a resume.

The freeze contract also includes `mixture_order/core.py` and
`mixture_order/run.py` but omits `mixture_order/__init__.py`
(`bank_regret/run.py:27-45`). If that initializer can affect import behavior,
the resume fingerprint is incomplete; include every imported local source or
state the package initializer is immutable and irrelevant.

These provenance issues are separate from the mathematical solver result. A
fresh run should be blocked on the family-seeded policy leak and the missing
independent RU exactness check, then re-audited for deterministic resume. No
priority, true-law coverage, safe-improvement, or learned-forecaster claim
follows from the current source alone.

**Qualification on the seed finding.** The family label is not inserted into
the Dirichlet or Beta counts, so this is not evidence that the true shifted
law was numerically passed to the posterior. If the protocol intentionally
allows independent family-specific randomization, classify the issue as a
paired-comparison and reproducibility confound rather than an oracle leak.
Under the stricter contract that the policy is a function only of observed
history and public design, the family-derived seed still has to be removed or
replaced by an observed-input seed.

## Source re-audit after the requested fixes

The reported fixes address the implementation blockers above at source level.
`observed_posterior_seed` now hashes only the observed context/category arrays
and the public design (`bank_regret/study.py`), and `run_policy` no longer adds
family or history-index metadata to that posterior seed. The added same-history
cross-family test monkeypatches the generator and checks both fitted-world and
decision-lock equality. This removes the hidden-family RNG input under the
observed-history-only contract; the test was inspected but not executed in this
review.

Resume validation now reconstructs the observed fit and policy decision and
compares their hashes before accepting a policy checkpoint (`bank_regret/run.py`).
The freeze manifest now includes `mixture_order/__init__.py`. Preflight also
re-solves the actual learned 128-action posterior worlds with `solve_union` and
compares that result with the policy certificate. These changes close the
specific stale-fit, incomplete-freeze, and policy-path local/union gaps
identified above, subject to the pending frozen test/run receipts.

The source-level exactness coverage is materially stronger: the added tests
include independent all-pair RU certificates, an independent tail-risk LP
check, duplicates, alpha=1, singleton intervals, near-parallel lines, costs,
label symmetry, shared-world semantics, and resume immutability. This is a
credible finite falsification suite, but no test result is claimed here because
this review did not execute it. The local-knot proof remains sound within the
declared finite-law, fixed-cost, float64 scope; no new mathematical error was
found in `solve_local` versus the union reference.

One temporal wording correction matters for interpretation: `component_shift`
switches at t=448 within the 512 observations and the swapped emission law
continues thereafter. It is an in-window regime-change stress, not a
post-window change. The fit still uses all 512 observations under its stationary
conjugate model, so this remains deliberate misspecification rather than a
future-label input.

The remaining scientific limits are unchanged. The posterior worlds and Beta
interval are a finite stress set without true-law coverage; the evaluator truth
may fall outside it. The 32 histories share one public bank/design, so any
uncertainty is conditional on that design and says nothing about random banks,
markets, or real PnL. The family-separated comparison is a paired synthetic
stress audit, not evidence of a conditional forecaster or safe improvement.
No priority or peer-review claim follows from these fixes.

## Frozen-summary interpretation and claim boundary

This final audit read `runs/compositional_risk/20261008/frozen/summary.json`
and the already-audited protocol/source. I did not execute tests, rerun cases,
or inspect test output in this pass. The numerical statements below are
therefore **REPORTED** by the frozen summary, while the sequencing and scope
statements are **SOURCE-READ**.

The strongest supported result is the finite computational solver check. The
summary reports all 96/96 cases complete, no failed cases or numerical warnings,
zero local-versus-union selected-index disagreements, maximum regret error
`2.22e-16`, and maximum witness error `1.78e-15`. This supports the action-local
knot reduction as an exact finite-law specialization of the union reference
under the frozen float64 implementation. It does not establish priority: the
summary explicitly leaves `novelty_priority_established` false. The risk
evaluation counts are much smaller for local solving in the larger banks, but
the reported `union_over_local` wall-time ratios range from about `0.97` to
`1.16`; hence this run supports evaluation-count reduction, not a uniform
wall-clock speedup or hardware-independent complexity claim.

The learned policy composition has no joint benefit across the frozen families.
In the stationary family, `shared_full` has lower reported mean true net regret
than `rectangular_full` (difference `-7.19e-05`, reported percentile interval
`[-1.22e-04,-3.06e-05]`) but higher regret than the simpler `point` policy
(difference `+2.48e-05`, interval `[4.78e-06,4.73e-05]`). In the
`component_shift` family, `shared_full` is worse than `rectangular_full`
(difference `+1.21e-04`, interval `[4.98e-05,2.00e-04]`) and has a positive,
though interval-crossing, difference versus `point` (`+7.26e-05`, interval
`[-2.46e-06,1.53e-04]`). Thus the method does not dominate the matched controls,
and the shift stress reverses its stationary advantage against the rectangular
control.

`shared_full` and `shared_endpoints` make the same aggregate policy choices in
both families, as do `rectangular_full` and `rectangular_endpoints`; the
reported factorial interaction is exactly zero. The frozen design therefore
shows no decision value from interior threshold changes. The 7 stationary and
25 shifted cases where the finite stress bound underestimates true regret are
consistent with the declared absence of true-law coverage. The common nominal
forecast surface and the source-defined point/nominal-components equivalence
also prevent interpreting the selected-action differences as forecast
improvement.

The strongest justified final claim is consequently: **an exact, finite-bank
action-local algorithmic reduction with a reproducible observed-context policy
audit, whose policy benefit is mixed in-stress and negative against the point
control in this frozen study**. Unsupported claims include a new forecaster,
conditional tail-risk coverage, safe improvement, generalization to random
banks or markets, and novelty priority.

One decisive next gate is a single pre-registered matched evaluation on an
independent public bank and independently specified true-law process, with
`shared_full`, `point`, `rectangular_full`, and incumbent locked before seeing
outcomes. Require a decision-quality gain over `point` without losing to the
rectangular control under the target family; otherwise retain the solver as an
algorithmic result and close the policy-novelty line. This is a go/no-go gate,
not a request for additional sweeps in this run.
