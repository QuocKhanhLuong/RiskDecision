# Decision-gap falsification — frozen before new outcomes

Parent `a9b6dff`; date 2026-10-07. This is a falsification of a generic decision gate, **not a proposed APTC v3 or a new confidence theorem**. Previous market final tests remain exposed and are not accessed.

Question: does preserving paired uncertainty between portfolio ES estimates produce useful safer decisions, beyond conservative absolute-risk intervals and strong controls with the same available history?

## Data and separation

Run 200 new seeds 81000–81199 for each of Gaussian, Student t4, asymmetric crash, AR1(.6), and Markov volatility. Use the unchanged stationary Cholesky generator from the coverage study, fixed 8-asset parameters and fixed 285-portfolio bank seed2026. These are five synthetic mechanisms, not five markets. Development smoke uses only Gaussian seeds80000/80001. Cases within a family are independent; sizes256/1024 are nested and must not be pooled as independent replications.

Train frozen v2 recipes on the first512 observations. Baseline is the portfolio chosen by historical+SE; challengers are the portfolios chosen by pure support_mix50, support_band50 and FHS on exactly that training sample. Freeze all four weights, skip32 observations, then assess on the next256 or1024 observations. The gap reduces dependence but does not create independence in dependent families. No refitting of these frozen portfolios on assessment observations.

On the assessment sample, reestimate each portfolio VaR95 and compute exact empirical ES95, including partial tail atoms. Centered influence approximation is `(L−VaR_hat)+/.05` minus its sample mean. This avoids treating a fixed training hinge as ES and avoids treating one realized loss as true ES. It remains a first-order approximation with estimated thresholds, vulnerable to small tail samples and heavy tails.

Use999 Gaussian multiplier draws shared by all four columns, with complete nonoverlapping blocks:1 for IID families,16 for dependent families. For simulated estimation noise `Z_bj`, absolute radius `a=quantile95(max_j |Z_bj|)` gives contrast radius2a. Paired radius `c=quantile95(max_j>0 |Z_bj−Z_b0|)`. Both use the same draws and no per-hinge studentization. Point control uses radius0. For each rule, switch to the smallest assessed ES challenger only if its estimated difference plus radius is below−1e−12; otherwise retain baseline. Ties retain baseline. Because c≤2a for every draw/quantile, the paired rule admits at least every absolute-rule switch; this algebra is not evidence that extra switches help.

## Truth, controls, metrics

Preregistered candidate-removal ablation `paired_no_band`: remove APTC's challenger from both the menu and the bootstrap maximum, retaining pure mixture and FHS; use identical observations and multiplier draws. Compare paired risk outcomes against the full gate. Merely selecting a slot labeled APTC is not proof of incremental contribution because portfolio choices can coincide. This ablation was added during code review before freezing or running new seeds.

Population evaluator runs after fitting and gating. Primary target is stationary marginal ES95. Secondary stress is next-step conditional ES95; Markov truth uses evaluator-only latent state, not information given to methods. A stationary gate does not claim conditional coverage. Conditional ES can be negative: normalize all risk differences by the positive **marginal training-baseline ES**, and all regrets by the **marginal finite-bank minimum ES**. Never discard a case because conditional ES is negative.

Report switch frequency, harm frequency (selected true ES > baseline true ES), simultaneous three-contrast coverage, radius, available true improvement, chosen challenger, and normalized risk/regret. Harm frequency is unconditional; also report harm among switches with its denominator. No certification follows merely from low observed harm, especially with few switches.

Controls: retain training historical+SE, each training challenger, equal weight, historical+SE fit to all currently available observations, and recent512 historical+SE/pure mixture/APTC/FHS. All controls have the same cutoff; recent models can adapt using assessment history and are compared to the gate as competing end-to-end uses of the data. The holdout cost and staleness of training decisions are part of the method's cost. Full-history historical+SE is an additional same-budget control; recent recipes preserve v2's fixed512 contract.

Separately compare model ES forecasts on the **same equal-weight target** and errors of the whole common bank and contrasts to the fixed training historical+SE portfolio. These diagnostic forecast errors are not selected-portfolio outcomes, market FZ0 scores, or evidence from future realized single losses.

## Decision criteria and reporting

Report every family and size; no method tuning or selection from outcomes. Wilson95 intervals for binary frequencies; deterministic paired seed bootstrap10000 for mean differences. Intervals are descriptive pointwise, not simultaneous claims across all tables. Gate deserves another study only if, at n1024 in **every IID family**, harm Wilson upper≤5%, switch Wilson lower≥10%, and mean paired risk-difference CI upper<0 versus training historical+SE, recent historical+SE, recent pure mixture and recent FHS. Dependence/conditional stress can falsify broader claims. Passing would establish neither novelty nor deployable safety. Failing is NO-GO for promoting this gate as a new method; do not repair it after seeing outcomes.

Implementation and config hashes are frozen in `configs/decision_gap_freeze.json`, committed before running seeds81000–81199. Local arrays/cache remain in ignored `runs/`; aggregate CSV, receipts and independently checked report tables may be published. Two CPU processes are numerical parallelism, never independent reviewers.

## Prior-art boundary

The [Model Confidence Set](https://www.kevinsheppard.com/files/teaching/mfe/advanced-econometrics/Hansen_Lunde_Nason.pdf) already formalizes comparisons using dependent loss differences and uncertainty about the best alternative. Our ES difference is a difference of nonlinear functionals, not directly its mean-loss statistic; this distinction does not make generic paired bootstrap novel. [OIC](https://arxiv.org/html/2306.10081v4) already targets decision evaluation and optimization bias. [SPIBB](https://proceedings.mlr.press/v97/laroche19a/laroche19a.pdf) addresses baseline-safe improvement in batch RL, under assumptions that do not transfer to this ES gate. These works motivate strong controls, not inherited guarantees.

Reproduce: `rtk proxy bash scripts/reproduce_decision_gap.sh`.
