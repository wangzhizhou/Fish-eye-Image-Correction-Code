"""Fisheye lens projection models used in the source (globalInclude.h `camMode`).

  theta : angle between incoming ray and optical axis, [0, FOV/2]
  p     : radial distance on the image plane (pixels)
  f     : focal length in pixels
  R     : radius of the effective fisheye circle (pixels)
  FOV   : full field of view alpha (radians), source restricts 0 < FOV <= pi

Model           forward p(theta)       inverse theta(p)        f from p(FOV/2)=R
STEREOGRAPHIC   2 f tan(theta/2)       2 atan(p/(2f))          R / (2 tan(FOV/4))
EQUIDISTANCE    f theta                p / f                   R / (FOV/2)
EQUISOLID       2 f sin(theta/2)       2 asin(p/(2f))          R / (2 sin(FOV/4))
ORTHOGONAL      f sin(theta)           asin(p/f)               R / sin(FOV/2)

The `foval` formulas are copied from corrector.cpp L468-483 / L677-692 /
L942-957 and findCircleParameter.cpp L171-186 / L285-299; they all enforce
p(FOV/2) = R (verified in tests/test_projection.py).
"""
from __future__ import annotations

import numpy as np

STEREOGRAPHIC, EQUIDISTANCE, EQUISOLID, ORTHOGONAL = "STEREOGRAPHIC", "EQUIDISTANCE", "EQUISOLID", "ORTHOGONAL"
MODELS = (STEREOGRAPHIC, EQUIDISTANCE, EQUISOLID, ORTHOGONAL)


def _check_fov(fov):
    if not (0 < fov <= np.pi):
        raise ValueError("FOV must be in (0, pi] (same check as the source)")


def focal_length(model: str, R: float, fov: float) -> float:
    """Source formula for `foval`."""
    _check_fov(fov)
    if R <= 0:
        raise ValueError("R must be > 0")
    if model == STEREOGRAPHIC:
        return R / (2 * np.tan(fov / 4))
    if model == EQUIDISTANCE:
        return R / (fov / 2)
    if model == EQUISOLID:
        return R / (2 * np.sin(fov / 4))
    if model == ORTHOGONAL:
        return R / np.sin(fov / 2)
    raise ValueError(model)


def theta_to_p(model: str, theta, f: float):
    theta = np.asarray(theta, dtype=float)
    if model == STEREOGRAPHIC:
        return 2 * f * np.tan(theta / 2)
    if model == EQUIDISTANCE:
        return f * theta
    if model == EQUISOLID:
        return 2 * f * np.sin(theta / 2)
    if model == ORTHOGONAL:
        return f * np.sin(theta)
    raise ValueError(model)


def p_to_theta(model: str, p, f: float):
    """Inverse model, with clamping of asin arguments (numerical protection)."""
    p = np.asarray(p, dtype=float)
    if np.any(p < 0):
        raise ValueError("p must be >= 0")
    if model == STEREOGRAPHIC:
        return 2 * np.arctan(p / (2 * f))
    if model == EQUIDISTANCE:
        return p / f
    if model == EQUISOLID:
        return 2 * np.arcsin(np.clip(p / (2 * f), -1.0, 1.0))
    if model == ORTHOGONAL:
        return np.arcsin(np.clip(p / f, -1.0, 1.0))
    raise ValueError(model)


def dp_dtheta(model: str, theta, f: float):
    """Radial magnification; ratio dp/dtheta at edge vs centre measures edge compression."""
    theta = np.asarray(theta, dtype=float)
    if model == STEREOGRAPHIC:
        return f / np.cos(theta / 2) ** 2
    if model == EQUIDISTANCE:
        return f * np.ones_like(theta)
    if model == EQUISOLID:
        return f * np.cos(theta / 2)
    if model == ORTHOGONAL:
        return f * np.cos(theta)
    raise ValueError(model)


def max_theta(model: str) -> float:
    """Largest half-angle for which the model is monotone/finite."""
    return {STEREOGRAPHIC: np.pi, EQUIDISTANCE: np.inf, EQUISOLID: np.pi, ORTHOGONAL: np.pi / 2}[model]
