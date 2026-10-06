# Quyết định sau kiểm chứng simultaneous calibration

Ngày2026-10-06. Parent`de51ade`; freeze đã commit/push tại`77ba092` trước khi chạy. **Đã thực hiện thí nghiệm, chưa đủ novelty để gọi là phương pháp mới có bảo đảm.** Kết quả mới bác bỏ việc gắn một band bootstrap thông dụng vào pipeline hiện tại rồi mặc nhiên gọi đó là calibrated ES95. Đây là kết luận về các recipe và cỡ mẫu đã thử, không phải bất khả thi cho mọi phương pháp bootstrap.

## Đã làm và kiểm tra

- Chạy500 chuỗi synthetic mới:5 DGP×100 seeds, mỗi chuỗi1280 quan sát×8 assets. Dùng256 quan sát base, calibration256/1024,285 danh mục,3 ngưỡng mỗi danh mục,2 cách dựng ngưỡng,4 cách dựng band và2 estimands. Tổng16.000 rows/160 strata. Không tạo forecast candidate mới.
- 70 tests pass. Audit tái tạo đúng500 input arrays, tính lại96.000 metrics từ per-feature artifacts;600 giá trị số trong bảng được render trực tiếp từ CSV. Hai trường hợp Gaussian62000/Markov62099 refit GMM, ngưỡng, selected feature và tất cả bán kính đều khớp chính xác. Không GMM warning/nonconvergence.
- Reverify931/931 file lịch sử khớp byte; không đổi frozen market source/config/results hoặc correction diagnostic trước đó. Raw FX/cache/per-case synthetic vẫn local. Không tải thêm market data hoặc mở lại validation/final test.

[Bảng đầy đủ](SIMULTANEOUS_CALIBRATION_RESULTS.md), [CSV](../results/coverage_audit_v1/coverage.csv), [protocol](SIMULTANEOUS_CALIBRATION_PROTOCOL.md), [audit](../results/coverage_audit_v1/audit.json).

## Kết quả quyết định

Với `base_only`, tỷ lệ bao phủ đồng thời855 hinge means của **short-block max-t** cho stationary marginal là:

| DGP | n=256 | n=1024 |
|---|---:|---:|
| Gaussian |23/100|61/100|
| Student t4 |23/100|58/100|
| Asymmetric crash |51/100|86/100|
| AR(1) |9/100|46/100|
| Markov volatility |41/100|70/100|

Đây là recipe nhắm mức95%, nhưng không đạt gần95% trong những cấu hình này. Tăng dữ liệu có cải thiện nhiều trường hợp, chưa tạo ra bảo đảm. Với Gaussian/IID max-t, n256 đạt22% (Wilson95%[15,0%;31,1%]); n1024 đạt63%[53,2%;71,8%]. Trong khi đó, riêng equal-weight/q95 đạt98%/100% và selected empirical feature đạt91%/100%. Chỉ báo cáo một danh mục có thể che việc band không đồng thời đúng trên cả bank.

Localization **post-hoc, mô tả, không dùng sửa recipe**: Gaussian/base-only/IID max-t thất bại ở ngưỡng97,5% trong78/100 cases tại n256,37/100 tại n1024. Tất cả lỗi trong kiểm tra này là upper endpoint của band nằm dưới population hinge mean. Có25 cases chứa zero-radius feature tại n256; n1024 không có zero-radius feature nhưng vẫn thất bại37 cases. Vì vậy zero variance không giải thích hết vấn đề. Các quan sát phù hợp với khó khăn của ước lượng tail hiếm và studentization hữu hạn mẫu; chưa phải phân rã nhân quả hay định lý mới. [CSV chẩn đoán](../results/coverage_audit_v1/gaussian_failure_localization.csv).

Heuristic v2 không được định nghĩa là CI95%. Nó bao phủ Gaussian/base-only46% tại n256 và99% tại n1024, với mean median normalized radius xấp xỉ0,242 ở n1024, so IID max-t0,126. Floor không co theo căn bậc hai cỡ mẫu nên coverage cao ở một DGP không chứng minh calibration tổng quát hoặc hiệu quả quyết định. Không đổi floor để cứu kết quả.

Quan trọng hơn, **marginal không đồng nghĩa next-conditional**. AR(1), short-block/base-only có conditional coverage3% tại n256 và0% tại n1024, dù marginal coverage9%/46%. Markov tương ứng conditional50%/26%, marginal41%/70%; band rộng có thể tình cờ bao phủ một trạng thái nhiều hơn mục tiêu marginal, nên không kết luận mọi conditional coverage luôn thấp hơn. Markov dùng latent-state oracle chỉ ở evaluator. Phản ví dụ chính xác trong protocol cho stationary ES95=4 nhưng next-state ES95=10 hoặc0,8163; không phải một realized loss được gọi là true ES.

## Novelty và quyết định

**NO-GO cho claim hiện tại “APTC + simultaneous block bootstrap tạo calibrated ES/portfolio guarantee”.** Có ba lỗ hổng riêng: empirical finite-sample coverage chưa đạt; finite grid không kiểm soát toàn bộ threshold ES; stationary calibration không xác định conditional forecast. Không thể sửa lỗ hổng thứ hai/thứ ba chỉ bằng band rộng hơn.

Khung simultaneous block multiplier đã có trong [Zhang–Cheng](https://arxiv.org/html/1406.1037v2); inference dưới sampling phụ thuộc cũng thuộc các hướng [robust optimization/empirical likelihood](https://arxiv.org/abs/1610.03425). Các recipe ở đây là biến thể studentized để chẩn đoán, không được nhận thừa kế nguyên theorem của các bài đó. Ghép chúng vào objective regularized-maxent chưa tạo khác biệt mới so với [đối chiếu prior art trước đó](NOVELTY_AUDIT_2026_10.md).

Đóng góp bảo vệ được hiện tại là **bằng chứng chẩn đoán có thể tái lập**: tách marginal/conditional, fixed-target/selected-target, và pointwise/simultaneous; chỉ rõ khi nào một claim rộng bị số liệu và phản ví dụ bác bỏ. Nó chưa là thuật toán mới đủ mạnh hoặc bằng chứng APTC thắng baseline. Nghiên cứu này không thay đổi kết luận market: FHS dẫn điểm số forecast trên common ECB target; pure mixture có pooled selected-exposure ES thấp nhất theo điểm ước lượng; APTC v2 chưa chứng minh vượt historical+penalty và pure mixture.

Nếu tiếp tục phát triển phương pháp, cần chọn rõ estimand và giả định trước: conditional risk đòi hỏi cấu trúc trạng thái/thông tin dự báo; stationary risk cần kiểm soát tail/threshold và sai số đồng thời có điều kiện áp dụng cụ thể. Một thiết kế mới phải có điểm khác biệt ngoài việc ghép maxent, bootstrap và ES variational formula. Không dùng các cỡ block/DGP/market test đã xem để chọn rồi tự gọi là xác nhận mới. Chưa có candidate v3 được chọn hoặc triển khai trong lần này.

## NOT RUN và tái lập

Review độc lập **NOT RUN**: Orca terminal báo `zsh: command not found: claude`, sau đó parse error khi task rơi vào shell. Dispatch đã abandon sau khi đọc full stream; release bị Orca giữ lại với`identity_unproven`. Các kiểm tra trên do coordinator thực hiện, không phải peer review. Không dùng CPU multiprocessing hay agent ngoài Orca để thay tên cho review đó.

Không chạy market test mới, yield curves, neural candidate, bootstrap asymptotic proof, all-threshold theorem hoặc independent academic novelty review. Protocol/generator/checks chạy thực tế trên M4 Pro12cores/RAM24GiB; môi trường Python pin giữ nguyên.

```bash
rtk proxy bash scripts/reproduce_coverage_audit.sh
```

Lần chạy mới tạo500 cases mất44,58 giây; cache được kiểm identity/checksum khi tái lập. Thời gian của một lần chỉ đọc cache không phải thời gian chạy500 cases mới. Mọi bảng công khai đều là aggregate, không chứa market raw.
