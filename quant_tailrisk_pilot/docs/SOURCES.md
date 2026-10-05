# Primary sources checked on 2026-10-05

This is a targeted review, not an exhaustive prior-art clearance.

1. Smith, J. E., & Winkler, R. L. (2006). The Optimizer's Curse: Skepticism and Postdecision Surprise in Decision Analysis. Management Science, 52(3), 311–322. DOI: https://doi.org/10.1287/mnsc.1050.0451
   - Original phenomenon and Bayesian correction; cannot claim optimization-induced optimism is new.

2. Rockafellar, R. T., & Uryasev, S. (2002). Conditional value-at-risk for general loss distributions. Journal of Banking & Finance. Source: https://www.sciencedirect.com/science/article/abs/pii/S0378426602002716
   - CVaR variational representation and numerical optimization foundation.

3. Meucci, A. Fully Flexible Views: Theory and Practice. Open manuscript: https://arxiv.org/abs/1012.2848
   - General distribution/scenario adjustment via information-theoretic views. Relevant to entropy/moment projection; the prototype must not claim this operation as new.

4. Papp, G., Caccioli, F., & Kondor, I. Bias-variance trade-off in portfolio optimization under Expected Shortfall with l2 regularization. https://arxiv.org/abs/1602.08297
   - Estimation error and regularization in ES portfolio optimization are already studied.

5. Sun, C., Wu, Q., & Yan, X. (2023). Dynamic CVaR Portfolio Construction with Attention-Powered Generative Factor Learning. https://arxiv.org/abs/2301.07318
   - Generative financial scenarios plus CVaR portfolio optimization are already studied.

6. Tang, J., Wu, J., Wu, Z. S., & Zhang, J. (2026). Dimension-Free Decision Calibration for Nonlinear Loss Functions. ICLR 2026.
   https://openreview.net/forum?id=vAU1fo1zRV
   https://proceedings.iclr.cc/paper_files/paper/2026/file/8ad060589ed7e18aea4ee1cc8a486c89-Paper-Conference.pdf
   - Official version inspected, including assumptions on iid samples, finite action space and bounded losses.

7. Yang et al. DFF: Decision-Focused Fine-tuning for Smarter Predict-then-Optimize with Limited Data. https://arxiv.org/html/2501.01874v1
   - Trust-region correction and the danger of changing the physical meaning of predictive outputs.

8. Zhou, Y., Zhou, Y., Morstyn, T., & Wang, Y. (2026, preprint). Decision-Focused Scenario Generation and Selection for Efficient and Robust Grid Dispatch. https://arxiv.org/html/2607.05830v1
   - Prior art outside finance for decision-focused joint scenario learning and selection.

9. Chen, C., Shen, J., Deng, Z., & Lei, L. (2026, preprint). Adversarially Robust Control of Conditional Value-at-Risk via Rockafellar-Uryasev Conformal Inference. https://arxiv.org/abs/2606.00320
   - Online empirical CVaR control with portfolio experiments; risk control itself is not an untouched gap. No reproduction was run.

## Market data planned but NOT run

Federal Reserve Board H.10:
https://www.federalreserve.gov/releases/h10/hist/
https://www.federalreserve.gov/releases/h10/hist/dat00_eu.htm

Usage policy:
https://www.federalreserve.gov/disclaimer.htm

The Board identifies its information as public domain unless otherwise stated, with attribution requested. H.10 quotes are reference exchange rates, not execution prices. The release schedule matters for backtesting: the historical page says Monday updates contain observations through the preceding Friday. Container download attempts failed, so NO market results are included in this package.
