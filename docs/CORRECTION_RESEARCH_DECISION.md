# Đánh giá sau chẩn đoán correction

Ngày2026-10-05. Freeze trước khi chạy: `dd468a2bff558f076aa41fc5c9fed4d644df68ce`. Đã thực hiện nghiên cứu bổ sung, không chỉ viết proposal. Tất cả bằng chứng mới là **development**, không thay thế market final test đã công bố.

## Kết luận hiện tại

**Chưa có cơ sở nâng APTC v2 thành đóng góp phương pháp mới mạnh hoặc model thắng.** Nghiên cứu lần này làm rõ cơ chế và thu hẹp claim, không cố cứu candidate bằng tuning. Mục tiêu tối ưu KL+band thuộc khung regularized maximum entropy đã có; adaptive mining còn chưa chứng minh lợi ích ổn định ở cả dự báo và lựa chọn danh mục.

Các nguồn và phép đối chiếu cụ thể nằm trong [novelty audit](NOVELTY_AUDIT_2026_10.md). Kết quả số được sinh trực tiếp từ CSV trong [báo cáo đầy đủ](CORRECTION_DIAGNOSTIC_RESULTS.md). Phản ví dụ và phân rã ở [identifiability](CORRECTION_IDENTIFIABILITY.md) là suy luận chẩn đoán cơ bản, không tự nhận định lý mới.

## Những điều đã học được

1. **Band thường hoạt động như giữ nguyên mixture trong mô phỏng:** 56/80 risk surfaces không đổi; 73/80 chọn cùng danh mục. Gaussian20/20 không đổi; crash15/20, Student13/20, Markov8/20. Scale floor chi phối trung bình85,43% hướng; band không tương đương một khoảng tin cậy một SE. Đối chứng random-band còn không đổi70/80.
2. **Khớp moment tốt hơn chưa đủ:** trên equal-weight synthetic, mean absolute fitted-moment residual của point chỉ0,01427 so band0,14316, nhưng mean relative ES error point25,31% so band21,72%. Cùng target có mean absolute sampling-error component0,63800 và reference-anchor gap0,21067; posterior-anchor gap của band chỉ0,00174. Các thành phần tương quan và có triệt tiêu, không được gọi là tỷ lệ nguyên nhân cộng lại. Chưa có bằng chứng rằng chỉ cập nhật thêm ngưỡng VaR sẽ sửa phần lỗi chủ đạo.
3. **Không thể giải thích market bằng inactivity đơn thuần:** ECB band chỉ không đổi253/1.537 ngày (16,46%), nhưng vẫn chọn cùng mixture1.198 ngày (77,94%). Floor chi phối99,48% hướng theo trung bình cửa sổ. Sự có mặt của correction không tự chứng minh nó cải thiện forecast.
4. **Forecast trên cùng danh mục chưa thắng:** ECB equal-weight, band−mixture ΔFZ0=+0,003015, CI95%[−0,014281;0,024371]; band−random=+0,002408,[−0,006378;0,012759]. Common historical-SE reference cũng không có chênh lệch rõ. FHS có FZ0 trung bình tốt nhất trong tập phương pháp đã chạy trên cả hai target.
5. **Có tín hiệu allocation thật nhưng có giới hạn:** ECB band pooledES95=0,693913pp, mixture0,715408pp, random0,718419pp. Δband−mixture=−0,021495pp, CI block17[−0,049254;−0,001907]; block5/20 cũng âm, block60[−0,056227;0,000535] còn chứa0. So random, CI âm ở cả bốn block. Đây là development và pointwise CI, không phải xác nhận thắng mới. So historical+SE vẫn chứa0. Point correction còn có ES0,651895pp, tốt hơn band: Δband−point=+0,042018pp,[0,009767;0,075238]. FHS thấp nhất quan sát,0,642585pp.

Do đó không hợp lệ để chọn point chỉ từ bảng allocation, hoặc chọn band chỉ từ synthetic forecast rồi gọi một phương pháp thắng chung. Hai nhiệm vụ và hai giai đoạn cho kết quả khác nhau. Tín hiệu allocation gợi ý correction có thể hữu ích trong một số điều kiện; bằng chứng này chưa xác định được một quy tắc chọn regime đã kiểm chứng.

## Chất lượng thực thi và giới hạn

- **60 tests pass**, bao gồm13 tests mới: tương thích cùng support với frozen calibration, no-update condition, phản ví dụ ES, analytical hinge evaluator cho bốn DGP, decomposition identity, common-target pairing, paired bootstrap và chặn mở lại giai đoạn test.
- Chạy80 synthetic instances/1.680 rows và1.537 ECB origins/32.277 rows; tổng33.957 rows. Hai artifact audits PASS: đối chiếu CSV/window, weights, target gốc, chronology và score; decomposition residual tối đa1,78e−15 synthetic và3,06e−16 ECB.
- Synthetic tất cả correction hội tụ. ECB band2, point1, random5 ngày có finite nonconvergence; vẫn giữ đủ ngày. Không fallback, không score undefined, không base-GMM warning. Hai numerical processes, một numerical thread mỗi process; không gọi đó là independent agents.
- Dùng snapshot synthetic gốc làm input. Refitted scenario surfaces có thể khác lịch sử do nền tảng linear algebra; max ES-surface difference ghi nhận0,674706. Đây không phải sai số của instrumentation trên cùng support. [NumPy giải thích giới hạn tái lập multivariate-normal giữa các builds](https://numpy.org/doc/2.1/reference/random/generated/numpy.random.Generator.multivariate_normal.html). Không đổi sampler sau khi thấy kết quả và không ghi đè snapshot gốc.
- Reverify importer:931/931 files khớp,0 files cần tạo. Frozen market source/config và toàn bộ held-out CSV không thay đổi. Raw và từng ngày market vẫn ở cache local. Không tải thêm nguồn hay mở final test.
- Review độc lập **NOT RUN**: Orca Task `task_d5238cc99f24` thất bại trước dispatch vì `agent_readiness: timeout`; đã release terminal, không thay bằng agent khác ngoài Orca. Các kiểm tra do coordinator thực hiện.
- Bootstrap phụ thuộc giả định gần stationary, nhiều so sánh chưa điều chỉnh; chỉ20 synthetic seed clusters và một panel FX development. Markov oracle, latest-vintage/availability assumption, reference-price và finite-bank giới hạn vẫn còn nguyên.

## Quyết định tiếp theo

**Không thêm v3 bằng cách giảm band hoặc thêm ngưỡng ngay.** Phản ví dụ chỉ chứng minh thiếu điều kiện đủ; decomposition chưa chứng minh threshold drift là vấn đề thực nghiệm chủ đạo. Giữ historical+SE, pure mixture, point và random controls.

**Đúng một next action:** lấy một review độc lập cho phép đối chiếu regularized-maxent và thiết kế một claim về calibration đồng thời trên danh mục/ngưỡng dưới sampling phụ thuộc, trước khi triển khai candidate mới. Review phải chỉ ra khác biệt cụ thể so với Dudík–Schapire, Tang và Duchi–Glynn–Namkoong; nếu chỉ tái đóng gói các khung này thì dừng claim phương pháp mới. Không tự coi ý tưởng này đã có novelty, và không dùng test years đã xem làm fresh confirmation.

Tái lập bằng `rtk proxy bash scripts/reproduce_correction_diagnostic.sh` với cache và `.venv` đã pin. Report generation không đưa raw FX vào Git.
