# Sparse witnesses for ES regret over mixtures of component laws

**Working derivation, 2026-10-08.** Proof reviewed by the root and two AI
reviewers; not an independently published or human-reviewed theorem. Priority
is unresolved. The RU formula, mixture concavity and extreme-point reasoning
are established ingredients, explicitly credited in the manuscript.

## Setting

Let P_1,...,P_R be probability measures on a common measurable space, R finite.
Let L_1,...,L_M be fixed real-valued measurable losses, M finite, integrable
under every P_r. Dependence between different actions' losses is unrestricted.
Only their marginals enter this criterion. For q in the closed simplex Δ_R,
P_q=sum_r q_r P_r. Let c_i be finite fixed action costs. Define upper-tail ES,
using tail mass α (not confidence level), by

\[
 E_i(q)=\inf_{t\in\mathbb R}\left[t+\alpha^{-1}
            \sum_r q_r\mathbb E_{P_r}(L_i-t)_+\right],
 \quad F_i(q)=E_i(q)+c_i,\quad
 g(q)=\min_{1\le j\le M}F_j(q),\quad H_i(q)=F_i(q)-g(q).
\]

For 0<α<1 the infimum is attained at any t satisfying
P_q(L_i>t)≤α≤P_q(L_i≥t). This includes fractional treatment of threshold
atoms. For α=1, ES is the expectation. Our subject is ES_i−min_j ES_j,
not ES of the pointwise loss difference, and not a percentage ratio.

## Lemma 1: continuity and concavity

For each i, E_i is finite, continuous and concave on Δ_R. Consequently g is
continuous and concave, H_i is continuous and its maximum exists.

**Proof.** The RU expression at fixed t is affine in q; an infimum of affine
functions is concave. Choose finite a<b so that for every component,
P_r(L_i≥a)>α and P_r(L_i>b)<α. Such a,b exist for a finite collection of
real-valued laws. The same strict inequalities hold for every mixture, so a
minimizing threshold can always be chosen in [a,b]. On this interval the
coefficients E_r[(L_i−t)_+] are finite and uniformly bounded, since they are
at most E_r|L_i|+max(|a|,|b|). Thus all the affine RU functions are uniformly
Lipschitz in q, and their infimum is continuous, including on simplex faces.
The hypograph of min_j F_j is the intersection of their convex hypographs,
so g is concave; a finite minimum preserves continuity. Compactness of Δ_R
gives attainment. For α=1 the assertions follow from linearity. □

## Lemma 2: a nested-tail polytope has sparse vertices

Let a,b in R^R satisfy a_r≤b_r. Every vertex of

\[
 Q=\{q\in\Delta_R:a^Tq\le\alpha\le b^Tq\}
\]

has at most two positive coordinates.

**Proof.** At a vertex q let I={r:q_r>0}. The smallest simplex face containing
q has dimension |I|−1. At most two further inequalities can be active. If
zero or one are active their rank is at most one. If both are active,
sum_{r∈I} q_r(b_r−a_r)=0. Each summand is nonnegative, so b_r=a_r for every
r∈I. Restricted to this face the two active equalities are therefore the
same equality. In all cases their active rank on the face is at most one.
A vertex requires |I|−1≤1. This argument handles empty Q, equal coefficients,
zero atoms and dependent rows without a nondegeneracy assumption. □

## Theorem 1: two component laws suffice for every action

Under the setting above, for each i and 0<α<1,

\[
 \max_{q\in\Delta_R}H_i(q)
 =\max_{\substack{q\in\Delta_R\\ |\operatorname{supp}q|\le2}}H_i(q).
\]

For α=1 the support bound improves to one. The same bound holds regardless
of the number of bank actions or whether the component losses have finite,
continuous, mixed, or unbounded integrable supports.

**Proof.** Let q* maximize H_i and choose one of its upper-tail quantiles t*.
Set a_r=P_r(L_i>t*) and b_r=P_r(L_i≥t*). On the nonempty compact polytope
Q_i(t*)={q:a^Tq≤α≤b^Tq}, t* remains a valid minimizing RU threshold. Hence
E_i, and therefore F_i, is affine on Q_i(t*). By Lemma 1, −g is convex.
Thus H_i is convex **on this polytope**, without an assertion of global
convexity. Express q* as a convex combination of its vertices. Convexity
ensures at least one vertex v satisfies H_i(v)≥H_i(q*). Lemma 2 gives
|supp(v)|≤2. Global maximality of q* implies equality. When α=1, F_i is
affine on the entire simplex, so the same argument uses simplex vertices. □

This is a support bound on **component laws**, not the number of atoms in
the underlying loss law. In particular two continuous components can still
produce a continuously distributed worst-case loss.

## Sharpness at one ES level

Let α=1/20. Under component 1, action A has loss0 and B loss1. Under
component2, A has loss10 surely and B loss11 with probability1/20 and loss0
otherwise. If q is the weight of component2,

\[
 E_A(q)=\min(10,200q),\qquad E_B(q)=1+10q.
\]

Action A has zero regret at both pure components. Its unique worst regret
is 17/2 at q=1/20. Thus checking only supplied laws fails, even for two
actions. Both component weights are necessary. This construction was already
derived in the preceding mixture-order audit and is **reused**, not new
experimental evidence. The new full-simplex implementation rechecks it.

## Theorem 2: finitely many ES levels and affine constraints

Replace each E_i by S_i=sum_{l=1}^J w_l ES_{α_l}(L_i), w_l>0, 0<α_l<1.
An additional affine mean term with nonnegative weight is allowed and does
not increase J. With g=min_j(S_j+c_j), each action's worst regret on the
full simplex has an optimizer with at most min(R,J+1) positive coordinates.
The α_l need not be distinct, but merging equal levels can tighten the bound.

More generally, let the admissible set be a nonempty closed polytope in Δ_R.
If the additional active affine constraints have rank at most d when
restricted to any positive-support face (excluding normalization), the bound
is min(R,J+d+1).

**Proof.** At a maximizing q*, fix one valid quantile for each of the J
levels. Intersect the J nested-tail polytopes (and, if present, the affine
ambiguity polytope). S_i is affine there and −g is convex. Its vertices
therefore suffice. At a vertex with positive support I, each quantile pair
contributes active rank at most one on that face by the same nonnegative
atom-mass argument as Lemma2. The extra ambiguity constraints contribute at
most d. Hence |I|−1≤J+d. Continuity and existence follow from the finite sum
version of Lemma1. □

This rank count is a specialization of ordinary polyhedral/moment sparsity,
not a new general extreme-point theorem. The construction below establishes
sharpness for every J with distinct levels and no extra constraints. No
general sharpness in the additional rank d or nonlinear region is claimed.

## Two ES levels really can require three components

Take action B to be constant0 and action A with these component laws:

| Component | Loss: probability |
|---|---|
| 1 | 0:309/1000; 3:235/1000; 9:147/1000; 14:309/1000 |
| 2 | 0:58/1000; 7:790/1000; 14:130/1000; 16:22/1000 |
| 3 | 0:685/1000; 10:161/1000; 18:88/1000; 20:66/1000 |

For S=(ES_{1/5}+ES_{3/5})/2, exact rational enumeration of all joint
quantile-cell vertices finds a unique maximizer

\[
 q^*=(29412,26879,41646)/97937,
 \quad S(q^*)=750784201/58762200.
\]

The best point on any simplex edge has value82963/6600. Their positive
gap is1112324/5386535. The construction is an exploratory proof witness,
with a saved exact enumeration; it is not a preregistered stochastic test.
The full one-level solver must therefore **not** be applied separately to
two levels and summed to certify their common-mixture spectral objective.

![Two-level spectral counterexample](../../runs/sparse_regret_audit/20261008/spectral_sharpness.png)

The background is a grid visualization only. The marked optimizer and strict
gap come from rational enumeration, not the plotted mesh.

## Theorem 3: sharpness for every number of distinct ES levels

For every J≥1, every strictly ordered set 1>α_1>...>α_J>0 and positive
weights w_j, there exist J+1 component laws and two nonnegative-loss actions
whose spectral ES regret has a unique maximizing mixture. That mixture
assigns positive mass to all J+1 components. Thus Theorem2's bound cannot be
reduced uniformly, even for two actions on a finite common support.

**Construction and proof.** Use N=J+2 loss atoms z_k=k, k=0,...,J+1.
Choose 0<ρ<α_J and the positive reference probability vector

\[
 p^*=(1-\alpha_1,\alpha_1-\alpha_2,\ldots,
       \alpha_{J-1}-\alpha_J,\rho,\alpha_J-\rho).
\]

For level j, both thresholds j−1 and j are optimal at p*. Encode their RU
forms as coefficient vectors on the probability simplex:

\[
 a^-_{jk}=j-1+(k-j+1)_+/\alpha_j,\qquad
 a^+_{jk}=j+(k-j)_+/\alpha_j.
\]

Let h_j=a^-_j−a^+_j and g=Σ_j w_j(a^-_j+a^+_j)/2. Then
h_{jk}=−1+1_{k≥j}/α_j and h_jᵀp*=0. For every probability vector p,

\[
 S(p):=\sum_jw_j ES_{\alpha_j}(p)
 \le g^Tp-\tfrac12\sum_jw_j|h_j^Tp|,
 \qquad S(p^*)=g^Tp^*.
\]

The N rows (1,g,h_1,...,h_J) are linearly independent. The first and last
J rows are identical at the two highest atoms; the difference of g at
those atoms is Σ_j w_j/α_j>0, so the coefficient of g in any dependence
is zero. Consecutive coordinates then eliminate each h_j coefficient and
finally the constant coefficient. Therefore there are unique vectors v_j
with 1ᵀv_j=gᵀv_j=0 and h_lᵀv_j=δ_lj. Set v_{J+1}=−Σ_{j≤J}v_j and

\[
 \epsilon=\frac{\min_k p^*_k}{2\max(1,\max_{r,k}|v_{rk}|)},\qquad
 p^{(r)}=p^*+\epsilon v_r.
\]

All p^(r) are positive probability vectors. For mixture weights q in Δ_{J+1},
p(q)−p*=εΣ_{j≤J}(q_j−q_{J+1})v_j, and the inequality above gives

\[
 S(p^*)-S(p(q))\ge\frac\epsilon2
       \sum_{j=1}^Jw_j|q_j-q_{J+1}|.
\]

The right side is zero only at q*=(1,...,1)/(J+1); that mixture gives p*.
Thus it is the unique maximum. On every simplex boundary,
Σ_{j≤J}|q_j−q_{J+1}|≥1/J. If q_{J+1}=0 the sum is1; if q_k=0 for
k≤J, write x=q_{J+1}, and the sum is at least x+|1−Jx|≥1/J.
Consequently every boundary value is below the maximum by at least
ε min_j w_j/(2J)>0. For equal normalized weights this is ε/(2J²).
Taking action A's loss as z and action B's loss as constant0 makes its
absolute spectral regret exactly S; all costs are zero. □

The construction is rational whenever the levels and weights are rational
and ρ is rational. It also proves existence for arbitrary real levels and
weights. Distinctness matters: repeated levels merge first.

This family was derived **after** the one-level computational study. A
separate exploratory check instantiates J=1,...,8 under two level/weight
recipes (16 cases): exact Fraction identities and positivity, plus104
unrestricted spectral LPs covering each full simplex and each boundary
face. All checks passed; the smallest measured boundary gap was about
3.2150e-5. The exact lower-bound proof, not float LP agreement, establishes
strict separation. This is not a production spectral-bank solver or a
new stochastic confirmation study. Code and resume receipts are in
`scripts/check_spectral_sharpness.py` and
`runs/sparse_regret_audit/20261008/sharpness_family/`.

## Constrained-simplex failure

With three components, α=.05, action A deterministic losses(1,0,0) by
component, and B constant0, restrict q_1≤.04 and q_2,q_3≥.10. Maximum regret
is .8 at q_1=.04, so every maximizer has three positive coordinates. Feasible
edge points with q_1=0 exist but have zero regret; none attains the maximum. Theorem2's rank condition
can handle polyhedral restrictions; Theorem1 cannot be reused unchanged.

## Corollary: a shared-hull finite-bank evaluator

For finite support, on an edge q=(1−u)e_a+u e_b, each action's ES is the
minimum of finitely many RU lines in u. The benchmark is the minimum of all
bank lines, so one lower hull, with action-owner labels, represents it.
Between two consecutive knots of action i's **own** ES function, F_i is
affine and −g is convex. The interval endpoints therefore suffice for that
action's maximum. The benchmark's additional knots need not be queried.

Let K≤MS be the total number of retained action threshold lines for S common
scenarios. After coefficient construction, the shared hull costs O(K log K);
evaluating O(K) own knots costs O(K log K). Theorem1 permits evaluation on
all R(R−1)/2 edges, for O(R² K log K) hull/query arithmetic time. Straightforward
per-edge support sorting and cumulative coefficient preprocessing adds
O(R² MS log S); it is covered by O(R² MS log(MS)) end to end. Per-edge working storage is O(MS),
in addition to O(RS+MS) input and O(MR) dense returned witness storage.
The α=1 case instead evaluates R pure-component mean vectors in O(RSM).

The comparator called `union` uses the **same** hull and evaluates all actions
on the union of all action knots. This isolates own-knot pruning. The
independent unrestricted-simplex LP comparator uses

\[
 E_j(q)+c_j=\min_s a_{js}^Tq,\qquad
 \max_q H_i(q)=\max_{j,s}\max_{q,z}\{z-a_{js}^Tq:
     z\le a_{it}^Tq\ \forall t,\ q\in\Delta_R\}.
\]

It has no edge assumption. Same-action pairs contribute exactly zero and
are skipped. This is a generic RU/LP decomposition, not claimed novel.
The mathematical algorithms are exact over real arithmetic. Float64/HiGHS
outputs are validated to declared tolerances; they are not outward-rounded
certified risk upper bounds.
