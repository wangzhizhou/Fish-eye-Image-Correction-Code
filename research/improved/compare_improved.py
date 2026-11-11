"""Original program/ (compiled, via research/cpp_harness) vs the improved implementation
(research/improved). Build both first:
    bash research/cpp_harness/build.sh && bash research/improved/cpp/build.sh
    python research/improved/compare_improved.py [--quick]
Writes results/metrics/improved.json and results/figures/improved_*.png|jpg.
Everything here is a PROPOSAL evaluated against the original; program/ is not modified.
"""
from __future__ import annotations

import itertools
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "experiments"))
from _common import REPO, MET, FIG, plt, savefig, C  # noqa: E402
import cv2  # noqa: E402
from geometry import Camera, Output, Axis, latlon_rays, PI  # noqa: E402
from synthetic import render_fisheye, render_output, err_stats  # noqa: E402
import projection_metrics as pm  # noqa: E402
from circle_radial import detect_circle  # noqa: E402
from sphere_stitch import Shot, calibrate, render as render_pano, features, match_pairs  # noqa: E402
from vals import vals_source, vals_improved, synthetic_fisheye  # noqa: E402
from lccp import get_phi_closed, get_phi1_closed  # noqa: E402

QUICK = "--quick" in sys.argv
ORIG = os.path.join(HERE, "..", "cpp_harness", "build")
IMPB = os.path.join(HERE, "cpp", "build")
WORK = os.path.join(IMPB, "run")
SS = 2 if QUICK else 3
LENSES = ("EQUIDISTANCE", "EQUISOLID", "STEREOGRAPHIC", "ORTHOGONAL")


def sh(exe, *args, cwd=None, check=True, timeout=900):
    r = subprocess.run([exe, *map(str, args)], cwd=cwd or WORK, capture_output=True, text=True,
                       stdin=subprocess.DEVNULL, timeout=timeout)
    if check and r.returncode != 0:
        raise RuntimeError(f"{exe} {args}: {r.returncode}\n{r.stdout}\n{r.stderr}")
    return r


def W(n):
    return os.path.join(WORK, n)


def num(out, key):
    m = re.search(rf"{key}\s+([-0-9.eE]+)", out)
    return float(m.group(1)) if m else None


def imp_args(cam: Camera, o: Output):
    return [f"cx={float(cam.cx)!r}", f"cy={float(cam.cy)!r}", f"r={float(cam.r)!r}", f"lens={cam.lens}",
            f"fov={float(cam.fov)!r}", *o.cli_args()]


def encode(h, w):
    v, u = np.mgrid[0:h, 0:w]
    img = np.zeros((h, w, 3), np.uint8)
    img[..., 0] = u & 255; img[..., 1] = v & 255; img[..., 2] = 128 | (u >> 8) | ((v >> 8) << 3)
    return img


def decode(img):
    b, g, r = (img[..., k].astype(np.int64) for k in range(3))
    return b | ((r & 7) << 8), g | (((r >> 3) & 7) << 8), r >= 128


# ===================================================================== A. build / API (I6)
def part_build():
    def rd(p):
        p = os.path.join(IMPB, p)
        return open(p).read() if os.path.exists(p) else ""
    log5 = rd("original_vs_opencv5.log")
    return dict(
        improved_opencv4=rd("opencv_version.txt").strip(), improved_opencv4_warnings=rd("improved_cli.log").count("warning"),
        improved_opencv5=rd("opencv_version_cv5.txt").strip(), improved_opencv5_built=os.path.exists(os.path.join(IMPB, "improved_cli_cv5")),
        improved_opencv5_warnings=rd("improved_cli_cv5.log").count("warning"),
        original_vs_opencv5_files_compiling=log5.count("exit 0"),
        original_vs_opencv5_first_error=next((ln for ln in log5.splitlines() if "error" in ln), ""))


# ===================================================================== B. synthetic accuracy (I1 I2 I3 T1 BUG-08)
def c3_orig_rays(ii, jj, Wd=1920, Hd=1920):
    lam = get_phi_closed(np.clip(ii * 4.0 / Wd, 0, 3.999999))
    phi = get_phi_closed(np.clip(jj * 4.0 / Hd, 0, 3.999999))
    d = latlon_rays(lam, PI / 2 - phi)
    return d, d[..., 2] >= math.cos(math.radians(88))


def c4_orig_rays(ii, jj, w=PI / 2, fov=PI, S=512):
    h2 = 2 * 2 * math.sin(w) / (math.sin(w) + math.cos(w))
    lam = (PI - fov) / 2 + ii * fov / S
    phi = get_phi1_closed(np.clip(jj * h2 / S, 0, h2), w)
    d = latlon_rays(lam, PI / 2 - phi)
    return d, d[..., 2] >= math.cos(min(math.radians(88), fov / 2))


def imp_rays(o: Output, fov):
    def f(ii, jj):
        d = latlon_rays(o.col_to_lon(ii), o.row_to_lat(jj))
        return d, d[..., 2] >= math.cos(min(math.radians(88), fov / 2))
    return f


def part_synthetic():
    out = {}
    true = Camera(946.37, 634.62, 623.0)                       # non-integer centre on purpose (BUG-08)
    t = time.time()
    fish = render_fisheye(true, 1280, 1920, SS)
    cv2.imwrite(W("syn_fisheye.png"), fish)
    out["render_s"] = round(time.time() - t)
    cases = {}
    # Correction3 projection (Braun lon + lat) on a 1920x1920 grid
    r = sh(os.path.join(ORIG, "harness"), "c3", W("syn_fisheye.png"), 946, 634, 623, W("syn_c3_orig.png"))
    gt, val = render_output(lambda i, j: c3_orig_rays(i, j), 1920, 1920, SS)
    cases["C3 original (int circle, getPhi bisection, fastAtan, Point trunc, nearest)"] = err_stats(cv2.imread(W("syn_c3_orig.png")), gt, val)
    o3 = Output(Axis("lccp", PI / 2), Axis("lccp", PI / 2), width=1920, height=1920).resolve(true)
    for name, cam in (("C3 projection, improved, int circle (946,634,623)", Camera(946, 634, 623)),
                      ("C3 projection, improved, exact double circle", true)):
        sh(os.path.join(IMPB, "improved_cli"), "correct", f"in={W('syn_fisheye.png')}", f"out={W('syn_c3_imp.png')}", *imp_args(cam, o3))
        g2, v2 = render_output(imp_rays(o3, PI), 1920, 1920, SS)
        cases[name] = err_stats(cv2.imread(W("syn_c3_imp.png")), g2, v2)
    # equator band (rows/cols 940-980): where getPhi's spurious root acts
    band = np.zeros((1920, 1920), bool); band[940:981, :] = True; band[:, 940:981] = True
    o_img = cv2.imread(W("syn_c3_orig.png"))
    i_img = cv2.imread(W("syn_c3_imp.png"))
    out["C3_centre_cross_band_MAE"] = dict(original=err_stats(o_img, gt, val & band)["MAE"],
                                          improved_double_circle=err_stats(i_img, g2, v2 & band)["MAE"])
    # Correction4 projection (lin lon, LCCP pi/2 lat) on 512x512 and on the auto size
    sh(os.path.join(ORIG, "harness"), "c4", W("syn_fisheye.png"), 946, 634, 623, repr(PI / 2), "EQUIDISTANCE", repr(PI), W("syn_c4_orig.png"), cwd=W(""))
    gt4, v4 = render_output(lambda i, j: c4_orig_rays(i, j), 512, 512, SS)
    cases["C4 original 512x512"] = err_stats(cv2.imread(W("syn_c4_orig.png")), gt4, v4)
    o4 = Output(Axis("lin"), Axis("lccp", PI / 2), width=512, height=512).resolve(true)
    sh(os.path.join(IMPB, "improved_cli"), "correct", f"in={W('syn_fisheye.png')}", f"out={W('syn_c4_imp.png')}", *imp_args(true, o4))
    g4, vv4 = render_output(imp_rays(o4, PI), 512, 512, SS)
    cases["C4 projection, improved 512x512"] = err_stats(cv2.imread(W("syn_c4_imp.png")), g4, vv4)
    o4a = Output(Axis("lin"), Axis("lccp", PI / 2)).resolve(true)
    sh(os.path.join(IMPB, "improved_cli"), "correct", f"in={W('syn_fisheye.png')}", f"out={W('syn_c4a_imp.png')}", *imp_args(true, o4a))
    g4a, v4a = render_output(imp_rays(o4a, PI), o4a.height, o4a.width, SS)
    cases[f"C4 projection, improved auto size {o4a.width}x{o4a.height}"] = err_stats(cv2.imread(W("syn_c4a_imp.png")), g4a, v4a)
    out["cases"] = cases
    out["C4_auto_size"] = [o4a.width, o4a.height]

    # figure: crops at the image centre (getPhi cross) and an edge region
    fig, axs = plt.subplots(2, 3, figsize=(15, 9.5))
    crops = [(slice(900, 1020), slice(860, 1060)), (slice(300, 420), slice(150, 350))]
    for r_, (sy, sx) in enumerate(crops):
        for c_, (im, ttl) in enumerate(((gt, "ground truth (supersampled)"), (o_img, "original C3 (C++)"),
                                        (i_img, "improved, same projection"))):
            a = np.clip(im[sy, sx], 0, 255).astype(np.uint8)
            axs[r_, c_].imshow(cv2.cvtColor(a, cv2.COLOR_BGR2RGB), interpolation="nearest")
            axs[r_, c_].set_title(f"{ttl}\nrows {sy.start}-{sy.stop}, cols {sx.start}-{sx.stop}", fontsize=9)
            axs[r_, c_].axis("off")
    fig.suptitle("SYNTHETIC cube room, equidistant 180 deg, circle (946.37, 634.62, 623): Correction3 projection")
    savefig(fig, "improved_A_synthetic_crops.png")
    return out


# ===================================================================== C. FOV < 180 (T4, BUG-13/14)
def part_fov():
    out = {}
    fov = 0.8 * PI
    true = Camera(946.0, 634.0, 623.0, fov=fov)
    cv2.imwrite(W("enc.png"), encode(1280, 1920))
    sh(os.path.join(ORIG, "harness"), "c4", W("enc.png"), 946, 634, 623, repr(PI / 2), "EQUIDISTANCE", repr(fov), W("fov_c4_orig_enc.png"), cwd=W(""))
    u, v, wr = decode(cv2.imread(W("fov_c4_orig_enc.png")))
    outside = np.hypot(u - 946, v - 634) > 623
    out["original_C4_fov0.8pi_written_pixels_sampling_outside_circle"] = float((outside & wr).sum() / wr.sum())
    sh(os.path.join(ORIG, "harness"), "c3", W("enc.png"), 946, 634, 623, W("fov_c3_orig_enc.png"))
    out["original_C3_ignores_fov"] = "harness c3 has no fov input: latitudeCorrection3's ranges ignore camerFieldAngle (BUG-14)"
    o = Output(Axis("lin"), Axis("lccp", PI / 2)).resolve(true)
    sh(os.path.join(IMPB, "improved_cli"), "maps", f"out={W('fov_maps.bin')}", *imp_args(true, o))
    raw = np.fromfile(W("fov_maps.bin"), np.int32, 2)
    m = np.fromfile(W("fov_maps.bin"), np.float32, offset=8).reshape(2, raw[0], raw[1])
    valid = m[0] >= 0
    out["improved_fov0.8pi_size"] = [int(raw[1]), int(raw[0])]
    out["improved_valid_pixels_sampling_outside_circle"] = float((np.hypot(m[0][valid] - 946, m[1][valid] - 634) > 623 + 1e-3).mean())
    out["improved_masked_fraction"] = float(1 - valid.mean())
    return out


# ===================================================================== D. round trip (I2, BUG-04/05)
def part_roundtrip():
    out = {}
    o = Output(Axis("lin"), Axis("lccp", PI / 2))
    for lens in LENSES:
        cam = Camera(945, 634, 623, lens)
        oo = o.resolve(cam)
        sh(os.path.join(IMPB, "improved_cli"), "roundtrip", f"out={W('rt.txt')}", "step=3", *imp_args(cam, oo))
        d = dict(ln.split() for ln in open(W("rt.txt")) if ln.strip())
        out[lens] = {k: float(v) for k, v in d.items()}
    orig = json.load(open(os.path.join(MET, "cpp_harness.json")))["C4_C5"]
    out["original_cpp"] = {k: orig[k] for k in orig if k.startswith("roundtrip_cpp")}
    return out


# ===================================================================== E. timing (I1, I7, BUG-21)
def part_timing():
    img = os.path.join(REPO, "ImagesForTest", "1", "1.JPG")
    out = {}
    for exe in ("harness", "harness_O2"):
        r = sh(os.path.join(ORIG, exe), "c3", img, 946, 634, 623, W("t.png"))
        out[f"original_C3_1920x1920_{exe}_ms"] = num(r.stdout, "ms_latitudeCorrection3")
    cam = Camera(946, 634, 623)
    o3 = Output(Axis("lccp", PI / 2), Axis("lccp", PI / 2), width=1920, height=1920).resolve(cam)
    for exe, thr in (("improved_cli_g", 1), ("improved_cli", 1), ("improved_cli", 0)):
        args = ["time", f"in={img}", "reps=5", *imp_args(cam, o3)] + ([f"threads={thr}"] if thr else [])
        r = sh(os.path.join(IMPB, exe), *args)
        out[f"improved_C3proj_1920x1920_{exe}_{'1thread' if thr else 'allthreads'}_ms"] = num(r.stdout, "ms_per_call")
    return out


# ===================================================================== F. projection choice (T2/T3)
def part_projection(img_real):
    out = {}
    for k, (a, b) in pm.candidates().items():
        out[k] = pm.metrics(a, b)
    ws = np.round(np.arange(1.50, 2.20, 0.01), 4)
    best, table = pm.optimise(objective="mean_shape_distortion", ws=ws, n=241)
    wbest = best[1]
    out["optimum_lin_lon_lccp_lat"] = dict(w=wbest, w_deg=math.degrees(wbest), **pm.metrics(Axis("lin"), Axis("lccp", wbest)))
    out["optimum_note"] = "grid over w_lon in {lin} U [1.50,2.19] and w_lat in [1.50,2.19] (step 0.01); objective = solid-angle mean |ln(k/h)|"
    out["optimum_lon_axis"] = "lin" if best[0] is None else best[0]
    # Pareto curve over w for lin lon
    wsg = np.linspace(0.2, 2.3, 85)
    mm = [pm.metrics(Axis("lin"), Axis("lccp", w), n=241) for w in wsg]
    fig, axs = plt.subplots(1, 2, figsize=(13, 4.6))
    axs[0].plot(wsg, [m["mean_shape_distortion"] for m in mm], label="mean |ln(k/h)| (shape)")
    axs[0].plot(wsg, [m["area_scale_log_std"] for m in mm], label="std ln(area scale) (resolution)")
    axs[0].axvline(PI / 2, color=C[2], ls="--", lw=1); axs[0].text(PI / 2, 0.02, " pi/2 (paper)", fontsize=8)
    axs[0].axvline(wbest, color=C[3], ls="--", lw=1); axs[0].text(wbest, 0.12, f" optimum {wbest:.2f}", fontsize=8)
    axs[0].set_xlabel("w of the LCCP latitude axis (longitude linear)"); axs[0].legend(); axs[0].set_ylim(0, 1.4)
    for k, m in out.items():
        if isinstance(m, dict) and "mean_shape_distortion" in m:
            axs[1].scatter(m["area_scale_log_std"], m["mean_shape_distortion"], s=25)
            axs[1].annotate(k.split(" (")[0] if "optimum" not in k else "optimum", (m["area_scale_log_std"], m["mean_shape_distortion"]), fontsize=7)
    axs[1].set_xlabel("std ln(area scale)  (lower = more uniform resolution)"); axs[1].set_ylabel("mean |ln(k/h)|  (lower = less shape distortion)")
    fig.suptitle("Distortion of the separable sphere->plane maps over the visible hemisphere (solid-angle weighted)")
    savefig(fig, "improved_B_projection_metrics.png")
    return out


# ===================================================================== G. circle detection (T5)
def part_circle():
    out = {"synthetic": {}, "real": {}}
    CONDS = {"clean": {}, "noisy(sigma=8)": dict(noise=8), "low_contrast": dict(inner=45, background=10, vignette=0.6, texture=10),
             "missing_edge": dict(missing_sector=(np.radians(200), np.radians(260))), "outlier_specks": dict(specks=4)}
    GT = dict(cx=410.3, cy=297.6, r=260.0)
    for cname, kw in CONDS.items():
        rows = {"source_VALS_t40_N5": [], "improved_VALS_t40": [], "radial_auto": [], "radial_init_t5..80_max": []}
        for s in (0, 1, 2):
            img = synthetic_fisheye(seed=s, **GT, **kw)
            e = lambda cx, cy, r: (math.hypot(cx - GT["cx"], cy - GT["cy"]), abs(r - GT["r"]))
            v = vals_source(img, 40, 5); rows["source_VALS_t40_N5"].append(e(*v.center, v.radius) if v.ok else (np.nan, np.nan))
            v = vals_improved(img, 40); rows["improved_VALS_t40"].append(e(*v.center, v.radius) if v.ok else (np.nan, np.nan))
            r = detect_circle(img); rows["radial_auto"].append(e(r.cx, r.cy, r.r))
            ee = [e(q.cx, q.cy, q.r) for q in (detect_circle(img, t) for t in (5, 10, 20, 40, 80))]
            rows["radial_init_t5..80_max"].append(tuple(np.max(ee, 0)))
        out["synthetic"][cname] = {k: dict(centre_err_max=float(np.nanmax([x[0] for x in v])), radius_err_max=float(np.nanmax([x[1] for x in v])),
                                           failures=int(np.isnan([x[0] for x in v]).sum())) for k, v in rows.items()}
    st = json.load(open(os.path.join(MET, "vals_E3_real_stability.json")))
    centres = []
    for k in range(1, 10):
        p = os.path.join(REPO, "ImagesForTest", str(k), "1.JPG")
        if not os.path.exists(p):
            continue
        g = cv2.cvtColor(cv2.imread(p), cv2.COLOR_BGR2GRAY)
        res = [detect_circle(g, t) for t in ("auto", 10, 20, 30, 40, 60)]
        a = np.array([[q.cx, q.cy, q.r] for q in res])
        out["real"][f"set{k}"] = dict(size=list(g.shape[::-1]), circle_auto=[round(x, 2) for x in a[0]], reliable=res[0].reliable,
                                      rays_used=res[0].n_used, fit_rms_px=res[0].rms_residual,
                                      radial_range_over_thresholds=[round(float(x), 3) for x in np.ptp(a, 0)],
                                      source_VALS_range=[st[f"set{k}_source"][x] for x in ("cx_range", "cy_range", "r_range")] if f"set{k}_source" in st else None,
                                      improved_VALS_range=[round(st[f"set{k}_improved"][x], 2) for x in ("cx_range", "cy_range", "r_range")] if f"set{k}_improved" in st else None)
        if k <= 6:
            centres.append(a[0])
    c = np.array(centres)
    out["real_sets1to6_same_camera_spread"] = dict(cx_std=float(c[:, 0].std()), cy_std=float(c[:, 1].std()), r_std=float(c[:, 2].std()),
                                                   mean=[float(x) for x in c.mean(0)])
    return out


# ===================================================================== H. stitching (T6) + original pipeline
def original_pipeline(k):
    """program/main.cpp flow without GUI: VALS (Python port; valid_params threshold) -> C3 (C++) -> Stitcher (C++)"""
    thr = {1: 23, 2: 26, 3: 20, 4: 24, 5: 46, 6: 11}[k]
    imgs = [os.path.join(REPO, "ImagesForTest", str(k), f"{i}.JPG") for i in range(1, 5)]
    g = cv2.cvtColor(cv2.imread(imgs[0]), cv2.COLOR_BGR2GRAY)
    v = vals_source(g, thr, 5)
    outs = []
    for i, p in enumerate(imgs):
        sh(os.path.join(ORIG, "harness"), "c3", p, *v.center, v.radius, W(f"op{k}_{i}.jpg"))
        outs.append(W(f"op{k}_{i}.jpg"))
    r = sh(os.path.join(ORIG, "harness"), "stitch", W(f"op{k}_pano.png"), *outs, check=False)
    msg = [ln for ln in r.stdout.splitlines() if ln.strip()][-1:]
    return dict(circle=[*v.center, v.radius], threshold=thr, exit_code=r.returncode, stdout=msg,
                success=r.returncode == 0 and os.path.exists(W(f"op{k}_pano.png")) and "panorama" in " ".join(msg))


def part_stitch():
    out = {}
    sets = [1, 2, 3, 4, 5, 6] if not QUICK else [1, 3]
    thumbs = {}
    for k in sets:
        shots = []
        for i in range(1, 5):
            img = cv2.imread(os.path.join(REPO, "ImagesForTest", str(k), f"{i}.JPG"))
            r = detect_circle(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))
            shots.append(Shot(img, r.cx, r.cy, r.r))
        F = features(shots); P = match_pairs(F)
        res = {"mutual_matches": int(sum(len(m) for m in P.values()))}
        cals = {}
        for lens in LENSES:
            c = calibrate(shots, lens, feats=F, pairs=P)
            cals[lens] = c
            res[f"{lens}_fitted"] = dict(fov_deg=c["fov_deg"], within_1px=c["within_1px"], within_2px=c["within_2px"],
                                         within_4px=c["within_4px"], rms_within_2px=c["rms_within_2px"])
        c180 = calibrate(shots, "EQUIDISTANCE", refine_f=False, feats=F, pairs=P)
        cals["EQUIDISTANCE_180_fixed"] = c180
        res["EQUIDISTANCE_180_fixed (paper/code assumption)"] = dict(within_1px=c180["within_1px"], within_2px=c180["within_2px"],
                                                                     within_4px=c180["within_4px"])
        # panoramas: adjacent-pair overlap disagreement for the best fit vs the code's assumption
        for name in ("EQUISOLID", "EQUIDISTANCE", "EQUIDISTANCE_180_fixed"):
            pano, info = render_pano(shots, cals[name], width=3000 if not QUICK else 1600,
                                     lens=name.replace("_180_fixed", ""))
            adj = [m for m, pq in zip(info["overlap_mad"], info["overlap_pairs"]) if pq[1] - pq[0] == 1 or pq == [0, 3]]
            res[f"panorama_{name}"] = dict(overlap_mad_by_pair=info["overlap_mad"], overlap_pairs=info["overlap_pairs"],
                                           overlap_mad_adjacent_mean=float(np.mean(adj)) if adj else None,
                                           overlap_mad_mean=info["overlap_mad_mean"],
                                           coverage=info["coverage"], gains=info["gains"], size=info["size"])
            if name == "EQUISOLID":
                thumbs[k] = pano
                if k == 1:
                    cv2.imwrite(os.path.join(FIG, "improved_D_panorama_set1.jpg"), pano, [cv2.IMWRITE_JPEG_QUALITY, 90])
                    cv2.imwrite(W("pano_set1.png"), pano)
        res["original_pipeline_cpp"] = original_pipeline(k)
        out[f"set{k}"] = res
        print(f"   set{k}: equisolid fov {res['EQUISOLID_fitted']['fov_deg']:.2f}, 2px {res['EQUISOLID_fitted']['within_2px']}/{res['mutual_matches']}, "
              f"original stitch success={res['original_pipeline_cpp']['success']}")
    fig, axs = plt.subplots(len(thumbs), 1, figsize=(12, 3.1 * len(thumbs)))
    for ax, (k, p) in zip(np.atleast_1d(axs), thumbs.items()):
        ax.imshow(cv2.cvtColor(cv2.resize(p, (1200, 600)), cv2.COLOR_BGR2RGB)); ax.axis("off")
        ax.set_title(f"ImagesForTest/{k}: sphere stitching, fitted equisolid lens", fontsize=9)
    savefig(fig, "improved_D_panoramas.png")
    return out


# ===================================================================== I. viewer (I7, BUG-24)
def part_viewer():
    pano = W("pano_set1.png")
    if not os.path.exists(pano):
        return {"skipped": "no panorama"}
    r = sh(os.path.join(ORIG, "harness"), "viewer", pano, W("view_orig.png"))
    t_orig = num(r.stdout, "ms_updataWindow")
    r = sh(os.path.join(IMPB, "improved_cli"), "viewer", f"in={pano}", f"out={W('view_imp.png')}", "reps=10", "aH=0", "aV=1.5707963267948966")
    t_imp = num(r.stdout, "ms_per_render")
    a, b = cv2.imread(W("view_orig.png")).astype(float), cv2.imread(W("view_imp.png")).astype(float)
    fig, axs = plt.subplots(1, 2, figsize=(13, 3.6))
    for ax, im, ttl in ((axs[0], a, f"original viewer::updataWindow ({t_orig:.0f} ms)"), (axs[1], b, f"improved Viewer::render ({t_imp:.1f} ms)")):
        ax.imshow(cv2.cvtColor(im.astype(np.uint8), cv2.COLOR_BGR2RGB)); ax.set_title(ttl, fontsize=9); ax.axis("off")
    savefig(fig, "improved_E_viewer.png")
    return dict(original_updataWindow_ms=t_orig, improved_render_ms=t_imp, speedup=t_orig / t_imp,
                window_MAE_between_them=float(np.abs(a - b).mean()),
                note="same geometry (poles on +-z, lon = atan2(y,x), V*H rotation, d=300); improved = precomputed rays + bilinear")


# ===================================================================== J. defect checks on the improved code
def part_defects():
    out = {}
    cv2.imwrite(W("enc400.png"), encode(400, 400))
    side = W("cwd_imp"); shutil.rmtree(side, ignore_errors=True); os.makedirs(side)
    r = sh(os.path.join(IMPB, "improved_cli_asan"), "correct", f"in={W('enc400.png')}", f"out={os.path.join(side, 'o.png')}",
           "cx=200", "cy=200", "r=300", cwd=side, check=False)
    out["clipped_circle_asan"] = dict(exit=r.returncode, asan_error="AddressSanitizer" in r.stderr)
    out["files_written_in_cwd"] = sorted(os.listdir(side))
    r = sh(os.path.join(IMPB, "improved_cli"), "statics", check=False)
    out["w_change_in_one_process"] = dict(exit=r.returncode, out=r.stdout.strip())
    r = sh(os.path.join(IMPB, "improved_cli"), "correct", "in=/nonexistent.jpg", f"out={W('x.png')}", "cx=1", "cy=1", "r=1", check=False)
    out["failure_exit_code"] = r.returncode
    return out


def gallery(stitch, proj):
    """real image: original C3 output vs improved recommended mapping with the fitted lens"""
    img_p = os.path.join(REPO, "ImagesForTest", "1", "1.JPG")
    s1 = stitch.get("set1", {})
    fov = math.radians(s1.get("EQUISOLID_fitted", {}).get("fov_deg", 180.0))
    g = cv2.cvtColor(cv2.imread(img_p), cv2.COLOR_BGR2GRAY)
    rc = detect_circle(g)
    cam = Camera(rc.cx, rc.cy, rc.r, "EQUISOLID", fov)
    wopt = proj["optimum_lin_lon_lccp_lat"]["w"]
    sh(os.path.join(ORIG, "harness"), "c3", img_p, 946, 634, 623, W("g_orig.png"))
    imgs = [("original C3 (main.cpp), equidistant 180, Braun lon+lat", cv2.imread(W("g_orig.png")))]
    for ttl, o in (("improved: C4 projection (paper Eq.17, w=pi/2), fitted lens", Output(Axis("lin"), Axis("lccp", PI / 2))),
                   (f"improved: shape-optimal w={wopt:.2f}, fitted lens", Output(Axis("lin"), Axis("lccp", wopt)))):
        oo = o.resolve(cam)
        sh(os.path.join(IMPB, "improved_cli"), "correct", f"in={img_p}", f"out={W('g_imp.png')}", *imp_args(cam, oo))
        imgs.append((ttl, cv2.imread(W("g_imp.png"))))
    fig, axs = plt.subplots(1, 3, figsize=(16, 7))
    for ax, (ttl, im) in zip(axs, imgs):
        ax.imshow(cv2.cvtColor(im, cv2.COLOR_BGR2RGB)); ax.set_title(ttl, fontsize=9); ax.axis("off")
    fig.suptitle(f"ImagesForTest/1/1.JPG; improved uses circle ({rc.cx:.1f}, {rc.cy:.1f}, {rc.r:.1f}) and equisolid fov {math.degrees(fov):.1f} deg (from stitching)")
    savefig(fig, "improved_C_real_gallery.png")
    return dict(circle=[rc.cx, rc.cy, rc.r], lens="EQUISOLID", fov_deg=math.degrees(fov), w_opt=wopt)


def main():
    for p in (os.path.join(ORIG, "harness"), os.path.join(IMPB, "improved_cli")):
        if not os.path.exists(p):
            sys.exit(f"missing {p}: run research/cpp_harness/build.sh and research/improved/cpp/build.sh")
    os.makedirs(WORK, exist_ok=True)
    res = {}
    for name, fn in (("A_build", part_build), ("B_synthetic_accuracy", part_synthetic), ("C_fov", part_fov),
                     ("D_roundtrip", part_roundtrip), ("E_timing", part_timing), ("F_projection", lambda: part_projection(None)),
                     ("G_circle", part_circle), ("H_stitch", part_stitch), ("I_viewer", part_viewer), ("J_defects", part_defects)):
        t = time.time()
        res[name] = fn()
        print(f"[{name}] {time.time() - t:.0f}s  {json.dumps(res[name], default=float)[:300]}", flush=True)
        with open(os.path.join(MET, "improved.json"), "w") as f:      # keep partial results
            json.dump(res, f, indent=1, default=float)
    res["K_gallery"] = gallery(res["H_stitch"], res["F_projection"])
    with open(os.path.join(MET, "improved.json"), "w") as f:
        json.dump(res, f, indent=1, default=float)
    print("->", os.path.join(MET, "improved.json"))


if __name__ == "__main__":
    main()
