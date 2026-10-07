# Q2 tiếp: HMM chuẩn giải thích phần lớn conditional gap trong Markov pilot

**Đã chạy baseline Gaussian HMM trên seeds mới, không đổi cấu hình sau test.**
Ở Markov dừng, cùng full512 portfolio/threshold, conditional MSE của HMM là
**.00959678**, Gaussian iid **.09523840**. Primary paired delta **−.08564162**,
CI 95% **[−.10164200, −.06984456]**, 32 path clusters. MSE giảm khoảng **89,9%**
trong setting này. Đây là baseline chuẩn phù hợp family mô phỏng, **không phải
method mới** hoặc bằng chứng trading/market.

Kết quả làm rõ hướng nghiên cứu: cần một forecaster mô hình hóa trạng thái có
điều kiện; chưa có lý do từ pilot này để mở APTC/neural variant. HMM xử lý được
phần lớn gap mà Gaussian iid/EWMA chưa xử lý trên các seeds mới. Residual error
vẫn còn; không kết luận HMM giải quyết mọi structural shift.

Branch `research/markov-hmm-q2`, base `3203bb34966ad8e029ea684e6cadf1b9c9bacbd1`.
Đã fetch origin/main và xác nhận là ancestor của base; không merge main.
Workspace sạch lúc bắt đầu; **274 file tracked trước lượt này giữ nguyên bytes**.
Q0/Q1/Q2 measured source/config/results không sửa. User “tiếp đi” tiếp tục đúng
HMM control đã đề xuất trong [Q2 trước](20261008_temporal_risk_q2.md).

## VERIFIED / RUN

| Hạng mục | Đã thực hiện |
|---|---|
| Test suite | **99 PASS**, 2,57 giây, gồm 9 HMM tests mới |
| Seed audit | 9.544 local files; 0 collision quan sát được, gồm gzip exports |
| Development | 2 seeds riêng × 2 worlds × 8 origins = **32 origins**; tất cả selected fits hội tụ |
| Compute gate | Ước lượng có margin ×2 **105,48 giây**, dưới cap 600 giây |
| Pilot mới | **512 origins**, 32 path clusters × 2 coupled worlds × 8 origins |
| Fitting | **1.536 HMM restarts**, toàn bộ admissible/hội tụ; 1.024 portfolio/threshold fits |
| Results | 7.168 estimate rows; 0 failed cases, 0 null estimates, 0 warnings |
| Verifier | PASS; tính lại 1.536 likelihoods, forecasts và **216 paired CIs**, không refit |
| Resume | Partial 5 rồi 507; complete resume **512 reused / 0 new**, **551 artifacts byte-identical** |

Pilot case compute 54,18 giây; completion session 55,70 giây; verifier 50,81
giây; complete resume 1,78 giây. Progress JSONL, terminal tqdm/ETA, full histories
và actual timing ở [run directory](../../runs/markov_hmm/20261008_q2_hmm/RESULTS.md).
32 paths là đơn vị inference. Worlds ghép cặp, origins overlap và restarts
không tăng số quan sát độc lập. Sample size giới hạn compute, chưa có thiết kế
power cho superiority phổ quát. Không thêm seeds sau outcomes.

## Protocol trước outcomes, cùng information và cùng decision

[Protocol](../../markov_hmm/PROTOCOL.md) và [config](../../markov_hmm/config.json)
được khóa trước development/pilot. Pilot seeds `2026110000:2026110032`,
development `2026109998/99`; audit không bao phủ external runs không có local
artifacts. Config hash
`85aa84337b91f026b0115bbb8151bb635ddce1937ad8042bb5ef22f331b5d738`.

DGP Q2 giữ nguyên: Markov stationary và Markov transition shift; emissions giữ
nguyên, transition đổi từ index 768. Cùng innovations/uniforms, paths bằng nhau
trước break. Origins 512:64:960, past `[t−512,t)`, target X_t. **Horizon một
observation**, stride 64 không phải horizon 64.

HMM hai trạng thái Gaussian full covariance, hmmlearn 0.3.3, ordinary ML EM.
Ba deterministic starts dùng quantile .50/.70/.85 của standardized squared
radius trong past; start/transition/emissions đều học lại. Chọn maximum
**past training likelihood**, không chọn bằng population risk/test scores.
Window, số state, khởi tạo, maxiter 200, tolerance 1e−4 và mọi baseline đã khóa;
development chỉ kiểm tra numerical/compute, không tune risk errors.

Số state và Gaussian family trùng DGP là điều kiện thuận lợi được khai báo từ
đầu, không chứng minh tự tìm đúng state count trên dữ liệu tùy ý. Trong world
shift, giả định transition time-homogeneous không đúng toàn window.

Model chỉ nhận past và settings; không nhận world, latent states, true DGP
parameters, change time hay future. Next probabilities = final filtered
posterior × learned transition. Dùng final posterior tại t−1 trực tiếp cho t
sẽ sai; test enumeration và verifier kiểm tra bước chuyển này.

Conditional truth dùng observed-window filter với **true parameters/change
schedule**, nên vẫn là parameter oracle, không learned baseline. Latent-state
truth chỉ là diagnostic khác. Không trộn information sets để claim learned
algorithm gap bằng 0.

Mỗi forecaster chấm **cùng (w,v)** trong policy: full512 historical optimizer
hoặc equal512 cố định weights và fit threshold. Feasible set long-only, sum=1,
cap=.5; alpha=.05, tau=.1. Equal512 vẫn fit threshold, không phải zero-selection
control. Không dùng own-selected portfolios khác nhau để gọi superiority.

## Kết quả conditional: primary và toàn bộ controls

MSE là **mean squared relative smoothed-objective error**, không tỷ lệ lỗ vốn.
Average origins theo path trước bootstrap 10.000 draws; primary chỉ một contrast.

| Full512, all origins | Markov stationary | Markov shift |
|---|---:|---:|
| Raw | .132313 | .129838 |
| iid OIC | .179105 | .151496 |
| Gaussian iid | .095238 | .123025 |
| AR Gaussian | .094843 | .123028 |
| EWMA Gaussian | .107751 | .094153 |
| **HMM filtered** | **.009597** | **.015434** |
| HMM stationary mixture | .140971 | .129648 |

Primary HMM − Gaussian iid tại stationary/full512/all: **−.08564162**,
CI **[−.10164200, −.06984456]**. Đó là một comparison đã đăng ký, không lựa
chọn winner từ bảng sau test. Các contrasts dưới là **secondary, CI không
điều chỉnh multiplicity**:

| Full512 contrast | Delta MSE | 95% CI |
|---|---:|---|
| Stationary all: HMM − EWMA | −.09815408 | [−.12045565, −.07697585] |
| Stationary all: HMM − stationary mixture | −.13137400 | [−.14601828, −.11633295] |
| Shift all: HMM − Gaussian iid | −.10759027 | [−.12380547, −.09206735] |
| Shift all: HMM − EWMA | −.07871850 | [−.10137750, −.05825733] |
| Shift after: HMM − EWMA | −.07215636 | [−.10050587, −.04753234] |

Sau break, MSE HMM=.022773, EWMA=.094929, Gaussian iid=.159796. HMM có lợi
trong structural-shift instance đã khóa nhưng không biết trước transition mới.
Không suy rộng thành guarantee cho mọi change mechanism.

HMM stationary mixture dùng **cùng fitted emissions/transition**, chỉ thay
final conditional probabilities bằng invariant probabilities. Conditional
performance kém hơn rõ: việc dùng posterior hiện tại quan trọng trong ablation
này. Đây không phải causal decomposition của selection/shift hoặc một iid GMM
được fit riêng.

Equal512 cũng giữ dấu hiệu: HMM/Gaussian iid/EWMA conditional MSE lần lượt là
.007234/.091340/.114493 ở stationary và .011569/.111613/.100215 ở shift. Không
dùng chênh lệch full/equal như isolated causal selection effect.

## Giữ kết quả không thuận lợi và phân biệt target

HMM filtered không tốt cho mọi mục tiêu. Khi so với **average marginal risk
trên fitting dates**, full512 MSE là:

| Method | Stationary | Shift |
|---|---:|---:|
| Raw | .029854 | .025639 |
| iid OIC | .024655 | .020639 |
| Gaussian iid | .045288 | .043511 |
| HMM filtered | **.240757** | **.239963** |
| HMM stationary mixture | .022139 | .018139 |

Mục tiêu next-step conditional và historical marginal khác nhau. Kết quả xấu
trên marginal được giữ nguyên, không chuyển target sau test để gọi HMM thắng
mọi mặt. Tương tự, iid OIC tốt hơn raw ở marginal nhưng kém ở conditional trong
pilot này. Không biến correction objective thành coherent VaR/ES forecast pair.

## Numerical audit, khả năng resume và phần chỉ đọc

Tất cả 1.536 starts hội tụ, tối đa 47 iterations, không chạm cap; covariance
eigenvalue chuẩn hóa nhỏ nhất .115982, effective state occupancy nhỏ nhất
38,60. Max portfolio supporting-plane gap 9,38e−12. Verifier tính lại likelihood
của từng restart từ saved fitted parameters với filter khác; max discrepancy
1,73e−11. Max forecast-objective discrepancy 8,69e−12, posterior 3,00e−15,
parameter-oracle filter 1,67e−15. Đây là software/numerical audit, không peer review.

Resume không refit case hoàn tất. Source/config/environment/package/input
changes bị từ chối; 551 artifact hashes không đổi sau complete resume. Publish
gzip lossless của exports lớn và bundle chứa **toàn bộ 578 synthetic path/case
payload files** của development/pilot, có member hashes. Muốn resume từ clone
cần khôi phục payloads, giữ đúng môi trường đã ghi; môi trường khác không gọi
là byte-identical resume. Raw originals local không bị thay đổi.

**REPORTED/READ:** Q0/Q1/Q2 báo cáo trước chỉ được đọc, không rerun scientific
comparisons. Đọc official [hmmlearn tutorial](https://hmmlearn.readthedocs.io/en/stable/tutorial.html)
và [GaussianHMM API](https://hmmlearn.readthedocs.io/en/stable/api.html#hmmlearn.hmm.GaussianHMM),
cùng installed 0.3.3 source cho M-step/fit/convergence. Không claim tái lập paper
gốc hoặc proof khi distribution shift. Library có thể báo converged khi chạm
iteration cap; runner dùng tiêu chí likelihood riêng và lưu cả hai trạng thái.

## NOT_RUN và đúng một next action

**NOT_RUN:** market/Q3, economic utility, neural/APTC variants, state-count hoặc
window sweeps, online change detection, calibrated joint VaR/ES scores,
continuous conditional-optimum regret, independent peer review. Chưa có
novelty/trading claim. Các kết quả synthetic này không làm mới dữ liệu thị
trường assessment đã từng được xem trong lịch sử.

**PROPOSED:** triển khai và khóa evaluator Q3 trên ECB reference FX cho các
forecasts VaR/ES hợp lệ ở cùng portfolio, giữ bộ statistical baselines đã định
sẵn và khai báo rõ assessment nào là historical reuse trước khi mở outcomes.
Không ghép arbitrary OIC correction vào một VaR/ES pair để chấm joint score.
