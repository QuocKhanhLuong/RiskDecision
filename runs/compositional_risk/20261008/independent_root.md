# Root independent generation — compositional research

2026-10-08. Written before this round's external search or exposure to the two
other reviewers' ideas. AI-assisted. Prior anchors: frozen Q0/Q1/Q2/HMM results,
conditional-vs-average failure and the finite-mixture ranking witness. The user
now accepts several small contributions forming a coherent whole. This broadens
the question; it does not license retrospective novelty claims or test tuning.

Focal question: when can a learned conditional risk model justify changing a
portfolio, and can shared uncertainty plus decision structure reduce needless
conservatism or compute without weakening the target? Useful scientific outputs
can include a new problem decomposition, a justified algorithmic specialization
and evidence of a component interaction; novelty remains to be checked.

R1 — A shared-world conditional-risk switching policy. Fit a standard conditional
model, retain joint alternative fitted distributions rather than separate risk
intervals, and compare each proposal against the incumbent under the same law.
Add an explicit switching-cost margin. Known: robust policy improvement,
relative CVaR, scenario ensembles, transaction costs. Potential interaction:
joint uncertainty cancellation makes safe switching possible where independent
margins abstain; interior quantile changes invalidate an endpoints shortcut.
Falsifier: reduces exactly to existing robust dominance/minimax regret; all gains
come from a different ambiguity set rather than a new decision rule. Must compare
same world set and fit, and keep empirical stress robustness separate from coverage.

R2 — Output-sensitive bank-wide ES regret envelope. For many fixed portfolios,
each finite-mixture ES is the minimum of affine RU threshold costs. The best
portfolio's risk is the lower envelope of *all* these lines. Build it once and
compare each portfolio curve to it rather than compute every pairwise contrast.
Known: RU, convex hulls, minimax regret. Potential contribution: a specialized
output-sensitive exact solver plus decision witnesses and a switch/no-switch
policy, with a testable complexity gain over pairwise certified comparisons.
Falsifier: generic RU global hull is already the strongest natural baseline;
worst-case complexity remains quadratic in the number of actions. Need actual
equivalence proof and a comparator with common preprocessing and no fake grid.

R3 — Allocate numerical/model-refinement budget near tail-risk decision ties.
Keep cheap lower/upper risk bounds per action and refine only overlapping
contenders, stopping when the selected action has a certified epsilon-regret.
Known: best-arm identification, branch-and-bound, adaptive quadrature, safe
screening. Potential interaction: integrate state-mixture quantile crossing
certificates with common uncertainty so that refining irrelevant tails is avoided.
Falsifier: ordinary branch-and-bound does everything; approximation errors or
data-dependent stopping invalidate the guarantee, or refinement overhead wins.

R4 — Reframe contribution as conditional-risk evaluation plus policy, rather
than a new risk forecaster: same estimated distributions, common-target scores,
regret/switching decisions, and a stress-axis identifying when a component helps.
Known: crossed evaluation and robust policy evaluation. Potential useful artifact:
an executable benchmark showing complementary error sources and an ablation
interaction, coupled to a rigorously scoped method specialization. Falsifier:
only a benchmark convenience with no general insight or independently useful
method; must not call engineering packaging method novelty.

Selection criteria before results: identifiable target; novelty at the level of
the interaction rather than ingredient counting; strongest same-information
control; exact falsifier; coherent guarantee or explicit absence; bounded compute;
prospective ablations isolating uncertainty coupling and tail-threshold handling.
No automatic winner or weighted novelty score. All ideas are PROPOSED.
