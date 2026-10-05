# Correction mechanism diagnosis — development only

Prepared on 2026-10-05 from clean parent `88b149bcea963c7609c068fd577fdfefccb0d34a`, branch `research/correction-mechanism-audit`. This is an explanatory study after the market final tests were opened. It is not fresh confirmation or a new method-selection contest. The old 931-file history, `local_market/`, market freeze and published held-out results stay byte-for-byte unchanged.

Machine contract: [`correction_diagnostic_v1.json`](../configs/correction_diagnostic_v1.json). Source/config hashes are captured in `configs/correction_diagnostic_freeze.json` before any diagnostic performance run. Unit tests use artificial inputs; preflight checks archive inputs, evaluator agreement and date eligibility only. This is an internal freeze, not external preregistration.

## Questions and fixed comparisons

1. Does the band leave the mixture unchanged? Count the exact sufficient no-update condition over all 285 directions, numerical no-change at ES tolerance 1e-10, total variation from prior, KL, and selector agreement.
2. Does adaptive direction mining add value? Compare frozen adaptive band with a random ordering of eight unique directions, using the same support, prior, thresholds, scales and solver. One random order per seed/window; no selection over random orders. Both execute eight solves; adaptive search itself has extra search cost, so this is a moment/solve budget match, not a wall-time equivalence.
3. Does fitting the original hinge identify ES? Decompose error into fitted moment residual, target sampling error, reference anchor gap and posterior anchor gap. Synthetic population quantities are evaluator-only. On ECB the reference is the **empirical training calibration block**, never a population or future true ES.

Methods: historical, historical+SE, pure mixture, band, point correction, random band and EWMA filtered historical. Band vs mixture and historical+SE remain primary scientific controls; point/random are mechanism ablations. No hyperparameter tuning or new candidate promotion.

## Inputs and evaluation

- ECB: every eligible development origin 2010–2015, 1,537 one-session forecasts; fixed bank285, seed2026, training512, one-observation gap, scenario seed7000+return index. Existing official data cache, quote conversion, availability convention and missing-date rules are reused. A hard guard rejects dates after2015. No market validation/test run.
- Synthetic: the 80 original validation instances (20 seeds × four families), now explicitly exposed development. Fit the **archived return arrays**, not regenerated replacements. Original bank and analytic true-ES vector are checked. Population parameters are reconstructed only for evaluation and checked against those archived vectors; Markov truth retains the original latent-state oracle limitation.
- Preflight found that NumPy multivariate-normal sampling can yield different arrays across platform linear algebra implementations even with the same seed (first Gaussian instance max difference6.21154). Therefore no cross-platform byte-identical scenario/risk-surface claim. Local GMM draws are refitted; report discrepancies from archived surfaces. Original files are untouched. Instrumentation equivalence is tested against the frozen implementation on identical local support.
- TrackA: identical equal-weight and past-only historical-SE reference portfolios for all estimators. ECB mean FZ0/pinball; synthetic mean relative absolute ES error. TrackB: each selector's own portfolio; ECB pooled ES95 and stability, synthetic population relative regret against the finite bank. No FZ0 ranking across different portfolios.
- Paired 5,000-replicate bootstrap: ECB moving blocks17 primary,5/20/60 sensitivity; synthetic seed clusters preserve all families. Pointwise exploratory intervals, approximate stationarity, no multiplicity adjustment. Report all years/families, not a favorable subset.
- Finite nonconvergence stays and is counted. Exceptions/nonfinite surfaces abort the entire diagnostic execution; no skipped losing dates or implicit fallback. Content-bound per-window resume; all local rows retain training hashes and dates.

## Boundaries and acceptance

No new market download, neural model, yield-curve study, new final-test claim, trading return or Sharpe. All original market terms/vintage limitations remain. Public outputs are aggregate diagnostics and provenance only; per-date market rows/cache stay ignored.

Accept execution only after same-input implementation tests, complete counts, original-target recomputation, common-target checks, CSV/window identity, score recomputation and decomposition identities pass. These coordinator checks do not constitute independent peer review. Never promote a method from this explanatory study.

Independent Orca audit was attempted again: Run `run_eaedc9ba2825`, Task `task_d5238cc99f24`, Dispatch `ctx_5e64e2b69cbe`. Exact-workspace start failed at `agent_readiness: timeout`; the receipt explicitly says the Task never ran. Its terminal was released and no reclaimable worker remained. No non-Orca agent substituted; independent review remains NOT RUN.
