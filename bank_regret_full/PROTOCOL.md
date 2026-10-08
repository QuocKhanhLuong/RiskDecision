# Full synthetic extension, prospective 2026-10-08

User requests "chạy full đi" after the 96-case pilot. Interpret as completing
a larger, fresh-seed synthetic validation of the SAME methods, not a claim of
novelty or authorization to tune a policy on viewed pilot tests. This decision
supersedes the previous next-action-only literature gate for execution scope;
prior-art priority remains unresolved. All 755 tracked files at the start,
including bank_regret/config.json and all pilot outputs, remain unchanged.

## Estimands and frozen methods

Import the complete existing bank_regret policy and DGP without modification.
Keep window512, 32 scenarios, 8 assets, bank128, alpha=.05, conjugate .5 priors,
4 emission posterior draws plus nominal world, q interval [.05,.95] posterior
quantiles, .001 times turnover cost, shift at448 inside the observation window.
Same ten policies/ablations; same observed-context information, decision lock,
true conditional ES evaluator and warnings. No latent HMM or market evidence.
World/q comparator is shared absolute ES-difference regret, not a ratio.
The finite stress set still does not provide statistical true-law coverage.

24 independently seeded public dictionaries/portfolio banks, each with64 new
histories in EACH family (stationary and component_shift): 3,072 histories.
Public bank and histories use a namespace disjoint from the pilot. The same bank
is used for both families; histories are independently seeded by family.
No study outcomes are reused or pooled with the pilot. The sampling unit for
generalization across environments is the BANK cluster (24), not3072 histories
or393216 action-history pairs. The estimator averages histories within bank,
then averages the24 equally weighted bank means, separately for each family.

Primary contrast remains shared_full minus rectangular_full true ES+cost regret;
secondary shared_full minus point. Report all ten policies, harmful switches,
switch costs, forecast MSE on the common bank, stress-bound underestimation,
full/endpoints action differences and factorial interaction. Pointwise95%
percentile bootstrap CIs resample24 bank means with10,000 seeded replicates.
For the two family-specific primary contrasts also provide97.5% intervals
(Bonferroni simultaneous nominal95% across the two). No guarantee of finite-
sample coverage for this bootstrap. Report bank-level effects and win counts.
No interim outcome inspection, adaptive stopping or winning-model deployment.
Replication is compute-bounded, not a formal power claim; 24 clusters limits
precision. "Full" means this finite registered matrix, not all possible DGPs.

Pre-freeze namespace hygiene: the first software-test pass internally generated
one prototype v1 policy history without reporting effectiveness. Final assessment
uses namespace v2; all subsequent tests append /unit-tests. This administrative
seed separation is made before preflight/freeze, not in response to policy scores.

## Computational matrix and memory

Full factorial bank size {8,32,128,512,2048}, support {16,64,256}, alpha
{.01,.05,.2,1}, four independent replicates per cell:240 cases. For every alpha,
replicates0/2 use full q interval and1/3 use random subintervals. This balances
interval type across alpha (unlike the pilot's alpha/replicate coupling).
Reuse original input generator/solvers via config adapters. Every alpha gets
its own seed namespace; alpha is the sole entry of benchmark_alphas, so the
unchanged generator uses the requested alpha for each replicate.

Same strong union-knots/global-hull comparator, same laws/costs, three timing
repetitions with alternating call order. Randomize case order within this stage.
Run timing cases serially with no policy pool active; one BLAS thread. Report
per-alpha results, numerical failures/ties, measured wall times and risk-query
counts. Runtime variation is not independent scientific evidence.

30 extra memory measurements: each size/support at alpha=.2, replicate0,
one fresh subprocess per solver. Record process peak RSS including Python,
imports, inputs and solver (ru_maxrss: bytes on macOS, KiB on Linux), plus
pre-input peak. Their difference is only an incremental high-water indication,
not a direct allocation or exact solver-memory measure. Memory cases reuse
benchmark inputs and are not new independent accuracy samples. No tracemalloc
claim for all NumPy/native allocations. Run these serially too.

Every learned policy case additionally compares the complete shared regret
vector with the union-knots solver on all5 fitted worlds; retain max error and
selected-index agreement. This is software verification on the same history.

## Compute gate, freeze and resume

Before full outcomes, preflight one distinct development case for each of60
size/support/alpha strata with one timing repetition, and four development
policy histories. Project full serial benchmark time from3x these timings,
policy time from measured worker throughput, and memory time from corresponding
largest/full-interval development timings. Record the conservative projection
and refuse full execution if above3600 seconds. This gate only uses timings,
numerical checks and RSS, never policy effectiveness. No smaller matrix is
silently substituted if the gate fails.

Freeze module code/config/protocol, imported bank_regret and mixture_order
Python sources and pilot config, Python binary/library/platform/thread settings.
Persist deterministic job layout and gzip JSON per-case checkpoints with body
digest, task identity, input hash, timings and warnings. Atomic replace and
exclusive run lock. Source/config/environment drift requires a new directory.
Partial exit3, full exit0, numerical failure exit1. No-op resume must create no
new cases and preserve checkpoint bytes; it validates payload and task identity
against the freeze, not a full refit. Deep verification separately regenerates
all input hashes/history/ground truth, recomputes summary, and refits fixed first
two histories per bank/family (96), never selecting samples based on outcomes.
Those refits get independent LP risk checks for chosen/benchmark actions.

Progress JSONL and tqdm/ETA per stage, periodic heartbeat while futures execute,
outer invocation wall times including validation. Policy stage uses four CPU
processes only for computation, not independent AI or human review. Stages do
not overlap. Failed work remains recorded; no failed history deletion.

Publish a new research branch, all synthetic receipts/checkpoints and one final
consolidated report. Keep RUN/VERIFIED, READ/REPORTED, PROPOSED and NOT RUN clear.
Market data, new OIC/HMM/model variants, reserve utility, full-text novelty audit
and human review are NOT RUN by this command.
