"""C++ (original program/ sources, via research/cpp_harness) vs Python port.
Skipped unless the harness has been built:  bash research/cpp_harness/build.sh"""
import os
import subprocess

import numpy as np
import pytest

from lccp import PI, get_phi_source, SourceStatics, aux_func_source
from correction import c4_latlon, maps_from_latlon

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, "..", "cpp_harness", "build")
HARNESS = os.path.join(BUILD, "harness")
REPO = os.environ.get("FISHEYE_REPO", os.path.abspath(os.path.join(HERE, "..", "..")))
pytestmark = pytest.mark.skipif(not os.path.exists(HARNESS), reason="C++ harness not built")


def _run(tmp_path, *args):
    r = subprocess.run([HARNESS, *map(str, args)], cwd=tmp_path, capture_output=True, text=True,
                       stdin=subprocess.DEVNULL, timeout=300)
    assert r.returncode == 0, r.stderr
    return r


def test_getphi_bitwise_and_equator_error(tmp_path):
    _run(tmp_path, "getphi", 1920, tmp_path / "g.txt")
    j, l, phi = np.loadtxt(tmp_path / "g.txt").T
    assert np.array_equal(phi, [get_phi_source(x).phi for x in l])        # bit-identical
    assert abs(phi[960] - PI / 2 - 0.012271846303085088) < 1e-15             # BUG-01 in C++


def test_static_cache_in_cpp(tmp_path):
    _run(tmp_path, "static", repr(PI / 2), repr(PI / 4), 512, tmp_path / "s.txt")
    j, l, phi = np.loadtxt(tmp_path / "s.txt").T
    st = SourceStatics()
    st.get_phi1(0.0, PI / 2)
    assert np.array_equal(phi, [st.get_phi1(x, PI / 4) for x in l])         # BUG-03 in C++


def test_point_constructor_truncates(tmp_path):
    """cv::Point(double,double) truncates: C4 sampling map equals Python trunc map exactly."""
    import cv2
    h, w = 1280, 1920
    v, u = np.mgrid[0:h, 0:w]
    img = np.dstack([u & 255, v & 255, 128 | (u >> 8) | ((v >> 8) << 3)]).astype(np.uint8)
    cv2.imwrite(str(tmp_path / "enc.png"), img)
    _run(tmp_path, "c4", tmp_path / "enc.png", 945, 634, 623, repr(PI / 2), "EQUIDISTANCE", repr(PI), tmp_path / "o.png")
    assert (tmp_path / "ret.jpg").exists()                                   # BUG-16 side effect
    o = cv2.imread(str(tmp_path / "o.png")).astype(int)
    cu, cv_ = o[..., 0] | ((o[..., 2] & 7) << 8), o[..., 1] | (((o[..., 2] >> 3) & 7) << 8)
    phi, lam = c4_latlon(512, 512, PI / 2, PI / 2, PI, source_like=True)
    mu, mv = maps_from_latlon(phi, lam, 945, 634, 623, PI, "EQUIDISTANCE", fast=True)
    assert np.array_equal(np.trunc(mu).astype(int), cu) and np.array_equal(np.trunc(mv).astype(int), cv_)
    assert np.mean(np.rint(mu).astype(int) == cu) < 0.6


def test_corrected0_byte_identical(tmp_path):
    src = os.path.join(REPO, "ImagesForTest", "1", "1.JPG")
    gold = os.path.join(REPO, "resources", "corrected0.jpg")
    if not (os.path.exists(src) and os.path.exists(gold)):
        pytest.skip("repository images missing")
    _run(tmp_path, "c3", src, 946, 634, 623, tmp_path / "c0.jpg")
    assert open(tmp_path / "c0.jpg", "rb").read() == open(gold, "rb").read()


def test_aux_func_matches(tmp_path):
    _run(tmp_path, "aux", repr(PI / 3), tmp_path / "a.txt")
    phi, a = np.loadtxt(tmp_path / "a.txt").T
    assert np.max(np.abs(a - aux_func_source(PI / 3, phi))) < 1e-15
