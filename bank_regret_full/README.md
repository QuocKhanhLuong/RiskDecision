# Full synthetic validation of the frozen bank-regret methods

This wrapper keeps `bank_regret/` and its published pilot immutable. It expands
the same methods to24 independent public dictionaries/banks, 64 histories per
bank and per family (3,072 histories), 240 computational cases, and30 separate
peak-RSS measurements. It does not add a model, tune a method, or establish novelty.

See [prospective protocol](PROTOCOL.md) and
[full report](../docs/experiments/20261008_compositional_risk_full.md).
The policy inference unit is the bank cluster (n=24); portfolio/history counts
are not a substitute for independent environment replication.

Run from repository root using a **new output directory**:

```bash
rtk proxy env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 .venv/bin/python -m bank_regret_full.run preflight --out runs/compositional_risk_full/reproduction
rtk proxy env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 .venv/bin/python -m bank_regret_full.run run --out runs/compositional_risk_full/reproduction --max-new-cases 5
# Intentional partial exit 3; completed run exits 0.
rtk proxy env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 .venv/bin/python -m bank_regret_full.run run --out runs/compositional_risk_full/reproduction
rtk proxy env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 .venv/bin/python -m bank_regret_full.run run --out runs/compositional_risk_full/reproduction
```

Preflight freezes all imported source/config/environment and projects runtime;
it refuses a projection above one hour. It uses separate development seeds and
does not expose or select on development policy effectiveness. Each stage has
tqdm/ETA and JSONL progress. Benchmark timing and memory stages run serially;
four worker processes execute policy histories only after timing stages finish.
Multiprocessing is not independent review. `outer_wall_seconds` includes resume
validation; sum of concurrent case seconds is not elapsed wall time.

Checkpoints are individually gzip-compressed JSON with payload hashes and exact
task identity. The timestamp-free gzip wrapper is deterministic for unchanged
payloads. No-op resume verifies freeze/layout, payload and decision-lock hashes;
it does not refit every policy. The separate verification command regenerates
all input recipes/truth and refits a fixed subset of96 histories with LP checks.

For the published run, including saved partial/full checkpoint hash maps:

```bash
rtk proxy env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 .venv/bin/python -m bank_regret_full.verify --out runs/compositional_risk_full/20261008
```

Verification reuses saved cases and is not independent scientific data. Never
rerun into published output files to change their timings; use a fresh directory.
Python binary/platform/library changes also require a fresh freeze. Source code
and the report identify finite-stress coverage limits and synthetic-only scope.
