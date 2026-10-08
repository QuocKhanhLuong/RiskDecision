# Independent compositional-risk generation B

Status: `INITIAL GENERATION RECORDED BEFORE LITERATURE SEARCH` (2026-10-08).

Focal question: **what useful, falsifiable compositional contribution can be
built around learned conditional tail risk, selection/decision quality, and
limited information, after prior negative novelty gates?** This document
records an independent AI-assisted generation round before opening external
literature. It is a proposal and falsifier design, not a novelty claim or human
peer review.

## Fixed boundary and evidence already known

The decision receives only the declared history `H_t` (the same past-512
information and locked portfolio bank). Future outcomes and hidden simulator
states are evaluator-only. Evaluation must separate: (i) common-target
conditional tail forecasts on the same portfolios, (ii) the decision quality of
the selected portfolio, and (iii) reserve or economic utility. Historical
CVaR, uncertainty penalties, OIC where applicable, sample splitting, HMM,
GARCH/FHS, DRO, and standard calibration are treated as baselines or known
ingredients. Earlier OIC/HAC work did not forecast next conditional risk under
dependence; the correctly specified Gaussian Markov HMM result is a diagnostic,
not novelty evidence. No new training or test outcome is used in this round.

## Independent ideas

### C1 — Order-aware posterior-mixture conditional ES for selection

**Problem formulation.** Suppose a learned conditional predictive law is
represented by component laws (F_{t,s,w}) for portfolio `w` and component or
regime `s`, with an observed-history posterior

\[
  \pi_t(s)=P(s\mid H_t),\qquad
  F^{mix}_{t,w}=\sum_s\pi_t(s)F_{t,s,w}.
\]

Use the tail risk of the *mixture law*

\[
  r^{mix}_{t,w}=ES_\alpha(F^{mix}_{t,w})
\]

for selection, optionally with a predeclared uncertainty reserve, rather than
the tempting average of component risks
\[
  r^{avg}_{t,w}=\sum_s\pi_t(s)ES_\alpha(F_{t,s,w}).
\]
The selector is `argmin_w r_t,w` over the locked bank. Components and
posteriors must be fitted from `H_t` only; no hidden state is supplied to the
selector. The evaluator may use the simulator state or the known conditional
law solely to compute the target.

**Known ingredients.** Regime or mixture conditional modeling, HMM-like
filtering, RU/ES computation, mixture concavity, and decision selection are
each established ingredients. The potentially useful interaction is that
noncommutation of ES and posterior mixing changes the *ordering of actions*,
so a forecast that looks reasonable component-by-component can select the
wrong portfolio under limited information. The contribution would be an
order-correct composition and a matched decision-quality evaluation, not a new
HMM or a claim that mixture concavity itself is new.

**Assumptions.** Each component law has a finite or numerically evaluable tail;
the posterior is measurable from `H_t`; the same component model, history,
bank, and tuning budget are used for `r^{avg}` and `r^{mix}`; and the mixture
law is the intended one-step predictive law. Parameter uncertainty must be
separated from regime uncertainty rather than silently folded into `pi_t`.

**Prediction.** `r^{avg}` can be anti-conservative and can reverse portfolio
ordering relative to `r^{mix}`. The order-correct selector should reduce
selected true conditional ES/regret in regimes with crossing tails, while the
two selectors should agree when component tails have a common ordering or the
posterior is degenerate. Common-target forecast scores may remain unchanged;
any decision gain must survive evaluation on the same fixed bank.

**Cheap exact falsifier.** Use upper-tail mass `alpha=.05`. In state 0 let
`A=0` and `B=1` deterministically. In state 1 let `A=10` deterministically
and let `B=11` with probability `.05`, otherwise `0`. At posterior weight
`pi(state1)=.05`, the averaged component ES values are
`r_A^avg=.5` and `r_B^avg=1.5`, so averaging selects A. The true mixture ES
values are `r_A^mix=10` and `r_B^mix=1.5`, so the order-correct rule selects B.
This is an exact atom-level ordering reversal. A single-state/equal-tail
Gaussian case is the converse falsifier: the interaction should collapse to
the baseline and add no gain. If an implementation cannot reproduce both
limits, stop before training.

**Strong matched control.** Freeze the component predictive laws and posterior
before held-out evaluation and compare: (a) averaged component ES, (b) exact
posterior-mixture ES, (c) a direct observed-history conditional ES model with
matched information and capacity, and (d) evaluator-only conditional truth.
Report common-target FZ/ES error, selected conditional ES/regret, selection
reversals, and reserve utility separately. A state-oracle selector is a
diagnostic upper-information control, never an equally informed baseline.

### C2 — Pairwise tail-order reserve under dependent selection

**Problem formulation.** Estimate a joint dependent error process for the
conditional ES surface over the bank, then form a confidence/reserve for each
pairwise ordering (D_t(a,b)=r_t(a)-r_t(b)). Select using a predeclared
upper-risk or posterior-dominance rule such as

\[
  \hat w_t=\arg\min_a\left[\hat r_t(a)+
  \lambda\,Q_{1-\gamma}\{\max_b(\hat D_t(a,b)-D_t(a,b))\mid H_t\}\right].
\]

The dependence estimate uses blocked or multiplier residuals and cross-fitting;
the selection cell or margin is fixed before assessment.

**Known ingredients.** Selective inference, block bootstrap/multiplier bands,
simultaneous risk surfaces, and uncertainty-penalized selection are known.
The possible contribution is a decision-level reserve targeted at pairwise
tail-order mistakes rather than marginal ES intervals, which could be useful
when portfolios have highly correlated errors.

**Falsifiers and control.** On a known Gaussian AR process with exact
conditional ES, the band should attain its predeclared conditional coverage;
on iid data it should not beat a correctly applicable OIC or independent-split
control at equal width. A large-margin selection case should show no material
benefit. If gains come only from wider reserves or block tuning, this collapses
to a standard selective/dependent bootstrap and is rejected as a new method.

### C3 — Nested-information selection-regret attribution

**Problem formulation.** Define an observed-information surface
`r_t^I(w)=ES(Y_{t+1}(w)|I_t)` and an evaluator-only richer-information surface
`r_t^O(w)=ES(Y_{t+1}(w)|O_t)`, with `I_t` contained in `O_t`. For a selector
`w_I` and a fixed evaluator comparator `w_O`, report the exact attribution

\[
 r^O(w_I)-r^O(w_O)
 = [r^O(w_I)-r^I(w_I)]
 + [r^I(w_I)-r^I(w_O)]
 + [r^I(w_O)-r^O(w_O)].
\]

The three terms are labeled information mismatch at the selected action,
observed-information decision/estimation mismatch, and comparator information
mismatch. They are descriptive signed terms; CVaR/ES does not provide a tower
property, so they must not be advertised as nonnegative values of information.

**Known ingredients.** Value-of-information comparisons, oracle controls,
crossed evaluation, and conditional risk are established. The useful
composition is a frozen attribution protocol that prevents an apparent
forecaster win from being caused by better information or an oracle selector.

**Falsifiers and control.** In a no-hidden-state DGP, `I_t=O_t` should make the
information terms vanish. In a known Markov DGP, the observed-history filter,
state oracle, fixed-bank selector, and direct learned selector should satisfy
the algebraic identity row by row. Failure indicates leakage or a sign error.
If the attribution does not change the interpretation of any method ranking,
it is a reporting aid rather than a useful contribution.

## Pre-search ranking and search gate

Initial ranking: **C1 strongest**, because it has an exact action-ordering
falsifier, a clear limited-information boundary, and a small bounded experiment
that can compare a composition operator without introducing a new forecaster.
C2 is likely to collapse to selective inference plus dependent bootstrap. C3 is
likely a valuable evaluator but a known value-of-information decomposition.

The literature search has not started. After this record, search at most eight
focused primary-source queries for C1: posterior or regime-mixture conditional
CVaR/ES, the distinction between ES of a mixture and mixture of ES, risk-aware
portfolio selection under partial information, and decision quality after
regime filtering. Record exact overlap, access/full-text status, and a narrow
remaining gap. No source result may be used to rewrite this initial generation.

## Initial decision

`C1 / PROPOSED / NOT RUN / NO NOVELTY CLAIM.` The minimum meaningful experiment
is an exact atom reversal followed by a frozen three-way selector comparison on
the same past-512 histories and locked portfolios. Stop if C1 agrees with the
average-risk baseline on all tail-crossing cases, if any gain is explained by
different component information or tuning, or if direct conditional ES matches
it at equal decision quality and reserve cost.

## Bounded post-search audit of C1

Search provenance: eight focused query strings were used after the initial
generation, with primary papers or their author/preprint records preferred.
Search results were used to test overlap, not to rewrite the initial ideas or
claim an exhaustive review. Access and overlap details are recorded in
`queries_b.json`.

### What the sources cover

Tselishchev's open preprint proves the central inequality: Expected Shortfall
is concave with respect to probability distributions, so ES of a finite
mixture is at least the posterior-weighted average of component ES values. This
is the mathematical reason that C1 can be more conservative and can change an
action ordering. The inequality itself is established prior art and cannot be
the contribution.

Bodnar et al.'s open Bayesian portfolio-selection preprint already uses a
posterior predictive distribution to compute VaR/CVaR and select portfolios
from observed data. Related published Bayesian VaR/CVaR work makes the same
posterior-predictive composition explicit. These are close on the
limited-information and selection dimensions. The bounded source views did
not find a direct experiment that holds component laws and the observed-history
posterior fixed while comparing ES-of-mixture against mixture-of-ES on the same
locked action bank and reporting selected conditional regret.

HMM scenario generation for mean-CVaR portfolio selection, regime-switching
WCVaR/DRO, and robust regime-switching portfolio papers cover regime filtering,
conditional tail risk, and allocation. Their objectives are scenario
generation, robust allocation, or model uncertainty; the exact aggregation
operator/order and the common-target versus selected-decision decomposition in
C1 were not verified as their stated contribution. This is a narrow remaining
gap in the checked sources, not evidence that no equivalent exists.

The Rockafellar--Uryasev variational representation
([DOI 10.21314/jor.2000.038](https://doi.org/10.21314/jor.2000.038)) is the
standard computational route for evaluating each supplied mixture law. It
further weakens any algorithmic novelty claim: the candidate's possible value
is the controlled decision consequence of applying the known operation to a
posterior predictive law.

### Adversarial overlap verdict

C1 is **not a new theorem and probably not a standalone new estimator**. If
the component predictive laws and posterior are already available, applying RU
to their posterior mixture is the standard posterior-predictive operation, and
the ES ordering inequality is known. The potentially useful contribution is a
small, falsifiable composition and evaluation protocol: isolate whether
correctly applying that operation changes portfolio decisions under limited
information, while controlling the component model, posterior, history, tuning
budget, and action bank. This may be publishable as a careful decision-quality
finding only if the ordering reversals occur and the matched experiment shows a
material selected-regret/reserve benefit that is not a better forecaster or
extra information. No novelty claim is supported by this bounded search.

### Strongest matched experiment, still not run

First run the exact atom reversal and a Gaussian/equal-component null. Then use
the same past-512 histories and locked bank in a frozen two-regime observed-data
simulation. Fit or freeze one component predictive law and one posterior model
on development histories; the selector receives only the posterior from
observed history. Compare exactly:

1. averaged component ES, `sum_s pi_s ES(F_s,w)`;
2. posterior-mixture ES, `ES(sum_s pi_s F_s,w)` (C1);
3. a direct conditional ES forecaster with matched information and tuning
   budget; and
4. an evaluator-only state oracle, reported as an information diagnostic.

The primary endpoints are common-target conditional ES/FZ error on every fixed
portfolio, selected true conditional ES/regret, and the frequency of action
ordering reversals. Reserve width/utility and posterior calibration are
secondary. Freeze the posterior, component model, alpha, selector tie rule,
and all tuning before held-out episodes. Do not give the selector hidden state
labels. Stop if the exact reversal cannot occur, if C1's gain disappears on
crossed common targets, if it requires extra information, or if the direct
model matches it at equal decision quality and reserve cost.

### Final status

`C1 / PROPOSED COMPOSITION / NOT RUN / HIGH PRIOR-ART OVERLAP / NO NOVELTY
CLAIM.` The minimum defensible next action is the exact falsifier plus the
matched aggregation-operator experiment above. C2 remains likely to collapse
to selective dependent inference, and C3 remains an attribution/control
protocol rather than a new risk estimator.

## Post-generation candidate audit: action-local minimax-regret hull

### Candidate and exact reduction

The new candidate is a finite-bank evaluator. For action (i), let the finite
RU representation be

\[
  E_i(q)=\min_{t\in T_i}\ell_{i,t}(q),\qquad
  \ell_{i,t}(q)=a_{i,t}+b_{i,t}q,\qquad q\in[\mathrm{lo},\mathrm{hi}].
\]

Here the support losses are fixed and the state/component probabilities vary
affinely with (q). Then, exactly,

\[
  g(q)=\min_i E_i(q)=\min_{i,t}\ell_{i,t}(q).
\]

The last expression is a pointwise minimum of affine functions and is
concave. More generally, the pointwise minimum of finitely many concave
functions on a common convex domain is concave: its hypograph is the
intersection of the concave hypographs (equivalently, apply the concavity
inequality and then take the minimum over the finite index set). The RU line
representation is still essential computationally here because it supplies a
finite lower-envelope/hull representation and explicit owner witnesses; it is
not needed for the abstract concavity fact.

For a fixed action (i), include the endpoints and every breakpoint at which
its own lower RU envelope can change. In the usual finite-support mixture,
these are the roots where a cumulative tail probability crosses the ES level,
with redundant roots and ties retained safely. Between consecutive own knots,
(E_i) is affine. Therefore

\[
  R_i(q)=E_i(q)-g(q)=\text{affine}-g(q)
\]

is convex on each such interval, even when (g) has additional kinks caused
by another action. A convex function on a compact interval reaches its
maximum at an endpoint, so the exact worst regret for action (i) is attained
at an endpoint or at one of (i)'s own knots. Competitor knots do not need to
be enumerated. This proves the proposed action-local witness reduction under
the displayed assumptions; it does not prove a generic result for arbitrary
conditional-risk surfaces.

If (K=\sum_i |T_i|), sorting lines by slope, dropping dominated parallel
lines, and building one global lower hull costs (O(K\log K)). Retain the
action and threshold owner(s) on each hull segment, including ties. Query that
hull at the (O(K_i)) own knots of each action; binary-search queries give
(O(K\log K)) total after knot generation, with (O(K)) storage. This avoids
an (M^2) table of pairwise action differences and an (M\times)all-knots
matrix. A strong comparator is an independent per-action RU evaluation at the
union of all actions' own knots, using the same global (g); for a tiny exact
fixture, enumerate all line intersections as a further check. Comparing only
to endpoint evaluation would be a weak baseline.

### Exact hand falsifier for the unnecessary competitor-knot claim

At \(\alpha=0.05\), let action A have loss 0 in state 0 and loss 10 in state
1, while action B has deterministic loss 1 in both states. Under state-1
probability (q\),

\[
  E_A(q)=\min(10,200q),\qquad E_B(q)=1,
  \qquad g(q)=\min(E_A(q),1).
\]

The global envelope has a competitor-induced kink at (q=0.005), while A's
own knots are only (0,0.05,1) (and B has endpoints). The A-regret values at
those knots are (0,9,9), so its exact supremum is 9; evaluating the extra
competitor kink is unnecessary. This is an exact piecewise-affine check of the
convexity proof, not a statistical experiment. An implementation should also
compare its result with direct RU evaluation on all union knots and, on small
instances, all line intersections.

### Degeneracies and scope boundaries

The own-knot set must contain every lower-envelope breakpoint. Cumulative-tail
crossings are sufficient for fixed finite support probabilities, but are not
sufficient if support losses or fitted parameters themselves depend on (q),
or if the RU line set is incomplete. Duplicate support values, zero masses,
parallel lines, and multiple coincident crossings require tie-safe handling;
the value is unchanged, but a single stored owner is not a complete witness at
a tie. The interval must be valid (for a two-component mixture, normally
\([0,1])); alpha=1 reduces to an affine mean and still needs the endpoints.

Adding a fixed action switching cost (c_i) is exact by replacing every line
(\ell_{i,t}) with (\ell_{i,t}+c_i) before building the global hull. A cost
depending on the previous action is a different state-indexed problem and
needs a separate hull per previous-action context (or an expanded action bank).

For finitely many fitted worlds (w), one hull and one action-local knot pass
per world is exact for an outer \(\max_w\max_q R_{i,w}(q)), since the finite
maxima commute. It is not a valid shortcut for \(\min_q\max_w R_{i,w}(q)\), an
expectation over worlds, or a model in which one shared fitted parameter
changes the lines across worlds; those objectives need their own partition and
order-of-optimization proof. Floating-point hull breakpoints and near ties
also need an independent RU comparator and explicit tolerances.

### Adversarial prior-art review and verdict

The bounded four-query search found substantial overlap. Rockafellar--Uryasev
provides the standard RU representation ([DOI
10.21314/jor.2000.038](https://doi.org/10.21314/jor.2000.038)). Huang, Zhu,
Fabozzi, and Fukushima's relative-robust CVaR paper ([DOI
10.1016/j.ejor.2009.07.010](https://doi.org/10.1016/j.ejor.2009.07.010);
[author-hosted PDF](https://repository.kulib.kyoto-u.ac.jp/dspace/bitstream/2433/87374/1/j.ejor.2009.07.010.pdf)) explicitly compares decisions with the
best decision under each uncertain distribution. Caçador, Dias, and Godinho
also formulate relative-robust portfolio solutions as minimax regret ([DOI
10.1111/itor.12674](https://doi.org/10.1111/itor.12674)). A CVaR relative-robust
portfolio formulation with LP/constraint-generation machinery is a particularly
close algorithmic comparator ([ScienceDirect record](https://www.sciencedirect.com/science/article/pii/S0377221721003702)). Generic finite-scenario
minimax-regret decision rules are also covered by Anderson and Zachary
([ScienceDirect record](https://www.sciencedirect.com/science/article/pii/S0377221723004095)).

The checked records did not expose a sentence claiming this exact
implementation reduction—one shared lower hull plus action-local RU knots and
owner witnesses. That absence is not evidence of novelty. The strongest
defensible status is **useful exact computational composition / likely
known convex-analysis corollary / no standalone novelty claim**. A bounded
experiment is justified only to measure wall-clock and witness benefits
against the strong all-union-knots RU comparator while proving identical
values and minimax-regret winners on exact fixtures. The candidate is not
evidence of improved forecasting, statistical coverage, or market performance.

### Correction recorded after independent review

The earlier sentence in this audit saying that the generic minimum of concave
functions is not concave was incorrect and has been replaced. For concave
(f_i) on a common convex domain,

\[
  \operatorname{hypo}(\min_i f_i)=\bigcap_i \operatorname{hypo}(f_i),
\]

and intersections of convex hypographs are convex; therefore \(\min_i f_i\)
is concave. The finite RU affine-line form remains the computational condition
that permits one global lower hull and owner witnesses, while the action-local
regret proof additionally requires each action to be affine between its own
complete lower-envelope knots. This correction was prompted by the root
reviewer on 2026-10-08 and does not change the high-overlap/no-novelty verdict.

## Final frozen adjudication: all96 evaluator and policy results

### Evidence boundary

I read `runs/compositional_risk/20261008/frozen/summary.json` for this
adjudication. I did not rerun the frozen benchmark, policy experiment, or
tests. The statements below are therefore reported results from that frozen
summary, not newly executed evidence in this review.

The summary reports 96/96 cases complete, no failed cases or numerical
warnings, zero selected-index disagreements, maximum regret error
2.22e-16, and maximum witness error 1.78e-15. Its reported case time is
21.579 seconds. These
values support numerical agreement between the action-local-knot bank-hull
path and the same-global-hull union comparator in the frozen cases, but they
do not establish a statistical guarantee; the summary explicitly records
`true_law_coverage_guarantee: false`.

### Runtime and decision findings

The reported `union_over_local` runtime ratio reaches 1.156 at the largest
tested 512x64 grid, with 1.122 at 512x16. The small grids
are slightly below one (about 0.971--0.993), so the local-knot path is slower
there. This is a modest, size-dependent evaluator speed result, not evidence
of a uniform O(K log K) wall-clock win. The lower local evaluation counts
and identical values/winners are the stronger exactness result; asymptotic
claims still need independent scaling measurements.

The exploratory 32-history policy blocks do not establish a new decision
policy. In the reported stationary block, shared full/endpoints has mean true
net regret 7.7511e-5, better than rectangular full/endpoints
1.4938e-4, but worse than point/nominal components 5.2735e-5. Full and
endpoints are identical in the reported
metrics. In the component-shift block, shared is 3.6812e-4, versus 2.4748e-4
for rectangular and 2.9556e-4 for point; shared also has 24 harmful switches in
that block. These are exploratory pilot outcomes with 32 histories, not a
causal claim that shifting causes the difference. They provide no coverage
guarantee and no evidence that the hull evaluator improves the forecaster.

The root-provided SSRN abstract for Fan (2026), [Data-Driven Minimax-Regret
Portfolio Optimization under Tail-Risk
Ambiguity](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7486600),
describes a frozen-library audit, engine mixtures, relative ES/regret, and LP
machinery. The abstract is the available source here; the full paper and its
definitions were unavailable. It reinforces prior-art overlap, but I do not
equate its relative-ES objective with this finite-\(q\) difference or claim
that it contains this hull reduction.

### Final adjudication and next gate

The candidate passes the frozen exactness check as a **reported computational
composition**: it reproduced the strong union comparator to numerical
precision and avoided the unnecessary all-action/all-knot evaluation count.
The measured speed benefit is small and disappears or reverses on small
grids. Together with RU, relative-robust CVaR, generic minimax-regret prior
art, and the Fan abstract, the evidence supports no standalone novelty claim
and no scientific or market-performance claim.

The one remaining gate should be a pre-registered scaling audit on exact
synthetic line banks: after warmup, compare local-knots/global-hull,
all-union-knots/global-hull, and tiny-instance all-intersection enumeration at
fixed \(M,K\) sizes, recording wall time, memory, regret values, witness
owners, and winners. Require tolerance-level equality and zero winner
disagreements, then require a repeatable runtime advantage beyond the observed
small-grid overhead at the intended scale. If that advantage is not stable,
close this as an exact evaluator optimization with no novelty priority.

### Objective wording correction

The candidate objective is **absolute ES-difference regret**,

\[
R_i(q)=ES_i(q)-\min_j ES_j(q),
\]

with no division or ratio. The runtime `union_over_local` ratio reported above
is only a benchmark timing ratio. Fan's abstract uses the phrase “relative
ES/regret”; the full paper and exact definitions were not read, so this audit
does not assume that Fan's relative ES is a ratio or identify it with the
candidate's absolute ES difference. This correction preserves the prior
adjudication and is appended rather than rewriting its history.
