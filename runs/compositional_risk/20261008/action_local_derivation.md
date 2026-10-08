# Post-generation derivation: action-local regret witnesses

Derived by root before stochastic experiment/code; reviewer B independently
checked the reduction. A review error about minimum-of-concave functions was
caught by root and corrected append-only; reviewer consensus is not a proof.

Fixed finite actions i=1,...,M, finite loss supports, upper-tail probability
alpha, two fixed component laws, q in a compact interval. Add a fixed action
cost c_i, e.g. a one-step cost from the same incumbent. Let

    f_i(q) = ES_alpha(L_i; (1-q)P0+qP1) + c_i
           = min_t [t+c_i + ((1-q)E0[(L_i-t)+]+q E1[(L_i-t)+])/alpha].

For finite support it suffices to take t from the support. All threshold costs
are affine in q; f_i is concave piecewise affine. The same-world best action is

    g(q) = min_i f_i(q) = min_{i,t} affine_line_{i,t}(q).

It is concave. More generally, hypograph(min_i f_i) is the intersection of
convex hypographs, so minimum of concave functions on a common convex domain
is concave. A single lower hull over all lines represents g and carries the
identity of a minimizing action/threshold at every q.

On an interval between adjacent knots of action i's OWN f_i, f_i is affine.
Thus f_i-g is convex there and cannot exceed the larger endpoint value.
Therefore

    max_q [f_i(q)-g(q)] = max_{q in own_knots_i plus endpoints} [f_i(q)-g(q)].

Competitor/global-envelope knots need not be evaluated for action i. Quantile
crossing points form a complete (possibly redundant) own-knot set. If K is
the total count of support thresholds across the bank, constructing the
global line hull and all own knots and querying g at those knots costs
O(K log K) time/O(K) memory, including sorting/prefix sums/binary-search ES.
The minimax-regret action is then the argmin of these M maxima. A generic
global-hull/all-union-knots comparator can use O(M K log K) work; exact pairwise
contrasts also repeat work unnecessarily. These are comparison bounds, not a
claim that every existing minimax-regret solver has that cost.

Across finitely many fitted-component worlds k, repeat once per world and
take max_k for each action. Complexity sums over worlds. Guarantees are exact
for the supplied finite world set and q intervals (up to numerical error),
not statistical coverage of an unknown true conditional distribution.
Same incumbent costs must appear in both chosen and benchmark action costs.

The primitives (RU, lower hulls, minimax regret, fixed switching costs) are
known. Candidate contribution: the action-local witness reduction composed
with a shared bank hull, an exact implementable bound and a learned-world
policy audit. Priority/novelty is NOT ESTABLISHED by this derivation alone.
Need stronger-than-pairwise comparator, complete-knot/tie tests, and prospective
policy ablations. No claim of a new forecaster, statistical coverage, dynamic
multi-period guarantee, or general simplex algorithm.
