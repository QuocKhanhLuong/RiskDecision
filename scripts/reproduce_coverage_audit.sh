#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
.venv/bin/python -m pytest -q tests quant_research_v2/tests
.venv/bin/python -m coverage_audit.run --workers 2
.venv/bin/python -m coverage_audit.analyze
.venv/bin/python scripts/build_coverage_report.py
.venv/bin/python scripts/verify_coverage_audit.py
