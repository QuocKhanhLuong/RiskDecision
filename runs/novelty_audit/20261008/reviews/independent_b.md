# Independent novelty review B — conditional post-selection tail risk

Status: `PROPOSAL / SEARCH-INCOMPLETE` (2026-10-08)

This review addresses the focal question: **what narrowly defensible new method or
theory could improve assessment of next conditional tail risk for a portfolio
selected from a locked bank when observations are dependent, given only the same
past-512 information?** The output is a research proposal and prior-art audit,
not evidence of novelty, validity, or peer review.

## Independent generation round (before literature search)

Provenance: `independent_b`, AI-assisted generation, generated before opening
external literature or seeing another agent's candidate list. The current
repository constraints supplied the neutral prompt and fixed-information
boundary. No human participant contributed to this round. The ideas below are
retained verbatim in their initial form; later overlap checks are separate.

### B1 — Selection-conditioned dependent risk envelope (SC-DRE)

**Idea.** Estimate the joint conditional error process of the whole risk surface
over the locked portfolio bank, then condition its one-sided envelope on the
selection event. For loss `L_{t+1}(w)`, observable history `F_t`, and conditional
tail target

\[
  r_t(w)=ES_\alpha(L_{t+1}(w)\mid F_t),\qquad
  \hat w_t=\arg\min_{w\in W}\hat r_t(w),
\]

construct residuals `u_{j,w}=L_{j+1}(w)-\hat r_j(w)` using only historical
information available at `j`. Estimate a dependence-preserving multiplier
process `G_t(w)` with covariance kernel `\hat\Sigma_t(w,w')`, using a
predeclared block length or a fitted transition kernel. Simulate the conditional
law of the selected error, retaining multiplier draws whose perturbed surface
selects the same index (or the same predeclared selection cell):

\[
 c_{t,1-\gamma}^{sel}=Q_{1-\gamma}\{G_t(\hat w_t)\mid
       \arg\min_w[\hat r_t(w)+G_t(w)]=\hat w_t\},
 \qquad
 \hat r^{SC\text{-}DRE}_t(\hat w_t)=\hat r_t(\hat w_t)+c_{t,1-\gamma}^{sel}.
\]

The output is a selected-portfolio conditional upper envelope, rather than a
new unconditional forecaster. It uses the same past-512 data and has no test
outcome in the selector.

**Assumptions.** The loss-surface residual process is stationary enough for a
block/multiplier approximation; the selected index is measurable from `F_t`;
the estimated cross-portfolio covariance kernel is finite and not silently
independent across portfolios; ties and selection cells are specified before
assessment.

**Prediction.** Conditioning on selection should reduce undercoverage for the
portfolio actually chosen, especially when portfolios have correlated forecast
errors and the selection margin is small, while leaving common-target forecast
error approximately unchanged. A simultaneous unconditioned block envelope may
be more conservative but should be a strong control.

**Falsifiers.** (i) Conditional coverage on held-out next-period blocks is no
better than an unconditioned dependent envelope or time-aware split; (ii) the
selection-conditioned correction is unstable under block length or cell
choices; (iii) it fails under a stationary Markov process with known
parameters; or (iv) it improves coverage only by materially inflating reserve
size and loses on a predeclared coverage-versus-width criterion.

**Uncertainty.** This may collapse to selective inference plus block bootstrap;
the novelty question is whether a useful finite-bank, conditional tail-risk
formulation and valid dependent approximation are absent from the checked
literature. No guarantee is claimed here.

### B2 — Transition-coupled optimism and drift correction (TC-OC)

**Idea.** For a conditional risk model `r(w,theta)` fitted from the dependent
history, correct two distinct errors jointly: the curvature-induced optimism
from selecting `w`, and the predictable one-step movement of the conditional
parameter. Let `H_t` be the predeclared Hessian of a smoothed optimization
criterion in `w`, `J_t` an estimated conditional long-run covariance of its
estimating scores, and `m_t` the fitted transition prediction for `theta_{t+1}`.
Use

\[
 \hat r^{TC\text{-}OC}_{t+1}(\hat w_t)=
 r(\hat w_t,\hat\theta_t)
 +n_t^{-1}\operatorname{tr}(H_t^{-1}J_t)
 +\nabla_\theta r(\hat w_t,\hat\theta_t)^\top
       (m_t-\hat\theta_t).
\]

The first term is the OIC-like selection correction; the last term is a
transition-conditioned forecast update estimated from `F_t`, rather than an
HAC multiplier treated as a stationary unconditional variance. A valid
implementation must state the smoothing, parameter transition, and how `m_t`
is estimated without hidden state or future outcomes.

**Assumptions.** A locally smooth conditional risk surface exists; the
parameter transition is identifiable from observed history; a first-order
expansion is adequate over one forecast step; score dependence is weak enough
for `J_t`; all portfolio choices use the same information and optimizer.

**Prediction.** When conditional risk changes predictably after a regime or
volatility feature in `F_t`, the coupled correction should reduce next-period
conditional error relative to iid OIC/HAC and a frozen conditional model. When
the transition drift is zero, it should reduce to the appropriate OIC/HAC
control up to estimation noise.

**Falsifiers.** (i) On a no-drift stationary DGP it adds systematic bias; (ii)
on an observed-state Markov DGP it does not beat the frozen model after equal
parameter and information budgets; (iii) the drift term is numerically equal
to a standard rolling update or filtered GARCH/HMM forecast; or (iv) first-
order expansion errors dominate at the locked portfolio boundary.

**Uncertainty.** The displayed decomposition may be an obvious combination of
known optimism and online/state-transition corrections. It is a theory-shaped
candidate only if a conditional post-selection target and a proof identify a
term that standard OIC plus time-aware estimation cannot recover.

### B3 — Dependence-preserving tail support completion (DPT-SC)

**Idea.** Reweighting historical scenarios cannot represent a conditional tail
event absent from the 512 observations. Build a conditional path law from
observable innovations and a predeclared lag signature, then apply a constrained
transport repair that adds support while preserving the observed dependence
structure. For generated paths `z_{1:H}` and base conditional law `P_t^0`, define

\[
 Q_t^*=\arg\min_Q KL(Q\Vert P_t^0)
 +\lambda\left\|E_Q[\psi(z_{1:H})]-\hat m_t\right\|_2^2
 +\eta\,D_{\rm lag}(Q,\hat P_t),
\]

where `psi` includes tail and cross-asset moments and `D_lag` penalizes changes
to predeclared lag/cross-sectional dependence. Scenario generation and the
selector are frozen before future evaluation; a historical mixture and a DRO
reweighting control receive the same portfolio bank. The intended improvement
is conditional-tail support, not generic optimism correction.

**Assumptions.** The innovation/path generator is identifiable enough from
`F_t`; its support contains plausible but previously unseen tail paths;
`psi` and lag constraints are chosen without future outcomes; generated paths
are evaluated at common fixed portfolios as well as the selected one.

**Prediction.** It can reduce common-target conditional ES error when the main
failure is missing tail support and historical reweighting saturates, while
preserving serial dependence better than iid scenario perturbation.

**Falsifiers.** (i) Pure historical reweighting or a correctly tuned DRO
control matches or beats it on common targets; (ii) synthetic support completion
raises ES bias or undercoverage in a correctly specified Markov process; (iii)
the result disappears when generated support is held fixed before selection;
or (iv) gains come only from extra effective samples/parameters rather than
the dependence-preserving constraint.

**Uncertainty.** This is likely close to conditional scenario generation,
entropy pooling, robust optimization, or decision-focused simulation. Without
a specific missing-support diagnostic and a separating ablation it is not a
credible novelty claim.

## Scope and evidence boundary

The internal evidence motivating these candidates is synthetic: iid smooth
CVaR OIC is reported as an applicable marginal correction, iid OIC/HAC did not
forecast the next conditional risk, and a correctly specified learned
two-state Gaussian HMM reduced conditional MSE in a Gaussian Markov simulation.
That HMM result is a baseline diagnostic, not novelty. Every proposed method
must use the same past-512 information and locked portfolios, expose the
selection rule, and separate common-target forecast error from own-selected
decision quality and reserve utility. No latent state may enter training or
selection. No test-based model selection is permitted.

The next sections record the bounded primary-source search, overlap analysis,
and a post-search independent reopening. A bounded search cannot establish
absence; all gaps below must be phrased as “no direct source located.”

## Bounded primary-source search

Search date: 2026-10-08. I used nine focused web-search batches, then opened
the primary paper or the official publisher/proceedings landing page. Search
results from index pages were used to locate a DOI or repository copy; they are
not treated as evidence when the primary record was available. The search was
bounded to selective inference after selection, dependent/time-series risk
forecasting, post-selection downside-risk calibration, and tail scenario/DRO
methods. It was not an exhaustive systematic review.

| ID | Source and access status | Located technical overlap | Boundary relevant here |
|---|---|---|---|
| S1 | [Iyengar, Lam & Wang, OIC v4](https://arxiv.org/abs/2306.10081v4), arXiv preprint, revised 2025; full HTML/PDF | First-order optimizer-bias correction for data-driven decisions, including risk functions and portfolio/DRO examples | The formulation starts from `n` iid samples and corrects expected optimized objective performance; no conditional next-period serial-risk target was located in the paper. |
| S2 | [Kettunen & Salo (2017)](https://onlinelibrary.wiley.com/doi/full/10.1111/poms.12727), Production and Operations Management, open full text | Directly shows selected-portfolio downside percentiles are biased and proposes closed-form or Monte Carlo calibration after selection | Project portfolios use static value/error distributions and selection conditioning; no serially dependent conditional ES surface or next-step forecast was located. |
| S3 | [Liu, Markovic-Voronov & Taylor (2023)](https://arxiv.org/abs/2203.14504), arXiv v2; full HTML/PDF | Generic black-box selective inference estimates a selection probability by bootstrap re-running the selection algorithm and conditions inference on the selection event | It assumes asymptotic normality and accurate selection-probability estimation; no dependent-tail-risk or joint VaR/ES portfolio result was located. |
| S4 | [Bao et al., CAP v5](https://arxiv.org/abs/2403.07728), arXiv v5 (2025); full HTML/PDF | Online post-selection predictive intervals, adaptive historical calibration, and selection-conditional coverage/FCR | The exact SCC proposition is stated for iid labeled data; dynamic extensions target long-run FCR under shift, not a serially dependent finite-bank ES forecast or selected risk surface. |
| S5 | [Xu & Xie (2023), SPCI](https://proceedings.mlr.press/v202/xu23r.html), ICML/PMLR, full paper/PDF | Sequential conformal inference estimates future residual quantiles using temporal dependence and gives asymptotic conditional coverage for time series | It wraps a point predictor and produces intervals/quantiles; it does not condition a joint portfolio VaR/ES surface on an optimizer's selected index. |
| S6 | [Patton, Ziegel & Chen (2019)](https://doi.org/10.1016/j.jeconom.2018.10.008), Journal of Econometrics; publisher abstract plus author full PDF/arXiv | Dynamic jointly elicitable VaR/ES models and FZ scoring for conditional tail forecasts, including GARCH/rolling comparisons | This is conditional risk forecasting, not post-selection inference or selection optimism correction. It is a strong B2 baseline. |
| S7 | [Fairbrother, Turner & Wallace (2019)](https://link.springer.com/article/10.1007/s10107-019-01451-7), Mathematical Programming, publisher full article | Problem-driven scenario generation targets the risk region of CVaR and proves consistency for tail-risk stochastic programs | It is primarily distribution/scenario representation for static or staged optimization; it does not supply selected-portfolio conditional inference under serial dependence. |
| S8 | [Yan et al. (2020)](https://doi.org/10.1007/s10479-019-03147-9), Annals of Operations Research; abstract available, publisher full text restricted | ARMA-GARCH plus dynamic Student-t-Clayton copula scenario trees capture time-varying asymmetric tail dependence for multiperiod portfolio selection | It is an explicit dynamic scenario-generation baseline, not a selection-conditioned risk correction; full article was not accessible in this search. |
| S9 | [Esfahani & Kuhn (2018)](https://link.springer.com/article/10.1007/s10107-017-1172-1), Mathematical Programming, open full article | Wasserstein DRO gives finite-sample out-of-sample certificates and can move mass away from the empirical distribution | The paper's concentration result is built around iid training samples; it is not a conditional, selection-event-specific tail forecast. |
| S10 | [Fung et al. (2026)](https://doi.org/10.1016/j.jeconom.2025.106127), Journal of Econometrics; publisher full text restricted, abstract/keywords indexed | Nonparametric systemic-risk portfolio selection, conditional ES, asymptotics, and moving-block bootstrap | This is the closest recent portfolio/time-series inference lead found, but the accessible abstract does not state a finite locked-bank post-selection correction; full-text verification remains needed. |
| S11 | [Wasserstein worst-case scenarios and asset pricing (2026)](https://doi.org/10.1016/j.jmoneco.2026.103955), publisher abstract accessible, full text restricted | Wasserstein transport permits support-shifting adverse scenarios and discusses persistent state dynamics | It addresses robust asset pricing and ambiguity, not selected conditional tail-risk inference; it makes B3's support-completion framing clearly adjacent to existing DRO. |

The strongest direct challenges are therefore S2 for selection-conditioned
downside risk, S3/S4 for selection-conditioned inference, S5/S6 for dependent
conditional tail forecasting, and S7--S11 for tail scenario/DRO construction.
No source in this bounded search was verified to give the exact combination of
joint VaR/ES score-process inference, finite locked portfolio-bank selection,
and serially dependent next-period conditional risk. That is a search result,
not a novelty claim; S10 in particular requires a full-text check before any
priority statement.

## Adversarial overlap review

### B1 — SC-DRE

**Evidence status: `challenge-located / search-incomplete`.** The mechanism is
already structurally present in selective inference: S3 estimates the
selection event with repeated bootstrap runs and conditions the target law on
that event. S4 gives a selection-conditional predictive guarantee after an
adaptive pick, and S5 supplies the dependent-residual quantile component. S2
shows directly in a portfolio setting that post-selection downside risk needs
calibration. A block multiplier process over all locked portfolios is also a
standard dependent-inference ingredient. Thus “condition a bootstrap band on
the selected index” is not defensible as a standalone novelty statement.

The remaining narrow gap located is a *target and integration gap*: a selected
portfolio's next-period **joint VaR/ES** risk should be assessed from a common
multivariate score process over the entire locked bank, with the dependence
approximation and the selection cell fixed before future outcomes. S3 is
generic, S4's finite-sample SCC is iid, S5 is not post-selection ES, and S2 is
static. No direct paper was located that proves or evaluates this exact
combination. The gap could disappear after a full search or after reading S10.

**Adversarial failure modes.** Conditioning can make the accepted multiplier
sample nearly empty when the selected portfolio has a small margin. A fitted
cross-portfolio covariance kernel can be more fragile than the point forecast.
Block length and selection-cell width can become hidden tuning parameters. A
coverage gain can be bought by arbitrarily wide reserves. If any of these occur,
SC-DRE is an expensive restatement of selective bootstrap with no useful
conditional-risk improvement.

### B2 — TC-OC

**Evidence status: `challenge-located; likely collapse`.** S1 already gives the
optimizer-curvature correction for the iid objective and explicitly extends to
risk functions. S6 already models the predictable dynamics of a jointly
elicitable VaR/ES pair. GARCH, HMM, filtered simulation, and score-driven
models are the natural baselines for the transition term. The proposed
expression adds these components, but the displayed `m_t - theta_t` term is
not identified by the proposal alone: it can double-count a dynamic forecast
update or measure model drift rather than selection optimism. No source was
located that supports the exact decomposition as a theorem for the target in
question. Without a derivation showing a nonzero cross-term that both S1 and
S6 omit, B2 is a renamed combination of known corrections.

The appropriate falsifier is a matched observed-history Markov or stochastic-
volatility simulation with frozen parameter budget: if a direct dynamic ES
model plus applicable OIC/HAC matches TC-OC, the candidate stops. A negative
result would still identify that next conditional-risk failure is forecast
misspecification rather than an uncorrected selection term.

### B3 — DPT-SC

**Evidence status: `challenge-located; reject pending redesign`.** S7 already
targets tail-risk regions with problem-driven scenario generation. S8 builds
time-varying tail-dependent scenario trees, while S9 supplies a transport
ambiguity set with performance certificates. S11 explicitly studies
Wasserstein support shifts beyond the reference support. These papers make a
generic “add unseen tail support while preserving dependence” claim too broad
to defend.

There is also a concrete internal inconsistency in the initial equation: the
constraint `Q << P_t^0` together with `KL(Q || P_t^0)` forbids probability mass
outside the base support, so it cannot simultaneously add new support. Removing
absolute continuity and replacing KL with a transport cost turns the proposal
into a Wasserstein/DRO or generative-scenario method already covered by S7--S11.
The missing-support premise itself must be diagnosed at common fixed
portfolios before any generator is trained. Until that diagnostic exists, B3 is
not an efficient research direction.

## Post-search independent reopening

Provenance: `post-check`, AI-assisted, generated after the source audit and
kept separate from the initial ideas. The result is a narrower descendant of
B1, not evidence that B1 was novel.

### B4 — FZ selection-cell risk envelope (FZ-SCRE)

Use a jointly elicitable VaR/ES score rather than correcting ES alone. For each
locked portfolio `w`, let `z_t(w)=(v_t(w),e_t(w))` be its conditional VaR/ES
forecast and let

\[
 s_{j,w}=\nabla_z L_\alpha^{FZ}\!\left(\hat z_j(w);L_{j+1}(w)\right)
\]

be the score influence vector computed only after historical outcome `j` is
available. Estimate the cross-portfolio, serially dependent score-process
covariance from predeclared blocks. At decision time, select

\[
 \hat w_t=\arg\min_{w\in W}\hat e_t(w),
 \quad A_t=\{\hat w_t=k,\;\hat e_t(w)-\hat e_t(k)\in C_w\},
\]

where the selection index and margin cells `C_w` are fixed before assessment.
Use block multipliers on the vector process `s_{j,w}` and invert the simulated
joint score law for a one-sided upper bound on `e_t(\hat w_t)` conditional on
`A_t`. The intended claim is narrowly about the **selected conditional ES
assessment and its joint VaR/ES coherence**, with common-target FZ scores
reported separately. It has no latent-state input and does not re-select a
model on test outcomes.

This candidate still inherits the generic selective-inference machinery in
S3--S5. Its only plausible remaining contribution is a theorem or validated
finite-bank procedure for this exact target under an explicit mixing/Markov
condition, with a useful width-versus-conditional-coverage tradeoff. If that
theorem reduces to a block bootstrap confidence band, the work should be
reported as a careful adaptation or null result rather than a new method.

## Transparent prioritization

The criteria were fixed before the qualitative ranking: (1) a specific gap
after the checked sources, (2) a mechanism that changes the selected conditional
target, (3) a falsifier that can be run with the locked information set, (4)
feasibility within a finite simulation, and (5) value of a null result. Scores
are 1 (weak) to 5 (strong), are judgment aids rather than evidence, and do not
establish originality.

| Candidate | Gap specificity | Mechanism/testability | Feasibility | Null-result value | Decision |
|---|---:|---:|---:|---:|---|
| B1 SC-DRE | 3 | 4 | 3 | 4 | Keep only as a broad parent; generic selective bootstrap overlap is high. |
| B2 TC-OC | 1 | 3 | 3 | 3 | Do not pursue before an analytic cross-term is derived. |
| B3 DPT-SC | 1 | 3 | 2 | 3 | Reject for now; formula has a support contradiction and strong DRO/scenario prior art. |
| B4 FZ-SCRE | 3 | 5 | 3 | 5 | Strongest bounded candidate, `PROMISING BUT UNPROVEN`. |

The strongest candidate is therefore B4, with the explicit caveat that this is
a research direction, not an established novel method. It earns priority
because it has a well-defined selected conditional target, a coherent VaR/ES
score, and a falsifiable comparison against an unconditioned dependent band.
It may still collapse to existing selective inference after the theorem and
full S10 audit.

## Minimum meaningful experiment

First run a finite analytical check before any expensive fitting. Use two or
three fixed portfolios with jointly Gaussian observed AR(1) losses, known
dependence only for the evaluator, and a predeclared linear/parametric VaR/ES
score estimator. Derive or numerically integrate the selection-conditional
law for the minimum estimated ES. Verify that the implementation's block
multiplier conditional band has the intended coverage and does not become
empty or unbounded as the selection margin shrinks. If it fails this toy check,
stop B4.

If that gate passes, use independent simulated episodes with the same past-512
length and the same locked portfolio bank:

1. iid Gaussian serves as the regression control where OIC is applicable;
2. stationary observed-history AR/volatility dependence tests the serial score
   process without latent-state leakage; and
3. a regime-change process tests conditional failure under a changed law, with
   the hidden simulator state used only by the evaluator and never by fitting
   or selection.

Freeze the methods, block lengths, margin cells, and confidence level before
held-out episodes. Compare naive selected ES, applicable iid OIC, an
unconditioned block multiplier band, a time-aware split control, and B4. Keep
HMM/GARCH/FHS as forecast baselines with identical information where run. The
primary endpoint is conditional coverage error for the selected ES at a fixed
width/reserve budget; secondary endpoints are interval width, joint FZ score on
the same fixed portfolios, selected true ES/regret, and reserve utility. Report
selection frequency and failed/empty conditioning draws. No test outcome may
choose a model, block length, or margin cell.

Stop the branch if B4 has no conditional-coverage/width improvement over the
unconditioned dependent band, if it only wins after widening reserves, or if
the gain is explained by a better underlying ES forecaster. That outcome would
still resolve whether the remaining failure is selection assessment or
conditional forecasting. Do not start neural or generative sweeps before this
gate and the full-text audit of S10.

## Decision

`PROPOSE B4 / NOT RUN / NO NOVELTY CLAIM.` Keep B1--B3 as documented candidate
and negative directions. The single next action is the analytical two-portfolio
selection-cell check followed, only if it passes, by the frozen three-DGP
Monte Carlo comparison above.

## Post-search candidate audit: finite-support shared-mixture ES gap

Provenance: `independent_b`, adversarial review of a root-provided post-search
candidate, recorded after the initial generation and literature pass. This is a
bounded overlap check and implementation review, not a novelty determination.

### Algebra and scope

The core finite-support statement is correct after fixing the tail-level
notation. Let `tau` be the upper-tail probability, let `q` lie in `[lo, hi]`
inside `[0,1]`, and write the mass at an ordered support value `x_i` as

```text
p_i(q) = (1-q) p_i^0 + q p_i^1.
```

For the Rockafellar--Uryasev upper-tail definition,

```text
ES_tau(X; q) = min_t { t + tau^{-1} sum_i p_i(q) (x_i - t)_+ }.
```

For finite fixed support it is enough to consider support values for `t`.
Each objective at a fixed `t` is affine in `q`; hence ES is the lower envelope
of finitely many affine functions and is concave piecewise affine. On an
interval where the quantile index is fixed, the same fact follows from the
fractional-atom tail sum. Its possible slope changes occur when a prefix mass
`C_i(q)` reaches `1-tau` (equivalently a top-tail mass reaches `tau`). Thus,
after coalescing equal support values, the union of those roots for A and B
plus `lo` and `hi` is a sufficient partition. The difference of the two ES
values is affine on each open cell, so its maximum over the compact interval is
attained at a partition endpoint. The argument does not require the difference
itself to be concave.

The proposed witness checks out under this definition. With `tau=.05`,

```text
ES_A(q) = min(10, 200 q),       ES_B(q) = 1 + 10 q,
D(q)   = 190 q - 1  (q <= .05),
          9 - 10 q   (q >= .05).
```

Therefore `D(0)=D(1)=-1` and `D(.05)=8.5`; endpoint-only checking fails.
The point `q=.05` is exactly the A tail-mass knot. This is a valid deterministic
shared-mixture safety-gap certificate.

There are three definition hazards to freeze in an implementation. First, the
notation `ES_alpha` is ambiguous here: the witness uses `.05` as tail mass,
whereas the common confidence-level notation would call this `ES_.95` and use
tail mass `1-.95`. Second, the result requires the RU fractional inclusion of
an atom at the tail boundary; a hard rounded “average of the top samples” is a
different, potentially discontinuous functional. Third, this certifies
`ES(A;P_q)-ES(B;P_q)` using two marginal loss laws. It does not certify
`ES(A-B;P_q)` or CVaR of a random regret, for which the joint coupling of A and
B matters. The result should be named a relative ES gap unless the marginal
difference is explicitly the intended safety quantity.

### Complexity audit

The claimed `O((S_A+S_B) log(S_A+S_B))` cost is plausible but conditional on
what “envelope evaluation” includes. For each portfolio, sort and coalesce the
state supports, store state-specific prefix masses and prefix first moments,
solve at most one linear equation per cumulative threshold, and sort/merge the
resulting roots. At each knot, a binary search for the quantile index plus
prefix-moment lookup evaluates ES in `O(log S)` time. This gives the stated
bound, with `S` meaning the number of unique support values after coalescing.
A linear sweep can reduce the evaluation pass further.

If “pre-sorted cumulative sums” instead means scanning all support values at
every knot, the actual cost is `O(S^2)`; sorting alone does not establish the
claimed bound. The implementation must also handle zero root denominators
(constant cumulative mass), duplicate roots, zero-mass atoms, exact ties at the
tail threshold, and a mixture interval outside `[0,1]` (which is not a
probability mixture). These are finite algebraic edge cases, not statistical
coverage issues.

The strongest independent comparator is a generic RU piecewise-linear
envelope. For each portfolio and each support threshold `x_j`, construct the
affine line

```text
g_j(q) = x_j + tau^{-1} sum_i p_i(q) (x_i - x_j)_+,
```

build the lower envelope of these lines, merge the active-cell breakpoints for
A and B, and maximize the affine difference at the merged endpoints. A hull
implementation gives an independent `O(S log S)` check. Endpoint-only checking
is a deliberately weak comparator and should not be used as the safety test.

### Closest primary sources and overlap

| Source and access | Actual overlap | Remaining distinction observed in this bounded check |
| --- | --- | --- |
| Rockafellar & Uryasev, *Optimization of Conditional Value-at-Risk*, DOI [`10.21314/JOR.2000.038`](https://doi.org/10.21314/jor.2000.038); publisher metadata and author-hosted PDF are available, full article not independently retrieved here. | RU variational form and finite-scenario piecewise-linear/LP evaluation are the direct computational foundation of the proposed envelope. | The candidate packages two fixed marginal ES envelopes over a one-dimensional shared mixture and takes their exact difference supremum; no claim that this packaging is absent from the literature. |
| Huang, Zhu, Fabozzi & Fukushima (2010), *Portfolio selection under distributional uncertainty: a relative robust CVaR approach*, DOI [`10.1016/j.ejor.2009.07.010`](https://doi.org/10.1016/j.ejor.2009.07.010); metadata/abstract accessible, publisher full text returned 403. | Relative/worst-case CVaR over distribution uncertainty and multiple priors overlap the robust “which portfolio is safer” motivation. | The bounded source view did not verify this exact fixed-A/fixed-B finite-mixture endpoint algorithm; absence is not evidence of novelty. |
| Tselishchev (2019), *On the Concavity of Expected Shortfall*, [arXiv:1910.00640](https://arxiv.org/abs/1910.00640); full HTML/PDF open. | It explicitly proves concavity of ES with respect to finite mixture distributions, which supplies the candidate's central structural property. | It is a theorem about ES under mixtures, not evidence that the proposed difference certificate is a new method. |
| Pun, Wang & Yan (2023), *Data-Driven Distributionally Robust CVaR Portfolio Optimization Under a Regime-Switching Ambiguity Set*, DOI [`10.1287/msom.2023.1229`](https://doi.org/10.1287/msom.2023.1229); abstract/metadata accessible via [RePEc](https://ideas.repec.org/a/inm/ormsom/v25y2023i5p1779-1795.html), publisher full text not retrieved. | Regime-mixture ambiguity, CVaR, portfolio comparison, and tractable robust optimization are nearby application/theory families. | Their ambiguity set and statistical/data-driven objective are broader/different; exact shared-mixture ES-gap equivalence was not verified. |
| Bitar (2024), *Distributionally Robust Regret Minimization*, [arXiv:2412.15406](https://arxiv.org/abs/2412.15406); full HTML/PDF open. | It explicitly treats worst-case CVaR of a regret random variable under Wasserstein ambiguity. | CVaR of regret is not the difference of two marginal CVaRs. Importing its terminology would overclaim what this certificate establishes. |

The bounded search found no source that states the exact final two-portfolio
algorithm verbatim, but the construction is a short finite-support consequence
of the RU representation plus mixture concavity and envelope arithmetic. A
direct equivalent may therefore exist in optimization implementations or in
the full text of the relative-robust sources. This search does not support a
novelty claim.

### Decisive finite checks and reviewed verdict

Before presenting this as a method, use exact rational arithmetic on the stated
witness and on randomized finite supports, including shared and disjoint
supports, duplicate values, zero slopes, and threshold ties. Compare (i) the
candidate's root set and maximum, (ii) the independent RU lower-envelope hull,
and (iii) a dense-grid diagnostic. Then benchmark increasing unique-support
counts to distinguish the promised `O(S log S)` implementation from a hidden
quadratic scan. Keep the interval inside `[0,1]` and freeze whether `.05` means
tail probability or confidence level.

Reviewed verdict: `ALGEBRA PASS WITH DEFINITION CONDITIONS; WITNESS PASS;
COMPLEXITY PLAUSIBLE ONLY WITH PREFIX/HULL IMPLEMENTATION; DIRECT-PRIOR
OVERLAP HIGH; STANDALONE NOVELTY NO-GO.` The candidate is worth retaining as a
deterministic, reproducible shared-distribution safety certification and as a
strong evaluator for endpoint failures. It is not evidence about HMM training,
conditional statistical coverage, or generic minimax-regret novelty, and it
should not be used to make those claims.

Executed finite receipt (2026-10-08): exact `Fraction` arithmetic reproduced the
witness values `D(0)=-1`, `D(.05)=17/2`, and `D(1)=-1`; an additional finite
support case matched the candidate root evaluation to direct RU minimization at
all merged knots (`finite_check=PASS`). This is an algebra check only, not a
statistical or novelty result.

## Read-only implementation audit: `mixture_order` finite gates

Provenance: `independent_b`, read-only review of `mixture_order/core.py`,
`mixture_order/run.py`, `mixture_order/PROTOCOL.md`, and
`tests/test_mixture_order.py` after the root implementation. No production file
was edited. This section audits correctness and run integrity; it does not turn
the synthetic gates into a numerical safety or scientific result.

### What passes

For ordinary finite float64 inputs, `FiniteMixture.es` sorts losses in descending
order, finds the first cumulative upper-tail atom by vectorized binary search,
and uses fractional mass at the boundary. `crossings` enumerates the affine
cumulative-mass roots, and the union with the endpoints is sufficient for the
common-q difference because both ES curves are affine between their roots.
Duplicate loss values are retained rather than coalesced; that can add
redundant roots but does not change the RU value. The `LowerEnvelope` comparator
uses the generic RU threshold lines and is an appropriate strong comparator.

The test suite passed with the repository environment (`PYTHONPATH=.`):
`27 passed in 0.31s`. The checks include an independent risk-envelope LP for
atoms, duplicate values and zero masses, all pairwise RU-line intersections for
one random case, the exact witness, and resume byte preservation. An additional
read-only audit over 500 seeded random finite cases found maximum specialized
versus RU-hull upper-value error `7.11e-15`. The endpoint witness and the
common-q-versus-separate-max/min distinction remain correctly represented.

### Findings requiring an audit decision

**1. Partial runs exit successfully while incomplete (high priority).**
`summary` sets `all_checks_passed` to `all(...)` over the records even when
`complete` is false, and `main` exits only from the fallback
`result.get('all_checks_passed', False)`. I executed a fresh read-only partial
run with `--max-new-cases 1`: the process returned exit code 0 and wrote
`cases_done=1`, `cases_expected=265`, `complete=false`,
`all_checks_passed=true`. A downstream job that trusts the process status can
publish an incomplete gate as successful. The full audit should remain frozen
until the runner or wrapper requires `complete and all_checks_passed` for a
successful run; a partial checkpoint is a development receipt only.

**2. Resume hashes detect accidental corruption, not a changed-and-rehashed
payload.** `read_checkpoint` verifies a self-contained `sha256`, fingerprint,
and case ID, but it does not recompute the expected case input from the frozen
config/seed or validate the result schema. An edited checkpoint whose body is
rehashed, or a copied body relabeled with the expected case ID and rehashed, is
accepted. The existing test changes the body without updating the hash, so it
only tests accidental corruption. The same limitation applies more directly to
`preflight.json`: an existing receipt is trusted after checking only its
fingerprint, so its `passed` or benchmark fields can be changed while retaining
that fingerprint. This is acceptable only if the run directory is a trusted
local workspace. For portable audit artifacts, anchor checkpoint/preflight
digests in an immutable manifest or regenerate and compare each expected case
input before resuming.

**3. “Finite input” does not imply finite numerical output.** The constructor
accepts any finite loss, including values near `1e308`, and divides RU excess
moments by small `alpha` in float64 without checking the result. A concrete
read-only probe with losses `[0, 1e308, -1e308]`, `alpha=.05`, and valid
probabilities returned a finite specialized certificate but `hull_certificate`
returned `nan` at both endpoints with overflow/invalid-operation warnings. The
mathematical finite-support theorem is unaffected, but the implementation has
no numerical safety certificate for its accepted input domain. Either bound or
scale the supported loss range, reject nonfinite intermediate lines/results,
or state explicitly that the gate covers the moderate synthetic scale only.
Near-normalized probabilities are also accepted within `1e-12` and cumulative
totals are forcibly set to one; this is practical tolerance, not exact law
preservation, and should not be described as exact arithmetic.

**4. Curve agreement is checked at the merged breakpoints only.** For exact
mathematics this is enough because both constructions are affine between all
crossing and hull-start points. In float64, a missed or badly rounded crossing
could leave an untested interior slope change. The existing all-intersection
test is useful, but the frozen stress receipt should either record the actual
root/hull partitions or independently evaluate each merged cell's affine
slope. This is a robustness improvement rather than evidence of a current
normal-scale failure.

### Gaussian falsifier boundary

The AR(1) half-squared-loss derivation is internally consistent: the matrix
quadratic identity, trace mean, residual quadratic variance, and oracle
conditional control agree in the tests. It is correctly labelled as an oracle
parameter, non-tail synthetic falsifier. It does not test learned conditional
forecasting, tail coverage, or market risk. The finite constant correction is
optimal among constants for the stated MSE target, while nonzero residual
variance blocks exact terminal recovery by that correction; those claims should
remain limited to this Gaussian construction.

### Reviewed verdict and freeze recommendation

`CORE ES/PARTITION: PASS; RU HULL COMPARATOR: PASS ON NORMAL-SCALE FINITE
INPUTS; FLOAT64 NUMERICAL DOMAIN: QUALIFIED; RESUME/COMPLETION STATUS:
BLOCKER FOR PUBLIC RUN RECEIPT.` The strongest comparator is present and the
27-test plus 500-case checks support implementation agreement on the exercised
domain. Do not call a partial run successful, and do not publish a numerical
safety claim beyond the finite moderate-scale synthetic inputs until the
completion check and nonfinite-intermediate policy are resolved. None of this
changes the earlier `NO NOVELTY CLAIM` decision.

## Resolution recheck after runner fixes

Provenance: `independent_b`, concise read-only recheck of the root's fixes after
the preceding audit. No production file was edited and no new broad stress
search was run.

The three prior blockers are resolved for the declared local reproducibility
scope:

1. `main` now returns exit code `3` for an incomplete `run` stage after the
   ordinary failed-check gate. An actual partial invocation produced exit code
   `3` with `complete=false`; the summary still records that all completed
   cases passed, so consumers must require both fields for a publishable full
   receipt.
2. `strict_numerics` wraps the ES, crossing, RU-hull, certificate, and Gaussian
   analytic paths. The former extreme finite-loss probe now fails closed with a
   floating-point exception, and the focused test covers this behavior rather
   than allowing a `nan` hull to be interpreted as a bound.
3. `preflight.json` now carries and verifies a payload digest. Resume validates
   checkpoint schema, regenerates mixture inputs from the frozen seed recipe,
   and recomputes the paired certificate, so a changed-and-rehashed mixture
   payload is rejected. The README and protocol now state that these hashes are
   accidental-corruption/reproducibility checks, not signed anti-adversarial
   protection. AR resume remains metadata-bound by design; it is not a replay
   of all Monte Carlo histories.

The RU comparator now reuses the constructor's descending support order by
reversing it, preserving the same lower-envelope construction without a second
sort. The focused suite passes `29 passed in 0.30s`, including the new
incomplete-CLI, overflow, and rehashed-input checks. The implementation review
therefore moves from `BLOCKER` to
`RESOLVED FOR THE DECLARED FROZEN SYNTHETIC RUN`, subject to recording
`complete=true`, `all_checks_passed=true`, and the documented float64/hash
limitations in the final receipt. This remains a deterministic RU diagnostic,
not a numerical interval certificate, statistical coverage result, or novelty
claim.
