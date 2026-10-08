# Targeted priority audit, 2026-10-08

This is a bounded, multi-pass primary-source search and citation-chain audit,
not a systematic review or proof of novelty. Source access differs by record.
Two independent AI reviewers and the root checked the closest formulations.
Human bibliographic/theorem verification remains pending.

| Primary source | Actually inspected | Established contribution | Relation to this draft |
|---|---|---|---|
| [Huang et al., 2010](https://doi.org/10.1016/j.ejor.2009.07.010) | Actual19-page repository PDF; root Sections2–3 incl footnote4, reviewer full relevant text | Law-specific relative CVaR difference; finite rival-law LP/SOCP. Percentage alternative in footnote4 | Regret criterion is prior art. Our evaluated ambiguity set contains every probability-law mixture, with a fixed bank |
| [Zhu and Fukushima, 2009](https://doi.org/10.1287/opre.1080.0684) | Actual28-page2005 author report; Theorem1, eqs4–11 | Full-simplex worst absolute CVaR via common-threshold minimax | Mixture ambiguity and RU tractability are prior art; no bank benchmark subtraction in that theorem |
| [Pertaia and Uryasev, 2019](https://doi.org/10.1515/demo-2019-0019) | Actual10-page author-linked PDF; Proposition3.2, Section3.3 | Mixture-weight CVaR concavity; optionally imposed cardinality in fitting | Concavity and sparse mixtures are prior art. Their imposed cardinality is not our automatic worst-regret witness property |
| [RU general distributions](https://sites.math.washington.edu/~rtr/papers/rtr187-CVaR2.pdf) | Primary PDF Theorem10, eqs28–31 | RU threshold minimum, including atoms | Foundation; not claimed new |
| [Acerbi and Tasche](https://arxiv.org/abs/cond-mat/0104295) | Primary PDF Proposition4.2, Corollary4.3 | Arbitrary-law quantile bracket and atom-aware tail formula | Foundation for the fixed-quantile polytope |
| [Tselishchev](https://arxiv.org/abs/1910.00640) | Primary PDF main theorem/eq12 and spectral extension | Concavity in probability mixtures | Foundation, including weighted ES mixtures |
| [Winkler,1988](https://doi.org/10.1287/moor.13.4.581) | Publisher abstract only; full text NOT READ | General moment-set extreme points | Strong generic sparsity overlap; cannot claim a new general support theorem |
| [Tao and Deng,2025](https://sxzz.whu.edu.cn/html/2025/2/20250202.htm) | Official full HTML; eq3.1,3.2, assumptions and main bound | CVaR minimax-regret generalization for finite density-ratio class | Direct prior objective; this draft makes no new generalization claim |
| [Bitar,2024](https://arxiv.org/html/2412.15406v1) | Primary HTML Sections1–3, eq21–22 | Worst CVaR of ex-post regret over Wasserstein balls | Different order of ES and regret, and different ambiguity set |
| [Pinelis,2012 preprint /2016 journal](https://arxiv.org/pdf/1204.0249) | Root read Theorem1, Corollaries4–5, Theorem12; reviewer full10-page PDF | Atomic partition/linear independence; Theorem12 explicitly reproduces Winkler support bound | Generic moment sparsity is established; ES-specific rank collapse remains a specialization |
| [Henrion, Kružík and Weis,2026](https://arxiv.org/html/2606.21391v1) | Root Theorem2.6/Proposition3.2 and moment section; reviewer full PDF | Injectivity on smallest faces and affine-independent finite support | Direct generic rank-geometry overlap; no new general support theorem here |
| [Fan,2026](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7486600) | Primary abstract and metadata; full text403, no lawful alternate found | Abstract reports engine-score mixtures, ES regret, audit split and extreme-point LP | Abstract describes risk-score mixtures, not explicitly law mixtures. Cannot exclude a matching full-text lemma |

| [Fan, second2026 preprint](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7492399) | Primary abstract/metadata; full text403; public author page checked | Convex aggregations of implemented risk functions; validation-calibrated regret and polyhedral LP | Score/function mixing differs from evaluating ES after law mixing; full comparison unresolved |

The combined contribution under consideration is: (1) integrable-law
support-two **absolute ES-gap** witnesses with a degeneracy-complete proof;
(2) the finite-level/rank extension and a constructive all-J sharpness proof;
(3) shared-hull, own-knot all-bank evaluation on every component edge; and
(4) unrestricted LP, rational vertex and continuous-law diagnostic controls.
This is a useful derived computational package, not established priority.

Search families included exact ES/CVaR regret, mixture/simplex/edge/support-two,
Caratheodory/moment sparsity, finite spectral sums, and citation chains of
Huang, Zhu/Fukushima and Pertaia/Uryasev. The reviewer query logs are in
`runs/sparse_regret_audit/20261008/queries_a.json` and the review Markdown files.
Search engines, arXiv, official journal/author sites and repository APIs were
used for discovery/access; no claim of exhaustive database coverage is made.

Huang's obsolete bitstream path returned a short HTML app page. The actual
open file was recovered through the repository's public DSpace item→bundle→
bitstream links:
[repository PDF](https://repository.kulib.kyoto-u.ac.jp/server/api/core/bitstreams/5d7f031d-a1cf-4aa5-894e-5387e34d4481/content).
Pertaia's obsolete institutional path404 was replaced by the PDF linked on
[the author's current publication page](https://uryasev.github.io/publications/).
File hashes/access receipts are in the reviewer appendices. Full copyrighted
PDFs are kept outside the repository and are not published with this branch.

## Claim boundary

- **Supported derivation:** the stated sparse-witness and computational claims.
- **Verified computation:** only the declared run matrix and explicit diagnostics.
- **Suitable now:** a working mathematical/computational draft for human review.
- **Unresolved:** novelty priority, match to inaccessible Fan full text, generic
  whether the ES-specific specialization and all-J sharpness family merit a venue. Generic moment-rank attribution is now checked in two accessible primary full texts.
- **Not supported:** first-ever ES regret, first mixture-CVaR method, new
  forecasting model, calibrated financial guarantee, market superiority, or
  a claim that the paper is ready to submit.

## Additional attribution check

Pinelis Theorem12 restates Winkler's probability-measure support bound, so
Winkler's inaccessible original does not leave the generic rank principle
unexamined. Henrion–Kružík–Weis Proposition3.2 supplies the same geometric
framework via a smallest-face argument. Our extra ES-specific step is the
nonnegative atom-mass collapse of each quantile pair to one active rank.
This is a narrow specialization, not a competing general theorem. The
newly derived all-J construction establishes sharpness for any distinct
levels and positive weights, but does not itself establish priority. The
review and corrections are in `reviews/moment_prior_final_a.md` and
`reviews/general_j_sharpness_b.md` under the run root.
