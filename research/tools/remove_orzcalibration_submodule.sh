#!/usr/bin/env bash
# Remove the dangling OrzCalibration submodule (its upstream repository no longer exists).
# What it references (verified 2026-11-11):
#   .gitmodules                 [submodule "OrzCalibration"] path/url
#   .git/config                 [submodule "OrzCalibration"] active/url
#   index / HEAD tree           160000 gitlink 2c586eaf48962895fd7d0bea17be78ed750aa264 OrzCalibration
#   working tree                empty directory OrzCalibration/
# Nothing in program/, build.sh, run.sh, Dockerfile or .vscode uses it.
# Usage (from the repository root):  bash research/tools/remove_orzcalibration_submodule.sh
# The change is STAGED, not committed. Review with `git status`, then commit yourself.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
if git ls-files --stage -- OrzCalibration | grep -q '^160000'; then
  git rm -q --cached OrzCalibration                         # drop the gitlink from the index
fi
if git config -f .gitmodules --get-regexp '^submodule\.OrzCalibration\.' >/dev/null 2>&1; then
  git config -f .gitmodules --remove-section submodule.OrzCalibration
  git add .gitmodules
fi
git config --remove-section submodule.OrzCalibration 2>/dev/null || true
rm -rf .git/modules/OrzCalibration
[ -d OrzCalibration ] && rmdir OrzCalibration 2>/dev/null || true
echo "OrzCalibration submodule removed (staged). Remaining submodules:"
git submodule status 2>/dev/null || git config -f .gitmodules --get-regexp path
git status --short
