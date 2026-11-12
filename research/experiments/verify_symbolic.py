"""Symbolic (SymPy) + high-precision (mpmath, 50 digits) verification of every closed
form used in REPORT.md.  Constraint #1 of the task: no formula is reported unless it
passes here.

Run:  python experiments/verify_symbolic.py
Writes results/metrics/symbolic_verification.json and exits non-zero on any failure.
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "results", "metrics", "symbolic_verification.json")

try:
    import sympy as sp
    import mpmath as mp
except ImportError:  # do not fake results
    print("SymPy/mpmath not installed -> symbolic verification NOT run. `pip install sympy`")
    sys.exit(2)

results = []


def check(name, expr_zero, assumptions_note="", numeric_subs=None):
    """expr_zero must simplify to 0. If simplify can't prove it, fall back to 50-digit
    evaluation at many random points and report the method used."""
    z = sp.simplify(sp.trigsimp(sp.expand_trig(expr_zero)))
    method = "sympy.simplify"
    ok = z == 0
    maxerr = None
    if not ok and numeric_subs is not None:
        method = "mpmath 50-digit random sampling (simplify inconclusive)"
        mp.mp.dps = 50
        f = sp.lambdify(list(numeric_subs[0].keys()), expr_zero, "mpmath")
        maxerr = mp.mpf(0)
        for subs in numeric_subs:
            v = f(*[mp.mpf(str(x)) for x in subs.values()])
            maxerr = max(maxerr, abs(v))
        ok = maxerr < mp.mpf("1e-40")
    results.append({"name": name, "ok": bool(ok), "method": method,
                    "residual": str(z) if method == "sympy.simplify" else str(maxerr),
                    "assumptions": assumptions_note})
    print(("PASS " if ok else "FAIL ") + name + f"   [{method}]")
    return ok


def rand_points(syms, ranges, n=200, seed=1):
    import random
    rnd = random.Random(seed)
    return [{s: rnd.uniform(*ranges[s]) for s in syms} for _ in range(n)]


x, y, a, b, r = sp.symbols("x y a b r", real=True)
p1, p2, p3 = 2 * a, 2 * b, r ** 2 - a ** 2 - b ** 2

# ---------------------------------------------------------------- Kasa
check("Kasa: (x-a)^2+(y-b)^2-r^2 == x^2+y^2-(p1 x+p2 y+p3)",
      (x - a) ** 2 + (y - b) ** 2 - r ** 2 - (x ** 2 + y ** 2 - (p1 * x + p2 * y + p3)))
check("Kasa: r^2 == (p1^2+p2^2)/4 + p3", r ** 2 - ((p1 ** 2 + p2 ** 2) / 4 + p3))

# ---------------------------------------------------------------- projection models
R, F, th = sp.symbols("R F theta", positive=True)
models = {
    "STEREOGRAPHIC": (lambda f, t: 2 * f * sp.tan(t / 2), R / (2 * sp.tan(F / 4)), lambda f, p: 2 * sp.atan(p / (2 * f))),
    "EQUIDISTANCE": (lambda f, t: f * t, R / (F / 2), lambda f, p: p / f),
    "EQUISOLID": (lambda f, t: 2 * f * sp.sin(t / 2), R / (2 * sp.sin(F / 4)), lambda f, p: 2 * sp.asin(p / (2 * f))),
    "ORTHOGONAL": (lambda f, t: f * sp.sin(t), R / sp.sin(F / 2), lambda f, p: sp.asin(p / f)),
}
for name, (fwd, foc, inv) in models.items():
    check(f"{name}: p(FOV/2) with source focal length == R", fwd(foc, F / 2) - R)
    pts = rand_points([th, F], {th: (0.01, 1.5), F: (1.0, 3.14)})
    pts = [{th: d[th] * d[F] / 3.2, F: d[F]} for d in pts]       # theta < FOV/2
    check(f"{name}: inverse(forward(theta)) == theta  (0<theta<=FOV/2<=pi/2)",
          inv(foc, fwd(foc, th)) - th, "theta in (0, FOV/2]", numeric_subs=[{th: d[th], F: d[F], R: 1.0} for d in pts])
# 180 deg normalisation
for name, (fwd, foc, inv) in models.items():
    check(f"{name}: FOV=pi focal length value", sp.simplify(foc.subs(F, sp.pi)) -
          {"STEREOGRAPHIC": R / 2, "EQUIDISTANCE": 2 * R / sp.pi, "EQUISOLID": R / sp.sqrt(2), "ORTHOGONAL": R}[name])

# ---------------------------------------------------------------- getPhi
l, phi, w, A = sp.symbols("l phi w a", real=True)
func = (l / 2 - 1) * sp.cos(phi) - sp.sin(phi) + 1
check("getPhi: phi = pi/2 is a root of func for every l (spurious root)", func.subs(phi, sp.pi / 2))
phi_star = 2 * sp.atan(l / (4 - l))
check("getPhi: phi* = 2 atan(l/(4-l)) is a root of func", func.subs(phi, phi_star),
      "l in [0,4)", numeric_subs=[{l: v} for v in [0.01 * k for k in range(1, 399)]])
check("getPhi forward map: l(phi) = 2 - 2 tan(pi/4 - phi/2) solves func",
      func.subs(l, 2 - 2 * sp.tan(sp.pi / 4 - phi / 2)),
      "phi in [0,pi), phi != pi/2 numerically", numeric_subs=[{phi: v} for v in [0.0123 * k for k in range(1, 255) if abs(0.0123 * k - 1.5708) > 1e-3]])
# derivative of func at the root near pi/2 vanishes as l->2 (double root)
check("getPhi: func(2, phi) == 1 - sin(phi)  (double root at pi/2 when l=2)", func.subs(l, 2) - (1 - sp.sin(phi)))

# ---------------------------------------------------------------- auxFunc
aux_src = sp.sin(w) * sp.sqrt(sp.cos(phi) ** 2 + (1 - sp.sin(phi)) ** 2) / \
    sp.sin(sp.pi - w - sp.atan((1 - sp.sin(phi)) / sp.Abs(sp.cos(phi))))
aux_closed = 2 * sp.sin(w) * sp.sin(A) / sp.sin(w + A)
# northern hemisphere phi = pi/2 - 2a, a in (0, pi/4]
north = aux_src.subs(phi, sp.pi / 2 - 2 * A)
south = aux_src.subs(phi, sp.pi / 2 + 2 * A)    # magnitude; the source then negates it (if phi > PI/2)
grid = [{w: 0.05 + 2.25 * i / 23, A: 0.001 + 0.784 * j / 19} for i in range(24) for j in range(20)]
check("auxFunc north: equals 2 sin w sin a / sin(w+a), phi = pi/2-2a", north - aux_closed,
      "w in (0,3pi/4), a in (0,pi/4]", numeric_subs=grid)
check("auxFunc south: |aux| equals 2 sin w sin a / sin(w+a) at phi = pi/2+2a (source applies the minus sign)", south - aux_closed,
      "w in (0,3pi/4), a in (0,pi/4]", numeric_subs=grid)
check("sub-identity: sqrt(cos^2 phi + (1-sin phi)^2) == 2 sin a", sp.sqrt(sp.cos(sp.pi / 2 - 2 * A) ** 2 +
      (1 - sp.sin(sp.pi / 2 - 2 * A)) ** 2) - 2 * sp.sin(A), "a in (0, pi/4]",
      numeric_subs=[{A: 0.001 + 0.784 * j / 99} for j in range(100)])
check("sub-identity: (1 - sin phi)/|cos phi| == tan a", (1 - sp.sin(sp.pi / 2 - 2 * A)) / sp.cos(sp.pi / 2 - 2 * A) - sp.tan(A))
check("w = pi/2: aux == 2 tan(a) (Braun)", aux_closed.subs(w, sp.pi / 2) - 2 * sp.tan(A))
check("tan form: 2 sin w sin a/sin(w+a) == 2 tan a / (1 + cot w tan a)", aux_closed - 2 * sp.tan(A) / (1 + sp.cot(w) * sp.tan(A)))
h = aux_closed.subs(A, sp.pi / 4)
check("h(w) = aux(w,0) == 2 sin w/(sin w + cos w)", h - 2 * sp.sin(w) / (sp.sin(w) + sp.cos(w)))
check("h(w) == sqrt(2) sin w / sin(3pi/4 - w)   (paper Eq.17)", h - sp.sqrt(2) * sp.sin(w) / sp.sin(3 * sp.pi / 4 - w))
check("d aux/da == 2 sin^2 w / sin^2(w+a)  (>0 => strictly monotone)", sp.diff(aux_closed, A) - 2 * sp.sin(w) ** 2 / sp.sin(w + A) ** 2)
check("w=pi/2: aux(pi/2,phi) == 2 - l_getPhi(phi) i.e. getPhi is LCCP(pi/2)",
      aux_closed.subs(w, sp.pi / 2) - (2 - (2 - 2 * sp.tan(A))))
s_ = sp.symbols("s", positive=True)
a_inv = sp.atan(s_ * sp.sin(w) / (2 * sp.sin(w) - s_ * sp.cos(w)))
check("inverse: aux(w, a_inv(s)) == s", aux_closed.subs(A, a_inv) - s_, "0<s<=h(w)",
      numeric_subs=[{w: g[w], s_: (0.001 + 0.998 * k / 9) * float(h.subs(w, g[w]))} for g in grid[::12] for k in range(10)])
check("func == (cos phi / 2) * func1(w=pi/2)  (northern branch, phi=pi/2-2a)",
      func.subs(phi, sp.pi / 2 - 2 * A) - sp.cos(sp.pi / 2 - 2 * A) / 2 * (l - 2 + aux_closed.subs(w, sp.pi / 2)),
      "a in (0, pi/4], l in [0, 4)", numeric_subs=[{l: 0.07 * i, A: 0.001 + 0.78 * j / 19} for i in range(57) for j in range(20)])

# ---------------------------------------------------------------- coordinate chain
ph, la = sp.symbols("phi lam", positive=True)
X, Y, Z = -sp.sin(ph) * sp.cos(la), sp.cos(ph), sp.sin(ph) * sp.sin(la)
check("latlon->xyz is on the unit sphere", X ** 2 + Y ** 2 + Z ** 2 - 1)
check("acos(y) recovers phi", sp.acos(Y) - ph, "phi in (0,pi)",
      numeric_subs=[{ph: 0.01 + 3.12 * k / 50, la: 1.0} for k in range(51)])
check("atan2(z,-x) recovers lam", sp.atan2(Z, -X) - la, "phi in (0,pi), lam in (0,pi)",
      numeric_subs=[{ph: 0.01 + 3.12 * i / 9, la: 0.01 + 3.12 * j / 9} for i in range(10) for j in range(10)])

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w") as fh:
    json.dump({"sympy": sp.__version__, "mpmath": mp.__version__, "checks": results}, fh, indent=2, ensure_ascii=False)
n_fail = sum(not r["ok"] for r in results)
print(f"\n{len(results) - n_fail}/{len(results)} checks passed -> {OUT}")
sys.exit(1 if n_fail else 0)
