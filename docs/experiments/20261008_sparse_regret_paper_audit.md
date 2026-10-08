# Sparse ES regret: kết quả chạy và trạng thái bản thảo

**Ngày:** 2026-10-08. **Branch:** `research/sparse-regret-paper-audit`.
Base `e03b5a6c16ec298075dbb0269be30edc82b4cdba`; main đã fetch ở
`f6dcffdf6ab7e22a9246aadb17df437e3aae8c6e`. Không merge main.

## Kết luận được phép

Đã có một **kết quả cấu trúc đúng trong phạm vi nêu rõ**, implementation chạy
được, full computational audit và một bản thảo technical note. **Chưa xác lập
novelty/priority và chưa sẵn sàng nộp paper.** Hai phản biện AI đều không tìm
thấy lỗi chặn của chứng minh cuối; cả hai giữ đánh giá rằng đây là một hệ quả
hình học hẹp của các nguyên liệu đã biết, không phải một risk measure hoặc
forecaster mới. Không dùng việc tests pass để thay thế prior-art audit.

Đóng góp đang xem xét là một gói cụ thể:

1. Với mỗi action cố định, worst **ES-difference regret** trên toàn simplex
   của R component laws có một nghiệm dùng tối đa **hai component**, kể cả
   component liên tục hoặc đuôi không bị chặn nhưng khả tích.
2. Ghép J mức ES có bound **J+1**; affine ambiguity constraints cộng thêm
   active rank. Đã chứng minh bound này chặt với mọi J mức phân biệt: một construction có nghiệm duy nhất dùng đủ J+1 component, kể cả chỉ hai actions.
3. Với finite supports, dùng một bank lower hull trên mỗi cạnh và chỉ truy
   vấn các knot của chính action cần đánh giá; trả cả competitor và mixture
   witness. Có LP độc lập trên toàn R-dimensional simplex để đối chiếu.

Đây là scope cho bản thảo, không phải tuyên bố “đầu tiên”. Xem
[bản thảo](../../papers/sparse_es_regret/manuscript.md),
[chứng minh](../../papers/sparse_es_regret/THEORY.md) và
[đối chiếu prior art](../../papers/sparse_es_regret/PRIOR_ART.md).

## VERIFIED / thực sự chạy trong lượt này

| Kiểm tra | Kết quả |
|---|---|
| Full matrix đã khóa | **168/168 case**: 72 LP-comparison, 72 scaling, 24 rational |
| LP độc lập trên full simplex | **29.847 solves** trong assessment; không dùng định lý support-two |
| Sai khác lớn nhất, toàn regret vector | **1.0436096431476471e-14** |
| Sai khác witness/competitor lớn nhất | **1.1324274851176597e-14** |
| Raw argmin disagreement | **0** |
| Numerical warnings trong full assessment | **0** |
| Exact rational oracle | **4.960 hệ active-set**; verifier kiểm tra **72 action witnesses** bằng phân số |
| Continuous-law diagnostic | **32 mixture points / 96 action checks**, normal và Student-t3; đạt |
| J=2 sharpness | Unique support-three maximizer; exact edge gap **1112324/5386535** |
| General-J construction mới | **16/16 case**, J=1…8 với hai recipes; **104 LP**, mọi mặt biên; 0 warnings |
| Tests cuối | **167 passed**, 7.48 giây; `tests quant_research_v2/tests` |
| Resume một phần | **3/3 checkpoint** giữ nguyên, chạy tiếp 165 case |
| Resume sau hoàn tất | **168/168 checkpoint** giữ nguyên, **0 case mới**, 0.3353 giây |
| Bảo toàn lịch sử | **4.137 file tracked trước lượt này** giữ nguyên SHA256 |

Preflight dùng seed development riêng: 3 case, tổng thời gian thực 21.326 giây;
dự phóng bảo thủ 1606.55 giây dưới giới hạn 1800. Assessment thực 242.836 giây
qua hai invocation. Timings đầy đủ, tqdm, ETA, cảnh báo và checkpoint nằm trong
[`runs/sparse_regret_audit/20261008/`](../../runs/sparse_regret_audit/20261008/).
Các số LP ở bảng trên không cộng thêm development preflight hoặc unit tests.

Freeze SHA256:
`3768946e9fd8a403f94c86967cb229cc3e2bdb8996f5cbb3032e6610aa33d338`.
Mac ARM64, Python3.13.15, NumPy2.3.5, SciPy1.17.0, một BLAS thread,
benchmark chạy tuần tự. Đây là finite synthetic computational evidence,
không phải 168 thị trường độc lập. Float64 matching không phải outward-rounded
certificate hay statistical coverage guarantee.

### Tốc độ và kết quả không thuận lợi

Control `union` dùng cùng bank hull; vì vậy comparison này chỉ đo tác dụng
của own-knot pruning. Trong 72 scaling inputs, median của paired timing ratios
`union/local` là **1.055×** ở α=.05, **1.138×** ở α=.2 và **.969×** ở α=1.
Local nhanh hơn trên 56/72 input medians; 16 case còn lại được giữ nguyên.
Hai đường α=1 gọi cùng mean shortcut, nên khác biệt là timing noise.

Ở M=256,S=128,R=12, hai input-level ratios là **1.209–1.211×** ở α=.05 và
**1.370–1.434×** ở α=.2. Đây là cải thiện vừa phải. Generic LP có thể cạnh
tranh/thắng ở bank nhỏ, nhiều component; LP chỉ được timing một lần, edge
solvers ba lần. Không dùng speed ratio rất lớn của LP ở α=1 để quảng bá
algorithm: LP reference không có mean shortcut và là correctness oracle.

![All scaling cases](../../runs/sparse_regret_audit/20261008/timing.png)

Không chọn lại recipe, không bỏ timing xấu, không retime để làm đẹp. Các case
lớn chỉ so local/union có shared code; independent LP chỉ chạy trong declared
small/rational matrix. CSV giữ mọi cell và raw timings ở từng checkpoint.

### Mở rộng toán học sau full run

Đã dựng proof cho mọi J mức ES phân biệt và weights dương. Một hệ tuyến tính
định nghĩa các component laws quanh reference distribution; điểm trộn đều là
nghiệm duy nhất. Bound định lượng ở mọi mặt biên là
`epsilon * min(weight) / (2J)`, và là `epsilon/(2J²)` khi weights bằng nhau.
Đã chạy riêng 16 cases J=1…8, kiểm tra các đẳng thức bằng `Fraction` và
104 LP trên full simplex/từng boundary face. Tổng 0.1326 giây; gap đo nhỏ nhất
3.2150e-5. Resume xác nhận 16/16 checkpoint không thay bytes. Đây là
**exploratory construction check**, không cộng vào matrix 168 đã freeze.

Hai lỗi công thức trong bản review đầu (top-atom gradient và epsilon cho
reference không đều) được root phát hiện và sửa, giữ correction trail. Một
lỗi parse ở script lắp receipt giả định Fraction luôn có dấu `/`; đã sửa
bằng `Fraction`, không đụng computation/checkpoint. Chi tiết nằm trong
`sharpness_family/verification.json` và `reviews/general_j_sharpness_b.md`.

## READ / REPORTED — không gọi là chạy mới

- Đã đọc actual PDFs của **Huang2010**, **Zhu/Fukushima2005 report→2009
  article**, **Pertaia/Uryasev2019**. Đã đối chiếu RU general-law formula,
  Acerbi/Tasche atom formula, mixture concavity, Tao/Deng CVaR MRO và Bitar
  CVaR-of-regret. Links, page/equation pointers và access limits ở prior-art
  table; original PDFs không commit.
- **Hai Fan2026 chỉ đọc abstract/metadata**; full texts trả403; đã kiểm tra author page nhưng không có alternate mở. Abstracts nói score/risk-function mixtures; không suy diễn toàn văn. **Winkler1988 chỉ đọc abstract**, nhưng định lý generic của ông được đối chiếu qua Theorem12 của **Pinelis**, và **Henrion–Kružík–Weis** đã đọc phần định lý. Generic moment/rank sparsity là prior art.
- Full policy run trước ở commit`e03b5a6` là evidence cũ đã xem. Không chạy lại
  policy hoặc dùng outcomes đó để chọn model. Các kết quả mixed/negative của
  policy tiếp tục giữ nguyên; run mới không chứng minh chúng đã được cải thiện.
- Two-component sharpness fixture là construction từ lượt trước, được recheck
  ở implementation mới. J=2 fixture và general-J family là exploratory mathematical constructions,
  không giả thành preregistered stochastic confirmation.

## PROPOSED / NOT RUN

Định lý và thuật toán cho one-level finite bank đã có proof/code; spectral
J+1 là proof với all-J sharpness, J=2 exact fixture và 16 construction checks, **chưa có production J-level solver**.
Continuous laws có proof và diagnostic point-wise, **chưa chạy global continuous
optimization benchmark**. Constrained-simplex rank extension có proof;
**chưa implement arbitrary constrained-region optimizer**.

Không chạy mới: learned forecaster, OIC, HMM, neural sweep, market evaluation,
reserve utility, execution-cost/PnL/Sharpe, continuous portfolio optimizer,
GPU/memory benchmark hoặc journal submission. Không gọi các việc này là đã
hoàn tất nhờ kết quả hình học.

## Hồ sơ bản thảo và giới hạn readiness

Có 28 claim IDs, 22 evidence records, source-access ledger, proof supplement,
hai figures xuất PNG/PDF từ dữ liệu và code tái tạo. Reference-schema check
pass; có 18 warnings cho 9 local artifacts không có DOI/URL. Numeric consistency
check pass. **Human-verification claim gate chưa pass**: 154 findings đều là
chưa có human verification cho 28 claims và 63 claim/source mappings, được
kiểm tra cả registry lẫn manuscript markers; không gán tên người xác
nhận giả. Initial schema/audit failures được giữ rồi sửa schema, không xóa log.

Plot đầu có Fontconfig cache warning và nhãn P3 chạm tiêu đề; đã sửa layout,
vẽ lại và kiểm tra trực quan. Warning nằm trong`plot_warning.txt`, tách khỏi
0 numerical solver warnings. Môi trường vẽ riêng Python3.11.16/Matplotlib3.11.1/
NumPy2.4.6 không thay environment đã freeze của benchmark.

Root đã sửa hai điểm từ review: regret chỉ convex **trên own quantile cell**;
trong constrained example, chỉ **mọi maximizer** cần ba component, không phải
mọi feasible point. Preprocessing complexity được cộng rõ. Review B ban đầu
nhầm rằng rational path chỉ kiểm tra scalar; correction xác nhận full vector
đã được kiểm tra, rồi root bổ sung exact stored-witness verifier riêng. Các
review/correction được giữ nguyên provenance. AI review không phải peer review.

Phần chưa khép lại để nói “cf novelty”: kết quả có tính hệ quả từ moment/
extreme-point geometry; đã xác nhận generic moment overlap; chưa loại trừ overlap ở hai Fan full texts còn thiếu, và
chưa có đánh giá độc lập của nhà nghiên cứu về mức đóng góp. Vì vậy
`writing_package_complete=true`, `novelty_priority_confirmed=false`,
`submission_ready=false` là trạng thái thực trong
[`readiness.json`](../../papers/sparse_es_regret/readiness.json).

## Tái lập và bước tiếp theo duy nhất

```sh
rtk proxy env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 .venv/bin/python -m sparse_regret.run --out runs/sparse_regret_audit/20261008/frozen
rtk proxy .venv/bin/python scripts/verify_sparse_regret.py
rtk proxy env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 .venv/bin/python scripts/check_spectral_sharpness.py
rtk proxy env MPLCONFIGDIR=/private/tmp/riskdecision-mpl XDG_CACHE_HOME=/private/tmp/riskdecision-plot-cache /Users/alvinluong/miniforge3/bin/python scripts/export_sparse_regret.py
rtk proxy env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 .venv/bin/python -m pytest tests quant_research_v2/tests -q
```

Resume dùng cùng environment/source; environment khác phải tạo run directory
mới. Byte preservation là giữ nguyên checkpoint đã serialize, không hứa
hai lần chạy độc lập có bytes giống nhau vì payload có timestamp.

**Gate còn thiếu:** đối chiếu toàn văn hai Fan preprints khi có bản truy cập hợp lệ và đánh giá mức đóng góp của theorem/algorithm package. Generic moment attribution đã được bổ sung; không thể dùng search non-hit để xác nhận priority.
