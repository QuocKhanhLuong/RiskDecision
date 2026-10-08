# Compositional study, prospective 2026-10-08

User now permits a modestly broader question and coherent combinations of minor
contributions. This run follows independent generation and bounded primary-source
checks, before stochastic test output. Preserve all 621 existing tracked files.
No old test outcome is used to choose a new model or hyperparameter. One report
will combine a computational theorem, implementation and a policy audit.

## Target and potentially useful composition

For a finite bank i, supplied component world k, q in [lo_k,hi_k], fixed
incumbent-dependent costs c_i and upper-tail probability alpha, define
f_ki(q)=ES_alpha(loss_i; mixture_k(q))+c_i,
g_k(q)=min_j f_kj(q), R_i=max_k max_q [f_ki(q)-g_k(q)].
Select argmin_i R_i with lowest-index tie breaking. The q, component world,
cost convention and bank in the comparator must be shared. This is an absolute
ES-difference regret, not a ratio, ES of pathwise regret, or cumulative trading
regret. No dynamic optimality or safe-improvement guarantee is claimed.

Each f_i is a concave lower envelope of affine RU threshold lines. The bank
envelope g is one lower hull over all lines. On an action's own affine interval,
f_i-g is convex, so its maximum is attained at an own endpoint. Querying only
the action's own quantile crossings/endpoints gives all bank regrets in
O(K log K) time/O(K) storage, K total support thresholds. Owner witnesses identify
the competing action at the worst q. Sum these costs over finite component worlds.
Known ingredients are RU, convex hulls, minimax regret and switching costs.
The action-local witness reduction is the candidate computational contribution;
its priority is NOT ESTABLISHED and it may be a known convex-analysis corollary.

## Stage C: exactness and computational comparison

Strong comparator: same global hull and same prepared losses, but evaluate every
action at the UNION of all action knots. This is exact, not a coarse grid or
naive-only pairwise baseline. Small tests also compare direct pairwise RU/LP
enumeration independently. Compare complete risk-regret vectors and witness
values, not only the selected index; near ties cannot imply ranking certainty.

32 cases: full Cartesian M={8,32,128,512}, S={16,64}, replicate=0..3;
alpha={.01,.05,.2,1} determined by replicate. Independent t5 loss arrays and
Dirichlet(.3) component masses per action; fixed random action costs in [0,.1].
Even replicate intervals [0,1], odd replicate deterministic-seeded subintervals.
No synthetic case is a real market, and bank actions are not independent trials.
Time whole solvers from prepared immutable laws, including hull construction;
report preprocessing separately. Alternate call order, 3 repetitions each.
Record absolute errors, evaluation counts and median timings, including losses.
The operation bound is proved analytically; measured speed ratios are local
Python/NumPy implementation results, not hardware-independent complexity evidence.

## Stage P: learned-component one-step policy audit

This is a **new observed-context categorical benchmark**, not a rerun or claim
about historical hidden-state HMM results. A binary context z_t is publicly
observed. At time T every method gets the same last512 pairs (z_t,scenario_t),
the public 32-scenario asset-loss dictionary and the same fixed bank of 128
8-asset portfolios (long-only, sum1, cap.5, equal-weight index0). Future context,
true transition/emission probabilities and post-T outcomes never enter fitting.

Training: standard conjugate Dirichlet categorical emission posterior per
observed context and Beta next-context transition posterior from transition
counts. Priors are .5 per category/outcome. Nominal world uses posterior means;
four additional worlds are posterior draws of both emission distributions.
For each world use the Beta posterior .05/.95 quantile interval for next-context
probability. This is a finite **posterior stress set**, not a simultaneous 90%
confidence set for the unknown true law. Discrete emission worlds generally do
not contain the true emission law. Truth-bound violations must be reported.
All methods use this same fit, bank, world set, costs and information.

Public synthetic environment: dictionary generated from fixed Gaussian common,
sector and asset-specific factors (scale .01); context emission masses tilt
toward opposite signs of the public sector factor. Transition matrix
[[.94,.06],[.12,.88]], stationary initial context. In component_shift, swap the
two emission laws at t=448; only evaluator knows that change. Same fit in both
families; no drift detector or model search added after outcomes. Seed namespaces
are distinct by family and history, with 32 independent histories per family.
Incumbent is fixed equal-weight; one-step cost .001*(L1 distance/2). These costs
are scenario assumptions, not measured transaction costs, utility or profit.

Frozen policies / ablations:

- point: nominal posterior-predictive ES plus cost, optimizing actual mixture ES;
- shared_full: all worlds, shared q, full ES threshold changes (main composition);
- shared_endpoints: same but only q interval endpoints;
- rectangular_full: separate max chosen cost and min benchmark cost across laws;
  argmin equals standard absolute worst-case ES. This is the strongest structural
  same-fit control for the policy contrast, not a novel method;
- rectangular_endpoints: factorial companion;
- nominal_components: shared_full with only posterior-mean emissions;
- fixed_q: shared_full with q fixed to posterior mean in every emission world;
- ignore_cost: shared_full chooses with zero costs, evaluated with actual costs;
- historical: empirical unconditional ES on the same512 observations plus cost;
- incumbent: keep equal-weight.

Primary policy contrast: shared_full minus rectangular_full true conditional
ES+cost regret within the same bank. Secondary contrast: shared_full minus point.
Each family reported separately; mean paired differences and 95% percentile
bootstrap CIs resample the 32 independent histories (4,000 replicates). No
family pooling or action-count pseudoreplication. Exploratory pilot: sample size
is compute-bounded, not powered for broad superiority; no formal accept/reject
claim from CI alone and no winner-picked-after-test deployment.

Factorial interaction in true net regret is
(shared_full-shared_endpoints)-(rectangular_full-rectangular_endpoints).
Report point forecast MSE on the COMMON bank separately; all same-fit policies
have exactly identical nominal forecasts. True conditional risk uses evaluator
probabilities, not one future loss. Report switch rate, harmful switch rate vs
incumbent, cost/turnover and stress-certificate underestimation by true regret.
No forecast improvement claim may be inferred from a different selected action.

## Execution, boundaries, stopping

Run exact unit/regression tests first. Preflight benchmarks the largest C cell
and one development P history, records projections and refuses >240 seconds.
It is only a compute/numerical gate, not policy tuning. Freeze source/config,
imported historical dependencies and environment before fresh test draws. Case
seeds, deterministic input hashes, learned worlds, decision vectors, witness
records and full history inputs are retained. Source/config changes need a new
output directory. Partial exit3, full successful exit0; per-case payload hashes,
expected input checks, tqdm/ETA, JSONL progress, actual timings and warnings.
Exercise partial5/full/no-op resume with unchanged checkpoint hashes.

Before freeze, reviewer A requested stronger same-history invariance: posterior
RNG seed is derived only from the observed history and public-design hash, not
family/index labels. Resume re-creates the conjugate fit, finite worlds and
decisions to verify their identity; it skips new benchmark timings/data/evaluation.
Those verification calculations are reported separately from newly completed cases.

No new raw market data, archive replay, hidden-state HMM refit, OIC variant,
neural sweep, estimated-law coverage proof or human peer review in this run.
If exactness fails, stop scaling and keep failure. If the composed policy is
neutral/worse, retain the solver result separately and do not rename that as
forecast novelty. Prior-art overlap may limit the contribution to a useful
algorithmic specialization and benchmark; absence of a located paper is not
evidence of priority.
