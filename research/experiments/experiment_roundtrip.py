"""Experiment D: are latitudeCorrection4 (reverse) and latitudeCorrection5 (forward)
inverse to each other?  Constraint #2: measured, not inferred from names.

Pipelines (fisheye -> output -> fisheye unless stated):
  P1 exact          closed forms + numpy atan2, continuous coordinates
  P2 source-cont.   source numerics (getPhi1 bisection LIMIT=1e-4, cvFastArctan float32), continuous coords
  P3 source-int     what the two C++ functions actually do with pixels:
                    C5: (int) truncation of output coords; C4: output pixel (i,j) -> Point(u,v),
                    i.e. truncation of the fisheye coords too (measured with research/cpp_harness)
  P3_prev           P3 with C4 ROUNDING -- the wrong assumption of the first report version (kept
                    for traceability only)
  P3b               proposed fix: rounding in both C5 and C4 (removes the bias)
  P4 output -> fisheye -> output with source numerics (opposite direction)
  P5 model mismatch: C4 with STEREOGRAPHIC / EQUISOLID / ORTHOGONAL, C5 is hard-coded EQUIDISTANCE
Also: hole fraction of forward mapping (C5) vs fisheye radius.

    python experiments/experiment_roundtrip.py
"""
from __future__ import annotations

import numpy as np

from _common import plt, savefig, savejson, C
from lccp import PI, SourceStatics, get_phi1_closed, lccp_h, aux_func_source
from correction import c5_forward_coords, correction5
from coordinate_transform import latlon_to_fisheye

S = 512


def c4_inverse(U, V, cx, cy, R, w, fov=PI, model="EQUIDISTANCE", source=True):
    """latitudeCorrection4 evaluated at (possibly non-integer) output coordinates (U, V)."""
    limi = 2 * float(aux_func_source(w, 0.0))
    l = V * limi / S
    if source:
        st = SourceStatics()
        uniq, inv = np.unique(l, return_inverse=True)
        phi = np.array([st.get_phi1(x, w) for x in uniq])[inv].reshape(l.shape)
    else:
        phi = get_phi1_closed(np.clip(l, 0, limi), w)
    lam = (PI - fov) / 2 + U * (fov / S)
    return latlon_to_fisheye(phi, lam, cx, cy, R, fov, model, fast=source)


def stats(e):
    e = np.asarray(e, float)
    return dict(mean=float(e.mean()), rms=float(np.sqrt((e ** 2).mean())), max=float(e.max()),
                p50=float(np.median(e)), p99=float(np.percentile(e, 99)))


def main():
    print("[D] Correction4 / Correction5 round trip")
    rng = np.random.default_rng(42)
    cx, cy, R = 946, 634, 623          # circle of resources/corrected0-3.jpg (byte-identical C++ reproduction, §10.6)
    n = 40000
    rr = R * np.sqrt(rng.uniform(0, 1, n)) * 0.999
    tt = rng.uniform(0, 2 * PI, n)
    u = cx + rr * np.cos(tt)
    v = cy + rr * np.sin(tt)
    out = {"setup": dict(cx=cx, cy=cy, R=R, out_size=S, n_points=n, model="EQUIDISTANCE", fov="pi")}
    errs = {}
    for wname, w in (("pi/2", PI / 2), ("pi/4", PI / 4), ("pi/3", PI / 3)):
        # P1 exact
        U, V = c5_forward_coords(u, v, cx, cy, R, w, PI, S, fast=False)
        u1, v1 = c4_inverse(U, V, cx, cy, R, w, source=False)
        e1 = np.hypot(u1 - u, v1 - v)
        # P2 source numerics, continuous
        U2, V2 = c5_forward_coords(u, v, cx, cy, R, w, PI, S, fast=True)
        u2, v2 = c4_inverse(U2, V2, cx, cy, R, w, source=True)
        e2 = np.hypot(u2 - u, v2 - v)
        # P3 integer pixels (source): C5 trunc, C4 trunc (C++-exact)
        ui, vi = np.rint(u), np.rint(v)
        U3, V3 = c5_forward_coords(ui, vi, cx, cy, R, w, PI, S, fast=True)
        I3, J3 = np.trunc(U3), np.trunc(V3)
        ok = (I3 >= 0) & (I3 < S) & (J3 >= 0) & (J3 < S)
        u3, v3 = c4_inverse(I3[ok], J3[ok], cx, cy, R, w, source=True)
        e3 = np.hypot(np.trunc(u3) - ui[ok], np.trunc(v3) - vi[ok])
        bias3 = (float(np.mean(np.trunc(u3) - ui[ok])), float(np.mean(np.trunc(v3) - vi[ok])))
        # P3_prev: C4 rounding (wrong assumption of the first report version)
        e3p = np.hypot(np.rint(u3) - ui[ok], np.rint(v3) - vi[ok])
        bias3p = (float(np.mean(np.rint(u3) - ui[ok])), float(np.mean(np.rint(v3) - vi[ok])))
        # P3b proposed fix: round in both
        I3b, J3b = np.rint(U3), np.rint(V3)
        okb = (I3b >= 0) & (I3b < S) & (J3b >= 0) & (J3b < S)
        u3b, v3b = c4_inverse(I3b[okb], J3b[okb], cx, cy, R, w, source=True)
        e3b = np.hypot(np.rint(u3b) - ui[okb], np.rint(v3b) - vi[okb])
        bias3b = (float(np.mean(np.rint(u3b) - ui[okb])), float(np.mean(np.rint(v3b) - vi[okb])))
        # P4 output -> fisheye -> output
        J, I = np.mgrid[0:S, 0:S].astype(float)
        uf, vf = c4_inverse(I, J, cx, cy, R, w, source=True)
        Ub, Vb = c5_forward_coords(uf, vf, cx, cy, R, w, PI, S, fast=True)
        e4 = np.hypot(Ub - I, Vb - J)
        # local output pixel size in fisheye px (quantisation scale)
        out[f"w={wname}"] = {
            "P1_exact_continuous_px": stats(e1),
            "P2_source_numerics_continuous_px": stats(e2),
            "P3_integer_pipeline_cpp_exact_px": stats(e3), "P3_mean_signed_bias_px(u,v)": bias3,
            "P3_prev_assumed_C4_rounding_px": stats(e3p), "P3_prev_mean_signed_bias_px(u,v)": bias3p,
            "P3b_fix_round_both_px": stats(e3b), "P3b_mean_signed_bias_px(u,v)": bias3b,
            "P4_output_fisheye_output_outpx": stats(e4),
            "P4_excluding_row0_pole_and_col0_wrap": stats(e4[1:, 1:]),
            "P4_rows0_pole_bad_px": int((e4[0] > 1).sum()), "P4_col0_atan2_wrap_bad_px": int((e4[1:, 0] > 1).sum()),
        }
        errs[wname] = (e1, e2, e3, e4, ok)
    # P5 model mismatch
    out["P5_model_mismatch"] = {}
    for model in ("STEREOGRAPHIC", "EQUISOLID", "ORTHOGONAL", "EQUIDISTANCE"):
        U, V = c5_forward_coords(u, v, cx, cy, R, PI / 2, PI, S, fast=False)
        um, vm = c4_inverse(U, V, cx, cy, R, PI / 2, model=model, source=False)
        out["P5_model_mismatch"][model] = stats(np.hypot(um - u, vm - v))
    # FOV < pi (both use the same fov)
    U, V = c5_forward_coords(u, v, cx, cy, R, PI / 2, 0.8 * PI, S, fast=False)
    okf = (U >= 0) & (U < S) & (V >= 0) & (V < S)
    uf2, vf2 = c4_inverse(U[okf], V[okf], cx, cy, R, PI / 2, fov=0.8 * PI, source=False)
    out["fov_0.8pi_exact"] = stats(np.hypot(uf2 - u[okf], vf2 - v[okf]))
    out["fov_0.8pi_fraction_of_fisheye_points_landing_inside_output"] = float(okf.mean())

    # heatmaps (w = pi/2)
    e1, e2, e3, e4, ok = errs["pi/2"]
    fig, axs = plt.subplots(1, 4, figsize=(17, 4))
    for ax, e, uu, vv, ttl in ((axs[0], e1, u, v, "P1 exact (px)"), (axs[1], e2, u, v, "P2 source numerics, continuous (px)"),
                               (axs[2], e3, u[ok], v[ok], "P3 integer pipeline (px)")):
        sc = ax.scatter(uu, vv, c=e, s=1, cmap="Blues", vmin=0, vmax=np.percentile(e, 99.5) if e.max() > 0 else 1)
        ax.set_aspect("equal"); ax.invert_yaxis(); ax.set_title(ttl, fontsize=9)
        fig.colorbar(sc, ax=ax, shrink=0.75)
    im = axs[3].imshow(e4, cmap="Blues", vmax=np.percentile(e4, 99.5))
    axs[3].set_title("P4 output->fisheye->output (output px)", fontsize=9)
    fig.colorbar(im, ax=axs[3], shrink=0.75)
    fig.suptitle("Correction5 (forward) then Correction4 (reverse), w = pi/2, R=623 (fisheye px)")
    savefig(fig, "roundtrip_D_heatmaps.png")

    fig, ax = plt.subplots(figsize=(7, 3.6))
    bins = np.logspace(-14, 1.5, 80)
    for k, (e, lab) in enumerate(((e1, "P1 exact"), (e2, "P2 source numerics"), (e3 + 1e-14, "P3 integer pixels"))):
        ax.hist(e + 1e-15, bins=bins, histtype="step", lw=1.5, color=C[k], label=lab)
    ax.set_xscale("log"); ax.set_xlabel("round-trip error (fisheye px)"); ax.set_ylabel("count"); ax.legend(fontsize=8)
    ax.set_title("Round-trip error distribution (w = pi/2)")
    savefig(fig, "roundtrip_D_hist.png")

    # hole fraction of the forward method
    holes = {}
    for Rh in (128, 200, 256, 400, 623, 900):
        img = (np.random.default_rng(1).integers(1, 255, (2 * Rh + 20, 2 * Rh + 20, 3))).astype(np.uint8)
        _, hit, oob = correction5(img, Rh + 10, Rh + 10, Rh, PI / 2, PI, S)
        holes[str(Rh)] = dict(hole_fraction=float(1 - hit.mean()), fisheye_pixels=int(PI * Rh * Rh), oob_reads=oob)
    # clipped circle -> out-of-bounds reads in C++
    img = np.zeros((1100, 1300, 3), np.uint8)
    _, hit, oob = correction5(img, 650, 520, 600, PI / 2, PI, S)
    holes["clipped_circle_cy520_R600_H1100"] = dict(oob_reads=oob, note="C++ reads imgOrg.at(j,i) outside the image (UB)")
    out["C5_forward_holes"] = holes
    savejson(out, "roundtrip_D.json")
    return out


if __name__ == "__main__":
    o = main()
    import json
    print(json.dumps({k: v for k, v in o.items() if k != "setup"}, indent=1, default=float)[:6000])
