# Quyết định nghiên cứu sau market evaluation

> Cập nhật sau bước chẩn đoán development được yêu cầu tiếp tục: xem [CORRECTION_RESEARCH_DECISION.md](CORRECTION_RESEARCH_DECISION.md). Nội dung dưới giữ kết luận market tại commit88b149b; held-out artifacts không thay đổi.

**Không nâng APTC v2 thành phương pháp thắng hoặc thay thế baseline.** Giữ `historical_se_penalty` và `support_mix50` làm đối chứng bắt buộc. Không sửa method từ kết quả final test vừa xem.

ECB là thí nghiệm chính đã hoàn tất:1.022 validation origins và1.538 final-test origins, cùng protocol đóng băng trước held-out evaluation. `filtered_historical` có mean FZ0 thấp nhất quan sát trên cả equal-weight (−0.611857) và common historical-SE reference (−0.774027), nhưng selector của nó không có pooled ES thấp nhất. `support_mix50` có pooled ES95 thấp nhất quan sát,0.488726pp; historical+penalty0.489436pp; candidate0.490895pp. Đây là minh họa trực tiếp vì sao phải tách forecast quality và selection quality.

Candidate trên ECB equal-weight có ΔFZ0 so historical+penalty −0.004303, CI95%[−0.024080;0.016182], và so pure mixture −0.007419,[−0.024125;0.009201]. TrackB ΔpooledES lần lượt+0.001459pp,[−0.016246;0.016653] và+0.002169pp,[−0.001894;0.007024]. Những so sánh này không chứng minh candidate tốt hơn; thiếu bằng chứng cũng không chứng minh tương đương. Kết luận không đổi với block sensitivity5/20/60. Candidate có mean half-L1 weight-change0.061956 so baseline0.004769; đây là bất lợi về stability quan sát, không được quy thành phí hay lợi nhuận chưa đo.

BoC chỉ là sensitivity về provider/base currency/panel, có nhiều FX factors chồng lấp ECB.747 final-test origins: FHS đứng đầu primary equal-weight FZ0 (−0.661629); Gaussian/Student-t có pooled ES95 thấp nhất quan sát,0.480668pp. Candidate primary ΔFZ0 so historical+penalty −0.000818,[−0.016371;0.012239], so mixture −0.001241,[−0.006109;0.004430]: chưa chứng minh thắng.

**Tín hiệu tích cực có giới hạn:** trên BoC common historical-SE reference, candidate ΔFZ0 so historical+penalty −0.016729,[−0.038664;−0.000497] ở block chính10; CI loại0 với cả5/20/60. Nhưng so pure mixture ở block chính, Δ−0.002942,[−0.006806;0.001536], chưa tách khỏi0; chỉ block60 cho CI âm rất sát0. Không chọn block60 sau khi thấy kết quả. Đây là target phụ, pointwise interval và không điều chỉnh multiple comparisons; không chuyển thành tuyên bố thắng tổng thể. TrackB candidateES0.488166pp so mixture0.486381pp, Δ+0.001785,[0;0.005408].

Các vấn đề còn giới hạn kết luận: latest vintage chưa chứng minh historical availability, chỉ reference changes, tail counts hữu hạn, bootstrap gần-stationary trong môi trường đổi regime, finite bank285, chưa có independent agent/human review. Không có Sharpe/PnL, true conditionalES, confidence guarantee, novelty/SOTA hay độc lập giữa hai nguồn.

**Đúng một next action:** thực hiện một audit độc lập đối với frozen commit `9e70a57` và các CSV/receipt ECB–BoC đã công bố, tập trung vào availability và paired inference, trước khi mở rộng dữ liệu hoặc phương pháp. Giữ nguyên các test years đã xem; chúng không còn là fresh confirmation cho một method được sửa tiếp.
