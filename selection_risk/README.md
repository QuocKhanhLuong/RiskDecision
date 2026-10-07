# Selection-risk baseline run

This module adds Q0 crossed evaluation and the Q1 independent-split baseline.
Historical package source, configurations and measured outputs are read-only.
OIC is **NOT_RUN**; see [applicability gate](OIC_APPLICABILITY.md).

From the repository root, using Python 3.13 and the pinned dependencies:

```bash
rtk proxy uv pip install --python .venv/bin/python -r selection_risk/requirements.txt
rtk proxy mkdir -p runs/selection_risk/NEW_RUN/historical_snapshot
rtk proxy cp archives_manifest.json runs/selection_risk/NEW_RUN/historical_snapshot/
rtk proxy .venv/bin/python scripts/import_chat_archives.py \
  --archive-dir /Users/alvinluong/Downloads/RiskDecision_Local_Import_Bundle \
  --repo-root runs/selection_risk/NEW_RUN/historical_snapshot
rtk proxy .venv/bin/python -m pytest -q tests quant_research_v2/tests
rtk proxy .venv/bin/python -m selection_risk.run preflight \
  --out runs/selection_risk/NEW_RUN \
  --archive-dir /Users/alvinluong/Downloads/RiskDecision_Local_Import_Bundle
rtk proxy .venv/bin/python -m selection_risk.run q0 --out runs/selection_risk/NEW_RUN
rtk proxy .venv/bin/python -m selection_risk.run micro --out runs/selection_risk/NEW_RUN
rtk proxy .venv/bin/python -m selection_risk.run pilot --out runs/selection_risk/NEW_RUN
rtk proxy .venv/bin/python scripts/verify_selection_risk.py --out runs/selection_risk/NEW_RUN
```

These commands reproduce the registered seeds, not a new unseen assessment.
For a genuinely new study, register new seeds/configuration before outcomes.
The documented original seeds are now seen and must not support method selection.

Repeat a stage with its existing `--out` to resume. A complete checkpoint skips
fitting; `--max-new-cases 3` demonstrates an interrupted bounded session. Each
case is atomic, hashed and checked against code/config/input/environment identity;
parallel writers to the same stage are rejected. Preserve the entire local run,
including `cases/` and `arrays/`, to resume. The published compact receipts alone
are insufficient to resume an absent checkpoint. Missing or corrupt arrays fail
closed. Q0 missing archives fail rather than substituting aggregates or refitting.

Progress and elapsed/ETA events are in `<stage>/progress.jsonl`; tqdm writes to
stderr. Capture both streams in a log, as the completed run does. A new run freezes
its identity before its first case. Microbenchmark timing gates the 128-instance
pilot; no interim outcome stopping or tuning occurs. On the first full Q0 resume,
CSV column order can change because checkpoint keys are serialized in sorted
order. Read columns by name; the verified record values/order are unchanged.

`core.py` isolates `fit(past)`, `risk(weights)` and past-only selection from
population evaluation. Historical and penalty selectors share exactly the same
forecast surface. Stored surfaces support exact bank queries only. Every method
must supply the same complete finite bank; no method-specific target masks.

The split comparison locks weight **and threshold** on 256 observations and
evaluates the hinge objective on the other 256. It is not an OIC implementation,
not a full-512 deployment portfolio, and not automatically a coherent adjusted
VaR/ES pair. Two-fold summaries average the two policy evaluations, not weights.
The primary endpoint and fixed sample size are in [pilot config](configs/pilot.json).

The complete result and limitations are in
[the consolidated report](../docs/experiments/20261007_selection_risk_baselines.md).
