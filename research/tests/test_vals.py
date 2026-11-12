import numpy as np
from vals import synthetic_fisheye, vals_source, vals_improved

GT = dict(cx=410.3, cy=297.6, r=260.0)


def test_vals_clean_synthetic():
    r = vals_source(synthetic_fisheye(**GT), 40, 5)
    assert r.ok
    assert np.hypot(r.center[0] - GT["cx"], r.center[1] - GT["cy"]) < 1.0
    assert abs(r.radius - GT["r"]) < 1.5


def test_vals_mean_filter_can_leave_one_pair():
    """BUG-07 evidence: `distance < mean` keeps only 1 pair -> Kasa fails on a CLEAN image."""
    r = vals_source(synthetic_fisheye(**GT), 40, 3)
    assert not r.ok and len(r.valid_points) == 2


def test_vals_outlier_specks_break_source():
    r = vals_source(synthetic_fisheye(**GT, specks=6, seed=3), 40, 5)
    assert not r.ok or np.hypot(r.center[0] - GT["cx"], r.center[1] - GT["cy"]) > 20


def test_vals_n_zero_no_pairs():
    """N = 0 is reachable from the trackbar (min 0): no direction -> 0/0 mean in C++."""
    r = vals_source(synthetic_fisheye(**GT), 40, 0)
    assert not r.ok and r.distances == []


def test_improved_vals():
    for kw in ({}, dict(specks=6, seed=3), dict(noise=8)):
        r = vals_improved(synthetic_fisheye(**GT, **kw), 40)
        assert r.ok and np.hypot(r.center[0] - GT["cx"], r.center[1] - GT["cy"]) < 0.5
