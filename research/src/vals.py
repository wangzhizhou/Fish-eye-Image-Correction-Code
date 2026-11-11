"""VALS - Variable Angle Line Scan (变角度线扫描法).

Faithful Python port of findCircleParameter::revisedScanLineMethod
(program/findCircleParameter.cpp L355-837) + synthetic image generator +
an improved variant (clearly separated, NOT part of the source/paper).

Source behaviour reproduced (line numbers refer to findCircleParameter.cpp):
* L369  : 2N scan directions, theta_n = pi*n/(2N), n = 0..2N-1
* n == 0: horizontal rows, top->bottom and bottom->top, per-row
          (max-min) > threshold, tangent point = first argmax in that row
          (cv::minMaxLoc semantics, L385-425)
* 0<n<N : oblique lines y = tan(theta)*(i-x) scanned from the top-left corner
          (L444-498) and y = H-1-tan(theta)*(x-i) from the bottom-right
          (L506-560). max/min are CUMULATIVE over all pixels visited so far in
          this direction (not reset per line); the point stored is the
          (first) pixel that reached the running maximum.
* n == N: vertical columns, left->right and right->left (L581-623)
* N<n<2N: L643-756 (note L703 `imgSize.width - 1 / 2` == width, integer division)
* L433/569/631/765: a pair contributes a distance only when both sides are found
* L794-811: mean of pair distances; keep pairs with distance < mean (strict)
* L815: Kasa fit (with int truncation of centre and radius)

Coordinates: pixel (x to the right, y down), integer, as in the source.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from kasa import kasa_fit_source, kasa_fit, CircleFit


# --------------------------------------------------------------------------
#  Synthetic data
# --------------------------------------------------------------------------
def synthetic_fisheye(h=600, w=800, cx=410.3, cy=297.6, r=260.0, *, inner=150.0,
                      background=8.0, noise=3.0, texture=40.0, vignette=0.0,
                      missing_sector=None, specks=0, seed=0, crop_bottom=0) -> np.ndarray:
    """Grey-level synthetic circular fisheye frame (SYNTHETIC DATA).

    inner        mean grey level inside the circle
    vignette     0..1, how much the brightness drops toward the rim (low contrast edge)
    missing_sector (a0, a1) radians: rim sector rendered dark (simulated missing edge)
    specks       number of bright outlier blobs placed outside the circle
    """
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:h, 0:w].astype(float)
    d = np.hypot(xx - cx, yy - cy)
    ang = np.arctan2(yy - cy, xx - cx)
    tex = texture * (np.sin(xx / 17.0) * np.cos(yy / 23.0) + 0.5 * np.sin((xx + yy) / 41.0))
    rho = np.clip(d / r, 0, 1)
    lum = inner * (1 - vignette * rho ** 4) + tex * (1 - vignette * rho ** 2)
    # anti-aliased rim (one pixel transition)
    alpha = np.clip(r + 0.5 - d, 0, 1)
    if missing_sector is not None:
        a0, a1 = missing_sector
        m = ((ang - a0) % (2 * np.pi)) < ((a1 - a0) % (2 * np.pi))
        alpha = np.where(m & (d > 0.8 * r), 0.0, alpha)
    img = background + alpha * (lum - background)
    img += rng.normal(0, noise, img.shape)
    for _ in range(specks):
        while True:
            px, py = rng.uniform(0, w), rng.uniform(0, h)
            if math.hypot(px - cx, py - cy) > r + 15:
                break
        img += 200 * np.exp(-((xx - px) ** 2 + (yy - py) ** 2) / (2 * 1.5 ** 2))
    if crop_bottom:
        img = img[: h - crop_bottom]
    return np.clip(np.rint(img), 0, 255).astype(np.uint8)


def synthetic_edge_points(n=200, cx=0.0, cy=0.0, r=100.0, noise=0.5, outlier_frac=0.0,
                          arc=(0, 2 * np.pi), outlier_scale=30.0, seed=0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    t = rng.uniform(arc[0], arc[1], n)
    p = np.c_[cx + r * np.cos(t), cy + r * np.sin(t)] + rng.normal(0, noise, (n, 2))
    k = int(round(outlier_frac * n))
    if k:
        idx = rng.choice(n, k, replace=False)
        p[idx] += rng.normal(0, outlier_scale, (k, 2))
    return p


# --------------------------------------------------------------------------
#  Faithful port
# --------------------------------------------------------------------------
@dataclass
class ValsResult:
    ok: bool
    center: tuple | None
    radius: int | None
    center_float: tuple | None
    points: list = field(default_factory=list)       # all tangent points (pairs)
    distances: list = field(default_factory=list)    # pair distances
    valid_points: list = field(default_factory=list)
    angles_used: list = field(default_factory=list)
    mean_distance: float = float("nan")
    message: str = ""


def _to_int(v: float) -> int:
    """C++ double -> int conversion (truncation toward zero)."""
    return int(math.trunc(v))


class _Running:
    """Cumulative max/min with cv-like strict update semantics."""

    def __init__(self):
        self.mx, self.mn, self.pt = 0, 255, (0, 0)

    def feed(self, I, pt, thr):
        if I > self.mx:
            self.mx, self.pt = I, pt
        if I < self.mn:
            self.mn = I
        return abs(self.mx - self.mn) > thr


def _scan_oblique(gray, theta, thr, which):
    """Port of the four oblique scanning loops. Returns point or None."""
    H, W = gray.shape
    t = math.tan(theta)
    run = _Running()
    if which == "A":       # 0<n<N first half  (L444-497)
        irange = range(0, W)
        jr = lambda i: range(0, i + 1)
        fy = lambda x, i: -t * (x - i)
    elif which == "B":     # 0<n<N second half (L506-559)
        irange = range(W - 1, -1, -1)
        jr = lambda i: range(i, W)
        fy = lambda x, i: H - 1 - t * (x - i)
    elif which == "C":     # N<n<2N first half (L643-694)
        irange = range(0, W)
        jr = lambda i: range(0, i + 1)
        fy = lambda x, i: H - 1 - t * (x - i)
    elif which == "D":     # N<n<2N second half (L703-755), note width - 1/2 == width
        irange = range(W - 1 // 2, -1, -1)
        jr = lambda i: range(i, W)
        fy = lambda x, i: -t * (x - i)
    else:
        raise ValueError(which)
    for i in irange:
        xs = np.fromiter(jr(i), dtype=np.int64)
        if xs.size == 0:
            continue
        ys = np.trunc(fy(xs.astype(float), i)).astype(np.int64)
        ok = (xs >= 0) & (xs < W) & (ys >= 0) & (ys < H)
        xs, ys = xs[ok], ys[ok]
        if xs.size == 0:
            continue
        vals = gray[ys, xs].astype(np.int64)
        # vectorised version of the per-pixel loop with identical semantics
        prev_mx, prev_mn = run.mx, run.mn
        cmx = np.maximum.accumulate(np.maximum(vals, prev_mx))
        cmn = np.minimum.accumulate(np.minimum(vals, prev_mn))
        hit = np.nonzero(np.abs(cmx - cmn) > thr)[0]
        if hit.size:
            k = hit[0]
            m = cmx[k]
            if m > prev_mx:
                j = int(np.nonzero(vals[: k + 1] == m)[0][0])
                run.pt = (int(xs[j]), int(ys[j]))
            return run.pt
        # no trigger: update state
        if cmx[-1] > prev_mx:
            j = int(np.nonzero(vals == cmx[-1])[0][0])
            run.pt = (int(xs[j]), int(ys[j]))
        run.mx, run.mn = int(cmx[-1]), int(cmn[-1])
    return None


def _scan_rows(gray, thr, reverse):
    H = gray.shape[0]
    rng = range(H - 1, -1, -1) if reverse else range(H)
    for i in rng:
        row = gray[i]
        if int(row.max()) - int(row.min()) > thr:
            return (int(np.argmax(row)), i)
    return None


def _scan_cols(gray, thr, reverse):
    W = gray.shape[1]
    rng = range(W - 1, -1, -1) if reverse else range(W)
    for i in rng:
        col = gray[:, i]
        if int(col.max()) - int(col.min()) > thr:
            return (i, int(np.argmax(col)))
    return None


def vals_source(gray: np.ndarray, threshold: int = 40, N: int = 5) -> ValsResult:
    """Faithful port of revisedScanLineMethod. `gray` must be uint8 single channel."""
    gray = np.asarray(gray)
    if gray.ndim == 3:
        raise ValueError("expects a single-channel grey image (source does cvtColor BGR2GRAY)")
    if gray.dtype != np.uint8:
        raise ValueError("expects uint8")
    points, distance, angles = [], [], []
    for n in range(0, 2 * N):
        theta = math.pi * n / (2 * N)
        if n == 0:
            p1, p2 = _scan_rows(gray, threshold, False), _scan_rows(gray, threshold, True)
        elif 0 < n < N:
            p1, p2 = _scan_oblique(gray, theta, threshold, "A"), _scan_oblique(gray, theta, threshold, "B")
        elif n == N:
            p1, p2 = _scan_cols(gray, threshold, False), _scan_cols(gray, threshold, True)
        else:
            p1, p2 = _scan_oblique(gray, theta, threshold, "C"), _scan_oblique(gray, theta, threshold, "D")
        if p1 is not None and p2 is not None:
            points += [p1, p2]
            distance.append(math.hypot(p1[0] - p2[0], p1[1] - p2[1]))
            angles.append(theta)
    res = ValsResult(False, None, None, None, points=points, distances=distance, angles_used=angles)
    if not distance:
        # source: mean /= distance.size() -> 0/0 = NaN, no valid point, Kasa fails
        res.message = "no complete tangent pair (source divides by zero -> NaN mean)"
        return res
    mean = sum(distance) / len(distance)
    res.mean_distance = mean
    valid = []
    for i, d in enumerate(distance):
        if d < mean:
            valid += [points[2 * i], points[2 * i + 1]]
    res.valid_points = valid
    ok, c, r, cf = kasa_fit_source(np.array(valid)) if valid else (False, None, None, None)
    if not ok:
        res.message = "Kasa failed (<=2 valid points)"
        return res
    res.ok, res.center, res.radius, res.center_float = True, c, r, cf
    return res


# --------------------------------------------------------------------------
#  Improvement (separate, NOT the source algorithm)
# --------------------------------------------------------------------------
def vals_improved(gray: np.ndarray, threshold: int = 40, N: int = 18, fitter=None) -> ValsResult:
    """Improved VALS (proposal): same tangent-line idea but
    * line positions are exact (no truncation, bilinear-free nearest sampling of
      every pixel crossed by using signed distance along the normal),
    * the tangent point is located as the extreme support point of the
      thresholded foreground in direction +-n (robust, sub-pixel by averaging the
      support set),
    * pair filtering uses a median/MAD rule instead of `< mean`,
    * small bright blobs (area < 0.5 % of the image) are discarded and tangent
      points touching the image border (clipped circle) are rejected,
    * final fit is geometric (orthogonal distance) with Huber loss.
    """
    from kasa import geometric_fit
    fitter = fitter or (lambda p: geometric_fit(p, loss="huber"))
    g = gray.astype(float)
    # foreground mask: pixel brighter than (dark background level + threshold)
    bg = np.percentile(g, 2)
    fg = g > bg + threshold
    # remove isolated specks: keep largest connected component
    import cv2
    nlab, lab, stats, _ = cv2.connectedComponentsWithStats(fg.astype(np.uint8), 8)
    if nlab <= 1:
        return ValsResult(False, None, None, None, message="empty foreground")
    areas = stats[1:, cv2.CC_STAT_AREA]
    keep_lab = 1 + np.nonzero(areas >= max(0.005 * fg.size, 0.05 * areas.max()))[0]   # drop small specks
    fg = np.isin(lab, keep_lab)
    H, W = fg.shape
    ys, xs = np.nonzero(fg)
    if xs.size == 0:
        return ValsResult(False, None, None, None, message="no foreground component large enough")
    pts, dist, angs = [], [], []
    for n in range(2 * N):
        th = math.pi * n / (2 * N)
        nx, ny = -math.sin(th), math.cos(th)   # normal of a line with inclination th
        s = xs * nx + ys * ny
        pair = []
        for sel in (s >= s.max() - 0.5, s <= s.min() + 0.5):
            px, py = xs[sel].mean(), ys[sel].mean()
            on_border = xs[sel].min() <= 0 or ys[sel].min() <= 0 or xs[sel].max() >= W - 1 or ys[sel].max() >= H - 1
            pair.append(None if on_border else (px, py))
        if None in pair:          # circle clipped by the image border in this direction
            continue
        pts += pair
        dist.append(math.hypot(pair[0][0] - pair[1][0], pair[0][1] - pair[1][1]))
        angs.append(th)
    if len(dist) < 2:
        return ValsResult(False, None, None, None, message="fewer than 2 unclipped tangent pairs")
    dist = np.array(dist)
    med = np.median(dist)
    mad = np.median(np.abs(dist - med)) + 1e-9
    keep = np.abs(dist - med) <= 3 * 1.4826 * mad + 1.0
    valid = [pts[2 * i + k] for i in np.nonzero(keep)[0] for k in (0, 1)]
    c = fitter(np.array(valid, float))
    return ValsResult(bool(c.ok), (c.cx, c.cy), c.r, (c.cx, c.cy, c.r), points=pts,
                      distances=list(dist), valid_points=valid, angles_used=angs,
                      mean_distance=float(dist.mean()))
