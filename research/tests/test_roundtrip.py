import numpy as np
import pytest
from lccp import PI
from correction import c5_forward_coords
from coordinate_transform import latlon_to_xyz, xyz_to_latlon, fast_atan2_deg
from experiment_roundtrip import c4_inverse


def _pts(n=3000, cx=945, cy=634, R=623, seed=0):
    rng = np.random.default_rng(seed)
    r = R * np.sqrt(rng.uniform(0, 1, n)) * 0.999
    t = rng.uniform(0, 2 * PI, n)
    return cx + r * np.cos(t), cy + r * np.sin(t)


def test_latlon_xyz_inverse():
    phi, lam = np.meshgrid(np.linspace(0.01, 3.13, 50), np.linspace(0.01, 3.13, 50))
    p2, l2 = xyz_to_latlon(*latlon_to_xyz(phi, lam))
    assert np.allclose(p2, phi, atol=1e-12) and np.allclose(l2, lam, atol=1e-12)


@pytest.mark.parametrize("w", [PI / 6, PI / 4, PI / 2, 2 * PI / 3])
def test_c4_c5_exact_inverse(w):
    u, v = _pts()
    U, V = c5_forward_coords(u, v, 945, 634, 623, w, PI, 512, fast=False)
    u2, v2 = c4_inverse(U, V, 945, 634, 623, w, source=False)
    assert np.max(np.hypot(u2 - u, v2 - v)) < 1e-8


def test_c4_c5_source_numerics_subpixel():
    u, v = _pts()
    U, V = c5_forward_coords(u, v, 945, 634, 623, PI / 2, PI, 512, fast=True)
    u2, v2 = c4_inverse(U, V, 945, 634, 623, PI / 2, source=True)
    assert np.max(np.hypot(u2 - u, v2 - v)) < 0.5


def test_truncation_bias():
    """BUG-05 evidence. C++-exact pipeline: C5 truncates the output coords AND C4's Point(u,v)
    truncates the fisheye coords (measured with research/cpp_harness) -> systematic negative
    offset. Rounding in both (proposed fix) removes it."""
    u, v = _pts(5000)
    ui, vi = np.rint(u), np.rint(v)
    U, V = c5_forward_coords(ui, vi, 945, 634, 623, PI / 2, PI, 512, fast=True)
    ok = (U >= 0) & (U < 512) & (V >= 0) & (V < 512)
    u3, v3 = c4_inverse(np.trunc(U[ok]), np.trunc(V[ok]), 945, 634, 623, PI / 2, source=True)
    assert np.mean(np.trunc(v3) - vi[ok]) < -2.0
    assert np.mean(np.trunc(u3) - ui[ok]) < -1.0
    u4, v4 = c4_inverse(np.rint(U[ok]), np.rint(V[ok]), 945, 634, 623, PI / 2, source=True)
    assert abs(np.mean(np.rint(v4) - vi[ok])) < 0.1


@pytest.mark.parametrize("model", ["STEREOGRAPHIC", "EQUISOLID", "ORTHOGONAL"])
def test_not_inverse_for_other_models(model):
    """BUG-06 evidence: C5 hard-codes EQUIDISTANCE."""
    u, v = _pts()
    U, V = c5_forward_coords(u, v, 945, 634, 623, PI / 2, PI, 512, fast=False)
    u2, v2 = c4_inverse(U, V, 945, 634, 623, PI / 2, model=model, source=False)
    assert np.max(np.hypot(u2 - u, v2 - v)) > 10


def test_fast_atan2_error_bound():
    rng = np.random.default_rng(1)
    y, x = rng.normal(size=20000), rng.normal(size=20000)
    d = np.abs(fast_atan2_deg(y, x) - np.degrees(np.mod(np.arctan2(y, x), 2 * np.pi)))
    d = np.minimum(d, 360 - d)
    assert d.max() < 0.011


def test_fast_atan2_matches_opencv():
    cv2 = pytest.importorskip("cv2")
    rng = np.random.default_rng(2)
    y, x = rng.normal(size=2000), rng.normal(size=2000)
    ref = np.array([cv2.fastAtan2(float(a), float(b)) for a, b in zip(y, x)])
    assert np.max(np.abs(fast_atan2_deg(y, x) - ref)) < 1e-3


def test_fov_below_pi_samples_outside_circle():
    """BUG-13 evidence: only `pt.inside(imgArea)` is tested, latitude always spans [0, pi]."""
    from correction import c4_latlon, c3_latlon
    from coordinate_transform import latlon_to_xyz
    for fov, lo in ((0.9 * PI, 0.2), (0.75 * PI, 0.4)):
        for phi, lam in (c4_latlon(256, 256, PI / 2, fov=fov, source_like=False), c3_latlon(256, 256, False)):
            P, L = np.meshgrid(phi, lam, indexing="ij")
            T = np.arccos(np.clip(latlon_to_xyz(P, L)[2], -1, 1))
            assert (T > fov / 2 + 1e-9).mean() > lo


def test_c5_out_of_bounds_reads_when_circle_clipped():
    """BUG-06 evidence: the C++ loop reads imgOrg.at(j, i) outside the image."""
    from correction import correction5
    img = np.zeros((300, 400, 3), np.uint8)
    _, _, oob = correction5(img, 200, 120, 150)      # circle extends above the image (120 - 150 < 0)
    assert oob > 0
    _, _, oob2 = correction5(np.zeros((400, 400, 3), np.uint8), 200, 200, 150)
    assert oob2 == 0


def test_c5_forward_mapping_holes():
    """BUG-07 evidence: forward splatting leaves unfilled output pixels."""
    from correction import correction5
    img = np.full((280, 280, 3), 200, np.uint8)
    _, hit, _ = correction5(img, 140, 140, 128)
    assert 1 - hit.mean() > 0.5
