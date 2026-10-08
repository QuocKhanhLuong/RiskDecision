# Independent idea round — root, AI-assisted

Recorded before this round's literature search or reading delegated ideas.
Prior anchor disclosed: Q1/Q2/HMM results and existing repository research state.
User now prioritizes a defensible method/theory contribution over proceeding
straight to Q3. Preserve prior experiments and do not tune on their test seeds.

Focal question: can we distinguish or correct errors relevant to a *difference*
of portfolio risks under temporal state uncertainty, with less estimation cost
than learning a uniformly accurate distribution, without weakening strong priors?

R1 — Decision-relevant projection of state uncertainty. For two locked actions,
loss contrast Delta(theta)=R_theta(wA)-R_theta(wB). Propagate parameter/state
uncertainty through gradient of Delta rather than add standalone risk margins.
Potential claim: reject/recompute only when uncertainty crosses a decision
boundary. Falsifier: this is just paired inference/delta method/robust decision
making with no new mathematical result. Test adversarial parameter errors that
preserve vs reverse ranking. Must compare equally informed robust paired control.

R2 — Selection and filtering influence interaction. Conditional risk estimate
uses both a fitted model/filter state q(D) and selected action w(D). Optimism
formula must include derivative through the final state filter, not treat
conditional weights as fixed. Potential target: data-dependent conditional
prediction error after portfolio optimization. Falsifier: OIC on a composite
estimator already includes the derivative, or ordinary conditional forecast
bootstrap handles it; no generic distribution-free conditional guarantee.

R3 — Ambiguity that changes weights but not component shapes. Unknown transition
drift lives in state probabilities; minimize or certify portfolio loss over a
probability ambiguity set. Potential efficient analytic envelope/rank stability
for CVaR Gaussian mixtures. Falsifier: established mixture-weight DRO/robust HMM
already contains it. A useful diagnostic is not itself a new risk model.

All are IDEAS, novelty unverified. Criteria before selection: exact overlap with
prior math (veto for renamed baseline), falsifiable target, matched information,
analytic tractability, independent headroom, feasible bounded fresh experiment.
No numerical weighted ranking or invented certainty. Human novelty review absent.
