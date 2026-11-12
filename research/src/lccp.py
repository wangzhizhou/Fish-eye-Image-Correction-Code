"""LCCP - Longitudinal Compression Cylindrical Projection (纵向压缩柱面投影).

Ports of corrector.cpp:
    func      L733-737     getPhi   L738-786
    func1     L1001-1006   getPhi1  L1007-1060
    auxFunc   L1062-1068
plus closed forms derived in REPORT.md section 7 and verified with SymPy
(tests/test_lccp.py, experiments/verify_symbolic.py).

Notation
    phi  : colatitude used by the source, phi = acos(y) in [0, pi]
           phi = 0 north pole, pi/2 equator, pi south pole.
    psi  : geographic latitude, psi = pi/2 - phi in [-pi/2, pi/2]
    w    : the paper's omega (angle between chord PC and projection ray), (0, 3pi/4)
    h(w) : auxFunc(w, 0) = l(w, 0), half height of the cylinder image (paper Eq. 17)

Closed forms (derivation in REPORT.md, verified symbolically):
    auxFunc(w, phi) = sgn(psi) * 2 sin(w) sin(|psi|/2) / sin(w + |psi|/2)
    h(w)            = 2 sin w / (sin w + cos w) = sqrt(2) sin w / sin(3pi/4 - w)
    w = pi/2:       auxFunc = 2 tan(psi/2)   (Braun stereographic cylindrical projection)
    getPhi(l)       = 2 atan(l / (4 - l)),   l in [0, 4)
    getPhi1(l, w)   = pi/2 - sgn(s) * 2 atan(|s| sin w / (2 sin w - |s| cos w)),  s = h(w) - l
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

PI = 3.1415926535897932384626433832795   # same literal as globalInclude.h
LIMIT = 1e-4                             # globalInclude.h: const double LIMIT = 1e-4
W_MAX = 3 * math.pi / 4


# --------------------------------------------------------------------------
# getPhi / func  (w = pi/2 special case, used by latitudeCorrection3)
# --------------------------------------------------------------------------
def func(l, phi):
    """corrector::func: (l/2 - 1) cos(phi) - sin(phi) + 1"""
    return (l / 2 - 1) * np.cos(phi) - np.sin(phi) + 1


@dataclass
class BisectInfo:
    phi: float
    iterations: int
    converged: bool
    residual: float


def get_phi_source(l: float, max_iter: int = 100000) -> BisectInfo:
    """Exact port of corrector::getPhi (no iteration cap in the source!).
    `max_iter` only exists so that the Python port cannot hang; reaching it means
    the C++ code would loop forever."""
    l = float(l)
    if 0 <= l < 2:
        head, tail = 0.0, PI / 2
        mid = head
        res = func(l, mid)
        it = 0
        while abs(res) > LIMIT:
            if it >= max_iter:
                return BisectInfo(mid, it, False, res)
            it += 1
            mid = (tail + head) / 2
            res = func(l, mid)
            if res > 0:
                head = mid
            else:
                tail = mid
    else:
        head, tail = PI / 2, PI
        mid = tail
        res = func(l, mid)
        it = 0
        while abs(res) > LIMIT:
            if it >= max_iter:
                return BisectInfo(mid, it, False, res)
            it += 1
            mid = (tail + head) / 2
            res = func(l, mid)
            if res < 0:
                head = mid
            else:
                tail = mid
    return BisectInfo(mid, it, True, res)


def get_phi(l):
    return get_phi_source(l).phi


def get_phi_closed(l):
    """Closed-form inverse of l = 2 - 2 tan(pi/4 - phi/2), l in [0, 4]."""
    l = np.asarray(l, dtype=float)
    if np.any((l < 0) | (l > 4)):
        raise ValueError("l must be in [0, 4]")
    return 2 * np.arctan2(l, 4 - l)


def l_of_phi_braun(phi):
    """Forward map used implicitly by getPhi: l = 2 - 2 tan(pi/4 - phi/2) = 2 + 2 tan(psi/2)... sign:
    psi = pi/2 - phi, l = 2 - 2 tan(psi/2)."""
    phi = np.asarray(phi, dtype=float)
    return 2 - 2 * np.tan((PI / 2 - phi) / 2)


# --------------------------------------------------------------------------
# auxFunc
# --------------------------------------------------------------------------
def aux_func_source(w, phi):
    """Exact port of corrector::auxFunc (vectorised, double precision)."""
    w = np.asarray(w, dtype=float)
    phi = np.asarray(phi, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        l = np.sin(w) * np.sqrt(np.cos(phi) ** 2 + (1 - np.sin(phi)) ** 2) / \
            np.sin(PI - w - np.arctan((1 - np.sin(phi)) / np.abs(np.cos(phi))))
    return np.where(phi > PI / 2, -l, l)


def check_w(w):
    w = float(w)
    if not (0 < w < W_MAX):
        raise ValueError(f"w must lie in (0, 3pi/4); got {w}")
    return w


def aux_func_closed(w, phi):
    """auxFunc(w, phi) = sgn(psi) 2 sin w sin(|psi|/2) / sin(w + |psi|/2), psi = pi/2 - phi."""
    w = check_w(w)
    phi = np.asarray(phi, dtype=float)
    psi = math.pi / 2 - phi
    a = np.abs(psi) / 2
    return np.sign(psi) * 2 * math.sin(w) * np.sin(a) / np.sin(w + a)


def aux_func_tan_form(w, phi):
    """Equivalent: 2 tan(a) / (1 + cot(w) tan(a)) with sign; shows w=pi/2 -> 2 tan(psi/2)."""
    w = check_w(w)
    psi = math.pi / 2 - np.asarray(phi, dtype=float)
    t = np.tan(np.abs(psi) / 2)
    return np.sign(psi) * 2 * t / (1 + t / math.tan(w))


def lccp_h(w):
    """h(w) = auxFunc(w, 0) = 2 sin w / (sin w + cos w)."""
    w = check_w(w)
    return 2 * math.sin(w) / (math.sin(w) + math.cos(w))


def d_aux_d_psi(w, psi):
    """Derivative of the closed form w.r.t. latitude psi (|psi| branch): sin^2 w / sin^2(w+|psi|/2)."""
    w = check_w(w)
    a = np.abs(np.asarray(psi, float)) / 2
    return math.sin(w) ** 2 / np.sin(w + a) ** 2


def inv_aux_closed(s, w):
    """Solve auxFunc(w, phi) = s for phi (s in [-h, h])."""
    w = check_w(w)
    s = np.asarray(s, dtype=float)
    h = lccp_h(w)
    if np.any(np.abs(s) > h * (1 + 1e-12)):
        raise ValueError("|s| must be <= h(w)")
    a = np.arctan2(np.abs(s) * math.sin(w), 2 * math.sin(w) - np.abs(s) * math.cos(w))
    return math.pi / 2 - np.sign(s) * 2 * a


# --------------------------------------------------------------------------
# func1 / getPhi1 with emulation of C++ function-local `static`
# --------------------------------------------------------------------------
class SourceStatics:
    """Emulates `static double limit = auxFunc(w, 0)` in func1 and
    `static double lim = auxFunc(w, 0)` in getPhi1: both are initialised ONCE,
    with whatever w is passed on the first call, for the lifetime of the process."""

    def __init__(self):
        self.func1_limit = None
        self.getphi1_lim = None

    def func1(self, l, phi, w):
        if self.func1_limit is None:
            self.func1_limit = float(aux_func_source(w, 0.0))
        return l - self.func1_limit + float(aux_func_source(w, phi))

    def get_phi1(self, l, w, return_info=False):
        N_lim, N = 100, 0
        if self.getphi1_lim is None:
            self.getphi1_lim = float(aux_func_source(w, 0.0))
        lim = self.getphi1_lim
        if 0 <= l < lim:
            head, tail = 0.0, PI / 2
            mid = head
            res = self.func1(l, mid, w)
            while True:
                if not abs(res) > LIMIT:
                    break
                cond = N < N_lim
                N += 1                       # C++: N++ < N_lim (post-increment)
                if not cond:
                    break
                mid = (tail + head) / 2
                res = self.func1(l, mid, w)
                if res > 0:
                    head = mid
                else:
                    tail = mid
        else:
            N = 0
            head, tail = PI / 2, PI
            mid = tail
            res = self.func1(l, mid, w)
            while True:
                if not abs(res) > LIMIT:
                    break
                cond = N < N_lim
                N += 1
                if not cond:
                    break
                mid = (tail + head) / 2
                res = self.func1(l, mid, w)
                if res > 0:
                    head = mid
                else:
                    tail = mid
        if return_info:
            return BisectInfo(mid, N, abs(res) <= LIMIT, res)
        return mid


def get_phi1_source(l, w, return_info=False):
    """getPhi1 in a *fresh process* (statics initialised with this w)."""
    return SourceStatics().get_phi1(l, w, return_info)


def get_phi1_closed(l, w):
    """Closed form of the root of func1: auxFunc(w, phi) = h(w) - l, l in [0, 2h]."""
    w = check_w(w)
    h = lccp_h(w)
    l = np.asarray(l, dtype=float)
    if np.any((l < -1e-12) | (l > 2 * h * (1 + 1e-12))):
        raise ValueError("l must be in [0, 2 h(w)]")
    return inv_aux_closed(np.clip(h - l, -h, h), w)


# --------------------------------------------------------------------------
# normalised vertical coordinate of LCCP
# --------------------------------------------------------------------------
def lccp_v_norm(phi, w):
    """Output row as a fraction of image height: v/H = (h - aux(w,phi)) / (2h)   (Eq. 17)."""
    h = lccp_h(w)
    return (h - aux_func_closed(w, phi)) / (2 * h)


def lccp_phi_from_v_norm(t, w):
    """Inverse of lccp_v_norm, t in [0, 1]."""
    return get_phi1_closed(np.asarray(t, float) * 2 * lccp_h(w), w)
