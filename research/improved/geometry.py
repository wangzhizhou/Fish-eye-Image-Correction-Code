"""Python mirror of research/improved/cpp/fisheye_improved.{hpp,cpp} (improved proposal, not the
original code). Used for ground-truth rays, distortion metrics and cross-checking the C++ maps.

Conventions as in program/corrector.cpp: colatitude phi from +y (up), longitude lam in [0, pi],
x = -sin(phi) cos(lam), y = cos(phi), z = sin(phi) sin(lam); psi = pi/2 - phi, lam' = lam - pi/2.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np

PI = np.pi
LENSES = ("STEREOGRAPHIC", "EQUIDISTANCE", "EQUISOLID", "ORTHOGONAL")


# ------------------------------------------------------------------ lens models
def focal(lens: str, r: float, fov: float) -> float:
    return {"STEREOGRAPHIC": r / (2 * np.tan(fov / 4)), "EQUIDISTANCE": r / (fov / 2),
            "EQUISOLID": r / (2 * np.sin(fov / 4)), "ORTHOGONAL": r / np.sin(fov / 2)}[lens]


def theta_to_p(lens, t, f):
    t = np.asarray(t, float)
    return {"STEREOGRAPHIC": lambda: 2 * f * np.tan(t / 2), "EQUIDISTANCE": lambda: f * t,
            "EQUISOLID": lambda: 2 * f * np.sin(t / 2), "ORTHOGONAL": lambda: f * np.sin(t)}[lens]()


def p_to_theta(lens, p, f):
    p = np.asarray(p, float)
    return {"STEREOGRAPHIC": lambda: 2 * np.arctan(p / (2 * f)), "EQUIDISTANCE": lambda: p / f,
            "EQUISOLID": lambda: 2 * np.arcsin(np.minimum(1, p / (2 * f))),
            "ORTHOGONAL": lambda: np.arcsin(np.minimum(1, p / f))}[lens]()


@dataclass(frozen=True)
class Camera:
    cx: float
    cy: float
    r: float
    lens: str = "EQUIDISTANCE"
    fov: float = PI

    @property
    def f(self):
        return focal(self.lens, self.r, self.fov)

    def rays_to_pixels(self, d):
        """unit rays (..., 3) in camera frame (z = optical axis, y up) -> (u, v, valid)"""
        x, y, z = d[..., 0], d[..., 1], d[..., 2]
        th = np.arccos(np.clip(z, -1, 1))
        a = np.arctan2(y, x)
        p = theta_to_p(self.lens, th, self.f)
        return self.cx + p * np.cos(a), self.cy - p * np.sin(a), th <= self.fov / 2 + 1e-12

    def pixels_to_rays(self, u, v):
        xc, yc = np.asarray(u, float) - self.cx, -(np.asarray(v, float) - self.cy)
        p = np.hypot(xc, yc)
        th = p_to_theta(self.lens, p, self.f)
        a = np.arctan2(yc, xc)
        d = np.stack([np.sin(th) * np.cos(a), np.sin(th) * np.sin(a), np.cos(th)], -1)
        return d, p <= self.r


# ------------------------------------------------------------------ axis maps
@dataclass(frozen=True)
class Axis:
    kind: str = "lin"          # "lin" | "lccp"
    w: float = PI / 2

    def fwd(self, a):
        a = np.asarray(a, float)
        if self.kind == "lin":
            return a
        h = np.abs(a) / 2
        return np.sign(a) * 2 * np.sin(self.w) * np.sin(h) / np.sin(self.w + h)

    def dfwd(self, a):
        """ds/da (closed form; = 1 for lin)"""
        a = np.asarray(a, float)
        if self.kind == "lin":
            return np.ones_like(a)
        h = np.abs(a) / 2
        return np.sin(self.w) ** 2 / np.sin(self.w + h) ** 2

    def inv(self, s):
        s = np.asarray(s, float)
        if self.kind == "lin":
            return s
        h = np.arctan2(np.abs(s) * np.sin(self.w), 2 * np.sin(self.w) - np.abs(s) * np.cos(self.w))
        return np.sign(s) * 2 * h

    def spec(self):
        return "lin" if self.kind == "lin" else f"lccp:{float(self.w)!r}"


@dataclass(frozen=True)
class Output:
    lon: Axis = Axis("lin")
    lat: Axis = Axis("lccp", PI / 2)
    lon_half: float = PI / 2
    lat_half: float = PI / 2
    width: int = 0
    height: int = 0

    def resolve(self, cam: Camera, clip=True, scale=1.0):
        lh = min(self.lon_half, cam.fov / 2) if clip else self.lon_half
        th = min(self.lat_half, cam.fov / 2) if clip else self.lat_half
        W = self.width or max(16, int(round(scale * cam.f * (self.lon.fwd(lh) - self.lon.fwd(-lh)))))
        H = self.height or max(16, int(round(scale * cam.f * (self.lat.fwd(th) - self.lat.fwd(-th)))))
        return replace(self, lon_half=lh, lat_half=th, width=W, height=H)

    def col_to_lon(self, i):
        s0, s1 = self.lon.fwd(-self.lon_half), self.lon.fwd(self.lon_half)
        return PI / 2 + self.lon.inv(s0 + (np.asarray(i, float) + 0.5) * (s1 - s0) / self.width)

    def row_to_lat(self, j):
        s0, s1 = self.lat.fwd(self.lat_half), self.lat.fwd(-self.lat_half)
        return self.lat.inv(s0 + (np.asarray(j, float) + 0.5) * (s1 - s0) / self.height)

    def rays(self):
        """unit rays (H, W, 3) of every output pixel centre, camera frame"""
        lam = self.col_to_lon(np.arange(self.width))
        psi = self.row_to_lat(np.arange(self.height))
        phi = PI / 2 - psi
        x = -np.sin(phi)[:, None] * np.cos(lam)[None, :]
        y = np.cos(phi)[:, None] * np.ones_like(lam)[None, :]
        z = np.sin(phi)[:, None] * np.sin(lam)[None, :]
        return np.stack([x, y, z], -1)

    def cli_args(self):
        return [f"lon={self.lon.spec()}", f"lat={self.lat.spec()}", f"w={self.width}", f"h={self.height}"]


def latlon_rays(lam, psi):
    phi = PI / 2 - np.asarray(psi, float)
    lam = np.asarray(lam, float)
    return np.stack([-np.sin(phi) * np.cos(lam), np.cos(phi) * np.ones_like(lam), np.sin(phi) * np.sin(lam)], -1)
