# Q2 extension: learned Gaussian HMM on fresh Markov paths

Status: prospective protocol, written before implementation/development/pilot.
Decision: the user approved continuing the HMM control proposed in Q2. The old
Q0/Q1/Q2 measurements remain immutable. This is a standard statistical baseline,
not a new method or a market study. Base: `3203bb3`.

## Question, information and unit

Can a two-state Gaussian HMM fitted on observed past reduce conditional next-step
objective error relative to Gaussian iid and EWMA on the same locked portfolio?
Two states/full covariance are declared in advance and match the stationary
simulation family: this is a favorable specified-family check, not evidence of
general regime discovery. The transition-shift world violates time homogeneity.

Use the Q2 DGP unchanged, restricted to Markov stationary and transition shift.
32 fresh path seeds 2026110000 through 2026110031; development 2026109998/99.
Audit locally available records before generating pilot paths. Origins
512,576,640,704,768,832,896,960; 512 observed returns [t-512,t); predict X_t.
Stride 64 is not holding horizon. Coupled worlds use the same innovations and
state uniforms, and coincide before change index 768. Only path seeds are
independent inference units; worlds, overlapping origins, restarts and portfolios
are not extra replicates. The bounded 32-path pilot is not a powered universal
superiority study; no sample-size extension after viewing outcomes.

Models receive only the past matrix and frozen fitting settings. They never
receive true state, DGP parameters, world name, change date, future observations
or population risks. The observed-window conditional parameter oracle from Q2
is evaluation truth; it knows parameters/change schedule, so is not a learned
baseline. Hidden-last-state truth is a separate diagnostic.

## Locked fitting and controls

Use hmmlearn 0.3.3 GaussianHMM, two states, unrestricted full covariance,
Baum-Welch EM, scaling implementation, max 200 iterations, total log-likelihood
tolerance 1e-4. Standardize each feature using this past window only. Three
deterministic starts split standardized squared radius at quantiles .50/.70/.85;
each initializes means/covariances from its two groups, start probabilities .5,
transition diagonal .90. Initial covariance gets 1e-3 identity only. All start,
transition, means and covariance parameters are learned. No emission/covariance
tying or true parameters. Flat transition/start priors 1, zero mean/covariance
prior weights and covariance prior 0 give the ordinary ML EM update. This can
have local optima/degeneracy; no global-optimum guarantee.

Select the finite, numerically admissible restart with highest training log
likelihood only. A restart is admissible if probabilities normalize, covariance
minimum eigenvalue in standardized space exceeds 1e-8, and likelihood decreases
are no worse than 1e-6. Record every start, iteration history, warning, occupancy,
eigenvalue and selected index. Explicit convergence requires last observed
likelihood increment in [-1e-6,1e-4]; hitting the cap alone is not convergence.
Append the score of final post-M-step parameters to the recorded history.
Keep selected finite capped fits as flagged estimates; do not silently replace
them with a different model. No admissible restart gives a null HMM cell.

Next mixture weights are the final filtered posterior times learned transition,
not the final posterior itself or a decoded state. Last posterior obtained from
score_samples on the permitted window contains no observation beyond t-1.
Transform emission means/covariances back to return units before risk evaluation.

Policies: full512 historical smooth CVaR optimizer and equal512 fixed weights
with fitted threshold, using unchanged Q1/Q2 alpha=.05, tau=.1, cap=.5.
Every forecaster scores exactly the same (w,v) within a policy.
Controls: raw, iid OIC, Gaussian iid, AR Gaussian, EWMA Gaussian lambda=.94.
The HMM stationary-mixture control uses the same fitted emissions/transition
with invariant state probabilities instead of the final filtered probabilities.
It isolates use of the last state posterior within the fitted model; it is not
a separately optimized iid mixture or proof of causal attribution.
No new HAC/bootstrap refits or old scientific reruns are needed for this question.

## Outcomes and frozen contrasts

Target: expected next-step **smoothed objective** at locked (w,v), not an adjusted
VaR/ES pair. Relative error is estimate/conditional_objective - 1. Primary:
stationary Markov, full512, all eight origins, HMM filtered minus Gaussian iid
**squared relative error**. Average origins within each path first; paired
bootstrap of 32 paths, 10,000 draws, fixed bootstrap seed.

Report HMM vs EWMA and its stationary-mixture control for both worlds, both
policies and before/after/all periods as unadjusted secondary comparisons.
Report every predeclared method, marginal-objective error, latent-information
gap and all convergence failures. Any missing/null required cell makes that
contrast INCOMPLETE: no complete-case dropping. Ordinary unadjusted CIs do not
license selecting the best post-test model. A negative primary CI supports this
baseline in this synthetic setting only. A CI crossing zero or worse result is
retained. A finite result with capped selected fits must carry that limitation.

## Development gate, freeze, resume and limits

Development runs both worlds/all origins on two disjoint seeds. It checks
numerical validity, convergence, information contracts and timing, not tunes
forecast errors. There is no hyperparameter search: settings above are fixed.
Pilot opens only if all selected development fits converge, no case fails,
and extrapolated case time with factor-two margin is <=600 seconds. Otherwise
report pilot NOT_RUN; any revision needs a separate prospectively named run.
Snapshot code, dependencies, config, protocol, audit and benchmark hashes.
Atomic per-origin checkpoints, source/config/input/environment rejection on
resume, tqdm/ETA, warnings, actual timing and progress JSONL live under runs/.
Test partial then complete resume without rerunning completed fits; compare
checkpoint/result hashes. Publish compact lossless exports and document any
local-only arrays/checkpoints. Preserve all previously tracked file bytes.

Independent numerical verification uses a separately coded log-space filter,
brute-force short-sequence tests, direct univariate quadrature, training-score
selection checks and recomputation of path-cluster CIs. This is software audit,
not independent subagent/peer review. If a scientific bug is found after opening
pilot outcomes, preserve the run as invalid and do not silently repair/retest.

## Source applicability (READ; not novelty)

Official [hmmlearn tutorial](https://hmmlearn.readthedocs.io/en/stable/tutorial.html)
documents custom initialization, EM local optima and training-score restart
selection. The [GaussianHMM API](https://hmmlearn.readthedocs.io/en/stable/api.html#hmmlearn.hmm.GaussianHMM)
documents full covariance and posterior scoring. Installed 0.3.3 source was read:
the monitor treats the iteration cap as converged, hence our separate criterion;
final parameters are updated after each monitored likelihood. The full covariance
M-step was checked for the zero-prior ML settings. These sources justify the
implementation, not prediction guarantees under structural change.

NOT_RUN here: market/Q3, utility, neural/APTC variants, state-count selection,
adaptive/window sweeps, online change detection, calibrated joint VaR/ES scores,
continuous conditional-optimum regret and independent peer review.
