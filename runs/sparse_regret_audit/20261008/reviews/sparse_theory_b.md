# Independent sparse-simplex theorem audit B

Status: `INDEPENDENT PROOF RECORDED BEFORE LITERATURE SEARCH` (2026-10-08).
This is an AI-generated mathematical review of
`runs/sparse_regret_audit/20261008/root_presearch_derivation.md`; it is not a
peer review and does not establish novelty.

## Candidate under review

There are R component laws, a finite action bank with i=1,...,M, and a
full mixture simplex

\[
  \Delta_R=\{q\ge 0:\mathbf 1^\top q=1\}.
\]

For each action, component support losses are finite and fixed; only their
mixture probabilities vary with q. With upper-tail probability alpha in
(0,1], define absolute regret

\[
  \mathcal R_i(q)=ES_{\alpha,i}(q)-\min_j ES_{\alpha,j}(q).
\]

The proposed claim is that a maximizer of max over i and q in Delta_R of
R_i(q) exists on a simplex face with at
most two positive components. The claim is initially marked `PROPOSED`, not
validated.

## Independent derivation before search

Fix an action and merge equal loss values across all components into
x_1<...<x_S. Let p_rs >= 0 be component r's mass at x_s, and let

\[
  m_s(q)=\sum_r q_rp_{rs},\qquad
  C_k(q)=\sum_{s\le k}m_s(q),\qquad \beta=1-\alpha.
\]

For a quantile cell with threshold x_k, use the closed polyhedron

\[
  Q_k=\{q\in\Delta_R:C_{k-1}(q)\le\beta\le C_k(q)\}.
\]

The nonempty Q_k cells cover the simplex. On Q_k, the finite-support
expected shortfall has the affine expression

\[
 ES_{\alpha,i}(q)=\alpha^{-1}
 \left(\sum_{s>k}x_sm_s(q)+x_k\big(C_k(q)-\beta\big)\right),
\]

with the usual endpoint convention. Adjacent expressions agree on shared
boundaries. Thus the action's ES is affine on every own quantile cell.

Each action ES is concave in q, and the finite pointwise minimum of
concave functions is concave on the common simplex (its hypograph is the
intersection of the action hypographs). Hence

\[
  q\mapsto ES_{\alpha,i}(q)-\min_jES_{\alpha,j}(q)
\]

is convex on Q_k. A convex function on a compact polytope has a maximum
at a vertex, so it remains to bound the support of a vertex of (Q_k).

Let I={r:q_r>0} at a cell vertex. The relative interior of the
simplex face on I has dimension |I|-1, and the cell contributes only
the two cumulative inequalities above. If at most one is active, at most one
independent equality cuts that face, so a vertex has |I|-1 <= 1, hence
|I| <= 2. If both are active, then m_k=C_k-C_{k-1}=0. Nonnegative
component masses and positive q_r force p_rk=0 for every r in I.
On that remaining positive-support face, the two cumulative equalities have
the same restriction, so again there is at most one independent equality and
|I| <= 2. Zero atoms and rank-deficient constraints only reduce the rank.

Therefore the proposed two-component support bound is **proved for finite,
fixed, merged supports and the full simplex**, subject to the stated absolute
ES regret objective. The proof is geometric; it does not imply a forecaster,
coverage, or market-performance result. Fixed action costs add constants to
the relevant ES surfaces and do not change the support argument.

### Ties, zero masses, and R>=4

Equal loss values must be merged before defining C_k; otherwise artificial
zero-width thresholds can be mistaken for two independent constraints. An
atom with zero mass for every component should be removed. An atom that is
zero only at a candidate q is handled by the m_k(q)=0 face argument.
The dimension argument does not depend on R, so it applies unchanged for
R>=4. Empty cells and duplicate crossings can be discarded after taking
their closures.

### Exact sharpness fixture: two components are necessary

Take alpha=0.05 and two components. Action A is deterministic loss 0 in
component 0 and deterministic loss 10 in component 1. Action B has loss 1
deterministically in component 0, and in component 1 has loss 11 with
probability 0.05 and loss 0 with probability 0.95. If q is the
component-1 weight,

\[
 ES_A(q)=\min(10,200q),\qquad ES_B(q)=1+10q.
\]

The A-regret is zero at both simplex vertices q=0 and q=1, while at
q=0.05, ES_A=10, ES_B=1.5, and A-regret is 8.5. The maximum
is unique there: for q<=0.05 it is max(190q-1,0), and for q>=0.05 it is
max(9-10q,0). It therefore requires both components and shows that the bound
cannot generally be reduced to one component.

### Why constrained mixture sets can fail edge sufficiency

The proof uses the full simplex. For a constrained convex set, its vertices
need not lie on simplex edges. An exact example at alpha=0.05 has three
components, action A with deterministic losses (1,0,0), and action B with
deterministic loss 0 in every component. On

\[
 Q=\{q\in\Delta_3:q_1\le0.04,\ q_2\ge0.10,\ q_3\ge0.10\},
\]

every feasible point has all three coordinates positive, while
ES_A(q)=20q_1 on Q. The maximum is attained at q_1=0.04 and
requires three positive components. Thus probability boxes, trust regions,
or moment constraints require a new active-constraint rank analysis; they
cannot inherit full-simplex edge sufficiency automatically.

### Weighted spectral extension: provisional bound

For a finite positive weighted sum of J distinct ES levels,

\[
 S_i(q)=\sum_{\ell=1}^J w_\ell ES_{\alpha_\ell,i}(q),\qquad w_\ell>0,
\]

partition the simplex by one quantile cell for every level. The same argument
makes S_i-min_j S_j convex on each product cell. On a support face, each
level contributes at most one independent cumulative equality: if both sides
of that level's quantile bracket bind, its threshold atom has zero mixture mass
and the two restrictions coincide. Thus a cell vertex has support at most
J+1, provided supports are finite, fixed, merged, and the objective is a
finite ES sum. This is a proposed extension pending adversarial checks; a
continuous spectral weight, VaR terms, or active ambiguity/moment constraints
needs a separate rank or limit argument. Generic extreme-point/moment
sparsity should be treated as prior-art risk, not as evidence of a new
specialization.

## Search status

No external source was opened before the proof and fixtures above were
recorded. The bounded primary-source search begins only after this section.

## Independent finite checks (actual run)

The optional review script
`runs/sparse_regret_audit/20261008/reviews/sparse_theory_check.py` was run
with Python 3.11 after the proof was recorded. The first run exposed and
fixed a fixture assertion that accidentally checked the bank-wide maximum at
the endpoints instead of action A's regret; this was a review-script error,
not a theorem counterexample. The corrected run printed:

```text
sharpness_ok [8.5, 0.0]
constrained_counterexample_ok [0.7999999999999999, 0.0]
single_level_R4_ok vertex_max 20.586660657430585 sample_max 20.553906122919848
weighted_J2_R4_ok max_support 2
all_checks_passed
```

This is a small enumeration and 20,000-point diagnostic sample, not an
independent proof, stress test, statistical experiment, or coverage result.
It checks the intended geometry for one (R=4) finite bank and the explicit
edge/constrained fixtures. No production code, model, or historical result
was changed.

## Bounded primary-source search after proof

Six focused search query strings were used after the derivation above. The closest
records and their access status were:

1. [A relative robust approach on expected returns with bounded CVaR for
   portfolio selection](https://www.sciencedirect.com/science/article/pii/S0377221721003702)
   (publisher HTML/search text accessible; full article not independently
   retrieved). It formulates scenario-based minmax regret with CVaR, dual/LP
   reformulations, and constraint generation. This is close on CVaR regret
   computation, but its scenarios are a finite set of alternatives; the
   checked record did not state the full-simplex quantile-cell support-two
   theorem.
2. [Minimax decision rules for planning under uncertainty: Drawbacks and
   remedies](https://www.sciencedirect.com/science/article/pii/S0377221723004095)
   (publisher abstract accessible; full text not retrieved). It analyzes
   finite-scenario minimax regret for finite and convex decision sets. This is
   generic decision-theory overlap, not a verified ES mixture-cell result.
3. [Robust Optimal Portfolio in a Mixture Setting with Partial
   Ambiguity](https://arxiv.org/abs/2603.00851) (arXiv abstract/HTML page
   accessible; full paper not independently inspected). It studies unknown
   mixture components/weights with CVaR and reduces the problem to a
   convex-nonconvex minimax problem. It is direct mixture/CVaR context, but no
   support-two regret maximizer was stated in the checked record.
4. [An Approximate Algorithm for Sparse Distributionally Robust
   Optimization](https://www.mdpi.com/2078-2489/16/8/676) (publisher page
   accessible). It uses sparsity and CVaR in a DRO algorithm, but its sparse
   approximation and ambiguity setting differ from fixed component laws and
   full-simplex absolute ES-difference regret.
5. [Worst-case conditional value-at-risk and conditional expected shortfall
   based on covariance information](https://justc.ustc.edu.cn/article/pdf/preview/JUSTC-2022-0023.pdf)
   (open nine-page PDF). Its moment-constrained worst-case CoES theorem has a
   two-point extremal marginal in a different continuous-distribution
   problem. That supports generic extremal-distribution prior-art risk, not
   this finite mixture-simplex theorem.
6. [Extreme Points of Moment
   Sets](https://doi.org/10.1287/moor.13.4.581) (publisher abstract and DOI
   record accessible; PDF not independently retrieved). Winkler characterizes
   extreme points under finitely many generalized moment conditions and uses
   them to optimize affine functionals. This is the generic extreme-point
   prior-art anchor behind any (J+1)-style extension; it does not state the
   finite-support ES quantile-cell argument or the absolute-regret edge result.

The six query strings were: `CVaR mixture distribution worst-case expected
shortfall two point mixture extreme points theorem`; `sparse extreme
distributions convex risk measure CVaR finite support mixture`; `minimax regret
CVaR distribution ambiguity expected shortfall portfolio finite scenarios`;
`spectral risk measure extreme point support J+1 expected shortfall`;
`Winkler extreme points moment sets probability measures support theorem
primary paper`; and `finite moment problem extreme points probability measures
support n+1 primary source`. Search was bounded to these strings and the
records above; it is not an exhaustive novelty review.

Known anchors from the earlier RiskDecision literature audit remain relevant:
the [Rockafellar--Uryasev RU
representation](https://doi.org/10.21314/jor.2000.038) and
[Tselishchev's finite-mixture ES concavity
result](https://arxiv.org/abs/1910.00640). RU supplies the finite affine-cell
calculation, while mixture concavity and elementary polyhedral geometry make
the present support argument look like a likely corollary. The bounded search
did not find a source explicitly stating this exact absolute-regret
full-simplex edge reduction, but that absence is not evidence of novelty.

## Adjudication

For the stated finite-support/full-simplex model, the support-at-most-two theorem
survives adversarial review. The key conditions are complete merging of equal
loss atoms, nonnegative component masses, a common full simplex, and absolute
ES-difference regret. Fixed action costs preserve the proof. The two-component
sharpness fixture shows that the result is exact as a bound: singleton
components do not suffice.

The theorem does not transfer automatically to probability boxes, trust
regions, moment constraints, continuous component laws, q-dependent
support losses, or other nonlinear parameterizations. On a constrained
polytope, the right replacement is an active-constraint rank bound; the
explicit Q fixture has a maximizing vertex with three positive
components. A finite positive J-level ES sum has the provisional
support-at-most-J-plus-one extension by the same rank argument, but generic
moment/extreme-point sparsity and spectral-risk literature make this a
high-prior-art-risk corollary. No standalone novelty claim is justified.

If the admissible mixture set also has d independent active affine moment
constraints on the positive-support face, the same dimension count gives the
conditional bound support-at-most-J-plus-d-plus-one, when the finite cell description
remains valid. This is only a rank bookkeeping statement; inequalities,
nonlinear constraints, or redundant/degenerate moments must be audited by
their actual active rank.

The strongest defensible contribution is therefore an exact evaluator
reduction for a narrowly specified ambiguity set: enumerate component pairs,
apply the existing two-component ES-regret hull on each edge, and take the
maximum. A meaningful next gate would be an exact implementation comparison
against direct cell-vertex enumeration on frozen finite fixtures, including
zero atoms, tied losses, R>=4, and constrained-set rejection cases. The
gate should require identical regret values and witnesses to numerical
tolerance; it should not be presented as improved conditional forecasting,
coverage, or market performance.

## Refinement: finite support is unnecessary for one ES level

This refinement was derived before the two direct searches recorded below;
the earlier six-source audit is a separate bounded search. Let L_{i,r} be
any integrable loss law for action i under component r, with no finite
support assumption. Fix 0<alpha<1, and let q* be any mixture at which action
i's absolute regret is evaluated. Choose a finite alpha-upper quantile t of
the mixture loss, so

\[
  a_r=P_r(L_{i,r}>t),\qquad b_r=P_r(L_{i,r}\ge t),
  \qquad a\cdot q^*\le\alpha\le b\cdot q^*.
\]

Define the compact polytope

\[
  Q(t)=\{q\in\Delta_R:a\cdot q\le\alpha\le b\cdot q\}.
\]

For every q in Q(t), t remains an upper-tail quantile and

\[
  ES_{\alpha,i}(q)=t+\alpha^{-1}
    \sum_rq_r\,E_r[(L_{i,r}-t)_+],
\]

which is affine in q. The benchmark g(q)=inf_j(ES_{alpha,j}(q)+c_j) is
concave for any finite-valued comparator class, including an infinite one,
because an arbitrary pointwise infimum of concave functions is concave.
Therefore action-i regret is convex on Q(t), and its maximum on Q(t) is
attained at an extreme point with regret at least that at q*.

The extreme-point support proof needs only the two tail inequalities. On the
positive-support face I={r:q_r>0}, at most one of them can be an independent
active equality unless both bind. If both bind, then

\[
  0=(b-a)\cdot q=\sum_{r\in I}q_rP_r(L_{i,r}=t).
\]

Nonnegativity forces P_r(L_{i,r}=t)=0 for every r in I, so the two tail
equalities coincide on that face. The face then has at most one independent
equality, giving |I|-1 <= 1 and |I| <= 2. Applying this to an action
attaining the global finite-bank maximum proves that a support-two maximizer
exists for arbitrary integrable component laws. For an infinite comparator
class where a supremum need not be attained, the same argument applied to
every near-maximizing q* proves equality of the full-simplex supremum and the
support-two supremum, assuming the regret is finite.

At alpha=1, ES is the mean, every action surface is affine, and regret is
convex on the whole simplex; a simplex vertex with support one suffices.
Fixed action costs remain intercept shifts. The only quantile requirement is
that the component mixture be integrable and real-valued; a finite quantile
exists for 0<alpha<1. This extends the original result to continuous and
infinite-support laws without changing its status as a geometric evaluator
result.

## Exact rational sharpness for the finite J=2 extension

The provisional J+1 bound is sharp. Consider one action A with three
components and the following rational laws; action B is deterministic zero
loss in every component.

| component | loss:probability |
|---|---|
| 1 | 0:309/1000, 3:235/1000, 9:147/1000, 14:309/1000 |
| 2 | 0:58/1000, 7:790/1000, 14:130/1000, 16:22/1000 |
| 3 | 0:685/1000, 10:161/1000, 18:88/1000, 20:66/1000 |

Use S=(ES_{1/5}+ES_{3/5})/2. Since B has zero loss, A's spectral regret
is S. Exact enumeration of all 12 joint quantile-cell vertices gives a
unique maximum at

\[
 q^*=\left(\frac{29412}{97937},\frac{26879}{97937},
             \frac{41646}{97937}\right),
\]

where the cumulative mass at loss 0 is 2/5 and the cumulative mass at loss
at most 10 is 4/5. The exact values are

\[
 S(q^*)=\frac{750784201}{58762200}\approx12.776652,
 \qquad
 \max_{q\text{ on a simplex edge}}S(q)=\frac{82963}{6600}
 \approx12.570152,
\]

with strict gap

\[
 \frac{1112324}{5386535}\approx0.206501.
\]

The check is in
`runs/sparse_regret_audit/20261008/reviews/j2_sharpness_check.py`; its actual
Python 3.11 run printed the exact optimizer, edge maximum, gap, 12 vertices,
and `all_checks_passed`. This is a finite exact fixture and enumeration, not a
statistical or forecasting result.

## Direct prior-overlap search for the refinement

The [Tselishchev preprint](https://arxiv.org/abs/1910.00640) is the closest
mathematical anchor: it proves ES concavity with respect to probability
mixtures (full arXiv HTML available). It does not, in the checked text,
state the quantile-tail polytope or support-two regret maximizer.
[Distributionally Robust Regret Minimization](https://arxiv.org/abs/2412.15406)
has full arXiv HTML available and derives worst-case CVaR-of-regret
reformulations over Wasserstein balls; its ambiguity set and decision variable
differ from this component-weight simplex, and no support-two component
theorem was identified. The [spectral-risk representation
record](https://link.springer.com/article/10.1007/s00186-021-00746-w) states
that spectral risk measures are mixtures of ES levels, but provides no finite
J+1 simplex-support result in the checked passage. These are strong prior-art
overlaps for the ingredients, not direct equivalents. The two new query strings
were `expected shortfall mixture weights extreme point two components theorem`
and `CVaR convex combination distributions support two components regret`.
No claim of novelty follows from the bounded search's failure to find an exact
match.

### Refined verdict

The one-level support-two statement is stronger than the original finite-
support formulation and is correct for arbitrary integrable component laws,
full simplex mixtures, and finite-valued absolute ES-difference benchmarks.
The J=2 fixture confirms that support three can be genuinely necessary for a
two-level spectral sum, so the J+1 extension is not merely an artifact of
loose counting. Both results remain likely convex/extreme-point corollaries
with substantial prior-art risk. The next implementation gate is an exact
continuous-law evaluator test using quantile-tail constraints and the rational
J=2 fixture, compared against direct cell enumeration; no neural sweep or
statistical coverage claim is warranted.
