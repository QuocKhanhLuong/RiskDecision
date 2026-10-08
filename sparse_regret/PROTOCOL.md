# Frozen sparse-regret computational audit

Decision, 2026-10-08: user requested continued novelty research and previously
authorized a full run. This is a new theorem/algorithm audit following the
negative/mixed policy findings. No forecaster is selected or trained, and no
historical assessment is repurposed as fresh evidence. All previous tracked
files remain immutable. New seeds do not create new market observations.

Object: every action's maximum absolute ES difference from the best action in
a fixed finite bank under the same probability-law mixture. Mixtures range over
the FULL component simplex. Nonnegative fixed costs are supported. Upper-tail
mass alpha is used; alpha=1 is the expectation control. The statistical/market
meaning of supplied component laws is outside this computational experiment.

## Locked tasks

- 72 LP cells: M={2,8}, S={8,24}, R={3,6,12}, alpha={.05,.2,1}, two inputs/cell.
  Compare the complete regret vector and attained witnesses from edge/local,
  edge/union, and independent unrestricted R-dimensional RU LP enumeration.
  LP is measured ONCE; edge solvers three times. Report timings as such.
- 72 scaling cells: M={64,256}, S={32,128}, same R/alpha/replicates. Compare
  edge/local against edge/union, both sharing the identical bank hull; three
  sequential timing rounds in seeded alternating order. LP NOT RUN here.
- 24 exact rational audits: R={3,4}, 12 replicates each, M=3, S=6,
  alpha=1/5, integer masses/losses and rational fixed costs. Enumerate every
  active set of the full-dimensional own-quantile polytope, including both
  quantile inequalities. This oracle makes no support-two shortcut. Compare
  with both numerical solvers. Fraction arithmetic results are saved.

For numerical inputs, draw common scenario/action losses from normal factors
plus action noise, round to 2 decimals (ties), inject zero probability atoms,
and duplicate a component in every third input recipe. Keep all cases. Costs
are fixed uniform[0,.01]. All random streams are SHA256-derived from namespace,
task identity and development/assessment partition. No outcome-based tuning.

Gates: finite output, LP success and primal residual <=2e-8, full-vector
absolute error <=2e-8, each recorded competitor is optimal at its witness and
attained regret agrees within 2e-8. Record raw argmin disagreements separately
from regret-value disagreements; a numerical tie is not a different theorem.
No tolerance sweep, dropped cases, fresh reruns of inconvenient timings,
speedup threshold, or learned-policy superiority test is authorized here.

Preflight: smallest and largest LP cases and largest scaling case with a
disjoint development seed; project total computational time <=1800 seconds.
If over budget, STOP full run and make a new protocol/run, retaining this one.
No theorem or algorithm tuning based on development speed. Three timings
include input-to-bank creation outside solver but per-edge construction inside.
Single BLAS thread; no concurrent benchmark workers. Process memory NOT RUN.

## Receipts / resume

Source, protocol, config and runtime are hashed before preflight. Each checkpoint
has task/freeze/payload SHA256 and compressed deterministic bytes. Resume validates
all receipts, never overwrites a case, and rejects source/runtime changes. A
partial execution and a completed no-op resume must preserve checkpoint bytes.
Append progress JSONL with actual elapsed time, warning list and ETA; tqdm is
written to invocation logs. Preserve failures and exceptions. Summary and plots
must include slower/tied cases, alpha=1 control and all fixed task cells.

Generalization to integrable component laws and finite spectral sums is a
mathematical argument, not validated by synthetic benchmarks alone. Rational
sharpness fixtures are construction evidence, not sampled population results.
Novelty/priority requires the separate primary-literature comparison; passing
this protocol does not assert it. Calibration, utility, new OIC/market/HMM runs,
continuous-action optimization, neural training and submission remain NOT RUN.
