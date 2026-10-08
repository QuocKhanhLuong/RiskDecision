# Full synthetic run index, 2026-10-08

Narrative: [consolidated report](../../../docs/experiments/20261008_compositional_risk_full.md).
Prospective design: [protocol](../../../bank_regret_full/PROTOCOL.md).

`start_receipt.json` records scope, branch, main/base SHAs and755 protected files.
`frozen/freeze.json` binds source/config/environment, and `layout.json` enumerates
the exact3342 tasks:240 computational cases,30 memory measurements on reused
computational inputs, and3072 new policy histories across24 independent banks.

`frozen/preflight.json` records the compute-only gate and separate development
seeds. `frozen/cases/*.json.gz` preserves inputs/recipes, learned worlds, locked
choices, errors, timings, warnings and payload hashes. `progress.jsonl` records
stage progress/ETA; `invocations.jsonl` separates resumed/new cases and actual
wall time. Full/no-op summary and byte-hash maps demonstrate resume immutability.

`tests_collection_error.*` preserves the initial collection failure caused by
same-named modules in a historical snapshot. No snapshot files were removed or
edited. `tests_main_only.*` is an intermediate127-test pass. `tests.*` records
the final153-test run of explicit active suites `tests quant_research_v2/tests`.
These counts are not added together. Prototype software tests used a separate
namespace before the final v2 assessment namespace was frozen.

`verification.json` and `verification.log` record all-input provenance checking,
summary recomputation, the fixed96-history deep-refit subset and independent LP
cross-checks. They reuse the assessment cases and do not add scientific samples.
`benchmark_summary.csv`, `memory_summary.csv`, `policy_summary.csv`,
`paired_cluster_contrasts.csv` and `bank_effects.csv` export the complete frozen
summary via `scripts/export_bank_regret_full.py`; no cases are filtered.
`publication_manifest.json` hashes the allowlisted new package, excluding itself
and runtime lock/cache files. No new raw market data or credentials are included.
