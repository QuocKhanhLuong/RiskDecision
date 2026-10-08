# Final proof audit (independent B)

## Evidence boundary

I read `papers/sparse_es_regret/THEORY.md`, the exact J=2 fixture used by the derivation, and the continuous-law diagnostic script. This is a mathematical source review, not a new experiment or a human peer review. The root reports that the post-run verifier checked all 168 saved input recipes, all numerical witnesses, the 72 exact rational witness regrets, and the recorded historical hashes; those are reported execution results here, not executions by this reviewer.

## Verdict on the core theorem

Theorem 1 is mathematically sound under its stated assumptions. The key correction is correctly present: a finite pointwise minimum of concave functions is concave, since its hypograph is the intersection of the individual convex hypographs. Therefore `g=min_j(F_j)` is concave and `-g` is convex.

For a maximizer `q*` of one action's regret, fixing an upper-tail quantile `t*` gives the nested-tail polytope

`Q={q: P_q(L_i>t*) <= alpha <= P_q(L_i>=t*)}`.

The fixed RU threshold is valid throughout `Q`, so that action's ES is affine there. Regret is consequently convex on `Q`, and a maximum is attained at a vertex of `Q`. Lemma 2's face-rank argument is valid: if both tail inequalities are active, positivity on the support and `a<=b` force `a=b` on that support, so the two active rows have rank one rather than two. Thus a vertex has at most two positive component weights. The argument handles ties, zero component masses, dependent active rows, and lower-dimensional simplex faces.

The continuous-law extension is also valid for arbitrary integrable real-valued component laws. For `0<alpha<1`, common finite lower and upper thresholds can be chosen across the finite component family, which bounds all minimizing RU thresholds and establishes continuity. A finite upper-tail quantile exists for every mixture, and the same polytope/vertex argument applies. The `alpha=1` case is correctly separated as the linear expectation case, whose convex regret maximum over the simplex occurs at a pure component.

Theorem 2's `J+1` support bound follows from the same rank count when all spectral weights are positive and each level contributes one nested-tail pair. The stated `J+d+1` version is correct provided `d` means a uniform upper bound on the rank of the additional active affine constraints after restriction to each positive-support simplex face. Affine mean terms contribute no additional rank. The proof does not claim sharpness for every `J,d`, which is the right boundary.

## Sharpness and algorithmic corollary

The exact two-level fixture is a valid sharpness witness for the `J+1` bound as presented. Its two-dimensional cell enumeration includes the simplex-face constraints and both tail-cell pairs, evaluates every feasible cell vertex, and compares all support-at-most-two points. The reported unique positive three-component maximizer and strict edge gap are therefore an appropriate finite rational witness, subject to the stated “working draft, not human reviewed” status.

The shared-hull corollary is also correct. On a finite two-component edge, each action ES is the minimum of its finite RU lines, and the bank benchmark is the minimum over the union of all action lines. Between consecutive breakpoints of an action's own ES, that action is affine while the negative benchmark is convex, so its regret is convex and the interval maximum is at an own breakpoint or an endpoint. Competitor-only knots need not be queried. The independent unrestricted-simplex LP formulation in the theory has the correct `z <= own lines` constraints and `z - competitor-line` objective.

Two wording refinements are needed but do not block the proof:

1. The claimed `O(K log K)` hull cost is the envelope-construction cost after finite RU line coefficients and sorted supports are available. End-to-end finite-support preprocessing also includes per-action support sorting/cumulative coefficient construction, such as `O(MS log S)` in a straightforward implementation, plus line generation. The stated bound should be read as the shared-hull stage or amended to include preprocessing.

2. In the constrained-simplex example, it is not true that every feasible point has three positive coordinates: `q1=0` with `q2,q3>=.10` is feasible and has support two. The intended and correct statement is that the maximizing point has `q1=.04` and, because both `q2,q3>=.10`, every maximizer has all three coordinates positive; no feasible support-at-most-two point attains the `.8` maximum. This does not affect the claimed failure of the unconstrained support-two theorem under added constraints.

The continuous diagnostic is useful sanity evidence but is not part of the arbitrary-law proof. Its candidate construction emphasizes pairwise tail crossings and is not itself a complete generic vertex enumerator for every possible one-active or pure-simplex vertex. The proof, rather than that diagnostic, carries the general theorem. The exact J=2 enumeration and the reported post-run witness verifier supply the relevant finite execution evidence.

## Final adjudication

I find no mathematical blocker in the working derivation. It is ready to serve as a bounded mathematical draft of the finite/full-simplex support-two theorem, the weighted `J+1` extension under its rank condition, the J=2 finite sharpness witness, and the action-local shared-hull evaluator. The draft must retain its explicit scope: it is not a new ES definition, a statistical coverage result, a forecaster result, or an established priority claim. This is an AI review only; human peer review and priority remain open.
