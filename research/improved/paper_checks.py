"""Checks of specific statements in the journal paper (Paper/单幅圆形鱼眼图像的校正.pdf) used by
research/PAPER_REVISION.md.   python research/improved/paper_checks.py
-> results/metrics/paper_checks.json
  1. Table 1 (p.1445): radii, mean, pair midpoints (antipodality), Kasa fit of the kept / all pairs
  2. VALS as the paper describes it (per-line test, vals_paper.py) on the synthetic conditions of
     experiment E2 and on the real images (threshold stability)  -> the paper's robustness claim
  3. horizontal/vertical scale ratio k/h below the horizon for C2/C3/C4/optimal w -> the
     "cars are stretched" remark (p.1447)
"""
from __future__ import annotations

import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "experiments"))
from _common import REPO, MET  # noqa: E402
import cv2  # noqa: E402
from kasa import kasa_fit  # noqa: E402
from vals import synthetic_fisheye, vals_source  # noqa: E402
from vals_paper import vals_paper  # noqa: E402
from geometry import Axis, PI  # noqa: E402

# Table 1, p.1445: (scan-line angle deg, point 1, point 2, radius printed in the paper)
TABLE1 = [(0, (446, 6), (430, 881), 437.57), (30, (229, 109), (625, 834), 413.04), (60, (72, 270), (780, 692), 412.11),
          (90, (21, 469), (846, 467), 412.50), (120, (69, 665), (788, 258), 413.10), (150, (531, 25), (224, 823), 427.50)]
CONDS = {"clean": {}, "noisy(sigma=8)": dict(noise=8), "low_contrast": dict(inner=45, background=10, vignette=0.6, texture=10),
         "missing_edge": dict(missing_sector=(np.radians(200), np.radians(260))), "outlier_specks": dict(specks=4)}
GT = dict(cx=410.3, cy=297.6, r=260.0)


def table1():
    rows, mids = [], []
    for ang, a, b, rp in TABLE1:
        r = math.dist(a, b) / 2
        m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        rows.append(dict(angle=ang, radius_recomputed=round(r, 3), radius_paper=rp)); mids.append(m)
    mids = np.array(mids)
    med = np.median(mids, 0)
    for row, m in zip(rows, mids):
        row["midpoint"] = [float(x) for x in m]
        row["midpoint_dev_from_median_px"] = round(float(np.hypot(*(m - med))), 2)
    out = dict(rows=rows, mean_recomputed=round(float(np.mean([r["radius_recomputed"] for r in rows])), 3),
               mean_paper=419.30, median_midpoint=[float(x) for x in med])
    for name, idx in (("kasa_kept_pairs_2to5", [1, 2, 3, 4]), ("kasa_all_pairs", range(6))):
        P = np.array([p for i in idx for p in (TABLE1[i][1], TABLE1[i][2])], float)
        c = kasa_fit(P)
        res = np.hypot(P[:, 0] - c.cx, P[:, 1] - c.cy) - c.r
        out[name] = dict(cx=round(c.cx, 2), cy=round(c.cy, 2), r=round(c.r, 2), rms_residual=round(float(np.sqrt(np.mean(res ** 2))), 2))
    return out


def vals_claims():
    out = {"synthetic": {}, "real_threshold_range": {}}
    for cname, kw in CONDS.items():
        acc = {"paper_VALS": [], "source_VALS": []}
        for s in (0, 1, 2):
            img = synthetic_fisheye(seed=s, **GT, **kw)
            for name, fn in (("paper_VALS", vals_paper), ("source_VALS", vals_source)):
                for N in (3, 5):
                    v = fn(img, 40, N)
                    acc[name].append((N, math.hypot(v.center[0] - GT["cx"], v.center[1] - GT["cy"]) if v.ok else np.nan,
                                      abs(v.radius - GT["r"]) if v.ok else np.nan))
        out["synthetic"][cname] = {
            f"{name}_N{N}": dict(centre_err_max=float(np.nanmax([x[1] for x in v if x[0] == N])) if any(not np.isnan(x[1]) for x in v if x[0] == N) else None,
                                 radius_err_max=float(np.nanmax([x[2] for x in v if x[0] == N])) if any(not np.isnan(x[2]) for x in v if x[0] == N) else None,
                                 failures=int(sum(np.isnan(x[1]) for x in v if x[0] == N)))
            for name, v in acc.items() for N in (3, 5)}
    for k in range(1, 7):
        g = cv2.cvtColor(cv2.imread(os.path.join(REPO, "ImagesForTest", str(k), "1.JPG")), cv2.COLOR_BGR2GRAY)
        a = [[*v.center, v.radius] for v in (vals_paper(g, t, 5) for t in (10, 20, 30, 40, 60)) if v.ok]
        out["real_threshold_range"][f"set{k}"] = [round(float(x), 2) for x in np.ptp(np.array(a), 0)] if a else None
    return out


def stretch():
    maps = {"C2 equirect": (Axis("lin"), Axis("lin")), "C3 main": (Axis("lccp", PI / 2), Axis("lccp", PI / 2)),
            "C4 w=pi/2 (paper Eq.17)": (Axis("lin"), Axis("lccp", PI / 2)), "lin + LCCP w=1.81": (Axis("lin"), Axis("lccp", 1.81))}
    out = {}
    for name, (lo, la) in maps.items():
        out[name] = {f"psi={p},lam'={l}": round(float(lo.dfwd(np.radians(l)) / np.cos(np.radians(p)) / la.dfwd(np.radians(p))), 3)
                     for p, l in ((-30, 0), (-45, 0), (-60, 0), (-45, 45), (0, 60))}
    return out


if __name__ == "__main__":
    res = dict(table1=table1(), vals=vals_claims(), horizontal_stretch_k_over_h=stretch())
    with open(os.path.join(MET, "paper_checks.json"), "w") as f:
        json.dump(res, f, indent=1, ensure_ascii=False)
    print(json.dumps(res, indent=1, ensure_ascii=False))
