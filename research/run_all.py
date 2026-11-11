"""Run every experiment and the test-suite.  python run_all.py [--quick]
Set FISHEYE_REPO if research/ is not inside the repository (images are read from there)."""
import subprocess, sys, os, time
HERE = os.path.dirname(os.path.abspath(__file__))
steps = ["experiment_projection.py", "experiment_lccp.py", "experiment_roundtrip.py",
         "experiment_real.py", "experiment_vals.py", "verify_symbolic.py"]
rc = 0
for s in steps:
    t = time.time()
    args = [sys.executable, os.path.join(HERE, "experiments", s)] + (["--quick"] if "--quick" in sys.argv and s == "experiment_vals.py" else [])
    r = subprocess.run(args)
    print(f"== {s}: exit {r.returncode} ({time.time() - t:.0f}s)")
    if s == "verify_symbolic.py" and r.returncode == 2:
        print("   (SymPy missing: `pip install sympy` to run the symbolic checks)")
    elif r.returncode:
        rc = 1
# C++ harness comparison (original program/ compiled against OpenCV 4.x); needs cpp_harness/build.sh first
if os.path.exists(os.path.join(HERE, "cpp_harness", "build", "harness")):
    t = time.time()
    r = subprocess.run([sys.executable, os.path.join(HERE, "cpp_harness", "compare.py")])
    print(f"== cpp_harness/compare.py: exit {r.returncode} ({time.time() - t:.0f}s)")
    rc = rc or r.returncode
else:
    print("== cpp_harness/compare.py: skipped (run `bash research/cpp_harness/build.sh` first)")
# improvement proposal vs original (needs cpp_harness/build.sh AND improved/cpp/build.sh)
if all(os.path.exists(os.path.join(HERE, *p)) for p in (("cpp_harness", "build", "harness"), ("improved", "cpp", "build", "improved_cli"))):
    t = time.time()
    r = subprocess.run([sys.executable, os.path.join(HERE, "improved", "compare_improved.py")] + (["--quick"] if "--quick" in sys.argv else []))
    print(f"== improved/compare_improved.py: exit {r.returncode} ({time.time() - t:.0f}s)")
    rc = rc or r.returncode
else:
    print("== improved/compare_improved.py: skipped (run research/improved/cpp/build.sh first)")
r = subprocess.run([sys.executable, "-m", "pytest", "-q", os.path.join(HERE, "tests")])
sys.exit(rc or r.returncode)
