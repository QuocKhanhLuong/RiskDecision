# Quant tail-risk research v2 — kết quả ngày 05/10/2026

## 1. Kết luận thực tế

Đã mở rộng nghiên cứu, xây và kiểm thử các biến thể, chạy **80 bộ validation và 320 bộ test mô phỏng**, tổng cộng 7.200 dòng đánh giá của 18 cấu hình/đối chứng. Không phải 7.200 thị trường độc lập. Các seed test chưa được dùng để chọn cấu hình.

**Kết quả tốt nhất theo tiêu chí đã khóa vẫn là baseline CVaR lịch sử + phạt bất định: sai số ES tương đối trung bình 14,30%. Candidate APTC v2 đạt 15,01%.** Không có cơ sở gọi APTC v2 là phương pháp mới đã thắng. Các cấu hình tốt ở riêng từng DGP không được dùng tạo một routing oracle sau khi xem test.

**Chưa chạy được dữ liệu thị trường thật.** Đã xác minh nguồn và điều khoản ECB, Bank of Canada và BIS, nhưng tải file vào môi trường tính toán thất bại. Các số dưới đây hoàn toàn từ dữ liệu mô phỏng, không phải FX/bond backtest. Không có Sharpe, lợi nhuận giao dịch hay bằng chứng triển khai thực tế.

## 2. Nâng cấp method

APTC v2 dùng GMM ba thành phần tạo kịch bản, bổ sung các quan sát ở block correction vào support, rồi hiệu chỉnh trọng số bằng KL. Điểm thay đổi quan trọng là chỉ phạt phần sai lệch moment vượt một band theo quy mô standard error, thay vì ép khớp một target tail vốn rất ít mẫu. Band này là heuristic, không phải khoảng tin cậy được bảo đảm.

Các ablation: chỉ trộn support; khớp point-target; beta .25/.50; một phiên bản lọc volatility EWMA. Validation chọn beta=.50 và band=1. Predictor/candidate/metric đã khóa trước test.

Không huấn luyện deep learning. Entropy pooling, volatility filtering và regularization đã có prior art. Method là prototype ứng viên, không phải phát minh đã xác lập.

## 3. Protocol

- 8 tài sản; chỉ mua; tổng trọng số1; mỗi tài sản tối đa.5; không cash, đòn bẩy hoặc transaction costs.
- 285 danh mục dùng chung cho mọi model trong mỗi lần lặp.
- 512 quan sát cho các equal-information controls. GMM gốc chỉ256; block256 còn lại là dữ liệu huấn luyện thêm của correction. Không gọi nó là certification set.
- 1.536 kịch bản sinh không tạo thêm quan sát thị trường độc lập.
- 4 DGP: Gaussian, mixture có cú sốc đồng thời, Student-t df4, Markov latent volatility.
- Validation20 seed/family; test80 seed/family. Các seed validation2000–2019 và test4000–4079 tách hoàn toàn.
- Primary selection endpoint: trung bình |ES dự báo − ES population|/ES population của danh mục được model chọn, cân bằng bốn DGP.
- ES95 được tính bằng công thức population chỉ trong evaluator. Không vào fitting, candidate selection hay tối ưu danh mục.
- Markov truth có điều kiện theo latent state thật tại cuối cửa sổ; model không biết state. Đây là oracle-conditional diagnostic, không phải regret so với Bayes optimum dựa trên cùng thông tin quan sát.
- Paired bootstrap5.000 lần theo seed, giữ cùng seed giữa bốn DGP; CI pointwise, không có claim nhiều kiểm định đồng thời.

## 4. Bảng tổng hợp test

| Phương pháp | Sai số ES tương đối ↓ | Regret ES tương đối ↓ |
|---|---:|---:|
| GMM gốc trên 256 mẫu | 18.15% | 5.10% |
| GMM trên toàn bộ 512 mẫu | 15.43% | 3.55% |
| APTC v1 — bản đối chứng 8 vòng | 14.46% | 3.50% |
| CVaR lịch sử | 14.64% | 3.11% |
| CVaR lịch sử + phạt bất định | 14.30% | 3.50% |
| Chỉ trộn kịch bản model/lịch sử 50/50 | 15.08% | 3.27% |
| Support + khớp moment dạng điểm | 17.15% | 4.41% |
| APTC v2 — support + uncertainty band | 15.01% | 3.30% |
| Filtered historical — EWMA | 17.32% | 6.25% |
| Filtered APTC v2 | 17.68% | 5.92% |
| Student-t + covariance shrinkage | 18.75% | 1.44% |
| Gaussian + covariance shrinkage | 20.26% | 1.44% |

Sai số ES tương đối15% nghĩa là mức ES dự báo lệch khoảng15% so với ES population của chính danh mục được chọn; **không phải mất15% vốn**. Regret tương đối so với danh mục tốt nhất theo population trong cùng bank285; không phải optimum liên tục và không phải lợi nhuận đầu tư.

## 5. Đối chiếu quan trọng

- APTC v2 giảm sai số khoảng **17.3%** so với GMM256. Nhưng phương pháp correction được thêm dữ liệu nên đây không phải bằng chứng lợi ích thuật toán equal-information.
- So với GMM512: chênh lệch sai số tương đối **−0,422 điểm phần trăm**, CI95% [−1,242;0,313]. Chưa xác lập hơn baseline pooled.
- So với baseline đã chọn CVaR+penalty: **+0,712 điểm phần trăm**, CI95% [−0,041;1,386]. Không chứng minh candidate tốt hơn; cũng không khẳng định thua có ý nghĩa trên toàn bộ miền dựa vào CI này.
- Band so với point-fit trên cùng empirical support: **−2,138 điểm phần trăm**, CI95% [−3,082;−1,168]. Đây là ablation tích cực rõ nhất: quá khớp tail moment ít mẫu có hại.
- Band so với chỉ trộn support: **−0,071 điểm phần trăm**, CI95% [−0,725;0,503]. Chưa chứng minh adaptive moment correction giúp thêm ngoài mixture đơn giản.
- Trên Gaussian,79/80 runs band không làm đổi risk surface so với prior mixture. Student-t60/80, Markov42/80, crash39/80. Đây là phân tích hậu nghiệm cơ chế, không phải tiêu chí chọn model.

## 6. Theo từng loại thị trường

| Thị trường mô phỏng | GMM 512 | CVaR lịch sử | CVaR + penalty | APTC v2 |
|---|---:|---:|---:|---:|
| Gaussian | 5.87% | 5.03% | 5.07% | 5.34% |
| Cú sốc đồng thời | 10.84% | 10.63% | 10.06% | 12.21% |
| Student-t, df4 | 11.47% | 9.80% | 10.19% | 10.54% |
| Biến động Markov | 33.55% | 33.11% | 31.87% | 31.94% |

Trong crash mixture, APTC v2 có ES thật trung bình2,8531% so với2,8224% của historical+penalty. Chênh lệch+0,0307 điểm phần trăm, CI95% [0,0137;0,0504]: ở thí nghiệm này baseline chọn danh mục ít rủi ro hơn.

Ở Markov, APTC v2 có selected ES thấp hơn historical+penalty khoảng0,0130 điểm phần trăm, nhưng forecast error vẫn khoảng32%. Không suy thành chiến thắng toàn diện. Gaussian/Student covariance controls có thể chọn danh mục tốt dù đánh giá tail risk sai; hai nhiệm vụ phải tách.

## 7. Dataset thật đã xác minh, chưa chạy

1. **ECB FX reference rates**: lựa chọn đầu tiên; official archive; eight-currency panel; terms yêu cầu ghi nguồn, nêu biến đổi và điều kiện paid use. Reference prices, không phải executed quotes.
2. **Bank of Canada daily FX**: nguồn kiểm tra khác, method hiện tại từ2017; quotedCAD/foreign; indicative daily averages. Không coi ECB và BoC là hai thị trường độc lập.
3. **Bank of Canada zero-coupon curves**: fixed-income risk,120maturities0.25–30 năm. Công bố thường trễhai tuần. Phải định nghĩa bond repricing/DV01, không dùng yield changes như total returns.
4. **ECB euro-area yield curves**: fitted curves cho risk fixed-income; cần series/compounding/vintage chính xác.
5. **BIS effective exchange rates**: panel bổ trợ/stress covariates, không phải traded assets.

Nguồn, terms, cách trích dẫn và trạng thái được ghi trong docs/DATASET_AUDIT.md. Các file data/downloads.json là error receipts; không có market raw bytes bị giả lập. Không có actual cleaned counts cho các dataset này.

## 8. Kiểm thử và tính tái lập

- **26 tests pass**, gồm numerical risk, fractional atoms, split isolation, entropy simplex/dead-zone, train/future separation và loader fixtures. Fixtures không phải market observations.
- Audit lại400 cached market instances,7.200 aggregate rows,**79,200 scalar values**; bốn refit kiểm tra candidate; không thấy sai lệch aggregate.
- Analytic ES kiểm tra thêm bằng200.000 future draws/family, không tham gia fitting. Đây là kiểm tra số học, không phải market evidence.
- GMM fits đều báo hội tụ. Có **7 component-run receipts** mà ít nhất một bước calibration không báo success; trong đó candidate chính có1/320 test instance. Các output hữu hạn vẫn giữ trong bảng, không loại để làm đẹp. Loại instance candidate bị cảnh báo trong sensitivity không thay kết luận. File audit_receipt.json có chi tiết. Không tuyên bố mọi optimization step hội tụ.
- Validation walltime39.13s; test154.43s với3 CPU workers trong môi trường Linux này. Không phải benchmark Mac. Các phương pháp chia sẻ fit/risk artifacts;18 result rows không phải18 lần train độc lập.
- Chạy song song bằng process; **không có independent subagent/human review**.

## 9. Kết luận phương pháp

Giữ **historical CVaR + uncertainty penalty** làm mốc mạnh nhất theo tiêu chí đã đăng ký. APTC v2 là candidate/ablation, chưa thay thế baseline. Không tuyên bố novelty, SOTA hay lợi nhuận tài chính.

Nghiên cứu tiếp chỉ có ý nghĩa nếu kiểm tra được empirical time-series risk, với FHS/GARCH và DRO phù hợp. Không nên thêm neural network để cứu một cải thiện mà pure historical mixture đã giải thích được. Chuỗi kiểm tra nên là: official data → correct timing → frozen equal-information comparison → evaluate forecast and economic risk separately.

## 10. Giới hạn chưa hoàn thành

Chưa có official market data imported; chưa empirical FX/bond test; chưa tái lập full Wasserstein DRO, DCC-GARCH hay decision-focused deep scenario model; không có continuous-weight optimizer; không có expert/economic validation. Toàn bộ kết quả nằm trong bốn synthetic families đã định trước, không xác lập generalization sang thị trường thật.
