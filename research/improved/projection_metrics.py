"""T2/T3: distortion of separable sphere->plane maps (lon axis, lat axis), weighted by solid angle
over the visible hemisphere (lam' in [-pi/2, pi/2], psi in [-pi/2, pi/2]).

For U = f * s_u(lam'), V = f * s_v(psi) (same pixel scale f on both axes, as resolve() does),
the local stretches on the unit sphere are
    k (east-west)  = f * s_u'(lam') / cos(psi)        h (north-south) = f * s_v'(psi)
Shape distortion  D = |ln(k/h)|   (0 <=> locally conformal; k/h > 1 = horizontally stretched)
Area scale        A = k*h / f^2   (output pixels per steradian, relative to the image centre)
"""
from __future__ import annotations

import itertools

import numpy as np

from geometry import Axis, PI


def grid(n=721):
    a = (np.arange(n) + 0.5) / n * PI - PI / 2           # cell centres, avoids the exact poles
    L, P = np.meshgrid(a, a)                              # L = lam', P = psi
    wgt = np.cos(P)
    return L, P, wgt / wgt.sum()


def metrics(lon: Axis, lat: Axis, n=721):
    L, P, wgt = grid(n)
    k = lon.dfwd(L) / np.cos(P)
    h = lat.dfwd(P)
    D = np.abs(np.log(k / h))
    lnA = np.log(k * h)
    m = float((wgt * lnA).sum())
    horizon = lambda lp: float(lon.dfwd(lp) / lat.dfwd(0.0))   # k/h on the horizon (psi = 0)
    span = lambda ax: float(ax.fwd(PI / 2) - ax.fwd(-PI / 2))
    return dict(
        mean_shape_distortion=float((wgt * D).sum()),
        frac_shape_distortion_gt_25pct=float(wgt[D > np.log(1.25)].sum()),
        area_scale_log_std=float(np.sqrt((wgt * (lnA - m) ** 2).sum())),
        horizon_k_over_h_at_lam60=horizon(np.radians(60)), horizon_k_over_h_at_lam85=horizon(np.radians(85)),
        k_over_h_at_psi60_centre=float(lon.dfwd(0.0) / np.cos(np.radians(60)) / lat.dfwd(np.radians(60))),
        aspect_W_over_H=span(lon) / span(lat),
        pixels_per_f2=span(lon) * span(lat),
    )


def candidates():
    c = {"C2 equirect (lin, lin)": (Axis("lin"), Axis("lin")),
         "C3 main (lccp pi/2, lccp pi/2)": (Axis("lccp", PI / 2), Axis("lccp", PI / 2))}
    for name, w in (("pi/6", PI / 6), ("pi/4", PI / 4), ("pi/3", PI / 3), ("3pi/8", 3 * PI / 8),
                    ("pi/2", PI / 2), ("2pi/3", 2 * PI / 3)):
        c[f"C4 (lin, lccp {name})"] = (Axis("lin"), Axis("lccp", w))
    return c


def optimise(n=241, objective="mean_shape_distortion", ws=None):
    """grid search over (w_lon, w_lat) in the LCCP family (lin lon included as w_lon = None)."""
    ws = ws if ws is not None else np.round(np.arange(0.10, 2.30, 0.05), 4)
    best = None
    table = []
    for wu in [None, *ws]:
        lon = Axis("lin") if wu is None else Axis("lccp", float(wu))
        for wv in ws:
            m = metrics(lon, Axis("lccp", float(wv)), n)
            table.append((wu, float(wv), m[objective]))
            if best is None or m[objective] < best[2]:
                best = (wu, float(wv), m[objective])
    return best, table
