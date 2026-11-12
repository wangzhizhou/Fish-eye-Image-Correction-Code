"""Coordinate chain shared by latitudeCorrection2/3/4/5 (corrector.cpp).

Frames (kept strictly separate):
  * fisheye pixel      (u, v)          origin top-left, v downward
  * fisheye centred    (x_c, y_c)      x_c = u - cx, y_c = -(v - cy)  (y up)   [corrector.cpp L1149-1150]
  * fisheye polar      (p, alpha)      p = |(x_c,y_c)|, alpha = atan2(y_c, x_c)
  * camera sphere      (Theta, alpha)  Theta = angle from optical axis (+z)
  * unit vector        (x, y, z)       x = sin T cos a, y = sin T sin a, z = cos T   [L1163-1165]
  * lat/long (source)  (phi, lam)      phi = acos(y) in [0,pi]   (colatitude from +y)
                                       lam = atan2(z, -x) in [0,pi] for z >= 0     [L1168-1169]
    inverse:  x = -sin(phi) cos(lam), y = cos(phi), z = sin(phi) sin(lam)          [L887-889]
  (paper Eq. 12 states exactly the same relation.)

`fast_atan2_deg` reproduces cv::fastAtan2 (what cvFastArctan calls), including the
float32 argument conversion. It is used to quantify the error the source incurs.
"""
from __future__ import annotations

import numpy as np

from fisheye_models import focal_length, theta_to_p, p_to_theta

# OpenCV  modules/core/src/mathfuncs_core.simd.hpp  (atan_f32)
_DEG = np.float32(180 / np.pi)
_P1 = np.float32(0.9997878412794807) * _DEG
_P3 = np.float32(-0.3258083974640975) * _DEG
_P5 = np.float32(0.1555786518463281) * _DEG
_P7 = np.float32(-0.04432655554792128) * _DEG
_EPS = np.float32(np.finfo(np.float64).eps)


def fast_atan2_deg(y, x):
    """Emulation of cv::fastAtan2(float y, float x) -> degrees in [0, 360)."""
    y = np.asarray(y, dtype=np.float32)
    x = np.asarray(x, dtype=np.float32)
    ax, ay = np.abs(x), np.abs(y)
    with np.errstate(divide="ignore", invalid="ignore"):
        c1 = ay / (ax + _EPS)
        c2 = ax / (ay + _EPS)
    poly = lambda c: (((_P7 * c * c + _P5) * c * c + _P3) * c * c + _P1) * c
    with np.errstate(over="ignore", invalid="ignore"):
        a = np.where(ax >= ay, poly(c1), np.float32(90) - poly(c2)).astype(np.float32)
    a = np.where(x < 0, np.float32(180) - a, a)
    a = np.where(y < 0, np.float32(360) - a, a)
    return a.astype(np.float32)


def atan2_0_2pi(y, x, fast=False):
    """Angle in [0, 2pi). fast=True reproduces cvFastArctan(y,x)*PI/180 (float result)."""
    if fast:
        return fast_atan2_deg(y, x).astype(np.float64) * np.pi / 180
    return np.mod(np.arctan2(y, x), 2 * np.pi)


# ---------------------------------------------------------------------------
def pixel_to_centered(u, v, cx, cy):
    return np.asarray(u, float) - cx, -(np.asarray(v, float) - cy)


def centered_to_pixel(xc, yc, cx, cy):
    return np.asarray(xc, float) + cx, -np.asarray(yc, float) + cy


def latlon_to_xyz(phi, lam):
    phi, lam = np.asarray(phi, float), np.asarray(lam, float)
    return -np.sin(phi) * np.cos(lam), np.cos(phi), np.sin(phi) * np.sin(lam)


def xyz_to_latlon(x, y, z, fast=False):
    phi = np.arccos(np.clip(y, -1.0, 1.0))
    lam = atan2_0_2pi(z, -np.asarray(x, float), fast=fast)
    return phi, lam


def xyz_to_fisheye(x, y, z, cx, cy, R, fov=np.pi, model="EQUIDISTANCE", fast=False):
    """Sphere -> fisheye pixel (continuous). Theta = acos(z) (clamped)."""
    T = np.arccos(np.clip(z, -1.0, 1.0))
    a = atan2_0_2pi(y, x, fast=fast)
    f = focal_length(model, R, fov)
    p = theta_to_p(model, T, f)
    return centered_to_pixel(p * np.cos(a), p * np.sin(a), cx, cy)


def fisheye_to_xyz(u, v, cx, cy, R, fov=np.pi, model="EQUIDISTANCE", fast=False):
    xc, yc = pixel_to_centered(u, v, cx, cy)
    a = atan2_0_2pi(yc, xc, fast=fast)
    p = np.hypot(xc, yc)
    T = p_to_theta(model, p, focal_length(model, R, fov))
    return np.sin(T) * np.cos(a), np.sin(T) * np.sin(a), np.cos(T)


def latlon_to_fisheye(phi, lam, cx, cy, R, fov=np.pi, model="EQUIDISTANCE", fast=False):
    return xyz_to_fisheye(*latlon_to_xyz(phi, lam), cx, cy, R, fov, model, fast)


def fisheye_to_latlon(u, v, cx, cy, R, fov=np.pi, model="EQUIDISTANCE", fast=False):
    return xyz_to_latlon(*fisheye_to_xyz(u, v, cx, cy, R, fov, model, fast), fast=fast)
