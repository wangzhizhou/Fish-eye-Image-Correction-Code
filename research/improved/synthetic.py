"""SYNTHETIC ground truth: a camera inside a checkered cube room. The scene is a function of the
viewing ray only, so both the fisheye input AND the ideal output of any projection can be rendered
exactly (with supersampling = area-averaged pixels). Used to measure resampling error.
"""
from __future__ import annotations

import numpy as np

from geometry import Camera


def scene(d):
    """d: (..., 3) unit rays in the camera frame (z forward, y up) -> RGB float in [0, 255]"""
    m = np.max(np.abs(d), -1, keepdims=True) + 1e-12
    X, Y, Z = np.moveaxis(d / m, -1, 0)
    face = np.argmax(np.stack([np.abs(X), np.abs(Y), np.abs(Z)]), 0)
    a = np.where(face == 0, Y, X)
    b = np.where(face == 2, Y, Z)
    chk = (np.floor((a + 1) * 6) + np.floor((b + 1) * 6)) % 2
    fa, fb = ((a + 1) * 6) % 1, ((b + 1) * 6) % 1
    line = (np.abs(fa - 0.5) > 0.46) | (np.abs(fb - 0.5) > 0.46)          # thin grid lines
    rgb = np.stack([50 + 160 * chk, 70 + 110 * (face == 1) + 30 * chk, 80 + 100 * (face == 2)], -1).astype(float)
    rgb[line] = 15.0
    return rgb


def _ss_offsets(ss):
    return (np.arange(ss) + 0.5) / ss - 0.5


def render_fisheye(cam: Camera, H: int, W: int, ss: int = 3, chunk: int = 64):
    """area-averaged fisheye image (pixel (u, v) covers [u-0.5, u+0.5] x [v-0.5, v+0.5])"""
    out = np.zeros((H, W, 3))
    o = _ss_offsets(ss)
    for v0 in range(0, H, chunk):
        vv, uu = np.mgrid[v0:min(H, v0 + chunk), 0:W].astype(float)
        acc = np.zeros(vv.shape + (3,))
        for dv in o:
            for du in o:
                d, ok = cam.pixels_to_rays(uu + du, vv + dv)
                acc += np.where(ok[..., None], scene(d), 0.0)
        out[v0:v0 + chunk] = acc / ss ** 2
    return np.clip(np.rint(out), 0, 255).astype(np.uint8)


def render_output(ray_fn, H: int, W: int, ss: int = 3, chunk: int = 64):
    """ideal output image. ray_fn(col, row) -> (rays (...,3), valid (...)) for continuous pixel coords.
    Returns (image float, valid mask: all sub-samples valid)."""
    out = np.zeros((H, W, 3)); val = np.ones((H, W), bool)
    o = _ss_offsets(ss)
    for r0 in range(0, H, chunk):
        jj, ii = np.mgrid[r0:min(H, r0 + chunk), 0:W].astype(float)
        acc = np.zeros(jj.shape + (3,)); vok = np.ones(jj.shape, bool)
        for dj in o:
            for di in o:
                d, ok = ray_fn(ii + di, jj + dj)
                acc += scene(d); vok &= ok
        out[r0:r0 + chunk] = acc / ss ** 2
        val[r0:r0 + chunk] = vok
    return out, val


def err_stats(img, gt, mask):
    d = np.abs(img.astype(float) - gt)[mask]
    mse = float(np.mean(d ** 2))
    return dict(MAE=float(d.mean()), PSNR=float(10 * np.log10(255 ** 2 / max(mse, 1e-12))), n=int(mask.sum()))
