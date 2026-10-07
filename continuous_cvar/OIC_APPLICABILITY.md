# Continuous CVaR / OIC applicability — pre-implementation decision

Scope: a new numerical benchmark, separate from bank285 and all historical
results. **Conditional GO for a documented KKT-derived OIC implementation on a
fixed smooth objective.** NOT a reproduction of the authors' code, an OIC result
for the unsmoothed empirical LP, or a proved finite-sample guarantee.

## VERIFIED_SOURCE

Primary source: Iyengar, Lam and Wang, [arXiv:2306.10081v4](https://arxiv.org/html/2306.10081v4),
21 July 2025, preprint. Re-read Definition 2.7/2.8, Theorem 2.6/2.9,
Example 6.4 and Appendix 7.3.3. The target is expected optimized decision cost
under iid sampling. An estimated influence function supplies the first-order
optimism correction. Smoothness, curvature, constraint recovery and solver
accuracy matter. This is not a calibrated VaR/ES forecast pair.

The displayed constrained formulas deserve care: Theorem 2.6 discusses the
pseudoinverse of projected curvature, while Definition 2.8 and Appendix 7.3.3
display a projection around a Hessian pseudoinverse. These are generally
different matrices. We do not silently identify them. The implementation below
uses the local derivative of the constrained estimating equations, tested by
perturbing sample probabilities.

## DERIVED HERE — exact objective and local influence function

Let `theta=(w,v)`, `alpha=.05`, and

`h_tau(theta;x) = v + tau/alpha * log(1+exp((-x.w-v)/tau))`.

Every fitting method uses the same feasible set: `sum(w)=1`, `0<=w<=.5`,
`-50<=v<=50`. The broad, fixed threshold bounds also permit a convex first-order
optimality-gap certificate; any active threshold bound is flagged. Units are the
unchanged synthetic return units. Primary `tau=.1`; sensitivity `.05,.2`, all
declared before outcomes. These are three distinct fixed smoothed targets, not
bandwidths selected by test. No statement is made about a vanishing-tau limit.

For `a_i=(-x_i,-1)` and `s_i=sigmoid(a_i.theta/tau)`:

`g_i = e_v + s_i*a_i/alpha`,
`H = mean[s_i*(1-s_i)/(alpha*tau) * a_i*a_i.T]`.

Let C collect the budget equality and active linear bound normals; let N be an
orthonormal basis of its null space. Differentiating the KKT equations for
contamination of the empirical distribution by sample i gives

`IF_i = -N * inverse(N.T*H*N) * N.T*(g_i-mean(g))`.

At the constrained optimum `N.T*mean(g)=0`. The correction we implement is

`c = mean[(g_i*N) * inverse(N.T*H*N) * (N.T*g_i)] / n`,
`OIC_KKT = mean[h_tau] + c`.

There is no arbitrary SE penalty, ridge, clipped correction or zero-Hessian
inversion. Centering is immaterial at exact stationarity; projected score means
are logged. H is the Lagrangian Hessian here because all constraints are linear.
The unconstrained inverse bracketed by projections is retained only as a
diagnostic discrepancy, never substituted for the KKT derivative.

## ASSUMED and numerically checked

Fixed positive tau makes the objective smooth and convex. Gaussian and crash
Gaussian-mixture draws are iid conditional on seed-defined parameters, have
finite moments and full-dimensional density. Their population curvature is
positive on feasible directions. At a stable active set with strict complementarity,
local influence differentiation is justified. Population active-set recovery
and the asymptotic theorem are not established by a finite pilot.

Before the pilot: finite-difference gradients/Hessians, active-set contamination
response, nonnegative correction and solver equivalence tests. Per fit: feasibility,
stationarity, dual signs, complementarity, tangent eigenvalues/condition number,
constraint rank, positive-multiplier margin, and convex objective-gap bound.
Weak-active-set cases stay in the output with flags; invalid numerical corrections
are null and make the primary analysis INCOMPLETE rather than being dropped.

The numerical gate uses no population parameters. An exact empirical CVaR LP is
a solver/unsmoothed decision reference on the same feasible set; it gets **no OIC**.
Independent B evaluates the smooth objective at theta_A locked on A. Full-512
OIC/raw comparisons share theta_512; half-256 OIC/raw/independent comparisons share
theta_A (and separately theta_B). They are not interchangeable estimands.

## NOT_RUN / excluded claims

No OIC for bank285 or the raw hinge LP; no coherent adjusted VaR/ES pair;
no continuous APTC variant or continuous SE-penalty redesign; no comparison of
regret between continuous and bank285 spaces; no temporal/market/utility claim.
Frozen bank285 baseline comparisons remain in the previous run. This run's
purpose is to validate the continuous correction mechanism and its limitations.
