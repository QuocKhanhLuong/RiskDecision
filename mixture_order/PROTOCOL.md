# Prospective finite gates, 2026-10-08

User explicitly prioritizes novelty research over the pending Q3 market audit.
This additive branch preserves every historical tracked file. The independent
idea round and literature search precede this protocol; the deterministic
counterexamples were already derived and are **development evidence**, not an
unseen test. No learned model, financial strategy, test-seed selection or market
download is involved. Config/source hashes are frozen by the runner before any
random stress results are opened. Revisions after a run require a new run ID.

## Gate M: shared-mixture order, fixed actions

Loss convention: alpha is the **upper-tail probability**, not confidence level.
For two fixed actions A,B and laws P0,P1, certify
`max_{q in [lo,hi]} [ES_alpha(A;Pq)-ES_alpha(B;Pq)]`, Pq=(1-q)P0+qP1.
Use fractional atoms via Rockafellar-Uryasev (RU), not naive conditional means.
The q and component laws are supplied inputs, not estimated confidence sets.
No sampling coverage, calibrated reserve or market claim is allowed.

Proposed implementation: sort each finite support, build cumulative mass and
first moments, enumerate tail-mass crossings, evaluate using vectorized binary
search. Complexity O(S log S), including sorting, with O(S) memory. Strong
comparator: generic lower convex hull of RU affine threshold costs; it has the
**same asymptotic complexity**. Agreement is a correctness gate, and equivalence
vetoes a standalone algorithmic novelty claim. Report actual timing against
this comparator, even if the specialized implementation loses. A naive dense
grid is only a diagnostic and cannot serve as an exact strong baseline.

Known witness: alpha=.05; state0 A=0,B=1; state1 A=10, B=11 with probability
alpha else 0. D(0)=D(1)=-1 but D(alpha)=8.5. Exact rational check is required.
The two actions can be (.5,.5,0,0) and (0,0,.5,.5) with duplicated within-pair
asset losses. They are fixed; no optimization over a bank or fitting follows.
For locked RU thresholds, each objective is affine in q and endpoints suffice;
this gate **does not contradict** historical Q2's locked-(w,v) calculation.

Stress suite: 256 cases, support sizes 8/32/128/512 balanced; alpha .01/.05/.2/1
balanced within size. Independent t5 support values and Dirichlet(.3) state
masses for each action; B has three extra atoms. Even cases use [0,1], odd cases
use a deterministic-seeded random subinterval. Compare maxima/entire piecewise
curves to generic RU hull within absolute 1e-9. Record endpoint underestimation,
false endpoint-safe certificates, separate-max/min conservatism, and timings.
These frequencies describe only this artificial generator, not markets.
Input arrays and all case seeds are saved. Every case stays in the report.

## Gate T: average optimism versus terminal conditional risk

Stationary Gaussian AR(1), Var(X)=1, theta_hat=sample mean,
ell=.5*(theta-X)^2. T in {32,128,512}, phi in {0,.5,.9}; nine distinct seeded
cells with 32,768 independent histories each. No parameters are fitted. Both
correction and direct forecast receive the same **oracle** phi and variance;
this is a mathematical falsifier, not an equally informed learned-model result.

Let u=ones/T, a=u-phi*e_T, Sigma_ij=phi^abs(i-j),
A=.5*(aa' - I/T + uu'), c=.5*(1-phi^2). Then conditional-minus-training
half-loss is `G=X'AX+c`, its exact mean is
`Delta=Var(mean)-Cov(mean,X_next)`, and variance is `2 tr(A Sigma A Sigma)`.
Finite correction Delta is optimal among **constant** additive corrections
under MSE, yet residual conditional MSE is Var(G)>0. This falsifies exact
terminal recovery by a deterministic transport correction. It does not rule
out all history-dependent estimators. Infinite-lag correction is
1/[T*(1-phi)], and its MSE excess is (infinite-Delta)^2.
Direct analytic conditional half-loss is
`.5*((theta_hat-phi*X_T)^2+1-phi^2)` and is an oracle zero-error control.
All quantities use the half-loss convention; no factor-of-two mixing.

Compute exact matrix traces independently of finite-lag sums. Monte Carlo
checks mean and MSE against analytic answers within six estimated standard
errors; report all errors and signs. This is a software/algebra check, not a
statistical discovery threshold. Check iid reduction and the negative-phi
boundary in tests. If the general conditional claim fails, **no tail-model
training** follows in this run.

## Execution and audit

Preflight benchmarks four mixture cases plus one smaller AR cell; refuse full
execution if projected compute exceeds 180 seconds. Timings are local CPU,
not GPU or production benchmarks. tqdm shows counts/rate/ETA; JSONL progress
records elapsed seconds, remaining count and ETA. Per-case atomic checkpoints
include input arrays, source/config/environment fingerprint and payload hashes.
Resume validates all completed cases and skips them; corruption or changed
source/config/environment fails closed. Exercise partial run, full resume and
completed no-op resume, and preserve logs. Failed checks remain visible.
Partial CLI exit code is 3, successful completion is 0. Resume checks deterministic
input identity and re-evaluates the small mixture certificates; it does not repeat
Monte Carlo histories or timings. Hashes are not cryptographic signatures against
coordinated rewrites. Overflow/nonfinite intermediates must raise an error.

Do not promote an idea based on the synthetic outcomes. Decision criteria were
recorded before search: algebra/prior equivalence veto, identifiable estimand,
matched information, tractability and finite falsifier. Report initial ideas,
independent AI critiques, root adjudication, negative results and missing source
access. AI agents are not independent human peer review. Exactly one next
research action will be proposed after these gates.
