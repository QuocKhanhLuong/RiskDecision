# Orca AGY review and coordinator adjudication

2026-10-07; Run `run_67275a941164`. These are machine-agent critiques, not academic peer review. The coordinator checks arguments and artifacts; agreement among agents is not evidence of truth.

## Design critic

Task `task_9e120cb53a50`, Dispatch `ctx_7de6dfe673df`, AGY/Antigravity. Accepted `worker_done` at06:09:18Z; authored ignored local `work/agy_design_review.md`. Scope read-only except that report. No worker commits, market runs or method edits.

Accepted concerns: abstention must be separated from safety; compare against a baseline with access to the whole available history; do not transfer stationary inference to next-step conditional ES; do not infer ES from one fixed hinge; candidate selection on assessment data requires multiplicity accounting. The protocol reports switching, harm, conditional stress, recent512 controls and full-history historical+SE.

Rejected or narrowed claims in the raw review:

| Reviewer statement | Coordinator adjudication |
|---|---|
| Gate will abstain90–98%, or100% after multiplicity adjustment. | Unsupported numerical predictions; no such experiment had run. They are not evidence and are excluded from our findings. |
| Two distributions with identical VaR and identical hinge expectation at that VaR have different ES. | False: at a common actual VaR the variational identity fixes ES. The repository counterexample shares a fixed threshold, not both actual VaRs. |
| Difference of two ES values has zero mathematical relationship to ES of loss differences. | Equality generally fails, but subadditivity gives `−ES(B−A) ≤ ES(A)−ES(B) ≤ ES(A−B)`. “Zero relationship” is false. Runner computes differences of separately optimized empirical ES values. |
| Adaptive baseline necessarily invalidates this assessment bootstrap. | Selection on the **same assessment data** is a concern. Here all four weights are selected on prior training data; conditional on training they are fixed for an IID holdout. A gap does not establish exact independence for dependent families, which remain stress tests. The review's proposed design inconsistently reselects its baseline on its assessment block; that proposal is rejected. |
| Must correct over284 pairs because training searched285 portfolios. | Here the assessment sees only three frozen challenger contrasts. Conditional on independent training, multiplicity is three, not284. A method searching the entire bank on assessment would require a different correction. |
| Asymmetric-crash generator has state-dependent next-step distribution. | Its states are IID; next-step truth equals marginal truth. Only AR1 and Markov families differ in this experiment. |
| Historical+SE is established DRO. | It is a heuristic related to variance regularization; no exact DRO equivalence or guarantee is claimed for the repository implementation. |
| Clip-based DKW intervals are a comparable unbounded-ES control. | Clipping changes the target. This experiment instead compares absolute and paired multiplier recipes for the same unbounded loss target, clearly without a finite-sample guarantee. |

The design critique usefully identifies hazards, but its speculative percentages and several categorical statements cannot serve as research conclusions.

## Direct mathematical checks

For shared bootstrap noise, `max_j |Z_j−Z_0| ≤ 2 max_j |Z_j|`, hence the paired radius is no larger than the absolute-derived contrast radius. This holds draw by draw and for the empirical quantile. A narrower radius admits more switches; it says nothing about whether those switches reduce population ES.

Common-mode cancellation can be real. If `L_1=L_0+c` with deterministic c, ES cash additivity gives `ES(L_1)−ES(L_0)=c` exactly even when each absolute ES estimate is noisy. Conversely, heterogeneous tail events need not cancel. Tests verify the shifted-loss and identical-portfolio cases. Neither fact is a new theorem.

The centered ES influence approximation is `((L−q)+−E[(L−q)+])/.05`. Contrasts subtract two such influences. Reestimating each empirical quantile removes the fixed-anchor identity error in the empirical ES calculation; bootstrap approximation and finite-tail-sample error remain. Exact empirical evaluation is not exact population inference.

## Additional primary-source check

- [Hansen, Lunde and Nason2011](https://www.kevinsheppard.com/files/teaching/mfe/advanced-econometrics/Hansen_Lunde_Nason.pdf), sections2–3: uncertainty-aware comparison through loss differences is established. ES contrasts require nonlinear-functional inference; our simple gate is not an MCS implementation or a novel replacement.
- [Iyengar, Lam and Wang, OIC, v4/2025](https://arxiv.org/html/2306.10081v4): decision evaluation and correction of optimization bias already have a dedicated framework. Its smoothness/regularity assumptions must be checked before applying it to hard finite-bank choices; it was not run here.
- [Laroche et al2019, SPIBB](https://proceedings.mlr.press/v97/laroche19a/laroche19a.pdf): baseline-safe improvement exists in batch RL. This is conceptual overlap; RL policy-value guarantees do not certify a portfolio ES gate.
- [Pele and Mazurencu-Marinescu-Pele2026, preprint v1](https://www.preprints.org/frontend/manuscript/e42e8bf767108098bee7423701a6327e/download_pub): tail-information scarcity and pairwise ES-comparison diagnostics are already explicit research topics. Read this as prior-art scope, not verification of every equation or a universal lower bound for perfectly coupled ES contrasts. The publisher's later PDF could not be retrieved during this audit.
- [Bartl and Eckstein, v2/2026](https://arxiv.org/abs/2405.00357): robust finite-sample nonparametric ES estimation under IID sampling already exists. Abstract/version metadata checked; implementation and complete theorem audit NOT RUN.
- [He, Tan and Zhou2022](https://arxiv.org/abs/2212.05565): robust ES regression using orthogonal scores and high-dimensional inference already exists. Abstract checked; full comparative implementation NOT RUN. “Add orthogonality/robustness” alone is not a cleared novel direction.

This is a targeted search, not exhaustive novelty clearance. It eliminates easy renaming claims; it does not prove no useful contribution is possible.
