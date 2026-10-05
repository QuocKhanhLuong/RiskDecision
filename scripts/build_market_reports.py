"""Render public Vietnamese result tables directly from audited aggregate CSVs."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    with path.open() as f:
        return list(csv.DictReader(f))


def number(x, places=6):
    return f"{float(x):.{places}f}"


def report(source):
    base = ROOT/"results/local_market"
    test = base/(source+"_test")
    validation = base/(source+"_validation")
    meta = json.loads((test/"provenance.json").read_text())
    audit = json.loads((test/"artifact_audit.json").read_text())
    assert audit["status"] == "PASS"
    rows, ci, pairs = [read(test/p) for p in ["summary.csv", "intervals.csv", "paired_differences.csv"]]
    block = str(meta["primary_block_length"])
    primary_ci = {(r["track"], r["target"], r["method"], r["metric"]): r for r in ci if r["block_length"] == block}
    def interval(track, target, method, metric):
        r = primary_ci[track, target, method, metric]
        return f'[{number(r["ci_low"])}; {number(r["ci_high"])}]'
    a = sorted([r for r in rows if r["track"] == "A" and r["target"] == "equal_weight"], key=lambda r: float(r["mean_fz0"]))
    b = sorted([r for r in rows if r["track"] == "B"], key=lambda r: float(r["pooled_es95_pp"]))
    r = meta["run_receipt"]
    lines = [f'# {source.upper()} — kết quả market risk-factor đã chạy', '',
             f'Test: **{r["windows"]} phiên**, {r["first"]}–{r["last"]}, {r["rows"]} forecast rows. '
             f'Stride1, 2 CPU workers, {r["wall_seconds_this_invocation"]:.2f}s. '
             'Các bảng dưới đây được tạo trực tiếp từ CSV; artifact audit PASS. Không dùng một realized loss làm true conditional ES.', '',
             f'Protocol SHA256 `{meta["protocol_sha256"]}`; commit khóa/push trước test: `9e70a57`. '
             'Không tune model sau khi xem validation/test. Đây là internal freeze, không phải external preregistration.', '',
             f'Track A có mean FZ0 thấp nhất mô tả trên equal-weight: **{a[0]["method"]}** ({number(a[0]["mean_fz0"])}). '
             f'Track B có pooled ES95 thấp nhất mô tả: **{b[0]["method"]}** ({number(b[0]["pooled_es95_pp"])} điểm phần trăm). '
             'Thứ hạng quan sát không tự chứng minh ưu thế thống kê hay conditional calibration.', '',
             '## Track A — cùng equal-weight exposure', '',
             '| Estimator | Mean FZ0 ↓ | CI95% FZ0 | Pinball95 ↓ | Breaches / n | Mean predicted ES (pp) | FZ0 undefined |',
             '|---|---:|---|---:|---:|---:|---:|']
    critical = [x for x in pairs if x["metric"] in ("fz0", "pooled_es95_pp")]
    if all(float(x["ci_low"]) <= 0 <= float(x["ci_high"]) for x in critical):
        at = lines.index('## Track A — cùng equal-weight exposure')
        lines[at:at] = ['**APTC v2 chưa chứng minh vượt historical+penalty hoặc pure support mixture.** '
                       'CI95% chênh lệch FZ0 trên cả hai common targets và pooled ES của Track B đều chứa0, '
                       'ở block chính lẫn sensitivity5/20/60. Không diễn giải thiếu bằng chứng là hai mô hình tương đương.', '']
    for x in a:
        lines.append(f'|{x["method"]}|{number(x["mean_fz0"])}|{interval("A", "equal_weight", x["method"], "fz0")}|{number(x["mean_pinball95"])}|{x["breaches"]}/{x["n"]}|{number(x["mean_predicted_es95_pp"])}|{x["fz0_undefined_n"]}|')
    lines += ['', 'Historical và historical+SE báo cùng unpenalized ES trên cùng weights; penalty chỉ đổi selector. '
              '`equal_weight` trong Track A là historical estimator alias. GMM256 chỉ là diagnostic khác information budget.', '',
              '## Track A — cùng reference policy từ quá khứ', '',
              '| Estimator | Mean FZ0 ↓ | Pinball95 ↓ | Breaches / n | Shortfall residual mean (pp) | CI95% residual |',
              '|---|---:|---:|---:|---:|---|']
    for x in sorted([r for r in rows if r["track"] == "A" and r["target"] == "historical_se_reference"], key=lambda r: float(r["mean_fz0"])):
        lines.append(f'|{x["method"]}|{number(x["mean_fz0"])}|{number(x["mean_pinball95"])}|{x["breaches"]}/{x["n"]}|{number(x["mean_shortfall_residual_pp"])}|{interval("A", "historical_se_reference", x["method"], "shortfall_residual")}|')
    lines += ['', 'Reference policy chọn weights bằng historical ES+SE chỉ từ training. Tất cả estimators nhận cùng weights/loss tại mỗi origin. '
              'Residual là v+(L−v)+/0.05−e; mean gần0 là một diagnostic của cặp VaR/ES, không phải bảo đảm.', '',
              '## Track B — exposure do từng selector chọn', '',
              '| Selector | Pooled ES95 (pp) ↓ | CI95% ES | Mean loss (pp) | HHI | Mean half-L1 weight change |',
              '|---|---:|---|---:|---:|---:|']
    for x in b:
        lines.append(f'|{x["method"]}|{number(x["pooled_es95_pp"])}|{interval("B", "own_selection", x["method"], "pooled_es95_pp")}|{number(x["mean_loss_pp"])}|{number(x["mean_hhi"])}|{number(x["mean_half_l1_weight_change"])}|')
    lines += ['', f'Tail mass: 5% × n = {float(b[0]["tail_mass_n"]):.2f} observations; fractional boundary atoms được giữ. '
              'Đây là pooled out-of-sample policy statistic, không phải conditional ES ground truth. Half-L1 là thay đổi target weights, '
              'không gồm drift/transaction costs và không phải turnover giao dịch thực. Không xếp hạng FZ0 của các loss targets khác nhau.', '',
              f'## Candidate so với hai đối chứng — block chính {block}', '',
              '| Track / target | Reference | Metric | Candidate − reference | CI95% |',
              '|---|---|---|---:|---|']
    for x in pairs:
        if x["block_length"] == block:
            lines.append(f'|{x["track"]}/{x["target"]}|{x["reference"]}|{x["metric"]}|{number(x["difference"])}|[{number(x["ci_low"])}; {number(x["ci_high"])}]|')
    lines += ['', 'Âm là candidate tốt hơn trên metric tương ứng. CI là pointwise, paired moving-block percentile,5000replicates; '
              'không multiplicity-adjusted. Block sensitivity5/20/60 và toàn bộ intervals nằm trong CSV; '
              'không chọn block theo kết quả. Approximate stationarity/structural breaks là giới hạn.', '',
              '## Validation đã chạy trước final test', '',
              '| Method | A equal-weight FZ0 | B pooled ES95 (pp) |', '|---|---:|---:|']
    vv = read(validation/"summary.csv")
    for m in ["historical_se_penalty", "support_mix50", "support_band50", "filtered_historical"]:
        va = next(x for x in vv if x["track"] == "A" and x["target"] == "equal_weight" and x["method"] == m)
        vb = next(x for x in vv if x["track"] == "B" and x["method"] == m)
        lines.append(f'|{m}|{number(va["mean_fz0"])}|{number(vb["pooled_es95_pp"])}|')
    lines += ['', '## Diagnostics theo từng năm (tất cả năm test)', '',
              '| Year | n | Candidate A FZ0 | Historical A FZ0 | Mixture A FZ0 | Candidate B ES | Historical+SE B ES | Mixture B ES |',
              '|---|---:|---:|---:|---:|---:|---:|---:|']
    annual = read(test/"annual.csv")
    for year in sorted({x["year"] for x in annual}):
        aa = {x["method"]: x for x in annual if x["year"] == year and x["track"] == "A" and x["target"] == "equal_weight"}
        bb = {x["method"]: x for x in annual if x["year"] == year and x["track"] == "B"}
        ms = ["support_band50", "historical_se_penalty", "support_mix50"]
        lines.append('|'+year+'|'+aa[ms[0]]["n"]+'|'+'|'.join([number(aa[m]["mean_fz0"]) for m in ms]+[number(bb[m]["pooled_es95_pp"]) for m in ms])+'|')
    dd = json.loads((test/"diagnostic_counts.json").read_text())
    lines += ['', 'Mỗi năm chỉ khoảng12–13tail observations; annual results là mô tả, không là các thử nghiệm độc lập.', '',
              '## Hội tụ và giới hạn', '', '| Method | Nonconverged dates | Fallback dates | Warning dates | Failed correction steps |',
              '|---|---:|---:|---:|---:|']
    for m, x in dd.items():
        lines.append(f'|{m}|{x["nonconverged_dates"]}|{x["fallback_dates"]}|{x["warning_dates"]}|{x["failed_correction_steps"]}|')
    lines += ['', 'Giữ mọi finite warning output theo quy tắc khóa trước; không xóa ngày bất lợi. '
              'Latest-vintage reference changes, không reconstructed real-time release feed; không spread/carry/funding/fees, profit hoặc Sharpe. '
              'Không có independent agent/human peer review. Không full cross-evaluation,99% sensitivity,GARCH/DRO,neural hoặc yield-curve experiment.', '',
              ('BoC là source/base-currency sensitivity có currencies trùng ECB, không là thị trường độc lập. Không pool hai nguồn như independent samples.' if source == "boc" else 'BoC được báo riêng như source/base-currency sensitivity; không làm tăng số thị trường độc lập.'), '',
              f'Artifacts: [`results/local_market/{source}_test`](../results/local_market/{source}_test/), '
              f'[`validation`](../results/local_market/{source}_validation/). '
              '[Nguồn/quyền dùng](MARKET_DATA_MANIFEST.md), [protocol](MARKET_PROTOCOL_FROZEN.md), '
              '[lệnh tái lập](MARKET_REPRODUCTION.md).', '']
    (ROOT/"docs"/(source.upper()+"_MARKET_RESULTS.md")).write_text('\n'.join(lines))


if __name__ == "__main__":
    import sys
    for source in sys.argv[1:] or ["ecb", "boc"]:
        report(source)
