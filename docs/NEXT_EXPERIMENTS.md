# Kế hoạch chạy tiếp — RiskDecision

**PROPOSED / NOT RUN.** Ưu tiên Q0 -> Q1 -> Q2 -> Q3; được tải/audit dữ liệu song song nhưng không mở final outcomes để chọn method.

## Q0 — Crossed evaluation trước, không train candidate mới

Đọc risk surfaces/CSV lịch sử nếu có; nếu thiếu nhập archive có checksum theo runbook. Tái lập review 07/10 trên 320 stored synthetic tests với nhãn exploratory reuse.

Tách API:
- `forecaster.fit(past)` và `forecaster.risk(weights)`;
- `selector.choose(risk_surface, past_only)`;
- evaluator nhận portfolio đã khóa, future/truth riêng.

Với mỗi forecaster i và selector j, tính forecast của i tại **cùng w_j**. Giữ equal-weight, historical chọn, penalty chọn, APTC chọn và fixed bank. Assert historical/penalty có identical forecast surface; differences chỉ từ decision. Báo separately own-selected pipeline, common-target forecast, true risk/regret và concentration. Không chấm pure forecast bằng FZ trên các loss series khác nhau.

Output dự kiến: `runs/crossed_review/<run_id>/crossed_*.csv`, assertions, report. Tái tính CI customer không áp dụng ở đây: dùng seed cluster/bộ thị trường, các portfolios trong cùng ngày/seed không độc lập.

## Q1 — Optimism-correction baseline trong iid

Đọc OIC v4, nhất là CVaR example và regularity; tạo `OIC_APPLICABILITY.md` trước khi coding. Phân biệt correction cho expected optimized objective với một coherent VaR/ES forecast pair. Không ghép adjusted ES tùy ý với VaR cũ rồi gọi đó là mô hình calibrated.

Baselines tối thiểu: historical, historical+SE decision penalty, pure mixture, APTC frozen, independent split/cross-validation đánh giá post-selection, OIC **khi assumptions phù hợp**. Giữ tổng lượng dữ liệu/information/tuning budget công bằng; split baseline có ít fitting data phải nêu rõ.

Nếu discrete bank285 không phù hợp OIC formula, không giả vờ chạy OIC. Dựng separate continuous CVaR benchmark hoặc đúng formulation trong paper; mọi phương pháp trong comparison đó dùng cùng feasible set. Giữ kết quả bank285 lịch sử riêng, không so regret qua hai không gian tối ưu khác nhau. Kiểm tra nonsmooth hinge, constraints, Hessian/influence-function assumptions và solver accuracy. Smoothing nếu có phải predeclare và có sensitivity.

Pilot fresh synthetic seeds chưa được dùng (kiểm tra manifest local trước khi khóa), một Gaussian và một crash distribution; old seeds chỉ regression tests. Chọn trước primary paired comparison và sample size; không thêm model sau test. Population truth vào evaluator sau decision, không vào training/correction.

Gate: baseline gần nhất đã giải quyết sai lệch thì không claim APTC mới. Không kết luận mọi quant direction dead-end chỉ vì một configuration thua.

## Q2 — Tách temporal dependence và đổi trạng thái

Sau Q1 đúng, mở một dependent stationary setting và một regime-change setting. So rolling sample splitting, blocked validation/bootstrap, statistical volatility/state models và correction tương ứng. Block length/window chọn trong development; rolling windows/overlapping horizons không là iid samples.

Ở Markov simulation, giữ oracle biết state làm diagnostic riêng. Thêm reference conditional on observed history (ví dụ filter dùng DGP params thật) và ghi rõ đây vẫn là parameter oracle, không baseline học từ data. Không cho model dùng hidden state. Mục tiêu là tránh gán phần thiếu thông tin cho algorithmic error.

Chỉ mở ML/DL mới nếu có failure mode tái lập mà OIC/time-aware/statistical baselines chưa xử lý được. Đọc prior art cho mechanism mới; không gọi block bootstrap hay HMM là novelty.

## Q3 — Dữ liệu thị trường chính thức

Chọn ECB reference FX trước. Danh sách cũ: USD, JPY, GBP, CHF, SEK, NOK, CAD, AUD; quote foreign currency/EUR nên lấy reciprocal cho value changes theo EUR. Không tự chọn lại currencies sau risk outcomes.

Lưu terms/citation, retrieval timestamp, raw hash, series, units, observation/public availability convention, missing/holiday handling và dropped dates. Reference factors không phải executable asset returns; không Sharpe/profit khi thiếu spread/carry/funding.

Đề xuất time split để khóa sau khi audit metadata, trước final evaluation: development đến 2015-12-31, validation 2016–2019, assessment 2020–2025. Chỉ metadata được dùng để xác nhận data availability; nếu phải thay split, ghi lý do trước outcomes. Latest-vintage không tương đương full real-time vintage reconstruction.

Runner hiện có là prototype: `stride=5` chỉ lấy thưa ngày dự báo, không horizon 5 ngày. Khóa horizon một kỳ trước; dùng daily eligible dates cho serial VaR testing hoặc nêu giới hạn sparse analysis. Returns đi qua gap dài không tự gọi one-day return; phân biệt forecast information cutoff với thời gian kết thúc loss.

Báo joint VaR/ES score đúng upper-loss sign convention và domain; một realized loss không phải population ES. Same-portfolio forecast scores trước, own-selected realized risk/reserve cost sau. Economic reserve penalty ratios phải được đăng ký và gọi scenario assumptions, không regulation hoặc observed utility.

Bank of Canada FX chỉ secondary source/base-currency robustness, không independent market. Yield curves là extension cần repricing/DV01 và publication lag riêng, không đưa yield levels vào FX-return function.

## Tiêu chí dừng / mở method

Dừng APTC superiority claim nếu equal-information historical/pure mixture/OIC ngang hoặc hơn. Mở một method mới chỉ khi common-target residual error vẫn có ý nghĩa, economic consequence xác định được và prior-art baseline không xử lý được. Không yêu cầu một model thắng mọi metric.

Trong mỗi run giữ configs, hashes, chosen indices, warnings, progress/ETA, resume, timings và paired intervals. Một final report, không hàng loạt README appendices. Không rerun final test để tune cho đẹp.
