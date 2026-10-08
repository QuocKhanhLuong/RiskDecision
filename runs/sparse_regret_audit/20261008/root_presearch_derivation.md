# Root independent extension (derived before targeted edge-theorem search)

Candidate, NOT VALIDATED: for a finite action bank, finite supports, any finite
number R of component laws and q on their FULL mixture simplex, worst absolute
ES-difference regret has a maximizing q supported on at most two components.
For action i, on each own VaR region, ES_i is affine and benchmark min_j ES_j
is concave; the regret is convex there. Own VaR regions are intersections of
the simplex with consecutive nested cumulative-mass inequalities. If both
adjacent inequalities are tight, the threshold atom has zero mixture mass,
forcing support onto the face of components where that atom mass is zero.
At a region vertex there is only one independent cumulative-mass equality on
the remaining positive-support face, so support size is at most two. Thus all
simplex edges suffice, and the existing two-component bank hull algorithm can
be shared per edge. Fixed action costs only shift intercepts.

Possible extension (NOT PROVED): positive weighted sums of J distinct ES
levels require at most J+1 active components; active ambiguity moment constraints
can increase this support bound. Arbitrary probability boxes/trust regions may
invalidate edge sufficiency. Continuous-loss laws need a separate limit argument.

Prior-art risk: generic moment/extreme-point sparsity and known worst-CVaR
mixture results may already imply this. Need nearest-source mathematical audit,
independent proof/counterexample review and exact independent LP/enumeration
controls. No inference of priority from lack of a search hit; no new forecaster
or calibrated policy guarantee. Recorded before targeted support-two searches;
prior known RU/minimax-regret literature is an acknowledged anchor.
