# Import status — transparent boundary

## Published directly through the GitHub connector

The repository contains executable v1/v2 research engines, numerical tests, official FX loaders, the prototype market runner, core method/protocol/data documents, historical result reports, selected aggregate metadata and the local execution prompt. Original paths are retained. Transferred original text is checked against its archive blob hash.

## Not fully uploaded directly

The complete archives contain **931 historical files**: 83 v1 files and 848 v2 files. The direct import is a subset. It does not contain all per-seed NPZ arrays, large raw/aggregate CSVs, figures, complete historical manifests or ancillary reporting files. Therefore, cloning this repository alone does not yet reproduce the complete original artifact inventory. This is an upload limitation, not a new research result.

The complete original ZIPs remain the source for the missing files. Their hashes/counts are in `archives_manifest.json`; no result is reconstructed merely to fill a missing artifact.

## Complete it locally

Save the two original attachments in Downloads:

1. Quant_Tail_Risk_Method_and_Pilot.zip
2. Quant_Risk_v2_Code_Results.zip

From a clean clone, BEFORE editing imported files:

```bash
python3 scripts/import_chat_archives.py --archive-dir "$HOME/Downloads" --verify-only
python3 scripts/import_chat_archives.py --archive-dir "$HOME/Downloads"
git status --short
# Review paths, then stage only the two historical study directories:
git add -- quant_tailrisk_pilot quant_research_v2
git commit -m "data: restore verified historical synthetic research snapshots"
# Push the current research branch after confirming origin and branch.
```

Do not run blanket `git add .` after downloading new market data. Do not force-push. Update this status only after the full local import has actually been committed/pushed, including the receipt and commit SHA.

## Checks performed during handoff

- Existing v2 tests rerun: 26 passed.
- Fresh full archive extraction: 931 files checked and created.
- Second verification: 931 matching files, no new writes needed.
- Conflicting existing file: correctly rejected before overwrite.
- No market experiment run during this handoff.

Full data audits require the restored historical files and should run on an isolated working copy: original audit/report scripts can rewrite receipts. Hardware and runtime of a local reproduction must be recorded separately from the historical Linux results.
