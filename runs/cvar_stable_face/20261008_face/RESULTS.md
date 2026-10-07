# Stable-face CVaR: actual run, 2026-10-08 Asia/Ho_Chi_Minh

[Consolidated report](../../../docs/experiments/20261008_cvar_stable_face.md).
Fresh pilot COMPLETE: 128 cases / 64 paired seed clusters, 1,152 smooth fits,
3,200 rows, zero failures/null OIC. No vertex targets occurred in this fresh
pilot. Vertex repair evidence remains development/seen-array regression.

- Primary full512/tau=.1 OIC-minus-raw MSE: −.0037113409973,
  bootstrap 95% CI [−.0059241825178, −.0014362584737].
- A256 OIC-minus-independent MSE: +.0078836704830,
  secondary CI [+.0008844209706, +.0158174574045]. B256 CI includes zero.
- Config SHA256: `82c5718f58f8d48ee2a14d344bbd6bb9932b34338daa2af53f1dcfa57ff9256c`.
- Pilot fingerprint: `2e8a5e59e51284fcc3b52b1a60822c96f815e85caf80dfa887ddd138236a050e`.
- Tests: 76 passed / 1.72s. Earlier unscoped collection failure retained separately.
- Seen-array audit: 0.77814s; 14 old nulls certified, no historical risk aggregation.
- Development: 0.15747s case compute, 20.15629s predicted pilot including ×2 margin.
- Fresh pilot: 9.08182s case compute; partial session 0.27100s (3 new), completion
  session 10.18858s (125 new / 3 resumed). Compute cap was 600s.
- Independent final verifier: PASS / 12.49640s, all 90 paired contrasts reproduced.
- Complete resume: 1.94711s, 128 reused / 0 new, 262 artifacts byte-identical.

`pilot_initial_completion.json` retains the original completion receipt before
the zero-refit resume. `face_audit_progress.jsonl`, development/pilot progress,
tqdm terminal logs and timing receipts are included. `vertex_lp_verification.json`
is explicitly post-run verification of old cases, not fresh vertex evidence.

All 176 previously tracked files retain their hashes. Compact publication
contains CSVs, complete diagnostics, frozen provenance and verification logs;
NPZ/full checkpoint payloads remain local. A compact clone alone cannot resume
the measured run or execute array verifiers without those payloads.

Sources/prior reports are read evidence; temporal/market/utility/new-model and
weak-face/nonsmooth OIC remain NOT_RUN. The one proposed next action is Q2
development and frozen temporal evaluation, as specified in the report.
