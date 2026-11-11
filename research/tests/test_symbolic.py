import os
import subprocess
import sys
import pytest


def test_symbolic_verification():
    pytest.importorskip("sympy")
    script = os.path.join(os.path.dirname(__file__), "..", "experiments", "verify_symbolic.py")
    res = subprocess.run([sys.executable, script], capture_output=True, text=True, timeout=1800)
    print(res.stdout[-4000:])
    assert res.returncode == 0, res.stdout[-4000:] + res.stderr[-2000:]
