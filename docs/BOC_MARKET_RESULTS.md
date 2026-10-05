# BOC — kết quả market risk-factor đã chạy

Test: **747 phiên**, 2023-01-03–2025-12-31, 24651 forecast rows. Stride1, 2 CPU workers, 75.97s. Các bảng dưới đây được tạo trực tiếp từ CSV; artifact audit PASS. Không dùng một realized loss làm true conditional ES.

Protocol SHA256 `741fb298702c77cef204f0aa33f6129b9681d5004a69e076cf7886451a1291be`; commit khóa/push trước test: `9e70a57`. Không tune model sau khi xem validation/test. Đây là internal freeze, không phải external preregistration.

Track A có mean FZ0 thấp nhất mô tả trên equal-weight: **filtered_historical** (-0.661629). Track B có pooled ES95 thấp nhất mô tả: **gaussian_LW** (0.480668 điểm phần trăm). Thứ hạng quan sát không tự chứng minh ưu thế thống kê hay conditional calibration.

## Track A — cùng equal-weight exposure

| Estimator | Mean FZ0 ↓ | CI95% FZ0 | Pinball95 ↓ | Breaches / n | Mean predicted ES (pp) | FZ0 undefined |
|---|---:|---|---:|---:|---:|---:|
|filtered_historical|-0.661629|[-0.783147; -0.512935]|0.026342|41/747|0.527395|0|
|gmm_pooled|-0.604780|[-0.706602; -0.482069]|0.027613|29/747|0.556943|0|
|support_band50|-0.598973|[-0.706227; -0.472911]|0.027648|31/747|0.559347|0|
|equal_weight|-0.598155|[-0.710190; -0.466443]|0.027669|33/747|0.570276|0|
|historical|-0.598155|[-0.710190; -0.466443]|0.027669|33/747|0.570276|0|
|historical_se_penalty|-0.598155|[-0.710190; -0.466443]|0.027669|33/747|0.570276|0|
|support_mix50|-0.597732|[-0.703172; -0.471896]|0.027688|31/747|0.563836|0|
|student_t_LW|-0.590644|[-0.686804; -0.470757]|0.027804|30/747|0.609004|0|
|gaussian_LW|-0.588150|[-0.686604; -0.464169]|0.027993|26/747|0.566440|0|
|aptc_v1|-0.584796|[-0.682870; -0.467000]|0.028048|24/747|0.564539|0|
|gmm_base|-0.582472|[-0.682329; -0.464899]|0.028233|31/747|0.565813|0|

Historical và historical+SE báo cùng unpenalized ES trên cùng weights; penalty chỉ đổi selector. `equal_weight` trong Track A là historical estimator alias. GMM256 chỉ là diagnostic khác information budget.

## Track A — cùng reference policy từ quá khứ

| Estimator | Mean FZ0 ↓ | Pinball95 ↓ | Breaches / n | Shortfall residual mean (pp) | CI95% residual |
|---|---:|---:|---:|---:|---|
|support_band50|-0.671174|0.025439|27/747|0.033188|[-0.060313; 0.175260]|
|support_mix50|-0.668232|0.025491|25/747|0.030457|[-0.062966; 0.172309]|
|gmm_pooled|-0.667185|0.025545|24/747|0.027574|[-0.064352; 0.166987]|
|student_t_LW|-0.654958|0.025716|23/747|-0.005907|[-0.099613; 0.137128]|
|equal_weight|-0.654445|0.025689|28/747|0.030549|[-0.064809; 0.176081]|
|historical|-0.654445|0.025689|28/747|0.030549|[-0.064809; 0.176081]|
|historical_se_penalty|-0.654445|0.025689|28/747|0.030549|[-0.064809; 0.176081]|
|aptc_v1|-0.646449|0.026023|17/747|0.034742|[-0.054291; 0.170560]|
|filtered_historical|-0.643663|0.025638|37/747|0.048861|[-0.047831; 0.192810]|
|gaussian_LW|-0.641022|0.026000|21/747|0.036247|[-0.054991; 0.175924]|
|gmm_base|-0.636220|0.026299|22/747|0.032821|[-0.056606; 0.168807]|

Reference policy chọn weights bằng historical ES+SE chỉ từ training. Tất cả estimators nhận cùng weights/loss tại mỗi origin. Residual là v+(L−v)+/0.05−e; mean gần0 là một diagnostic của cặp VaR/ES, không phải bảo đảm.

## Track B — exposure do từng selector chọn

| Selector | Pooled ES95 (pp) ↓ | CI95% ES | Mean loss (pp) | HHI | Mean half-L1 weight change |
|---|---:|---|---:|---:|---:|
|gaussian_LW|0.480668|[0.384940; 0.620140]|0.000075|0.429710|0.001095|
|student_t_LW|0.480668|[0.384940; 0.620140]|0.000075|0.429710|0.001095|
|support_mix50|0.486381|[0.383855; 0.629371]|-0.003055|0.355099|0.093590|
|support_band50|0.488166|[0.386736; 0.630811]|-0.002051|0.355282|0.094652|
|filtered_historical|0.495533|[0.407588; 0.576866]|-0.004288|0.283467|0.066870|
|historical_se_penalty|0.499929|[0.395558; 0.643282]|-0.001451|0.370181|0.003706|
|historical|0.502504|[0.397585; 0.646426]|-0.000235|0.369221|0.004463|
|gmm_pooled|0.506952|[0.402117; 0.648239]|-0.000566|0.369007|0.162495|
|gmm_base|0.509433|[0.402477; 0.653436]|-0.002126|0.373467|0.223890|
|aptc_v1|0.512248|[0.402867; 0.650491]|0.000688|0.359041|0.140766|
|equal_weight|0.540039|[0.465623; 0.614000]|-0.003338|0.125000|0.000000|

Tail mass: 5% × n = 37.35 observations; fractional boundary atoms được giữ. Đây là pooled out-of-sample policy statistic, không phải conditional ES ground truth. Half-L1 là thay đổi target weights, không gồm drift/transaction costs và không phải turnover giao dịch thực. Không xếp hạng FZ0 của các loss targets khác nhau.

## Candidate so với hai đối chứng — block chính 10

| Track / target | Reference | Metric | Candidate − reference | CI95% |
|---|---|---|---:|---|
|A/equal_weight|historical_se_penalty|fz0|-0.000818|[-0.016371; 0.012239]|
|A/equal_weight|historical_se_penalty|pinball95|-0.000021|[-0.000468; 0.000381]|
|A/equal_weight|support_mix50|fz0|-0.001241|[-0.006109; 0.004430]|
|A/equal_weight|support_mix50|pinball95|-0.000040|[-0.000132; 0.000069]|
|A/historical_se_reference|historical_se_penalty|fz0|-0.016729|[-0.038664; -0.000497]|
|A/historical_se_reference|historical_se_penalty|pinball95|-0.000250|[-0.000470; -0.000038]|
|A/historical_se_reference|support_mix50|fz0|-0.002942|[-0.006806; 0.001536]|
|A/historical_se_reference|support_mix50|pinball95|-0.000052|[-0.000109; 0.000015]|
|B/own_selection|historical_se_penalty|pooled_es95_pp|-0.011763|[-0.028176; 0.003685]|
|B/own_selection|support_mix50|pooled_es95_pp|0.001785|[0.000000; 0.005408]|

Âm là candidate tốt hơn trên metric tương ứng. CI là pointwise, paired moving-block percentile,5000replicates; không multiplicity-adjusted. Block sensitivity5/20/60 và toàn bộ intervals nằm trong CSV; không chọn block theo kết quả. Approximate stationarity/structural breaks là giới hạn.

## Validation đã chạy trước final test

| Method | A equal-weight FZ0 | B pooled ES95 (pp) |
|---|---:|---:|
|historical_se_penalty|-0.458566|0.574827|
|support_mix50|-0.457481|0.582142|
|support_band50|-0.457907|0.588623|
|filtered_historical|-0.433271|0.579002|

## Diagnostics theo từng năm (tất cả năm test)

| Year | n | Candidate A FZ0 | Historical A FZ0 | Mixture A FZ0 | Candidate B ES | Historical+SE B ES | Mixture B ES |
|---|---:|---:|---:|---:|---:|---:|---:|
|2023|248|-0.459173|-0.462610|-0.459173|0.489899|0.525989|0.489899|
|2024|250|-0.686794|-0.695359|-0.683438|0.345602|0.348792|0.340271|
|2025|249|-0.650038|-0.635561|-0.649685|0.614068|0.613064|0.610654|

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
|aptc_v1|0|0|0|0|
|support_mix50|0|0|0|0|
|support_band50|2|0|0|4|
|filtered_historical|0|0|0|0|
|equal_weight|0|0|0|0|

Giữ mọi finite warning output theo quy tắc khóa trước; không xóa ngày bất lợi. Latest-vintage reference changes, không reconstructed real-time release feed; không spread/carry/funding/fees, profit hoặc Sharpe. Không có independent agent/human peer review. Không full cross-evaluation,99% sensitivity,GARCH/DRO,neural hoặc yield-curve experiment.

BoC là source/base-currency sensitivity có currencies trùng ECB, không là thị trường độc lập. Không pool hai nguồn như independent samples.

Artifacts: [`results/local_market/boc_test`](../results/local_market/boc_test/), [`validation`](../results/local_market/boc_validation/). [Nguồn/quyền dùng](MARKET_DATA_MANIFEST.md), [protocol](MARKET_PROTOCOL_FROZEN.md), [lệnh tái lập](MARKET_REPRODUCTION.md).
