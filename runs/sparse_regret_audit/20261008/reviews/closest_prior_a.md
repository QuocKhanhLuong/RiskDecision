# Closest-prior audit: sparse regret over a component-law simplex

**Audit date:** 2026-10-08
**Owner:** independent review A
**Scope:** `sparse_regret_audit/20261008`
**Status vocabulary:** `READ` means source text or abstract was inspected; `REPORTED` means the frozen run report was read as existing evidence; `PROPOSED` means a mathematical idea generated for this audit; `NOT VALIDATED` means no new proof, implementation, or experiment was executed here.

## Question and provenance

The narrow question is whether a fixed finite action bank can be audited exactly for relative expected-shortfall (ES) regret when the data-generating law is any mixture of finitely many supplied component laws. For action (i), with fixed cost (c_i), write

\[
 E_i(q)=\operatorname{ES}_\alpha(L_i; p(q)),\qquad
 p(q)=\sum_{r=1}^R q_r p_r,\qquad q\in\Delta_R,
\]

and

\[
 g(q)=\min_j\{E_j(q)+c_j\},\qquad
 h_i(q)=E_i(q)+c_i-g(q).
\]

The candidate is **PROPOSED, NOT VALIDATED**: under finite common support, full-simplex ambiguity, fixed action losses/costs, and ordinary scalar ES, the maximum of (h_i(q)) should be attained on a component vertex or an edge of (Delta_R). If true, the current two-component own-knot hull solver could be reused on every pair of components to obtain an exact all-edge certificate.

I performed the primary-text extraction before reading `root_presearch_derivation.md`, as required by the independent-generation workflow. The root derivation was then read as a hypothesis to attack. I did not run a benchmark, train a model, open test outcomes, or alter source/results. The frozen computational report was read only as existing `REPORTED` evidence.

## Primary-source findings

| Source and access | Exact object located | Overlap with the candidate | Narrow remaining gap | Evidence status |
|---|---|---|---|---|
| Huang et al. (2010), [repository item](https://repository.kulib.kyoto-u.ac.jp/items/aea5f2a7-481d-4835-ad7c-0e01c56e18cb/full), [public PDF](https://repository.kulib.kyoto-u.ac.jp/bitstream/2433/87374/1/j.ejor.2009.07.010.pdf), [DOI](https://doi.org/10.1016/j.ejor.2009.07.010) | Section 2 defines (\operatorname{RCVaR}_\alpha(x)=\sup_{\pi\in\mathcal P}[\operatorname{CVaR}_\alpha(x,\pi)-\operatorname{CVaR}_\alpha(z^*(\pi),\pi)]). Section 3, eqs. (4)-(6), specializes to a finite rival set (\mathcal P_M=\{\pi^1,\ldots,\pi^l\}), with a law-specific optimum (\gamma^*(\pi^i)=\min_z\operatorname{CVaR}(z,\pi^i)), and solves (\min_x\max_i\{F_\alpha(x,\pi^i)-\gamma^*(\pi^i)\}). Theorem 1 gives an equivalent auxiliary formulation with one threshold variable per rival law and an LP/SOCP route. | Directly establishes the relative-CVaR/minimax-regret functional and per-law best-action subtraction. This rules out novelty for “regret relative to the best action under each law.” | The located formulation uses a finite list of rival laws and optimizes a continuous portfolio. I found no theorem there reducing a full probability-simplex law mixture to component edges for a fixed finite action bank. That absence is a search result, not a novelty proof. | `READ`: public PDF and indexed full-text excerpts. The direct PDF parser exposed no lines in this environment; publisher access was limited. Exact section/equation pointers were verified from indexed PDF text. |
| Zhu & Fukushima (2005 report; 2009 article), [open primary PDF](https://www-optima.amp.i.kyoto-u.ac.jp/~fuku/papers/2005-006.pdf), [article DOI](https://doi.org/10.1287/opre.1080.0684) | Defines the full mixture set (\mathcal P_M=\{\sum_i\lambda_i p_i:\lambda_i\ge0,\sum_i\lambda_i=1\}). Theorem 1 (PDF pp. 4-6) gives (\operatorname{WCVaR}_\beta(x)=\min_\alpha\max_i F^i_\beta(x,\alpha)), with LP formulations. Theorem 2 treats a compact convex set of discrete distributions (around pp. 9-10). | Establishes full-simplex mixture-law ambiguity and the lower-envelope/LP machinery surrounding worst CVaR. It is a direct warning that “mixture ambiguity plus CVaR tractability” is established. | It is **absolute** worst-case CVaR. There is no law-specific benchmark term (\min_j E_j(q)) in the theorem located, and the common (\alpha) minimax coupling is different from the candidate’s relative regret. I found no support-two certificate for the relative objective. | `READ`: open full text, including the mixture set, Theorem 1, proof, and Theorem 2. |
| Fan (2026), [SSRN abstract](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7486600), [DOI](https://doi.org/10.2139/ssrn.7486600) | Abstract: “Data-Driven Minimax-Regret Portfolio Optimization under Tail-Risk Ambiguity.” It mixes training scores from tail-risk engines, audits relative ES differences on a frozen library, projects onto an admissible engine-mixture set, and interpolates between a validated mixture and worst admissible regret. It claims a high-probability bound and a finite-library LP from admissible-set extreme points. | Closest contemporary conceptual threat: ES, minimax regret, finite mixtures, extreme-point computation, and a validation/audit split all appear in the abstract. | The abstract describes ambiguity over **tail-risk engines/admissible weights**, not a full simplex of component probability laws. The proposed support-two theorem and own-threshold edge certificate are not stated in the accessible abstract. | `READ` abstract only. Direct SSRN manuscript access returned HTTP 403; no access-control bypass was attempted. No section/theorem claim is made. |
| Zhu, Fan & Li (2014), [DOI](https://doi.org/10.1016/j.jedc.2014.08.015) | “Portfolio management with robustness in both prediction and decision: A mixture model based learning approach” uses a learned mixture distribution/credible region for mixture weights and robust mean-CVaR portfolio optimization via LP/SOCP. | Overlaps learned mixture weights, ambiguity sets, and robust CVaR decision quality. | Located abstract/section material does not give relative ES regret against a law-specific best action or a support-two edge theorem for a fixed action bank. | `READ`: official abstract/metadata; full publisher article was not fully accessible. |
| Benati & Conde (2022), [DOI](https://doi.org/10.1016/j.ejor.2021.04.038), [open repository copy](https://idus.us.es/server/api/core/bitstreams/b108c989-0c25-45fa-9e29-b3b5b4d2e780/content) | Relative robust optimization over empirical rival scenarios with bounded CVaR; Section 4 gives a minmax-regret expected-return formulation and LP/duality/constraint-generation treatment. The paper explicitly positions empirical time-window distributions as finite rival forecasts in the Huang line. | Overlaps relative robustness, rival distributions, CVaR constraints, and tractable scenario algorithms. | Its regret is applied to expected return with CVaR restrictions, rather than the candidate’s relative ES difference evaluated over the full component-law simplex. No all-edge support certificate was located. | `READ`: official abstract plus open repository text excerpts. |
| Pun, Wang & Yan (2023), [INFORMS DOI](https://doi.org/10.1287/msom.2023.1229) | Data-driven distributionally robust CVaR portfolio optimization under a regime-switching ambiguity set, with covariate/HMM structure and a tractable DRO formulation. | Overlaps regime/context-aware conditional CVaR ambiguity. | It is not a relative-regret edge certificate; the accessible abstract does not assert a full-simplex support bound. | `READ`: official abstract/metadata. |
| Rustem, Becker & Marty (2000), [DOI](https://doi.org/10.1016/S0165-1889(99)00088-3), [author PDF](https://www.imperial.ac.uk/media/imperial-college/research-centres-and-groups/business-school/public/working-papers/2000/WP2000-17.pdf) | Robust min-max portfolio strategies over rival forecast and risk scenarios. | Establishes the broad rival-scenario minmax decision pattern before the later CVaR-specific work. | It does not supply the candidate’s relative ES/full-simplex/edge theorem. | `READ`: official abstract and public author PDF. |

## Exact comparison with the two closest precedents

### Huang et al. (2010): regret is known; the ambiguity geometry differs

Huang’s relative robust CVaR is the most direct definition-level precedent. For every rival law (\pi), it subtracts the best CVaR attainable under that same law. With a finite law list, the outer supremum is a maximum over scenarios. The auxiliary formulation uses a separate RU threshold for each scenario and then solves the resulting LP/SOCP. This is the same law-specific benchmark logic needed by (h_i(q)).

The candidate changes two structural elements. First, it evaluates a **fixed finite action bank** rather than solving a continuous portfolio optimization problem at audit time. Second, it enlarges the rival set from an explicitly enumerated finite list to every mixture (q\in\Delta_R) of supplied component laws. The proposed contribution is therefore an exact reduction of this particular evaluation problem to all component edges, conditional on a proof. It is not a new regret criterion, and it does not supersede Huang’s optimization formulation.

### Zhu & Fukushima: full mixture ambiguity is known; relative subtraction is the gap

Zhu and Fukushima explicitly use the full simplex of mixtures of supplied distributions and show that the worst **absolute** CVaR can be represented through a finite max over component-specific RU functions after a common threshold minimization. This makes it unsafe to describe “full mixture ambiguity for CVaR” as new.

Their (\min_\alpha\max_i F_i(x,\alpha)) is not the candidate’s

\[
\max_{q\in\Delta_R}\left[\operatorname{ES}_i(q)+c_i-
\min_j\{\operatorname{ES}_j(q)+c_j\}\right].
\]

The inner law-specific benchmark and the action-bank minimum make the objective a difference of a concave ES function and a concave lower envelope. The proposed edge result comes from the resulting convexity on the evaluated action’s own ES cells; it does not follow merely from Zhu/Fukushima’s absolute WCVaR theorem. Conversely, their theorem is a serious prior-art constraint on any claim that the candidate’s mixture-law or RU-hull ingredients are new.

## Adversarial check of the proposed support-two reduction

The following is a proof sketch, not an established theorem. Let each component law have finite common support and let the action losses be fixed on that support. Under the usual upper-tail RU representation,

\[
 E_i(q)=\min_\tau\left\{\tau+\alpha^{-1}
 \sum_s p_s(q)(L_{i,s}-\tau)_+\right\},
 \qquad p_s(q)=\sum_rq_rp_{r,s}.
\]

For fixed (i), (E_i) is a concave piecewise-affine function of (q), because it is the pointwise minimum of affine functions. The bank envelope (g(q)=\min_j(E_j(q)+c_j)) is also concave: its hypograph is the intersection of the concave hypographs. Consequently, (h_i=E_i+c_i-g) is convex.

Partition the simplex by the threshold cells of action (i). On a cell with threshold loss level (k), (E_i) is affine and the cell is the simplex intersected by the cumulative-mass strip around the tail cutoff, schematically

\[
 C_{k-1}(q)\le 1-\alpha\le C_k(q),
 \qquad C_k(q)=\sum_{s\le k}p_s(q).
\]

A convex function reaches its maximum over a compact polytope at some vertex. If no cutoff inequality is active, the vertex is a simplex vertex (one component). If exactly one is active, the simplex has one additional independent equality, so a vertex has at most two positive (q_r). If both are active, then (p_k(q)=C_k(q)-C_{k-1}(q)=0). Since (p_k(q)) is a nonnegative mixture of the component probabilities, every component receiving positive weight has (p_{r,k}=0). On that face the two cutoff constraints collapse to one independent equality, again leaving a vertex with at most two positive mixture weights. Ties or zero-probability loss levels add degeneracy but do not increase the number of independent equalities in this argument after equal loss levels are merged.

This supports the **conditional** proposition that every action’s worst regret has an optimizer on a simplex vertex or edge. It does not establish the result for continuous supports, multiple simultaneously weighted ES levels, law-dependent actions, or ambiguity sets other than the full simplex.

### Decisive falsifiers and limitations

The proposed theorem should be rejected if any finite (R\ge3) construction with common finite support produces a strictly larger value at an interior simplex vertex of an own-threshold cell than at all vertices/edges. The cheapest decisive check is an exhaustive exact cell-vertex enumeration for small rational (p_{r,s}), losses, (\alpha), action banks, and fixed costs, compared with direct edge enumeration. That check was **not run in this audit** because the instruction was to perform no new experiments.

Other clear failure modes are:

- adding moment, box, trust-region, or posterior constraints to (q), which can create extra active equalities and vertices with more than two positive components;
- replacing scalar ES by a weighted sum of several ES levels, for which a support bound of (J+1) is only a conjecture here;
- allowing action losses, costs, or the action set to depend on (q);
- using continuous component laws without a separate approximation/limit proof; and
- treating a learned credible region as the full simplex. A constrained credible region can have vertices unrelated to component edges.

Even if the theorem survives, enumerating all (\binom{R}{2}) edges costs roughly (O(R^2 K\log K)) for (K) action/RU lines per edge. For large (R), this may be an exact audit certificate with poor computational scaling rather than a broad algorithmic breakthrough.

## Relation to the current implementation and frozen run

The existing `bank_regret` implementation is a two-component finite-mixture solver. Its `solve_local` method checks each action’s own threshold crossings against a shared lower hull; `solve_union` is the exact union-of-knots comparator. The proposed all-simplex extension would call that two-component machinery on every component pair and include the component vertices. It is not implemented in the current code, and the current implementation does not establish the arbitrary-(R) theorem.

The frozen full report `docs/experiments/20261008_compositional_risk_full.md` was read as `REPORTED` evidence only. It reports exact local-versus-union agreement for its measured two-component computational matrix and mixed policy behavior, but those results do not validate the arbitrary-(R) support theorem, do not establish an improved conditional forecaster, and do not show a joint policy benefit. No stochastic experiment or frozen outcome was rerun here.

## Bounded novelty verdict

**Decision: no established novelty; a narrow candidate remains plausible but is not paper-ready.**

The strongest defensible statement is:

> **PROPOSED:** for a fixed finite action bank, finite common outcome support, scalar ES, fixed costs, and a full simplex of mixtures of supplied component laws, relative ES regret may admit an exact reduction to component vertices and edges, making the existing two-component RU-hull certificate reusable edge by edge.

This statement combines known ingredients—Huang’s law-specific relative CVaR regret, Zhu/Fukushima’s mixture-law CVaR machinery, and standard RU lower-envelope geometry—with a potentially new interaction: convexity of relative regret on the evaluated action’s own threshold cells plus the special structure of a simplex cut by a single tail-cumulative strip. The bounded search did not locate the same edge theorem, but that is not proof of absence. Fan’s abstract shows that current work already combines ES minimax regret, finite mixtures, audit data, and extreme-point LP computation, so any eventual paper would need to distinguish probability-law mixtures from tail-risk-engine mixtures and cite Fan directly once the full text is accessible.

The decisive next gate is a formal theorem with all degeneracy cases followed by an independent exact (R=3) cell-vertex/edge certificate and a comparison against a generic full-simplex LP or exhaustive vertex oracle. Until that gate passes, the contribution should be described as a proposed computational composition and an auditable hypothesis, not as a new method, theorem, or peer-reviewed result.

## Correction appended after adversarial review

The sentence above stating “Consequently, (h_i=E_i+c_i-g) is convex” was too broad. Globally, (E_i(q)) is generally concave piecewise affine, so (E_i+c_i-g) is not asserted to be convex on the whole simplex. The valid statement is narrower: after fixing an (alpha)-quantile/threshold (t) of the evaluated action, (E_i) is affine on the corresponding set (Q(t)); because (g) is concave, (h_i) is convex **on that (Q(t))**. The support-two argument must therefore maximize over each (Q(t)) and then take the supremum over thresholds. This correction preserves the original derivation and removes the global-convexity claim.

The terminology is also clarified here: the target is an **absolute ES difference from the best bank action under the same law**. “Relative” may describe a benchmark-relative comparison in some prior-paper titles, but the target is never a ratio or multiplicative relative error.

## Full-text receipts and source-status correction (append-only)

The three directly relevant PDFs were retrieved through public, lawful routes and read locally with pypdf on 2026-10-08. These receipts supersede the earlier “indexed text/limited parser” wording above; they do not change the bounded novelty verdict.

| Source | Public primary URL(s) and access | Local receipt |
|---|---|---|
| Huang, Zhu, Fabozzi & Fukushima, Portfolio Selection under Distributional Uncertainty: A Relative Robust CVaR Approach (2010) | [Kyoto DSpace API PDF](https://repository.kulib.kyoto-u.ac.jp/server/api/core/bitstreams/5d7f031d-a1cf-4aa5-894e-5387e34d4481/content); [DOI](https://doi.org/10.1016/j.ejor.2009.07.010). **FULL PDF read**, 19 pages. | /private/tmp/riskdecision-huang2010-full.pdf; SHA-256 3ac939e86111e47fa7247a21594419ed1d5dd3deed2447a907a93b9788a79acd. |
| Zhu & Fukushima, Worst-Case Conditional Value-at-Risk with Application to Robust Portfolio Management (2005 report / Operations Research article) | [Public Kyoto author PDF](https://www-optima.amp.i.kyoto-u.ac.jp/~fuku/papers/2005-006.pdf); [article DOI](https://doi.org/10.1287/opre.1080.0684). **FULL PDF read**, 28 pages. | /private/tmp/riskdecision-zhu2005.pdf; SHA-256 d19779a265bbea1e0e5dd9b60ab3b24bda8766c8e7bf31d9bdfe86cf889d860f6. |
| Pertaia & Uryasev, Fitting heavy-tailed mixture models with CVaR constraints (2019) | [DOI](https://doi.org/10.1515/demo-2019-0019); [public author PDF route](https://uryasev.ams.stonybrook.edu/wp-content/uploads/2020/04/23002298-Dependence-Modeling-Fitting-heavy-tailed-mixture-models-with-CVaR-constraints.pdf). **FULL PDF read**, 10 pages, from the author-homepage/Dropbox route available to the root researcher. | /private/tmp/riskdecision-pertaia2019-full.pdf; SHA-256 fed82ff684943e3dea0015c0f836bf1c08229b569f9762e58137f25a51046410. |

### What the full PDFs actually say

Huang et al. p. 5 defines the benchmark-relative **absolute** difference
\(\operatorname{CVaR}(x,\pi)-\operatorname{CVaR}(z^*(\pi),\pi)\). Their Section 3, pp. 6-8, then restricts the rival set to the explicitly finite list \(\mathcal P_M=\{\pi^1,\ldots,\pi^l\}\) (eq. (4)), writes the law-specific optimum \(\gamma^*(\pi^i)\) and finite maximum (eqs. (5)-(6)), and gives the per-rival-threshold auxiliary formulation (Theorem 1, p. 7) and LP (p. 8). Footnote 4 on p. 6 separately gives a **percentage-regret ratio**; that ratio is not the target audited here. The full text contains no statement reducing a full probability-simplex mixture to component edges for a fixed action bank. This is a direct overlap on regret definition and RU computation, while the all-edge reduction remains a distinct unverified interaction.

Zhu & Fukushima p. 5 defines the full simplex of mixture densities (eq. (4)). Theorem 1, pp. 5-7, proves that **absolute** worst-case CVaR over this simplex equals a common-threshold \(\min_\alpha\max_i F^i_\beta(x,\alpha)\) expression (eq. (6)), with its finite LP route. Their Theorem 2, p. 10, extends the minimax interchange to a compact convex discrete-law set. These results subsume the candidate's mixture-law and RU-hull ingredients for absolute WCVaR, but they do not subtract a law-specific best bank action and do not state the support-two edge certificate for the resulting regret gap. The proof's extreme points are used for a fixed-threshold affine maximization; that is materially different from the own-action threshold-cell argument needed for the relative gap.

Pertaia & Uryasev p. 4 states and proves Proposition 3.2: CVaR of a finite mixture is concave in the mixture weights. Their pp. 5-6 cardinality section imposes an integer upper bound \(M\) on the number of nonzero weights; it does not derive \(M=2\) for a regret maximizer. Their conclusion p. 9 repeats the concavity result and the user-imposed cardinality model. Thus this is a close prior for the ES-in-mixture concavity ingredient, not a direct all-edge or benchmark-regret theorem.

The full-text check therefore strengthens the prior-art warning but does not reveal a direct theorem that subsumes the proposed all-edge reduction. That is a bounded search result only; absence in these inspected passages is not evidence of priority. The narrowest defensible description remains a **proposed computational certificate** for a fixed bank, scalar ES, common component laws, and the unrestricted simplex. The root's frozen run is REPORTED rather than independently executed here: 168 cases, 29,847 LPs, and reported maximum local-versus-union error \(1.04\times10^{-14}\). Those arithmetic checks support the implementation's measured two-component behavior, not theorem priority or a conditional-forecasting claim.
