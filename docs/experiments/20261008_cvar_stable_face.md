# Q1: stable-face audit và pilot iid mới — 08/10/2026

**Đã hoàn thành bước tiếp theo: xử lý redundant active normals trên development,
khóa protocol, rồi chạy 128 cases mới. Primary full512 OIC-minus-raw MSE đạt
−.00371134, CI 95% [−.00592418, −.00143626].** Đây là bằng chứng cho OIC baseline
trên smoothed objective đã đăng ký. Không phải method mới đã thắng strong
independent-split control hoặc bằng chứng giao dịch thực tế.

**Pilot mới không có vertex suy biến.** Vì thế không thể quy mức cải thiện MSE
cho phần sửa vertex. Evidence của sửa vertex vẫn là derivation và kiểm tra
development/regression trên dữ liệu đã xem. Không thêm seeds sau khi biết điều
này, không đổi primary/tau và không ghép pilot cũ để tăng cỡ mẫu.

Branch `research/cvar-stable-face`, base `9238568dc95a057b614c793f21ebe4b4736bf159`.
Workspace sạch khi bắt đầu. **176 files tracked trước lượt này giữ nguyên bytes**;
main không merge. Code mới nằm trong `continuous_cvar_face/`, không sửa fitter
hoặc config/report lịch sử.

## VERIFIED — thực sự chạy

| Hạng mục | Kết quả và giới hạn |
|---|---|
| Tests | **76 PASS** trong 1,72 giây, gồm 19 tests mới; [log](../../runs/cvar_stable_face/20261008_face/tests.log) |
| Seen-array development audit | 128 arrays cũ / 1.152 fit targets; 14 old nulls được chứng nhận strict-face; không dùng population risk để chọn method |
| Development microbenchmark | 2 cases riêng, numerical gate PASS, estimate 20,16 giây với margin ×2, cap 600 giây |
| Fresh pilot | **128 cases / 64 seed clusters**, 1.152 smooth fits, 3.200 estimate rows; 0 failed cases, 0 OIC nulls |
| Fresh active geometry | 0 vertex targets; minimum positive margin 4,49e−5, lớn hơn tolerance khóa 1e−5 |
| Numerical verifier | KKT/SVD, direct quadrature, true-ES checks và **90 paired contrasts PASS** |
| Post-run vertex audit | Independent dual LP kiểm tra 14 targets cũ; hash 128 arrays khớp receipt lịch sử; không phải fresh confirmation |
| Resume | Partial 3 rồi 125 cases; complete resume 128 reused / 0 new; **262 artifacts byte-identical** |

Lệnh pytest không chỉ định thư mục đầu tiên gặp **collection error** do các test
trùng tên trong historical snapshot. Không test nào chạy trong invocation lỗi;
log/XML được giữ. Lệnh thành công chỉ định `tests quant_research_v2/tests`, bao
phủ các test hiện hành, không sửa archive. Không có lỗi numerical bị giấu bằng
việc loại observations.

Logs, thời gian đo chi tiết, warnings, nguồn, freeze và manifest ở
[run RESULTS](../../runs/cvar_stable_face/20261008_face/RESULTS.md).

## Applicability và thay đổi cụ thể

Đã đọc lại constrained assumptions trong Appendix 7.3.3 của
[OIC v4](https://arxiv.org/html/2306.10081v4). Bản này là extension theo geometry
của derivation KKT trước, không tái lập code chính thức hoặc chứng minh định lý
OIC mới. [Audit trước implementation](../../continuous_cvar_face/APPLICABILITY.md)
ghi rõ điều kiện, falsifiers và phạm vi giả định.

Với gradient theo weights `q` và budget multiplier `lambda`, free coordinates
cần `q_F+lambda=0`; lower coordinates cần `q_L+lambda>0`; upper coordinates cần
`q_U+lambda<0`. Tại vertex không có free weights, certificate strict tồn tại
nếu **max(q_U) < min(q_L)**. Chọn lambda ở giữa khoảng hợp lệ cho bound
multipliers dương, dù budget cùng bound normals có hàng dư thừa. Multipliers
least-squares âm của representation cũ không phủ định sự tồn tại certificate này.

Khi strict margins đạt, critical cone bằng tangent space của minimal face.
Basis N được dựng từ free weights có tổng thay đổi bằng 0 và threshold tự do.
Correction giữ công thức `mean[(g_i N)(NᵀHN)⁻¹(Nᵀg_i)]/n`. Ở vertex hai weights
bằng .5, local portfolio derivative bằng 0; chỉ threshold thay đổi. Finite
perturbations lớn vẫn có thể chuyển face; đây là đạo hàm local.

**Không chỉ bỏ kiểm tra rank.** Gate mới yêu cầu positive margin >1e−5 cùng
feasibility, stationarity, convex gap, reduced curvature và threshold interior.
Weak/zero-margin case có thể có directional derivative phi tuyến, bị từ chối.
Đã test counterexample đó và probability perturbations ±eps với eps 1e−5/1e−6.
Duplicate/rescale/reorder normals không đổi operator. Original optimizer,
theta/raw objective và feasible set giữ nguyên.

Seen regression: 14 old gate failures đều qua strict certificate; maximum
discrepancy với independent augmented KKT 1,15e−14. Correction ở các targets
vốn đã hợp lệ khác bản cũ tối đa 7,11e−14. Các kết quả này **không thay thế báo
cáo primary INCOMPLETE của lượt trước** và không được gộp vào inference mới.

## Frozen pilot và chống selection leakage

- Seeds mới `2026108000:2026108064`; audit 8.530 local files, observed-use
  collisions = 0 trước pilot. Audit không bảo đảm cho runs ngoài máy không có
  artifacts. Config/source khóa trước khi sinh fresh pilot outcomes.
- Gaussian và asymmetric crash, n512, 8 assets; `sum(w)=1`, `0<=w<=.5`,
  `v∈[-50,50]`; primary tau=.1, sensitivity .05/.2 từ trước.
- 64 seed clusters: hai families cùng seed được bootstrap cùng nhau, 10.000
  replicates. 1.152 fits/3.200 rows không phải số thị trường độc lập.
- Primary: full512 OIC_FACE-minus-raw **squared relative smoothed-objective
  error**, tại cùng locked decision. Mọi fit/correction xong trước khi evaluator
  nhận population parameters. Không chọn tau, model hay seeds từ test.
- Half A256/B256 raw/OIC/independent là secondary, mỗi chiều cùng decision.
  Independent dùng nửa 256 còn lại; full512 có nhiều fitting data hơn half256.
  Không so chúng như cùng decision. Các secondary CI không chỉnh multiplicity.

Đây là bounded feasibility pilot, không phải study đủ power để chứng minh
superiority phổ quát. Primary null nếu có sẽ khiến comparison INCOMPLETE theo
quy tắc đã khóa; lần này không có null.

## Kết quả tại primary tau=.1

Signed bias là mean relative error ×100, không phải phần trăm vốn mất.
MSE là mean squared relative error, không nhân 100. Target là expected smooth
objective tại `(w,v)`, không phải đã tạo một calibrated VaR/ES pair.

| Full512 scope | Raw signed bias (%) | OIC signed bias (%) | Raw MSE | OIC MSE |
|---|---:|---:|---:|---:|
| **Overall** | **−6,6737** | **−1,1755** | **.01191962** | **.00820828** |
| Gaussian | −4,2126 | −.7314 | .00388601 | .00262484 |
| Crash | −9,1347 | −1,6195 | .01995323 | .01379171 |

Primary delta **−.00371134**, CI **[−.00592418, −.00143626]**.
Overall bias CI: raw [−8,2605%, −5,1066%], OIC [−2,8730%, +.5180%].
Family deltas secondary: Gaussian −.00126117, CI [−.00208403, −.00043926];
crash −.00616151, CI [−.01024503, −.00195942]. Đây là hai family strata trong
cùng pilot, không hai xác nhận độc lập bổ sung.

| Same-decision split policy | Raw MSE | OIC MSE | Independent MSE |
|---|---:|---:|---:|
| A256 | .02818740 | .02188314 | **.01399947** |
| B256 | .03082685 | .02906762 | **.01783923** |

| Paired MSE contrast | Mean delta | 95% CI |
|---|---:|---|
| A256 OIC − raw | −.00630426 | [−.01251439, +.00096850] |
| B256 OIC − raw | −.00175923 | [−.01480660, +.01619280] |
| A256 OIC − independent | **+.00788367** | **[+.00088442, +.01581746]** |
| B256 OIC − independent | +.01122839 | [−.00415282, +.03021983] |

Independent split có point MSE thấp hơn OIC ở cả hai chiều. A256 paired
secondary CI không chứa 0; B256 vẫn chứa 0. Không chọn chiều thuận lợi làm
primary, không coi hai chiều là hai samples độc lập. Full512 OIC tốt hơn raw
ở primary không đồng nghĩa OIC đã thắng independent evaluation.

## Sensitivity, decision quality và numerical checks

Full512 OIC-minus-raw MSE: tau=.05 −.00396454, CI [−.00637617, −.00147647];
tau=.2 −.00257142, CI [−.00417297, −.00098367]. Giữ primary .1. Ba tau nhắm ba
smoothed objectives khác nhau, không chọn bandwidth từ bảng này.

| tau | Mean smoothing gap | Mean threshold gap | Continuous ES regret (%) |
|---|---:|---:|---:|
| .05 | .0102188 | .0138348 | 2,7858 |
| .1 | .0383273 | .0113450 | 2,5819 |
| .2 | .1262310 | .0280348 | 2,2516 |

Raw/OIC cùng w nên true ES/regret giống nhau. Correction không cải thiện decision
trong thiết kế này. Exact empirical LP và continuous population ES oracle có
chạy như reference riêng; không gán OIC cho nonsmooth LP, không so continuous
regret với bank285 historical regret.

1.152/1.152 smooth optimizers success; 0 fitting warnings; max convex gap
3,16e−11, minimum reduced eigenvalue .02536, maximum condition 402,76. Verifier
độc lập về cách tính có max KKT discrepancy 2,18e−14 và max direct-quadrature
discrepancy 2,94e−8. Đây là software/numerical verification, không independent
peer review hoặc chứng minh population active-set recovery.

## REPORTED / chỉ đọc và NOT_RUN

Q0 crossed, bank285 split và pilot continuous trước là evidence đã công bố;
không chạy lại scientific comparisons của chúng. Lượt này chỉ đọc source paper,
đọc các reports đó và dùng arrays cũ cho numerical regression. Archive là lịch
sử, không task list. Không sửa kết quả cũ hoặc gom old/new inference.

**NOT_RUN:** fresh vertex-enriched scientific evaluation; weak-face directional
OIC; unsmoothed/discrete OIC; Q2 dependent/regime-change benchmark; Q3 market
evaluation; utility; APTC/neural variant search. Không có novelty, market PnL,
Sharpe, hay corrected VaR/ES calibration claim.

## PROPOSED — đúng một next action

**Mở Q2 với protocol development tách dependence và regime change, khóa
time-aware split/statistical controls trước một temporal pilot mới.** Giữ OIC
iid và independent split hiện tại làm baselines; không mở model mới từ pilot
đã xem. Q1 đã có baseline đúng phạm vi, không còn lý do diễn giải selection
optimism như lợi thế riêng của APTC.
