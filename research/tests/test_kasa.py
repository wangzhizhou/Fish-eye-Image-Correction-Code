import numpy as np
import pytest
from kasa import FITTERS, kasa_fit, kasa_fit_source
from vals import synthetic_edge_points


@pytest.mark.parametrize("name", list(FITTERS))
def test_exact_circle_recovered(name):
    t = np.linspace(0, 2 * np.pi, 50, endpoint=False)
    p = np.c_[123.4 + 77 * np.cos(t), -50.5 + 77 * np.sin(t)]
    c = FITTERS[name](p)
    assert c.ok
    assert abs(c.cx - 123.4) < 1e-6 and abs(c.cy + 50.5) < 1e-6 and abs(c.r - 77) < 1e-6


def test_kasa_noise_accuracy():
    p = synthetic_edge_points(400, 640, 480, 300, noise=1.0, seed=3)
    c = kasa_fit(p)
    assert np.hypot(c.cx - 640, c.cy - 480) < 0.3 and abs(c.r - 300) < 0.3


def test_kasa_needs_three_points():
    assert not kasa_fit([[0, 0], [1, 1]]).ok
    ok, *_ = kasa_fit_source(np.array([[0, 0], [1, 1]]))
    assert not ok          # source: validPoints.size() <= 2 -> false


def test_source_truncates_centre_to_int():
    # BUG-08 evidence: centre 100,100 is computed as 99.99999999999937 and truncated to 99
    ok, c, r, cf = kasa_fit_source(np.array([[0, 100], [100, 0], [200, 100], [100, 200]]))
    assert ok and abs(cf[1] - 100) < 1e-9
    assert c == (100, 99)


def test_kasa_short_arc_bias():
    """Kasa is known to be biased toward small radii on short arcs (documented weakness)."""
    errs_k, errs_t = [], []
    for s in range(20):
        p = synthetic_edge_points(60, 0, 0, 300, noise=1.0, arc=(0, np.radians(45)), seed=s)
        errs_k.append(FITTERS["kasa"](p).r - 300)
        errs_t.append(FITTERS["taubin"](p).r - 300)
    assert np.mean(errs_k) < np.mean(errs_t)
