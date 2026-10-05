# Market artifact audit — PASS

Checked all **125,532 forecast rows**, **627 summary/annual rows**, and **8 fixed first/last-date refits** across four held-out runs. No method or frozen-source changes followed test opening.

| Run | Sessions | Forecast rows | Summary + annual rows | Status |
|---|---:|---:|---:|---|
|ecb_validation|1022|33726|165|PASS|
|ecb_test|1538|50754|231|PASS|
|boc_validation|497|16401|99|PASS|
|boc_test|747|24651|132|PASS|

Audit reconciles each forecast CSV with its atomic window JSON; recomputes realized losses from the local official derived panel and bank weights; checks512 training rows, one-observation gap, last training availability before origin, common targets and source hashes; recomputes scores, failure denominators and pooled ES via a separate fractional-tail calculation. Each run refits the first and last predeclared dates and matches forecasts/weights at1e-10 tolerance.

Report tables are rendered from audited CSVs by `scripts/build_market_reports.py`. All annual periods are present; calibration/residual CIs and all block sensitivities are in public CSVs. Pointwise bootstrap intervals are not a scientific correctness guarantee or independent peer review.

No fallback or undefined FZ0 occurred in the four runs. Finite correction nonconvergence was retained: ECB candidate1validation/5test dates, APTC v1 2validation/3test dates; BoC candidate0validation/2test, APTC v1 1validation/0test. Detailed step counts remain in diagnostic counts and local logs. No dates were discarded for model-specific performance.

Source, configuration and pinned dependencies match pretest commit9e70a57. Original931-file snapshots still match archive checksums; raw/processed market data, per-date rows and caches remain local. Public outputs contain aggregate CSVs plus provenance/audit metadata only.

Machine receipt: [market_artifact_audit.json](market_artifact_audit.json). [Reproduction](MARKET_REPRODUCTION.md), [scope not run](NOT_RUN_STATUS.md). Independent agent review remains **NOT RUN** after documented Orca readiness failures.
