"""T6 (improvement proposal): stitch circular fisheye shots directly on the unit sphere.

Instead of correcting each fisheye to a cylinder and feeding the results to cv::Stitcher (which
assumes pinhole images; program/main.cpp), each fisheye pixel is turned into a ray with the lens
model, the shots are related by pure rotations (tripod, fixed viewpoint), and the panorama is
rendered as a true 360 x 180 equirectangular image -- exactly what program/viewer.cpp assumes.

  1. SIFT keypoints inside each fisheye circle -> rays (lens model, circle).
  2. All image pairs: kNN ratio test (0.75) + mutual consistency (both are the rules described in
     the thesis, ch. 5.2.1) -> RANSAC rotation (Kabsch on 3 rays, inlier angle < 2 fisheye px).
  3. Global refinement (scipy least_squares, Huber): rotations of shots 1..n-1 and ONE shared focal
     length f (=> the lens field of view is estimated from the data: self-calibration, T4).
  4. Level the panorama with the pan axis, gain compensation, feathered blending, equirect output
     in the viewer's convention (row <-> acos(z_world), column <-> atan2(y_world, x_world)).
"""
from __future__ import annotations

import itertools
import math
from dataclasses import dataclass

import cv2
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation

from geometry import p_to_theta, focal, theta_to_p


@dataclass
class Shot:
    img: np.ndarray
    cx: float
    cy: float
    r: float


def _kabsch(A, B):
    """rotation R minimising sum |R b - a|^2  (rows of A, B are unit rays)"""
    Hm = B.T @ A
    U, _, Vt = np.linalg.svd(Hm)
    D = np.diag([1, 1, np.sign(np.linalg.det(Vt.T @ U.T))])
    return Vt.T @ D @ U.T


def _rays(p, alpha, lens, f):
    th = p_to_theta(lens, p, f)
    return np.stack([np.sin(th) * np.cos(alpha), np.sin(th) * np.sin(alpha), np.cos(th)], -1)


def features(shots, nfeat=6000, margin=6):
    sift = cv2.SIFT_create(nfeatures=nfeat)
    out = []
    for s in shots:
        g = cv2.cvtColor(s.img, cv2.COLOR_BGR2GRAY)
        mask = np.zeros_like(g)
        cv2.circle(mask, (int(round(s.cx)), int(round(s.cy))), int(s.r - margin), 255, -1)
        kp, des = sift.detectAndCompute(g, mask)
        pts = np.array([k.pt for k in kp], float)
        xc, yc = pts[:, 0] - s.cx, -(pts[:, 1] - s.cy)
        out.append(dict(p=np.hypot(xc, yc), a=np.arctan2(yc, xc), des=des, pts=pts))
    return out


def match_pairs(feats, ratio=0.75):
    bf = cv2.BFMatcher(cv2.NORM_L2)
    pairs = {}
    for i, j in itertools.combinations(range(len(feats)), 2):
        def one_way(a, b):
            m = bf.knnMatch(feats[a]["des"], feats[b]["des"], k=2)
            return {x.queryIdx: x.trainIdx for x, y in (mm for mm in m if len(mm) == 2) if x.distance < ratio * y.distance}
        ab, ba = one_way(i, j), one_way(j, i)
        mutual = [(q, t) for q, t in ab.items() if ba.get(t) == q]        # symmetric rule
        if len(mutual) >= 8:
            pairs[(i, j)] = np.array(mutual, int)
    return pairs


def ransac_rotation(a, b, thr, iters=3000, seed=0):
    rng = np.random.default_rng(seed)
    best = None
    for _ in range(iters):
        idx = rng.choice(len(a), 3, replace=False)
        R = _kabsch(a[idx], b[idx])
        ang = np.arccos(np.clip(np.sum((b @ R.T) * a, 1), -1, 1))
        inl = ang < thr
        if best is None or inl.sum() > best[1].sum():
            best = (R, inl)
    R = _kabsch(a[best[1]], b[best[1]])
    ang = np.arccos(np.clip(np.sum((b @ R.T) * a, 1), -1, 1))
    return R, ang < thr


def _solve(obs, n, lens, f0, x0, refine_f, scale):
    def unpack(x):
        Rs = [np.eye(3)] + [Rotation.from_rotvec(x[3 * k:3 * k + 3]).as_matrix() for k in range(n - 1)]
        return Rs, (f0 * math.exp(x[-1]) if refine_f else f0)

    def resid(x):
        Rs, f = unpack(x)
        return np.concatenate([(_rays(pi, ai, lens, f) @ Rs[i].T - _rays(pj, aj, lens, f) @ Rs[j].T).ravel()
                               for i, j, pi, ai, pj, aj in obs])

    sol = least_squares(resid, x0, loss="huber", f_scale=scale, x_scale="jac")
    return sol.x, unpack(sol.x)


def _angles(obs_all, Rs, lens, f):
    return [np.arccos(np.clip(np.sum((_rays(pi, ai, lens, f) @ Rs[i].T) * (_rays(pj, aj, lens, f) @ Rs[j].T), 1), -1, 1))
            for i, j, pi, ai, pj, aj in obs_all]


def calibrate(shots, lens="EQUIDISTANCE", fov0=math.pi, refine_f=True, feats=None, pairs=None, px_thr=2.0,
              loose_deg=1.5, eval_matches=None):
    """returns dict with rotations (camera k -> camera 0), f, fov, residual statistics.
    Stage 1: RANSAC per pair with a loose angular threshold (robust to a wrong initial f).
    Stage 2: global refinement; inliers re-selected at px_thr with the refined model; refined again.
    eval_matches: optional {(i,j): match array} on which the final residuals are ALSO reported
    (used to compare lens models on one common observation set)."""
    feats = feats or features(shots)
    pairs = pairs or match_pairs(feats)
    n = len(shots)
    r_mean = float(np.mean([s.r for s in shots]))
    f0 = focal(lens, r_mean, fov0)
    rel, inl = {}, {}
    for (i, j), m in pairs.items():
        a = _rays(feats[i]["p"][m[:, 0]], feats[i]["a"][m[:, 0]], lens, f0)
        b = _rays(feats[j]["p"][m[:, 1]], feats[j]["a"][m[:, 1]], lens, f0)
        R, ok = ransac_rotation(a, b, math.radians(loose_deg))
        if ok.sum() >= 15:
            rel[(i, j)], inl[(i, j)] = R, m[ok]
    Rabs = {0: np.eye(3)}
    while len(Rabs) < n:
        grown = False
        for (i, j), R in sorted(rel.items(), key=lambda kv: -len(inl[kv[0]])):
            if i in Rabs and j not in Rabs:
                Rabs[j] = Rabs[i] @ R; grown = True
            elif j in Rabs and i not in Rabs:
                Rabs[i] = Rabs[j] @ R.T; grown = True
        if not grown:
            raise RuntimeError(f"shots not connected: {sorted(set(range(n)) - set(Rabs))}")
    closure = None
    if all((k, k + 1) in rel for k in range(n - 1)) and (0, n - 1) in rel:
        C = np.eye(3)
        for k in range(n - 1):
            C = C @ rel[(k, k + 1)]
        C = C @ rel[(0, n - 1)].T
        closure = float(np.degrees(Rotation.from_matrix(C).magnitude()))

    mk = lambda mm: [(i, j, feats[i]["p"][m[:, 0]], feats[i]["a"][m[:, 0]], feats[j]["p"][m[:, 1]], feats[j]["a"][m[:, 1]])
                     for (i, j), m in mm.items()]
    x = np.concatenate([Rotation.from_matrix(Rabs[k]).as_rotvec() for k in range(1, n)] + [np.zeros(1)])
    x, (Rs, f) = _solve(mk(inl), n, lens, f0, x, refine_f, math.radians(loose_deg) / 3)
    # stage 2: re-select inliers among ALL mutual matches with the refined model
    for _ in range(2):
        allobs = mk(pairs)
        angs = _angles(allobs, Rs, lens, f)
        thr = px_thr / f
        new = {k: pairs[k][a < thr] for k, a in zip(pairs, angs) if (a < thr).sum() >= 15}
        if len(new) < n - 1:            # model cannot explain the data at px_thr: keep the loose set
            break
        inl = new
        x, (Rs, f) = _solve(mk(inl), n, lens, f0, x, refine_f, thr)
    angs = np.concatenate(_angles(mk(inl), Rs, lens, f))
    fov = 2 * float(p_to_theta(lens, r_mean, f))
    pool = np.concatenate(_angles(mk(pairs), Rs, lens, f)) * f          # every mutual match, in fisheye px
    within = {f"within_{t}px": int((pool < t).sum()) for t in (1, 2, 4)}
    w2 = pool[pool < 2]
    out = dict(lens=lens, R=Rs, f=f, f0=f0, fov_deg=math.degrees(fov), pairs={k: int(len(v)) for k, v in inl.items()},
               n_obs=int(angs.size), rms_deg=float(np.degrees(np.sqrt(np.mean(angs ** 2)))),
               median_deg=float(np.degrees(np.median(angs))), rms_px=float(np.sqrt(np.mean(angs ** 2)) * f),
               loop_closure_deg=closure, inliers=inl, feats=feats, matches=pairs,
               pool=int(pool.size), rms_within_2px=float(np.sqrt(np.mean(w2 ** 2))) if w2.size else None, **within)
    if eval_matches is not None:
        ea = np.concatenate(_angles(mk(eval_matches), Rs, lens, f))
        out.update(common_n=int(ea.size), common_rms_px=float(np.sqrt(np.mean(ea ** 2)) * f),
                   common_median_px=float(np.median(ea) * f))
    return out


def pan_axis_frame(Rs):
    """world frame: z = pan axis (up), x = horizontal component of shot 0's optical axis."""
    axes = []
    for R in Rs[1:]:
        rv = Rotation.from_matrix(R).as_rotvec()
        if np.linalg.norm(rv) > 1e-3:
            axes.append(rv / np.linalg.norm(rv))
    up = np.mean([a if a @ np.array([0, 1, 0]) > 0 else -a for a in axes], 0)
    up /= np.linalg.norm(up)
    zc = np.array([0.0, 0.0, 1.0])
    ex = zc - (zc @ up) * up; ex /= np.linalg.norm(ex)
    ey = np.cross(up, ex)
    return np.stack([ex, ey, up])            # rows: world axes expressed in camera-0 coordinates


def render(shots, cal, width=None, feather=True, gains=True, lens=None):
    lens = lens or cal["lens"]
    f, Rs = cal["f"], cal["R"]
    width = width or int(round(2 * math.pi * f))
    width += width % 2
    H, W = width // 2, width
    Mw = pan_axis_frame(Rs)                   # world <- cam0
    lon = (np.arange(W) + 0.5) / W * 2 * math.pi
    lat = (np.arange(H) + 0.5) / H * math.pi  # colatitude from +z (viewer convention)
    dw = np.stack([np.sin(lat)[:, None] * np.cos(lon)[None, :], np.sin(lat)[:, None] * np.sin(lon)[None, :],
                   np.cos(lat)[:, None] * np.ones(W)[None, :]], -1)
    d0 = dw @ Mw                              # world -> cam0 coordinates
    acc = np.zeros((H, W, 3)); wsum = np.zeros((H, W)); warped = []
    for s, R in zip(shots, Rs):
        dc = d0 @ R                           # cam0 -> cam k  (R maps cam k -> cam0)
        th = np.arccos(np.clip(dc[..., 2], -1, 1))
        a = np.arctan2(dc[..., 1], dc[..., 0])
        p = theta_to_p(lens, th, f)
        valid = p <= s.r - 2
        mx = (s.cx + p * np.cos(a)).astype(np.float32)
        my = (s.cy - p * np.sin(a)).astype(np.float32)
        im = cv2.remap(s.img, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT).astype(float)
        wgt = np.where(valid, np.clip(1 - p / s.r, 0, 1) if feather else 1.0, 0.0)
        warped.append((im, valid, wgt))
    g = np.ones(len(shots))
    if gains:   # Brown & Lowe gain compensation: sum N_ij[(g_i I_ij - g_j I_ji)^2/sN^2 + (1-g_i)^2/sg^2]
        sN, sg = 10.0, 0.1
        A = np.zeros((len(shots), len(shots))); bvec = np.zeros(len(shots))
        for i, j in itertools.permutations(range(len(shots)), 2):
            ov = warped[i][1] & warped[j][1]
            N = float(ov.sum())
            if N < 1000:
                continue
            Ii, Ij = warped[i][0][ov].mean(), warped[j][0][ov].mean()
            A[i, i] += N * (Ii * Ii / sN ** 2 + 1 / sg ** 2)
            A[i, j] -= N * Ii * Ij / sN ** 2
            bvec[i] += N / sg ** 2
        if np.all(np.diag(A) > 0):
            g = np.linalg.solve(A, bvec)
    for (im, valid, wgt), gk in zip(warped, g):
        acc += im * gk * wgt[..., None]; wsum += wgt
    pano = np.where(wsum[..., None] > 0, acc / np.maximum(wsum, 1e-9)[..., None], 0)
    # seam consistency: mean abs difference of the gain-compensated pairs on their overlaps
    diffs, dpairs = [], []
    for i, j in itertools.combinations(range(len(shots)), 2):
        ov = warped[i][1] & warped[j][1]
        if ov.sum() > 1000:
            diffs.append(float(np.abs(warped[i][0][ov] * g[i] - warped[j][0][ov] * g[j]).mean()))
            dpairs.append([i, j])
    coverage = float((wsum > 0).mean())
    return np.clip(pano, 0, 255).astype(np.uint8), dict(gains=[float(x) for x in g], overlap_mad=diffs, overlap_pairs=dpairs,
                                                         overlap_mad_mean=float(np.mean(diffs)) if diffs else None,
                                                         coverage=coverage, size=[W, H])
