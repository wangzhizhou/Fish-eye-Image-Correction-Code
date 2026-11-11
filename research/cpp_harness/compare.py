"""Run the C++ harness (original program/ sources) and compare it number-by-number with the
Python port in research/src.  Build first:  bash research/cpp_harness/build.sh
    python research/cpp_harness/compare.py
Writes research/results/metrics/cpp_harness.json (+ a figure)."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "experiments"))
from _common import REPO, MET, FIG, plt, savefig  # noqa: E402
import cv2  # noqa: E402
from lccp import (PI, get_phi_source, get_phi_closed, SourceStatics, get_phi1_closed,  # noqa: E402
                  aux_func_source, aux_func_closed)
from kasa import kasa_fit_source  # noqa: E402
from coordinate_transform import fast_atan2_deg  # noqa: E402
from correction import c3_latlon, c4_latlon, maps_from_latlon, c5_forward_coords, correction5  # noqa: E402

BUILD = os.path.join(HERE, "build")
HARNESS = os.path.join(BUILD, "harness")
WORK = os.path.join(BUILD, "run")
WS = {"pi/6": PI / 6, "pi/4": PI / 4, "pi/3": PI / 3, "pi/2": PI / 2, "2pi/3": 2 * PI / 3}
CX, CY, R = 945, 634, 623          # best match of resources/corrected0.jpg (REPORT §10.5)


def run(*args, exe=HARNESS, cwd=None, check=True, **kw):
    r = subprocess.run([exe, *map(str, args)], cwd=cwd or WORK, capture_output=True, text=True,
                       stdin=subprocess.DEVNULL, **kw)
    if check and r.returncode != 0:
        raise RuntimeError(f"{args}: exit {r.returncode}\n{r.stdout}\n{r.stderr}")
    return r


def W(name):
    return os.path.join(WORK, name)


# ---- coordinate-encoded test images: every pixel stores its own (u, v) -------------------
def encode(h, w):
    v, u = np.mgrid[0:h, 0:w]
    assert w <= 2048 and h <= 2048
    img = np.zeros((h, w, 3), np.uint8)
    img[..., 0] = u & 255
    img[..., 1] = v & 255
    img[..., 2] = 128 | (u >> 8) | ((v >> 8) << 3)        # bit 7 set => (0,0,0) means "not written"
    return img


def decode(img):
    b, g, r = (img[..., k].astype(np.int64) for k in range(3))
    written = r >= 128
    u = b | ((r & 7) << 8)
    v = g | (((r >> 3) & 7) << 8)
    return u, v, written


def stats(e):
    e = np.asarray(e, float)
    return dict(n=int(e.size), mean=float(e.mean()), rms=float(np.sqrt((e ** 2).mean())), max=float(e.max()))


# ---------------------------------------------------------------------------------------------
def t_getphi():
    run("getphi", 1920, W("getphi.txt"))
    j, l, phi = np.loadtxt(W("getphi.txt")).T
    py = np.array([get_phi_source(x).phi for x in l])
    err = phi - get_phi_closed(l)
    k = int(np.argmax(np.abs(err)))
    return dict(
        H=1920, max_abs_diff_cpp_vs_python_port=float(np.max(np.abs(phi - py))),
        bitwise_identical_rows=int(np.sum(phi == py)),
        cpp_getPhi_at_l2=float(phi[960]), cpp_error_at_l2_rad=float(err[960]),
        cpp_max_abs_error_vs_closed_rad=float(np.abs(err[k])), at_row=int(j[k]), at_l=float(l[k]),
        rows_error_gt_1em3=int(np.sum(np.abs(err) > 1e-3)),
        rows_error_gt_1em3_range=[int(j[np.abs(err) > 1e-3].min()), int(j[np.abs(err) > 1e-3].max())],
        # row shift: the exact mapping would put the C++ phi at row j* = H/4 * (2 - 2 tan(pi/4 - phi/2))
        cpp_max_row_shift=float(np.max(np.abs(1920 / 4 * (2 - 2 * np.tan(PI / 4 - phi / 2)) - j))),
    ), (l, err)


def t_getphi1():
    out = {}
    for name, w in WS.items():
        f = W(f"getphi1_{name.replace('/', '_')}.txt")
        run("getphi1", repr(w), 512, f)
        j, l, phi = np.loadtxt(f).T
        py = np.array([SourceStatics().get_phi1(x, w) for x in l])
        cl = get_phi1_closed(np.clip(l, 0, None), w)
        out[name] = dict(max_abs_diff_cpp_vs_python_port=float(np.max(np.abs(phi - py))),
                         bitwise_identical_rows=int(np.sum(phi == py)),
                         cpp_max_abs_error_vs_closed_rad=float(np.max(np.abs(phi - cl))))
    return out


def t_static():
    w0, w = PI / 2, PI / 4
    run("static", repr(w0), repr(w), 512, W("static.txt"))
    j, l, phi = np.loadtxt(W("static.txt")).T
    st = SourceStatics()
    st.get_phi1(0.0, w0)
    py = np.array([st.get_phi1(x, w) for x in l])
    err = np.degrees(np.abs(phi - get_phi1_closed(l, w)))
    return dict(first_w="pi/2", then_w="pi/4", rows=512,
                max_abs_diff_cpp_vs_python_port=float(np.max(np.abs(phi - py))),
                cpp_rows_error_gt_1deg=int(np.sum(err > 1)), cpp_max_error_deg=float(err.max()))


def t_aux():
    out = {}
    for name, w in WS.items():
        f = W(f"aux_{name.replace('/', '_')}.txt")
        run("aux", repr(w), f)
        phi, a = np.loadtxt(f).T
        out[name] = dict(max_abs_diff_cpp_vs_python_port=float(np.max(np.abs(a - aux_func_source(w, phi)))),
                         max_abs_diff_cpp_vs_closed=float(np.max(np.abs(a - aux_func_closed(w, phi)))),
                         cpp_aux_at_equator=float(a[1000]), cpp_h=float(a[0]))
    return out


def t_fastatan():
    run("fastatan", W("fastatan.txt"))
    y, x, a = np.loadtxt(W("fastatan.txt")).T
    py = fast_atan2_deg(y.astype(np.float32), x.astype(np.float32)).astype(float)
    ex = np.degrees(np.mod(np.arctan2(y, x), 2 * PI))
    d = np.abs(a - py)
    de = np.abs(a - ex)
    de = np.minimum(de, 360 - de)
    return dict(n=int(a.size), max_abs_diff_cpp_vs_python_emulation_deg=float(d.max()),
                cpp_max_error_vs_atan2_deg=float(de.max()))


def t_kasa():
    rng = np.random.default_rng(7)
    sets = {"diamond_100_100": np.array([[0, 100], [100, 0], [200, 100], [100, 200]])}
    for k in range(40):
        cx, cy, r = rng.uniform(300, 1600), rng.uniform(300, 1000), rng.uniform(100, 700)
        t = rng.uniform(0, 2 * PI, int(rng.integers(3, 25)))
        p = np.c_[cx + r * np.cos(t), cy + r * np.sin(t)] + rng.normal(0, 2, (t.size, 2))
        sets[f"rand{k}"] = np.trunc(p).astype(int)
    sets["two_points"] = np.array([[0, 0], [10, 10]])
    with open(W("kasa_in.txt"), "w") as f:
        for k, p in sets.items():
            f.write(f"{k} {len(p)} " + " ".join(f"{a} {b}" for a, b in p) + "\n")
    run("kasa", W("kasa_in.txt"), W("kasa_out.txt"))
    agree, rows = 0, {}
    for line in open(W("kasa_out.txt")):
        k, ok, cx, cy, r = line.split()
        ok, cpp = bool(int(ok)), (int(cx), int(cy), int(r))
        pok, pc, pr, cont = kasa_fit_source(sets[k]) if len(sets[k]) > 2 else (False, None, None, None)
        same = (ok == pok) and (not ok or cpp == (*pc, pr))
        agree += same
        if k in ("diamond_100_100", "two_points") or not same:
            rows[k] = dict(cpp_ok=ok, cpp=cpp if ok else None, python_ok=pok,
                           python=(*pc, pr) if pok else None,
                           python_continuous=[float(c) for c in cont] if pok else None)
    return dict(sets=len(sets), cpp_equals_python_port=agree, details=rows)


def t_c3(img1):
    """latitudeCorrection3: exact C++ sampling map vs Python maps (rint vs trunc), gold MAE."""
    H0, W0 = 1280, 1920
    cv2.imwrite(W("enc_1920x1280.png"), encode(H0, W0))
    t = time.time()
    run("c3", W("enc_1920x1280.png"), CX, CY, R, W("c3_enc.png"))
    t_c3 = time.time() - t
    u, v, wr = decode(cv2.imread(W("c3_enc.png")))
    phi, lam = c3_latlon(1920, 1920, source_like=True)
    mu, mv = maps_from_latlon(phi, lam, CX, CY, R, PI, "EQUIDISTANCE", fast=True)
    res = dict(cpp_runtime_s=round(t_c3, 1), written_fraction=float(wr.mean()))
    for name, fn in (("rint", np.rint), ("trunc", np.trunc)):
        pu, pv = fn(mu).astype(int), fn(mv).astype(int)
        ins = (pu >= 0) & (pu < W0) & (pv >= 0) & (pv < H0)
        same = (pu == u) & (pv == v) & wr & ins
        res[f"python_{name}_agrees_with_cpp"] = float(same.sum() / wr.sum())
        res[f"python_{name}_mask_agrees"] = float(np.mean(ins == wr))
    # gold: original program output shipped in the repo
    gold = cv2.imread(os.path.join(REPO, "resources", "corrected0.jpg")).astype(int)
    eq = slice(950, 971)
    for cx in (945, 946):
        run("c3", os.path.join(REPO, "ImagesForTest", "1", "1.JPG"), cx, CY, R, W(f"c3_real_{cx}.png"))
        cpp_real = cv2.imread(W(f"c3_real_{cx}.png")).astype(int)
        res[f"gold_MAE_cpp_direct_{cx}_634_623"] = float(np.abs(cpp_real - gold).mean())
        res[f"gold_MAE_cpp_direct_{cx}_634_623_rows950_970"] = float(np.abs(cpp_real[eq] - gold[eq]).mean())
        res[f"gold_MAE_cpp_direct_{cx}_634_623_cols950_970"] = float(np.abs(cpp_real[:, eq] - gold[:, eq]).mean())
    # byte-level check: main.cpp applies the FIRST image's circle to all images and saves with
    # imwrite("correctedN.jpg") (OpenCV default JPEG quality 95). Let the C++ harness write the .jpg.
    byte_eq = {}
    for k in range(4):
        src = os.path.join(REPO, "ImagesForTest", "1", f"{k + 1}.JPG")
        dst = W(f"corrected{k}_cpp.jpg")
        run("c3", src, 946, CY, R, dst)
        a = open(dst, "rb").read()
        b = open(os.path.join(REPO, "resources", f"corrected{k}.jpg"), "rb").read()
        da, db = cv2.imread(dst).astype(int), cv2.imread(os.path.join(REPO, "resources", f"corrected{k}.jpg")).astype(int)
        byte_eq[f"corrected{k}.jpg"] = dict(input=f"ImagesForTest/1/{k + 1}.JPG", bytes_cpp=len(a), bytes_repo=len(b),
                                            byte_identical=a == b, decoded_MAE=float(np.abs(da - db).mean()))
    res["byte_identity_946_634_623"] = byte_eq
    res["jpeg_q95_self_MAE_reference"] = float(np.abs(cv2.imdecode(cv2.imencode(
        ".jpg", cpp_real.astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 95])[1], 1).astype(int) - cpp_real).mean())
    # is the getPhi equator error in the shipped output?  same trunc sampling, closed-form phi/lambda
    phc, lac = c3_latlon(1920, 1920, source_like=False)
    for name, (ph_, la_) in (("source_getPhi", (phi, lam)), ("closed_form_phi", (phc, lac))):
        a, b = maps_from_latlon(ph_, la_, 946, CY, R, PI, "EQUIDISTANCE", fast=True)
        a, b = np.trunc(a).astype(int), np.trunc(b).astype(int)
        ok = (a >= 0) & (a < W0) & (b >= 0) & (b < H0)
        o = np.zeros_like(gold)
        o[ok] = img1[b[ok], a[ok]]
        res[f"gold_946_trunc_{name}_MAE_all"] = float(np.abs(o - gold).mean())
        res[f"gold_946_trunc_{name}_MAE_rows950_970"] = float(np.abs(o[eq] - gold[eq]).mean())
        res[f"gold_946_trunc_{name}_MAE_cols950_970"] = float(np.abs(o[:, eq] - gold[:, eq]).mean())
    # grid search with the C++-exact (trunc) sampling, done in Python with the C++ operation order
    Th = np.arccos(np.sin(phi)[:, None] * np.sin(lam)[None, :])
    al = fast_atan2_deg(np.cos(phi)[:, None] * np.ones_like(lam)[None, :],
                        (-np.sin(phi)[:, None] * np.cos(lam)[None, :])).astype(float) * PI / 180
    ca, sa = np.cos(al), np.sin(al)
    best = []
    for cx in range(943, 950):
        for cy in range(631, 638):
            for rr in range(620, 627):
                p = rr / (PI / 2) * Th
                uu = np.trunc(p * ca + cx).astype(int)
                vv = np.trunc(-(p * sa) + cy).astype(int)
                ok = (uu >= 0) & (uu < W0) & (vv >= 0) & (vv < H0)
                out = np.zeros_like(gold)
                out[ok] = img1[vv[ok], uu[ok]]
                best.append((float(np.abs(out - gold).mean()), cx, cy, rr))
    best.sort()
    res["gold_grid_search_trunc_top3"] = best[:3]
    res["gold_grid_search_trunc_at_945_634_623"] = [b for b in best if b[1:] == (945, 634, 623)][0][0]
    res["gold_grid_search_trunc_at_946_634_623"] = [b for b in best if b[1:] == (946, 634, 623)][0][0]
    return res, (u, v, wr, mu, mv)


def t_c4c5():
    H0, W0 = 1280, 1920
    enc = W("enc_1920x1280.png")
    res = {}
    # ret.jpg side effect (BUG-16): fresh directory
    side = W("cwd_sidefx")
    shutil.rmtree(side, ignore_errors=True)
    os.makedirs(side)
    run("c4", enc, CX, CY, R, repr(PI / 2), "EQUIDISTANCE", repr(PI), W("c4_enc.png"), cwd=side)
    after_c4 = os.path.exists(os.path.join(side, "ret.jpg"))
    m4 = cv2.imread(os.path.join(side, "ret.jpg")) if after_c4 else None
    run("c5", enc, CX, CY, R, repr(PI / 2), "EQUIDISTANCE", repr(PI), W("c5_enc.png"), cwd=side)
    m5 = cv2.imread(os.path.join(side, "ret.jpg"))
    c4o, c5o = cv2.imread(W("c4_enc.png")).astype(int), cv2.imread(W("c5_enc.png")).astype(int)
    res["BUG16_ret_jpg"] = dict(
        created_by_c4=after_c4, MAE_retjpg_after_c4_vs_c4_output=float(np.abs(m4.astype(int) - c4o).mean()),
        MAE_retjpg_after_c5_vs_c5_output=float(np.abs(m5.astype(int) - c5o).mean()),
        MAE_retjpg_after_c5_vs_c4_output=float(np.abs(m5.astype(int) - c4o).mean()))

    u4, v4, w4 = decode(cv2.imread(W("c4_enc.png")))
    u5, v5, w5 = decode(cv2.imread(W("c5_enc.png")))
    # C4 map vs Python
    phi, lam = c4_latlon(512, 512, PI / 2, PI / 2, PI, source_like=True)
    mu, mv = maps_from_latlon(phi, lam, CX, CY, R, PI, "EQUIDISTANCE", fast=True)
    for name, fn in (("rint", np.rint), ("trunc", np.trunc)):
        same = (fn(mu).astype(int) == u4) & (fn(mv).astype(int) == v4) & w4
        res[f"C4_python_{name}_agrees_with_cpp"] = float(same.sum() / w4.sum())
    # C5: each written output pixel (V,U) holds the source fisheye pixel (u,v) (last writer)
    V, U = np.nonzero(w5)
    su, sv = u5[w5], v5[w5]
    pu, pv = c5_forward_coords(su, sv, CX, CY, R, PI / 2, PI, 512, fast=True)
    res["C5_python_trunc_forward_agrees_with_cpp"] = float(np.mean((np.trunc(pu) == U) & (np.trunc(pv) == V)))
    py5, hit, _ = correction5(encode(H0, W0), CX, CY, R, PI / 2, PI, 512)
    res["C5_hole_fraction_cpp"] = float(1 - w5.mean())
    res["C5_hole_fraction_python"] = float(1 - hit.mean())
    res["C5_image_identical_pixels_cpp_vs_python"] = float(np.mean(np.all(py5.astype(int) == c5o, axis=2)))
    # integer round trip fisheye -> C5 -> output -> C4 -> fisheye, all in C++ (one sample per output px)
    ok = w4[V, U]
    du, dv = (u4[V, U] - su)[ok], (v4[V, U] - sv)[ok]
    res["roundtrip_cpp_integer_EQUIDISTANCE"] = dict(**stats(np.hypot(du, dv)),
                                                    mean_signed_bias_uv=[float(du.mean()), float(dv.mean())])
    for name, fn in (("rint", np.rint), ("trunc", np.trunc)):
        qu, qv = fn(mu).astype(int)[V, U][ok], fn(mv).astype(int)[V, U][ok]
        res[f"roundtrip_python_C4{name}_same_samples"] = dict(
            **stats(np.hypot(qu - su[ok], qv - sv[ok])),
            mean_signed_bias_uv=[float((qu - su[ok]).mean()), float((qv - sv[ok]).mean())])
    # BUG-04: C4 with other lens models vs C5 (hard-coded equidistant)
    for model in ("STEREOGRAPHIC", "EQUISOLID", "ORTHOGONAL"):
        run("c4", enc, CX, CY, R, repr(PI / 2), model, repr(PI), W(f"c4_{model}.png"), cwd=side)
        a, b, wa = decode(cv2.imread(W(f"c4_{model}.png")))
        ok2 = wa[V, U]
        res[f"roundtrip_cpp_C5equidistant_C4{model}"] = stats(np.hypot(a[V, U][ok2] - su[ok2], b[V, U][ok2] - sv[ok2]))
    return res


def t_oob():
    """BUG-06: C5 reads imgOrg.at(j,i) without bounds check. Circle (200,200,R=300) in a 400x400 image.
    (a) build.sh flags (no NDEBUG): OpenCV's inline CV_DbgAssert in Mat::at fires -> uncaught cv::Exception.
    (b) -DNDEBUG + ASan: the raw out-of-bounds read itself."""
    cv2.imwrite(W("enc_400.png"), encode(400, 400))
    args = ("c5", W("enc_400.png"), 200, 200, 300, repr(PI / 2), "EQUIDISTANCE", repr(PI), W("c5_oob.png"))
    out = {}
    r = run(*args, check=False, timeout=120)
    out["buildsh_flags"] = dict(exit=r.returncode, stderr=next((ln.strip() for ln in r.stderr.splitlines()
                                                                if "Exception" in ln or "error" in ln), "")[:300])
    r = run(*args, exe=os.path.join(BUILD, "harness_asan_ndebug"), check=False, timeout=120)
    first = next((ln for ln in r.stderr.splitlines() if "ERROR: AddressSanitizer" in ln), "")
    frame = next((ln.strip() for ln in r.stderr.splitlines() if "corrector.cpp" in ln), "")
    out["ndebug_asan"] = dict(exit=r.returncode, asan_error=first.split("on address")[0].strip(),
                              first_program_frame=frame)
    return out


def t_navigator():
    """BUG-12: main.cpp L52 `i <= imagePaths.size()`; run the ORIGINAL main with ASan, one image."""
    exe = os.path.join(BUILD, "navigator_asan")
    r = run(os.path.join(REPO, "ImagesForTest", "1", "1.JPG"), exe=exe, check=False, timeout=60)
    first = next((ln for ln in r.stderr.splitlines() if "ERROR: AddressSanitizer" in ln), "")
    frame = next((ln.strip() for ln in r.stderr.splitlines() if "main.cpp" in ln), "")
    return dict(asan_exit=r.returncode, asan_error=first.split("on address")[0].strip(),
                first_program_frame=frame, stdout_tail=r.stdout.strip().splitlines()[-2:])


def t_stitchfail():
    """BUG-23: Stitcher failure -> Tip() -> exit(0) before exit(-1)."""
    r = run("stitchfail", check=False, timeout=120)
    return dict(input="1 image (Stitcher returns ERR_NEED_MORE_IMGS)", exit_code=r.returncode,
                stdout=[ln for ln in r.stdout.splitlines() if ln.strip()][:4])


def t_l1():
    """BUG-15: latitudeCorrection Forward uses R = radius/sin(FOV/2), Reverse uses R = radius."""
    out = {}
    enc = W("enc_1920x1280.png")
    for name, fov in (("pi", PI), ("0.8pi", 0.8 * PI)):
        maps = {}
        for t in ("Forward", "Reverse"):
            run("l1", enc, CX, CY, R, repr(fov), t, W(f"l1_{t}_{name}.png"))
            maps[t] = decode(cv2.imread(W(f"l1_{t}_{name}.png")))
        (uf, vf, wf), (ur, vr, wrr) = maps["Forward"], maps["Reverse"]
        both = wf & wrr
        d = np.hypot(uf - ur, vf - vr)[both]
        rr_f = np.hypot(uf[wf] - CX, vf[wf] - CY)
        rr_r = np.hypot(ur[wrr] - CX, vr[wrr] - CY)
        out[name] = dict(pixels_both=int(both.sum()), fwd_vs_rev_fisheye_distance=stats(d),
                         fwd_vs_rev_median=float(np.median(d)),
                         max_fisheye_radius_used_forward=float(rr_f.max()),
                         max_fisheye_radius_used_reverse=float(rr_r.max()))
    return out


def t_viewer():
    """BUG-24: viewer's Point pt(v,u) / Rect(0,0,height,width+1). Encoded 2048x1024 'panorama'."""
    Hp, Wp = 1024, 2048
    cv2.imwrite(W("enc_pano.png"), encode(Hp, Wp))
    run("viewer", W("enc_pano.png"), W("viewer_out.png"))
    u, v, wr = decode(cv2.imread(W("viewer_out.png")))
    # independent re-implementation with the intended (u, v) order and no inside() test
    h, w = 512, 1024
    j, i = np.mgrid[0:h, 0:w]
    p = np.stack([i - w // 2, h // 2 - j, np.full_like(i, 300)], -1).astype(float)
    p /= np.linalg.norm(p, axis=-1, keepdims=True)
    aH, aV = 0.0, PI / 2
    MH = np.array([[np.cos(aH), 0, -np.sin(aH)], [0, 1, 0], [np.sin(aH), 0, np.cos(aH)]])
    MV = np.array([[1, 0, 0], [0, np.cos(aV), -np.sin(aV)], [0, np.sin(aV), np.cos(aV)]])
    q = p @ (MV @ MH).T
    lat = np.arccos(q[..., 2])
    lon = fast_atan2_deg(q[..., 1].astype(np.float32), q[..., 0].astype(np.float32)).astype(float) * PI / 180
    pu = np.trunc(lon / (2 * PI) * Wp).astype(int) % Wp
    pv = np.trunc(lat / PI * Hp).astype(int) % Hp
    return dict(window=[w, h], written_fraction=float(wr.mean()),
                python_intended_indexing_agrees=float(np.mean((pu == u) & (pv == v) & wr)),
                note="written_fraction==1 => the swapped inside() test never rejects a pixel")


def t_stitch_real():
    """Run main.cpp's stitching sequence on the repo's own corrected0-3.jpg."""
    imgs = [os.path.join(REPO, "resources", f"corrected{k}.jpg") for k in range(4)]
    t = time.time()
    r = run("stitch", W("panorama_cpp.png"), *imgs, check=False, timeout=900)
    ref = cv2.imread(os.path.join(REPO, "resources", "panorama.jpg"))
    out = dict(exit_code=r.returncode, stdout=[ln for ln in r.stdout.splitlines() if ln.strip()][-2:],
               seconds=round(time.time() - t),
               repo_panorama_jpg_size=[ref.shape[1], ref.shape[0]],
               repo_panorama_aspect=round(ref.shape[1] / ref.shape[0], 3))
    if r.returncode == 0 and os.path.exists(W("panorama_cpp.png")):
        p = cv2.imread(W("panorama_cpp.png"))
        out.update(cpp_panorama_size=[p.shape[1], p.shape[0]], cpp_panorama_aspect=round(p.shape[1] / p.shape[0], 3))
    return out


def main():
    if not os.path.exists(HARNESS):
        sys.exit("harness not built: bash research/cpp_harness/build.sh")
    os.makedirs(WORK, exist_ok=True)
    img1 = cv2.imread(os.path.join(REPO, "ImagesForTest", "1", "1.JPG")).astype(int)
    out = dict(setup=dict(
        opencv=open(os.path.join(BUILD, "opencv_version.txt")).read().strip(),
        compiler=open(os.path.join(BUILD, "compiler_version.txt")).read().strip(),
        flags="-std=c++11 -g (as build.sh)", program_dir_modified=False,
        circle=[CX, CY, R]))
    steps = [("getPhi", t_getphi), ("getPhi1", t_getphi1), ("static_cache", t_static), ("auxFunc", t_aux),
             ("cvFastArctan", t_fastatan), ("CircleFitByKasa", t_kasa), ("C4_C5", t_c4c5),
             ("BUG06_C5_out_of_bounds_asan", t_oob), ("BUG12_navigator_asan", t_navigator),
             ("BUG23_stitch_failure_exit", t_stitchfail), ("BUG15_latitudeCorrection_fwd_vs_rev", t_l1),
             ("BUG24_viewer", t_viewer), ("stitch_real", t_stitch_real)]
    extra = {}
    for name, fn in [("getPhi", t_getphi)] + [("C3", lambda: t_c3(img1))] + steps[1:]:
        t = time.time()
        r = fn()
        if isinstance(r, tuple):
            r, extra[name] = r
        out[name] = r
        print(f"[{name}] {time.time() - t:.0f}s  {json.dumps(r, default=float)[:400]}")
    with open(os.path.join(MET, "cpp_harness.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)

    # figure: getPhi error measured in C++, and C3 sampling map C++ - Python(rint)
    l, err = extra["getPhi"]
    u, v, wr, mu, mv = extra["C3"]
    fig, axs = plt.subplots(1, 3, figsize=(15, 4.2))
    axs[0].plot(l, err, lw=1)
    axs[0].set_xlabel("l = 4j/H"); axs[0].set_ylabel("C++ getPhi(l) - 2atan(l/(4-l))  [rad]")
    axs[0].set_title("C++ getPhi error (H=1920), measured")
    du = np.where(wr, u - mu, np.nan)
    im = axs[1].imshow(du, cmap="coolwarm", vmin=-1, vmax=1)
    axs[1].set_title("C3: C++ sampled u  -  continuous u"); fig.colorbar(im, ax=axs[1], fraction=0.046)
    axs[2].hist((u - mu)[wr].ravel(), bins=100, range=(-1, 1), alpha=0.7, label="u")
    axs[2].hist((v - mv)[wr].ravel(), bins=100, range=(-1, 1), alpha=0.7, label="v")
    axs[2].set_title("C++ integer - continuous coordinate\n(trunc => (-1, 0]; rint would give [-0.5, 0.5])")
    axs[2].legend()
    savefig(fig, "cpp_harness_getphi_c3.png")
    print("->", os.path.join(MET, "cpp_harness.json"))


if __name__ == "__main__":
    main()
