# Nguồn cốt lõi và giới hạn

## Bằng chứng nội bộ

- [Kết quả v2](../quant_research_v2/RESULTS_VI.md), [method v2](../quant_research_v2/docs/METHOD_V2.md), [protocol](../quant_research_v2/docs/PROTOCOL.md), [source](../quant_research_v2/src/research.py).
- [Market runner](../quant_research_v2/src/run_market_risk.py): prototype, not real market evidence.
- [Original pilot](../quant_tailrisk_pilot/RESULTS_VI.md) tách khỏi v2; không gộp statistics khác protocol.
- Review trong chat `Finance_Quant_Research_Review_20261007.zip` / `REVIEW_VI.md` và `diagnostics/quant_crossed_summary_percent.csv`: phân tích hậu nghiệm crossed matrix trên artifact cũ, không training mới.

## Prior art bắt buộc

1. Iyengar, G., Lam, H., Wang, T. *Optimizer's Information Criterion: Dissecting and Correcting Bias in Data-Driven Optimization*. arXiv:2306.10081v4, revised 2025-07-21. https://arxiv.org/abs/2306.10081v4 ; DOI 10.48550/arXiv.2306.10081. Trang metadata kiểm tra lại 2026-10-07; review trước nêu Example 6.4 CVaR. Đọc full text trước port formulas. OIC hiệu chỉnh first-order optimized-performance optimism, không mặc nhiên là calibrated risk forecast cho time series.
2. Meucci, A. *Fully Flexible Views: Theory and Practice*, Risk 21(10), 2008, pp.97–102; arXiv posting 2010. https://arxiv.org/abs/1012.2848 . Nguồn cho entropy pooling, đối thủ gần của reweighting APTC.
3. Patton, A. J., Ziegel, J. F., Chen, R. *Dynamic Semiparametric Models for Expected Shortfall (and Value-at-Risk)*. https://arxiv.org/abs/1707.05108 . Nền tảng joint forecast/scoring cần đọc; không suy single realized loss là ground-truth ES.

Ba landing pages trên được kiểm tra lại 2026-10-07; đây không phải exhaustive literature search mới. Baseline DRO, FHS/GARCH và decision-focused scenario generation phải chọn đúng paper/formulation ở Q1/Q2, không gọi một heuristic là bản tái lập official.

## Quy tắc citation

Repo report phải ghi phiên bản, nguồn trực tiếp và trạng thái peer-reviewed/preprint. Dataset cite provider + release/retrieval + series + transformations + hash; source copyright/terms không bị thay thế bởi license code. Không khẳng định các nguồn legal audit cũ vẫn còn hiệu lực khi download mới chưa kiểm tra.
