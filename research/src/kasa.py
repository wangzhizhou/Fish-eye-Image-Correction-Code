"""Circle fitting: Kasa (as in the source and the paper), plus Pratt / Taubin /
geometric (Levenberg-Marquardt) and a RANSAC wrapper for comparison.

Source reference: program/findCircleParameter.cpp, CircleFitByKasa (L840-879).
Paper reference:  Eq. (1)-(3), section 2.

Kasa model (algebraic):
    (x-a)^2 + (y-b)^2 = r^2
 => x^2 + y^2 = 2a*x + 2b*y + (r^2 - a^2 - b^2)
 => x^2 + y^2 = p1*x + p2*y + p3        (linear in p = [p1, p2, p3])
    A = [x y 1],  B = x^2 + y^2,  p = pinv(A) B
    a = p1/2, b = p2/2, r = sqrt((p1^2 + p2^2)/4 + p3)

All coordinates here are *pixel* coordinates (x right, y down) unless stated.
"""
from __future__ import annotations

import numpy as np
from dataclasses import dataclass

try:
    from scipy.optimize import least_squares
except Exception:  # pragma: no cover
    least_squares = None


@dataclass
class CircleFit:
    cx: float
    cy: float
    r: float
    ok: bool = True
    method: str = ""

    def residuals(self, pts: np.ndarray) -> np.ndarray:
        """Geometric residuals d_i = |p_i - c| - r."""
        pts = np.asarray(pts, dtype=float)
        return np.hypot(pts[:, 0] - self.cx, pts[:, 1] - self.cy) - self.r

    def rms(self, pts) -> float:
        return float(np.sqrt(np.mean(self.residuals(pts) ** 2)))


def _check(pts) -> np.ndarray:
    pts = np.asarray(pts, dtype=float)
    if pts.ndim != 2 or pts.shape[1] != 2:
        raise ValueError("points must be an (n, 2) array")
    if not np.all(np.isfinite(pts)):
        raise ValueError("points contain NaN/inf")
    return pts


def kasa_fit(pts) -> CircleFit:
    """Kasa fit in double precision (continuous version, no truncation)."""
    pts = _check(pts)
    if len(pts) < 3:
        return CircleFit(np.nan, np.nan, np.nan, ok=False, method="kasa")
    x, y = pts[:, 0], pts[:, 1]
    A = np.column_stack([x, y, np.ones_like(x)])
    B = x * x + y * y
    p, *_ = np.linalg.lstsq(A, B, rcond=None)   # == pinv(A) @ B (SVD based)
    p1, p2, p3 = p
    r2 = (p1 * p1 + p2 * p2) / 4.0 + p3
    if not np.isfinite(r2) or r2 <= 0:
        return CircleFit(np.nan, np.nan, np.nan, ok=False, method="kasa")
    return CircleFit(p1 / 2.0, p2 / 2.0, float(np.sqrt(r2)), method="kasa")


def kasa_fit_source(pts):
    """Bit-for-bit *behaviour* of CircleFitByKasa in the C++ source:

    * returns failure when len(pts) <= 2 (source: `validPoints.size() <= 2`)
    * B is stored as `vector<int>` (pow() result truncated to int; exact for
      integer pixel coordinates < 46341)
    * P = A.inv(CV_SVD) * B  (pseudo-inverse)
    * center.x = p1/2 and center.y = p2/2 are assigned to `int` -> C++ truncation
      toward zero; radius likewise truncated.
    Returns (ok, (cx_int, cy_int), r_int, (p1/2, p2/2, r_float)).
    """
    pts = np.asarray(pts)
    if len(pts) <= 2:
        return False, None, None, None
    pts = pts.astype(np.int64)
    x, y = pts[:, 0].astype(float), pts[:, 1].astype(float)
    A = np.column_stack([x, y, np.ones_like(x)])
    B = np.trunc(x * x + y * y)
    p = np.linalg.pinv(A) @ B
    p1, p2, p3 = p
    r = np.sqrt((p1 ** 2 + p2 ** 2) / 4 + p3)
    return True, (int(np.trunc(p1 / 2)), int(np.trunc(p2 / 2))), int(np.trunc(r)), (p1 / 2, p2 / 2, r)


def pratt_fit(pts) -> CircleFit:
    """Pratt (1987) fit, Newton-based implementation (Chernov 2010, 'PrattNewton')."""
    pts = _check(pts)
    if len(pts) < 3:
        return CircleFit(np.nan, np.nan, np.nan, ok=False, method="pratt")
    m = pts.mean(axis=0)
    X = pts - m
    Xi, Yi = X[:, 0], X[:, 1]
    Zi = Xi * Xi + Yi * Yi
    Mxy = np.mean(Xi * Yi); Mxx = np.mean(Xi * Xi); Myy = np.mean(Yi * Yi)
    Mxz = np.mean(Xi * Zi); Myz = np.mean(Yi * Zi); Mzz = np.mean(Zi * Zi)
    Mz = Mxx + Myy
    Cov_xy = Mxx * Myy - Mxy * Mxy
    A2 = 4 * Cov_xy - 3 * Mz * Mz - Mzz
    A1 = Mzz * Mz + 4 * Cov_xy * Mz - Mxz * Mxz - Myz * Myz - Mz ** 3
    A0 = Mxz * Mxz * Myy + Myz * Myz * Mxx - Mzz * Cov_xy - 2 * Mxz * Myz * Mxy + Mz * Mz * Cov_xy
    A22 = A2 + A2
    xnew, ynew = 0.0, 1e20
    for _ in range(99):
        yold = ynew
        ynew = A0 + xnew * (A1 + xnew * (A2 + 4 * xnew * xnew))
        if abs(ynew) > abs(yold):
            xnew = 0.0
            break
        Dy = A1 + xnew * (A22 + 16 * xnew * xnew)
        xold = xnew
        xnew = xold - ynew / Dy
        if abs((xnew - xold) / (xnew if xnew != 0 else 1)) < 1e-12:
            break
        if xnew < 0:
            xnew = 0.0
            break
    DET = xnew * xnew - xnew * Mz + Cov_xy
    if abs(DET) < 1e-300:
        return CircleFit(np.nan, np.nan, np.nan, ok=False, method="pratt")
    cx = (Mxz * (Myy - xnew) - Myz * Mxy) / DET / 2
    cy = (Myz * (Mxx - xnew) - Mxz * Mxy) / DET / 2
    r = np.sqrt(cx * cx + cy * cy + Mz + 2 * xnew)
    return CircleFit(cx + m[0], cy + m[1], float(r), method="pratt")


def taubin_fit(pts) -> CircleFit:
    """Taubin (1991) fit, Newton-based implementation (Chernov 2010, 'TaubinNTN')."""
    pts = _check(pts)
    if len(pts) < 3:
        return CircleFit(np.nan, np.nan, np.nan, ok=False, method="taubin")
    m = pts.mean(axis=0)
    X = pts - m
    Xi, Yi = X[:, 0], X[:, 1]
    Zi = Xi * Xi + Yi * Yi
    Mxy = np.mean(Xi * Yi); Mxx = np.mean(Xi * Xi); Myy = np.mean(Yi * Yi)
    Mxz = np.mean(Xi * Zi); Myz = np.mean(Yi * Zi); Mzz = np.mean(Zi * Zi)
    Mz = Mxx + Myy
    Cov_xy = Mxx * Myy - Mxy * Mxy
    A3 = 4 * Mz
    A2 = -3 * Mz * Mz - Mzz
    A1 = Mzz * Mz + 4 * Cov_xy * Mz - Mxz * Mxz - Myz * Myz - Mz * Mz * Mz
    A0 = Mxz * Mxz * Myy + Myz * Myz * Mxx - Mzz * Cov_xy - 2 * Mxz * Myz * Mxy + Mz * Mz * Cov_xy
    A22, A33 = A2 + A2, A3 + A3 + A3
    xnew, ynew = 0.0, 1e20
    for _ in range(99):
        yold = ynew
        ynew = A0 + xnew * (A1 + xnew * (A2 + xnew * A3))
        if abs(ynew) > abs(yold):
            xnew = 0.0
            break
        Dy = A1 + xnew * (A22 + xnew * A33)
        xold = xnew
        xnew = xold - ynew / Dy
        if abs((xnew - xold) / (xnew if xnew != 0 else 1)) < 1e-12:
            break
        if xnew < 0:
            xnew = 0.0
            break
    DET = xnew * xnew - xnew * Mz + Cov_xy
    if abs(DET) < 1e-300:
        return CircleFit(np.nan, np.nan, np.nan, ok=False, method="taubin")
    cx = (Mxz * (Myy - xnew) - Myz * Mxy) / DET / 2
    cy = (Myz * (Mxx - xnew) - Mxz * Mxy) / DET / 2
    r = np.sqrt(cx * cx + cy * cy + Mz)
    return CircleFit(cx + m[0], cy + m[1], float(r), method="taubin")


def geometric_fit(pts, init: CircleFit | None = None, loss: str = "linear") -> CircleFit:
    """Orthogonal-distance fit (minimize sum (|p-c|-r)^2) with scipy least_squares.
    loss='soft_l1' or 'huber' gives a robust M-estimator."""
    pts = _check(pts)
    if len(pts) < 3 or least_squares is None:
        return CircleFit(np.nan, np.nan, np.nan, ok=False, method="geometric")
    init = init or kasa_fit(pts)
    if not init.ok:
        init = CircleFit(*pts.mean(0), float(np.std(pts)), method="init")
    f = lambda q: np.hypot(pts[:, 0] - q[0], pts[:, 1] - q[1]) - q[2]
    res = least_squares(f, [init.cx, init.cy, init.r], loss=loss, f_scale=1.0)
    return CircleFit(*res.x, ok=bool(res.success), method=f"geometric[{loss}]")


def ransac_kasa(pts, thresh: float = 2.0, iters: int = 300, seed: int = 0) -> CircleFit:
    """Improvement (NOT in source/paper): RANSAC on 3-point circles + Kasa refit on inliers."""
    pts = _check(pts)
    n = len(pts)
    if n < 3:
        return CircleFit(np.nan, np.nan, np.nan, ok=False, method="ransac")
    rng = np.random.default_rng(seed)
    best_inl = None
    for _ in range(iters):
        s = pts[rng.choice(n, 3, replace=False)]
        c = kasa_fit(s)
        if not c.ok:
            continue
        inl = np.abs(c.residuals(pts)) < thresh
        if best_inl is None or inl.sum() > best_inl.sum():
            best_inl = inl
    if best_inl is None or best_inl.sum() < 3:
        return CircleFit(np.nan, np.nan, np.nan, ok=False, method="ransac")
    c = kasa_fit(pts[best_inl])
    c.method = "ransac+kasa"
    return c


FITTERS = {
    "kasa": kasa_fit,
    "pratt": pratt_fit,
    "taubin": taubin_fit,
    "geometric": geometric_fit,
    "geometric_huber": lambda p: geometric_fit(p, loss="huber"),
    "ransac_kasa": ransac_kasa,
}
