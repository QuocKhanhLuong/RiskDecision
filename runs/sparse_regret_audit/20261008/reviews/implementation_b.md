# Sparse-regret implementation review (independent B)

## Scope and evidence boundary

I read `sparse_regret/core.py`, `sparse_regret/rational.py`, `sparse_regret/run.py`, `sparse_regret/PROTOCOL.md`, `sparse_regret/config.json`, `tests/test_sparse_regret.py`, and the dependent `bank_regret` / `mixture_order` cores. This is a read-only source review. I did not run the test suite, start a frozen case, or reuse a benchmark result as an independently executed result in this report. The reported 29-test/frozen-run status remains parent-agent evidence, not a run by this reviewer.

## What is actually independently checked

`solve_lp` is a credible full-simplex finite-support value oracle. For action `i`, its variables satisfy `z <= line_{i,t}(q)` for every RU line of `i`; minimizing `line_{j,s}(q)-z` therefore maximizes `ES_i(q)-line_{j,s}(q)`. Enumerating every line of every competitor `j != i` gives

`max_q [ES_i(q) - min_j ES_j(q)]`,

because each competitor ES is the minimum of its RU lines. The sign is easy to get wrong, but the implementation's `c=[row,-1]` and the final negation implement the required `z-row` objective. Omitting `j=i` is valid because the bank includes action `i`, so its regret is nonnegative. The LP returns a vector of action regrets and per-action witnesses, rather than only the selected action.

The exact rational evaluator is a second representation of the finite-support RU/cell argument: it uses exact fractions, exact tail inequalities, and active-set enumeration. Its threshold conditions use strict mass above `t` and mass at least `t`, which correctly handles ties. Zero combined-probability scenario rows are removed in `FiniteMixture`; duplicate loss values remain harmless because thresholds are deduplicated and the rational tail inequalities still distinguish `>` from `>=`.

The edge solver and the union comparator are internally consistent with the finite theorem: every two-component edge is evaluated, while `local` evaluates each action at its own quantile crossings and `union` evaluates the stronger all-actions knot union. `FiniteMixture.es` handles fractional mass at the VaR atom, alpha equal to a cumulative mass, negative losses, duplicate losses, and component rows containing zeros. The `SimplexBank` and mixture constructors reject nonfinite/negative probabilities and require normalized component rows.

## Concrete limitations and blockers

1. **The rational oracle has no witness or full-vector gate.** `perform()` compares `rational['regrets']` with the local vector, but deliberately excludes rational output from `witness_error()` and `choices`. `enumerate_cells()` returns only per-action regret strings and one worst `q` string; it does not return a competitor witness, and the runner never recomputes the exact risks at that `q`. A bug that preserves the regret values while emitting a wrong rational witness, wrong actionwise vector ordering, or wrong competitor could therefore pass the rational gate. This is the clearest implementation-level evidence gap. It does not invalidate the independently computed scalar values, but it prevents calling the exact oracle a full vector/witness audit.

2. **The strongest comparator is only partly code-independent.** `union` shares `FiniteMixture`, `bank_hull`, RU line construction, and floating-point ES evaluation with `local`; it is a stronger knot set, not an independent implementation. `solve_lp` rebuilds RU lines and uses SciPy's LP solver, so the small `lp` cases are materially stronger. The configured scale cases do not run the LP oracle, and the rational cases cover only the configured alpha `.2` tasks. Thus the frozen protocol supports a finite computational audit, but not an all-size or all-alpha independent oracle claim.

3. **The implementation scope is narrower than the general theorem.** The code accepts a finite scenario matrix and enumerates finite RU thresholds. It does not implement arbitrary integrable component laws, the continuous support-two reduction, or the weighted J-level `J+1` support statement. Those can be presented as separate mathematical claims only if their proofs and assumptions are stated; they should not be described as implemented or empirically validated by this run. The current exact rational checker is one-level finite ES, not a J=2 spectral checker.

4. **`SimplexBank.risks` is tolerant at the boundary.** It permits q entries down to `-1e-10` and clips them before forming mixture masses. This is useful for HiGHS roundoff, but means a witness with a small negative coordinate is silently projected rather than rejected. The LP residual gate checks negative q, and the resulting errors are bounded by the configured tolerance, so this is not a known false safety result; it should be stated as numerical tolerance rather than exact witness validation.

5. **The checkpoint bytes are not deterministic across fresh executions.** `save_case()` sets gzip `mtime=0`, but the JSON body also contains a fresh UTC timestamp. Since files are never overwritten this does not undermine resume validation, which binds the body digest, freeze fingerprint, task, and regenerated input. It does mean that any prose calling the serialized payload itself byte-deterministic is too strong; the reproducibility guarantee is deterministic inputs/results plus accidental-corruption detection, not identical bytes from independent fresh saves.

6. **Corrupt freeze/layout state fails closed only by exception.** If `freeze.json` survives while `layout.json` is missing or malformed, `execute()` cannot reconstruct the layout and aborts rather than reporting a structured provenance failure. This is acceptable for a manually preserved frozen run, but should be treated as a resume robustness limitation. The normal checkpoint path is strong: it refuses unknown cases, refuses overwrites, verifies the case digest and fingerprint, and regenerates each expected input from the frozen seed recipe before resume.

## Degeneracy review

The finite numerical path is reasonably defensive for zero masses and ties. `FiniteMixture` removes only rows with zero probability in both components, preserves one-sided zero masses, and adds endpoint knots. Stable descending sorting plus fractional-tail accounting gives the right ES when several atoms share the VaR loss. The rational path uses exact arithmetic and active-set subsets, so degeneracy can produce repeated systems but should not change the value. The tests include duplicate components, translation, costs, alpha `1`, one-component banks, random zero probabilities, and duplicate scenarios; the inspected tests do not constitute a fresh execution here.

The remaining degeneracy concern is coverage rather than a demonstrated algebra error: there is no explicit exact test that combines a zero-mass row, a repeated VaR atom, alpha exactly equal to that atom's cumulative mass, and a tied action minimum while checking every rational witness. That combination is where a scalar-only rational gate would be least informative.

## Adjudication for a bounded computational note

The finite result is strong enough to support a narrowly scoped computational note about an exact action-local knot evaluator on two-component mixture edges, with a shared lower-envelope comparator, provided the note labels the full-simplex LP and rational results as validation evidence and reports the missing rational witness gate. The mathematical support-two theorem and its J-level extension are more general than this implementation; they are not established by the source inspection or by the finite one-level run alone.

The work is not enough to claim a new CVaR definition, a better forecaster, statistical coverage, or priority over generic RU/envelope and minimax-regret methods. Priority remains unresolved. Before treating the implementation as publication-ready, the minimum gate is to make the exact rational path emit and verify (i) the complete action-regret vector, (ii) exact worst-q feasibility and value, and (iii) a competitor attaining the bank minimum at each reported action witness; then rerun the frozen finite protocol with the same source/fingerprint discipline. If that gate passes, the remaining contribution is a bounded algorithmic specialization, not a novelty proof.

## Correction to the scalar-vector finding

On re-reading `run.perform()`, my earlier wording that the rational path lacked a “full-vector gate” was too broad. Its `errors` comprehension subtracts each answer's complete `regrets` vector from the local reference, including the rational answer. The original frozen runner still did not validate rational worst-q feasibility or competitor witnesses; the separate post-run verifier now reported by the root has checked those exact rational witness regrets and all numerical witnesses. The remaining distinction is therefore scalar-vector comparison in the runner versus witness validation in the post-run audit, not absence of rational vector comparison.
