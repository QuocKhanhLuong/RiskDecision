# Q1 tiếp tục: continuous CVaR / OIC — kết quả 07/10/2026

**Đã implement và chạy benchmark liên tục riêng. Runner hoàn tất 128 cases;
primary OIC vẫn INCOMPLETE vì 4/128 cases không qua gate active-set.** Không bỏ
bốn cases để tính kết quả trên phần còn lại. Chưa có bằng chứng OIC thắng về
squared error, chưa mở APTC variant search hoặc claim novelty.

Branch `research/continuous-cvar-oic`, kế thừa `35fcea7818488101e0bd17796cfc8d1b649c1db9`
của lượt Q0/split trước. Main được giữ ở `f6dcffdf6ab7e22a9246aadb17df437e3aae8c6e`;
không merge main. Workspace sạch khi bắt đầu continuation. Hash audit xác nhận
**112 file đã tracked trước lượt này không đổi**, gồm source/config/results cũ.

## VERIFIED — thực sự chạy trong lượt này

| Hạng mục | Evidence thực chạy |
|---|---|
| Software tests | **57 passed**, 1,43 giây; [log](../../runs/continuous_cvar/20261007_oic_v3/tests.log), JUnit cùng thư mục |
| Development | 2 cases, seed riêng 2026107998; numerical gate PASS; dự tính pilot 17,93 giây với margin ×2, dưới cap 600 giây |
| Pilot | 128 cases = 64 seed clusters × Gaussian/crash; 1.152 smooth fits, 128 empirical LP references, 3.200 estimate rows |
| Final run | [20261007_oic_v3](../../runs/continuous_cvar/20261007_oic_v3/RESULTS.md), software replay sau sửa evaluator; **0 additional independent cases** |
| Numerical audit | 1.152/1.152 fits có optimizer success; 0 runtime warnings; max convex gap 2,78e−11 |
| Independent numerical verifier | Augmented KKT và direct quadrature PASS; 124 previously completed case arrays bit-identical sau replay |
| Resume | Partial 3 rồi 125 cases; complete resume dùng lại 128, thêm 0; **262 artifacts byte-identical** |

Các con số 1.152 fits/3.200 rows không phải số thị trường độc lập. Inference dùng
64 seed clusters, giữ hai families cùng seed trong một cluster; bootstrap 10.000
lần. Đây là pilot feasibility có giới hạn, không thiết kế đủ power để xác nhận
superiority phổ quát. CI secondary không hiệu chỉnh multiplicity.

Source/generator/config được khóa trước pilot. Seeds `2026107100:2026107164`
không có observed-use collision lúc pilot đầu tiên bắt đầu; audit chỉ bao phủ
file local khả dụng. Sau lần chạy đầu, toàn bộ seeds là **seen**. Replay không
được tính thành 256 instances hoặc xác nhận độc lập. Development có thể lặp để
kiểm tra phần mềm và không góp vào CI. Mọi fit/correction khóa xong trước khi
evaluator nhận population parameters.

## Formulation và phạm vi OIC

Đã đọc primary source [OIC v4, Iyengar/Lam/Wang](https://arxiv.org/html/2306.10081v4)
và viết [applicability audit](../../continuous_cvar/OIC_APPLICABILITY.md) trước
implementation. Đây là **documented KKT-derived adaptation**, không phải chạy
code chính thức của tác giả. Hai biểu thức projected Hessian inverse và
projection quanh Hessian inverse không được coi là tương đương; bản này dùng
đạo hàm local của constrained estimating equations và kiểm tra perturbation.

Với `theta=(w,v)`, `alpha=.05`, objective là

`h_tau(theta;x) = v + tau/alpha * log(1+exp((-x.w-v)/tau))`.

Giữ cùng feasible set cho mọi continuous method: 8 assets, long-only,
`sum(w)=1`, cap `.5`, `v∈[-50,50]`. Primary `tau=.1`; sensitivity `.05,.2`
được khai báo trước, không chọn tau sau test. Nếu `N` là cơ sở nullspace của
active constraint normals, `g_i` là sample gradient và `H` empirical Hessian:

`correction = mean[(g_i N)(Nᵀ H N)⁻¹(Nᵀ g_i)] / n`.

Không thêm ridge, SE penalty, hoặc clipping để ép correction qua gate. Điều kiện
stable active set/regularity chỉ được giả định và kiểm tra numerical tại mẫu;
pilot không chứng minh population active-set recovery hoặc định lý asymptotic.
Estimator nhắm expected **smoothed objective tại (w,v)**; không biến nó thành
coherent VaR/ES pair. True ES ở w, threshold gap và smoothing gap báo riêng.

Full512 raw/OIC cùng decision fit bằng 512 mẫu. A256 và B256 là hai chiều split:
raw/OIC/independent cùng decision, independent chấm trên nửa 256 còn lại. Tổng
dữ liệu khả dụng là 512; half policies có ít fitting data hơn full512. Không
gán lợi ích của estimator thành cải thiện portfolio. Exact empirical CVaR LP
là reference unsmoothed riêng, không mang nhãn OIC. Continuous population ES
oracle không so regret với optimum của historical bank285.

## Primary và secondary đã khóa

Primary: mean squared relative smoothed-objective error của OIC_KKT trừ raw,
full512, tau=.1, gộp hai families theo seed cluster. **Mean và CI để trống**:
bốn crash seeds `2026107101, 2026107106, 2026107154, 2026107158` không qua OIC
gate. Các fits vẫn có convex optimality certificate rất nhỏ; đây không phải
bốn optimizer thất bại. Active constraint matrix có 9 hàng nhưng rank 8 tại
vertex hai weights bằng .5; multipliers least-squares không duy nhất và có
thành phần âm. Gate OIC chưa xử lý representation này, nên giữ null.

| tau | Full512 OIC null /128 | A256 null /128 | B256 null /128 |
|---|---:|---:|---:|
| .05 | 4 | 0 | 1 |
| **.1** | **4** | **0** | **1** |
| .2 | 3 | 0 | 1 |

Tổng 14 null trên 1.152 fit targets, tất cả có constraint rank deficiency.
Minimum reduced eigenvalue 0,0121; maximum condition 576,03. Không đổi gate hoặc
loại seed sau khi thấy kết quả. Không kết luận OIC nói chung không thể xử lý
vertex từ hạn chế của implementation này.

### Full512, tau=.1

Signed bias dưới đây là trung bình relative error ×100, không phải tỷ lệ mất
vốn. MSE là bình phương relative error không nhân 100.

| Scope / estimator | Signed bias (%) | MSE | Trạng thái |
|---|---:|---:|---|
| Overall raw | −6,3054 | .0103333 | COMPLETE |
| Overall OIC | — | — | **INCOMPLETE** |
| Gaussian raw | −3,5757 | .00345455 | COMPLETE |
| Gaussian OIC | −0,1393 | .00261763 | COMPLETE, secondary |
| Crash raw | −9,0351 | .0172120 | COMPLETE |
| Crash OIC | — | — | INCOMPLETE |

Gaussian OIC-minus-raw MSE = **−.000836925**, paired 95% CI
**[−.001633174, +.000009925]**, vẫn chứa 0. Gaussian signed-bias CI raw
[−4,7182%, −2,4009%], OIC [−1,3843%, +1,1468%]. Bias giảm rõ ở point estimate,
nhưng không đủ kết luận MSE superiority. Không chọn Gaussian làm primary sau
khi overall gặp gate.

### Cùng half256 decision, tau=.1

| Policy / estimator | Signed bias (%) | MSE | Trạng thái |
|---|---:|---:|---|
| A256 raw | −11,3035 | .0289215 | COMPLETE |
| A256 OIC | −1,9888 | .0275402 | COMPLETE |
| A256 independent | −.0844 | .0160573 | COMPLETE |
| B256 raw | −11,1707 | .0267296 | COMPLETE |
| B256 OIC | — | — | INCOMPLETE, 1 null |
| B256 independent | −.3984 | .0114528 | COMPLETE |

A256 OIC-minus-raw MSE = −.00138137, CI [−.0116534, +.0145963].
A256 OIC-minus-independent MSE = **+.01148283**, CI
**[−.00049919, +.02838676]**. Independent split có point MSE thấp nhất trong
comparison đầy đủ A256; CI chênh lệch với OIC vẫn chứa 0. Không dùng bảng này
để chọn model mới hoặc claim thắng chắc. B256 cũng được báo, không chỉ chọn
chiều thuận lợi. Cả hai chiều dùng lại cùng 512 observations nên không phải
hai xác nhận độc lập.

### Smoothing và chất lượng decision — descriptive

| tau, full512 | Mean smoothing gap | Mean threshold gap | Mean continuous ES regret (%) |
|---|---:|---:|---:|
| .05 | .0102148 | .0121998 | 2,6144 |
| .1 | .0384477 | .0105258 | 2,4125 |
| .2 | .1264592 | .0284264 | 2,0875 |

Ba tau nhắm ba smoothed objectives khác nhau. Không chọn .2 bằng regret đã
thấy; primary giữ .1. Raw và OIC cùng portfolio nên true ES/regret giống nhau
trong cùng policy/tau. Bảng không phải bằng chứng correction cải thiện decision.

## Lỗi thực gặp, sửa evaluator và provenance

1. `20261007_oic`: development numerical work chạy, nhưng ghi `session_end`
   lỗi duplicate keyword `utc`; pilot NOT_RUN. Sửa tên field logging, giữ log.
   Seed audit cũng được sửa để tách seed chỉ đăng ký khỏi seed đã thực chạy,
   trước khi pilot bắt đầu; có regression test.
2. `20261007_oic_v2`: pilot chạy cả 128 jobs, 4 FAILED vì population oracle dùng
   nhầm gate cần LICQ/unique multipliers. Các oracle đã có convex gap nhỏ nhưng
   active normals dư thừa. Giữ receipt/failure payloads; không tạo primary
   statistics từ 124 completed cases.
3. `20261007_oic_v3`: chỉ đổi acceptance của **population oracle** sang
   feasibility + global convex supporting-plane gap. Config/fitter/generator
   không đổi; **không nới gate OIC**. Replay đủ 128, không phát sinh samples độc
   lập. Verifier xác nhận arrays của toàn bộ 124 cases đã hoàn tất ở v2 giống
   hệt sau replay. Bốn evaluator failures cũ khác tập bốn primary OIC null.

Verifier giải hệ augmented KKT thay cho nullspace và tích phân normal-mixture
trực tiếp thay cho localized smoothing excess: max correction discrepancy
8,62e−14, max quadrature discrepancy 2,65e−8. Đây là numerical/software audit
bằng code khác, **không phải independent peer review**. Tests và verifier không
bảo đảm hiệu quả trên thị trường thật.

Thời gian đo, warnings, source/config hashes, môi trường, progress JSONL,
tqdm/ETA, freeze và resume receipts nằm trong
[run](../../runs/continuous_cvar/20261007_oic_v3/RESULTS.md). Code/config SHA và
publication manifest cho phép kiểm tra publication; full arrays/checkpoint
payloads giữ local, không nằm hết trong compact Git evidence. Clone compact
không tự resume run đã đo nếu thiếu các payload này.

## REPORTED / chỉ đọc, không chạy lại trong continuation

- Q0 crossed historical và Q1 bank285 independent-split của commit `35fcea7`
  là evidence lượt trước; không tính thành experiment mới ở đây.
- Primary OIC paper là nguồn formulation/assumptions; không tái lập code hoặc
  toàn bộ experimental matrix của tác giả.
- Archive/report v1/v2 là lịch sử, không danh sách rerun. Không sửa số/config cũ.

## NOT_RUN

Unsmoothed OIC; OIC cho discrete bank285; correction xử lý degenerate active
sets; continuous APTC/SE method search; Q2 temporal/regime matrix; Q3 market
evaluation; economic reserve utility; ML/DL sweep. Không có market PnL, Sharpe,
coherent corrected VaR/ES calibration hoặc kết luận novelty trong lượt này.

## PROPOSED — đúng một next action

**Audit và derive cách xử lý active-set suy biến không phụ thuộc representation
(hoặc critical cone), kiểm tra trên development, rồi khóa một evaluation mới
với unseen seeds.** Bộ 128 cases hiện tại chỉ dùng regression sau đó; không
dùng để chọn biến thể và đồng thời gọi là xác nhận mới.
