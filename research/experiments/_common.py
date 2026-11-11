"""Shared paths, plotting style and IO for all experiments."""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RESEARCH = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(RESEARCH, "src"))

# repository root (research/ lives inside the repo); override with FISHEYE_REPO
REPO = os.environ.get("FISHEYE_REPO", os.path.abspath(os.path.join(RESEARCH, "..")))
FIG = os.path.join(RESEARCH, "results", "figures")
MET = os.path.join(RESEARCH, "results", "metrics")
os.makedirs(FIG, exist_ok=True)
os.makedirs(MET, exist_ok=True)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

# validated categorical order (dataviz reference palette, light mode)
C = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"

plt.rcParams.update({
    "figure.dpi": 110, "savefig.dpi": 140, "savefig.bbox": "tight",
    "axes.edgecolor": INK2, "axes.labelcolor": INK, "axes.titlesize": 11,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
    "axes.spines.top": False, "axes.spines.right": False,
    "xtick.color": INK2, "ytick.color": INK2, "lines.linewidth": 2,
    "legend.frameon": False, "font.size": 9,
    "axes.prop_cycle": matplotlib.cycler(color=C),
})


def savefig(fig, name):
    path = os.path.join(FIG, name)
    fig.savefig(path)
    plt.close(fig)
    print("  figure ->", os.path.relpath(path, RESEARCH))
    return path


def savejson(obj, name):
    path = os.path.join(MET, name)
    with open(path, "w") as fh:
        json.dump(obj, fh, indent=2, ensure_ascii=False, default=float)
    print("  metrics ->", os.path.relpath(path, RESEARCH))
    return path


def savecsv(rows, name):
    import csv
    path = os.path.join(MET, name)
    if not rows:
        return path
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("  metrics ->", os.path.relpath(path, RESEARCH))
    return path


def repo_path(*p):
    return os.path.join(REPO, *p)
