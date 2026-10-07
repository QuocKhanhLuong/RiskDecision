# Astra — RiskDecision: crossed evaluation + strongest baseline

Đọc AGENTS.md và docs/RESEARCH_STATE.md -> docs/NEXT_EXPERIMENTS.md -> docs/DATA_AND_REPRODUCIBILITY.md -> docs/SOURCES.md. Không chỉ viết plan; làm phần khả thi trong lượt này. Không train candidate mới để cố thắng.

## Nhiệm vụ lượt này

1. Kiểm tra HEAD, git status, môi trường Mac, artifacts và archive availability. Branch `research/selection-risk-baselines` hoặc tên chưa trùng; không overwrite thay đổi local, không force-push.
2. Khôi phục historical snapshots nếu cần bằng importer/checksum. Main mới chưa tự chứa đủ 931 files. Đừng chạy lại để tạo file rồi gọi original receipt; báo rõ thiếu gì. Giữ measured source v1/v2 nguyên vẹn.
3. Chạy tests hiện có. Implement Q0 crossed forecaster x selector evaluator trong module mới, dùng các risk surfaces/portfolio bank/masks giống nhau. Báo common-target forecast, own-selected pipeline và true selected risk/regret riêng. Assert historical và penalty có identical forecasts trên mọi w. Tái lập crossed summary của review bằng actual artifacts; nếu chỉ có aggregates thì không bịa CI.
4. Đọc OIC v4 và CVaR example bằng primary sources. Viết OIC_APPLICABILITY trước coding: smoothness/nonsmooth CVaR, constraints, discrete argmin, information, estimator output. Không gọi SE penalty là OIC. Nếu cần continuous benchmark, implement riêng với same feasible set across methods; không trộn với bank285 history.
5. Khi applicability gate qua, implement một OIC baseline phù hợp hoặc documented reimplementation, sample-splitting control, unit/synthetic tests. Chạy bounded fresh-seed iid pilot khóa config trước test; report negative results. Nếu gate chưa qua, hoàn thành audit và robust split baseline trước, đánh dấu OIC NOT_RUN, không tự chế formula.
6. Có thể tải/audit ECB bằng loader trong lúc làm Q0/Q1. Check terms/citation/hash/units/timing; kiểm tra metadata, không dùng final-market outcomes cho model search. Audit runner theo Q3 trước full market evaluation. Chưa được gọi prototype stride=5 là five-day forecast.

## Giới hạn

Chưa thực hiện Q2/Q3 full matrix hoặc mở potential directions nếu Q0/Q1 chưa đúng. Không thêm LSTM/Transformer/diffusion. Không so forecast score trên different portfolio losses để gọi superiority. Không dùng hidden DGP state/future outcomes trong inference. No market return/Sharpe claim từ reference FX.

Mỗi stage có config freeze, dataset/source hashes, seed/period, convergence receipt, progress/tqdm/ETA và resume. MPS không cần cho model hiện tại; CPU workers được nhưng không giả independent peer review. Giới hạn compute sau microbenchmark, giữ warnings/cases không đẹp.

## Deliverables

Code mới + tests, `runs/selection_risk/<run_id>/` chứa CSV/manifest/full logs và một RESULTS.md; docs chỉ một báo cáo tổng hợp ở `docs/experiments/` sau kết thúc. OIC applicability note phải phân biệt VERIFIED_SOURCE/ASSUMED/NOT_RUN. Không sửa historical report.

Kết thúc push branch, không tự merge main. Báo tiếng Việt: dữ liệu/file thực có, tests thực chạy, crossed conclusions, OIC có chạy đúng hay chưa, baseline mạnh nhất và phạm vi, những phần NOT_RUN, đúng một next action. Không hứa method novelty hoặc chấp nhận paper.
