# Frozen finite-grid coverage feasibility audit

Parent: `de51adecf6fefd3583a3f332ac123b0d907f99e6`. Written before inspecting this experiment's Monte Carlo outcomes. This is a diagnostic of uncertainty recipes, **not a new forecast model or fresh market confirmation**. The earlier synthetic and FX findings remain exposed development/held-out evidence as originally labelled.

## Question and prior art

Can a band around empirical tail-hinge means simultaneously cover population means for a fixed bank of portfolios and thresholds, at the calibration sample sizes used here? Does that coverage concern the stationary distribution or the next conditional distribution?

High-dimensional simultaneous mean inference under weak temporal dependence and block Gaussian multipliers already exists: [Zhang and Cheng, 2014, Sections 2.1 and 4](https://arxiv.org/html/1406.1037v2). We implement a studentized nonoverlapping-block variant, with a degrees-of-freedom factor, not a literal replication or a claim that their theorem applies automatically. Robust optimization / empirical-likelihood inference, including dependent stationary sampling, also has established theory: [Duchi, Glynn and Namkoong](https://arxiv.org/abs/1610.03425). Adding a bootstrap band to regularized maximum entropy does not, by itself, establish novelty. The earlier [maxent/decision-calibration comparison](NOVELTY_AUDIT_2026_10.md) still applies.

## Locked design

- Five fixed-parameter DGPs: Gaussian, Student t4, asymmetric crash mixture, stationary Gaussian AR(1) with coefficient0.6, and stationary two-state volatility with transition rows(0.985,0.015)/(0.12,0.88). Covariance construction uses seed62000. New samples use explicit Cholesky draws; historical snapshots are untouched.
- 100 independent seeds62000–62099 per DGP. Exactly500 generated series of1280 observations, eight assets. First256 observations fit the frozen three-component GMM recipe. Calibration sizes256 and1024 use nested prefixes following that base. All samples and failures retained.
- Same fixed285 long-only portfolios as the market runner, bank seed2026. Three anchor quantiles0.90/0.95/0.975 per portfolio:855 hinge features `h=(loss-eta)+`.
- Two anchor constructions: `base_only` uses GMM support only; `reused_mixture` uses half GMM support/half the calibration observations, as in v2. Thresholds remain fixed inside every multiplier draw. In IID families, base-only separates anchor fitting from calibration. Under dependence the contiguous blocks are not independent. Mixture anchors reuse calibration data and require additional empirical-process arguments for theory; this audit measures actual coverage without assuming such a theorem.
- Four radius recipes: the exact v2 heuristic floor/SE formula; IID studentized Gaussian max-t; short-block max-t (8 at n256,16 at n1024); long-block max-t (16/32). Bootstrap nominal level95%,499 draws, empirical quantile method `higher`. These block lengths are frozen sensitivities, not selected by observed coverage.

For `k=n/block` equal complete blocks, let `S_b` sum centered feature vectors in block b. Use `SE_j=sqrt(k/(k-1)*sum_b S_bj²)/n`. A bootstrap draw is `sqrt(k/(k-1))*sum_b G_b S_bj/n`, with independent standard-normal G. The critical value is the95th percentile of the maximum absolute standardized draw over855 features. Radius is critical×SE. IID is the special case block1. A zero SE receives zero radius, remains in the coverage test and is counted. The v2 heuristic is **not nominally a95% confidence band**; comparison with95% is diagnostic, not evidence that v2 broke a stated coverage guarantee.

## Targets, endpoints and interpretation

The population evaluator receives distribution parameters only after feature construction. For each observed threshold it computes exact normal-mixture or Student-t hinge expectations. Target1 is the stationary marginal distribution. Target2 is the next conditional distribution: identical in IID cases, conditioned on the last observed return for AR(1), and on the last **latent** state for Markov volatility. The latter is an evaluator-only oracle target, not an investor-observable information set.

Coverage endpoints are: all855 features simultaneously; equal-weight portfolio at q95; and the single feature with largest empirical standardized prior/calibration discrepancy. The last is selected without population information and used unchanged for every radius recipe. It audits an adaptive diagnostic feature, not the full eight-step APTC mining path.

Width is summarized as `radius/(0.05 * stationary population ES95)` for each portfolio, then the median/max across features, then the mean across seeds. This is a dimensionless **hinge uncertainty proxy**, not an ES interval. Both estimands share stationary ES normalization, avoiding negative conditional-ES denominators and making widths comparable.

Report160 strata, each with100 independent replications; the two n values, anchor types, estimands and procedures are paired views of these series, not additional independent replicates. Report pointwise Wilson95% Monte Carlo intervals. An upper interval bound below95% challenges a nominal95% recipe in that stratum; an interval containing95% does not prove validity. Multiple strata are not adjusted, and bootstrap critical values have finite499-draw noise. No tuning or method promotion follows from these results.

## Claims this design cannot establish

Three thresholds do not control all possible thresholds or guarantee inclusion of both distributions' ES minimizers. Thus a finite-grid band is not the uniform premise needed for the ES/regret bounds in [identifiability](CORRECTION_IDENTIFIABILITY.md). Unbounded hinges, Student heavy tails, estimated studentization, random anchors and selected features require their own assumptions. Stationarity is not conditional homogeneity. No generic theorem for these exact recipes is claimed.

A simple exact counterexample makes the last point: binary losses0/10 with stationary high-state mass0.02, high→high0.8 and low→high0.00408163265 have stationary ES95=4, next ES95=10 after a high state and0.81632653 after a low state. Even exact knowledge of every marginal hinge mean cannot turn that marginal distribution into the correct next conditional distribution. This is an elementary diagnostic example, not a novel theorem.

## Execution and publication

Machine rechecked: Apple M4 Pro,12 CPUs,25769803776 bytes RAM, macOS26.2 arm64. Python3.13.15/NumPy2.3.5/SciPy1.17.0/scikit-learn1.8.0. Two numerical processes, one numerical thread each. CPU parallelism is not independent agent review.

Freeze source/protocol hashes and commit before running500 cases. Tests exercise block equations, zero variance, no calibration leakage into base-only anchors, population evaluators, generators, the counterexample and aggregation pairing. Public artifacts are aggregate CSV, hashes, counts, protocol and report. Generated per-case NPZ/JSON/CSV stay under ignored `runs/`. No original market raw files, frozen code or historical snapshots are altered. No new market downloads, validation/test reruns, neural models or yield curves are part of this audit.

Independent Orca review was attempted: Run`run_067c302f5170`, Task`task_92882203de83`, Dispatch`ctx_08d4073e3791`. Full terminal stream positively showed `zsh: command not found: claude`, then shell parse error after the task text. No agent review occurred. The dispatch was abandoned after inspecting that evidence; release returned `retained: identity_unproven`, so Orca left the shell terminal in place. No unrelated terminal was closed. There is no substitute-agent or independent-review claim.
