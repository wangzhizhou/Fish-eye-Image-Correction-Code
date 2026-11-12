"""Re-implementation of corrector::latitudeCorrection2/3/4/5 (LATITUDE_LONGTITUDE branch).

Two flavours for every method:
  source_like=True   reproduces the C++ numerics: bisection getPhi/getPhi1 with LIMIT=1e-4,
                     cvFastArctan (float32 polynomial), `cv::Point(u, v)` with double u, v
                     (= Point_<int>(int,int): implicit double->int conversion, TRUNCATION toward
                     zero -- measured with the C++ harness, see REPORT §10.6; the first version of
                     this port wrongly used cvRound), `pt.inside(imgArea)` test only (no circle
                     test), C++ int truncation in the forward method.
  source_like=False  exact closed forms + numpy atan2 (the *intended* continuous mapping).

Output-pixel -> fisheye maps are computed separably: latitude depends only on the
row j, longitude only on the column i (true for all LATITUDE_LONGTITUDE branches), so
the bisections are evaluated once per row / column.
"""
from __future__ import annotations

import math

import numpy as np

from coordinate_transform import latlon_to_fisheye, fisheye_to_latlon, atan2_0_2pi
from lccp import (PI, get_phi, get_phi_closed, SourceStatics, get_phi1_closed,
                  aux_func_source, lccp_h, aux_func_closed)


# ---------------------------------------------------------------------------
# reverse methods: output pixel grid -> (phi, lam) -> fisheye (u, v)
# ---------------------------------------------------------------------------
def c2_latlon(H, W, fov=PI):
    """latitudeCorrection2 (equirectangular, '经纬映射'): phi = off + j*fov/H, lam = off + i*fov/W."""
    off = (PI - fov) / 2
    return off + np.arange(H) * (fov / H), off + np.arange(W) * (fov / W)


def c3_latlon(H, W, source_like=True):
    """latitudeCorrection3: phi = getPhi(4j/H), lam = getPhi(4i/W)   (both Braun / w=pi/2).
    Note: longitude ignores camerFieldAngle and covers [0, pi)."""
    lj = np.arange(H) * 4.0 / H
    li = np.arange(W) * 4.0 / W
    if source_like:
        return np.array([get_phi(l) for l in lj]), np.array([get_phi(l) for l in li])
    return get_phi_closed(lj), get_phi_closed(li)


def c4_latlon(H, W, w_lat=PI / 2, w_lon=PI / 2, fov=PI, source_like=True, statics=None):
    """latitudeCorrection4: phi = getPhi1(j * 2h(w_lat)/H, w_lat), lam = off + i*fov/W.
    w_lon is computed (limi_longtitude) but NEVER used (L855, L882 commented out)."""
    off = (PI - fov) / 2
    lam = off + np.arange(W) * (fov / W)
    limi = 2 * float(aux_func_source(w_lat, 0.0))
    lj = np.arange(H) * limi / H
    if source_like:
        st = statics if statics is not None else SourceStatics()
        phi = np.array([st.get_phi1(l, w_lat) for l in lj])
    else:
        phi = get_phi1_closed(lj, w_lat)
    return phi, lam


def maps_from_latlon(phi_rows, lam_cols, cx, cy, R, fov=PI, model="EQUIDISTANCE", fast=True):
    P, L = np.meshgrid(phi_rows, lam_cols, indexing="ij")
    return latlon_to_fisheye(P, L, cx, cy, R, fov, model, fast=fast)


def remap_source(img, map_u, map_v):
    """`pt = Point(u, v); if (!pt.inside(imgArea)) continue; ret(j,i) = org(pt)`.
    cv::Point_<int> has only Point_(int, int): double arguments are converted implicitly,
    i.e. truncated toward zero (NOT cvRound). Verified against the compiled original:
    99.9995% of the 1920x1920 Correction3 samples and 100% of Correction4 samples identical
    (research/cpp_harness, metrics/cpp_harness.json)."""
    H0, W0 = img.shape[:2]
    ui = np.trunc(map_u).astype(np.int64)
    vi = np.trunc(map_v).astype(np.int64)
    inside = (ui >= 0) & (ui < W0) & (vi >= 0) & (vi < H0)
    out = np.zeros(map_u.shape + img.shape[2:], dtype=img.dtype)
    out[inside] = img[vi[inside], ui[inside]]
    return out, inside


def remap_bilinear(img, map_u, map_v, cx=None, cy=None, R=None):
    """Improved sampling (paper says bilinear interpolation; source does nearest)."""
    import cv2
    out = cv2.remap(img, map_u.astype(np.float32), map_v.astype(np.float32),
                    interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    if R is not None:
        mask = np.hypot(map_u - cx, map_v - cy) <= R + 0.5
        out[~mask] = 0
    return out


def correction3(img, cx, cy, R, model="EQUIDISTANCE", fov=PI, source_like=True):
    H = W = max(img.shape[0], img.shape[1])            # L538-539
    phi, lam = c3_latlon(H, W, source_like)
    mu, mv = maps_from_latlon(phi, lam, cx, cy, R, fov, model, fast=source_like)
    return (remap_source(img, mu, mv)[0] if source_like else remap_bilinear(img, mu, mv, cx, cy, R)), (mu, mv)


def correction4(img, cx, cy, R, w_lat=PI / 2, w_lon=PI / 2, model="EQUIDISTANCE", fov=PI,
                source_like=True, size=512, statics=None):
    H = W = size                                        # L802 hard-coded 512
    phi, lam = c4_latlon(H, W, w_lat, w_lon, fov, source_like, statics)
    mu, mv = maps_from_latlon(phi, lam, cx, cy, R, fov, model, fast=source_like)
    return (remap_source(img, mu, mv)[0] if source_like else remap_bilinear(img, mu, mv, cx, cy, R)), (mu, mv)


# ---------------------------------------------------------------------------
# forward method: fisheye pixel -> (phi, lam) -> output pixel   (latitudeCorrection5)
# ---------------------------------------------------------------------------
def c5_forward_coords(u, v, cx, cy, R, w_lat=PI / 2, fov=PI, size=512, fast=True):
    """Continuous output coordinates (before the int cast) of latitudeCorrection5.
    NOTE: Theta = p*(fov/2)/radius is hard-coded EQUIDISTANCE (L1159) regardless of camProjMode."""
    xc, yc = np.asarray(u, float) - cx, -(np.asarray(v, float) - cy)
    a = atan2_0_2pi(yc, xc, fast=fast)
    p = np.hypot(xc, yc)
    T = p * (fov / 2) / R
    x, y, z = np.sin(T) * np.cos(a), np.sin(T) * np.sin(a), np.cos(T)
    phi = np.arccos(np.clip(y, -1, 1))
    lam = atan2_0_2pi(z, -x, fast=fast)
    L = float(aux_func_source(w_lat, 0.0))
    # L1174-1181: both branches equal L - auxFunc(w, phi) (auxFunc sign included)
    mag = np.sin(w_lat) * np.sqrt(np.cos(phi) ** 2 + (1 - np.sin(phi)) ** 2) / \
        np.sin(PI - w_lat - np.arctan((1 - np.sin(phi)) / np.abs(np.cos(phi))))
    l = np.where((phi >= 0) & (phi < PI / 2), L - mag, L + mag)
    off = (PI - fov) / 2
    dx = fov / size
    return (lam - off) / dx, l * size / (2 * L)


def correction5(img, cx, cy, R, w_lat=PI / 2, fov=PI, size=512):
    """Forward splatting exactly as L1135-1192. Returns (out, hit_mask, oob_reads)
    oob_reads counts source pixels that the C++ would read OUTSIDE imgOrg (UB)."""
    cx, cy, R = int(cx), int(cy), int(R)
    H0, W0 = img.shape[:2]
    left, top = cx - R, cy - R
    jj, ii = np.mgrid[top:top + 2 * R, left:left + 2 * R]
    inside_c = (ii - cx) ** 2 + (jj - cy) ** 2 <= R * R
    ii, jj = ii[inside_c], jj[inside_c]
    oob = (ii < 0) | (ii >= W0) | (jj < 0) | (jj >= H0)
    uo, vo = c5_forward_coords(ii, jj, cx, cy, R, w_lat, fov, size, fast=True)
    ui = np.trunc(uo).astype(np.int64)
    vi = np.trunc(vo).astype(np.int64)
    ok = (ui >= 0) & (ui < size) & (vi >= 0) & (vi < size) & ~oob
    out = np.zeros((size, size) + img.shape[2:], img.dtype)
    hit = np.zeros((size, size), bool)
    out[vi[ok], ui[ok]] = img[jj[ok], ii[ok]]          # later writes win, like the C++ loop order
    hit[vi[ok], ui[ok]] = True
    return out, hit, int(oob.sum())


# ---------------------------------------------------------------------------
# analysis helpers
# ---------------------------------------------------------------------------
def jacobian_area(mu, mv):
    """|det d(u,v)/d(i,j)|: fisheye pixel area sampled per output pixel.
    < 1  -> output over-samples the source (stretching / blur), > 1 -> under-sampling (aliasing)."""
    du_dj, du_di = np.gradient(mu)
    dv_dj, dv_di = np.gradient(mv)
    return np.abs(du_di * dv_dj - du_dj * dv_di)
