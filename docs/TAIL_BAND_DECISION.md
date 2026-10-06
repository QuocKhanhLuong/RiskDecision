# Đã tìm được cơ chế gây lỗi và một đối chứng sửa được trên Gaussian

Ngày 2026-10-06. Parent `29646c9`; khóa code và protocol tại `296457e` trước khi chạy. **Có tiến triển thực nghiệm rõ, nhưng chưa đủ để gọi là thuật toán mới hoặc nâng APTC thành model thắng.**

Lần trước chỉ biết band thiếu bao phủ. Lần này đã can thiệp từng thành phần trên cùng dữ liệu để phân biệt nguyên nhân. Chạy 200 Gaussian IID series mới, 5.400 dòng chẩn đoán và 600 dòng đối chứng ES bị chặn. Ba cỡ calibration 256/1.024/4.096 dùng prefix lồng nhau. Không mở market final test.

## Những gì kết quả thực sự chỉ ra

Trên **cùng 855 hinge means**, với ngưỡng lấy từ base GMM, số seed được bao phủ đồng thời là:

| Calibration n | Plug-in max-t | Thay SE bằng giá trị population, giữ critical value | Fixed-scale max từ mẫu base |
|---|---:|---:|---:|
|256|43/200 = 21,5%|174/200 = 87,0%|194/200 = 97,0%|
|1.024|130/200 = 65,0%|187/200 = 93,5%|188/200 = 94,0%|
|4.096|173/200 = 86,5%|189/200 = 94,5%|186/200 = 93,0%|

1. **Ước lượng ngưỡng không phải điều kiện cần để xảy ra lỗi.** Dùng chính quantile của Gaussian population vẫn chỉ đạt 50/200 = 25% ở n=256 với plug-in max-t. Ngưỡng base GMM đạt 21,5%, mixture tái dùng calibration đạt 22%. Không thể sửa toàn bộ vấn đề bằng việc fit GMM tốt hơn hoặc loại bỏ reuse.
2. **Cách phân bổ độ rộng theo SE là một phần quan trọng.** Ở n=256/base-only, giữ nguyên critical value rồi thay riêng SE làm coverage tăng 65,5 điểm phần trăm; paired CI95% [56,5; 74,0]. Can thiệp cứu 148 seed và mất 17 seed. Đây là bằng chứng cho tác động của phép thay width này, không phải phần trăm nguyên nhân cộng được hoặc một phương pháp triển khai được: population SE là oracle. Mức 87% vẫn thấp hơn nominal95%, Wilson upper bound khoảng 91,0%.
3. **Scale cố định từ mẫu base là đối chứng khả thi tốt hơn ở setting này.** N=256/base-only tăng 75,5 điểm phần trăm, paired CI95% [69,5; 81,5], cứu 152 seed và mất 1. Coverage97% có Wilson95% [93,6%; 98,6%]. Nhưng mean median normalized hinge radius tăng từ 0,249 lên 0,410, khoảng 65%. Vì radius không chia lại theo độ hiếm từng hinge, cách này cấp nhiều độ rộng hơn cho các ngưỡng tail cao. Không được gọi đây là chiến thắng cùng độ rộng hoặc là khoảng ES95 trực tiếp.
4. **Coverage của fixed-scale không tăng đơn điệu theo n:** 97% →94% →93% trên base-only. Cả ba CI còn chứa95%, nhưng chỉ200 replications nên không chứng minh chính xác95% hoặc uniform validity. Không chọn cỡ mẫu/hyperparameter theo bảng này.

Tại n=256/base-only, mean minimum plug-in/population SE ratio trong bank chỉ 0,207; mean median ratio lại 0,964. Chỉ xem SE trung vị dễ bỏ sót một số hướng có scale rất thấp. Tuy vậy, SE ratio tại feature có mean error lớn nhất khi chuẩn hóa bằng **population** SE lại trung bình 1,200. Đây là hai phép chọn feature khác nhau: kết quả không cho phép nói mọi feature sai lớn đều bị đánh giá thấp variance. Bằng chứng mạnh hơn là phép can thiệp paired ở trên, không phải riêng minimum ratio.

Với reused-mixture, “population SE” chỉ là căn của variance của một **fixed hinge** tại ngưỡng đã quan sát, chia n; không phải exact sampling variance có điều kiện của estimator khi ngưỡng cũng được học từ calibration. Oracle control ở nhánh đó chỉ có ý nghĩa chẩn đoán. Base-only dùng mẫu base độc lập nên phép diễn giải fixed-feature conditional-on-base rõ hơn.

## Đối chứng có bảo đảm: đúng, nhưng rộng và đổi target

Định nghĩa riêng `Y_w=clip(L_w,−3σ_w,3σ_w)` với biên biết trước, rồi dựng khoảng ES95 bằng DKW + union bound trên 285 danh mục. Đây là **ES của loss bị chặn**, không phải ES của Gaussian không bị chặn. Dưới IID và bank cố định, khoảng này có bảo đảm ít nhất95% đồng thời, nhờ CDF band kiểm soát mọi threshold và tính đơn điệu của ES. Đây là hệ quả chuẩn, không phải theorem mới.

| n | Coverage đồng thời ES của 285 danh mục | Mean relative ES interval width | Upper endpoint chạm biên support |
|---|---:|---:|---:|
|256|200/200|97,5%|100%|
|1.024|200/200|81,4%|100%|
|4.096|200/200|60,9%|0%|

Gaussian clipping làm population ES giảm khoảng 0,371% trong thiết kế này; không suy ra clipping ít ảnh hưởng với đuôi nặng. Với n256/1024, epsilon DKW lớn hơn tail mass 0,05 nên upper ES bound bằng đúng biên support. Đây là ví dụ cụ thể cho khác biệt giữa **bảo đảm đúng** và **khoảng đủ sắc để hữu ích**. Không dùng các con số width của ES interval để so trực tiếp với normalized hinge radius của bảng trên.

## Đóng góp và quyết định nghiên cứu

Điểm mới học được trong repository là một **failure mechanism đã được can thiệp kiểm tra**: studentization theo mỗi hinge có thể tạo các band quá hẹp ở một số hướng, dù trung vị SE hợp lý; dùng scale độc lập không theo từng hinge thay đổi mạnh coverage/width. Ngưỡng sai, temporal dependence và heavy tails không phải điều kiện cần cho lỗi này. Điều đó thu hẹp bài toán tiếp theo, thay vì thêm model để ép candidate thắng.

Tuy nhiên **unstudentized bootstrap, fixed scaling, oracle ablation và DKW không phải thuật toán mới**. Một recipe đạt97% trên Gaussian không chứng minh novelty, không giải quyết conditional risk và không xác nhận APTC vượt historical+penalty hoặc pure mixture. Kết luận market trước đó giữ nguyên: FHS dẫn điểm số forecast trên common ECB target; pure mixture có điểm ước lượng pooled selected-exposure ES thấp nhất; APTC v2 chưa chứng minh thắng chung.

Prior art được bổ sung trực tiếp: [Li, Peng và Song (2023)](https://www.cambridge.org/core/services/aop-cambridge-core/content/view/36337B7E7E1CDC09EEC7045AD07965C7/S0266466622000275a.pdf/div-class-title-simultaneous-confidence-bands-for-conditional-value-at-risk-and-expected-shortfall-div.pdf) đã làm simultaneous conditional VaR/ES bands trên tail levels bằng location-scale filtering và EVT. Uniformity trên portfolio bank và quyết định được chọn là vấn đề khác, nhưng sự khác biệt này chưa tự chứng minh khoảng trống mới. [Reeve (2024)](https://arxiv.org/pdf/2403.16651) còn có refinement CDF thích nghi theo vùng phân phối; [Maurer–Pontil (2009)](https://www.cs.mcgill.ca/~colt2009/papers/012.pdf) có inference/selection theo variance cho loss bị chặn. Không thể chỉ ghép các thành phần này rồi đổi tên thành đóng góp mới.

**Quyết định:** giữ fixed-scale như một baseline thống kê cần có khi nghiên cứu tiếp, không promote thành APTC v3. Bước có giá trị tiếp theo là kiểm tra độ sắc/coverage dưới tail heterogeneity và phụ thuộc, với scale chỉ được học từ quá khứ, trước khi xét tác động đến portfolio selection. Nếu muốn claim mới, cần một cơ chế hoặc định lý khác biệt xử lý phần này, cộng bằng chứng hơn các baseline đã biết. Đây là đề bài còn mở, chưa phải kết quả được xác nhận trong lần chạy hiện tại.

## Kiểm chứng, giới hạn và tái lập

- **80 tests pass**; hai công thức Gaussian hinge moments được kiểm bằng numerical quadrature, bootstrap plug-in khớp runner cũ, kiểm partial-atom ES và DKW support saturation.
- Audit tái tạo đúng 200 input arrays, tính lại 81.000 metrics và 600 bounded-control rows. Refit seed71000/71199 cho GMM, anchors và toàn bộ radii khớp chính xác. 246 giá trị số trong báo cáo được parse độc lập rồi đối chiếu CSV. Không GMM warning/nonconvergence.
- 931/931 historical files còn nguyên byte. Frozen market, correction và coverage audit trước đó không đổi. Raw FX và per-case arrays local; chỉ publish aggregate.
- Chỉ một Gaussian IID DGP/covariance và200 seeds; nhiều interval là pointwise chưa điều chỉnh multiplicity; oracle controls không triển khai được; chưa chứng minh fixed-scale validity tổng quát hoặc lợi ích forecast/portfolio.
- **NOT RUN:** heavy-tail/dependence extension của recipe mới, market test, candidate v3, independent review. Orca Codex khởi động vào updater rồi thoát; retry lỗi `agent_readiness: timeout` trước khi task được giao. Updater đã đổi CLI từ0.160.0 sang0.160.1; không có review agent hoàn thành. Terminal retry đã release, shell đầu được Orca giữ với`identity_unproven`. Không dùng CPU processes như independent reviewers.

[Báo cáo đầy đủ](TAIL_BAND_RESULTS.md), [protocol](TAIL_BAND_PROTOCOL.md), [CSV](../results/tail_band_v1/coverage.csv), [artifact audit](../results/tail_band_v1/audit.json).

```bash
rtk proxy bash scripts/reproduce_tail_band.sh
```

Lần thực thi đầu tạo đủ 200 cases mất 44,51 giây trên M4 Pro/RAM24GiB,2 numerical processes. Receipt đầu được giữ nguyên khi resume cache; không gọi thời gian đọc cache là thời gian chạy thí nghiệm mới.
