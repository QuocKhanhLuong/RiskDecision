# Q2: temporal dependence, transition shift và common-information evaluation

**Đã khóa protocol và chạy pilot temporal mới.** Trên AR(1) dừng, cùng full512
decision, AR Gaussian fit từ past đạt conditional MSE **.00163519**, so với
**.06520457** của iid OIC. Primary paired delta **−.06356938**, CI 95%
**[−.07275199, −.05444518]**. Đây là baseline thống kê phù hợp DGP, không phải
method mới. Không cần mở neural/APTC variant để giải thích kết quả này.

**Sửa optimistic bias của marginal objective không đồng nghĩa dự báo tốt bước
kế tiếp.** HAC/circular-block bootstrap chưa cải thiện rõ marginal MSE so với
iid OIC. Trong cả ba worlds, iid OIC có conditional MSE cao hơn raw tại cùng
decision. Đây là giới hạn chuyển mục tiêu đánh giá, không phải phản bác định lý
OIC iid trên mục tiêu ban đầu.

Branch `research/temporal-risk-q2`, base `fee458eef4069f9eea36929508e9f92ecc19d047`.
Workspace sạch khi bắt đầu; **229 file tracked lịch sử giữ nguyên bytes**.
Không merge main, không sửa measured configs/results cũ, không chọn model theo
pilot đã xem. Artifact chính: [run RESULTS](../../runs/temporal_risk/20261008_q2/RESULTS.md).

## VERIFIED — thực sự chạy trong lượt này

| Hạng mục | Kết quả |
|---|---|
| Test suite | **90 PASS**, 2,43 giây; [log](../../runs/temporal_risk/20261008_q2/tests.log) |
| Local seed audit | 8.693 files; 0 observed-use collision cho seeds mới |
| Development | 2 seeds riêng × 3 worlds × 8 origins = 48; numerical gate PASS |
| Development selection | b=16 từ rule ACF past-only; HAC lag 15, purge gap 16 |
| Pilot | **32 path clusters**, 3 coupled worlds × 8 origins = **768 origins**, 16.896 estimate rows |
| Fits | 2.304 locked decisions/thresholds; **24.576 bootstrap refits**; tất cả optimizer success |
| Failures/warnings | 0 failed cases, 0 null estimates, 0 runtime warnings, 0 AR coefficient clips |
| Independent verifier | **PASS**, 1.368 paired contrasts, mọi bootstrap replicate objective được tính lại không refit portfolio |
| Resume | 5 origins rồi 763; complete resume 768 reused / 0 new; **807 artifacts byte-identical** |

32 là số cluster độc lập cho inference. Origins overlap, các bootstrap refits,
portfolios và coupled worlds không tăng số sample độc lập. Pilot có giới hạn
compute, không được thiết kế đủ power cho superiority phổ quát. Secondary CIs
không điều chỉnh multiplicity. Không thêm seeds sau khi đọc kết quả.

## Protocol khóa trước outcomes và thông tin khả dụng

[Protocol/applicability](../../temporal_risk/PROTOCOL.md) được viết trước
implementation và pilot. Seeds mới `2026109000:2026109032`; development riêng
`2026108998/99`. Config hash
`7a727b15fde89537be588343e98c6ab93bab0703965ced7f0336497aee1bd5a4`.
Audit chỉ bao phủ local files có sẵn, không bảo đảm cho external runs không có
artifacts. Block rule dùng ACF returns/squared returns trên development past;
không dùng population risk errors để chọn b. Window 512, tau=.1 và baselines đã
khóa. Ước tính compute với margin ×2 là 249,99 giây, dưới cap 600 giây.

Ba worlds:

1. **AR(1) stationary**, phi=.6, initialized đúng stationary law.
2. **Markov stationary**, hai Gaussian volatility states và transition P0 cố định.
3. **Markov transition shift**, ghép cặp với world 2, dùng chung Gaussian
   innovations/state uniforms; P0 đổi sang P1 từ index 768. Emissions giữ nguyên.

Hai Markov paths giống từng byte trước break. Đây là một dạng nonstationarity
có kiểm soát; không đại diện mọi structural change trong thị trường.
Origins 512,576,640,704,768,832,896,960 chỉ nhìn `[t−512,t)`, dự báo X_t.
**Horizon = một observation; stride 64 chỉ là khoảng cách origins.**

Models nhận past và cấu hình fitting, không nhận world, transition matrices,
change time, true parameters, hidden state hoặc future. Target conditional
Markov dùng forward filter trên chính window được phép, với true DGP parameters
và marginal prior tại đầu window. Vì biết parameters và shift schedule, đây là
**parameter oracle**, không baseline đã học. Diagnostic khác dùng state(t−1),
không state(t); không trộn nó với observed-history truth. Forecast tại đúng
break có thể khó vì learned models không được báo trước lịch thay transition.

## So sánh tại cùng decision

Giữ feasible set Q1: long-only, sum(w)=1, cap=.5, threshold trong [−50,50],
alpha=.05, tau=.1. Full512 và older256 dùng optimizer lịch sử nguyên vẹn.
Equal512 cố định weights bằng nhau, chỉ fit threshold; vẫn có selection ở
threshold, không gọi đó là control hoàn toàn không fit.

- **Full512/equal512:** raw, iid OIC, HAC local optimism, circular-block bootstrap
  optimism, Gaussian iid, diagonal AR Gaussian và EWMA Gaussian.
- **Older256:** decision fit trên nửa cũ, rồi raw/iid OIC/HAC trên fitting half;
  chronological holdout 256 mới và purged holdout 240 mới sau gap 16; ba
  statistical forecasters dùng toàn bộ past512 để chấm cùng older decision.

Tổng information budget 512; fitting/evaluation sample sizes khác nhau được
ghi rõ. Không so scores qua hai policies khác w như common-target superiority.
AR là coordinatewise OLS + intercept và full residual covariance. EWMA dùng
lambda=.94 và past-window mean. Không dùng true phi hoặc fit learned HMM.

Target là **expected smoothed objective tại (w,v)**, không phải coherent
corrected VaR/ES pair. Conditional true ES có lưu riêng. Không đánh đồng một
realized next loss với ES truth; không tính market PnL/Sharpe hoặc utility.

## Primary và các baseline conditional

MSE là mean squared relative objective error, không nhân 100 và không phải
tỷ lệ mất vốn. Mọi ô dưới đây là **full512, cùng decision giữa các methods**,
average origins theo path trước khi bootstrap.

| Estimator | AR stationary | Markov stationary | Markov shift |
|---|---:|---:|---:|
| Raw | .057931 | .126753 | .133364 |
| iid OIC | .065205 | .177464 | .152493 |
| HAC | .071028 | .185075 | .156675 |
| Circular-block optimism | .071297 | .174919 | .151878 |
| Gaussian iid | .065557 | .085024 | .126229 |
| **AR Gaussian** | **.001635** | .085258 | .125974 |
| EWMA Gaussian | .140496 | .109422 | **.094580** |

Primary AR Gaussian − iid OIC = **−.06356938**, CI
**[−.07275199, −.05444518]**, n=32 clusters. AR Gaussian là well-specified
conditional family trong AR DGP này; không suy rộng thành thắng mọi temporal
market. Trong Markov stationary, Gaussian iid có point MSE thấp nhất trong
các baselines đã chạy; Markov shift có EWMA thấp nhất. Không chọn một method
sau test để gọi là winner phổ quát.

Secondary iid OIC − raw conditional MSE:

| World | Delta | 95% CI |
|---|---:|---|
| AR stationary | +.00727321 | [+.00517951, +.00931632] |
| Markov stationary | +.05071152 | [+.03958577, +.06255338] |
| Markov shift | +.01912896 | [+.01221483, +.02639758] |

Trong Markov shift **sau break**, conditional MSE raw=.143049,
iid OIC=.138635, EWMA=.107727. EWMA − iid OIC = −.03090809,
CI **[−.06099820, +.00648468]**, chưa phân biệt rõ theo CI secondary. Bảng cả
period và coupled shift-effect nằm trong CSV; không chỉ báo period thuận lợi.

## Marginal correction không giải quyết conditional mismatch

| Marginal MSE, full512 | AR stationary | Markov stationary | Markov shift |
|---|---:|---:|---:|
| Raw | .009303 | .026119 | .022771 |
| iid OIC | .006105 | .021973 | .019134 |
| HAC | .005612 | .023275 | .020142 |
| Circular-block optimism | .005662 | .021221 | .018032 |

HAC − iid OIC marginal MSE: AR −.0004930, CI [−.0011009,+.0001645]; stationary
Markov +.0013018, CI [−.0002679,+.0033731]; shift +.0010084, CI
[−.0003539,+.0027289]. Cả ba CI chứa 0. Circular-block − iid OIC cũng có CI
chứa 0 ở cả ba worlds. Không claim HAC/block method đã giải quyết residual gap.

HAC là documented local adaptation với Bartlett score covariance, không chứng
minh correction cho conditional risk. Circular bootstrap có **16 replicates**,
không phải independent future validation; max Monte Carlo SE .13085. Giữ
nguyên **8.618 negative replicate deltas**, **171/1.536 negative mean corrections**;
không clip về 0. Stationarity assumptions không được đảm bảo qua structural break.

Với cùng theta, identity được kiểm tra trên mọi row:

`estimate−R_next = (estimate−R_ref) + (R_ref−R_next)`.

R_ref là average unconditional marginal law trên đúng fitting dates. Đặt
A=(estimate−R_ref)/R_next, B=(R_ref−R_next)/R_next. Raw full512:

| World | E[A²] | E[B²] | E[2AB] | Conditional MSE |
|---|---:|---:|---:|---:|
| AR stationary | .012673 | .077258 | −.032000 | .057931 |
| Markov stationary | .048341 | .192608 | −.114196 | .126753 |
| Markov shift | .031726 | .154209 | −.052572 | .133364 |

Mismatch tồn tại ngay khi DGP stationary. Không thể gọi tất cả là distribution
shift. A gồm finite-sample estimation và selection, không tách được causal
selection riêng. Cross term âm cho thấy các sai số có thể bù nhau; không gán
phần trăm đóng góp bằng cách chia riêng hai square terms cho tổng MSE.

## Fixed-portfolio và chronological controls

Equal512 conditional MSE raw/iid OIC/AR Gaussian lần lượt: AR
.053487/.054852/.000923; stationary Markov .147655/.155228/.079699; shift
.132818/.135971/.112457. Conditional mismatch vẫn tồn tại khi weights cố định.
Threshold còn được fit, nên không coi chênh lệch policies là causal selection effect.

Older256 conditional MSE, cùng decision giữa các columns:

| World | Raw | Chronological 256 | Purged 240 | AR Gaussian | EWMA |
|---|---:|---:|---:|---:|---:|
| AR stationary | .074681 | .139737 | .141171 | .001926 | .205377 |
| Markov stationary | .109660 | .271543 | .265882 | .103292 | .161662 |
| Markov shift | .177421 | .269792 | .265717 | .157728 | .145986 |

Purging không tự biến empirical holdout average thành conditional next-step
forecast. Đây là kết quả của settings/window đã khóa; không kết luận mọi
time-series cross-validation vô dụng. Không đổi block/window sau khi thấy bảng.

## Verification, provenance và phần chỉ đọc

Tất cả main/bootstrap fits báo success. Max main convex gap 1,90e−11;
max bootstrap gap 1,64e−11. Verifier dùng dense Bartlett kernel, odds-form
filter, direct quadrature, OLS tính lại và cùng bootstrap indices đã lưu hash;
max discrepancy objective 1,20e−8, HAC 3,55e−15, filter 1,78e−15,
decomposition 1,33e−15. Đây là numerical/software audit, **không independent
peer review**. Không chứng minh temporal calibration/theorem từ tests.

Logs/timing/source/config hashes và full diagnostics ở run directory. Large
exports được publish gzip lossless, có SHA và roundtrip receipt; NPZ paths và
full checkpoints giữ local. Compact clone không tự resume nếu thiếu payloads.

**REPORTED/READ:** Q0/Q1 reports và historical source chỉ là evidence trước;
không rerun historical scientific comparisons. Đã đọc official
[statsmodels HAC documentation](https://www.statsmodels.org/stable/generated/statsmodels.stats.sandwich_covariance.cov_hac.html)
và [arch circular-bootstrap documentation](https://arch.readthedocs.io/en/latest/bootstrap/generated/arch.bootstrap.CircularBlockBootstrap.html).
NBER Newey–West page/PDF trả HTTP 403; Kunsch landing page không cung cấp full
text khả dụng. Full texts đó **NOT READ**, không claim paper reproduction.

## NOT_RUN và đúng một next action

**NOT_RUN:** learned HMM; market/Q3 full evaluation; utility; new APTC/neural
models; unsmoothed OIC; weak-face temporal theorem; calibrated VaR/ES scoring;
continuous conditional-optimum regret. Chưa có novelty hoặc trading claim.

**PROPOSED:** thêm baseline Gaussian HMM hai trạng thái fit chỉ từ past,
kiểm tra trên development rồi khóa một fresh-seed Markov pilot so với
Gaussian/EWMA hiện tại. Đây là closest-prior statistical control cần có trước
khi gọi residual Markov gap là cơ hội cho method mới.
