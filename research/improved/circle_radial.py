"""T5 (improvement proposal): threshold-free refinement of the fisheye circle.

Start from any coarse circle (e.g. VALS with any threshold). For n angles, sample the radial
intensity profile I(r) on [0.6 R, 1.3 R] (bilinear, averaged over a small tangential window),
smooth it and take the edge as the position of the strongest outward DROP dI/dr (sub-pixel by
a parabola through the extremum). A gradual vignetting fall-off has a much smaller slope than
the cut-off of the image circle, so no grey-level threshold is needed. Angles whose profile
leaves the image (clipped circle) or whose drop is weak are rejected; the circle is fitted with
a geometric Huber fit and residual outliers (> 3 MAD) are removed; the whole procedure is
iterated from the new estimate.
"""
from __future__ import annotations

import math
import os
import sys
from dataclasses import dataclass, field

import cv2
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from kasa import geometric_fit  # noqa: E402


@dataclass
class RadialResult:
    ok: bool
    cx: float = float("nan")
    cy: float = float("nan")
    r: float = float("nan")
    n_used: int = 0
    n_angles: int = 0
    rms_residual: float = float("nan")
    history: list = field(default_factory=list)

    @property
    def reliable(self) -> bool:
        """enough rays agree with the fitted circle (>= 30 % of the angles, RMS <= 1 % of r)"""
        return bool(self.ok and self.n_used >= 0.3 * self.n_angles and self.rms_residual <= 0.01 * self.r)


def refine_circle(gray: np.ndarray, cx: float, cy: float, r: float, n_angles: int = 720,
                  r_lo: float = 0.6, r_hi: float = 1.3, step: float = 0.25, sigma: float = 2.0,
                  tang: int = 5, iters: int = 3, first_lo: float = 0.4, first_hi: float = 1.8) -> RadialResult:
    g = gray.astype(np.float32)
    H, W = g.shape
    res = RadialResult(False, n_angles=n_angles)
    for it in range(iters):
        lo, hi = (first_lo, first_hi) if it == 0 else (r_lo, r_hi)   # wide first pass: coarse r may be far off
        radii = np.arange(lo * r, hi * r, step, dtype=np.float64)
        ang = (np.arange(n_angles) + 0.5) * 2 * math.pi / n_angles
        # tangential window of +-0.5 * (2pi/n_angles) split in `tang` sub-rays
        dt = (np.arange(tang) - (tang - 1) / 2) / tang * (2 * math.pi / n_angles)
        A = ang[:, None, None] + dt[None, :, None]
        X = (cx + radii[None, None, :] * np.cos(A)).astype(np.float32)
        Y = (cy + radii[None, None, :] * np.sin(A)).astype(np.float32)
        inside = (X >= 0) & (X <= W - 1) & (Y >= 0) & (Y <= H - 1)
        prof = cv2.remap(g, X.reshape(-1, radii.size), Y.reshape(-1, radii.size), cv2.INTER_LINEAR,
                         borderMode=cv2.BORDER_CONSTANT, borderValue=-1).reshape(X.shape)
        prof = prof.mean(1)                                    # (n_angles, n_r)
        valid_ray = inside.all(1)                              # (n_angles, n_r)
        # smooth along r and differentiate (units: grey level per pixel)
        k = max(1, int(round(3 * sigma / step)))
        t = np.arange(-k, k + 1) * step
        gk = np.exp(-t ** 2 / (2 * sigma ** 2)); gk /= gk.sum()
        sm = np.apply_along_axis(lambda p: np.convolve(p, gk, mode="same"), 1, prof)
        d = np.gradient(sm, step, axis=1)
        d[:, :k + 1] = 0; d[:, -k - 1:] = 0
        # background level and noise, measured on the smoothed profiles themselves (no user threshold):
        # the outer 20 % of every in-image ray, median over rays (robust to rays that end inside the circle)
        if it == 0:
            lv, sd = [], []
            for a_ in range(n_angles):
                vi = np.nonzero(valid_ray[a_, k + 1:radii.size - k - 1])[0] + k + 1
                if vi.size > 40:
                    seg = sm[a_, vi[-max(8, vi.size // 5):]]
                    lv.append(np.median(seg)); sd.append(np.std(seg))
            bg, nz = float(np.median(lv)), float(np.median(sd))
            bg_thr = bg + max(6 * nz, 2.0)
        # outermost departure from the background level (scene edges inside the circle can be
        # stronger than the rim, so "strongest drop on the ray" is not used on its own)
        bright = (sm > bg_thr) & valid_ray
        has = bright.any(1)
        b = np.where(has, radii.size - 1 - np.argmax(bright[:, ::-1], axis=1), 0)
        w = int(round(3 * sigma / step))
        dd = d.copy()
        idx = np.arange(radii.size)[None, :]
        dd[(idx < (b - w)[:, None]) | (idx > (b + w)[:, None])] = np.inf
        i0 = np.argmin(dd, axis=1)                             # strongest drop next to that point
        i0 = np.where(has, i0, 0)
        strength = np.where(has & (b < radii.size - 1 - k), -d[np.arange(n_angles), i0], 0.0)
        # sub-pixel parabola
        im, ip = np.clip(i0 - 1, 0, radii.size - 1), np.clip(i0 + 1, 0, radii.size - 1)
        ym, y0, yp = d[np.arange(n_angles), im], d[np.arange(n_angles), i0], d[np.arange(n_angles), ip]
        den = ym - 2 * y0 + yp
        with np.errstate(divide="ignore", invalid="ignore"):
            off = np.where(np.abs(den) > 1e-9, 0.5 * (ym - yp) / den, 0.0)
        re = radii[i0] + np.clip(off, -1, 1) * step
        # reject: the profile around the edge must be fully inside the image; weak drops
        margin = int(round(4 * sigma / step))
        ok_in = np.array([valid_ray[a, max(0, i - margin):i + margin + 1].all() for a, i in enumerate(i0)])
        ok = ok_in & (strength > 0.25 * np.median(strength[ok_in])) if ok_in.any() else ok_in
        if ok.sum() < 12:
            return res
        P = np.c_[cx + re[ok] * np.cos(ang[ok]), cy + re[ok] * np.sin(ang[ok])]
        fit = geometric_fit(P, loss="huber")
        resid = np.abs(np.hypot(P[:, 0] - fit.cx, P[:, 1] - fit.cy) - fit.r)
        mad = np.median(np.abs(resid - np.median(resid))) * 1.4826 + 1e-6
        keep = resid <= np.median(resid) + 3 * mad + 0.5
        fit = geometric_fit(P[keep], loss="huber")
        resid = np.hypot(P[keep, 0] - fit.cx, P[keep, 1] - fit.cy) - fit.r
        cx, cy, r = fit.cx, fit.cy, fit.r
        res = RadialResult(True, cx, cy, r, int(keep.sum()), n_angles, float(np.sqrt(np.mean(resid ** 2))),
                           res.history + [(cx, cy, r)])
    return res


def auto_threshold(gray: np.ndarray) -> int:
    """data-driven coarse threshold: half way between the dark background (2nd percentile) and the
    Otsu level of the blurred image. Only used for the coarse start; the refinement is threshold-free."""
    b = cv2.GaussianBlur(gray, (0, 0), 2)
    otsu, _ = cv2.threshold(b, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    bg = float(np.percentile(b, 2))
    return int(max(3, round((otsu - bg) / 2)))


def detect_circle(gray: np.ndarray, threshold="auto", **kw) -> RadialResult:
    """coarse circle from the improved VALS, then threshold-free refinement."""
    from vals import vals_improved
    t = auto_threshold(gray) if threshold == "auto" else int(threshold)
    v = vals_improved(gray, t)
    if not v.ok:
        H, W = gray.shape
        return refine_circle(gray, W / 2, H / 2, min(H, W) / 2, **kw)
    return refine_circle(gray, v.center[0], v.center[1], v.radius, **kw)
