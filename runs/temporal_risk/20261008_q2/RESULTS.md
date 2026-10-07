# Q2 temporal risk — measured run

[Consolidated Vietnamese report](../../../docs/experiments/20261008_temporal_risk_q2.md).
Run COMPLETE: 768 origins, 32 independent path clusters, three coupled worlds,
eight overlapping origins, 16,896 estimate rows. Zero failure/null/warning.

- Primary AR Gaussian minus iid OIC conditional MSE: −.06356937982575;
  paired path-cluster 95% CI [−.07275199142226, −.05444518402212].
- Conditional MSE .0016351890 versus .0652045689, same full512 decision.
- HAC/block marginal comparisons do not establish improvement over iid OIC;
  EWMA post-shift comparison also has a CI containing zero. No new model selected.
- 90 tests passed in 2.43s. Development: 48 origins, 7.81207s case compute,
  factor-two pilot estimate 249.98622s, below 600s cap. Selected b=16 from ACF only.
- Pilot case compute 124.50284s; completion session 129.47971s (763 new/5 resumed).
- Verifier PASS in 83.03205s: 1,368 contrasts, 24,576 bootstrap replicate objectives,
  independent filter/HAC/quadrature/OLS checks; 229 protected files unchanged.
- Complete resume PASS in 5.98398s, 768 reused/0 new, 807 artifacts byte-identical.
- Config SHA256 `7a727b15fde89537be588343e98c6ab93bab0703965ced7f0336497aee1bd5a4`.
- Pilot fingerprint `21071c7f2acad52831980d4b88f7894114215357a081cb1c67a1747afa3b8d48`.

`pilot_initial_completion.json` retains the completion receipt before the final
resume. Progress JSONL and terminal tqdm logs preserve actual timing/ETA.
`development_selection.json` contains every ACF/cutoff and the selected block.
`pilot/summary.csv`, `paired.csv`, `shift_effect.csv` and case index are published.
Large estimate/diagnostic exports are gzip-compressed without changing content;
`compressed_exports.json` records original/compressed SHA256 and roundtrip checks.
Full local CSV/JSON originals remain intact. NPZ paths/full case payloads remain
local; compact Git evidence alone cannot resume or run array verification.

Conditional truth uses observed-history parameter oracle; latent-state diagnostic
is separate. Marginal correction is not claimed to forecast conditional next-step
risk. Bootstrap negative values and finite 16-replicate Monte Carlo uncertainty
are retained. Old Q0/Q1 results are read evidence, not new runs here.

Learned HMM, market/Q3, utility and new models are NOT_RUN. The sole proposed
next action is the development/frozen fresh Markov HMM baseline in the report.
