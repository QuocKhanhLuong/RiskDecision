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

## Code reviewer and chronology

Task `task_31929ff431c1`, Dispatch `ctx_05c6802d7bb6`, AGY headless through an Orca-created terminal. Accepted `worker_done`06:21:40Z; report `work/agy_protocol_review.md`. It found no execution-blocking code defect and approved the falsification scope, including the no-APTC ablation. It was instructed not to read new result directories. Its review began before execution but **completion arrived after the coordinator froze/pushed a2ad3f8 and ran the experiment**; the report's “before confirmatory execution” wording is not an accurate completion timestamp.

Coordinator corrections to this second report:

- Its predicted radii/abstention percentages are pre-mortem assertions, not verified new outcomes. Only the executed CSV supports percentages in the decision report.
- A32-step gap reduces dependence; it does not purge it exactly. Conditioning on training fixes weights but does not make a dependent holdout independent.
- A bootstrap maximum accounts for the chosen simultaneous comparison set, but does not by itself “rigorously control” finite-sample FWER. Coverage is measured here, not guaranteed.
- Student t4's infinite fourth moment rules out assumptions of some approximation bounds, not every CLT or fixed-dimensional bootstrap result. The ES influence has finite variance; no impossibility result follows from the fourth moment alone.
- Reading a verifier that reconstructs1,000 cases is not evidence it has already executed. The actual coordinator audit receipt is separate and post-execution.
- “Fully negative novelty clearance” is too categorical: this search shows close existing components, not exhaustive proof that no novel contribution can ever be built.

## Runtime provenance

The installed Orca launcher rejected `worker-start --agent agy` as `agent_unconfigured` before Task creation. Documented custom-command terminal + low-level Dispatch was used, with exact returned preambles; no native subagents substituted. Low-level Dispatch owns task context but not terminal lifecycle. Two genuine AGY reviews completed; numerical CPU processes are separate from those reviewers.

A third attempted novelty Dispatch `ctx_7f2a92e9798d` received input but never reported a task session or review. Its terminal `term_dec68aa0-c2d9-41ff-b8d5-33f966520caf` remains live with fleet status `unverifiable/missing_status`; it is **not counted as completed, failed, or independent evidence**. The orchestration recovery guide says “Absence never authorizes stop, abandon, retry, or release”; its unresolved state is preserved, not silently converted into a successful review. The coordinator performed and documented the primary-source novelty search independently.

The two completed review terminals were closed by exact handle after completion and ownership checks; Orca confirmed `ptyKilled: true` for each. The unresolved third terminal is retained. These low-level terminals were operator-created; `worker-release` alone reported no owned process resource and did not close them.
