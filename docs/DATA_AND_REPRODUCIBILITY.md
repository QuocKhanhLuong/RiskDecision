# Dữ liệu, artifacts và runbook

## Snapshot hiện có và phần còn thiếu

`quant_tailrisk_pilot/` và `quant_research_v2/` giữ nguyên bytes từ base `41bcdc0`, gồm code/tests/configs, method và một số aggregates. Không di chuyển chúng: importer/hash/audit cần đường dẫn gốc.

Main trước consolidation chưa chứa toàn bộ snapshot 931 files. Per-seed NPZ, một số CSV/figures và artifacts nằm trong hai archive gốc; xem [import receipt](../archive/20261007/docs/IMPORT_STATUS.md). Không nói đã nhập đủ chỉ vì docs đã được dọn.

Nếu local có `RiskDecision_Local_Import_Bundle`:

```bash
python3 scripts/import_chat_archives.py --archive-dir "$HOME/Downloads/RiskDecision_Local_Import_Bundle" --verify-only
python3 scripts/import_chat_archives.py --archive-dir "$HOME/Downloads/RiskDecision_Local_Import_Bundle"
```

Thư mục cần chứa đúng hai ZIP gốc theo `archives_manifest.json`. Importer không download, không overwrite file khác, không tự push. Historical measured files giữ nguyên; logs/cache của experiments mới để `runs/`, không commit hàng loạt. Import vào branch/worktree riêng nếu cần audit đủ artifacts, không chạy lại để giả làm snapshot gốc.

## Môi trường

```bash
cd quant_research_v2
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
```

Dùng Python tương thích pins; source handoff ghi Python 3.13. Kiểm tra Mac thực tế thay vì đổi dependencies im lặng. Test receipt 26 pass là lịch sử; consolidation chưa rerun. Model hiện tại dùng CPU, không cần thuê GPU. MPS chỉ cho extension neural thực sự cần thiết.

## Market data gate

[Audit gốc](../quant_research_v2/docs/DATASET_AUDIT.md) mô tả ECB, Bank of Canada và BIS. Đây là audit tại 2026-10-05; kiểm tra lại terms/version khi tải. Còn **NOT RUN** trong main.

- ECB FX: primary candidate. Source và citation chính thức, accurate attribution/modification disclosures; reference prices không phải executable quotes.
- BoC daily FX: method hiện tại từ 2017; CAD/foreign units, nguồn/base currency robustness, không độc lập hoàn toàn với ECB.
- BoC zero curves: fitted yields/120 maturities trong audit; thường có release lag hai tuần. Không coi yields là bond returns; cần repricing/horizon đúng.
- BIS EER: supplementary indices, không investable prices.

Starter loader từ `quant_research_v2/`:

```bash
python src/market_data.py --source ecb --out ../data/raw/ecb
```

Chỉ sau Q3 audit mới chạy assessment. `src/run_market_risk.py` hiện chưa có crossed common-portfolio design đầy đủ; smoke fixtures không phải market validation. Không dùng output hiện tại xếp hạng forecaster trên khác loss targets.

## Historical replay

Runners cũ ghi trong package results. Dùng worktree riêng hoặc isolated copy để giữ measured files:

```bash
git fetch origin
git worktree add --detach ../RiskDecision-history-41bcdc0 41bcdc07799458b2a425bd0014e62a6695de5012
```

Mỗi new run: source/data/config/selection hashes, split/calendar, units, period/horizon, solver warnings, seed, forecast/selection IDs, device, timing và final report. Unknown/NOT RUN không ghi thành 0. Random future scenarios không phải market observations. Market raw và new outputs đã nằm trong gitignore; không commit credentials.
