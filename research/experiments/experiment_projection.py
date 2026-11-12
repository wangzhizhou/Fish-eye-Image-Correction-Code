"""Experiment A: the four fisheye projection models of the source (camMode).

    python experiments/experiment_projection.py
"""
from __future__ import annotations

import numpy as np

from _common import plt, savefig, savejson, C
from fisheye_models import MODELS, focal_length, theta_to_p, p_to_theta, dp_dtheta


def main():
    print("[A] projection models")
    R = 1.0
    fov = np.pi
    th = np.linspace(0, fov / 2, 400)
    metrics = {"FOV=pi": {}}
    fig, axs = plt.subplots(1, 3, figsize=(13, 3.8))
    for k, m in enumerate(MODELS):
        f = focal_length(m, R, fov)
        p = theta_to_p(m, th, f)
        axs[0].plot(np.degrees(th), p / R, color=C[k], label=f"{m}  f={f:.4f}R")
        mag = dp_dtheta(m, th, f) / dp_dtheta(m, np.array([0.0]), f)
        axs[1].plot(np.degrees(th), mag, color=C[k], label=m)
        # inverse round trip
        rt = np.max(np.abs(p_to_theta(m, p, f) - th))
        metrics["FOV=pi"][m] = dict(f_over_R=float(f), p_at_FOVhalf_over_R=float(theta_to_p(m, fov / 2, f) / R),
                                    edge_to_centre_radial_scale=float(mag[-1]), inverse_max_err_rad=float(rt))
    axs[0].plot(np.degrees(th), np.tan(th) / np.tan(np.radians(80)), color="#888", ls=":", lw=1,
                label="rectilinear f tan(theta) (diverges at 90 deg)")
    axs[0].set(xlabel="incidence angle theta (deg)", ylabel="p / R", ylim=(0, 1.05),
               title="normalised p(theta), p(FOV/2)=R, FOV=180 deg")
    axs[0].legend(fontsize=7)
    axs[1].set(xlabel="theta (deg)", ylabel="(dp/dtheta) / (dp/dtheta at 0)",
               title="radial magnification relative to centre")
    axs[1].legend(fontsize=7)
    # FOV vs effective radius with a fixed focal length f = 1
    fovs = np.linspace(np.radians(60), np.pi, 200)
    metrics["R_for_f=1"] = {}
    for k, m in enumerate(MODELS):
        Rf = theta_to_p(m, fovs / 2, 1.0)
        axs[2].plot(np.degrees(fovs), Rf, color=C[k], label=m)
        metrics["R_for_f=1"][m] = {"FOV=120": float(theta_to_p(m, np.radians(60), 1.0)),
                                   "FOV=180": float(theta_to_p(m, np.pi / 2, 1.0))}
    axs[2].set(xlabel="field of view alpha (deg)", ylabel="effective radius R (units of f)",
               title="R = p(alpha/2) for a fixed focal length")
    axs[2].legend(fontsize=7)
    savefig(fig, "projection_A_models.png")
    savejson(metrics, "projection_A_models.json")


if __name__ == "__main__":
    main()
