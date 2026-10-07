# Continuous CVaR / OIC — measured run

Authoritative narrative: [consolidated report](../../../docs/experiments/20261007_continuous_cvar_oic.md).
Runner COMPLETE; registered overall primary **INCOMPLETE**, four null OIC
corrections at full512/tau=.1. These cases remain in the evidence.

- 128 synthetic cases, 64 paired seed clusters; 1,152 smooth fits; 3,200 rows.
- Explicit software replay of v2 after evaluator-only repair; zero additional
  independent cases. Config SHA256
  `813a056840ffb8536aca3f40099b4773327329ca86be5f85f79f11018026d688`.
- Pilot fingerprint
  `76f72ef93ad9d1806839f023e220b97fdc8c3edba5070b15870d19f94ebc91ce`.
- 57 tests passed in 1.43s. Development case compute 0.14008s; predicted pilot
  17.93003s including ×2 margin. Pilot case compute 8.62379s; completion session
  (125 new / 3 resumed) 9.60180s. Verifier 12.48562s. Complete resume check 2.06614s.
- Numerical verifier PASS: 112 protected files unchanged, 124 prior completed
  case arrays identical, augmented KKT and direct quadrature cross-checks.
- Resume PASS: 128 reused, 0 new, 262 artifacts byte-identical. Partial resume
  also executed, 3 then 125 cases. `progress.jsonl` retains timestamps and ETA.
- 0 runtime warnings; all smooth optimizers success. There are 14 retained null
  OIC corrections across taus/policies; see `gate_summary.json`.

Gaussian full512 primary-tau OIC-minus-raw MSE is −.000836925, 95% CI
[−.001633174, +.000009925], a secondary comparison containing zero.
A256 independent has point MSE .0160573 versus OIC .0275402; paired difference
CI includes zero. No model or tau was selected from these results.

`pilot/estimates.csv`, `summary.csv`, `paired.csv`, `diagnostics.json` and
`case_index.csv` contain measured values; null primary estimates remain blank.
`pilot_initial_completion.json` preserves timing before the complete-resume
check overwrote the ordinary session receipt. Raw HTML, NPZ arrays and full case
payloads remain local; compact publication cannot itself resume without them.
`publication_manifest.json` lists exact published artifacts and hashes.

Earlier attempt logs/failure payloads are retained in sibling run directories.
Unsmoothed/discrete OIC, active-set remedy, Q2/Q3, utility and new models:
**NOT_RUN**. Proposed next action is the development-only degeneracy audit
specified in the consolidated report.
