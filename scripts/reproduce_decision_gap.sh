#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
.venv/bin/python -m pytest -q
.venv/bin/python -m decision_gap_audit.run --workers 2
.venv/bin/python scripts/build_decision_gap_report.py
.venv/bin/python scripts/verify_decision_gap.py
