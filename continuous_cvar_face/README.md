# Stable-face CVaR continuation

Additive continuation of `continuous_cvar/`. The original optimizer, configs,
reports and measured runs are unchanged. See the
[pre-implementation derivation](APPLICABILITY.md) and
[consolidated report](../docs/experiments/20261008_cvar_stable_face.md).

`model.py` certifies the capped-simplex minimal face using positive bound
gradient margins, avoiding the assumption that a least-squares multiplier vector
is unique. The existing reduced-Hessian correction is used only on a strictly
stable face. Weak/zero margins, bad curvature, threshold bounds, infeasibility
and inaccurate optimization remain rejection conditions. The returned decision
and raw objective are identical to the frozen original fitter.

`audit.py` checks all 128 previously seen array files without population risk
comparison. `run.py` freezes code/config, checks local seed use, requires that
audit, enforces the development compute gate, and preserves all pilot failures.
It provides atomic checkpoints, hashes, locks, tqdm/ETA and progress JSONL.

Measured test command (explicit directories avoid collecting archived copies):

```bash
rtk proxy .venv/bin/python -m pytest -q tests quant_research_v2/tests
```

The run sequence used, after the development tests passed:

```bash
rtk proxy .venv/bin/python -m continuous_cvar_face.run preflight --out runs/cvar_stable_face/20261008_face
rtk proxy .venv/bin/python -m continuous_cvar_face.audit --out runs/cvar_stable_face/20261008_face
rtk proxy .venv/bin/python -m continuous_cvar_face.run development --out runs/cvar_stable_face/20261008_face
rtk proxy .venv/bin/python -m continuous_cvar_face.run pilot --out runs/cvar_stable_face/20261008_face --max-new-cases 3
rtk proxy .venv/bin/python -m continuous_cvar_face.run pilot --out runs/cvar_stable_face/20261008_face
rtk proxy .venv/bin/python scripts/verify_cvar_stable_face.py --out runs/cvar_stable_face/20261008_face
rtk proxy .venv/bin/python scripts/verify_cvar_face_vertices.py --out runs/cvar_stable_face/20261008_face
```

Repeating `pilot` resumes the measured local tree; a completed resume reuses
all 128 cases and preserves CSV/array/checkpoint bytes. A changed code/config/
environment/input fingerprint is rejected. Saved failures stay in the output.
Preflight rejects already observed seeds except explicitly declared matching
software replay. All published seeds are now seen, even on a clean machine.
Do not rerun them as fresh confirmation or modify the measured config.

Compact publication contains all estimates, diagnostics, source/config hashes,
tests, progress and verification receipts. Full NPZ and case checkpoint payloads
remain local. A compact clone cannot resume the measured run or run the
array-based verifiers without those payloads. The regression audit also needs
the old `runs/continuous_cvar/20261007_oic_v3/pilot/arrays` directory. Numerical
tests with constructed/generated fixtures can run without that directory.

The new iid pilot's primary is COMPLETE and favors OIC over in-sample raw at
the same decision. It contains **zero vertex cases**, so it does not measure
incremental benefit from the vertex repair. That repair's evidence is limited
to the derivation, development perturbations and seen-array regression.
The estimator evaluates a fixed smoothed objective, not a coherent corrected
VaR/ES pair. No method novelty or market performance is established.
