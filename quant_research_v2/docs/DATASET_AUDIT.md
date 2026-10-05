# Additional market datasets: provenance, permitted use and execution status

Reviewed 2026-10-05. **No raw market dataset was successfully imported into this runtime. No empirical market result is claimed.** Official documentation was read through the browsing tool, while the execution environment's downloads failed (DNS / download service). `data/downloads.json` preserves the errors. The GitHub mirror `datasets/exchange-rates` was inspected for access feasibility, but not used for training: its README identifies FRED as the extraction source and makes a conditional public-domain assumption. It is not a substitute for the authoritative-use gate.

## Selected first market panel: ECB foreign exchange reference rates

- Provider/source: European Central Bank, Euro foreign exchange reference rates.
- Landing page: https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html
- Official archive: https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.zip
- Terms: https://www.ecb.europa.eu/services/using-our-site/disclaimer/html/index.en.html
- Status: **ACCEPT WITH ATTRIBUTION/REUSE CONDITIONS; DOWNLOAD FAILED; NOT RUN.** ECB permits free use of information obtained directly, accurate reproduction, citation of ECB, disclosure of modifications, and additional notices if incorporated into paid material. This is not a declaration that every ECB-authored document is CC-BY; authored publications have separate provisions.
- Proposed frozen subset: USD, JPY, GBP, CHF, SEK, NOK, CAD, AUD, common complete dates, cutoff 2025-12-31. Exact first date/row count will be measured after download; none fabricated here.
- Original quote: foreign-currency units per EUR. For euro-denominated value changes of foreign-currency positions, invert the levels before computing simple percent changes.
- Reference rates normally published around 16:00 CET on working days; ECB discourages use as transaction prices. The retrospective runner imposes an additional observation gap, but does not reconstruct complete historical release/vintage records.
- Economic use: portfolio *risk-factor* analysis, not executable trading returns. No spread, carry, funding cost or transaction-cost data.
- Citation: European Central Bank. *Euro foreign exchange reference rates*. Archive downloaded [actual date], subset and SHA256 in generated manifest. Authors' reciprocal and percentage-change transformations disclosed.

## Second FX source: Bank of Canada daily exchange rates

- Source: https://www.bankofcanada.ca/rates/exchange/daily-exchange-rates/
- API documentation: https://www.bankofcanada.ca/valet/docs
- Terms: https://www.bankofcanada.ca/terms/
- Status: **ACCEPT WITH RESTRICTIONS; DOWNLOAD FAILED; NOT RUN.** Bank-owned content may be used, copied, distributed and transmitted with attribution, accuracy and disclosure of changes; paid-use notice and third-party exceptions apply.
- Current-method daily series from 2017; earlier noon/closing rates have different construction and must not be silently spliced.
- Proposed subset: USD, EUR, GBP, JPY, CHF, AUD, NZD, CNY quoted in CAD per currency unit. Values are indicative averages, published once per business day by 16:30 ET. Exact count after parsing, not estimated as an actual dataset size.
- Citation: Bank of Canada. *Daily exchange rates*, Valet API, named series, actual retrieval date and SHA256.
- ECB and BoC overlap in underlying currencies. They are **not independent asset-class validations** just because providers/base currencies differ.

## Distinct market: Bank of Canada zero-coupon yield curves

- Source: https://www.bankofcanada.ca/rates/interest-rates/bond-yield-curves/
- Bank terms as above.
- Status: **ACCEPT WITH RESTRICTIONS; NO CURVE DATA IMPORTED; NOT RUN.** The attempted yield API probe used benchmark yields, not this full fitted zero-curve archive. Do not confuse those sources.
- Daily curves derived from Government of Canada bonds/T-bills. 120 maturities from 0.25 to 30 years, decimal yields (.05 = 5%). Provider documents gaps, including in 1986–1990. No measured clean sample count yet.
- **Release lag: usually Thursdays 16:30 ET, two weeks delayed.** Observation date is not public availability date.
- Method citation: Bolder, David J., Grahame Johnson and Adam Metzler (2004). *An Empirical Analysis of the Canadian Term Structure of Zero-Coupon Interest Rates*. Bank of Canada Working Paper 2004-48. Official repository: https://www.oar-rao.bank-banque-canada.ca/record/982 . The data page links this paper directly. DOI 10.34989/swp-2004-48 was discovered via the catalogue, but its resolver failed in the browser; repository citation is the directly inspected provider route.
- Not raw executable bond prices. Use a predeclared bond repricing/holding-period convention or DV01-normalized shock loss; **a yield change is not a bond total return**. No backtest implemented for these curves yet.

## ECB euro-area yield curves

- Source: https://www.ecb.europa.eu/stats/financial_markets_and_interest_rates/euro_area_yield_curves/html/index.en.html
- Terms: ECB general terms, with specific underlying/third-party restrictions to check for the exact exported product.
- Status: **CONDITIONALLY ELIGIBLE PROVIDER DATA; DOWNLOAD FAILED; NOT RUN.** Use the published fitted curves, not unlicensed underlying bond quotations.
- Provider offers historical estimated curves and selected credit-quality universes. Freeze exact maturity series, credit universe, release timing and compounding convention before calculating losses.
- Dataset row count and a clean subset have NOT been measured.
- Citation: ECB, *Euro area yield curves*, exact YC-series keys, actual retrieval date and hash.

## Auxiliary macro panel: BIS effective exchange rates

- Source: https://data.bis.org/topics/EER
- Specific terms: https://data.bis.org/help/legal
- Status: **ACCEPT WITH CONDITIONS AS AUXILIARY DATA; NOT DOWNLOADED/NOT RUN.** BIS statistics use is unrestricted subject to citation, nonmisleading use, translation disclosure when applicable, and commercial charging restrictions. API access terms apply separately.
- Broad daily/monthly and narrow long-history indices are documented by BIS; exact chosen panel not yet constructed.
- Use as market-state/stress covariates or a separate statistical panel. Trade-weighted effective exchange-rate indices are **not directly investable currency prices**. Do not claim daily portfolio profits from them.
- Citation: Bank for International Settlements, *Effective exchange rates*, series keys/vintage, retrieval date and hash.

## Citation/version and distribution contract

All future real runs must save: provider, original URL, official dataset title, terms URL, actual UTC retrieval, raw SHA256, selected series, units/orientation, observation and assumed availability dates, date filtering, transformations and dropped-row counts. Never replace registration or usage terms with an unrestricted community mirror. Public reports disclose modifications and do not imply central-bank endorsement. Dataset public-use permission is not a claim that the simulated experiment has become empirical.
