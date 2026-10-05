# Historical import completed

All **931 original historical files** (83 v1, 848 v2) were verified byte-for-byte against both original archives on 2026-10-05. The importer created 900 missing files; all 31 existing files matched. A second verification found 931 matches and zero pending files. No overwrite or regenerated result was used.

Import commit: [`ad0d967a520769f15528750aba5116223a4a133a`](https://github.com/QuocKhanhLuong/RiskDecision/commit/ad0d967a520769f15528750aba5116223a4a133a), pushed to `research/local-market-validation` before empirical code changes. Parent was actual clean HEAD `41bcdc07799458b2a425bd0014e62a6695de5012`; main was not changed.

See [receipt](HISTORICAL_IMPORT_RECEIPT.json) and [archive checksums](../archives_manifest.json). Archive sizes: 3,154,716 and 50,739,052 bytes; uncompressed historical bytes: 62,558,679. ZIP CRC and every existing file SHA256 passed. Exact original CSV CRLF/whitespace was retained despite Git whitespace warnings.

Historical results remain synthetic. New market code/results live separately; original snapshot source/results are immutable for this work. Public Git excludes new raw market data, per-date forecasts, caches and environments.
