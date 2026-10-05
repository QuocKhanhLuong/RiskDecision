# Real-data risk study: ready-to-run prototype, NOT EXECUTED ON MARKET DATA

## Frozen first source
ECB reference FX panel, eight currencies listed in DATASET_AUDIT.md, date cutoff2025-12-31. Do not treat a different base currency from a second provider as an independent economic market. Source/provider metadata and raw checksums required. No raw bytes were successfully obtained here.

## Loader
`market_data.py` downloads from the official endpoint or accepts an original downloaded file. It inverts ECB foreign/EUR quotes into EUR/foreign values. BoC CAD/foreign prices are not inverted. It retains complete common observations only, no forward fill. It records the transformation, exact range and hash. Parser tests use explicitly synthetic tiny fixtures, not purported market observations.

## Rolling runner
`run_market_risk.py` has been smoke-tested on a synthetic window only. For each selected date: use512 past percentage-point reference-price changes; leave one full observed return out as an extra availability gap; estimate risk and optimize among285 fixed weights; score the next unobserved reference-price move. No oracle population parameters, no known true ES, and no parameter tuning on evaluation losses. Default stride5 subsamples dates to bound cost; it is **not a five-day holding horizon** and cannot be presented as a full-daily VaR backtest.

Default first evaluation date2010-01-01 and end2025-12-31; BoC later data only yield eligible windows after sufficient history. Methods remain fixed by synthetic validation, with historical SE-penalty kept as the frozen leading reference. Other models are controls.

Output: predictedVaR, predictedES, realized loss of selected fixed one-period exposure, VaR breach, pinball score, upper-tail FZ0 score when ES>0, weights, lasttrainingdate. Negative/nonpositive ES makes FZ0 undefined and is explicitly recorded, not silently clipped. Do not compute market ES-error/regret using a single realized return as 'true ES'.

## Limits before a paper claim
This is retrospective risk-factor evaluation using the downloaded vintage. The observation-gap simplification does not reconstruct every historical publication delay/revision. No bid–ask, carry, funding, rebalancing, fees or executeable prices. Do not report strategy Sharpe or trading profits. Full paper confirmation must freeze exact availability rules and market sampling, score with dependence-aware inference, and separately consider turnover/costs if economic PnL is introduced.

BoC zero-coupon curves require a different loader and a declared duration/repricing transformation, with the provider's two-week publication lag. The FX runner MUST NOT be reused directly on yield levels. BIS effective rates are auxiliary indices, not traded assets. Neither curve nor BIS experiment is implemented or claimed as run.
