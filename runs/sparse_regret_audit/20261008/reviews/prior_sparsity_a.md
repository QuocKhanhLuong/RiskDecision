# Prior-sparsity audit: the (Q(t)) support-two argument

**Audit date:** 2026-10-08
**Owner:** independent review A
**Scope:** fixed finite action bank, law mixture (P_q=sum_{r=1}^R q_rP_r), and absolute ES gap from the best bank action.
**Status:** literature and mathematical audit only. No source code, frozen result, benchmark, or model was changed or rerun.

## Verdict first

The stronger formulation appears mathematically sound under a broader assumption than the earlier finite-outcome statement: the component laws may be arbitrary integrable laws. For any fixed evaluated action (i), choose an (alpha)-quantile (t) of its loss under a mixture (P_q), and define

\[
 Q_i(t)=\left\{q\in\Delta_R:
 \sum_rq_rP_r(L_i>t)\le \alpha\le
 \sum_rq_rP_r(L_i\ge t)\right\}.
\]

On (Q_i(t)), ES of action (i) is affine in (q). Every bank ES is concave in (q), so the bank minimum is concave and the evaluated action’s absolute gap is convex on (Q_i(t)). A vertex of (Q_i(t)) has at most two positive mixture weights: one active tail inequality gives one extra equality; if both are active, their difference is a nonnegative mixture of atom masses and forces the positive support onto the zero-atom face, where the two equalities collapse to one. Maximizing convex gap over each (Q_i(t)), then taking the threshold that belongs to a global maximizer, gives a component vertex or edge witness.

This is **PROPOSED/NOT FORMALLY VERIFIED** here. The primary literature establishes the ingredients separately, and I did not locate the exact support-two certificate stated as a theorem. The result therefore looks like a short, potentially useful geometric lemma and audit algorithm, rather than a new risk measure or a strong standalone theoretical contribution. The fact that the proof is an immediate combination of known ES formulas and elementary polyhedral geometry is itself a novelty warning.

## Derivation without finite loss support

Let (L_i) be the loss of the evaluated action under component law (P_r), and assume the relevant negative/positive part is integrable so ES is finite. Use an upper-tail mass (alpha\in(0,1)). Set

\[
 a_r(t)=P_r(L_i>t),\quad b_r(t)=P_r(L_i\ge t),\quad
 m_r(t)=E_{P_r}[L_i\mathbf 1_{\{L_i>t\}}].
\]

For (q\in Q_i(t)), the standard atom-splitting ES formula is

\[
 E_i(q)=\operatorname{ES}_\alpha^{P_q}(L_i)
 =\frac{\sum_rq_rm_r(t)+t\left(\alpha-\sum_rq_ra_r(t)\right)}{\alpha}.
\]

Thus (E_i) is affine in (q) on the fixed-(t) set (Q_i(t)). This remains true for continuous laws, mixed laws, and laws with atoms; no common finite loss support is needed. For (alpha=1), ES is the mean and is affine on the whole simplex, so a component vertex already suffices. The (alpha=0) essential-supremum case is outside this argument.

For every bank action (j),

\[
 E_j(q)=\inf_{s\in\mathbb R}
 \left[s+\alpha^{-1}E_{P_q}(L_j-s)_+\right]
\]

is concave in (q), since it is the pointwise infimum of affine functions of (q). Hence

\[
 g(q)=\min_j\{E_j(q)+c_j\}
\]

is concave, and the absolute bank gap

\[
 h_i(q)=E_i(q)+c_i-g(q)
\]

is convex only after restricting to (Q_i(t)), where (E_i) is affine. This is the corrected scope of the earlier convexity sentence; there is no global-convexity claim.

The support argument is finite-dimensional even when the (P_r) are not. Write (a\cdot q=\sum_ra_rq_r), (b\cdot q=\sum_rb_rq_r), and (d=b-a\ge0). The set (Q_i(t)) is the simplex intersected by (a\cdot q\le\alpha) and (b\cdot q\ge\alpha).

- If neither tail inequality is active at a vertex, the vertex is a simplex vertex and has support one.
- If exactly one is active, the normalization equality and one additional independent equality leave a vertex with support at most two.
- If both are active, then (d\cdot q=0). Because (d_r=P_r(L_i=t)\ge0) and (q_r\ge0), every positive component must satisfy (P_r(L_i=t)=0). On that face (a\cdot q=b\cdot q), so the two tail equalities reduce to one independent equality; the vertex again has support at most two.

For a global maximizer (q^*) of (h_i), choose any (alpha)-quantile (t^*) of (L_i) under (P_{q^*}). Then (q^*\in Q_i(t^*)). A convex function on this compact polytope has a maximizing vertex, and that vertex is also a global maximizer because (q^*) was global. Therefore an edge/vertex witness exists. This is a direct proof sketch, not a substitute for a formal treatment of all endpoint and measurability cases.

## What primary sources establish

### Acerbi and Tasche: exact arbitrary-law quantile and atom formula

The public author/arXiv copy of [Acerbi and Tasche, “On the coherence of Expected Shortfall”](https://arxiv.org/abs/cond-mat/0104295) is the closest direct source for the (Q_i(t)) step. In Proposition 4.2, eqs. (4.7)-(4.10), the minimizer interval is characterized by

\[
P[X<s]\le\alpha\le P[X\le s].
\]

Corollary 4.3, eq. (4.11), then writes ES/CVaR at any (s) in that interval as a tail integral plus a threshold correction. Eq. (4.12) gives the equivalent strict-inequality version. In the loss convention used here, these are exactly the (P(L>t)\le\alpha\le P(L\ge t)) conditions and the affine atom-splitting formula above. The paper explicitly allows integrable random variables and discusses discontinuities.

This source establishes the threshold-cell formula for arbitrary integrable laws. It does **not** state that maximizing an action-bank gap over the resulting (Q_i(t)) needs only two mixture components.

### Rockafellar and Uryasev: RU representation and quantile argmin

The public author PDF of [Rockafellar and Uryasev, “Conditional Value-at-Risk for General Loss Distributions”](https://sites.math.washington.edu/~rtr/papers/rtr187-CVaR2.pdf) gives the same foundation for general distributions. Theorem 10, eqs. (28)-(31), states the minimization formula, identifies the argmin interval with the lower and upper VaR endpoints, and derives the one-sided derivative conditions. Corollary 11 gives convexity in a decision variable when the loss is convex in that decision.

The theorem supports the use of a fixed threshold and the RU formula, including atoms. Its convexity statement is about the portfolio/decision variable in the loss, not about mixture probabilities (q), and it contains no support-two or edge-enumeration result. The difference matters: ES is concave in the **law mixture weights**, as the next sources make explicit.

### Tselishchev: direct concavity in probability mixtures and spectral extension

[Tselishchev, “On the Concavity of Expected Shortfall”](https://arxiv.org/pdf/1910.00640) directly proves the missing law-weight property. Equation (3) defines ES through the integrated quantile, eq. (4) gives the atom-aware formula, and the main theorem, eq. (12), states for a finite distribution mixture that

\[
\operatorname{ES}_\alpha(\operatorname{mix}_\beta X)
\ge\sum_j\beta_j\operatorname{ES}_\alpha(X_j).
\]

The proof’s Lemma, eqs. (7)-(11), constructs component tail levels whose weighted sum is the mixture level. The final discussion, eq. (16) and the paragraph immediately following it, extends the same concavity claim to spectral risk measures represented as weighted ES mixtures.

This is a direct primary precedent for concavity of each (E_j(q)), including arbitrary risk positions and mixture laws. It does not form an action-bank minimum, subtract it from an affine-on-(Q_i(t)) evaluated action, or derive a two-support extreme point.

### Pertaia and Uryasev: mixture-weight CVaR concavity already used computationally

[Pertaia and Uryasev, “Fitting heavy-tailed mixture models with CVaR constraints”](https://doi.org/10.1515/demo-2019-0019) states Proposition 3.2: the CVaR of a finite mixture is a concave function of its component weights. The displayed proof substitutes the mixture CDF into the RU objective and uses pointwise minimization over the threshold. This is nearly the same concavity ingredient, with a mixture-fitting application rather than a regret audit.

The publisher/IDEAS record marks the full text downloadable, and the indexed primary PDF exposes Proposition 3.2; the direct PDF fetch returned a transient 502 in this environment. No support bound or law-specific benchmark subtraction appears in the accessible proposition.

### Zhu and Fukushima: full-simplex ambiguity, but absolute worst CVaR

The open primary report [Zhu and Fukushima, “Worst-Case Conditional Value-at-Risk with Application to Robust Portfolio Management”](https://www-optima.amp.i.kyoto-u.ac.jp/~fuku/papers/2005-006.pdf) and the [Operations Research DOI](https://doi.org/10.1287/opre.1080.0684) define the full mixture set (\{\sum_rq_rP_r:q\in\Delta_R\}). Their Theorem 1 (PDF pp. 4-6) reduces worst-case CVaR to a common-threshold expression (\min_\tau\max_rF_r(x,\tau)); Theorem 2 (around pp. 9-10) treats a compact convex set of discrete distributions.

This is strong prior art for the ambiguity family and RU/minimax computation. It is an **absolute** worst-CVaR problem. The common threshold and outer optimization do not provide the fixed-action, law-specific-best-action gap or the (Q_i(t)) support-two certificate. A generic minimax/saddlepoint argument from this paper should therefore not be cited as if it already proves the candidate.

### Kusuoka: spectral representation, not component sparsity

The primary record for [Kusuoka, “On Law Invariant Coherent Risk Measures”](https://repository.kulib.kyoto-u.ac.jp/items/7107ce87-03df-46fd-9005-620e01024a96?locale=en) ([book-chapter DOI](https://doi.org/10.1007/978-4-431-67891-5_4)) establishes the law-invariant coherent/spectral representation that motivates ES mixtures. The item lists the primary PDF, but the direct repository parser did not expose its text in this audit. The exact spectral consequence is independently visible in Tselishchev’s cited extension above.

No component-law simplex or support-two result was located in the accessible Kusuoka record. It is relevant for warning that replacing scalar ES by a general spectral measure adds a mixture over tail levels; it does not justify retaining a two-component law certificate for that generalization.

### Winkler: generic extreme-point moment theory

[Winkler, “Extreme Points of Moment Sets”](https://doi.org/10.1287/moor.13.4.581) characterizes extreme points of probability-measure sets defined by finitely many generalized moment conditions and uses them to optimize affine functionals. The INFORMS abstract is open, but the full article was not accessible here.

This is the closest generic “moment corollary” precedent. It would normally give a support bound based on the number of independent active moment constraints. The candidate’s sharper two-support result comes from the special nested pair (a\cdot q\le\alpha\le b\cdot q): when both bind, the nonnegative atom-mass difference forces the second equality to collapse. I did not locate this nested-tail specialization in Winkler or another primary source. Because the full theorem text was not accessed, no stronger attribution is made.

## Fan metadata and lawful access check

The [SSRN record for Fan, “Data-Driven Minimax-Regret Portfolio Optimization under Tail-Risk Ambiguity”](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7486600) now confirms the metadata: 36 pages, posted 21 September 2026, last revised 28 September 2026, written 31 March 2026, by Zheqi Fan. Its abstract describes ES minimax regret, finite tail-risk-engine mixtures, an independently audited admissible set, extreme-point LP computation, and a finite-sample bound.

The direct SSRN record returned HTTP 403 during this audit. I checked the author’s [public homepage](https://sites.google.com/view/zheqifan/home/); it does not list this manuscript or an alternate full-text link. No restricted route, contact request, or access-control bypass was attempted. Fan remains an abstract-only overlap threat: it concerns mixtures of risk engines/admissible weights in the abstract, whereas the candidate concerns mixtures of component probability laws and an edge certificate. The full paper could still contain a closer theorem; that remains unresolved.

## What remains defensible

The support-two fact should be presented as a **derived sparsity lemma for absolute ES-gap evaluation**, with assumptions stated explicitly:

1. finitely many component laws (P_1,\ldots,P_R), but arbitrary integrable loss distributions within each component;
2. the full simplex of mixture weights (q), with no extra moments, boxes, posterior credible-region inequalities, or Wasserstein constraints;
3. a fixed finite action bank and fixed costs;
4. scalar ES at one level (\alpha\in(0,1]), using the atom-splitting definition; and
5. a common mixture law used for every action’s marginal loss.

Under these conditions, an all-edge oracle is a plausible exact certificate. It is a computational composition of known ES geometry, not a new forecaster or conditional-risk guarantee. The direct prior overlap is substantial enough that “new theorem on robust CVaR mixtures” would be unsupported.

The claim fails or needs a new proof when the ambiguity set is a proper constrained subset of the simplex, when several ES levels are combined, when costs or actions depend on (q), or when ES is replaced by a non-ES tail functional. Generic moment/extreme-point bounds then apply, but support two is not automatic.

The decisive next gate is a formal proposition covering quantile nonuniqueness, unbounded integrable tails, (\alpha=1), and degenerate (a=b) rows, followed by an independently checked (R=3) exact vertex/edge comparison. That gate was not run here. Until it passes, record this as a promising sparsity certificate with **no established novelty**.

## Bounded query record

Focused primary-source searches were run on 2026-10-08 for: (i) ES concavity in probability mixtures; (ii) Rockafellar-Uryasev and Pflug arbitrary-law quantile/CVaR formulas; (iii) mixture-CVaR extreme-point and support theorems; (iv) Kusuoka spectral ES representations; (v) Winkler moment-set extreme points; (vi) full-simplex worst-case CVaR; (vii) Fan SSRN 7486600 metadata/full text; and (viii) exact “support two”/edge-enumeration combinations. Results and access status are recorded inline above. Search non-hits are not treated as evidence of absence.

## Full-text receipts and access-status correction (append-only)

The closest mixture-CVaR sources were subsequently retrieved as complete public PDFs and inspected page by page on 2026-10-08. The earlier statement that Pertaia and Uryasev's direct PDF was not verified is superseded by this receipt; the mathematical conclusion is unchanged.

| Source | Public primary URL(s), access level, and page pointers | Local receipt |
|---|---|---|
| Huang, Zhu, Fabozzi & Fukushima (2010) | [Kyoto DSpace API PDF](https://repository.kulib.kyoto-u.ac.jp/server/api/core/bitstreams/5d7f031d-a1cf-4aa5-894e-5387e34d4481/content); [DOI](https://doi.org/10.1016/j.ejor.2009.07.010). **FULL PDF read**, 19 pages. Section 2 / relative CVaR definition p. 5; finite rival laws and eqs. (4)-(6), plus ratio footnote 4, p. 6; Theorem 1 p. 7; LP p. 8. | /private/tmp/riskdecision-huang2010-full.pdf; SHA-256 3ac939e86111e47fa7247a21594419ed1d5dd3deed2447a907a93b9788a79acd. |
| Zhu & Fukushima (2005 report / 2009 article) | [Public Kyoto author PDF](https://www-optima.amp.i.kyoto-u.ac.jp/~fuku/papers/2005-006.pdf); [article DOI](https://doi.org/10.1287/opre.1080.0684). **FULL PDF read**, 28 pages. Mixture simplex eq. (4), Theorem 1 and proof pp. 5-7; compact-convex discrete-law Theorem 2 p. 10; general-distribution remark p. 9. | /private/tmp/riskdecision-zhu2005.pdf; SHA-256 d19779a265bbea1e0e5dd9b60ab3b24bda8766c8e7bf31d9bdfe86cf889d860f6. |
| Pertaia & Uryasev (2019) | [DOI](https://doi.org/10.1515/demo-2019-0019); [public author PDF route](https://uryasev.ams.stonybrook.edu/wp-content/uploads/2020/04/23002298-Dependence-Modeling-Fitting-heavy-tailed-mixture-models-with-CVaR-constraints.pdf). **FULL PDF read**, 10 pages, via the public author-homepage/Dropbox route available to the root researcher. Mixture/RU formula pp. 2-3; Proposition 3.2 and proof p. 4; user-imposed cardinality constraints pp. 5-6; conclusion p. 9. | /private/tmp/riskdecision-pertaia2019-full.pdf; SHA-256 fed82ff684943e3dea0015c0f836bf1c08229b569f9762e58137f25a51046410. |

The full-text comparison sharpens the support-two verdict. Huang's pp. 5-8 establish benchmark-relative absolute CVaR regret for a finite list of laws and separate a percentage-ratio alternative in footnote 4; they do not state an edge reduction for a full simplex. Zhu & Fukushima's pp. 5-7 reduce **absolute** WCVaR over the full mixture simplex to a common-threshold maximum of component RU functions, and p. 10 treats compact convex discrete-law sets. This is strong prior art for the ambiguity set and fixed-threshold extreme-point step, but the law-specific bank minimum is absent. Pertaia & Uryasev's Proposition 3.2 p. 4 proves the exact ES/CVaR concavity-in-weights ingredient used here, while pp. 5-6 impose an arbitrary cardinality cap \(M\); they do not prove that a worst absolute ES-gap witness has \(M=2\). The inspected full texts therefore contain all major ingredients separately, yet no directly stated nested-tail support-two regret certificate. This remains an absence observation, not a priority claim.

The resulting contribution should be framed as an elementary, assumption-sensitive **derived sparsity lemma** assembled from established RU/quantile formulas, ES concavity, and simplex geometry. It is not a new CVaR risk measure, a new relative-regret definition, or evidence that full-simplex robust CVaR is novel. Any paper claim should include these three sources as direct prior art and make the remaining interaction explicit: the evaluated action's fixed-threshold set \(Q_i(t)\) makes its ES affine, while the bank minimum remains concave, so convex gap maximization admits a vertex/edge witness. The decisive formal proof and independent \(R=3\) exact gate remain outstanding; no new test or run was executed in this receipt update.
