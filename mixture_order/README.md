# Finite research gates: mixture risk order and conditional optimism

This package is an executable diagnostic, not a new risk forecaster or a
published novelty claim. The user-directed novelty audit is additive to the
historical Q0/Q1/Q2/HMM packages. See the prospective [protocol](PROTOCOL.md).

For two supplied finite loss laws at each of two states, `paired_certificate`
computes the largest difference in upper-tail ES at a **shared** state mixture
probability. Inputs are fixed actions and known laws. The alpha parameter is
tail mass (0.05 means worst 5%). Atoms use the fractional-tail definition.
For supplied floating-point inputs, this is an exhaustive piecewise-affine
solution up to floating-point error, not an interval-arithmetic certificate.

Let the descending loss support of one action be x_1,...,x_S. The mass strictly
above its active tail threshold and corresponding first moment are affine in
q. Within a region where the threshold x_k is unchanged,

`ES(q) = [M_above(q) + (alpha-P_above(q))*x_k] / alpha`.

The threshold can change only when a cumulative mass equals alpha. Each
cumulative mass is affine in q, so each has at most one isolated crossing
(constant equalities produce the same ES on both threshold choices). Forming
the union of crossings for A and B partitions the interval into regions where
their risk difference is affine. Its maximum occurs at a region boundary.
Sorting, prefix sums and binary search give O(S log S) total work and O(S)
memory for total support size S. This is the standard RU lower-envelope
structure specialized to a two-component mixture. `hull_certificate` implements
the equally efficient generic affine-line hull comparator. No asymptotic
advantage over this comparator is claimed.

This object is neither ES(A-B) nor max_q ES(A;q)-min_q ES(B;q). The latter is
an upper bound that can be unnecessarily conservative because its two extreme
laws can disagree. The package does not estimate a statistically calibrated q
interval, handle component estimation error, optimize portfolio weights, or
certify unseen market performance.

The Gaussian AR(1) check uses half squared loss throughout. Exact finite
correction removes expected optimism over histories. The residual conditional
error has a nonzero quadratic-form variance, even with oracle parameters.
This falsifies a deterministic correction as exact conditional recovery and
does not prove every possible history-dependent correction impossible.

Run in the existing project environment (NumPy, SciPy for independent test LP,
pytest, tqdm); no new dependency installation is required:

```bash
rtk proxy .venv/bin/python -m pytest -q tests quant_research_v2/tests
rtk proxy .venv/bin/python -m mixture_order.run preflight --out runs/novelty_audit/20261008/finite_gates
rtk proxy .venv/bin/python -m mixture_order.run run --out runs/novelty_audit/20261008/finite_gates --max-new-cases 5
rtk proxy .venv/bin/python -m mixture_order.run run --out runs/novelty_audit/20261008/finite_gates
```

The last command resumes or verifies a completed no-op run. Per-case hashes
detect accidental checkpoint alteration, and source/config/environment changes
require a fresh output directory. Progress JSONL and tqdm preserve timing/ETA.
Intentional partial runs exit 3; full successful runs exit 0; failed gates exit
nonzero. Resume also regenerates mixture inputs from frozen seeds and verifies
their risk certificates. These hashes are reproducibility checks, not signed
protection against an actor rewriting code and receipts together. Overflow and
invalid floating-point intermediates raise instead of returning a risk bound.
The source/config/protocol receipt precedes stochastic results. Re-execution
after reading these outcomes is reproduction, not fresh confirmation.
