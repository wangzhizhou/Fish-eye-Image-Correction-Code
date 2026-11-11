"""VALS exactly as the JOURNAL PAPER describes it (p.1445), for evaluating the paper's own claims.

Differences from the source port `vals.vals_source` (program/findCircleParameter.cpp):
  * oblique scan lines: the test "max - min on the SAME scan line > threshold" is evaluated per
    line (the source accumulates max/min over all previous lines, REPORT BUG-11);
  * the Kasa result is kept as floats (paper Eq.3; the source truncates to int, BUG-08).
Everything else (2N directions theta_n = pi n / (2N), tangent point = brightest pixel of the first
line that passes the test, "discard pairs whose radius is above the mean", Kasa Eq.1-3) follows
the paper and is shared with the source port.
"""
from __future__ import annotations

import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from vals import _scan_rows, _scan_cols, ValsResult  # noqa: E402
from kasa import kasa_fit  # noqa: E402


def _scan_oblique_per_line(gray, theta, thr, which):
    H, W = gray.shape
    t = math.tan(theta)
    if which == "A":
        irange, jr, fy = range(0, W), (lambda i: range(0, i + 1)), (lambda x, i: -t * (x - i))
    elif which == "B":
        irange, jr, fy = range(W - 1, -1, -1), (lambda i: range(i, W)), (lambda x, i: H - 1 - t * (x - i))
    elif which == "C":
        irange, jr, fy = range(0, W), (lambda i: range(0, i + 1)), (lambda x, i: H - 1 - t * (x - i))
    else:  # "D"
        irange, jr, fy = range(W - 1, -1, -1), (lambda i: range(i, W)), (lambda x, i: -t * (x - i))
    for i in irange:
        xs = np.fromiter(jr(i), dtype=np.int64)
        if xs.size == 0:
            continue
        ys = np.trunc(fy(xs.astype(float), i)).astype(np.int64)
        ok = (xs >= 0) & (xs < W) & (ys >= 0) & (ys < H)
        xs, ys = xs[ok], ys[ok]
        if xs.size == 0:
            continue
        v = gray[ys, xs].astype(np.int64)
        if int(v.max()) - int(v.min()) > thr:                 # same scan line only
            k = int(np.argmax(v))
            return (int(xs[k]), int(ys[k]))
    return None


def vals_paper(gray: np.ndarray, threshold: int = 40, N: int = 5) -> ValsResult:
    points, distance, angles = [], [], []
    for n in range(2 * N):
        theta = math.pi * n / (2 * N)
        if n == 0:
            p1, p2 = _scan_rows(gray, threshold, False), _scan_rows(gray, threshold, True)
        elif 0 < n < N:
            p1, p2 = _scan_oblique_per_line(gray, theta, threshold, "A"), _scan_oblique_per_line(gray, theta, threshold, "B")
        elif n == N:
            p1, p2 = _scan_cols(gray, threshold, False), _scan_cols(gray, threshold, True)
        else:
            p1, p2 = _scan_oblique_per_line(gray, theta, threshold, "C"), _scan_oblique_per_line(gray, theta, threshold, "D")
        if p1 is not None and p2 is not None:
            points += [p1, p2]
            distance.append(math.hypot(p1[0] - p2[0], p1[1] - p2[1]))
            angles.append(theta)
    res = ValsResult(False, None, None, None, points=points, distances=distance, angles_used=angles)
    if not distance:
        res.message = "no complete tangent pair"
        return res
    mean = sum(distance) / len(distance)
    valid = [points[k] for i, d in enumerate(distance) if d < mean for k in (2 * i, 2 * i + 1)]
    res.valid_points, res.mean_distance = valid, mean
    if len(valid) <= 2:
        res.message = "Kasa needs > 2 points"
        return res
    c = kasa_fit(np.array(valid, float))
    res.ok, res.center, res.radius, res.center_float = bool(c.ok), (c.cx, c.cy), c.r, (c.cx, c.cy, c.r)
    return res
