# Novelty audit: tối ưu kiểm tra thứ hạng ES, bác bỏ conditional-transport shortcut

**Kết luận:** đã có code, chứng minh cấu trúc, thực nghiệm tổng hợp và tối ưu
runtime; **chưa có method novelty đủ cơ sở để tuyên bố**. Thuật toán kiểm tra
thứ hạng ES là một chuyên biệt hóa hữu ích của Rockafellar–Uryasev (RU), còn
finite-window transport chỉ sửa optimism trung bình, không khôi phục rủi ro
có điều kiện theo lịch sử đang quan sát. Giữ cả hai kết luận âm này.

Ngày 2026-10-08, branch `research/conditional-risk-novelty`, nền
`662e5dd0757cc72c8080844c66fce82eee8e7762`. User chuyển ưu tiên sang tìm novelty;
decision được ghi trước tìm kiếm và chạy trong
[start receipt](../../runs/novelty_audit/20261008/start_receipt.json).
Fetch origin/main cuối lượt xác nhận `f6dcffdf6ab7e22a9246aadb17df437e3aae8c6e`
đã là tổ tiên của branch. Không cần tích hợp thêm commit main; không merge main.
Workspace đầu lượt sạch và **320 file tracked cũ giữ nguyên SHA-256**.

## Bằng chứng nào đã thực sự có

| Trạng thái | Nội dung |
|---|---|
| **VERIFIED / RUN** | 128 tests PASS; 256 finite-mixture cases; 9 AR(1) cells × 32,768 lịch sử độc lập = 294,912 lịch sử; exact rational witness; 96 phép giải LP độc lập đối chiếu; kiểm tra partial/full/no-op resume |
| **READ / REPORTED** | Kết quả HMM cũ; tài liệu Q0/Q1/Q2; nội dung papers theo mức truy cập; những phép stress bổ sung do AI reviewer tự báo cáo |
| **PROPOSED** | Cận thứ hạng ES khi cả xác suất chế độ và phân phối thành phần được ước lượng từ cùng lịch sử; chưa có định lý/coverage mới |
| **NOT RUN** | Q3 market evaluation, model/neural sweep mới, utility/reserve/backtest, estimation của component uncertainty, kiểm tra trên người phản biện độc lập |

Protocol khóa trước kết quả ngẫu nhiên: [PROTOCOL.md](../../mixture_order/PROTOCOL.md).
Source/config/environment fingerprint:
`20fb8274846a086e168329758f0b8fcb5615daed40cfe54c8dc99cadd55f2e63`.
Đây là kiểm tra toán học/phần mềm trên dữ liệu tổng hợp, không phải dữ liệu tài
chính thật. Không huấn luyện/chọn model bằng test đã xem. Counterexample đã
được suy ra trước stochastic run nên được gắn **development evidence**.

## 1. Kết quả có thể dùng: kiểm tra ES ở chung một phân phối

Với hai danh mục **cố định** A,B, hai luật thành phần đã biết và q trong một
khoảng cho trước, code tính:

\[
U=\max_q\{ES_\alpha(A;(1-q)P_0+qP_1)-ES_\alpha(B;(1-q)P_0+qP_1)\}.
\]

Alpha=.05 là xác suất của **đuôi lỗ 5%**. Đây không phải ES(A−B), cũng không
phải lấy max ES(A) và min ES(B) ở hai q khác nhau. Không thêm correction tùy ý
vào VaR/ES. Atoms dùng đúng phần khối lượng cần để đủ đuôi.

Phản ví dụ kiểm tra bằng phân số chính xác:

- Chế độ 0: A lỗ 0; B lỗ 1.
- Chế độ 1: A lỗ 10; B lỗ 11 với xác suất .05, còn lại lỗ 0.
- Hai danh mục có thể nhúng vào bốn tài sản với weights (.5,.5,0,0) và
  (0,0,.5,.5), bằng cách lặp loss của từng cặp tài sản.

| q | ES(A) | ES(B) | A−B |
|---:|---:|---:|---:|
| 0 | 0 | 1 | −1 |
| .05 | 10 | 1.5 | **+8.5** |
| 1 | 10 | 11 | −1 |

Chỉ chấm hai chế độ riêng sẽ kết luận A tốt hơn, nhưng tại hỗn hợp q=.05 thì
thứ hạng đảo ngược. **Không mâu thuẫn Q2 cũ:** objective khi khóa cả (w,v) là
affine theo q; ở đây threshold VaR được tối ưu lại để lấy ES thật của mỗi luật.

Với finite support, cumulative probability là affine theo q. Threshold chỉ
đổi khi cumulative mass chạm alpha. Giữa hai điểm đổi của A hoặc B, hiệu ES là
affine; maximum nằm ở một điểm đổi hoặc đầu mút. Prefix moments và binary
search cho O(S log S) thời gian, O(S) bộ nhớ. Chứng minh và code nằm trong
[package](../../mixture_order/README.md).

**Baseline mạnh:** generic lower envelope của các RU affine threshold costs
cũng O(S log S). Vì vậy không gọi đây là thuật toán mới về độ phức tạp.
ES concave theo **mixture distributions** là kết quả đã biết; tác giả của
[On the Concavity of Expected Shortfall](https://arxiv.org/pdf/1910.00640)
còn ghi nhận prior result của Pertaia–Uryasev. Không nhận tính chất này là mới.

### Đo thực tế

256 ca mới, không loại ca nào; support A có n atoms, B có n+3. Cả hai phương
pháp gồm validation/sorting/preprocessing, chạy luân phiên thứ tự, 5 lần/case;
bảng là median của các median theo case. Đây là timing hai implementation
Python/NumPy trên máy hiện tại, không phải benchmark tối ưu mọi thư viện.

| n của A | Ca | Mass crossings (ms) | Generic RU hull (ms) | Hull / crossings |
|---:|---:|---:|---:|---:|
| 8 | 64 | .134 | .095 | .70× |
| 32 | 64 | .158 | .119 | .75× |
| 128 | 64 | .196 | .211 | 1.07× |
| 512 | 64 | .281 | .568 | **2.02×** |

Bản chuyên biệt chậm hơn ở hai cỡ nhỏ. Hai bản khớp upper value với sai số lớn
nhất **8.22e−15**, toàn bộ piecewise curves **1.07e−14**. 96 independent
risk-envelope LP solves có sai số lớn nhất **7.25e−15**.

Chỉ dùng endpoints đánh giá thiếu maximum ở **11/256** ca, lớn nhất .607751
đơn vị loss tổng hợp. **0/256** ca ngẫu nhiên kết luận endpoint-safe sai; chỉ
có witness dựng trước chứng minh khả năng đó. Không suy tần suất xảy ra trên
thị trường. Cận tách max/min có slack trung bình .068559 so với chung q;
đây là conservatism của cận, không phải lợi nhuận.

“Exact” ở đây chỉ cấu trúc liệt kê đầy đủ các đoạn; tính toán là float64,
không phải interval arithmetic hay statistical confidence certificate. Overflow
phải raise; trường hợp sát 0 không mang bảo đảm formal về dấu.

## 2. Kết quả bác bỏ: sửa optimism trung bình không đủ cho conditional risk

Mô hình kiểm tra là stationary Gaussian AR(1), Var(X)=1, theta_hat=sample mean,
loss bằng **một nửa squared error**. Cả correction và direct predictor đều
nhận oracle phi và variance. Không đưa oracle này vào bảng thắng thua của model
học từ dữ liệu. Không dùng một realized future loss làm truth.

Conditional target chính xác:

\[
r_T=\tfrac12[(\bar X-\phi X_T)^2+1-\phi^2].
\]

Đặt G=r_T−training half-loss. Với u=1/T, a=u−phi e_T,
A=.5(aa'−I/T+uu'), c=.5(1−phi²), ta có G=X'AX+c. Do đó
E[G]=Delta và Var(G)=2 tr(A Sigma A Sigma)>0.

Finite-window correction Delta tối ưu trong lớp **hằng số cộng** theo MSE,
nhưng residual conditional MSE vẫn bằng Var(G). Monte Carlo so với đáp án
trace giải tích; tất cả mean/MSE checks qua ngưỡng predeclared 6 SE, không
diễn giải đây là discovery significance hay tuning.

| T, phi=.9 | Delta hữu hạn | Infinite-lag correction | Conditional MSE còn lại của exact finite correction |
|---|---:|---:|---:|
| 32 | .152411758 | .312500000 | .199682819 |
| 128 | .067138785 | .078125000 | .319287526 |
| 512 | .018844604 | .019531250 | .329300427 |

Sai số có điều kiện không biến mất khi tăng T: theo luật số lớn,
G−Delta hội tụ về .5 phi²(X_T²−1) về sai số L2 trong quá trình stationary,
nên MSE tiến tới **phi⁴/2** (.32805 khi phi=.9). Đây là suy ra toán học của
root, không phải một model mới hay claim priority. Nó giải thích vì sao sửa
“bias theo trung bình” có thể ngày càng gần 0 nhưng vẫn bỏ sót biến động của
rủi ro hiện tại. Không loại trừ các estimator phụ thuộc lịch sử được xây đúng.

AI A ban đầu gọi FW-PT là conditional candidate; sau phản biện quadratic-form
đã hạ xuống control và ghi append-only correction. Sai khác factor .5 trong
proposal ban đầu cũng được giữ và đính chính. Không train tail model để cứu
claim đã trượt phép kiểm tra đơn giản này.

## 3. Novelty adjudication và prior art

Independent generation trước search: root và hai AI reviewer ghi ý tưởng riêng;
reviewer B phản biện candidate của root, root phản biện candidate A/B. Đây là
**AI-assisted review, không phải human independent peer review**. Tiêu chí
đặt trước: algebra/prior equivalence có quyền veto, estimand rõ, thông tin
tương xứng, tractability và finite falsifier. Không chọn bằng bỏ phiếu.

| Nhánh ý tưởng | Quyết định hiện tại |
|---|---|
| HMM + DRO / uncertainty trên mixture weights | Broad mechanism đã có; không đủ novelty |
| Composite conditional OIC / covariance penalty | Ingredient đã có; phải chứng minh target mới, không chỉ đổi tên |
| FW-PT | Bác claim terminal recovery; giữ integrated-bias control |
| State-weighted block deletion, tangent-cone/selective/FZ envelope | PROPOSED/control; chưa có conditional coverage theorem hay lợi ích riêng |
| KL support completion | NO-GO: nếu Q tuyệt đối liên tục theo P thì không tạo mass ngoài support P |
| Shared-mixture ES certificate | Code đúng, hữu ích, có tối ưu cục bộ; equivalent RU structure, standalone novelty NO-GO |

Các nguồn sát nhất: [OIC v4](https://arxiv.org/html/2306.10081v4) đã có
composite optimizer và contextual extension trên iid context pairs;
[Säfken–Kneib](https://onlinelibrary.wiley.com/doi/10.1111/sjos.12437) đã xét
conditional covariance penalties. Terminal observed-history là estimand cần
phân biệt, nhưng chỉ đổi estimand bằng lời chưa tạo ra một estimator hợp lệ.

[Pun–Wang–Yan 2023](https://pubsonline.informs.org/doi/10.1287/msom.2023.1229)
đã kết hợp HMM/covariates với regime-switching CVaR-DRO;
[Huang et al. 2010](https://www.sciencedirect.com/science/article/pii/S0377221709005104)
đã có relative robust CVaR. Root chỉ đọc abstract/preview của hai bài này,
chưa kiểm chứng mọi phương trình. Không dùng thiếu full text để nhận novelty.
[Bitar 2024](https://arxiv.org/html/2412.15406v1) là prior robust regret;
CVaR của pathwise regret cần phân biệt với hiệu hai CVaR đang xét.

Root có 28 query nghiên cứu và 2 query xác minh metadata; query/access logs và
reviewer reports ở [run directory](../../runs/novelty_audit/20261008/).
Tìm kiếm này có giới hạn, không phải systematic review/priority clearance.
Một số full-text fetch thất bại; [source access matrix](../../runs/novelty_audit/20261008/source_access.json)
ghi rõ phần VERIFIED_SOURCE và NOT_READ. Không commit nguyên văn papers.

## 4. Runtime, lỗi đã sửa, kiểm chứng và phạm vi

Preflight qua với dự toán 3.94 s; tổng thời gian các case đo được 1.212 s.
Partial invocation .031 s, resumed full invocation 1.412 s. Đây là finite
NumPy checks nhỏ, không phải thời gian training HMM. Timings, warnings và ETA
ở run logs; không thêm log dài vào README.

Partial 5/265 exit **3**; full resume thêm 260 case exit **0**; completed
resume thêm **0** case, 265 checkpoint giữ nguyên hash. Freeze source/config/
environment và checkpoint payload được kiểm tra; mixture input được tái sinh
từ seed để chống nhầm checkpoint. Hash không phải chữ ký chống người sửa cả
code và receipts. AR resume kiểm tra metadata, còn verifier cuối đã tái sinh
đúng cả 294,912 histories; lần tái sinh là **reproduction, không bằng chứng
độc lập mới**.

Development ghi 25 PASS/2 FAIL do một expected variance trong test mới bị suy
ra sai; đã sửa trước freeze, không đổi thuật toán để khớp kết quả mong muốn.
Reviewer còn phát hiện partial-exit ambiguity và intermediate overflow; cả hai
được sửa trước full run, có regression tests. Final **128 PASS**, warnings số
học trong audit **0**, không loại case thất bại.

[Verification receipt](../../runs/novelty_audit/20261008/verification.json)
khóa 265 completed cases, 96 LP checks, 320 historical hashes và nguồn main.
[Code/run commands](../../mixture_order/README.md) tái lập được trên environment
đã ghi. Dữ liệu cũ HMM chỉ **đọc lại báo cáo**: conditional MSE stationary
.0095968 so với iid Gaussian .0952384; không refit lại ở lượt này và không
gọi kết quả đó là novelty. Q3 vẫn NOT RUN do user đổi ưu tiên.

## Đúng một next action

**Kiểm tra một định lý/counterexample cho cận thứ hạng ES khi component laws
cũng phải ước lượng từ cùng lịch sử**, đối chiếu trực tiếp relative robust
CVaR và regime-switching DRO. Điều kiện qua: phải chỉ ra bảo đảm mới hoặc độ
chặt tốt hơn ở cùng thông tin và assumptions; nếu công thức quy về baseline
cũ thì dừng nhánh này. Hiện đây là **PROPOSED, novelty NOT ESTABLISHED**;
không kéo dài search/huấn luyện để ép một kết quả dương.
