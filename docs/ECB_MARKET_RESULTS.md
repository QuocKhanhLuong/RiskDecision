# ECB — kết quả market risk-factor đã chạy

Test: **1538 phiên**, 2020-01-02–2025-12-31, 50754 forecast rows. Stride1, 2 CPU workers, 159.96s. Các bảng dưới đây được tạo trực tiếp từ CSV; artifact audit PASS. Không dùng một realized loss làm true conditional ES.

Protocol SHA256 `741fb298702c77cef204f0aa33f6129b9681d5004a69e076cf7886451a1291be`; commit khóa/push trước test: `9e70a57`. Không tune model sau khi xem validation/test. Đây là internal freeze, không phải external preregistration.

Track A có mean FZ0 thấp nhất mô tả trên equal-weight: **filtered_historical** (-0.611857). Track B có pooled ES95 thấp nhất mô tả: **support_mix50** (0.488726 điểm phần trăm). Thứ hạng quan sát không tự chứng minh ưu thế thống kê hay conditional calibration.

**APTC v2 chưa chứng minh vượt historical+penalty hoặc pure support mixture.** CI95% chênh lệch FZ0 trên cả hai common targets và pooled ES của Track B đều chứa0, ở block chính lẫn sensitivity5/20/60. Không diễn giải thiếu bằng chứng là hai mô hình tương đương.

## Track A — cùng equal-weight exposure

| Estimator | Mean FZ0 ↓ | CI95% FZ0 | Pinball95 ↓ | Breaches / n | Mean predicted ES (pp) | FZ0 undefined |
|---|---:|---|---:|---:|---:|---:|
|filtered_historical|-0.611857|[-0.723837; -0.475756]|0.027603|75/1538|0.567628|0|
|support_band50|-0.472766|[-0.638365; -0.254255]|0.030092|81/1538|0.573134|0|
|equal_weight|-0.468463|[-0.630941; -0.246143]|0.030179|81/1538|0.576726|0|
|historical|-0.468463|[-0.630941; -0.246143]|0.030179|81/1538|0.576726|0|
|historical_se_penalty|-0.468463|[-0.630941; -0.246143]|0.030179|81/1538|0.576726|0|
|support_mix50|-0.465347|[-0.630947; -0.238683]|0.030234|81/1538|0.575357|0|
|aptc_v1|-0.456263|[-0.615336; -0.240699]|0.030300|74/1538|0.556936|0|
|gmm_pooled|-0.451504|[-0.627751; -0.206138]|0.030492|84/1538|0.573137|0|
|student_t_LW|-0.450543|[-0.634875; -0.190061]|0.030392|93/1538|0.555058|0|
|gaussian_LW|-0.441163|[-0.631979; -0.170691]|0.030412|82/1538|0.516750|0|
|gmm_base|-0.320157|[-0.524751; -0.036726]|0.032393|98/1538|0.543698|0|

Historical và historical+SE báo cùng unpenalized ES trên cùng weights; penalty chỉ đổi selector. `equal_weight` trong Track A là historical estimator alias. GMM256 chỉ là diagnostic khác information budget.

## Track A — cùng reference policy từ quá khứ

| Estimator | Mean FZ0 ↓ | Pinball95 ↓ | Breaches / n | Shortfall residual mean (pp) | CI95% residual |
|---|---:|---:|---:|---:|---|
|filtered_historical|-0.774027|0.023366|71/1538|-0.006556|[-0.045500; 0.040217]|
|equal_weight|-0.696842|0.024535|86/1538|0.039859|[-0.011535; 0.101021]|
|historical|-0.696842|0.024535|86/1538|0.039859|[-0.011535; 0.101021]|
|historical_se_penalty|-0.696842|0.024535|86/1538|0.039859|[-0.011535; 0.101021]|
|student_t_LW|-0.694306|0.024600|84/1538|0.014513|[-0.038022; 0.076973]|
|aptc_v1|-0.693697|0.024535|69/1538|0.031701|[-0.015753; 0.087655]|
|support_band50|-0.691586|0.024632|80/1538|0.040057|[-0.010111; 0.100255]|
|support_mix50|-0.689378|0.024689|81/1538|0.038324|[-0.012305; 0.098649]|
|gmm_pooled|-0.689045|0.024746|82/1538|0.033599|[-0.017551; 0.093877]|
|gaussian_LW|-0.688262|0.024645|75/1538|0.048589|[-0.001125; 0.108324]|
|gmm_base|-0.622081|0.025608|94/1538|0.060328|[0.003594; 0.127867]|

Reference policy chọn weights bằng historical ES+SE chỉ từ training. Tất cả estimators nhận cùng weights/loss tại mỗi origin. Residual là v+(L−v)+/0.05−e; mean gần0 là một diagnostic của cặp VaR/ES, không phải bảo đảm.

## Track B — exposure do từng selector chọn

| Selector | Pooled ES95 (pp) ↓ | CI95% ES | Mean loss (pp) | HHI | Mean half-L1 weight change |
|---|---:|---|---:|---:|---:|
|support_mix50|0.488726|[0.442831; 0.536532]|0.001176|0.265398|0.063523|
|historical|0.489432|[0.438445; 0.541546]|0.002705|0.260258|0.005804|
|historical_se_penalty|0.489436|[0.439072; 0.541587]|0.002652|0.262956|0.004769|
|support_band50|0.490895|[0.443200; 0.541378]|0.000922|0.263359|0.061956|
|gmm_pooled|0.493151|[0.440059; 0.547107]|0.003610|0.274202|0.125585|
|filtered_historical|0.497001|[0.445957; 0.547538]|0.000610|0.276839|0.060297|
|gaussian_LW|0.500265|[0.447105; 0.554922]|0.003247|0.257305|0.003111|
|student_t_LW|0.500265|[0.447105; 0.554922]|0.003249|0.257483|0.002705|
|aptc_v1|0.501719|[0.452589; 0.551211]|0.005012|0.264397|0.162113|
|gmm_base|0.586387|[0.489164; 0.712373]|0.003280|0.267651|0.150973|
|equal_weight|0.594379|[0.513757; 0.690226]|0.004867|0.125000|0.000000|

Tail mass: 5% × n = 76.90 observations; fractional boundary atoms được giữ. Đây là pooled out-of-sample policy statistic, không phải conditional ES ground truth. Half-L1 là thay đổi target weights, không gồm drift/transaction costs và không phải turnover giao dịch thực. Không xếp hạng FZ0 của các loss targets khác nhau.

## Candidate so với hai đối chứng — block chính 17

| Track / target | Reference | Metric | Candidate − reference | CI95% |
|---|---|---|---:|---|
|A/equal_weight|historical_se_penalty|fz0|-0.004303|[-0.024080; 0.016182]|
|A/equal_weight|historical_se_penalty|pinball95|-0.000086|[-0.000346; 0.000180]|
|A/equal_weight|support_mix50|fz0|-0.007419|[-0.024125; 0.009201]|
|A/equal_weight|support_mix50|pinball95|-0.000142|[-0.000337; 0.000029]|
|A/historical_se_reference|historical_se_penalty|fz0|0.005256|[-0.007703; 0.017830]|
|A/historical_se_reference|historical_se_penalty|pinball95|0.000098|[-0.000114; 0.000294]|
|A/historical_se_reference|support_mix50|fz0|-0.002208|[-0.012106; 0.008218]|
|A/historical_se_reference|support_mix50|pinball95|-0.000056|[-0.000195; 0.000084]|
|B/own_selection|historical_se_penalty|pooled_es95_pp|0.001459|[-0.016246; 0.016653]|
|B/own_selection|support_mix50|pooled_es95_pp|0.002169|[-0.001894; 0.007024]|

Âm là candidate tốt hơn trên metric tương ứng. CI là pointwise, paired moving-block percentile,5000replicates; không multiplicity-adjusted. Block sensitivity5/20/60 và toàn bộ intervals nằm trong CSV; không chọn block theo kết quả. Approximate stationarity/structural breaks là giới hạn.

## Validation đã chạy trước final test

| Method | A equal-weight FZ0 | B pooled ES95 (pp) |
|---|---:|---:|
|historical_se_penalty|-0.525174|0.469767|
|support_mix50|-0.512661|0.497148|
|support_band50|-0.526901|0.476831|
|filtered_historical|-0.542283|0.491699|

## Diagnostics theo từng năm (tất cả năm test)

| Year | n | Candidate A FZ0 | Historical A FZ0 | Mixture A FZ0 | Candidate B ES | Historical+SE B ES | Mixture B ES |
|---|---:|---:|---:|---:|---:|---:|---:|
|2020|257|0.007164|0.023903|0.025029|0.509621|0.505838|0.509621|
|2021|258|-0.808575|-0.764941|-0.774572|0.314289|0.326740|0.326740|
|2022|257|-0.118195|-0.151302|-0.136270|0.702804|0.680668|0.693182|
|2023|255|-0.706016|-0.713636|-0.703712|0.464980|0.454804|0.464980|
|2024|256|-0.805936|-0.774026|-0.785463|0.364208|0.347510|0.363351|
|2025|255|-0.406326|-0.432441|-0.418627|0.445900|0.474119|0.445900|

Mỗi năm chỉ khoảng12–13tail observations; annual results là mô tả, không là các thử nghiệm độc lập.

## Hội tụ và giới hạn

| Method | Nonconverged dates | Fallback dates | Warning dates | Failed correction steps |
|---|---:|---:|---:|---:|
|historical|0|0|0|0|
|historical_se_penalty|0|0|0|0|
|gaussian_LW|0|0|0|0|
|student_t_LW|0|0|0|0|
|gmm_pooled|0|0|0|0|
|gmm_base|0|0|0|0|
|aptc_v1|3|0|0|3|
|support_mix50|0|0|0|0|
|support_band50|5|0|0|10|
|filtered_historical|0|0|0|0|
|equal_weight|0|0|0|0|

Giữ mọi finite warning output theo quy tắc khóa trước; không xóa ngày bất lợi. Latest-vintage reference changes, không reconstructed real-time release feed; không spread/carry/funding/fees, profit hoặc Sharpe. Không có independent agent/human peer review. Không full cross-evaluation,99% sensitivity,GARCH/DRO,neural hoặc yield-curve experiment.

BoC được báo riêng như source/base-currency sensitivity; không làm tăng số thị trường độc lập.

Artifacts: [`results/local_market/ecb_test`](../results/local_market/ecb_test/), [`validation`](../results/local_market/ecb_validation/). [Nguồn/quyền dùng](MARKET_DATA_MANIFEST.md), [protocol](MARKET_PROTOCOL_FROZEN.md), [lệnh tái lập](MARKET_REPRODUCTION.md).
