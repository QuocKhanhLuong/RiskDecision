# Astra — RiskDecision: hoàn tất import, tải dữ liệu chính thức và chạy local

Bạn đang làm việc trên máy local của tôi, repository:
https://github.com/QuocKhanhLuong/RiskDecision

Đây là nhiệm vụ thực thi: đọc code, tải dữ liệu, kiểm tra phương pháp, chạy thí nghiệm, kiểm tra artifact và đưa thay đổi lên GitHub. Không chỉ viết thêm kế hoạch. Không bịa dữ liệu/kết quả, không để một lỗi download biến thành kết quả giả lập được gọi là market backtest.

## 1. Hoàn tất đưa TOÀN BỘ nghiên cứu cũ vào Git trước khi sửa code

Đọc README.md, docs/IMPORT_STATUS.md, archives_manifest.json và docs/LOCAL_EXECUTION_PLAN.md. Repo được khởi tạo qua connector nên chỉ chứa một phần các file gốc; chưa có toàn bộ snapshot lớn. Không hiểu nhầm thiếu cache là thí nghiệm chưa từng chạy.

Tìm đúng hai archive gốc trong thư mục Downloads hoặc workspace được cấp quyền:
- Quant_Tail_Risk_Method_and_Pilot.zip
- Quant_Risk_v2_Code_Results.zip

Không tìm trên toàn bộ ổ đĩa cá nhân và không dùng một ZIP khác trùng tên mà bỏ checksum. Chạy từ root:

```bash
python3 scripts/import_chat_archives.py --archive-dir "$HOME/Downloads" --verify-only
python3 scripts/import_chat_archives.py --archive-dir "$HOME/Downloads"
```

Script kiểm SHA256 toàn archive, số file và từng file đã có; không được overwrite một file khác nội dung. Hai archive chứa tổng 931 file lịch sử. Nếu thiếu archive, hoàn thành phần tải/chạy có đủ source, nhưng ghi rõ import chưa đầy đủ; không tạo file rỗng để lấp chỗ thiếu. Nếu tôi đã giải nén gói đầy đủ, kiểm tra hash thay vì copy đè.

Kiểm tra git status, origin và HEAD; bảo toàn thay đổi chưa commit. Tạo branch riêng, ví dụ research/local-market-validation, từ HEAD thực tế. Import các file còn thiếu vào đúng hai thư mục quant_tailrisk_pilot/ và quant_research_v2/. Chỉ stage các đường dẫn nghiên cứu đã kiểm tra. Được commit và push toàn bộ snapshot mô phỏng này vì tôi đã yêu cầu đưa toàn bộ vào repo public. Không đưa token, môi trường, private files hay dữ liệu thị trường mới tải vào commit đó. Không force-push main. Ghi receipt SHA256/counts và cập nhật IMPORT_STATUS.md sau khi import thực sự hoàn tất.

Tách commit import-history khỏi commit sửa code/chạy dữ liệu thật. Không sửa lịch sử để khiến nó khớp kết quả mới.

## 2. Đọc source of truth và giữ kết quả âm tính

Đọc tối thiểu:
- quant_research_v2/RESULTS_VI.md
- quant_research_v2/docs/METHOD_V2.md
- quant_research_v2/docs/PROTOCOL.md
- quant_research_v2/docs/DATASET_AUDIT.md
- quant_research_v2/docs/MARKET_PROTOCOL_NOT_RUN.md
- quant_research_v2/results/selection_freeze.json
- quant_research_v2/src/research.py
- quant_research_v2/src/market_data.py
- quant_research_v2/src/run_market_risk.py
- quant_research_v2/tests/
- tài liệu method/sources của pilot v1.

Bằng chứng cũ là mô phỏng, KHÔNG phải market backtest. V2 chạy 80 validation + 320 test instances, 18 cấu hình. Baseline chọn trên validation là historical_se_penalty (~14.30% relative ES error); candidate là support_band50 (~15.01%). APTC v2 chưa chứng minh thắng. Một phần lợi ích đã được giải thích bởi pure support mixture. Band là heuristic, không phải confidence guarantee. Không có DL đã chạy trong package này.

Giữ cả hai nhiệm vụ: báo cáo rủi ro đúng và chọn danh mục ít rủi ro. Không trộn chúng thành một score tùy ý.

## 3. Môi trường và bảo toàn snapshot

Máy được báo cáo là Apple M4 Pro/24 GiB; kiểm tra thực tế. Ghi OS, chip, RAM, Python, package versions, numerical threads và device. GMM/scipy/sklearn chạy CPU; không ép sang MPS hoặc cài neural stack chỉ để dùng GPU.

requirements.txt chứa phiên bản pin; chọn Python có wheel tương thích, ưu tiên kiểm tra Python 3.13 như môi trường cũ. Dùng uv nếu đã có hoặc venv. Không âm thầm sửa pins; nếu phải thay, tạo lockfile local mới và ghi lý do.

```bash
cd quant_research_v2
python -m pip install -r requirements.txt
python -m pytest -q
```

Import đã được kiểm bằng 26 tests trong ChatGPT, nhưng bạn phải báo kết quả chạy local của chính mình. Không dùng con số cũ làm receipt mới.

research.py có CFG thực thi; config.json không tự động điều khiển mọi CLI. audit.py/make_report.py/synthetic runner có thể ghi đè receipt/results. Audit hoặc tái lập toàn bộ trên bản copy riêng dưới work/, không overwrite snapshots gốc. fetch_probe.py là probe cũ có đường dẫn /mnt/data và dependency requests; không dùng nó làm entrypoint local mặc định.

## 4. Tải dữ liệu thật theo thứ tự

### A. ECB reference FX — thí nghiệm chính

Nguồn cần xác minh lại:
- https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html
- https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.zip
- https://www.ecb.europa.eu/services/using-our-site/disclaimer/html/index.en.html

Panel đã đề xuất: USD, JPY, GBP, CHF, SEK, NOK, CAD, AUD. Giữ cutoff 2025-12-31 để tránh tự mở rộng mẫu sau khi xem kết quả. Lấy đầu lịch sử thực sự có chung dữ liệu, báo đúng counts, không bịa first date.

Từ quant_research_v2/:

```bash
python src/market_data.py --source ecb --out ../data/raw/ecb
```

Nếu urllib gặp lỗi, chẩn đoán HTTP/DNS/TLS; dùng bounded retry/backoff hoặc curl chuẩn vào cùng endpoint chính thức rồi --raw-file. Không tắt TLS verification, không bypass CAPTCHA/login và không tự dùng community mirror. Kiểm content-type, magic bytes, ZIP CRC, schema và trường hợp server trả HTML với HTTP200.

### B. Bank of Canada FX — sensitivity thứ hai

- https://www.bankofcanada.ca/rates/exchange/daily-exchange-rates/
- https://www.bankofcanada.ca/valet/docs
- https://www.bankofcanada.ca/terms/

```bash
python src/market_data.py --source boc --out ../data/raw/boc
```

Đây là nguồn/base-currency sensitivity có nhiều currencies trùng ECB, không phải independent asset-class confirmation. Không ghép chuỗi cũ/mới khác phương pháp thu thập mà không khai báo.

### C. Bank of Canada zero-coupon curves — giai đoạn riêng nếu đủ nguồn lực

- https://www.bankofcanada.ca/rates/interest-rates/bond-yield-curves/

Phải tải đúng fitted zero-coupon archive, không nhầm benchmark yields trong probe cũ. Tạo loader, loss contract và protocol riêng. Nếu chưa làm được thì ghi NOT RUN, không trì hoãn kết quả ECB để ôm toàn bộ.

Mọi dataset phải có gate quyền sử dụng cho academic research/publication, citation, phiên bản, hạn chế redistribution. DOI không bắt buộc nếu có citation chính thức ổn định. Không tự gắn CC-BY cho toàn bộ nguồn. Lưu URL terms và ngày kiểm tra. Dữ liệu mới raw/processed giữ local trừ khi quyền chia sẻ và scope đã rõ.

## 5. Audit dữ liệu trước khi mở kết quả test

Lưu raw bytes bất biến + manifest: provider, URL, retrieval UTC, HTTP metadata nếu có, SHA256, series, quote direction, units, raw/clean counts, duplicates, ngày thiếu, range và mọi biến đổi.

ECB công bố foreign currency per EUR; giá trị vị thế foreign currency theo EUR phải nghịch đảo. BoC CAD/foreign không nghịch đảo. returns_pp hiện tính simple change nhân100; không trộn decimal với percentage-point units hoặc log return mà giữ nguyên mọi threshold.

Parser hiện drop incomplete dates trước khi tính return. Audit xem có vô tình biến một khoảng nhiều ngày mất dữ liệu thành một daily return không. Phân biệt lịch nghỉ chính thức và data outage; đăng ký cách xử lý gaps, báo số return bị loại, không forward/backward fill tùy tiện.

Kiểm availability_time chứ không chỉ observation_date. Xác minh lịch xuất bản ECB/BoC tại nguồn. Gap một observation trong prototype chỉ là giả định thận trọng, không chứng minh vintage real-time. Với yield curves, phải xử lý độ trễ công bố khoảng hai tuần theo nguồn; không đưa số liệu chưa công bố vào input. Dữ liệu hiện tại tải về là latest-vintage lịch sử; không gọi nó là archived real-time feed nếu chưa có vintage.

Không coi reference prices là execution prices. Không có spread/carry/funding/fees thì không báo Sharpe hoặc profit chiến lược có thể giao dịch.

## 6. Audit và hoàn thiện empirical runner

Giữ code cũ nguyên vẹn; thêm runner/package local_market có version hoặc refactor trong branch với compatibility tests và bản snapshot cũ. Viết RUNNER_AUDIT.md nêu thay đổi trước empirical evaluation.

Bắt buộc sửa/kiểm tra:
1. --stride5 chỉ chọn mỗi năm observation một forecast một kỳ, KHÔNG phải horizon5 ngày. Final daily/session forecast dùng stride1. Smoke được dùng stride5/limit20.
2. Log mọi GMM/correction convergence status, warnings, fallback và failed dates; hiện runner bỏ nhiều diagnostics. Đăng ký fallback trước khi xem test, không loại riêng ngày model thua.
3. Thêm pure support_mix50 đối chứng vì source market runner hiện chưa có dù nó rất cạnh tranh trong synthetic study.
4. Kiểm FZ0 upper-loss sign convention, positive-ES domain, pinball, weighted CVaR fractional atoms. Không clip ES<=0 tùy tiện để làm score đẹp; báo số undefined/failure và denominator.
5. Mỗi forecast ghi information cutoff, last training timestamp, forecast origin, target interval, weights và seed.
6. GMM256 không ngang information budget với pooled/corrected512; giữ làm diagnostic, không dùng làm baseline duy nhất.
7. Tất cả model dùng cùng risk-factor order, weight bank, availability rules và eligible dates.
8. Không truyền population parameters hoặc true future loss vào fitting/selection.

## 7. Tách hai evaluation tracks — rất quan trọng

TRACK A: RISK FORECAST QUALITY TRÊN CÙNG TARGET.

Ít nhất dùng danh mục equal-weight cố định. Tốt hơn thêm một reference policy chọn từ quá khứ theo rule khóa trước. Mọi risk estimator dự báo VaR/ES của CÙNG weights và được chấm với CÙNG realized loss.

Nếu có compute, xây cross-evaluation: mỗi selector chọn weights rồi tất cả estimator chấm cùng weights đó. Tách rõ selection effect khỏi forecast effect.

TRACK B: QUALITY OF EACH MODEL'S CHOSEN PORTFOLIO.

Mỗi model tối ưu trên cùng bank285 hoặc cùng feasible set đã khóa. Báo actual one-period exposure losses, pooled realized tail-loss statistics, concentration và turnover proxy. Nếu thay sang continuous optimizer phải là extension riêng với fair optimizer budgets, không thay lặng lẽ.

Không xếp hạng forecast accuracy bằng FZ0 của các danh mục có realized losses KHÁC NHAU rồi kết luận model nào dự báo đúng hơn. Track B là so sánh quyết định/risk-factor exposure, không phải same-target forecasting tournament.

Historical+SE penalty chọn weights bằng ES+penalty nhưng ES báo cáo vẫn là unpenalized estimate. Penalty không phải một upper confidence certificate.

Market thật không có population ES như synthetic DGP. Không lấy một realized loss làm trueES để tính relative error/regret. Empirical pooled ES trên chuỗi losses chỉ là thống kê ngoài mẫu của policy, không phải ground truth conditional ES tại từng ngày.

## 8. Khóa protocol theo thời gian

Trước khi chạy test, tạo MARKET_PROTOCOL_FROZEN.md và machine-readable config/hash. Không random split các ngày.

Đề xuất lịch ban đầu, chốt theo data availability chứ không dựa performance:
- ECB: development tới2015; validation2016–2019; test2020–2025.
- BoC FX: development tới2020; validation2021–2022; test2023–2025, với đủ warmup512+gap.

Giữ case không đủ warmup ngoài sample và báo counts. Chỉ điều chỉnh lịch vì vấn đề dữ liệu/phương pháp trước khi mở kết quả test, ghi rõ lý do. Tách kiểm tra schema khỏi nhìn đồ thị/test performance. Test2020–2025 chỉ mở sau freeze.

512 quan sát quá khứ, 8 risk factors, ES95 và bank285 là primary historical configuration. Rolling refit trên dữ liệu đã khả dụng được phép; architecture/hyperparameter/policy không được tune lại từ test outcomes.

Nếu thử hyperparameter mới, dùng inner chronological folds trong development/validation, ngân sách nhỏ và cố định. Benchmark APTC v2 giữ nguyên để kiểm transfer. Test đã xem sau này chỉ còn descriptive, không được gọi một lần tune tiếp là fresh confirmation.

## 9. Baseline tối thiểu

Giữ:
- equal-weight exposure reference;
- historical CVaR;
- historical CVaR + SE penalty;
- Gaussian + Ledoit-Wolf;
- Student-t + shrinkage;
- GMM pooled512;
- APTC v1 controlled comparator;
- support_mix50;
- support_band50;
- EWMA-filtered historical.

Không thêm LSTM/Transformer để buộc AI thắng. Một FHS/GARCH implementation đúng và/hoặc DRO có thể thêm trước test nếu literature audit chỉ ra baseline thiếu; phải ghi là implemented/reimplemented/not run, có equal-information setting và compact tuning. Không gọi penalty hiện tại là Wasserstein DRO.

Nếu v2 vẫn không hơn simple mixture/historical trên market, giữ negative result. Chỉ đề xuất một thay đổi method sau phân tích development; không tune trên final test để cứu novelty.

## 10. Metrics và thống kê

Track A: common-target VaR exceedance rate/count, pinball, mean joint VaR/ES score, calibration diagnostics; kiểm điều kiện áp dụng backtests trước khi chạy. Báo mean predictedES và shortfall residuals nếu định nghĩa đúng, không chỉ một số AUC/RMSE vô nghĩa.

Track B: distribution of realized loss, empirical ES với uncertainty, concentration HHI, weight stability, turnover proxy; không suy profit hoặc Sharpe sau chi phí từ reference changes.

Bootstrap theo contiguous date blocks, giữ ghép cặp mọi model. Chọn rule block length bằng dữ liệu development, báo sensitivity. Nhiều seeds/model draws không tạo thêm market days độc lập. Không pool currencies/datasets như độc lập nếu nguồn chồng nhau. CI pointwise phải ghi đúng, tránh hàng chục significance claims.

Lưu full forecast rows và lỗi; làm annual/subperiod diagnostics theo các khoảng đặt trước, không chỉ chọn crisis mà method đẹp. Báo effective observations/exceedances ở từng mức tail; 99% chỉ sensitivity khi đủ dữ liệu.

## 11. Chạy local, resume và song song

Ưu tiên hoàn tất ECB trước: download -> audit -> tests -> smoke development20windows -> freeze -> validation -> final evaluation -> artifact audit.

Các lệnh cũ để smoke từ quant_research_v2/:

```bash
python src/run_market_risk.py --levels ../data/raw/ecb/levels.csv \
  --out ../runs/ecb_smoke --from-date 2010-01-01 --to-date 2015-12-31 \
  --stride 5 --limit 20
```

Lệnh trên không thay thế runner hai-track đã audit. Tạo CLI/config mới cho final runs và ghi đúng command trong README. Unique run IDs, atomic per-window output và checkpoint/resume; không trộn artifact từ configs/hashes khác nhau. Bắt đầu2–3 CPU workers, một numerical thread/worker; benchmark trước tăng. Không giả định runtime Linux cũ là runtime Mac.

Có thể chia subagents thật nếu môi trường có: một worker audit data/license/timing, một worker audit risk/scoring, một worker implementation/tests. Dùng worktrees hoặc ownership rõ, coordinator khóa protocol và review tích hợp. Nếu không có subagent, tự thực hiện và ghi rõ, không nhận process parallelism là independent review. Không sửa quy tắc orchestration của môi trường để lách một worker failure.

## 12. Fixed-income extension chỉ khi đã sẵn sàng

BoC curves cần hợp đồng loss: chọn maturities trước, xác minh compounding/interpolation, constant-maturity yield là fitted series; định nghĩa zero-bond repricing với maturity roll-down hoặc DV01-normalized risk shocks. Negative yields không phải lý do loại tùy tiện. Không chạy returns_pp trên yield levels, không ghép benchmark yield và zero-coupon curve.

Thời điểm công bố là ràng buộc input; target loss có thể được quan sát hồi cứu nhưng phải ghi đúng. Chỉ claim risk-factor study nếu chưa có executable bond prices/carry/costs. Nếu extension chưa đủ thời gian/dữ liệu thì bàn giao ECB hoàn chỉnh, ghi curve NOT RUN.

## 13. Artifact, Git và báo cáo cuối

Tạo tối thiểu:
- docs/LOCAL_ENVIRONMENT.md
- docs/MARKET_DATA_MANIFEST.md + machine-readable metadata
- docs/RUNNER_AUDIT.md
- docs/MARKET_PROTOCOL_FROZEN.md
- docs/ECB_MARKET_RESULTS.md
- docs/BOC_MARKET_RESULTS.md hoặc NOT_RUN_STATUS.md
- docs/MARKET_ARTIFACT_AUDIT.md
- docs/NEXT_RESEARCH_DECISION.md

runs/<id>/ lưu config, source/data hashes, split dates, raw forecast table, weights, diagnostics, scores, bootstrap outputs và runtime. Public Git chỉ nhận code, đủ metadata/citation và aggregate tables/figures được phép. Market rows/raw/cache/model artifacts giữ local trừ khi quyền và scope cho phép rõ. Snapshot mô phỏng được import theo yêu cầu riêng ở mục1.

Kiểm lại bảng từ CSV, số ngày, train/test ordering, no-future tests, hội tụ và data provenance. Không nhận một lần chạy tests pass là scientific peer review.

Commit/push branch với thay đổi và kết quả thật; không force push, không ghi đè historical decision. Đưa link branch/commit/PR nếu có, counts/hashes cho import. Có thể tạo PR về main khi branch đã ổn, không tự merge các thay đổi phương pháp chưa review.

Trả lời cuối bằng tiếng Việt:
1. Toàn bộ931 file lịch sử đã import và push chưa? Nếu chưa, còn gì?
2. Dataset nào tải thật, size/dates/series/license/citation?
3. Local tests và empirical runs nào đã thực hiện?
4. Track A: forecast nào tốt nhất trên cùng loss target, CI và failures?
5. Track B: allocation nào giảm risk tốt nhất, không giả trading PnL?
6. APTC v2 có hơn historical+penalty và pure mixture không?
7. Các negative results và NOT RUN.
8. Link code/aggregate report, exact reproduction commands.
9. Đúng một next action có cơ sở.

Mục tiêu là market evidence tái lập được, không phải buộc candidate chiến thắng. Không dừng ở việc tạo download script nếu máy local tải được; hãy thực sự tải, kiểm tra và chạy.
