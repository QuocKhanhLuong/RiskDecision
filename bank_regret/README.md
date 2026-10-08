# Finite-bank ES regret with action-local witnesses

This research module evaluates absolute minimax ES-difference regret for a fixed
finite action bank, two-component probability mixtures, finite component worlds,
and fixed costs from one common incumbent. It is a computational specialization,
not an established novelty, calibrated uncertainty guarantee, or trading system.

The bank lower envelope shares all Rockafellar–Uryasev threshold lines. For each
action, only that action's own quantile-crossing knots and interval endpoints
need to be queried. With K total support thresholds, the algorithm uses
O(K log K) time and O(K) storage per world. This is a real-arithmetic statement;
the implementation uses float64 and does not certify signs arbitrarily near zero.

See the [prospective protocol](PROTOCOL.md),
[derivation](../runs/compositional_risk/20261008/action_local_derivation.md), and
[consolidated executed report](../docs/experiments/20261008_compositional_risk_policy.md).

From repository root, with the existing Python environment:

```bash
rtk proxy .venv/bin/python -m pytest tests/test_bank_regret.py -q
rtk proxy .venv/bin/python -m bank_regret.run preflight --out runs/compositional_risk/reproduction
rtk proxy .venv/bin/python -m bank_regret.run run --out runs/compositional_risk/reproduction --max-new-cases 5
# Exit 3 above is the intentional incomplete-run status.
rtk proxy .venv/bin/python -m bank_regret.run run --out runs/compositional_risk/reproduction
rtk proxy .venv/bin/python -m bank_regret.run run --out runs/compositional_risk/reproduction
```

The last command revalidates inputs, fits and decisions but creates no new cases.
Its printed execution-loop timer excludes validation: use an outer process timer
for total resume cost. The published run's outer no-op resume cost is recorded.
Changed source, configuration, Python binary, versions, platform or thread
environment requires a **fresh output directory**. Never overwrite published
results. The immutable `mixture_order` dependencies are hashed with this module.

To audit the published run in its recorded environment:

```bash
rtk proxy .venv/bin/python scripts/verify_bank_regret.py
```

This validates all checkpoint hashes/input recipes, recreates learned policies,
checks all learned-world regrets against the union-knots solver, recomputes
summary/evaluations, checks risk-envelope LPs and the historical-file manifest.
It reuses the same observations; it is not an independent scientific replication.

The published pilot found a modest large-bank runtime gain and no joint policy
superiority. Keep both results: endpoints-only choices matched full choices on
all 64 histories despite some differing regret surfaces; shared uncertainty was
better than the rectangular control only in the stationary family and worse than
the simpler point policy there. Policy fit/choices were frozen before evaluation.
