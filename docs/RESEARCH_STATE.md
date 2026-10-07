# RiskDecision — trạng thái và hướng đã chọn

Cập nhật: **2026-10-07**. Base `41bcdc07799458b2a425bd0014e62a6695de5012`. Lần này tổng hợp lại thông tin và hướng chạy; không có training hoặc dữ liệu thị trường mới.

## 1. Quyết định chính

**Giữ câu hỏi về rủi ro sau tối ưu, tạm dừng APTC variant search.** Tách ba việc: (a) ước lượng rủi ro trên cùng danh mục; (b) chất lượng danh mục được chọn; (c) dự phòng rủi ro/thiệt hại kinh tế. Bổ sung OIC và sample-splitting đúng phạm vi trước khi gọi một model mới.

Câu hỏi đã chọn: Trong dữ liệu quá khứ có phụ thuộc thời gian, đánh giá rủi ro của danh mục được lựa chọn sai bao nhiêu vì selection, bao nhiêu vì thị trường thay đổi, và có thể sửa phần nào ở cùng tập thông tin quan sát?

Optimizer's curse, CVaR, entropy pooling, volatility filtering và optimistic-bias correction đều có prior art. Đây là hướng nghiên cứu, chưa phải novelty xác lập.

## 2. Evidence giữ nguyên

Nguồn chính: [v2 results](../quant_research_v2/RESULTS_VI.md), [method](../quant_research_v2/docs/METHOD_V2.md), [protocol](../quant_research_v2/docs/PROTOCOL.md). V1 tách riêng, không coi v1 control trong v2 là nguyên xi cấu hình v1.

- 8 assets, long-only, sum weights=1, cap=.5; 285 candidate portfolios dùng chung mỗi instance.
- 512 observations cho equal-information controls; GMM gốc chỉ 256, block 256 correction là thêm training data, không phải independent certificate.
- 4 synthetic families: Gaussian, asymmetric-crash mixture, Student-t df4, Markov volatility.
- 80 validation và 320 held-out synthetic test instances; 18 configurations, 7,200 result rows không phải 7,200 thị trường độc lập.
- Validation chọn `historical_se_penalty` và candidate `support_band50`. Tất cả evidence là **SYNTHETIC**, không market backtest, không trading profits/Sharpe.

| Pipeline, trên danh mục nó chọn | Relative ES forecast error | Relative ES regret trong bank |
|---|---:|---:|
| Historical CVaR | 14.64% | 3.11% |
| Historical + uncertainty penalty | 14.30% | 3.50% |
| Pooled GMM, 512 observations | 15.43% | 3.55% |
| Pure support mixture 50/50 | 15.08% | 3.27% |
| APTC v2, support + band | 15.01% | 3.30% |

Sai số 15% không nghĩa mất 15% vốn. Regret so population-best trong cùng bank, không optimum liên tục. Markov truth cũ biết trạng thái ẩn cuối mà model không biết; đó là oracle-conditional diagnostic.

Ablation có bằng chứng: band tốt hơn ép khớp point moment, chênh lệch -2.138 điểm phần trăm, CI [-3.082,-1.168]. So với pure mixture, phần correction thêm chưa có ích rõ. V2 chưa thắng strong equal-information controls. Solver warning/convergence receipts giữ nguyên; không loại case khó để làm đẹp.

## 3. Điều phải sửa trong cách đọc kết quả

`historical` và `historical_se_penalty` dùng **cùng risk surface**; penalty chỉ thay argmin, không làm dự báo ES cho một w thay đổi. Vì vậy 14.30% là kết quả pipeline trên các portfolio do nó chọn, không chứng minh forecaster mới tốt hơn.

Bản review chat 07/10 đã tính chéo trên 320 artifact cũ (không phải test mới):

| Danh mục dùng chung | Historical | APTC v2 |
|---|---:|---:|
| Equal-weight | 17.17% | 17.27% |
| Historical+penalty chọn | 14.30% | 14.40% |
| APTC v2 chọn | 14.61% | 15.01% |
| Trung bình bank285 | 15.92% | 15.83% |

Các paired CI được báo cáo đều chứa 0. Trên portfolio do penalty chọn, APTC-minus-historical +.1064 điểm %, CI [-.5291,.6436]. Đây là hậu nghiệm có artifact hỗ trợ trong review, không cơ sở chọn variant mới. Nguồn: `Finance_Quant_Research_Review_20261007.zip`, bảng `quant_crossed_summary_percent.csv`; lần consolidation này không rerun audit.

## 4. Gap phải đối chiếu lại

[Optimizer's Information Criterion (OIC), Iyengar/Lam/Wang, arXiv v4 2025](https://arxiv.org/abs/2306.10081v4) trực tiếp nghiên cứu optimistic bias sau data-driven optimization. Bản review đã chỉ ra Example 6.4 về CVaR allocation. Không claim rộng "đầu tiên sửa rủi ro sau tối ưu". Agent phải đọc lại full text/assumptions trước implementation; không áp công thức influence-function của estimator smooth vào discrete argmin rồi nhận guarantee.

APTC có liên hệ entropy pooling. V2 hỗ trợ thêm historical scenarios và band nhưng phần lợi ích beyond pure mixture chưa được chứng minh. Do đó hiện ưu tiên **đánh giá đúng và baseline sát**, không APTC v3.

## 5. Hướng giải quyết được chọn

`Dữ liệu quá khứ khả dụng -> risk forecaster -> portfolio selector -> crossed evaluator + independent/temporal validation -> phân biệt selection optimism và distribution shift -> đánh giá risk reserve/decision cost`.

Q0 tính lại forecaster x selector; Q1 OIC/sample-splitting trên iid; Q2 phụ thuộc thời gian và common information; Q3 ECB FX với protocol đã khóa. Xem [NEXT_EXPERIMENTS](NEXT_EXPERIMENTS.md).

**Chưa làm:** market run, OIC reproduction, complete DRO/DCC-GARCH comparison, continuous optimizer confirmation, neural improvement, utility validation. Dataset lớn hoặc model lớn hơn không tự tạo novelty.
