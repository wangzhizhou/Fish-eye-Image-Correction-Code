"""Phase 2 experiments: Kasa vs other circle fits, and the VALS port on SYNTHETIC images
and on the repository's real fisheye images (no ground truth there -> stability only).

    python experiments/experiment_vals.py [--quick]
"""
from __future__ import annotations

import sys
import time

import numpy as np

from _common import plt, savefig, savejson, savecsv, repo_path, C
from kasa import FITTERS
from vals import synthetic_fisheye, synthetic_edge_points, vals_source, vals_improved

QUICK = "--quick" in sys.argv
TRIALS = 20 if QUICK else 100


# ----------------------------------------------------------------- E1 circle fits
def exp_fits():
    print("[E1] circle fitting on synthetic edge points")
    R0, CX, CY = 300.0, 640.0, 480.0
    scen = []
    for s in (0.5, 1, 2, 4):
        scen.append(("noise", s, dict(noise=s)))
    for o in (0.0, 0.05, 0.1, 0.2, 0.3):
        scen.append(("outliers", o, dict(noise=1, outlier_frac=o)))
    for arcdeg in (360, 180, 90, 45, 20):
        scen.append(("arc_deg", arcdeg, dict(noise=1, arc=(0, np.radians(arcdeg)))))
    rows = []
    for kind, val, kw in scen:
        for name, fit in FITTERS.items():
            ce, re_, rms, fail = [], [], [], 0
            for t in range(TRIALS):
                p = synthetic_edge_points(60, CX, CY, R0, seed=1000 + t, **kw)
                c = fit(p)
                if not c.ok or not np.isfinite(c.r):
                    fail += 1
                    continue
                ce.append(np.hypot(c.cx - CX, c.cy - CY)); re_.append(abs(c.r - R0)); rms.append(c.rms(p))
            rows.append(dict(scenario=kind, value=val, method=name,
                             center_err_mean=np.mean(ce) if ce else np.nan,
                             center_err_p95=np.percentile(ce, 95) if ce else np.nan,
                             radius_err_mean=np.mean(re_) if re_ else np.nan,
                             residual_rms_mean=np.mean(rms) if rms else np.nan,
                             center_err_std=np.std(ce) if ce else np.nan, failures=fail, trials=TRIALS))
    savecsv(rows, "vals_E1_circle_fits.csv")
    fig, axs = plt.subplots(1, 3, figsize=(13, 3.6))
    for ax, kind, xl in zip(axs, ("noise", "outliers", "arc_deg"),
                            ("edge noise sigma (px)", "outlier fraction", "visible arc (deg)")):
        for k, name in enumerate(FITTERS):
            rr = [r for r in rows if r["scenario"] == kind and r["method"] == name]
            ax.plot([r["value"] for r in rr], [r["center_err_mean"] for r in rr], marker="o", ms=4,
                    color=C[k], label=name)
        ax.set_yscale("log"); ax.set_xlabel(xl); ax.set_ylabel("mean centre error (px)")
        if kind == "arc_deg":
            ax.invert_xaxis()
    axs[0].legend(fontsize=8)
    fig.suptitle(f"Circle fit comparison, R=300 px, 60 pts, {TRIALS} trials (SYNTHETIC)")
    savefig(fig, "vals_E1_circle_fits.png")
    return rows


# ----------------------------------------------------------------- E2 VALS on synthetic images
CONDS = {
    "clean": dict(),
    "noisy(sigma=8)": dict(noise=8),
    "low_contrast": dict(inner=45, background=10, vignette=0.6, texture=10),
    "missing_edge": dict(missing_sector=(np.radians(200), np.radians(260))),
    "outlier_specks": dict(specks=4),
}
GT = dict(cx=410.3, cy=297.6, r=260.0)


def _err(res):
    if not res.ok:
        return np.nan, np.nan
    cx, cy = res.center
    return float(np.hypot(cx - GT["cx"], cy - GT["cy"])), float(abs(res.radius - GT["r"]))


def exp_vals_synth():
    print("[E2] VALS port on synthetic images")
    seeds = (0, 1) if QUICK else (0, 1, 2)
    rows = []
    t0 = time.time()
    for cname, kw in CONDS.items():
        imgs = [synthetic_fisheye(seed=s, **GT, **kw) for s in seeds]
        for N in range(1, 16):
            for s, img in zip(seeds, imgs):
                r = vals_source(img, 40, N)
                ce, re_ = _err(r)
                rows.append(dict(sweep="N", cond=cname, N=N, threshold=40, seed=s, ok=r.ok, center_err=ce,
                                 radius_err=re_, pairs=len(r.distances), valid_pairs=len(r.valid_points) // 2,
                                 algo="source"))
        for thr in (5, 10, 20, 30, 40, 60, 80, 100, 120):
            for s, img in zip(seeds, imgs):
                for algo, fn in (("source", lambda: vals_source(img, thr, 5)),
                                 ("improved", lambda: vals_improved(img, thr))):
                    r = fn()
                    ce, re_ = _err(r)
                    rows.append(dict(sweep="threshold", cond=cname, N=5, threshold=thr, seed=s, ok=r.ok,
                                     center_err=ce, radius_err=re_, pairs=len(r.distances),
                                     valid_pairs=len(r.valid_points) // 2, algo=algo))
    print(f"   {len(rows)} runs in {time.time() - t0:.1f}s")
    savecsv(rows, "vals_E2_synthetic_sweeps.csv")

    fig, axs = plt.subplots(2, 2, figsize=(12, 7))
    for k, cname in enumerate(CONDS):
        rr = [r for r in rows if r["sweep"] == "N" and r["cond"] == cname]
        Ns = sorted({r["N"] for r in rr})
        med = [np.nanmedian([r["center_err"] for r in rr if r["N"] == n] or [np.nan]) for n in Ns]
        fr = [np.mean([not r["ok"] for r in rr if r["N"] == n]) for n in Ns]
        axs[0, 0].plot(Ns, med, marker="o", ms=4, color=C[k], label=cname)
        axs[1, 0].plot(Ns, fr, marker="o", ms=4, color=C[k], label=cname)
        for algo, ls in (("source", "-"), ("improved", "--")):
            rr = [r for r in rows if r["sweep"] == "threshold" and r["cond"] == cname and r["algo"] == algo]
            Ts = sorted({r["threshold"] for r in rr})
            med = [np.nanmedian([r["center_err"] for r in rr if r["threshold"] == t] or [np.nan]) for t in Ts]
            fr = [np.mean([not r["ok"] for r in rr if r["threshold"] == t]) for t in Ts]
            axs[0, 1].plot(Ts, med, ls=ls, marker="o", ms=4, color=C[k], label=f"{cname} [{algo}]" if algo == "source" else None)
            axs[1, 1].plot(Ts, fr, ls=ls, marker="o", ms=4, color=C[k])
    axs[0, 0].set(yscale="log", xlabel="N (2N scan directions), threshold=40", ylabel="median centre error (px)")
    axs[1, 0].set(xlabel="N", ylabel="failure rate")
    axs[0, 1].set(yscale="log", xlabel="threshold (N=5); dashed = improved VALS", ylabel="median centre error (px)")
    axs[1, 1].set(xlabel="threshold", ylabel="failure rate")
    axs[0, 0].legend(fontsize=7); axs[0, 1].legend(fontsize=7)
    fig.suptitle("VALS source port on SYNTHETIC fisheye images (GT cx=410.3, cy=297.6, r=260)")
    savefig(fig, "vals_E2_synthetic_sweeps.png")

    # illustrate one run of each condition
    fig, axs = plt.subplots(1, 5, figsize=(16, 3.4))
    for ax, (cname, kw) in zip(axs, CONDS.items()):
        img = synthetic_fisheye(seed=0, **GT, **kw)
        r = vals_source(img, 40, 5)
        ax.imshow(img, cmap="gray"); ax.set_title(cname, fontsize=9); ax.axis("off")
        if r.points:
            P = np.array(r.points); ax.plot(P[:, 0], P[:, 1], "o", ms=4, color=C[1])
        if r.valid_points:
            V = np.array(r.valid_points); ax.plot(V[:, 0], V[:, 1], "o", ms=4, color=C[2])
        if r.ok:
            t = np.linspace(0, 2 * np.pi, 200)
            ax.plot(r.center[0] + r.radius * np.cos(t), r.center[1] + r.radius * np.sin(t), color=C[0], lw=1.2)
        ax.text(5, 590, "ok" if r.ok else "FAILED", color="w", fontsize=8)
    fig.suptitle("orange = tangent points, green = kept by `distance < mean`, blue = fitted circle (N=5, t=40)")
    savefig(fig, "vals_E2_examples.png")
    return rows


# ----------------------------------------------------------------- E3 real images
def exp_vals_real():
    import cv2
    print("[E3] VALS on the repository's real images (no ground truth: stability only)")
    params = {1: (5, [23, 24]), 2: (5, [26, 27]), 3: (5, [20, 21, 22, 23, 24, 25, 26]),
              4: (5, [24, 25]), 5: (5, [46, 49]), 6: (5, [11, 12, 13])}   # ImagesForTest/valid_params.txt
    rows = []
    for k, (N, ts) in params.items():
        p = repo_path("ImagesForTest", str(k), "1.JPG")
        img = cv2.imread(p)
        if img is None:
            print("   missing", p); continue
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        for thr in sorted(set(ts + [10, 20, 30, 40, 60])):
            for algo in ("source", "improved"):
                r = vals_source(gray, thr, N) if algo == "source" else vals_improved(gray, thr)
                rows.append(dict(set=k, image=f"ImagesForTest/{k}/1.JPG", h=img.shape[0], w=img.shape[1], N=N,
                                 threshold=thr, listed_in_valid_params=thr in ts, algo=algo, ok=r.ok,
                                 cx=r.center[0] if r.ok else np.nan, cy=r.center[1] if r.ok else np.nan,
                                 r=r.radius if r.ok else np.nan, pairs=len(r.distances),
                                 valid_pairs=len(r.valid_points) // 2))
    savecsv(rows, "vals_E3_real_images.csv")
    summ = {}
    for k in params:
        for algo in ("source", "improved"):
            rr = [r for r in rows if r["set"] == k and r["algo"] == algo and r["ok"]]
            if rr:
                summ[f"set{k}_{algo}"] = dict(
                    cx_range=float(np.ptp([r["cx"] for r in rr])), cy_range=float(np.ptp([r["cy"] for r in rr])),
                    r_range=float(np.ptp([r["r"] for r in rr])), r_values=[r["r"] for r in rr],
                    thresholds=[r["threshold"] for r in rr])
    savejson(summ, "vals_E3_real_stability.json")
    return rows


if __name__ == "__main__":
    out = {"E1": exp_fits(), "E2": exp_vals_synth(), "E3": exp_vals_real()}
