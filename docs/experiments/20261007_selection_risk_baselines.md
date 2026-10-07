# Selection-risk baselines — kết quả thực chạy 07/10/2026

**Kết luận:** Q0 tái lập được điểm ước lượng crossed review từ original artifacts;
không có bằng chứng APTC tốt hơn historical trên các common targets lịch sử.
Q1 fresh iid pilot cho thấy independent split cải thiện đánh giá **frozen objective**
trên cùng danh mục/ngưỡng do nửa A chọn. Kết quả này chưa phải cải thiện ES forecast
cho danh mục được fit bằng đủ 512 observations. **OIC NOT_RUN**, applicability gate
cho discrete bank chưa qua. Không mở APTC variant mới.

Branch: `research/selection-risk-baselines`; base sau pull:
`f6dcffdf6ab7e22a9246aadb17df437e3aae8c6e`.
Run: [`runs/selection_risk/20261007_selection_baselines/`](../../runs/selection_risk/20261007_selection_baselines/RESULTS.md).
Mọi số bên dưới là synthetic, không phải market performance hay phần trăm mất vốn.

## VERIFIED — dữ liệu và phần thực chạy

- Trạng thái Git đầu lượt sạch; không có thay đổi tracked/untracked cần stash.
  Các thư mục run/data bị ignore từ những lượt cũ được giữ nguyên.
- Hai ZIP trong `Downloads/RiskDecision_Local_Import_Bundle` khớp đúng size và
  SHA256 trong `archives_manifest.json`. Checkout có 31 files khớp; còn thiếu 900
  archive members. Importer gốc nhập **931 files** vào `historical_snapshot/` riêng,
  không ghi vào packages lịch sử. Có 404 NPZ v2 (320 test, 80 validation, 4 smoke)
  và 60 NPZ v1; Q0 chỉ đọc 320 test v2, không rerun các nhiệm vụ archive.
- Q0 thực tính **11.200 crossed rows** từ 320 instances, 5 forecast labels ×
  7 targets (6 selectors + bank mean), 4 families, **80 seed clusters**.
  Historical/penalty identity được assert cho cả VaR và ES trên toàn bộ bank285.
  Chosen indices, ES, error, regret và HHI khớp CSV lịch sử cho 6 selectors.
- Q1 fit các baseline đã khóa trên **128 fresh instances**, 2 iid families ×
  **64 paired seed clusters**, seeds `2026107000:2026107064` (stop exclusive).
  Local audit 7.271 source/config/CSV/manifest files không thấy seed collision;
  không chứng nhận các runs bên ngoài chưa được cung cấp. Microbenchmark dùng
  seed riêng `2026107999`, không tham gia inference.
- **26 tests cũ pass** trước implementation; **41 tests pass** trên cây kết hợp
  (15 tests/cases mới). Có test chống sai bank/mask, sai forecast identity,
  holdout làm đổi first-fold decision, sai frozen-objective target,
  pseudoreplication, checkpoint/config/input corruption và Q0 refit ngoài ý muốn.
- Verifier riêng kiểm lại toàn bộ 14.272 crossed rows, 512 split rows và 1.235
  summary means bằng array arithmetic; numerical integration của survival tail
  khớp frozen-objective truth với sai lệch tối đa `3.32e-12`. Primary paired CI
  được tính lại và khớp. Đây là software/numerical verification, không independent
  peer review. **39 tracked historical/archive/importer files và 931 imported
  files vẫn nguyên hash**.

Nguồn bằng chứng: [preflight](../../runs/selection_risk/20261007_selection_baselines/preflight.json),
[tests](../../runs/selection_risk/20261007_selection_baselines/combined_tests.log),
[verification](../../runs/selection_risk/20261007_selection_baselines/verification.json).

## Q0 — exploratory reuse, không phải held-out test mới

Mean absolute relative ES error (%), cùng portfolio cho từng hàng:

| Target | Historical | APTC frozen | APTC − historical, điểm % [95% CI] |
|---|---:|---:|---:|
| Equal-weight | 17,1733 | 17,2716 | +0,0983 [−0,8381; +0,8910] |
| Historical chọn | 14,6447 | 14,7432 | +0,0986 [−0,5380; +0,6742] |
| Historical + SE chọn | 14,2981 | 14,4046 | +0,1064 [−0,5270; +0,6555] |
| APTC chọn | 14,6085 | 15,0098 | +0,4013 [−0,3755; +1,0556] |
| Trung bình bank285 | 15,9205 | 15,8298 | −0,0906 [−0,8750; +0,5687] |

Bootstrap 10.000 resamples của seed clusters, average 4 families trong seed trước
resampling. Không tính 285 portfolios thành 285 thị trường độc lập. Toàn bộ 7
APTC-minus-historical overall paired intervals chứa 0. Family-specific tables vẫn
được giữ; Markov truth lịch sử biết hidden final state nên chỉ là oracle diagnostic.

Own-selected pipeline và chất lượng decision được tách riêng:

| Pipeline | Relative ES error % | True selected ES, synthetic units | Bank regret % | HHI |
|---|---:|---:|---:|---:|
| Historical | 14,6447 | 1,65662 | 3,1126 | 0,28350 |
| Historical + SE | 14,2981 | 1,65831 | 3,5024 | 0,29736 |
| Pooled GMM | 15,4323 | 1,66069 | 3,5521 | 0,28994 |
| Pure mixture 50/50 | 15,0804 | 1,65901 | 3,2711 | 0,27963 |
| APTC frozen | 15,0098 | 1,66028 | 3,3009 | 0,27688 |

Penalty có own-selected error thấp hơn nhưng regret cao hơn historical trong
Q0; nó không tạo forecaster mới. Regret là so với population-best trong cùng bank.

**REPORTED:** `RESEARCH_STATE.md` ghi review ZIP/CSV và CI
`[−0,5291; +0,6436]` cho penalty target. Review ZIP không tìm thấy tại Downloads/
import bundle đã kiểm; không có original bootstrap config của review. Lượt này
tái lập điểm ước lượng +0,1064166 từ NPZ và các số làm tròn ở bảng review; CI mới
dùng bootstrap seed đã đăng ký `871031`, không gọi là exact reproduction của CI cũ.

Q0 giữ nguyên mọi case. Original diagnostics có 5 nonconverged components:
`support_point50` 2; `support_band50`, `filtered_support_band50`, `aptc_v1` mỗi loại 1.
Trong đó chỉ `support_band50` thuộc candidate được chấm trong ma trận này.
Các trạng thái này **đọc từ original diagnostics**, không phải refit mới.

## Q1 — independent split và frozen baseline pilot

[Config](../../selection_risk/configs/pilot.json) khóa trước generation. 512 past
observations, 8 assets, long-only, cap .5, bank285; historical, SE selector,
pure mixture50 và support-band50 dùng nguyên settings v2. Không chọn lại model
bằng kết quả Q0/pilot. Population parameters chỉ vào evaluator sau khi tất cả
weights/thresholds đã khóa.

Primary so sánh trên **cùng `(w_A, v_A)`** fit bởi 256 samples A:
resubstitution trên A với mean `v_A + max(L(w_A)−v_A,0)/.05` trên 256 samples B.
Truth là population expectation của objective tại threshold đã khóa, không phải
population ES sau khi tối ưu lại threshold. Kết quả:

| Endpoint, A→B | Resubstitution A | Independent B |
|---|---:|---:|
| Mean signed relative objective error % | −10,6666 | −0,7785 |
| Mean absolute relative objective error % | 13,3931 | 9,5939 |
| Mean squared relative objective error | 0,0281389 | 0,0152285 |

**Primary paired delta (split − resubstitution): −0,0129103**,
95% seed-cluster CI **[−0,0196134; −0,0066672]**, dimensionless squared relative
error. Bias CI của independent B: [−2,9172%; +1,5057%]. Gaussian bias −0,0834%;
crash bias −1,4736%; cả hai CI chứa 0. Đây là bounded pilot, không có power-based
superiority claim cho một phương pháp tổng quát.

Two-fold diagnostic average signed relative error −0,4375%; reverse fold B→A
−0,0965%. Hai folds không là hai thị trường độc lập. Trung bình squared errors
của hai policies không phải squared error của một danh mục trung bình.

Chi phí thông tin rõ ràng: split dùng 256 fitting + 256 evaluation, tổng 512.
Nó không đánh giá decision full-512 mà không bias. A-selected mean regret 4,0002%,
cao hơn điểm ước lượng 2,3640% của historical full-512. Mean gap giữa frozen
objective và population ES là 0,03291 synthetic units. Holdout tự tính quantile
có relative ES error 9,2786%; diagnostic này không hưởng lập luận unbiased cho
fixed-threshold sample mean.

Full-512 baseline own-selected error / bank regret:

| Pipeline | Relative ES error % | Bank regret % |
|---|---:|---:|
| Historical | 8,0552 | 2,3640 |
| Historical + SE | 7,8309 | 2,1452 |
| Pure mixture50 | 8,0812 | 2,4025 |
| APTC frozen | 8,5186 | 2,5133 |

Common-target kiểm tra APTC-minus-historical: penalty-selected +0,3295 điểm %,
CI [−0,1598; +0,8330]; bank mean +0,6624, CI [+0,1847; +1,1922]; APTC-selected
+0,8156, CI [+0,2783; +1,4088]. Đây là secondary exploratory intervals chưa
hiệu chỉnh multiplicity, không dùng để chọn model mới. Giữ kết quả âm đối với
APTC. Fresh GMM/APTC diagnostics ghi **0 nonconverged components, 0 warnings**.

**Baseline mạnh nhất trong phạm vi đã đo:** historical + SE có own-selected error
điểm ước lượng thấp nhất trong các full-512 pipelines đã khóa; điều đó không chứng
minh forecaster tốt hơn. Independent split là control trực tiếp có bằng chứng
primary cho post-selection **frozen-objective evaluation**, với fitting budget
nhỏ hơn. Không gộp hai nhận định thành một bảng xếp hạng chung.

## OIC, market gate và phần chưa chạy

[OIC_APPLICABILITY](../../selection_risk/OIC_APPLICABILITY.md) được viết trước
implementation, phân biệt VERIFIED_SOURCE / ASSUMED / NOT_RUN. Đã đọc primary
[arXiv v4](https://arxiv.org/html/2306.10081v4), gồm CVaR Example 6.4, regularity,
constraints và numerical accuracy; lưu URL, retrieval time và hash tại
[source receipt](../../runs/selection_risk/20261007_selection_baselines/source_receipt.json).
Discrete bank chưa có influence-function/curvature derivation được xác minh;
**không implement công thức OIC giả hoặc cộng SE vào ES rồi giữ VaR cũ**.

**VERIFIED bằng static code read:** prototype `run_market_risk.py` lấy thưa forecast
indices với `stride=5`, còn target là một adjacent retained-observation return;
không phải five-day horizon. `past_window(..., gap=1)` giữ 512 returns và bỏ một
observation trước target. `returns_pp` không nhận dates nên không phân biệt gap
cuối tuần/ngày thiếu. Loader lấy reciprocal ECB, complete cases/no fill nhưng
không ghi từng dropped date hay thực dựng publication/vintage history. Own-selected
FZ rows có portfolio losses khác nhau, chưa đủ để xếp hạng pure forecasters.

**NOT_RUN:** OIC correction/continuous benchmark; smoothing sensitivity; Q2
stationary-dependent/regime matrix; Q3 full market assessment; new ECB download
và current terms recheck; DCC/GARCH/DRO matrix; economic reserve utility;
neural/variant search. Không mở prior market outcome metrics để chọn model;
local run folders cũ chỉ được inventory/hash phục vụ provenance/seed audit.

## Runtime, resume và publication

Mac arm64, macOS 26.2; Python 3.13.15; NumPy 2.3.5, SciPy 1.17.0,
scikit-learn 1.8.0, pytest 9.0.2; thêm tqdm 4.67.1, CPU single-thread settings.
Q0 3,28 s; micro 2 cases fit 0,203 s, estimated pilot có margin 19,50 s < cap 900 s.
Pilot total case compute 11,74 s; completion session 12,50 s (125 new + 3 resumed).
Logs, timestamps, progress/ETA, config/source/data hashes và warnings nằm trong run.

Thử dừng sau 3 cases rồi resume hoàn tất; full resume sau đó skip 320 Q0 và 128
pilot cases, **0 refit**. 128 arrays giữ nguyên bytes. Trong 138 CSV/array files,
137 giữ nguyên hash; Q0 raw CSV đổi thứ tự cột khi reload JSON, **11.200 record
values và record order giữ nguyên** khi so bằng tên cột. Giới hạn định dạng này
được ghi rõ ở [resume receipt](../../runs/selection_risk/20261007_selection_baselines/resume_verification.json).

Branch chứa code/tests, compact synthetic CSVs, manifests, diagnostics và full
stage logs. Original snapshot/NPZ mới/HTML nguồn vẫn local; hashes và lệnh tái lập
được công bố. Không commit market raw/cache/credentials, không sửa hoặc merge main.
Để resume cần giữ toàn bộ local `cases/` và `arrays/`; các aggregate receipts trên
remote tự chúng không thay thế được checkpoint. Source fingerprints khóa tree
thực chạy dù commit được tạo sau khi hoàn tất.

**Đúng một next action — PROPOSED:** dựng benchmark continuous CVaR riêng với
same capped simplex cho mọi baseline và audit influence-function/curvature/KKT
để quyết định triển khai OIC; chưa mở Q2/Q3 hoặc method mới.
