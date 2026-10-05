import numpy as np
from numpy.testing import assert_allclose
from local_market.stats import block_indices, bootstrap
from local_market.models import METHODS
from local_market.scoring import empirical_es


def test_blocks_are_contiguous_within_blocks_and_seeded():
    a = block_indices(np.random.default_rng(4), 100, 10, 20)
    assert a.shape == (20, 100)
    assert (np.diff(a.reshape(20, 10, 10), axis=2) == 1).all()
    assert_allclose(a, block_indices(np.random.default_rng(4), 100, 10, 20))


def test_bootstrap_identical_policies_have_zero_paired_difference():
    rows = []
    for i in range(100):
        for track, target in [("A", "equal_weight"), ("A", "historical_se_reference"), ("B", "own_selection")]:
            for m in METHODS:
                rows.append({"date": str(i).zfill(3), "track": track, "target": target, "method": m,
                             "fz0": np.sin(i), "pinball95": abs(np.sin(i)), "var_breach": int(i%20 == 0),
                             "shortfall_residual": np.cos(i), "realized_loss": np.sin(i)})
    _, pairs = bootstrap(rows, 5, replicates=200)
    assert all(r["difference"] == r["ci_low"] == r["ci_high"] == 0 for r in pairs)


def test_es_batched_fractional_matches_scalar():
    a = np.random.default_rng(5).normal(size=(5, 103, 4))
    e = empirical_es(a, axis=1)
    for i in range(5):
        for j in range(4):
            assert_allclose(e[i, j], empirical_es(a[i, :, j]))
