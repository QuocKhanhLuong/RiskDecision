# Frozen Q2 HMM pilot — measured receipts

Status: COMPLETE / VERIFIED, synthetic data only. See the single consolidated
[Vietnamese report](../../../docs/experiments/20261008_markov_hmm_q2.md) and
[prospective protocol](../../../markov_hmm/PROTOCOL.md).

Base `3203bb34966ad8e029ea684e6cadf1b9c9bacbd1`; branch `research/markov-hmm-q2`.
Config SHA256 `85aa84337b91f026b0115bbb8151bb635ddce1937ad8042bb5ef22f331b5d738`.
Pilot fingerprint `b7d6c5de335678e76ea7deb729b11a9d2c74f08c8c7f6a55eb7c3e99c5ce80a8`.

| Actual execution | Result |
|---|---|
| Tests | 99 PASS / 2.57 seconds |
| Development | 32 origins; 3.296 seconds case compute; numerical gate PASS |
| Prospective ×2 compute estimate | 105.479 seconds, cap 600 |
| Fresh pilot | 512 origins, 32 independent path clusters, 7,168 rows |
| Fits | 1,536 HMM starts, all converged; 1,024 decisions/thresholds |
| Pilot compute | 54.178 seconds case compute; 55.701 completion-session seconds |
| Verifier | PASS, 50.812 seconds; 216 paired CIs and all restart likelihoods |
| Complete resume | 512 reused, 0 new, 551 artifacts byte-identical; 1.781 seconds |
| Historical preservation | 274 previously tracked files byte-identical |

Primary stationary/full512/all conditional squared relative error:
HMM .0095967814 versus Gaussian iid .0952384002; delta −.0856416187,
95% paired path-cluster CI [−.1016420002, −.0698445582].
This is a known-family HMM baseline, not a new method or universal superiority.
Secondary shift-after HMM − EWMA delta −.0721563642,
CI [−.1005058655, −.0475323354]. Secondary intervals are unadjusted.

Negative target-transfer result retained: full512 marginal MSE of filtered HMM
.240757/.239963 (stationary/shift), versus raw .029854/.025639. Conditional and
historical marginal targets are distinct. No model/config/seed changes after
pilot outcomes. Zero case failures, null estimates or runtime warnings.

`preflight.json`, `development/benchmark.json`, stage `freeze.json`,
`case_index.csv`, `progress.jsonl`, terminal logs, `verification.json` and
`resume_verification.json` contain the execution receipts. Large exports are
losslessly compressed with raw hashes in `compressed_exports.json`.
`checkpoint_payloads.tar.gz` contains all synthetic NPZ paths/case checkpoints;
`checkpoint_manifest.json` provides every member hash. Restore absent payloads
before resume/verification on a clone; do not overwrite differing local files.

REPORTED/READ: old Q0/Q1/Q2 reports, official hmmlearn documentation and installed
source. NOT_RUN: market, economic utility, neural/APTC, calibrated joint VaR/ES,
state-count/window tuning, online change detection or independent peer review.
Sole proposed continuation is the Q3 evaluator described in the report.
