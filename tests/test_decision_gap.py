import numpy as np
from numpy.testing import assert_allclose
from decision_gap_audit.core import intervals, assess


def test_identical_decisions_cancel_exactly():
    x = np.random.default_rng(2).normal(size=(256, 2))
    w = np.tile([.5, .5], (4, 1))
    r = intervals(x, w, 1, 999, 42)
    assert r["paired_radius"] == 0
    assert r["absolute_radius"] > 0
    assert_allclose(r["delta"], 0)
    assert all(i == 0 for i in r["choices"].values())


def test_translation_and_scale_equivariance():
    rng = np.random.default_rng(3)
    x = rng.normal(size=(256, 3))
    w = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1], [1/3]*3])
    a = intervals(x, w, 16, 999, 5)
    b = intervals(x*7+4, w, 16, 999, 5)
    assert_allclose(b["delta"], a["delta"]*7, atol=1e-12)
    assert_allclose(b["paired_radius"], a["paired_radius"]*7)
    assert b["choices"] == a["choices"]
    assert a["paired_radius"] <= 2*a["absolute_radius"]+1e-12


def test_shifted_loss_candidate_has_exact_gap():
    z = np.random.default_rng(7).normal(size=256)
    x = np.column_stack([z, z+1, z-1, z+.5])
    r = intervals(x, np.eye(4), 1, 999, 9)
    assert_allclose(r["delta"], [-1, 1, -.5], atol=1e-12)
    assert r["paired_radius"] < 1e-12
    assert r["choices"]["paired"] == 1


def test_truth_is_only_evaluation_and_negative_es_allowed():
    r = {"radii": {"paired": 0.}, "choices": {"paired": 1},
         "delta": np.array([-1., 1., -.5]), "paired_to_absolute_radius": 0.}
    rows = assess(r, np.array([-4., -5., -3., -4.5]), np.arange(4), 2., 1.)
    assert rows[0]["relative_delta"] == -.5
    assert rows[0]["relative_regret"] == 0
    assert rows[0]["harm"] == 0
