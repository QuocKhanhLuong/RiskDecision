# Targeted novelty audit — 2026-10-05

Scope: distinguish the implemented APTC v2 objective, finite-budget mining heuristic and possible future contribution. This is a targeted primary-source audit, not an exhaustive literature clearance. No algorithm is declared novel from absence of a search hit.

| Primary source | Established overlap | Remaining distinction / implication |
|---|---|---|
| [Meucci, Fully Flexible Views, Risk2008; arXiv version2010](https://arxiv.org/html/1012.2848v1), sections2/4 and appendixA | Relative-entropy scenario reweighting, nonlinear views, inequality constraints and confidence pooling. | Reweighting simulated scenarios through KL and allowing approximate views are not standalone novelty. The current empirical tail targets and mining recipe need their own demonstrated contribution. |
| [Dudík & Schapire, COLT2006](https://www.schapire.net/papers/maxent_with_genreg.pdf), sections3–5 | Generalized maximum-entropy estimation, convex potentials and Fenchel duality, including combined L1 and squared-L2 regularization; sequential feature updates. | This is closer to the band objective than the earlier finance-only comparison. For fixed features, v2 is an instance of established regularized maximum entropy. Their guarantees are not automatically inherited by this data-dependent, dependent-time-series construction. |
| [Tang, Wu, Wu & Zhang, ICLR2026](https://proceedings.iclr.cc/paper_files/paper/2026/file/8ad060589ed7e18aea4ee1cc8a486c89-Paper-Conference.pdf), sections1–3 | Nonlinear decision calibration, limits of deterministic response, and dimension-free auditing under smooth response. | Merely calling tail moments decision-focused is insufficient. That paper uses iid observations, bounded losses and a different prediction/decision framework; it does not certify the hard argmin, unbounded hinges or temporal v2 recipe. |
| [Duchi, Glynn & Namkoong, 2018 arXiv revision](https://arxiv.org/abs/1610.03425) | Generalized empirical likelihood, divergence uncertainty sets, variance regularization, asymptotic inference including quickly mixing stationary sequences. | Dependence-aware uncertainty or a variance penalty alone is not an unoccupied claim. Historical+SE remains a heuristic here, not an implementation of their DRO certificate. |
| [Rockafellar & Uryasev, JBF2002](https://sites.math.washington.edu/~rtr/papers/rtr187-CVaR2.pdf), Theorem10 | ES/CVaR as a minimum over threshold-dependent hinge expectations, including general loss distributions. | One fixed hinge per portfolio is not a complete representation of ES calibration. The attached counterexample is an elementary diagnostic, not a new risk-measure theorem. |

## Exact objective mapping (our algebra)

For `phi(r) = (|r|-delta)_+^2/(2rho)`, maximizing `u*r-phi(r)` gives `phi*(u)=delta|u|+rho*u^2/2`. Combining this conjugate with the log-partition conjugate of KL yields the implemented dual

`log sum_i p0_i exp(-A_i'v) + B'v + delta ||v||_1 + rho ||v||_2^2/2`.

Thus the fixed-feature optimization is a regularized maxent instance. This mapping does **not** establish that all data-selection rules, support augmentation and mining steps reproduce an existing complete algorithm. It does eliminate the convex objective and L1/L2 band dual as defensible standalone novelty claims.

## Gate before another method

The open empirical question is whether the **adaptive correction** improves common-target risk estimation or allocation beyond support mixing and matched random directions. The development-only diagnostic is designed to answer that question. A favorable subgroup cannot replace the full results or become a rule tuned from viewed final tests.

A future contribution would require a precise departure from these frameworks and a useful, valid guarantee or robust new empirical mechanism. Simultaneous threshold/portfolio control under adaptive temporal sampling is a possible research problem, not a claim that such an idea is new. No new neural architecture or additional dataset is needed to settle the current component question.
