# Decision-gap results

Generated from local case CSV; values are fractions, not percentage points. No market data or final-test rerun.

## Marginal decision gate

|family|n|recipe|switches|harms|coverage|relative_delta|radius_ratio|chosen_band|
|---|---|---|---|---|---|---|---|---|
|ar1|1024|absolute|0|0|1.000000|0.000000|0.266315|0|
|ar1|1024|paired|13|0|0.955000|-0.002921|0.266315|0|
|ar1|1024|paired_no_band|13|0|0.955000|-0.002921|0.266315|0|
|ar1|1024|point|67|16|0.085000|-0.006445|0.266315|1|
|ar1|256|absolute|0|0|1.000000|0.000000|0.276231|0|
|ar1|256|paired|11|1|0.875000|-0.001695|0.276231|0|
|ar1|256|paired_no_band|11|1|0.875000|-0.001695|0.276231|0|
|ar1|256|point|82|33|0.085000|-0.003241|0.276231|0|
|asymmetric_crash|1024|absolute|0|0|1.000000|0.000000|0.212548|0|
|asymmetric_crash|1024|paired|7|1|0.955000|-0.001541|0.212548|1|
|asymmetric_crash|1024|paired_no_band|7|0|0.970000|-0.001663|0.212548|0|
|asymmetric_crash|1024|point|76|23|0.070000|-0.004228|0.212548|8|
|asymmetric_crash|256|absolute|0|0|1.000000|0.000000|0.219513|0|
|asymmetric_crash|256|paired|1|0|0.960000|-0.000160|0.219513|0|
|asymmetric_crash|256|paired_no_band|1|0|0.960000|-0.000160|0.219513|0|
|asymmetric_crash|256|point|88|48|0.070000|0.003541|0.219513|9|
|gaussian|1024|absolute|0|0|1.000000|0.000000|0.275231|0|
|gaussian|1024|paired|20|1|0.955000|-0.003502|0.275231|0|
|gaussian|1024|paired_no_band|20|1|0.955000|-0.003502|0.275231|0|
|gaussian|1024|point|91|23|0.085000|-0.006748|0.275231|0|
|gaussian|256|absolute|0|0|1.000000|0.000000|0.280240|0|
|gaussian|256|paired|10|3|0.945000|-0.001058|0.280240|0|
|gaussian|256|paired_no_band|10|3|0.945000|-0.001058|0.280240|0|
|gaussian|256|point|102|40|0.085000|-0.002748|0.280240|0|
|markov_volatility|1024|absolute|0|0|1.000000|0.000000|0.127082|0|
|markov_volatility|1024|paired|12|0|0.945000|-0.002982|0.127082|3|
|markov_volatility|1024|paired_no_band|10|0|0.950000|-0.002605|0.127082|0|
|markov_volatility|1024|point|74|26|0.150000|-0.005489|0.127082|10|
|markov_volatility|256|absolute|0|0|1.000000|0.000000|0.164981|0|
|markov_volatility|256|paired|15|6|0.920000|-0.001330|0.164981|3|
|markov_volatility|256|paired_no_band|14|6|0.920000|-0.000760|0.164981|0|
|markov_volatility|256|point|97|48|0.150000|-0.002042|0.164981|12|
|student_t4|1024|absolute|0|0|1.000000|0.000000|0.234008|0|
|student_t4|1024|paired|17|1|0.950000|-0.006107|0.234008|2|
|student_t4|1024|paired_no_band|15|1|0.950000|-0.005140|0.234008|0|
|student_t4|1024|point|95|24|0.110000|-0.011760|0.234008|3|
|student_t4|256|absolute|0|0|1.000000|0.000000|0.245653|0|
|student_t4|256|paired|9|3|0.960000|-0.001433|0.245653|0|
|student_t4|256|paired_no_band|9|3|0.960000|-0.001433|0.245653|0|
|student_t4|256|point|99|39|0.110000|-0.005354|0.245653|4|

## Conditional stress at n1024

|family|recipe|switches|harms|coverage|relative_delta|
|---|---|---|---|---|---|
|ar1|absolute|0|0|0.920000|0.000000|
|ar1|paired|13|6|0.400000|-0.000799|
|ar1|paired_no_band|13|6|0.400000|-0.000799|
|ar1|point|67|35|0.085000|0.000180|
|asymmetric_crash|absolute|0|0|1.000000|0.000000|
|asymmetric_crash|paired|7|1|0.955000|-0.001541|
|asymmetric_crash|paired_no_band|7|0|0.970000|-0.001663|
|asymmetric_crash|point|76|23|0.070000|-0.004228|
|gaussian|absolute|0|0|1.000000|0.000000|
|gaussian|paired|20|1|0.955000|-0.003502|
|gaussian|paired_no_band|20|1|0.955000|-0.003502|
|gaussian|point|91|23|0.085000|-0.006748|
|markov_volatility|absolute|0|0|1.000000|0.000000|
|markov_volatility|paired|12|3|0.805000|-0.002106|
|markov_volatility|paired_no_band|10|3|0.810000|-0.001858|
|markov_volatility|point|74|16|0.150000|-0.011457|
|student_t4|absolute|0|0|1.000000|0.000000|
|student_t4|paired|17|1|0.950000|-0.006107|
|student_t4|paired_no_band|15|1|0.950000|-0.005140|
|student_t4|point|95|24|0.110000|-0.011760|

## Paired gate versus strong controls, marginal n1024

|family|comparator|mean|lo|hi|
|---|---|---|---|---|
|ar1|all_history_hist_se|0.010104|0.006920|0.013490|
|ar1|paired_no_band|0.000000|0.000000|0.000000|
|ar1|recent_filtered_historical|-0.034806|-0.041896|-0.027814|
|ar1|recent_historical_se_penalty|-0.004012|-0.008675|0.000627|
|ar1|recent_support_mix50|-0.002214|-0.006892|0.002536|
|ar1|training_hist_se|-0.002921|-0.004950|-0.001306|
|asymmetric_crash|all_history_hist_se|0.012998|0.009837|0.016440|
|asymmetric_crash|paired_no_band|0.000122|0.000000|0.000317|
|asymmetric_crash|recent_filtered_historical|-0.045027|-0.054707|-0.035657|
|asymmetric_crash|recent_historical_se_penalty|-0.000478|-0.005343|0.004405|
|asymmetric_crash|recent_support_mix50|-0.006880|-0.012720|-0.001172|
|asymmetric_crash|training_hist_se|-0.001541|-0.003028|-0.000352|
|gaussian|all_history_hist_se|0.009218|0.007070|0.011470|
|gaussian|paired_no_band|0.000000|0.000000|0.000000|
|gaussian|recent_filtered_historical|-0.021990|-0.026940|-0.017160|
|gaussian|recent_historical_se_penalty|-0.002265|-0.005669|0.001201|
|gaussian|recent_support_mix50|0.001214|-0.002026|0.004418|
|gaussian|training_hist_se|-0.003502|-0.005288|-0.001874|
|markov_volatility|all_history_hist_se|0.009620|0.006791|0.012487|
|markov_volatility|paired_no_band|-0.000377|-0.001064|0.000000|
|markov_volatility|recent_filtered_historical|-0.024522|-0.030531|-0.018576|
|markov_volatility|recent_historical_se_penalty|-0.005516|-0.010200|-0.000723|
|markov_volatility|recent_support_mix50|-0.003782|-0.007858|0.000223|
|markov_volatility|training_hist_se|-0.002982|-0.005087|-0.001267|
|student_t4|all_history_hist_se|0.016221|0.011899|0.020480|
|student_t4|paired_no_band|-0.000967|-0.002674|0.000000|
|student_t4|recent_filtered_historical|-0.027547|-0.037280|-0.018283|
|student_t4|recent_historical_se_penalty|-0.007195|-0.015343|0.000154|
|student_t4|recent_support_mix50|0.001784|-0.003834|0.007265|
|student_t4|training_hist_se|-0.006107|-0.009775|-0.002965|

Negative differences favor gate. Paired seed bootstrap intervals are pointwise descriptive; all comparisons and conditional strata are in CSV.

## Common-target forecast diagnostics (training512, marginal truth)

|family|method|common_equal_relative_error|bank_level_mae|bank_contrast_mae|same_choice_as_hist|
|---|---|---|---|---|---|
|ar1|filtered_historical|0.079060|0.120701|0.105299|0.140000|
|ar1|historical_se_penalty|0.057474|0.074551|0.075724|1.000000|
|ar1|support_band50|0.057908|0.074234|0.070969|0.545000|
|ar1|support_mix50|0.058163|0.074377|0.071051|0.550000|
|asymmetric_crash|filtered_historical|0.168524|0.518894|0.288845|0.100000|
|asymmetric_crash|historical_se_penalty|0.084149|0.259321|0.192564|1.000000|
|asymmetric_crash|support_band50|0.098067|0.297789|0.192424|0.435000|
|asymmetric_crash|support_mix50|0.091589|0.278637|0.193799|0.455000|
|gaussian|filtered_historical|0.056983|0.091420|0.088998|0.195000|
|gaussian|historical_se_penalty|0.040604|0.052393|0.055553|1.000000|
|gaussian|support_band50|0.041182|0.052825|0.052207|0.475000|
|gaussian|support_mix50|0.041182|0.052825|0.052207|0.475000|
|markov_volatility|filtered_historical|0.257381|0.522714|0.162751|0.190000|
|markov_volatility|historical_se_penalty|0.160012|0.309845|0.109061|1.000000|
|markov_volatility|support_band50|0.170375|0.330739|0.112656|0.630000|
|markov_volatility|support_mix50|0.161704|0.314653|0.112424|0.655000|
|student_t4|filtered_historical|0.148967|0.222706|0.153681|0.170000|
|student_t4|historical_se_penalty|0.092409|0.124994|0.109898|1.000000|
|student_t4|support_band50|0.093060|0.124418|0.101464|0.465000|
|student_t4|support_mix50|0.096020|0.128974|0.108142|0.475000|

Forecast errors and allocation risk are separate. Bank contrast MAE does not have the same scale as level MAE and is not a proof of risk improvement.

## Direct APTC comparisons (descriptive secondary analysis)

|family|track|comparator|mean|lo|hi|
|---|---|---|---|---|---|
|ar1|common_equal_error|historical_se_penalty|0.000434|-0.002036|0.002889|
|ar1|selected_marginal_risk|historical_se_penalty|-0.001814|-0.004921|0.001208|
|ar1|common_equal_error|support_mix50|-0.000255|-0.000596|-0.000009|
|ar1|selected_marginal_risk|support_mix50|-0.000027|-0.000082|0.000000|
|asymmetric_crash|common_equal_error|historical_se_penalty|0.013918|0.008497|0.019556|
|asymmetric_crash|selected_marginal_risk|historical_se_penalty|0.007652|0.003786|0.011722|
|asymmetric_crash|common_equal_error|support_mix50|0.006478|0.001891|0.011501|
|asymmetric_crash|selected_marginal_risk|support_mix50|0.003445|0.001478|0.005805|
|gaussian|common_equal_error|historical_se_penalty|0.000578|-0.001859|0.003046|
|gaussian|selected_marginal_risk|historical_se_penalty|-0.003829|-0.006561|-0.001151|
|gaussian|common_equal_error|support_mix50|-0.000000|-0.000000|0.000000|
|gaussian|selected_marginal_risk|support_mix50|0.000000|0.000000|0.000000|
|markov_volatility|common_equal_error|historical_se_penalty|0.010363|0.001228|0.019954|
|markov_volatility|selected_marginal_risk|historical_se_penalty|0.001065|-0.001846|0.003939|
|markov_volatility|common_equal_error|support_mix50|0.008671|-0.000389|0.018207|
|markov_volatility|selected_marginal_risk|support_mix50|-0.000676|-0.002375|0.000892|
|student_t4|common_equal_error|historical_se_penalty|0.000651|-0.004829|0.005990|
|student_t4|selected_marginal_risk|historical_se_penalty|-0.008321|-0.012916|-0.003962|
|student_t4|common_equal_error|support_mix50|-0.002960|-0.008503|0.002058|
|student_t4|selected_marginal_risk|support_mix50|-0.002713|-0.005673|-0.000253|

APTC minus comparator, both fit to the same training512. Negative favors APTC. The risk track uses population marginal ES, normalized by the training historical baseline ES; the error track uses common equal-weight relative absolute error. These additional paired summaries were formed after execution from prespecified logged metrics, with no method changes and no multiplicity-adjusted superiority claim.

## Preregistered decision

```json
{
  "gaussian": {
    "harm_pass": true,
    "switch_pass": false,
    "all_comparators_pass": false
  },
  "student_t4": {
    "harm_pass": true,
    "switch_pass": false,
    "all_comparators_pass": false
  },
  "asymmetric_crash": {
    "harm_pass": true,
    "switch_pass": false,
    "all_comparators_pass": false
  }
}
```

The gate is a generic statistical control; even a pass would not establish novelty or finite-sample safety. See DECISION_GAP_DECISION.md for adjudication and limitations.
