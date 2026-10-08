# Full synthetic validation — hoàn tất 2026-10-08

**Đã chạy đủ ma trận full:** 240 computational cases, 30 phép đo bộ nhớ và
3,072 policy histories mới trên 24 public dictionaries/portfolio banks độc lập.
Thuật toán own-knots cho cùng kết quả với đối chứng chính xác và nhanh hơn rõ
ở bank lớn. **Policy kết hợp vẫn chưa hơn baseline điểm; chưa xác lập novelty.**

Branch `research/compositional-risk-full`, base
`155326bee39ae947ca688e108234bb5fad4cc197`. Đã fetch main tại
`f6dcffdf6ab7e22a9246aadb17df437e3aae8c6e`, vốn là ancestor của base.
Worktree bắt đầu sạch; **755 file tracked cũ giữ nguyên SHA-256**, bao gồm
pilot/config/code/báo cáo lịch sử. Không merge main, không force-push.

## Phạm vi “full” và protocol trước chạy

Theo yêu cầu mới “chạy full đi”, mở rộng synthetic benchmark hiện tại thay cho
next-action-only literature gate ở báo cáo trước. Đây là **full của ma trận
đã đăng ký**, không phải full market backtest hay kiểm chứng mọi DGP. Decision
và hashes nằm trong [start receipt](../../runs/compositional_risk_full/20261008/start_receipt.json),
thiết kế trong [protocol](../../bank_regret_full/PROTOCOL.md).

Giữ nguyên toàn bộ 10 policies và tham số từ `bank_regret`: observed context,
window512, dictionary32 scenarios × 8 assets, bank128, alpha=.05, conjugate
priors .5, 4 posterior draws + nominal world, interval q theo posterior
quantiles .05/.95, chi phí .001 × turnover, component shift tại448 trong
window512. Không thêm model hoặc chỉnh tham số sau khi thấy pilot.

Mỗi trong24 bank có64 histories/family, hai families stationary và component
shift: **1,536 histories/family**. Seed namespace mới `...full-20261008-v2`,
khác pilot và development/tests. Một software-test pass ban đầu đã nội bộ tạo
một history của prototype namespace v1; không xuất effectiveness. Trước freeze,
đã tách v2 assessment và `/unit-tests`, không dựa trên policy score để chọn seed.

Mỗi bank là một cluster độc lập; 64 histories bên trong không được dùng thay
cho independent-bank replication. Các phương pháp chia sẻ dữ liệu, bank,
world set và cost convention. Fit không nhận truth/future; decision hash khóa
trước evaluator. True conditional ES được tính từ DGP evaluator, không lấy
một future realized loss làm ES truth. Đây là observed-context categorical
simulation, không phải latent-state HMM equally informed hoặc market data.

Inference lấy trung bình trong bank, rồi trung bình24 bank; bootstrap10,000
lần ở cấp bank, từng family riêng. Primary: shared_full−rectangular_full;
secondary: shared_full−point. Có CI95% và CI97.5% cho hai primary family
contrasts (Bonferroni nominal95% đồng thời). Bootstrap hữu hạn không được bảo
đảm exact coverage. Sample size bị giới hạn compute; không có formal power
claim, không interim outcome inspection hay chọn winner để triển khai.

## RUN / VERIFIED: compute và độ chính xác

Full factorial M={8,32,128,512,2048}, S={16,64,256},
alpha={.01,.05,.2,1}, 4 replicates/cell:240 cases. Với **mọi alpha**, hai
replicates dùng q interval đầy đủ và hai dùng subinterval; không còn coupling
alpha/interval type của pilot. Mỗi case time ba lần/solver với thứ tự xen kẽ.
Timing chạy tuần tự, không có policy pool đồng thời; BLAS thread count=1.

Đối chứng là **cùng global lower hull**, nhưng đánh giá mỗi action tại hợp
các knots toàn bank. Own-knots chỉ cần các điểm đổi ngưỡng của chính action.
Toàn vector regret, witness và argmin đều được kiểm tra. Không dùng coarse
grid hay chỉ một pairwise baseline chậm để tạo speedup.

Ô lớn nhất M=2048, S=256; số dưới là median của **bốn paired runtime ratios**
union/own, mỗi ratio dùng median ba lần gọi trên cùng input:

| Tail probability alpha | Median paired speedup | Khoảng min–max của4 replicate ratios |
|---|---:|---:|
| .01 | **1.831×** | 1.438–2.188× |
| .05 | **2.726×** | 1.050–3.187× |
| .20 | **4.178×** | 1.951–4.886× |
| 1.00 | **0.998×** | 0.992–4.861× |

Không có speedup đồng đều: 46/60 cells có median paired ratio>1, 14/60<1;
toàn matrix nằm trong0.976–4.178×. Alpha=1 là mean-risk case, median gần hòa.
Có runtime outlier lớn được giữ nguyên: alpha=1/replicate3 có local times
[3.304,.571,.577] giây, union [3.318,2.804,.632] giây; replicate1 cả hai
solver khoảng3.3 giây trong khi replicate0 khoảng.58 giây. Nguyên nhân
biến động hệ thống chưa đo. Không retime rồi thay kết quả thuận lợi hơn.
Vì vậy bảng dùng paired ratios, **không chia hai marginal medians** và không
claim hardware-independent throughput. Các thời gian/vectors gốc và đủ60 cells
có trong [benchmark CSV](../../runs/compositional_risk_full/20261008/benchmark_summary.csv).

Tại2048×256/alpha=.2, own-risk queries là9,117–31,459, đối chứng là
10,287,104–56,043,520 tùy replicate. Giảm query count không được gọi là tỷ lệ
giảm wall time. Chứng minh O(K log K) time/O(K) space mỗi world là kết quả
phân tích cho finite support, shared q, fixed costs; không suy từ timings.

**Độ chính xác:**

- 240/240 benchmarks đạt; max regret-vector error **6.66e-16**, witness error
  **3.55e-15**; **0 selected-index disagreements**.
- 3,072/3,072 policy histories được đối chiếu toàn bộ regret vector trên cả5
  fitted worlds với union-knots baseline: max error **4.34e-18**, **0 choice
  disagreements**. Đây là same-data software verification, không3072 confirmations
  độc lập về algorithmic novelty.
- 30 memory runs khớp input hash, selected index và regret-vector hash với
  đúng solver của computational case tương ứng.

Mỗi memory run dùng fresh subprocess, đo **process peak RSS gồm Python/imports,
inputs và solver**, không phải isolated native allocation. Ở2048×256/alpha=.2:
own **184.04 MB**, union **187.06 MB** (MB=10^6 bytes); pre-input peak khoảng
97.1 MB. Không có memory gain lớn ở phép đo này. Baseline cũng không lưu toàn
bộ M×K risk matrix; không claim đã cải thiện bậc memory complexity so baseline.
Đủ30 measurements ở [memory CSV](../../runs/compositional_risk_full/20261008/memory_summary.csv).

## RUN / VERIFIED: chất lượng policy trên24 banks

Mean true conditional ES+cost regret ×10,000; **thấp hơn tốt hơn**. Các số
là synthetic loss units đã scale, không realized return, profit hay trading bps.
Harmful switch nghĩa là true ES+cost cao hơn giữ equal-weight incumbent.

| Frozen policy | Stationary regret | Shift regret | Harmful switches stationary / shift (mỗi family n=1536) |
|---|---:|---:|---:|
| Point posterior | 0.54619 | 6.39815 | 111 / 646 |
| Shared full | 0.66897 | 6.51031 | 119 / 649 |
| Shared endpoints | 0.66855 | 6.51031 | 119 / 649 |
| Rectangular full / absolute worst-case ES | 1.19818 | 5.97819 | 258 / 644 |
| Rectangular endpoints | 1.19781 | 5.97819 | 258 / 644 |
| Nominal components only | 0.54398 | 6.35446 | 110 / 642 |
| Fixed q | 0.65480 | 6.42999 | 115 / 643 |
| Ignore cost when selecting | 2.08202 | 7.75408 | 504 / 769 |
| Historical unconditional | 2.70370 | 3.71098 | 460 / 393 |
| Keep incumbent | 6.65188 | 7.98153 | 0 / 0 |

Các policy được báo cáo đầy đủ, không chọn một ablation làm model thắng sau
khi xem test. Shared full switches1,400/1,536 và1,396/1,536, mean assumed cost
0.00025033 và0.00024760, lần lượt stationary/shift. Không có measured fees,
reserve utility hoặc multi-period turnover evidence.

Paired bank-level contrasts ×10,000, **âm có lợi cho shared**:

| Contrast | Mean | CI95% | CI97.5% cho primary | Banks shared tốt hơn / kém hơn |
|---|---:|---:|---:|---:|
| Stationary: shared−rectangular | −0.52921 | [−0.76213, −0.31187] | [−0.79441, −0.28361] | 19 / 5 |
| Shift: shared−rectangular | +0.53212 | [+0.03090, +1.01340] | **[−0.02332, +1.07987]** | 7 / 17 |
| Stationary: shared−point | **+0.12278** | **[+0.06163, +0.18544]** | — | 4 / 20 |
| Shift: shared−point | +0.11216 | [−0.09128, +0.30786] | — | 10 / 13, hòa1 |

Shared policy thắng rectangular khi stationary, nhưng thua simpler point
policy. Khi shift, mean primary contrast bất lợi; CI95% nằm phía dương nhưng
**CI điều chỉnh hai primary comparisons chứa0**. Không gọi đó là xác nhận
significance sau điều chỉnh. So point ở shift chưa phân biệt được rõ.
Heterogeneity giữa banks được giữ trong [bank effects](../../runs/compositional_risk_full/20261008/bank_effects.csv),
không pool pilot cũ thành thêm24 bank độc lập.

Full/endpoints chỉ đổi shared choice ở **1/1536 stationary histories** và
**0/1536 shift histories**; rectangular tương ứng1 và0. Factorial interaction
stationary = **4.74e-9** raw regret, CI95% [−1.12e-7,+1.26e-7]; shift bằng0
trên toàn mẫu. Chưa có bằng chứng lợi ích cộng hưởng. CI0 ở shift không phải
population equivalence theorem; exact knots có ý nghĩa tính toán nhưng ít ảnh
hưởng decision trên những banks này.

Finite-stress certificate thấp hơn true selected regret ở **219/1536 (14.26%)**
stationary và **1241/1536 (80.79%)** shift histories. Đây không phải violation
của finite-world computation theorem: fitted world set không có true-law
coverage guarantee. Không gọi policy là calibrated safe switching.

## Forecast khác selection; bằng chứng khác pilot

Mọi same-fit policy có cùng nominal common-bank forecast vector. Lựa chọn khác
nhau không tạo forecaster mới. Common-bank MSE:

| Forecast | Stationary | Shift |
|---|---:|---:|
| Observed-context posterior nominal | 2.5657e-7 | 2.9578e-6 |
| Historical unconditional | 2.1045e-6 | 2.2518e-6 |

Conditional fit giúp stationary nhưng kém historical khi shift trong DGP này.
Regret không được so qua different banks để suy ra forecaster superiority.
Khác với pilot một-bank, incumbent không có mean shift regret thấp nhất ở
full24-bank run; không bảo vệ diễn giải tổng quát từ một bank cũ. Pilot chỉ là
[READ / REPORTED context](20261008_compositional_risk_policy.md), không rerun
hay gộp vào CI lượt full.

## Execution, kiểm chứng và publication

Fingerprint trước chạy:
`da6dbaecb183f1849c4a5dc29980295ace5bb4a6646022ea3db6f3689668f444`.
Toàn bộ14 file nguồn/config/protocol trong manifest, Python binary, versions,
platform và thread environment được khóa. Mac ARM64 CPU, Python3.13.15,
NumPy2.3.5, SciPy1.17.0;
policy dùng4 CPU processes, **không gọi multiprocessing là independent review**.

| Hoạt động thực chạy | Kết quả / wall time |
|---|---|
| Active test suites `tests quant_research_v2/tests` | **153 passed**, 6.67s |
| Preflight60 strata +4 separate development policies | PASS, 22.17s; projected990.88s |
| Partial5 cases | Exit3 đúng thiết kế; 2.35s |
| Resume thêm3337 tasks | Exit0; **681.87s** |
| Benchmark stage của full resume | 403.51s (ngoài5 cases partial) |
| Memory stage | 18.54s |
| Policy stage | 259.71s |
| No-op resume | 3342 resumed, **0 new cases**, 6.41s |
| Deep verification | PASS, 20.99s |

Main assessment partial+full mất **684.22s ≈11.4 phút**, không gồm code authoring,
tests, preflight hay verification. Sum of case wall times1458.81s không phải
elapsed wall time vì có concurrency. Numerical warnings ghi nhận: **0**;
warning về finite-world coverage vẫn nằm trong từng policy checkpoint.

Đã giữ log collection failure ban đầu: `pytest` không chỉ rõ paths quét cả
snapshot lịch sử có module trùng tên và dừng trước execution. Sau đó chạy
đúng explicit active suites; không xóa/sửa snapshot để làm tests pass. Intermediate
127-test pass không được cộng vào153. Archive không trở thành rerun backlog.

No-op resume kiểm tra payload/freeze/task/decision hashes, không refit mọi case.
Verification riêng tái tạo **toàn bộ input recipes/observed histories/truth**,
recompute summary, refit cố định first2 histories/bank/family (**96 histories**),
thực hiện **373 independent risk-envelope LP solves**, max error **2.60e-18**.
Đã xác nhận **5/5 và3342/3342 checkpoint giữ nguyên bytes**, 30 memory cases
khớp benchmark và755 protected files không đổi. Verification dùng cùng cases,
không là independent scientific replication hay human peer review.

Code/run commands: [bank_regret_full](../../bank_regret_full/README.md).
Artifacts, gzip checkpoints, logs/ETA và CSVs:
[run index](../../runs/compositional_risk_full/20261008/RESULTS.md).

## Claim status và đúng một next action

**VERIFIED / RUN:** đủ registered full matrix; exact computational reduction
được kiểm tra trên bank lớn hơn, đo tốc độ/RSS và policy trên24 independent banks;
negative/mixed outcomes, seed hygiene, test error và runtime outliers giữ nguyên.

**READ / REPORTED:** chứng minh own-knot/shared-hull và prior-art search của
báo cáo trước. Không đọc thêm toàn văn Fan/Huang trong lượt chỉ định chạy full;
không nâng abstract-level evidence thành full algorithm audit.

**PROPOSED:** giữ own-knot/shared-hull specialization làm ứng viên đóng góp
tính toán. Speedup không tự chứng minh priority. Không claim policy tổng hợp
mới tốt hơn chỉ vì đã có nhiều experiments hơn.

**NOT RUN:** full-text novelty audit; market/OIC/HMM/neural variants mới;
true-law coverage theorem, reserve utility, multi-period trading, human review
và replication trên hardware khác. Không chọn một model/hyperparameter mới từ
full test outcomes vừa xem.

**Next action duy nhất:** đối chiếu toàn văn Fan/Huang với own-knot/shared-hull
algorithm để quyết định claim đóng góp tính toán còn mới hay tương đương prior
art. Chưa mở thêm policy sweep trên các kết quả test đã xem.
