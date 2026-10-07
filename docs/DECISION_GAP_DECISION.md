# Kết luận nghiên cứu: chưa đủ novelty; gate không cứu được APTC v2

2026-10-07. Parent `a9b6dff`, khóa code/protocol và push tại `a2ad3f8` trước khi chạy. **Chưa có cơ sở gọi APTC v2, fixed-scale bands, hay paired decision gate là một phương pháp mới đã vượt baseline mạnh.** Lần này đã kiểm tra trực tiếp chất lượng quyết định, không chỉ tăng coverage rồi suy ra portfolio tốt hơn.

## Thực sự đã làm

Chạy 1.000 chuỗi mới:200 seeds mỗi cơ chế Gaussian, Student-t4, asymmetric crash, AR1 và Markov volatility; hai cỡ assessment 256/1024 dùng prefix lồng nhau. Fit các danh mục bằng 512 điểm đầu, giữ khoảng cách 32 điểm, đánh giá trên đoạn sau. Hai numerical processes, một thread/process, Apple M4 Pro 12 cores/RAM 24 GiB; thời gian thực thi 200,35 giây. Không đọc lại market final test để sửa phương pháp.

Baseline được giữ là historical+SE; ứng viên là danh mục do pure mixture, APTC và FHS chọn. So sánh gate dùng band tuyệt đối, gate dùng sai số **chênh lệch ES được ghép cặp**, rule chỉ nhìn point estimate, và gate bỏ riêng APTC. Đánh giá bằng population ES giải tích của mô phỏng, không lấy một realized loss làm “true ES”.

Hai AGY worker thực sự hoàn thành qua Orca: phản biện thiết kế và audit code. Tôi đã kiểm lại và bác một số kết luận quá mức của cả hai, ghi trong [review adjudication](DECISION_GAP_REVIEW.md). Reviewer code hoàn thành sau lúc freeze/chạy, được yêu cầu không xem kết quả mới; không mô tả đây là hai lượt phê duyệt hoàn tất trước test.

## Có lợi ích thật, nhưng baseline nào bị vượt là điều quyết định

Ở n=1024, paired radius trung bình chỉ bằng khoảng 12,7–27,5% radius lấy từ các band tuyệt đối. Gate tuyệt đối không đổi danh mục lần nào; paired gate đổi 7–20 lần/200 tùy cơ chế. Coverage đồng thời của ba chênh lệch marginal ES đạt 94,5–95,5%. Đây là quan sát thực nghiệm, không phải bảo đảm finite-sample 95%.

Bảng dưới là mean `(ES_gate − ES_comparator) / ES_marginal_training_baseline`, đổi sang phần trăm. CI 95% bootstrap ghép cặp theo seed, pointwise; số âm có lợi cho gate. Mỗi hàng 200 chuỗi độc lập trong cơ chế đó.

| Cơ chế, n=1024 | Số lần đổi | Gate so với giữ historical+SE cũ | Gate so với historical+SE dùng toàn bộ lịch sử hiện có, CI 95% |
|---|---:|---:|---:|
|Gaussian|20/200|−0,350%|+0,922% [0,707%; 1,147%]|
|Student-t4|17/200|−0,611%|+1,622% [1,190%; 2,048%]|
|Asymmetric crash|7/200|−0,154%|+1,300% [0,984%; 1,644%]|
|AR1|13/200|−0,292%|+1,010% [0,692%; 1,349%]|
|Markov volatility|12/200|−0,298%|+0,962% [0,679%; 1,249%]|

Paired CI cho cải thiện so với **giữ danh mục cũ** đều âm. Vì vậy nói “gate hoàn toàn vô dụng” là sai. Nhưng nó thua historical+SE dùng toàn bộ thông tin sẵn có ở cả năm cơ chế. Baseline này có thể dùng cả 32 điểm gap mà gate chủ động bỏ; đây là chi phí của thiết kế phân chia dữ liệu, không phải một phép can thiệp chỉ khác thuật toán. Các baseline recent 512 cũng được báo đầy đủ. Không thể lấy chiến thắng trước một danh mục đã cũ làm bằng chứng thắng cách dùng dữ liệu tốt hơn.

Cả ba cơ chế IID đều **trượt tiêu chí đã khóa** về mức switching tối thiểu có Wilson lower ≥ 10% và vượt toàn bộ nhóm comparator bắt buộc. Không thay ngưỡng sau khi biết kết quả. Full-history historical+SE có mean marginal risk thấp nhất trong các control đã chạy ở cả năm cơ chế; không suy ra nó tốt nhất cho mọi conditional forecast hoặc cho market thực.

## APTC có đóng góp thêm không?

**Chưa có bằng chứng thắng nhất quán.** Bỏ APTC khỏi gate không đổi quyết định ở Gaussian và AR1. Ở Student-t4/Markov có vài lần thay đổi có lợi nhưng CI của lợi ích thêm vẫn chạm 0; crash có điểm ước lượng xấu đi. Không gán mọi thành công của nhóm ứng viên cho APTC.

Phân tích trực tiếp bổ sung, ghi rõ descriptive sau thực thi, cũng giữ cả tín hiệu dương lẫn âm:

- Student-t4: danh mục APTC fit 512 có marginal ES thấp hơn historical+SE khoảng 0,832% (CI [−1,292%; −0,396%]) và thấp hơn pure mixture 0,271% (CI [−0,567%; −0,025%]). Đây là tín hiệu thành phần đáng ghi nhận, với CI pointwise chưa hiệu chỉnh nhiều so sánh.
- Gaussian: APTC tốt hơn historical+SE về allocation nhưng **trùng pure mixture**, nên chưa chứng minh entropy correction tạo lợi ích.
- Asymmetric crash: APTC tệ hơn cả historical+SE lẫn pure mixture ở **cả common-target forecast error và allocation risk**. Allocation tăng 0,765% so với historical+SE, 0,345% so với mixture, CI đều dương.
- Common equal-weight forecast: historical estimate có mean relative absolute ES error thấp nhất trong bốn estimator ở cả năm cơ chế. APTC có một tín hiệu nhỏ hơn mixture trên AR1, nhưng không vượt historical một cách rõ ràng. Forecast error và selected-portfolio risk vẫn là hai bảng riêng.

Đây không phải việc APTC “không bao giờ giúp”. Vấn đề là tín hiệu phụ thuộc cơ chế, không chiếm ưu thế trước các baseline mạnh, và chưa có cấu trúc thuật toán khác biệt được chứng minh. Student-t+shrinkage và random-direction correction chưa được chạy trong thí nghiệm mới này; thiếu chúng ngăn kết luận rằng tín hiệu Student-t4 là đóng góp riêng.

## Phản biện sâu hơn: safety marginal không đủ cho quyết định kế tiếp

Trên AR1/n=1024, paired gate có 0/200 lần làm marginal ES xấu đi nhưng **6/13 lần switching làm conditional ES kế tiếp xấu đi**. Coverage conditional chỉ 40%. Với Markov, 3/12 lần switching làm conditional ES xấu đi, coverage 80,5%; latent state chỉ được evaluator biết. Một harm rate nhỏ trên tất cả 200 cases có thể che rủi ro cao trong số ít lần hệ thống thực sự hành động.

Vì vậy một hướng mới muốn phục vụ quyết định theo thời gian phải xác định đúng information set và conditional target. Đổi tên một band marginal thành “safe decision” không giải quyết được vấn đề. Block bootstrap xử lý phụ thuộc của estimator cũng không tự biến estimand marginal thành conditional.

## Novelty: loại được những claim nào, còn gì chưa biết?

Mapping regularized maxent của APTC đã có trong audit trước. Lần này đối chiếu thêm MCS, OIC, SPIBB, precision diagnostics cho ES, robust ES estimation và orthogonal ES regression; nguồn gốc và phạm vi đọc ở [review](DECISION_GAP_REVIEW.md). So sánh cặp, bootstrap max, abstention theo CI, variance penalty hoặc thêm orthogonal score đều không tự tạo một đóng góp mới.

Đóng góp hiện có của repository là **bộ bằng chứng tái lập về các cơ chế lỗi và các đối chứng cần thiết**: inactive correction, fixed-hinge identification gap, studentization failure, chi phí phân chia dữ liệu, và marginal/conditional decision mismatch. Các mảnh đó có giá trị nghiên cứu, nhưng chưa đủ chứng minh một phương pháp mới hoặc tự bảo đảm một bài báo có novelty mạnh. Tìm kiếm này cũng không chứng minh mọi hướng APTC đều bất khả thi.

**Đúng một hành động tiếp theo có cơ sở:** kiểm chứng tín hiệu Student-t4 trên seeds và covariance mới, với **Student-t+shrinkage và random-direction correction** làm đối chứng, khóa protocol trước khi mở kết quả. Mục tiêu là bác bỏ lời giải thích “tail model/regularization có sẵn đã đủ”, trước khi nghĩ tới APTC v3. Đây là bước tiếp theo **NOT RUN**, không phải lời hứa candidate sẽ thắng; không tiếp tục mở hàng loạt dataset hoặc thêm neural model.

## Kiểm chứng và giới hạn

- 85 tests pass. Audit tái tạo 1.000 input arrays, 208.000 metrics, 30 model refits và 870 ô bảng kết quả. [Audit receipt](../results/decision_gap_v1/audit.json); 20 ô trong bảng tóm tắt trên cũng được đối chiếu trực tiếp với CSV.
- 3/3.000 fits APTC báo L-BFGS-B `status 2: ABNORMAL`, đều giữ kết quả hữu hạn, không loại case. Refit riêng ba trường hợp tái hiện lỗi; [chi tiết](../results/decision_gap_v1/convergence_failures.json). Không GMM warning/nonconvergence. Không sửa solver theo outcome.
- Một lỗi xuất JSON NumPy boolean được sửa ở report builder; model source và protocol hash không đổi. Báo cáo thêm các contrast trực tiếp sau chạy được gắn nhãn descriptive, không đổi tiêu chí GO.
- Một bank/covariance family cố định, chỉ 200 seeds mỗi cơ chế; sizes lồng nhau; nhiều CI pointwise. FHS nhắm động lực ngắn hạn nên không lấy thứ hạng trên marginal simulation làm thứ hạng market. Ba challenger được chọn từ training, không có guarantee cho tìm kiếm thích nghi trên toàn assessment bank.
- 931/931 file lịch sử vẫn nguyên byte; đã push riêng từ `ad0d967`. Market ECB/BoC đã tải/chạy ở vòng trước vẫn giữ nguyên, không công bố raw/cache. Thí nghiệm mới hoàn toàn synthetic.
- Kết luận market không đổi: ECB FHS thấp nhất về common-target FZ0; pure mixture thấp nhất về point estimate pooled selected-exposure ES; chưa chứng minh APTC thắng historical+penalty và mixture. BoC là sensitivity nguồn/base currency, không phải thị trường độc lập.
- **NOT RUN:** Student-t mechanism follow-up nói trên, phương pháp v3, theorem bảo đảm conditional safety, market confirmation mới, yield curves, neural models. Hai AGY review hoàn thành; một phiên novelty bổ sung chưa xác minh, không tính thành kết quả.

[Protocol](DECISION_GAP_PROTOCOL.md), [bảng đầy đủ](DECISION_GAP_RESULTS.md), [CSV](../results/decision_gap_v1/summary.csv), [paired comparisons](../results/decision_gap_v1/comparisons.csv), [APTC direct comparisons](../results/decision_gap_v1/direct_aptc_comparisons.csv).

```bash
rtk proxy bash scripts/reproduce_decision_gap.sh
```
