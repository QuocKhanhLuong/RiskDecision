# Kết quả pilot quant — 05/10/2026

## Kết luận

Đã thực hiện pilot có mã nguồn và kết quả thật, nhưng **toàn bộ là mô phỏng**, không phải backtest thị trường. Phiên bản hiệu chỉnh giảm sai số so với model gốc, nhưng **chưa chứng minh ưu thế trước baseline dùng cùng tổng lượng dữ liệu**. Không chốt novelty hoặc khả năng công bố từ thí nghiệm này.

## Method

Học mô hình hỗn hợp Gaussian (GMM), sinh kịch bản, dùng một block dữ liệu độc lập để hiệu chỉnh xác suất các kịch bản tại những hướng danh mục có sai lệch stop-loss lớn. Xác suất được giữ hợp lệ và dùng chung cho mọi danh mục. Lặp 12 lần, rồi tối ưu CVaR95. Xem METHOD.md cho công thức chính xác, dual solver và phạm vi của lập luận lý thuyết.

Không huấn luyện neural network. GMM là mô hình ML thống kê; thao tác cập nhật xác suất có liên hệ chặt với entropy pooling/moment calibration đã có trong literature.

## Setting

- 8 tài sản, long-only, tổng trọng số bằng 1, giới hạn 50% mỗi tài sản.
- 285 danh mục ứng viên cố định theo mỗi seed, dùng chung giữa các phương pháp chính.
- Hai loại thị trường: Gaussian; mixture có các cú sốc đồng thời theo nhóm tài sản.
- 30 lần lặp độc lập cho mỗi loại, seed 100–129.
- 256 quan sát fit GMM gốc + 256 quan sát dùng học correction; pooled controls được dùng cả 512.
- 2048 kịch bản sinh ra không được coi là 2048 quan sát thị trường mới.
- ES population được tính bằng công thức mixture, chỉ dùng sau khi khóa quyết định. Không dựa vào số đo tail từ một test nhỏ.
- Mixture là Gaussian-mixture hữu hạn, không phải power-law heavy tail. Chưa có dynamics, chi phí giao dịch hay thực thi.

## Kết quả ở thị trường có cú sốc

| Phương pháp | ES dự báo (%) | ES thật của danh mục (%) | Sai số tuyệt đối trung bình (điểm %) |
|---|---:|---:|---:|
| GMM ban đầu, 256 mẫu | 2.6495 | 2.8506 | 0.4145 |
| GMM dùng toàn bộ 512 mẫu | 2.6723 | 2.8104 | 0.3056 |
| Hiệu chỉnh hướng ngẫu nhiên | 2.6733 | 2.8358 | 0.2853 |
| Hiệu chỉnh portfolio-tail thích nghi | 2.6703 | 2.8220 | 0.2709 |
| CVaR lịch sử, 512 mẫu | 2.6856 | 2.7980 | 0.2359 |
| Gaussian + Ledoit–Wolf | 1.7732 | 2.7981 | 1.0249 |

Mỗi số là trung bình 30 lần lặp. Sai số tuyệt đối là trung bình |ES thật - ES dự báo| theo từng lần lặp; không bằng trị tuyệt đối của chênh lệch hai trung bình.

Hiệu chỉnh thích nghi giảm MAE từ 0.4145 xuống 0.2709 điểm %, giảm khoảng 34.7% so với GMM 256 mẫu. Nhưng correction được xem thêm 256 mẫu, vì vậy chỉ riêng so sánh này không chứng minh lợi ích thuật toán.

So với GMM 512 mẫu, chênh lệch MAE của candidate là -0.0347 điểm %, CI95% [-0.0935, 0.0258]: chưa có bằng chứng chắc chắn.

So với CVaR lịch sử, ES population của danh mục candidate cao hơn 0.0239 điểm %, CI95% [0.0035, 0.0466]. Ở setting này baseline thống kê đơn giản chọn danh mục có rủi ro thật thấp hơn.

So với chọn moment directions ngẫu nhiên, chênh lệch MAE -0.0144 điểm %, CI95% [-0.0423, 0.0108]: chưa xác nhận thành phần adaptive thắng trên thị trường stress.

Ở Gaussian control, candidate giảm MAE so với GMM gốc, nhưng Gaussian + Ledoit–Wolf vẫn tốt hơn. Đây là đối chứng quan trọng chống kết luận model phức tạp luôn có lợi.

## Hiện tượng trước/sau tối ưu

Với GMM gốc ở thị trường cú sốc:
- Danh mục chia đều: ES dự báo 2.9339%, ES thật 2.8637%.
- Danh mục tối ưu theo model: ES dự báo 2.6495%, ES thật 2.8506%.

Model dự báo lợi ích giảm rủi ro khoảng 0.2845 điểm %, nhưng lợi ích thật chỉ khoảng 0.0131 điểm %. Sai lệch thêm sau lựa chọn trung bình 0.2713 điểm %, bootstrap CI95% [0.2090, 0.3388]. Đây là bằng chứng mô phỏng của optimizer's curse đã biết, không phải phát hiện mới.

## Kiểm tra và giới hạn

- 480 dòng kết quả được kiểm tra lại từ saved risk surfaces và công thức population.
- 8 nhóm sanity assertions pass; population formula được đối chiếu thêm với 300,000 mẫu độc lập.
- Một optimizer trung gian ở random-control seed 111 báo lỗi line-search; tất cả nghiệm dual cuối cùng và GMM fits báo hội tụ. Cảnh báo được lưu.
- Khoảng tin cậy là paired bootstrap 10,000 lần trên 30 repetition độc lập, pointwise, không phải 10,000 thí nghiệm thị trường.
- Tổng thời gian các seed khoảng 19.75 giây CPU trong môi trường ChatGPT, không phải đo trên Mac của người dùng. Không tính thời gian nghiên cứu/viết code/audit.
- Không chứng minh upper bound rủi ro hay guarantee triển khai.
- Chưa so với DRO đầy đủ, DCC-GARCH, decision-calibration chuẩn hoặc decision-focused generative baseline hiện đại.
- Chưa có dữ liệu H.10 trong môi trường thực thi: request/download bị lỗi, không có kết quả thị trường.

## Quyết định khoa học

Giữ câu hỏi nghiên cứu về sai số rủi ro sau tối ưu. **Không gọi prototype này là một method mới đã thắng.** Muốn tiếp tục hướng method cần chứng minh thêm giá trị so với baseline equal-information, xử lý sai số của moment targets và mở rộng việc tìm hướng danh mục ngoài bank hữu hạn. Không tự động thêm Transformer/diffusion để cứu novelty.
