# Results — 20261007_selection_baselines

Consolidated Vietnamese report:
[20261007_selection_risk_baselines.md](../../../docs/experiments/20261007_selection_risk_baselines.md).

VERIFIED: original ZIP checksums and 931 isolated imported files; Q0 320 stored
instances / 80 seed clusters; Q1 128 fresh iid instances / 64 seed clusters;
26 existing tests and 41 combined tests pass; separate numerical verifier passes.
Historical tracked/imported hashes are unchanged.

Q0 reproduces reported common-target means. Historical versus APTC on
penalty-selected portfolios: 14.2981% versus 14.4046% relative ES error;
paired difference +0.1064 percentage points, new 95% CI [−0.5270, +0.6555].
Exploratory reuse, not new held-out evidence.

Q1 primary split-minus-resubstitution squared relative frozen-objective error:
−0.0129103, CI [−0.0196134, −0.0066672]. Both estimators evaluate the same weight
and threshold trained on A (256 observations); independent B has 256 observations.
This does not establish an improved full-512 ES forecaster. APTC remains frozen
and provides no improvement claim.

REPORTED: original review CI and historical convergence statuses. Original review
ZIP unavailable in the inspected download locations; new cluster-bootstrap CI
uses its own preregistered RNG, not a claimed byte-for-byte review reproduction.

NOT_RUN: OIC correction, continuous CVaR benchmark, Q2/Q3 full matrices, new market
download, economic utility and model search. See the applicability note.

Artifacts:

- `preflight.json`, `seed_audit.json`, `import_receipt.json`, `source_receipt.json`.
- `q0/` and `pilot/`: freezes, raw/summary/paired CSVs, diagnostics, per-case hashes,
  progress/ETA and session receipts. Full command logs are in this directory.
- `micro/benchmark.json`: measured compute gate, excluded from pilot statistics.
- `combined_tests.log`, `combined_tests.xml`, `verification.json`.
- `resume_verification.json`: partial resume and 0-refit complete resume checked;
  Q0 CSV column order changes on first full resume, field values do not.
- `publication_manifest.json`: exact published evidence hashes.

Original imported snapshots, arrays and case checkpoints remain local. The
published receipts do not themselves support checkpoint resume without these
local files. Reproduction commands are in `selection_risk/README.md`.

PROPOSED next action: audit a separate continuous CVaR benchmark's curvature,
constraints and influence function before implementing OIC.
