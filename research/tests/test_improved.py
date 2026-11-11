"""Tests of the improvement proposal in research/improved (NOT the original program/ code).
C++ parts are skipped unless research/improved/cpp/build.sh has been run."""
import math
import os
import subprocess
import sys

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "improved"))
from geometry import Axis, Camera, Output, LENSES, PI  # noqa: E402
from lccp import get_phi1_closed, lccp_h  # noqa: E402
import projection_metrics as pm  # noqa: E402

CLI = os.path.join(HERE, "..", "improved", "cpp", "build", "improved_cli")
need_cli = pytest.mark.skipif(not os.path.exists(CLI), reason="improved C++ not built")


@pytest.mark.parametrize("w", [PI / 6, PI / 4, PI / 3, PI / 2, 2 * PI / 3])
def test_lccp_closed_form_matches_verified_getphi1(w):
    """Axis('lccp', w).inv is the closed form proven with SymPy in phase 1: phi = getPhi1(l, w)."""
    h = lccp_h(w)
    l = np.linspace(0, 2 * h, 1001)
    psi = Axis("lccp", w).inv(h - l)
    assert np.max(np.abs((PI / 2 - psi) - get_phi1_closed(l, w))) < 1e-12


@pytest.mark.parametrize("w", [0.3, PI / 2, 2.2])
def test_axis_roundtrip_and_slope(w):
    a = Axis("lccp", w)
    x = np.linspace(-PI / 2, PI / 2, 2001)
    assert np.max(np.abs(a.inv(a.fwd(x)) - x)) < 1e-13
    num = (a.fwd(x + 1e-6) - a.fwd(x - 1e-6)) / 2e-6
    away = np.abs(x) > 1e-5          # C1 at a = 0 but the 2nd derivative jumps by 2 cot w (REPORT §6.2)
    assert np.max(np.abs(num - a.dfwd(x))[away]) < 1e-6
    assert abs(a.dfwd(0.0) - 1) < 1e-15


@pytest.mark.parametrize("lens", LENSES)
def test_lens_roundtrip_python(lens):
    cam = Camera(945.3, 634.7, 623.0, lens, PI)
    rng = np.random.default_rng(0)
    rr = 623 * np.sqrt(rng.uniform(0, 1, 2000)) * 0.999
    t = rng.uniform(0, 2 * PI, 2000)
    u, v = cam.cx + rr * np.cos(t), cam.cy + rr * np.sin(t)
    d, ok = cam.pixels_to_rays(u, v)
    u2, v2, ok2 = cam.rays_to_pixels(d)
    assert ok.all() and ok2.all() and np.max(np.hypot(u2 - u, v2 - v)) < 1e-9


def test_projection_metrics_analytic():
    # equirectangular: k/h = 1/cos(psi) -> 2 at psi = 60 deg; Braun lat: 1/(cos60 sec^2 30) = 1.5
    assert abs(pm.metrics(Axis("lin"), Axis("lin"), 121)["k_over_h_at_psi60_centre"] - 2) < 1e-12
    assert abs(pm.metrics(Axis("lin"), Axis("lccp", PI / 2), 121)["k_over_h_at_psi60_centre"] - 1.5) < 1e-12
    # Correction3 stretches the horizon horizontally by sec^2(lam/2): 4/3 at 60 deg
    assert abs(pm.metrics(Axis("lccp", PI / 2), Axis("lccp", PI / 2), 121)["horizon_k_over_h_at_lam60"] - 4 / 3) < 1e-12


def test_radial_circle_threshold_free():
    from vals import synthetic_fisheye
    from circle_radial import detect_circle
    img = synthetic_fisheye(cx=410.3, cy=297.6, r=260.0, inner=45, background=10, vignette=0.6, texture=10, seed=0)
    for t in ("auto", 5, 80):
        r = detect_circle(img, t)
        assert r.reliable and math.hypot(r.cx - 410.3, r.cy - 297.6) < 0.3 and abs(r.r - 260) < 0.5


@need_cli
def test_cpp_maps_match_python(tmp_path):
    cam = Camera(946.37, 634.62, 623.0, "EQUISOLID", math.radians(183))
    o = Output(Axis("lin"), Axis("lccp", 1.8)).resolve(cam)
    subprocess.run([CLI, "maps", f"out={tmp_path / 'm.bin'}", f"cx={cam.cx!r}", f"cy={cam.cy!r}", f"r={cam.r!r}",
                    f"lens={cam.lens}", f"fov={cam.fov!r}", *o.cli_args()], check=True)
    hw = np.fromfile(tmp_path / "m.bin", np.int32, 2)
    m = np.fromfile(tmp_path / "m.bin", np.float32, offset=8).reshape(2, *hw)
    u, v, ok = cam.rays_to_pixels(o.rays())
    assert np.array_equal(ok, m[0] >= 0)
    assert np.max(np.abs(m[0][ok] - u[ok])) < 1e-3 and np.max(np.abs(m[1][ok] - v[ok])) < 1e-3


@need_cli
@pytest.mark.parametrize("lens", LENSES)
def test_cpp_roundtrip_unbiased(tmp_path, lens):
    cam = Camera(945, 634, 623, lens)
    o = Output(Axis("lin"), Axis("lccp", PI / 2)).resolve(cam)
    subprocess.run([CLI, "roundtrip", f"out={tmp_path / 'r.txt'}", "step=7", "cx=945", "cy=634", "r=623", f"lens={lens}",
                    *o.cli_args()], check=True)
    d = {k: float(v) for k, v in (ln.split() for ln in open(tmp_path / "r.txt") if ln.strip())}
    assert d["cont_max"] < 1e-9 and abs(d["bias_u"]) < 0.01 and abs(d["bias_v"]) < 0.01


@need_cli
def test_cpp_no_side_effects_and_exit_codes(tmp_path):
    r = subprocess.run([CLI, "statics"], capture_output=True, text=True)
    assert r.returncode == 0
    r = subprocess.run([CLI, "correct", "in=/nonexistent.jpg", f"out={tmp_path / 'x.png'}", "cx=1", "cy=1", "r=1"],
                       cwd=tmp_path, capture_output=True, text=True)
    assert r.returncode != 0 and os.listdir(tmp_path) == []          # no ret.jpg, failure is reported


def test_paper_table1_recomputation():
    """journal p.1445 Table 1: radii are half the pair distance, mean 419.30, kept-pair Kasa fit."""
    from paper_checks import table1
    t = table1()
    assert all(abs(r["radius_recomputed"] - r["radius_paper"]) <= 0.011 for r in t["rows"])
    assert abs(t["mean_recomputed"] - 419.30) < 0.01
    k = t["kasa_kept_pairs_2to5"]
    assert abs(k["cx"] - 433.09) < 0.01 and abs(k["cy"] - 468.62) < 0.01 and abs(k["r"] - 412.79) < 0.01


def test_paper_vals_clean_but_fragile():
    """VALS as the paper describes it: accurate on a clean image, fails under outlier specks."""
    from vals import synthetic_fisheye
    from vals_paper import vals_paper
    gt = dict(cx=410.3, cy=297.6, r=260.0)
    v = vals_paper(synthetic_fisheye(seed=0, **gt), 40, 5)
    assert v.ok and math.hypot(v.center[0] - 410.3, v.center[1] - 297.6) < 0.5
    errs = []
    for s in (0, 1, 2):
        v = vals_paper(synthetic_fisheye(seed=s, specks=4, **gt), 40, 5)
        errs.append(math.hypot(v.center[0] - 410.3, v.center[1] - 297.6))
    assert max(errs) > 50
