# Local execution environment

Verified on2026-10-05; structured receipt: [local_environment.json](local_environment.json).

- Apple M4 Pro,12CPU cores (8performance/4efficiency),24GB reported by `system_profiler`; macOS26.2,arm64. Hardware identifiers were not published.
- CPython3.13.15 installed with existing `uv`, isolated repository `.venv`. Default machine Python was3.14.7, so it was not used for the pinned study.
- Original pins preserved: NumPy2.3.5, SciPy1.17.0, scikit-learn1.8.0, pytest9.0.2. Exact transitive versions in `requirements-local.lock`.
- CPU only. All five numerical-thread environment variables set to1; observed OpenMP pool1; `threadpool_limits(1)` around model fits. NumPy/SciPy macOS wheels can use Accelerate, whose internal pool is not enumerated by threadpoolctl; `VECLIB_MAXIMUM_THREADS=1` is set before numerical imports in the runner.
-2 process workers per empirical run. They are numerical processes, not independent research agents. No MPS/neural stack installed.

## Local evidence before held-out evaluation

Original suite: **26 passed in19.21s**, including first import/startup overhead. Extended suite: **47 passed in1.96s**, including all original tests. New tests check missing-date bridges, quote orientation, domain/sign/fractional tail atoms, past-only fit, common targets, historical penalty reporting, original-calibration compatibility, explicit fallback, nonconvergence retention, deterministic bootstrap pairing and atomic/config-bound resume.

ECB development smoke:20windows/660rows,2010-01-04–2010-05-19, stride5,2workers,2.7675s. BoC development smoke:20windows/660rows,2019-01-23–2019-06-10,2.7300s. No fallback/nonconvergence in either smoke. BoC has513 initial return origins without full512+gap history. These timings do not measure every model separately; methods share fits.

Receipts: [`results/local_market/development/smoke_receipts.json`](../results/local_market/development/smoke_receipts.json). First exploratory ECB smoke before adding aggregate/audit modules was also20windows and produced identical forecast checksum; final smoke uses the source tree frozen for evaluation. Smoke subsampling is not a five-day horizon or full development backtest.

## Errors and recovery

Sandbox initially blocked Git refs, uv runtime/cache and PyPI DNS; explicit approved escalation enabled required writes/downloads. One SciPy transfer failed with `address not available`; bounded retry succeeded without changing pins or disabling TLS. Both market downloads succeeded with official HTTPS endpoints. A hardware `sysctl` query was blocked, so hardware evidence is the successful `system_profiler` query; no inferred memory byte count is claimed.

Orca Run `run_6a65aab12f88`: data Task `task_3b8213467ac2`, runner Task `task_1c9bffedb8bc`, review Task `task_340776b81f92` all failed before task delivery at `agent_readiness timeout`. The data Task retry using exact RiskDecision workspace also failed. Four owned terminals released, zero reclaimable. The coordinator completed the work directly. Independent agent review: **NOT RUN**.
