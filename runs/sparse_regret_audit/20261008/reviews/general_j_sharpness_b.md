# General-J sharpness audit (independent B)

## Scope and claim

This is a newly derived mathematical construction, not a run and not a novelty or priority claim. It addresses whether the `J+1` support bound for a positive weighted sum of `J` ES levels can be sharp for every `J`. The answer is yes under an explicit hypothesis: the `J` tail levels are distinct and strictly ordered. Equal levels merge and should be counted once.

## Exact construction

Fix `J >= 1`, tail masses

`1 > alpha_1 > alpha_2 > ... > alpha_J > 0`,

and positive spectral weights `w_j` (normalizing their sum to one is optional). Let `N=J+2` and choose strictly increasing rational losses, for example `z_i=i-1` for `i=1,...,N`. Choose any rational `rho` with `0 < rho < alpha_J`, and define the strictly positive reference law

`p*_1 = 1-alpha_1`,

`p*_i = alpha_{i-1}-alpha_i` for `2 <= i <= J`,

`p*_{J+1}=rho`, `p*_{J+2}=alpha_J-rho`.

Then the mass above atom `z_j` under `p*` is exactly `alpha_j`. Thus, for level `alpha_j`, the two adjacent RU thresholds `z_j` and `z_{j+1}` are both active at `p*`; all other thresholds for that level are strictly inactive.

For `p` in the atom-probability simplex, write the two active RU affine forms as

`A_j(p) = z_j + alpha_j^{-1} sum_{i>j} p_i (z_i-z_j)`,

`B_j(p) = z_{j+1} + alpha_j^{-1} sum_{i>j+1} p_i (z_i-z_{j+1})`.

At `p*`, `A_j=B_j=ES_{alpha_j}(p*)`. Let `m_j` be the midpoint of their gradient vectors, and let `g=sum_j w_j m_j`. All these coefficients are rational when the levels and weights are rational.

Define

`D = {d : 1^T d=0 and g^T d=0}`.

The gradients are not constant across atoms. In particular, with `Delta=z_{J+2}-z_{J+1}>0`,

`g_{J+2}-g_{J+1}
 = Delta [ sum_{j=1}^{J-1} w_j/alpha_j + w_J/(2 alpha_J) ] > 0`.

The two constraints defining `D` are therefore independent, so `dim(D)=N-2=J`.

An explicit rational basis is useful for turning the construction into a bank of component laws. With `G_i=g_i`, for `k=1,...,J` set

`b_k = (G_{k+1}-G_N)e_1 + (G_N-G_1)e_{k+1} + (G_1-G_{k+1})e_N`.

Each `b_k` has zero sum and zero `g` inner product. The RU coefficients are nondecreasing in the ordered loss index and the top difference above is strict, so `G_N-G_1 != 0`; the distinct coordinate `k+1` makes `b_1,...,b_J` linearly independent. Set `v_k=b_k` for `k<=J` and `v_{J+1}=-sum_{k=1}^J b_k`. These `J+1` vectors are affinely independent, lie in `D`, and have zero barycenter.

Choose any sufficiently small positive rational `epsilon`, for example

`epsilon = 1 / (2 N max(1, max_{r,i}|v_{r,i}|))`.

The `J+1` component laws `p^(r)=p*+epsilon v_r` are then strictly positive probability vectors. Their equal-weight mixture is exactly `p*`, and affine independence makes that representation of `p*` unique with all `J+1` mixture weights positive.

## Strict spectral maximum proof

For a perturbation `d` with `1^T d=0`, the two active-line difference at level `j` is

`(A_j-B_j)(p*+d)
 = (z_{j+1}-z_j)/alpha_j * sum_{i>j} d_i`.

Since ES is the infimum of all RU lines, it is bounded above by the minimum of these two lines. Therefore

`S(p*+d) <= S(p*) + g^T d
             - sum_j (w_j/2) |(A_j-B_j)(p*+d)|`,

where `S=sum_j w_j ES_{alpha_j}`. On `D`, the linear term vanishes. If all displayed tail sums vanish, the equations for `j=J,...,1` force `d_2=...=d_J=0` and `d_{J+1}+d_{J+2}=0`; normalization then forces `d_1=0`. The only possible remaining direction is a transfer between the two highest atoms. Its `g` inner product is nonzero because `g_{J+2}-g_{J+1}>0`, so membership in `D` forces that transfer to vanish too. Hence every nonzero `d` in `D` has at least one nonzero kink term, and

`S(p*+d) < S(p*)`.

Thus `p*` is the unique maximizer of the spectral risk over the convex hull of the `J+1` component laws, and the maximizing mixture uses all `J+1` components. The argument is global over the hull; no local-neighborhood assumption is needed.

To turn this into an absolute regret fixture, add a second action with constant zero loss and zero cost. Use nonnegative `z_i` as above. The spectral risk of action A is nonnegative, so its regret against the zero action equals `S`; its unique worst mixture is the interior equal-weight mixture and requires support `J+1`.

## Adjudication

This establishes sharpness of the `J+1` upper bound for every number of distinct ES levels `J`, including an explicit finite rational construction whenever the levels, weights, `rho`, and `epsilon` are rational. The `J=2` fixture already saved in the audit is a concrete numeric instance; this derivation supplies the general family. The result is a support-sharpness statement for component-law mixtures, not a new ES definition, a statistical guarantee, or evidence of publication priority. Human review remains necessary.

## Corrections and a sharper uniform-level construction

Two formulas above require correction. First, for the adjacent thresholds `z_j` and `z_{j+1}`, the midpoint-gradient difference between the two highest atoms is full

`g_{J+2}-g_{J+1}
 = (z_{J+2}-z_{J+1}) sum_{j=1}^J w_j/alpha_j`,

not a half contribution at `j=J`. At the final kink, both adjacent RU coefficient vectors change by the same top-atom increment across those two atoms; averaging them therefore preserves the full increment. The strictness argument is unchanged.

Second, the displayed epsilon choice based on `1/N` is sufficient only for the uniform reference law. For the arbitrary-level construction, use

`epsilon < min_i p*_i / max(1, max_{r,i}|v_{r,i}|)`;

the rational choice `epsilon = min_i p*_i / (2 max(1, max_{r,i}|v_{r,i}|))` guarantees every component probability remains positive.

For an especially transparent exact family, take `z_k=k` for `k=0,...,J+1`, `p*_k=1/N`, and `alpha_j=(N-j)/N` for `j=1,...,J`. Encode each adjacent RU line on the simplex as a coefficient vector `a_j^-` at threshold `j-1` and `a_j^+` at threshold `j`, and put `h_j=a_j^-−a_j^+`. In these coordinates,

`h_j(k) = -1 + 1{k>=j}/alpha_j`.

The rows `(1,g,h_1,...,h_J)` are invertible: every `h_j` agrees on the last two atoms, while `g` differs there by the strictly positive full difference above; after removing `g`, successive coordinates identify the coefficients of the `h_j` rows. Hence one can choose rational vectors `v_j` satisfying

`1^T v_j=0`, `g^T v_j=0`, and `h_l^T v_j=delta_{lj}`.

Set `p^(j)=p*+epsilon v_j` for `j<=J` and `p^(J+1)=p*−epsilon sum_j v_j`. For a mixture q of these components, the perturbation from `p*` is

`epsilon sum_{j=1}^J (q_j-q_{J+1})v_j`,

so the kink coordinates are exactly `epsilon(q_j-q_{J+1})`. The supporting-line inequality gives the quantitative certificate

`S(p*)-S(P_q) >= (epsilon/2) sum_j w_j |q_j-q_{J+1}|`.

For equal weights `w_j=1/J`, any boundary mixture has `sum_j |q_j-q_{J+1}| >= 1/J` (the minimum is attained, for example, by `q_s=0` and all other `J` coordinates equal `1/J`). Thus every boundary mixture is below the unique interior optimum by at least `epsilon/(2J^2)`. This is an exact rational construction for rational `J`-level data and makes the all-`J+1` requirement quantitative.

## Final code review of the independent sharpness checker

I read `scripts/check_spectral_sharpness.py` and the saved receipts. The implementation matches the corrected construction. The uniform family uses `N=J+2`, `p*=1/N`, `alpha_j=(N-j)/N`, and equal positive weights. The unequal family uses positive ordered levels, positive unequal weights summing to one, and the arbitrary-level `p*` with its highest two atoms split one-third/two-thirds. The exact matrix rows are `[1,g,h_1,...,h_J]`; `linear_solve` produces dual vectors with zero normalization and g coordinates and with `h_l^T v_j=delta_lj`. The code asserts positivity, row normalization, barycentric recovery of `p*`, the full corrected top-coordinate identity `g[-1]-g[-2]=sum_j w_j/alpha_j`, and exact equality of the candidate value with `g^T p*`.

The epsilon calculation uses `min(pstar)/(2*max(1,max|v|))`, which is valid for both families and guarantees strictly positive component laws. Its analytic boundary lower bound, `epsilon*min(weights)/(2*J)`, follows from the boundary fact `sum_j |q_j-q_{J+1}| >= 1/J`; for equal weights this specializes to `epsilon/(2J^2)`.

The LP is an unrestricted spectral-risk control. It has one free epigraph variable per ES level and imposes `eta_j <= line_{j,t}^T q` for every RU threshold line, with no support, quantile-cell, or edge restriction. Positive weights make maximizing the eta variables recover the exact finite-support spectral risk. The full LP checks the exact candidate value and the uniform optimizer; each of the `J+1` additional LPs fixes one component weight to zero and checks the analytic boundary gap. These are numerical SciPy/HiGHS diagnostics of an exact rational construction, not a replacement for the proof or an exact rational LP certificate.

The recorded receipt reports 16 completed cases, 104 LP solves, and zero numerical warnings; the subsequent resume receipt reports all 16 cases resumed with the same frozen digest, 104 solves, and zero warnings. This confirms the configured controls ran as intended. I find no code-level blocker. The remaining scope statement is appropriate: this is an exploratory all-J sharpness diagnostic, separate from the frozen one-level package, and it establishes a mathematical construction rather than a novelty or priority claim.
