# Ghép đóng góp nhỏ: tính minimax ES regret nhanh hơn và kiểm tra policy học từ dữ liệu

**Kết luận:** đã triển khai và chạy một tổ hợp có nội dung toán học: dùng chung
đường bao rủi ro của toàn bộ bank, chỉ kiểm tra các điểm đổi ngưỡng của chính
từng action, rồi áp dụng cho nhiều phân phối thành phần ước lượng và chi phí
chuyển danh mục. Phần tính toán đúng trong sai số số học và có lợi ở bank lớn.
**Tổ hợp policy chưa chứng minh lợi ích chung; chưa có method novelty được xác lập.**

Ngày: 2026-10-08. Branch: `research/compositional-risk-policy`.
Base: `ec9371b3f7bfa0f9923b581a1f5e5fb9c5bc7c6e`.
Đã fetch `origin/main` tại `f6dcffdf6ab7e22a9246aadb17df437e3aae8c6e`, vốn là
ancestor của base; không cần merge. Worktree lúc bắt đầu sạch. Cả **621 file
tracked cũ giữ nguyên SHA-256**; không sửa kết quả/config/archive lịch sử.

User cho phép mở rộng câu hỏi để ghép các minor contributions. Decision được
ghi trước chạy trong [receipt](../../runs/compositional_risk/20261008/start_receipt.json)
và [protocol](../../bank_regret/PROTOCOL.md). Đây là phần mở rộng tiếp nối Q0/Q1/Q2
đã được báo cáo trước; các tài liệu archive không được diễn giải thành backlog
để chạy lại. Không chọn model/hyperparameter từ các test đã xem.

## 1. Câu hỏi và đóng góp ứng viên

Với bank hữu hạn, hai phân phối thành phần cố định trong mỗi world, xác suất
mixture `q` thuộc một interval, và chi phí `c_i` cố định từ cùng incumbent:

```text
f_ki(q) = ES_alpha(action_i; (1-q)P_k0 + qP_k1) + c_i
g_k(q) = min_j f_kj(q)
R_i = max_k max_q [f_ki(q) - g_k(q)]
choice = argmin_i R_i
```

Đây là **chênh lệch ES tuyệt đối** với action tốt nhất trong cùng world/q,
không phải tỷ số, ES của pathwise regret, hay cumulative trading regret.
Chi phí cùng incumbent nằm ở cả action chọn và action đối chứng.

Biểu diễn RU cho mỗi `f_i` là minimum của các đường affine theo `q`. Do đó
`g=min_{i,t} RU_line_{i,t}` có thể dựng bằng **một lower hull dùng chung**.
Trong từng đoạn affine của chính `f_i`, hàm `f_i-g` convex, nên maximum nằm
ở đầu/cuối đoạn. Vì vậy chỉ cần các own knots và hai đầu interval; không phải
đánh giá action i tại mọi knot của các đối thủ. Hull giữ owner để xuất được
world, q và competitor làm witness cho regret.

Với K là tổng số support thresholds, xây hull và truy vấn toàn bank cần
**O(K log K) thời gian, O(K) bộ nhớ** mỗi world, kể cả sắp xếp/prefix sums.
Nhiều world hữu hạn cộng chi phí từng world và lấy maximum cho mỗi action.
[Derivation trước chạy](../../runs/compositional_risk/20261008/action_local_derivation.md)
nêu đủ giả thiết. Đây là kết quả trong số học thực; code float64 không chứng
nhận dấu khi hai giá trị gần nhau tùy ý, không phải interval arithmetic.

| Thành phần | Trạng thái đóng góp |
|---|---|
| RU, ES mixture concavity, lower hull | Công cụ đã biết |
| Minimax regret, posterior estimation, switching cost | Công cụ đã biết |
| Own-knot witness + một hull cho toàn bank | Ứng viên specialization tính toán; priority chưa xác lập |
| Nhiều fitted worlds + shared-law comparator + chi phí | Tổ hợp đã implement; không tự tạo bảo đảm thống kê |
| Joint policy benefit của toàn tổ hợp | Không được dữ liệu lượt này ủng hộ |

## 2. VERIFIED / RUN: đã thực sự thực hiện

Code mới: [bank_regret](../../bank_regret/README.md). **144 tests passed**,
trong đó 16 test cases mới kiểm tra all-pair certificates, risk-envelope LP,
knots của competitor, ties, zero atoms, chi phí, đảo state, alpha=1, overflow,
same-history invariance, freeze và resume. Tests toàn suite là kiểm tra phần mềm,
không phải chạy lại các thí nghiệm khoa học lịch sử.

**96/96 cases hoàn tất** theo config khóa trước: 32 computational cases và
64 policy histories mới, không loại case. Source/config/dependency/environment
fingerprint:
`7b9fabe9daee5c382ad376a90ec1930619d6a5c64917329a46aef9bf29b7112d`.
Môi trường CPU macOS ARM64, Python 3.13.15, NumPy 2.3.5, SciPy 1.17.0.

Preflight dự báo 34.35 giây, dưới giới hạn 240 giây. Tổng thời gian tính 96 cases
thực tế **21.58 giây**; execution loop lượt partial là 1.37 giây, lượt nối thêm
91 cases là 20.43 giây. Các số này không gồm source/input validation trước loop.
No-op resume tạo **0 case mới**, nhưng tái tạo fit/decision để kiểm tra và mất
**17.78 giây outer wall time**. Không gọi đó là resume không tốn compute.
Final verification mất 26.57 giây, dùng lại cases nên không tính là sample mới.
Numerical warnings thu được: **0**; cảnh báo finite stress set không bảo đảm
true-law coverage được giữ trong từng policy checkpoint.

Đã dừng cố ý sau 5 cases (exit 3), resume đến đủ (exit 0), rồi resume lần nữa.
**5/5 và 96/96 checkpoint giữ nguyên byte hash**. Progress JSONL, tqdm/ETA,
source hashes, learned worlds, observed histories và decision hashes đều có trong
[run index](../../runs/compositional_risk/20261008/RESULTS.md).

### Exactness và tối ưu tính toán

Đối chứng mạnh dùng **cùng global hull**, nhưng đánh giá mỗi action tại hợp
của knots toàn bank. Không chỉ so với thuật toán pairwise chậm hay coarse grid.
32 cases gồm bank M={8,32,128,512}, support S={16,64}, bốn replicate tương ứng
alpha={.01,.05,.2,1}; interval đầy đủ hoặc subinterval đã khóa. Ba lần timing
mỗi solver/case, đảo thứ tự gọi; bảng là median của median từng case, gồm cả
hull construction, không gồm chuẩn bị `FiniteMixture` (đã lưu riêng theo case).

| M × S | Own knots (ms) | Union knots (ms) | Union / own |
|---|---:|---:|---:|
| 8 × 16 | 0.524 | 0.509 | 0.971 |
| 8 × 64 | 0.871 | 0.845 | 0.971 |
| 32 × 16 | 1.961 | 1.935 | 0.987 |
| 32 × 64 | 3.491 | 3.468 | 0.993 |
| 128 × 16 | 7.655 | 7.920 | 1.035 |
| 128 × 64 | 13.817 | 15.170 | 1.098 |
| 512 × 16 | 29.485 | 33.071 | 1.122 |
| 512 × 64 | 55.226 | 63.862 | **1.156** |

Ô lớn nhất đạt throughput tương đối 1.156×, tức giảm thời gian khoảng **13.5%**.
Bank nhỏ chậm hơn nhẹ; không có speedup đồng đều. Ví dụ case 512×64, alpha=.2
cần 4,437 own-risk evaluations so với 1,748,480 ở union baseline; mức giảm
query không chuyển nguyên vẹn thành wall-time vì còn hull/sắp xếp/overhead.
Bốn replicate cũng đổi alpha/interval nên bảng không chứng minh một định luật
scaling thực nghiệm. Không đo peak memory; O(K) là phân tích thuật toán.

- Sai số regret vector tối đa: **2.22e-16**; sai số witness: **1.78e-15**.
- **0/32** selected-index disagreements.
- Verification đối chiếu toàn bộ 64 fitted-world policies bằng union baseline:
  sai số tối đa **1.73e-18**, cùng lựa chọn.
- **554** risk-envelope LP cho witnesses benchmark: sai số tối đa **4.33e-15**.
  Tất cả actions/competitors tại saved witnesses của bank M=8; bank lớn kiểm
  tra selected action và competitor của nó. Không gọi đây là exhaustive LP
  proof toàn bộ continuous domain.
- **8,192** LP kiểm tra true conditional ES của mọi action × history:
  sai số tối đa **6.94e-18**.

### Learned policy: có fit thật, vẫn là synthetic pilot

Benchmark mới có context nhị phân **được quan sát**, 512 cặp context/category,
dictionary 32 scenarios × 8 assets công khai và bank cố định 128 portfolios.
Tất cả methods cùng thông tin, cùng bank, cost convention. Fit dùng conjugate
Dirichlet/Beta, không nhận family, latent truth hay future outcome. Seed posterior
lấy từ observed history/public design; cùng dữ liệu cho cùng fitted policy.
Truth chỉ đi vào evaluator sau khi khóa decision hash. Đã tái tạo và đối chiếu
history, fit, decision và evaluator truth với generator đã freeze.

Một nominal emission world và bốn posterior draws, interval q là quantiles
.05/.95 của Beta posterior. **Đây là finite stress set, không phải confidence
set có true-law coverage 90%.** Chi phí giả định là .001 × L1 turnover / 2,
tính từ equal-weight incumbent; không phải phí thực đo hoặc reserve utility.
`component_shift` đổi emission tại bước448 **bên trong** window512, tiếp tục
sang bước dự báo; model fit vẫn giả định stationary trong cả hai families.

Mỗi family có 32 histories độc lập conditional on **cùng một public dictionary
và bank**. 128 portfolios và 4 posterior draws không phải independent samples.
Pilot giới hạn compute, chưa powered cho superiority tổng quát. Không dùng
winner sau test để triển khai hoặc chọn cấu hình mới.

Mean true conditional ES+cost regret, nhân 10,000 để dễ đọc; **thấp hơn tốt hơn**.
Đây là đơn vị loss synthetic đã scale, không phải realized trading PnL.

| Frozen policy | Stationary | Component shift | Harmful switches stationary / shift |
|---|---:|---:|---:|
| Point posterior | **0.5273** | 2.9556 | 4/32; 15/32 |
| Shared full (tổ hợp chính) | 0.7751 | **3.6812** | 6/32; 24/32 |
| Shared endpoints | 0.7751 | 3.6812 | 6/32; 24/32 |
| Rectangular full / absolute worst-case ES | 1.4938 | 2.4748 | 13/32; 17/32 |
| Rectangular endpoints | 1.4938 | 2.4748 | 13/32; 17/32 |
| Nominal components only | 0.5273 | 2.9556 | 4/32; 15/32 |
| Fixed q | 0.6813 | 3.6161 | 6/32; 23/32 |
| Ignore cost when selecting | 0.8269 | 4.2322 | 8/32; 30/32 |
| Historical unconditional | 1.7117 | 1.9689 | 4/32; 4/32 |
| Keep incumbent | 1.4880 | **1.7713** | 0/32; 0/32 |

Shared full chuyển danh mục 29/32 và 24/32 lần, mean cost lần lượt 0.00015927
và 0.00013422. Harmful nghĩa là true ES+cost cao hơn giữ incumbent, không chỉ
phát sinh chi phí. Rectangular objective tách worst chosen-world và best
benchmark-world; argmin của nó đúng bằng absolute worst-case ES baseline.

Paired mean differences và percentile bootstrap 95% CI (4,000 resamples theo
history, cùng đơn vị ×10,000; **âm có lợi cho shared**):

| Contrast đã khóa | Stationary | Component shift |
|---|---:|---:|
| Shared − rectangular (primary) | −0.7187 [−1.2193, −0.3059] | **+1.2064 [+0.4981, +2.0040]** |
| Shared − point (secondary) | **+0.2478 [+0.0478, +0.4733]** | +0.7256 [−0.0246, +1.5251] |
| Factorial interaction full/endpoints × shared/rectangular | 0 [0,0] | 0 [0,0] |

Shared-law modeling giúp so với rectangular control khi stationary, nhưng
không thắng simpler point policy. Khi component shift, primary contrast đảo
chiều bất lợi. CIs là pilot exploratory, không multiple-testing-adjusted hay
chứng nhận superiority. CI [0,0] ở interaction chỉ phản ánh lựa chọn trùng
trong mẫu, không chứng minh population equivalence.

**Diagnostic sau chạy, không dùng tuning:** full/endpoints có cùng lựa chọn
ở cả64 histories; nominal-components cũng trùng point ở64/64. Tuy vậy shared
regret surfaces khác ở26/32 stationary và19/32 shift histories, chênh tối đa
0.00020337 và0.00009454. Có6,679/20,480 và3,174/20,480 world-action curves
có interior knots. Do đó cơ chế không hoàn toàn vắng mặt, nhưng chưa tác động
đến argmin trên bank đã khóa. Không đổi bank/tail probability sau khi thấy vậy
để cố tạo interaction dương.

Stress certificate thấp hơn true regret của selected shared action ở **7/32**
stationary và **25/32** shift histories. Certificate chỉ đúng với world set
được cấp; kết quả này không phải vi phạm theorem tính toán, và không được gọi
là calibrated safe switching.

### Forecast, selection và utility tách riêng

Mọi same-fit policy dùng **đúng cùng nominal forecast vector** trên common bank.
Thay selector không tạo forecaster mới. Common-bank forecast MSE:

| Forecast | Stationary | Component shift |
|---|---:|---:|
| Observed-context posterior nominal | 8.3462e-8 | 2.8300e-6 |
| Historical unconditional | 1.3203e-6 | 2.3714e-6 |

Conditional fit có ích ở stationary, kém historical khi shift trong pilot này.
Selection regret và assumed switching costs đã đo riêng; **reserve utility,
multi-period turnover, realized returns và market profitability: NOT RUN**.
Không gọi observed context này là kết quả latent-state HMM equally informed.

## 3. READ / REPORTED: prior art và review

RU/mixture concavity và relative-robust CVaR đều là prior art:
[Rockafellar–Uryasev](https://doi.org/10.21314/jor.2000.038),
[Tselishchev](https://arxiv.org/pdf/1910.00640),
[Huang et al.](https://doi.org/10.1016/j.ejor.2009.07.010).
Lượt này không đọc lại toàn văn RU/Tselishchev; Tselishchev đã được đọc ở lượt
trước. Publisher Huang không mở được; URL PDF Kyoto chỉ trả empty HTML,
**không tính là đã đọc PDF**.

Threat gần nhất tìm thấy là [Fan (2026), Data-Driven Minimax-Regret Portfolio
Optimization under Tail-Risk Ambiguity](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7486600).
Root đọc primary SSRN indexed abstract: paper kết hợp independent relative-ES
audit trên frozen library, admissible engine mixtures và minimax regret, có
bound thống kê và finite-library LP. **Toàn văn chưa đọc**, direct open thất bại.
Chưa biết paper đã bao phủ own-knot/shared-hull specialization hay chưa; không
được tuyên bố first minimax regret/relative-ES/library validation. Không suy
diễn chữ relative trong abstract thành ratio hoặc cho rằng objective tương đương.

[Weber, Relatively robust decisions](https://link.springer.com/article/10.1007/s11238-022-09866-z)
có ratio regret và structural envelope reductions: primary HTML phần mở đầu
và model đến§2.4 đã đọc, chưa audit toàn paper. Ratio objective khác absolute
difference ở đây; đó là prior-art threat về cấu trúc, chưa phải chứng minh
hai thuật toán giống nhau. [Robust OWA portfolio model](https://doi.org/10.1016/j.cor.2024.106666)
cho thêm ví dụ composition risk-profile/minimax regret đã có; root chỉ đọc
publisher preview. Không lấy việc ghép nhiều công cụ quen thuộc làm novelty.

Root có10 unique queries và1 repeat để kiểm chứng SSRN, thêm targeted opens;
hai AI reviewers có các search logs riêng. Đây là bounded search, không phải
systematic review hoặc chứng minh không tồn tại prior art. Source access từng
mục nằm trong [queries_root.json](../../runs/compositional_risk/20261008/queries_root.json).
Các metadata RePEc trong log reviewer là secondary metadata; root không nhận
chúng là independently verified primary full text.

Root và hai AI agents đã ghi initial ideas trước khi tìm literature trong
lượt mở rộng này, sau đó mới cross-review. Review A dẫn đến sửa posterior RNG
seed chỉ phụ thuộc observations, thêm same-history test, replay fit/decision,
dependency hashes và learned-world union check **trước freeze**. Review B
kiểm tra reduction; root phát hiện và sửa một nhận định sai về min-concavity
bằng hypograph argument. Có correction append-only cả cách gọi objective
trong review B; report này dùng absolute ES-difference. Consensus AI không
thay chứng minh hay human peer review. Review cuối chỉ đọc source/summary,
không tự chạy full tests/cases; root là người chạy và lưu receipts.

Kết quả Q0/OIC/stable-face/temporal/HMM/pairwise của các báo cáo trước chỉ là
**READ / REPORTED historical context** trong lượt này. Không claim đã rerun
để tạo independent confirmation, không tự dựng artifacts còn thiếu từ archive.

## 4. Phán quyết và phần chưa chạy

**VERIFIED:** có theorem hẹp + code executable + matched exact comparator,
96 cases mới, tests/resume/provenance và negative policy result giữ nguyên.
Đóng góp ứng viên có thể là một technical specialization về giải minimax
regret trên bank hữu hạn; prior-art priority và mức đủ lớn cho paper chưa rõ.

**PROPOSED:** đóng gói own-knot witness reduction với shared bank hull thành
đóng góp tính toán hẹp nếu full prior-art audit xác nhận khoảng trống thật.
Các ý tưởng gate/abstention và policy cải thiện thêm trong generation logs
chưa được triển khai như phương pháp mới, không tính vào thành tích lượt này.

**NOT RUN:** full-text closest-prior algorithm audit; independent public-bank
replication; peak-memory/scaling lớn hơn; true-law coverage theorem; human
peer review; hidden-state HMM refit; OIC variant/new OIC claims; new official
market validation hoặc download; neural sweep; dynamic policy/reserve utility.
Không dùng synthetic dictionary này làm bằng chứng giao dịch thực tế.

**Đúng một next action:** đối chiếu toàn văn thuật toán và định nghĩa của
Fan/Huang với own-knot/shared-hull reduction, ghi bảng equivalent/different/
unresolved để quyết định có giữ claim đóng góp tính toán hay không. Việc truy
cập toàn văn chưa thành công trong lượt này; không lấy abstract làm kết luận
priority. Chưa khởi chạy sweep khác hoặc chọn model mới từ kết quả vừa xem.
