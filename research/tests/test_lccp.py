import math
import numpy as np
import pytest
import lccp as L

WS = [np.pi / 6, np.pi / 4, np.pi / 3, np.pi / 2, 2 * np.pi / 3, 2.3]
PHI = np.linspace(0, np.pi, 5001)


@pytest.mark.parametrize("w", WS)
def test_auxfunc_closed_form(w):
    assert np.max(np.abs(L.aux_func_source(w, PHI) - L.aux_func_closed(w, PHI))) < 1e-12
    assert np.max(np.abs(L.aux_func_closed(w, PHI) - L.aux_func_tan_form(w, PHI))) < 1e-12


@pytest.mark.parametrize("w", WS)
def test_h_matches_paper_eq17(w):
    h = L.lccp_h(w)
    assert abs(h - float(L.aux_func_source(w, 0.0))) < 1e-12
    assert abs(h - math.sqrt(2) * math.sin(w) / math.sin(3 * math.pi / 4 - w)) < 1e-12


@pytest.mark.parametrize("w", WS)
def test_aux_monotone_continuous_odd(w):
    a = L.aux_func_source(w, np.linspace(0, np.pi, 100001))
    assert np.all(np.diff(a) < 0)
    eps = 1e-9
    assert abs(L.aux_func_source(w, np.pi / 2 - eps) - L.aux_func_source(w, np.pi / 2 + eps)) < 1e-8
    assert np.allclose(L.aux_func_closed(w, np.pi / 2 - (PHI - np.pi / 2)), -L.aux_func_closed(w, PHI), atol=1e-12)
    assert abs(float(L.aux_func_source(w, np.pi))) - L.lccp_h(w) < 1e-12


def test_w_pi_over_2_is_braun():
    psi = np.pi / 2 - PHI
    assert np.allclose(L.aux_func_closed(np.pi / 2, PHI), 2 * np.tan(psi / 2), atol=1e-12)


def test_w_domain():
    for w in (0.0, 3 * np.pi / 4, 2.5, -0.1):
        with pytest.raises(ValueError):
            L.lccp_h(w)
    assert np.isinf(L.aux_func_source(3 * np.pi / 4, 0.0)) or abs(L.aux_func_source(3 * np.pi / 4, 0.0)) > 1e12
    assert L.aux_func_source(5 * np.pi / 6, 0.0) < 0     # sign flips outside the domain


def test_getphi_closed_form_and_spurious_root():
    for l in np.linspace(0, 3.99, 200):
        assert abs(L.func(l, L.get_phi_closed(l))) < 1e-12
        assert abs(L.func(l, np.pi / 2)) < 1e-15          # pi/2 is ALWAYS a root
    # forward map l = 2 - 2 tan(pi/4 - phi/2)
    phi = np.linspace(0.01, 3.13, 50)
    assert np.allclose(L.get_phi_closed(L.l_of_phi_braun(phi)), phi, atol=1e-12)


def test_getphi_bisection_error_peaks_at_equator():
    """BUG-01 evidence: |f| <= 1e-4 stopping rule + double root -> 0.0123 rad error at l = 2."""
    far = [abs(L.get_phi(l) - L.get_phi_closed(l)) for l in np.linspace(0, 1.5, 200)]
    assert max(far) < 5e-4
    e2 = abs(L.get_phi(2.0) - np.pi / 2)
    assert e2 > 0.01


def test_getphi_nonconvergence_outside_domain():
    """BUG-02 evidence: l > 4 -> infinite loop in C++ (port stops at max_iter)."""
    assert not L.get_phi_source(5.0, max_iter=2000).converged
    assert L.get_phi_source(3.9).converged


@pytest.mark.parametrize("w", WS[:-1])
def test_getphi1_closed_form(w):
    h = L.lccp_h(w)
    ls = np.linspace(0, 2 * h, 801)[:-1]
    bis = np.array([L.get_phi1_source(l, w) for l in ls])
    assert np.max(np.abs(bis - L.get_phi1_closed(ls, w))) < 5e-4
    phi = L.get_phi1_closed(ls, w)
    assert np.allclose(ls - h + L.aux_func_closed(w, phi), 0, atol=1e-11)   # func1 == 0
    assert np.all(np.diff(phi) > 0)


def test_getphi_equals_getphi1_at_half_pi():
    ls = np.linspace(0, 3.99, 300)
    assert np.allclose(L.get_phi_closed(ls), L.get_phi1_closed(ls, np.pi / 2), atol=1e-12)


def test_static_cache_bug():
    """BUG-03 evidence: statics initialised with the first w are reused for later w."""
    st = L.SourceStatics()
    st.get_phi1(0.3, np.pi / 2)
    stale = st.get_phi1(0.3, np.pi / 4)
    fresh = L.get_phi1_closed(0.3, np.pi / 4)
    assert abs(stale - fresh) > 0.1
    assert abs(L.get_phi1_source(0.3, np.pi / 4) - fresh) < 5e-4


def test_inverse_aux():
    for w in WS[:-1]:
        h = L.lccp_h(w)
        s = np.linspace(-h, h, 101)
        assert np.allclose(L.aux_func_closed(w, L.inv_aux_closed(s, w)), s, atol=1e-11)


@pytest.mark.parametrize("w", WS[:-1])
def test_lccp_is_central_projection_from_fixed_point(w):
    """Derived interpretation (REPORT 6.2): in the meridian plane with tangent point C=(1,0)
    and tangent line x=1, the northern half is projected from X=(cos 2w, sin 2w), the
    southern half from its mirror image (cos 2w, -sin 2w)."""
    psi = np.linspace(1e-3, np.pi / 2, 400)
    for sgn in (1, -1):
        xA, yA = np.cos(psi), sgn * np.sin(psi)
        xX, yX = np.cos(2 * w), sgn * np.sin(2 * w)
        ok = np.hypot(xA - xX, yA - yX) > 1e-6          # A == X (w = pi/4 at the pole) is a 0/0 limit
        y = yX + (yA[ok] - yX) * (1 - xX) / (xA[ok] - xX)
        assert np.allclose(y, L.aux_func_closed(w, np.pi / 2 - sgn * psi[ok]), atol=1e-10)
