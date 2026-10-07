# RiskDecision

**Hướng hiện hành: đánh giá rủi ro sau tối ưu danh mục, tách selection optimism khỏi thay đổi thị trường.** Evidence đã có là mô phỏng; chưa có market backtest hoặc thuật toán mới đã thắng.

> Một model đo rủi ro và một policy chọn danh mục là hai thành phần khác nhau. Phải chấm forecast trên cùng danh mục trước khi kết luận model nào dự báo tốt hơn.

## Đọc và chạy tiếp

| Tài liệu | Nội dung |
|---|---|
| [Trạng thái nghiên cứu](docs/RESEARCH_STATE.md) | Câu hỏi, method, findings, cách đọc lại kết quả |
| [Thí nghiệm tiếp theo](docs/NEXT_EXPERIMENTS.md) | Q0 crossed matrix -> Q1 OIC -> Q2 temporal -> Q3 ECB |
| [Hướng tiềm năng](docs/POTENTIAL_DIRECTIONS.md) | Ba nhánh có gate; chưa claim novelty |
| [Data và runbook](docs/DATA_AND_REPRODUCIBILITY.md) | Snapshot còn thiếu, import, license, commands |
| [Nguồn](docs/SOURCES.md) | OIC, entropy pooling, joint VaR/ES và reports gốc |
| [Prompt Astra](prompts/ASTRA_NEXT_RUN.md) | Nhiệm vụ giới hạn cho lượt chạy local tiếp |

## Kết quả cần nhớ

- 80 validation + 320 test instances thuộc bốn synthetic families; không phải thị trường thật.
- Own-selected relative ES error: historical+penalty 14.30%, APTC v2 15.01%. Không phải mức lỗ vốn.
- Historical và historical+penalty có cùng risk forecasts, chỉ khác lựa chọn w. Không gọi penalty là forecaster mới tốt hơn.
- Crossed review trên cùng portfolios chưa chứng minh APTC hơn historical. Band tốt hơn ép khớp point moment nhưng gần pure mixture.
- Markov oracle biết trạng thái thật; model không biết. Phải tách chênh lệch thông tin khỏi lỗi estimator.

Nguồn: [results v2](quant_research_v2/RESULTS_VI.md) và [state/reanalysis](docs/RESEARCH_STATE.md). Đây là consolidation ngày 2026-10-07, không experiment mới.

## Model và nhiệm vụ hiện tại

Giữ GMM/APTC v1/v2, historical, uncertainty-penalty, pure mixture và covariance/FHS controls làm baselines. **Tạm dừng APTC variant search.** OIC có prior art rất sát, phải audit và tái lập đúng assumptions. Hướng tiềm năng ML/DL chỉ mở sau failure mode đã được xác định.

Chạy ngay Q0 và chuẩn bị Q1; tải/audit ECB được phép song song nhưng không dùng final-market outcomes để chọn model. Không có lệnh OIC/crossed runner mới trong consolidation: Astra sẽ triển khai theo spec, không giả vờ đã chạy.

## Giữ lịch sử, giảm log

`quant_tailrisk_pilot/`, `quant_research_v2/`, importer và archive manifest giữ nguyên bytes. Logs/plans/prompt handoff dài ở root chuyển sang [archive](archive/README.md); prompt cũ chỉ còn redirect. Snapshot trước dọn: branch `archive/pre-consolidation-20261007`, commit `41bcdc0`.

Main chưa chứa đủ 931 historical files; xem runbook để import archives có checksum khi cần. Không tái tạo số cũ rồi gọi là original archive. Raw market data, new caches/logs và outputs giữ local theo gitignore. Reproduction lịch sử chạy worktree riêng để bảo toàn measured reports.
