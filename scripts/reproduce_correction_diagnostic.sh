#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
.venv/bin/python -m pytest -q tests quant_research_v2/tests
.venv/bin/python -m correction_audit.run --source synthetic --out runs/correction_diagnostic_v1/synthetic --workers 2
.venv/bin/python -m correction_audit.analyze --run runs/correction_diagnostic_v1/synthetic --out results/correction_diagnostic_v1/synthetic
.venv/bin/python -m correction_audit.run --source ecb --out runs/correction_diagnostic_v1/ecb --workers 2
.venv/bin/python -m correction_audit.analyze --run runs/correction_diagnostic_v1/ecb --out results/correction_diagnostic_v1/ecb
.venv/bin/python scripts/build_correction_report.py
.venv/bin/python scripts/verify_correction_artifacts.py
