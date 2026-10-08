# Final moment-geometry and Fan prior audit

**Audit date:** 2026-10-08
**Owner:** independent review A
**Scope:** bounded primary-source recheck of the proposed support-two and
J+1 claims. Only this review file was created or changed. No production
source, historical report, test, frozen result, or Git state was changed.
No new experiment was run.

## Access receipts

| Source | Access actually obtained | Relevant pointers |
|---|---|---|
| [Pinelis, On the extreme points of moments sets](https://arxiv.org/pdf/1204.0249), arXiv:1204.0249v1 | **FULL 10-page PDF read** from public arXiv. | Theorem 1, pp. 2-3, necessary atomic-partition/linear-independence condition; Corollaries 4-5, pp. 4-5, finitely atomic representations and affine optimization; Theorem 12, p. 8, Winkler support bound \(1+k\) for \(k\) additional affine restrictions. |
| [Henrion, Kružík & Weis, Extreme points and faces in the moment problem](https://arxiv.org/pdf/2606.21391), [HTML](https://arxiv.org/html/2606.21391v1), arXiv:2606.21391v1 | **FULL 17-page PDF and full HTML read** from public arXiv. | Theorem 2.6, pp. 4-5, injectivity on the smallest face; Proposition 3.2 and Example 3.3, pp. 5-6, \(d+1\) affine-extreme support and its assumptions/counterexamples; Theorems 4.5-4.6, pp. 7-8, affine-independent moment extremes; Theorems 4.19 and 4.21, pp. 11-12, when integral optimization can restrict to finite/extreme measures. |
| [Fan, Data-Driven Minimax-Regret Portfolio Optimization under Tail-Risk Ambiguity](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7486600) | **ABSTRACT/METADATA ONLY**. SSRN record reports 36 pages, posted 2026-09-21 and revised 2026-09-28. The direct delivery/full-text route was not available lawfully in this audit. | Abstract says training-score mixtures of competing tail-risk engines, validation on a frozen audit library, projection to admissible engine mixtures, and an LP from admissible-set extreme points. It does not say that the mixture is a probability-law mixture. |
| [Fan, Validation-Calibrated Risk-Function Ambiguity for Minimax-Regret Portfolio Optimization](https://papers.ssrn.com/sol3/Delivery.cfm/7492399.pdf?abstractid=7492399&mirid=1&type=2), [SSRN record](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7492399) | **ABSTRACT/METADATA ONLY**. The SSRN-indexed abstract reports 31 pages, posted 2026-09-23. The direct PDF endpoint returned HTTP 403 through the public access route; no bypass or contact was attempted. | Abstract says fixed candidate risk engines, independent validation, and a polyhedral ambiguity set over convex aggregations of implemented risk functions, with an ES-regret certificate and LP. It does not state a probability-law mixture or a support-two theorem. |
| [Fan author research-output page](https://sites.google.com/view/zheqifan/home/research-output) | **PUBLIC HTML fetched**. It exposes ordinary SSRN links for both 7486600 and 7492399; no alternate manuscript, repository copy, or lawful full-text link was visible. | Links confirm the two records and their submitted/under-review status; they do not expand full-text access. |

The Fan abstract descriptions above are therefore source-bounded. “Risk
engine,” “implemented risk function,” and “engine mixture” are the accessible
terms; treating either abstract as a probability-law mixture paper would be
an overstatement.

## Exact overlap with the support claims

### Pinelis and the general moment bound

Pinelis Theorem 1 states a necessary condition for an extreme point of a
moment set: an atomic non-null partition whose integrated moment vectors are
linearly independent. Corollary 4 represents the moments and any additional
integral objective by a finitely atomic measure with at most \(k\) atoms under
its hypotheses, and Corollary 5 transfers an affine supremum to such
representatives. Theorem 12 quotes Winkler's more familiar probability-measure
form: \(k\) additional affine restrictions allow at most \(1+k\) support
points. These are direct prior art for generic rank-based sparsity, including
the shape of the draft's “additional active rank” extension.

The overlap is not merely terminological. If a fixed own-action quantile cell
is written as a probability measure on the finite component index set, its
tail constraints are affine moment inequalities. A generic treatment with
normalization plus two active tail inequalities permits a \(1+2=3\)
component bound. For \(J\) ES levels, the naïve generic count is \(1+2J\)
before exploiting any special structure. Thus the broad claim “extreme
moment problems have finite-support optimizers” and the rank-count intuition
are established.

Pinelis does not state the draft's result. Its atoms are atoms of the measure
being optimized, whereas the draft's support count is the number of supplied
component laws \(P_r\); a component law can itself be continuous. Pinelis also
studies affine integral objectives over moment sets. The draft's
\(H_i(q)\) is a difference involving a bank lower envelope and is only
convex after conditioning on the evaluated action's own quantile cell. No
direct theorem in the inspected passages forms that ES-regret objective.

### Henrion--Kružík--Weis and the affine-independence framework

Theorem 2.6 characterizes affine-constraint extreme points through
injectivity of the constraint map on the smallest face. Proposition 3.2 gives
the generic \(d+1\) extreme-point representation with affine-independent
constraint images, and Example 3.3 records that the assumptions matter.
Theorem 4.5 gives the necessary affine-independence condition for finitely
many moment constraints; the paper notes that the resulting measures have
at most \(d+1\) atoms. Theorem 4.6 supplies a converse under a singleton
constraint value, while Theorems 4.19 and 4.21 concern preservation of
integral optimization values on finite/extreme measures under their measure
and boundedness assumptions.

This source substantially overlaps the draft's polyhedral/rank language and
the \(J+1\) shape. It does not state the nested-tail ES-cell lemma. The
current problem is a finite simplex of already supplied laws, not an
unrestricted probability simplex over outcomes, and its objective is
piecewise convex maximization rather than the source's linear integral
minimization. The source's generic \(d+1\) count does not by itself explain
why two tail inequalities at a quantile cutoff collapse to one effective
rank on the positive-support face.

### The narrow remaining interaction

For the evaluated action and threshold \(t\), the draft uses
\[
 Q_i(t)=\{q\in\Delta_R:a(t)^\top q\le\alpha\le b(t)^\top q\},
 \qquad b_r(t)-a_r(t)=P_r(L_i=t)\ge0.
\]

On this set, the evaluated ES is affine and the bank minimum is concave, so
the regret gap is convex and can be maximized at a vertex. If both tail
inequalities bind, then
\[
 (b(t)-a(t))^\top q=0.
\]
Nonnegativity forces every positively weighted component to have zero atom at
\(t\). On that face the two active equations coincide, leaving one effective
tail rank and therefore at most two positive component weights. Repeating
this one-rank-per-level argument gives the draft's \(J+1\) upper bound.

This is the only technically narrow part that remains plausibly distinctive:
the support count is for **component-law mixtures**, the objective is an
absolute ES gap against a bank minimum, and the reduction uses the
nonnegative atom-difference degeneracy of an own-action quantile strip.
Neither Pinelis nor Henrion--Kružík--Weis states this combination in the
inspected text. That non-hit is not evidence of priority. It may be an
elementary specialization of their generic affine-extreme geometry, so the
draft must not call it a new general moment theorem or a first support
theorem.

The finite \(J=2\) example with a strict three-component interior optimizer
is useful as a falsifier of incorrectly summing one-level edge certificates.
It does not establish novelty of the \(J+1\) count: generic moment theory
already supplies the surrounding support/rank framework, and the example is
an internal exact construction.

## Fan overlap and remaining distinction

Fan 7486600 is a close conceptual prior for minimax ES regret, frozen
validation/audit libraries, mixtures, and extreme-point LP computation. Fan
7492399 is an even clearer wording-level overlap for convex aggregations of
implemented risk functions, validation-calibrated regret, and polyhedral LP
ambiguity. On accessible abstracts, both mix **risk-engine scores/functions**;
the draft mixes supplied **probability laws before evaluating ES**. That is a
real object-level distinction, but not a priority result. Either full paper
could contain a law-mixture or support lemma that is absent from its abstract.

The safe citation wording is: “Fan's abstracts independently combine
ES-regret auditing with finite mixtures/convex risk-engine aggregations and
extreme-point LPs; the accessible text does not establish equivalence to our
probability-law simplex or exclude a closer theorem.” Do not write that Fan
“does not use probability laws” without the full text.

## Significance and priority judgment

**Broad novelty: negative.** Generic finite-support, affine-independence,
moment-rank, and extreme-point reduction are established by Pinelis,
Winkler's theorem as reproduced there, and Henrion--Kružík--Weis. The \(J+1\)
shape and “active rank adds to support” language cannot be presented as a new
general extreme-point theorem.

**Narrow technical significance: cautiously positive but unconfirmed.** A
specialized corollary could still be useful: an absolute ES-regret evaluator
over a finite bank and the full simplex of supplied component laws may reduce
to component edges because each own quantile strip has a nested nonnegative
atom degeneracy. This gives an auditable all-edge computation and explains
why the one-level result is sharper than the naïve two-inequality generic
count. The contribution is a derived computational composition, not a new
risk measure, forecaster, calibration guarantee, or generic moment theorem.

**Priority: unresolved.** The inspected full texts do not state the exact
own-quantile/bank-regret reduction, but search absence is not priority
evidence. Fan's inaccessible full texts and broader citation chains remain
open. The readiness label should remain
novelty_priority_confirmed=false and submission_ready=false.

## Decisive next gate

Have a human mathematical reviewer map the proof line by line to the
Pinelis/Henrion--Kružík--Weis hypotheses, explicitly prove the nested-tail
rank collapse for all quantile degeneracies, and search the cited
Winkler/Weizsäcker--Winkler chain for the same specialization. Separately,
obtain lawful full text for Fan only if it becomes publicly available. No
new stochastic sweep or benchmark is needed to resolve this prior-art gate.

## Evidence boundary

This review used the public full Pinelis and Henrion--Kružík--Weis PDFs/HTML,
the public SSRN metadata/abstract records, and Fan's public research-output
page. It did not access restricted material, contact authors, run tests,
reopen frozen outcomes, or edit any production/source file.
