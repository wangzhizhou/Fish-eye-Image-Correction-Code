"""Experiment E: real fisheye images from the repository + a SYNTHETIC cube-room
checkerboard, corrected with the Python re-implementations, and the gold-standard check
against resources/corrected0.jpg (produced by the original C++ program).

    python experiments/experiment_real.py
"""
from __future__ import annotations

import numpy as np
import cv2

from _common import plt, savefig, savejson, repo_path, FIG
from lccp import PI, get_phi_closed
from vals import vals_source
from correction import (correction3, correction4, correction5, c2_latlon, maps_from_latlon,
                        remap_source, remap_bilinear)
from coordinate_transform import fisheye_to_xyz


def gold_check():
    print("[E1] gold standard: resources/corrected0.jpg vs Python Correction3")
    img = cv2.imread(repo_path("ImagesForTest", "1", "1.JPG"))
    gold = cv2.imread(repo_path("resources", "corrected0.jpg"))
    if img is None or gold is None:
        print("   images missing -> skipped"); return {"skipped": True}
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    vr = vals_source(gray, 23, 5)            # valid_params.txt: Fisheye\1: N=5, t=23, 24
    res = {"vals_t23_N5": dict(center=vr.center, radius=vr.radius)}

    def mae(o, rows=None):
        d = np.abs(o.astype(int) - gold.astype(int))
        return float(d.mean() if rows is None else d[rows].mean())

    eq = slice(950, 970)
    cands = {"vals_port_params": (*vr.center, vr.radius), "best_grid_search": (946, 634, 623),
             "cx-1": (945, 634, 623), "R-1": (946, 634, 622), "vals_t40": None}
    v40 = vals_source(gray, 40, 5)
    cands["vals_t40"] = (*v40.center, v40.radius)
    for name, (cx, cy, R) in cands.items():
        src, _ = correction3(img, cx, cy, R, source_like=True)
        H = W = 1920
        phi, lam = get_phi_closed(np.arange(H) * 4.0 / H), get_phi_closed(np.arange(W) * 4.0 / W)
        mu, mv = maps_from_latlon(phi, lam, cx, cy, R, fast=False)
        exact, _ = remap_source(img, mu, mv)
        res[name] = dict(params=(cx, cy, R), MAE_source_like=mae(src), MAE_exact_mapping=mae(exact),
                         MAE_rows950_970_source_like=mae(src, eq), MAE_rows950_970_exact=mae(exact, eq))
        if name == "best_grid_search":
            d = np.abs(src.astype(int) - gold.astype(int)).max(2)
            fig, axs = plt.subplots(1, 3, figsize=(15, 5))
            axs[0].imshow(cv2.cvtColor(gold, cv2.COLOR_BGR2RGB)); axs[0].set_title("resources/corrected0.jpg (original C++)")
            axs[1].imshow(cv2.cvtColor(src, cv2.COLOR_BGR2RGB)); axs[1].set_title("Python correction3 (source-like), (946,634,623)")
            axs[2].imshow(d, cmap="Blues", vmax=60); axs[2].set_title("|difference| (max over channels)")
            for a in axs: a.axis("off")
            savefig(fig, "real_E1_gold_comparison.png")
    res["jpeg_q95_self_MAE_reference"] = float(np.abs(cv2.imdecode(cv2.imencode(".jpg", src, [cv2.IMWRITE_JPEG_QUALITY, 95])[1], 1).astype(int) - src.astype(int)).mean())
    return res


def real_gallery():
    print("[E2] real images: Correction2/3/4/5 + improved")
    img = cv2.imread(repo_path("ImagesForTest", "1", "1.JPG"))
    if img is None:
        return {"skipped": True}
    cx, cy, R = 946, 634, 623          # circle proven by byte-identical C++ reproduction (REPORT §10.6)
    outs = {}
    H = W = 1024
    phi, lam = c2_latlon(H, W)
    mu, mv = maps_from_latlon(phi, lam, cx, cy, R, fast=True)
    outs["Correction2 equirect (nearest)"] = remap_source(img, mu, mv)[0]
    outs["Correction3 (source-like)"] = correction3(img, cx, cy, R)[0]
    outs["Correction4 w=pi/2 (source-like, 512)"] = correction4(img, cx, cy, R, PI / 2)[0]
    outs["Correction4 w=pi/4 (source-like, 512)"] = correction4(img, cx, cy, R, PI / 4)[0]
    c5, hit, oob = correction5(img, cx, cy, R, PI / 2)
    outs[f"Correction5 forward w=pi/2 (holes {100 * (1 - hit.mean()):.1f}%)"] = c5
    outs["improved: closed-form LCCP w=3pi/8 + bilinear"] = correction4(img, cx, cy, R, 3 * PI / 8, source_like=False, size=1024)[0]
    fig, axs = plt.subplots(2, 3, figsize=(15, 10))
    for ax, (k, o) in zip(axs.ravel(), outs.items()):
        ax.imshow(cv2.cvtColor(o, cv2.COLOR_BGR2RGB)); ax.set_title(k, fontsize=9); ax.axis("off")
    fig.suptitle("ImagesForTest/1/1.JPG, centre (946,634), R=623, EQUIDISTANCE, FOV=180")
    savefig(fig, "real_E2_methods_gallery.png")
    # crop around the equator to show the getPhi artefact (Correction3)
    c3s = outs["Correction3 (source-like)"]
    c3e = correction3(img, cx, cy, R, source_like=False)[0]
    fig, axs = plt.subplots(1, 2, figsize=(12, 4))
    axs[0].imshow(cv2.cvtColor(c3s[900:1020, 800:1120], cv2.COLOR_BGR2RGB)); axs[0].set_title("Correction3 source-like: rows 900-1020, cols 800-1120")
    axs[1].imshow(cv2.cvtColor(c3e[900:1020, 800:1120], cv2.COLOR_BGR2RGB)); axs[1].set_title("closed-form getPhi + bilinear (same crop)")
    for a in axs: a.axis("off")
    savefig(fig, "real_E2_equator_crop.png")
    return {"C5_hole_fraction": float(1 - hit.mean()), "C5_oob_reads": oob}


def synthetic_cube(size=900, R=420):
    """SYNTHETIC: equidistance 180deg fisheye image of a camera inside a checkered cube."""
    c = size / 2
    vv, uu = np.mgrid[0:size, 0:size].astype(float)
    inside = np.hypot(uu - c, vv - c) <= R
    x, y, z = fisheye_to_xyz(uu, vv, c, c, R)
    m = np.maximum(np.maximum(np.abs(x), np.abs(y)), np.abs(z)) + 1e-12
    X, Y, Z = x / m, y / m, z / m
    face = np.argmax(np.stack([np.abs(X), np.abs(Y), np.abs(Z)]), 0)
    a = np.where(face == 0, Y, X); b = np.where(face == 2, Y, Z)
    chk = ((np.floor((a + 1) * 4) + np.floor((b + 1) * 4)) % 2)
    line = (np.abs(((a + 1) * 4) % 1 - 0.5) > 0.47) | (np.abs(((b + 1) * 4) % 1 - 0.5) > 0.47)
    base = np.stack([60 + 150 * chk, 80 + 120 * (face == 1), 90 + 100 * (face == 2)], -1)
    base[line] = 20
    img = np.where(inside[..., None], base, 0).astype(np.uint8)
    return img, c, c, R


def synthetic_gallery():
    print("[E3] SYNTHETIC cube-room checkerboard")
    img, cx, cy, R = synthetic_cube()
    outs = {"SYNTHETIC input (equidistance 180deg)": img}
    phi, lam = c2_latlon(900, 900)
    mu, mv = maps_from_latlon(phi, lam, cx, cy, R, fast=False)
    outs["Correction2 equirect"] = remap_bilinear(img, mu, mv)
    outs["Correction3 (source-like)"] = correction3(img, cx, cy, R)[0]
    outs["Correction4 w=pi/2"] = correction4(img, cx, cy, R, PI / 2)[0]
    outs["Correction4 w=pi/4"] = correction4(img, cx, cy, R, PI / 4)[0]
    outs["Correction5 forward w=pi/2"] = correction5(img, cx, cy, R, PI / 2)[0]
    fig, axs = plt.subplots(2, 3, figsize=(15, 10))
    for ax, (k, o) in zip(axs.ravel(), outs.items()):
        ax.imshow(cv2.cvtColor(o, cv2.COLOR_BGR2RGB)); ax.set_title(k, fontsize=9); ax.axis("off")
    fig.suptitle("SYNTHETIC DATA - rendered, not photographed")
    savefig(fig, "synthetic_E3_cube_gallery.png")
    cv2.imwrite(f"{FIG}/synthetic_cube_input.png", img)
    return {"synthetic": True}


if __name__ == "__main__":
    out = {"E1_gold": gold_check(), "E2_real": real_gallery(), "E3_synthetic": synthetic_gallery()}
    savejson(out, "real_E.json")
    import json
    print(json.dumps(out, indent=1, default=float))
