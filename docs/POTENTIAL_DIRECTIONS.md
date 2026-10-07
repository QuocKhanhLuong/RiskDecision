# Hướng tiềm năng — chưa phải method đã chốt

Hướng chính đã chọn là evaluation/correction dưới selection và dependence, theo [NEXT_EXPERIMENTS](NEXT_EXPERIMENTS.md). Chỉ mở thêm một nhánh sau gate.

| Hướng | Cơ chế có thể nghiên cứu | Đối thủ mạnh | Khi nào đáng mở |
|---|---|---|---|
| P1 — post-selection risk assessment theo thời gian | Ước lượng/correction optimistic bias với rolling dependent observations, phân biệt selection và drift | OIC, time-aware sample splitting, blocked validation, regularized CVaR | Sau Q1/Q2 có lỗi dư rõ. Việc thêm block bootstrap đơn thuần không phải novelty |
| P2 — state-conditioned tail-risk learning | Học phân phối conditional theo thông tin quá khứ, không theo latent-state truth không quan sát | HMM/GARCH/FHS và filtered Student-t/copula; cùng information set | Khi common-target failure gắn với thay đổi state. Neural chỉ dùng khi giải quyết một limitation cụ thể, không thay backbone để kiếm số đẹp |
| P3 — support-aware scenario repair | Tạo/kiểm tra support còn thiếu thay vì chỉ reweight những scenarios đã có | Pure historical mixture, entropy pooling, DRO và decision-focused scenario generation | Khi chẩn đoán cho thấy support thiếu gây lỗi; có ablation tách support, thêm data và optimization. Không mở APTC v3 trước baseline gate |

Một extension bổ trợ là kiểm tra khả năng tối ưu trên continuous weights thay finite bank; đó là độ tổng quát/thí nghiệm, không tự thành thuật toán mới. Ràng buộc concentration/leverage và cost assumptions phải có lý do kinh tế, chọn trước test.

Nội dung kinh tế cần có: rủi ro bị đánh giá thấp làm nhu cầu dự phòng sai bao nhiêu; bảo thủ thêm tốn bao nhiêu; quyền lựa chọn danh mục/ràng buộc nhà đầu tư thay đổi độ lạc quan ra sao. Không thêm return forecasting alpha nếu nó làm trộn nguồn lỗi.

Gate novelty cho bất kỳ nhánh nào: nearest paper + exact technical difference + measurable failure + simple baseline + falsification. Chưa có evidence cho new theorem, SOTA hoặc lợi nhuận đầu tư.
