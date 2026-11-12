"""Experiments B and C + numerical studies of getPhi / auxFunc / getPhi1.

  B  LCCP latitude-compression curves for w in {pi/6, pi/4, pi/3, pi/2, 2pi/3}
  B2 accuracy / iterations of the source bisections vs closed forms
  B3 static-cache bug demonstration (func1 / getPhi1)
  C  Correction2/3/4 sampling grids projected onto the fisheye disc + Jacobian density

    python experiments/experiment_lccp.py
"""
from __future__ import annotations

import math

import numpy as np

from _common import plt, savefig, savejson, C, INK2
from lccp import (PI, aux_func_source, aux_func_closed, lccp_h, lccp_v_norm, get_phi_source,
                  get_phi_closed, SourceStatics, get_phi1_closed, get_phi1_source, W_MAX, d_aux_d_psi)
from correction import c2_latlon, c3_latlon, c4_latlon, maps_from_latlon, jacobian_area

WS = {"pi/6": PI / 6, "pi/4": PI / 4, "pi/3": PI / 3, "pi/2": PI / 2, "2pi/3": 2 * PI / 3}


def exp_B():
    print("[B] LCCP latitude curves")
    phi = np.linspace(0, PI, 2001)
    psi = np.degrees(PI / 2 - phi)
    out = {"domain": "w in (0, 3pi/4); all five requested w are valid", "per_w": {}}
    fig, axs = plt.subplots(1, 3, figsize=(15, 4.2))
    fig.subplots_adjust(wspace=0.3)
    for k, (name, w) in enumerate(WS.items()):
        assert 0 < w < W_MAX
        src = aux_func_source(w, phi)
        clo = aux_func_closed(w, phi)
        v = lccp_v_norm(phi, w)
        axs[0].plot(psi, v, color=C[k], label=f"w={name}  h={lccp_h(w):.4f}")
        scale = d_aux_d_psi(w, np.radians(psi)) / (2 * lccp_h(w))     # dv/dpsi (fraction of H per rad)
        axs[1].plot(psi, scale / scale[len(scale) // 2], color=C[k], label=f"w={name}")
        dense = aux_func_source(w, np.linspace(0, PI, 200001))
        out["per_w"][name] = dict(
            w=w, h_source=float(aux_func_source(w, 0.0)), h_closed=float(lccp_h(w)),
            h_paper=float(math.sqrt(2) * math.sin(w) / math.sin(3 * PI / 4 - w)),
            max_abs_source_minus_closed=float(np.nanmax(np.abs(src - clo))),
            strictly_decreasing_in_phi=bool(np.all(np.diff(dense) < 0)),
            continuity_at_equator=float(abs(aux_func_source(w, PI / 2 - 1e-9) - aux_func_source(w, PI / 2 + 1e-9))),
            pole_to_equator_vertical_scale=float(math.sin(w) ** 2 / math.sin(w + PI / 4) ** 2),
            second_derivative_jump_at_equator=float(2 / math.tan(w)),   # |f''(0+) - f''(0-)| = 2 cot w
            aux_at_phi_pi_over_2=float(aux_func_source(w, PI / 2)), aux_at_phi_pi=float(aux_func_source(w, PI)))
    axs[0].plot(psi, (90 - psi) / 180, color="#888", ls=":", lw=1.5, label="equirectangular (Correction2)")
    axs[0].set(xlabel="latitude psi = 90deg - phi (deg)", ylabel="output row v/H  (0 = top)",
               title="v/H = (h - aux) / 2h  (Eq. 17)")
    axs[0].invert_yaxis(); axs[0].legend(fontsize=7)
    axs[1].set(xlabel="latitude (deg)", ylabel="vertical scale / scale at equator",
               title="local vertical stretch (rel. to equator)", yscale="log")
    axs[1].axhline(1, color=INK2, lw=0.6)
    axs[1].legend(fontsize=7)
    ww = np.linspace(0.05, W_MAX - 0.02, 400)
    axs[2].plot(np.degrees(ww), [lccp_h(x) for x in ww], color=C[0], label="h(w)")
    axs[2].plot(np.degrees(ww), [math.sin(x) ** 2 / math.sin(x + PI / 4) ** 2 for x in ww], color=C[1],
                label="pole/equator vertical scale")
    axs[2].axvline(67.5, color=INK2, lw=0.6, ls="--"); axs[2].text(68.5, 6, "w=3pi/8: ratio 1", fontsize=7)
    axs[2].axvline(135, color=C[7], lw=0.8); axs[2].text(118, 12, "w=3pi/4\n(h -> inf)", fontsize=7, color=C[7])
    axs[2].set(xlabel="w (deg)", yscale="log", title="h(w), pole/equator stretch")
    axs[2].legend(fontsize=7)
    savefig(fig, "lccp_B_latitude_curves.png")
    w_eq = 3 * PI / 8
    out["w_equal_pole_equator_scale"] = dict(w=w_eq, deg=67.5, ratio=math.sin(w_eq) ** 2 / math.sin(w_eq + PI / 4) ** 2)
    # outside the legal domain: what the source formula returns
    out["illegal_w"] = {f"{x:.4f}": dict(aux_w_0=float(aux_func_source(x, 0.0)),
                                       aux_w_pi_over_8=float(aux_func_source(x, PI / 8)))
                        for x in (3 * PI / 4, 5 * PI / 6, PI, 0.0)}
    return out


def exp_B2():
    print("[B2] bisection accuracy (source) vs closed forms")
    res = {}
    fig, axs = plt.subplots(1, 2, figsize=(12, 3.8))
    ls = np.linspace(0, 4, 4001)[:-1]
    infos = [get_phi_source(l) for l in ls]
    err = np.abs(np.array([i.phi for i in infos]) - get_phi_closed(ls))
    axs[0].semilogy(ls, err + 1e-17, color=C[0], lw=1, label="getPhi (w=pi/2, Correction3)")
    k = int(np.argmax(err))
    res["getPhi"] = dict(max_err_rad=float(err.max()), at_l=float(ls[k]), median_err=float(np.median(err)),
                         max_iter=int(max(i.iterations for i in infos)),
                         err_in_fisheye_px_for_R623=float(err.max() * 623 / (PI / 2)),
                         err_in_output_rows_H1920=float(err.max() / (PI / 2) * 1920 / 4 * 1.0))
    res["getPhi_nonconvergence"] = {str(l): dict(converged=get_phi_source(l, max_iter=20000).converged)
                                    for l in (-1.0, 4.0, 4.5, 5.0)}
    for kk, (name, w) in enumerate(WS.items()):
        h = lccp_h(w)
        lw = np.linspace(0, 2 * h, 3001)[:-1]
        inf = [get_phi1_source(l, w, return_info=True) for l in lw]
        e = np.abs(np.array([i.phi for i in inf]) - get_phi1_closed(lw, w))
        axs[0].semilogy(lw / h * 2, e + 1e-17, color=C[kk + 1], lw=1, label=f"getPhi1 w={name}")
        res[f"getPhi1_w={name}"] = dict(max_err_rad=float(e.max()), median_err=float(np.median(e)),
                                       max_iter=int(max(i.iterations for i in inf)),
                                       all_converged=bool(all(i.converged for i in inf)))
    axs[0].set(xlabel="l (getPhi)  /  2 l / h(w) (getPhi1), i.e. 0..4 = top..bottom",
               ylabel="|phi_bisection - phi_exact| (rad)",
               title="bisection error, LIMIT = 1e-4 on |f|, not on phi")
    axs[0].legend(fontsize=7)
    # why: func near l=2 has a double root at pi/2
    pp = np.linspace(1.3, 1.85, 400)
    for l, c in ((1.9, C[0]), (1.99, C[1]), (2.0, C[2])):
        axs[1].plot(pp, (l / 2 - 1) * np.cos(pp) - np.sin(pp) + 1, color=c, label=f"func(l={l}, phi)")
    axs[1].axhspan(-1e-4, 1e-4, color=C[3], alpha=0.35, label="|f| <= LIMIT")
    axs[1].axvline(PI / 2, color=INK2, lw=0.6)
    axs[1].set(xlabel="phi (rad)", ylim=(-0.01, 0.02), title="func has roots 2atan(l/(4-l)) AND pi/2")
    axs[1].legend(fontsize=7)
    savefig(fig, "lccp_B2_bisection_accuracy.png")
    return res


def exp_B3():
    print("[B3] static local cache in func1/getPhi1")
    st = SourceStatics()
    first_w, second_w = PI / 2, PI / 4
    H = 512
    _ = c4_latlon(H, H, first_w, statics=st)          # first image corrected with w = pi/2
    phi_stale, _ = c4_latlon(H, H, second_w, statics=st)   # then w = pi/4 in the same process
    phi_fresh, _ = c4_latlon(H, H, second_w, source_like=False)
    err = np.abs(phi_stale - phi_fresh)
    fig, ax = plt.subplots(figsize=(6, 3.6))
    ax.plot(np.arange(H), np.degrees(phi_fresh), color=C[0], label="w=pi/4, fresh process")
    ax.plot(np.arange(H), np.degrees(phi_stale), color=C[1], label="w=pi/4 after a w=pi/2 call (stale statics)")
    ax.set(xlabel="output row j", ylabel="colatitude phi (deg)", title="Correction4: static cache bug")
    ax.legend(fontsize=7)
    savefig(fig, "lccp_B3_static_cache_bug.png")
    return dict(first_w=first_w, second_w=second_w, cached_limit=st.getphi1_lim, correct_limit=lccp_h(second_w),
                max_row_latitude_error_deg=float(np.degrees(err.max())),
                rows_with_error_gt_1deg=int((np.degrees(err) > 1).sum()))


def exp_C():
    print("[C] sampling grids Correction2 / 3 / 4")
    S = 512
    cfgs = {
        "Correction2 (equirect.)": c2_latlon(S, S),
        "Correction3 (Braun lat+lon)": c3_latlon(S, S, source_like=False),
        "Correction4 w=pi/2": c4_latlon(S, S, PI / 2, source_like=False),
        "Correction4 w=pi/4": c4_latlon(S, S, PI / 4, source_like=False),
    }
    R = 1.0
    fig, axs = plt.subplots(2, 4, figsize=(16, 8))
    stats = {}
    t = np.linspace(0, 2 * PI, 400)
    for k, (name, (phi, lam)) in enumerate(cfgs.items()):
        mu, mv = maps_from_latlon(phi, lam, 0.0, 0.0, R, fast=False)
        ax = axs[0, k]
        ax.plot(np.cos(t), np.sin(t), color=INK2, lw=0.8)
        step = S // 16
        for j in list(range(0, S, step)) + [S - 1]:
            ax.plot(mu[j, :], mv[j, :], color=C[0], lw=0.7)
        for i in list(range(0, S, step)) + [S - 1]:
            ax.plot(mu[:, i], mv[:, i], color=C[1], lw=0.7)
        ax.set_aspect("equal"); ax.invert_yaxis(); ax.set_title(name, fontsize=9); ax.axis("off")
        A = jacobian_area(mu, mv) * S * S / (PI * R * R)     # 1 == uniform sampling of the disc area
        rr = np.hypot(mu, mv)
        im = axs[1, k].imshow(np.log2(np.clip(A, 1e-3, None)), cmap="RdBu_r", vmin=-4, vmax=4)
        axs[1, k].set_title("log2(fisheye area per output px), normalised", fontsize=8); axs[1, k].axis("off")
        du = np.hypot(np.gradient(mu, axis=1), np.gradient(mv, axis=1))
        dv = np.hypot(np.gradient(mu, axis=0), np.gradient(mv, axis=0))
        stats[name] = dict(
            density_centre_r_lt_0_2=float(np.median(A[rr < 0.2])),
            density_mid_0_5_0_7=float(np.median(A[(rr > 0.5) & (rr < 0.7)])),
            density_edge_r_gt_0_9=float(np.median(A[rr > 0.9])),
            density_pole_rows_top5pct=float(np.median(A[: S // 20, S // 4: 3 * S // 4])),
            horizontal_step_centre_over_edge=float(np.median(du[S // 2 - 5:S // 2 + 5, S // 2 - 5:S // 2 + 5]) /
                                                   np.median(du[S // 2 - 5:S // 2 + 5, :10])),
            vertical_step_centre_over_pole=float(np.median(dv[S // 2 - 5:S // 2 + 5, S // 2 - 5:S // 2 + 5]) /
                                                 np.median(dv[:10, S // 2 - 5:S // 2 + 5])),
            pole_row_collapse_px_for_R623=float(623 * np.hypot(mu[0, -1] - mu[0, 0], mv[0, -1] - mv[0, 0])),
        )
    fig.colorbar(im, ax=axs[1, :].tolist(), shrink=0.7, label="log2 relative density (blue = output over-samples source -> stretch/blur)")
    fig.suptitle("Output grid (every 32 px of a 512x512 output) projected onto the unit fisheye disc (EQUIDISTANCE, FOV=180)")
    savefig(fig, "lccp_C_sampling_grids.png")
    return stats


if __name__ == "__main__":
    out = {"B": exp_B(), "B2_bisection": exp_B2(), "B3_static_cache": exp_B3(), "C_sampling": exp_C()}
    savejson(out, "lccp_BC.json")
