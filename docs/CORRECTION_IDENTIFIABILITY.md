# What the current correction identifies

These are elementary diagnostic derivations, not claimed new theorems. They locate gaps between the implemented surrogate and the desired ES/decision guarantees.

## 1. A sufficient condition for exactly no correction

For fixed selected features, the objective is

`J(p) = KL(p || p0) + (1/(2 rho)) sum_j (|A_j' p - B_j| - delta)_+^2`.

If every selected residual at `p0` lies inside the band, `J(p0)=0`. Both terms are nonnegative; with strictly positive `p0`, KL is zero only at `p=p0`. Thus `p0` is the unique minimizer. If the condition holds for **all** bank directions initially, any eight-direction mining sequence remains at the prior. This is a sufficient exact arithmetic condition; a solver tolerance can create additional practically unchanged cases.

At a fixed threshold eta, the mixture also mechanically shrinks its discrepancy from its own empirical component:

`E_p0 h - E_cal h = (1-beta) (E_generated h - E_cal h)`.

For beta=.5 that residual is halved. The threshold and scale themselves change with beta, so this identity alone does not prove monotonic inactivity across independently rebuilt mixtures. It explains why a band can become easier to satisfy after support mixing, conditional on the chosen feature.

## 2. Fixed-threshold moments do not identify ES

For integrable loss distributions, write `F_Q(eta) = eta + E_Q[(L-eta)_+] / alpha`, with alpha=.05. ES is `min_eta F_Q(eta)`; the minimization and fractional treatment of atoms are established in [Rockafellar and Uryasev (2002), Theorem10](https://sites.math.washington.edu/~rtr/papers/rtr187-CVaR2.pdf).

Let `eta0` be the prior VaR and `g_Q = F_Q(eta0)-ES_Q >= 0`. For a reference P, empirical correction-block hinge mean b, and fitted Q, direct subtraction gives

`ES_Q - ES_P = (E_Q h-b)/alpha + (b-E_P h)/alpha + g_P-g_Q`.

The first term is what the fit approximately controls. The second is target sampling error. The last two capture using a fixed threshold away from the respective minimizing thresholds. On real data P is unknown; using an empirical calibration distribution makes the second term zero by construction and gives only an in-sample diagnostic.

**Counterexample:** shared support losses `[0,1,3,11]`; Q probabilities `[.90,.05,.05,0]`, P probabilities `[.99,0,0,.01]`. Q has VaR95=1. At eta0=1 both hinge means equal0.1. Nevertheless ES95(Q)=3 and ES95(P)=2.2. The example refutes identification from one matched hinge; it does not claim these particular probabilities are outputs of the penalized optimizer. The test suite checks the atom arithmetic independently through the existing risk evaluator.

Consequently, even perfect population matching of these fixed-threshold features does not give a general ES certificate. Eight fitted portfolio directions add a second gap: unmeasured directions may induce a different selected portfolio.

## 3. What would be sufficient, and what is absent

If `sup_(w,eta) |E_Q h_(w,eta)-E_P h_(w,eta)| <= epsilon` over every eligible portfolio and a threshold set containing both distributions' minimizing thresholds for every portfolio, then `sup_w |ES_Q(w)-ES_P(w)| <= epsilon/alpha`: take minima of two uniformly close functions. A portfolio minimizing ES_Q then has P-regret at most `2 epsilon/alpha`, by adding the two estimation errors and using optimality under Q. These are standard uniform-approximation arguments, not a novel guarantee here.

V2 does not establish that premise. Empirical target reuse, data-dependent thresholds/scales, adaptive feature mining, dependent observations and potentially missing future tail support all need treatment. A pointwise heuristic SE band cannot stand in for a simultaneous population bound. Adding more thresholds might address one approximation gap while worsening statistical error; it is not automatically a fix or a novel method.

The diagnostic measures these pieces separately before deciding whether any extension is justified. It cannot certify a future market winner.
