# Downloaded official FX data

Both datasets were actually downloaded using verified TLS from official endpoints on2026-10-05. Bytes, HTTP headers, retrieval receipts, cleaned panels and per-date outputs remain local under ignored `data/` and `runs/`. Public machine-readable metadata: [`market_data_metadata/`](market_data_metadata/). No community mirror or synthetic replacement was used.

| Provider | Raw bytes | Raw rows | Included complete dates | Panel range | Base |
|---|---:|---:|---:|---|---|
| ECB |640414|7106|6913|1999-01-04–2025-12-31|EUR|
| Bank of Canada |1394356|2244|2244|2017-01-03–2025-12-31|CAD|

ECB raw archive extends through2026-10-02;193 rows after the predeclared cutoff were excluded before returns. BoC request ends at the cutoff. Each panel contains eight declared currencies, zero duplicate dates and zero incomplete panel dates. ECB yields6912 valid session changes, BoC2243. No return was excluded for an unresolved gap in these downloads.

## ECB

Citation: European Central Bank, *Euro foreign exchange reference rates*, [official landing page](https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html), [historical archive](https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.zip), retrieved2026-10-05; exact UTC, HTTP metadata and SHA256 in `ecb.json`.

Panel order: USD,JPY,GBP,CHF,SEK,NOK,CAD,AUD. Original foreign-currency/EUR levels are inverted to EUR/foreign unit. We compute100 times simple relative changes; these are percentage-point reference-price changes, excluding carry, spread, funding and fees.

The [ECB terms](https://www.ecb.europa.eu/services/using-our-site/disclaimer/html/index.en.html), checked2026-10-05, allow free use of directly obtained information with accurate attribution and disclosure of modifications; documents sold require notice that the information is freely available. Authored publications have separate restrictions. This is not a blanket CC-BY license. Our reciprocal/change transformations and derived risk summaries are explicitly disclosed; no endorsement is implied.

The [2015 ECB announcement](https://www.ecb.europa.eu/press/pr/date/2015/html/pr151207.en.html) documents publication moving from about14:30 to16:00CET on2016-07-01. Current reference determination is around14:10CET. These are information prices, discouraged for transaction use. Nominal release schedules are not historical per-observation timestamps.

Calendar audit uses [TARGET closures](https://www.ecb.europa.eu/ecb/contacts/working-hours/html/index.en.html), the [1999 transition closure](https://www.ecb.europa.eu/press/pr/date/1999/html/pr990331.el.html), and [2001 calendar rule](https://eur-lex.europa.eu/eli/guideline/2001/401/oj/eng).1999 had a different holiday convention;31December1999/2001 are explicit special closures. The manifest enumerates every absent weekday and classification; none remained unresolved.

## Bank of Canada

Citation: Bank of Canada, *Daily exchange rates*, [official data](https://www.bankofcanada.ca/rates/exchange/daily-exchange-rates/), [Valet documentation](https://www.bankofcanada.ca/valet/docs), retrieved2026-10-05; series and exact URL/hash in `boc.json`.

Panel order: USD,EUR,GBP,JPY,CHF,AUD,NZD,CNY; original CAD/foreign quotes are retained. Only current-method daily observations from2017 are used; historical noon/closing rates are not spliced. Daily averages are normally published by16:30ET, with possible delays. This is a provider/base-currency/panel sensitivity sharing currencies with ECB, not an independent market or asset class.

[BoC terms](https://www.bankofcanada.ca/terms/), checked2026-10-05, permit use/reproduction of Bank-owned content with attribution, accuracy and modification disclosure; paid-use notices and third-party exceptions apply. Underlying FX inputs are sourced from LSEG. We analyze Bank-published indicative averages and publish our aggregate analysis only; we do not claim a license to redistribute underlying third-party quotes. These rates are designated for statistical/analytical use, not executable FX benchmarks. [Bank holiday schedule](https://www.bankofcanada.ca/press/upcoming-events/bank-of-canada-holiday-schedule/) supports the holiday audit; every absent weekday is classified in metadata.

## Availability and gaps

No forward/backward filling. A return spanning a missing component or unrecognized absent weekday is invalid; recognized closure/weekend intervals are labeled one reference session and record elapsed calendar days. The runner resets512-observation eligibility after invalid training data. Actual downloads have no such invalid returns.

We conservatively assign availability at23:59:59UTC on observation date, plus an extra observation gap before the forecast target. This does not establish point-in-time real-time validity: downloads are latest vintage and neither revisions nor exceptional historical publication delays are reconstructed. Rights to publish these derived aggregates do not change this limitation.
