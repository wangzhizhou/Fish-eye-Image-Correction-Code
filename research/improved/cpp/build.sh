#!/usr/bin/env bash
# Build the improved implementation against OpenCV 4 and (if installed) OpenCV 5, and try to
# compile the ORIGINAL program/ sources against OpenCV 5 (BUG-26 evidence; expected to fail).
#   bash research/improved/cpp/build.sh
# Prefixes: OPENCV4_PREFIX (default brew opencv@4), OPENCV5_PREFIX (default brew opencv).
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/../../.." && pwd)"
OUT="$HERE/build"
mkdir -p "$OUT"
CXX="${CXX:-clang++}"
OPENCV4_PREFIX="${OPENCV4_PREFIX:-$(brew --prefix opencv@4 2>/dev/null)}"
OPENCV5_PREFIX="${OPENCV5_PREFIX:-$(brew --prefix opencv 2>/dev/null)}"

build() {   # $1 prefix  $2 suffix  $3 extra flags
  local P="$1" S="$2" F="$3"
  local INC
  INC="$(ls -d "$P"/include/opencv* 2>/dev/null | head -1)"
  [ -n "$INC" ] || { echo "no OpenCV headers under $P" >&2; return 1; }
  "$CXX" -std=c++17 $F -Wall -Wextra -I"$INC" "$HERE/fisheye_improved.cpp" "$HERE/improved_cli.cpp" \
    -L"$P/lib" -lopencv_core -lopencv_imgproc -lopencv_imgcodecs -Wl,-rpath,"$P/lib" \
    -o "$OUT/improved_cli$S" 2> "$OUT/improved_cli$S.log"
  local rc=$?
  "$P/bin/opencv_version" > "$OUT/opencv_version$S.txt" 2>/dev/null || true
  echo "improved_cli$S: exit $rc ($(cat "$OUT/opencv_version$S.txt" 2>/dev/null)), warnings: $(grep -c warning "$OUT/improved_cli$S.log")"
  return $rc
}

build "$OPENCV4_PREFIX" "" "-O2"                       # main binary, OpenCV 4
build "$OPENCV4_PREFIX" "_g" "-g"                      # same flags as the original build.sh (timing fairness)
build "$OPENCV4_PREFIX" "_asan" "-g -fsanitize=address -fno-omit-frame-pointer"
if [ -d "$OPENCV5_PREFIX/include" ]; then
  build "$OPENCV5_PREFIX" "_cv5" "-O2"
  # original sources against OpenCV 5 (compile only)
  INC5="$(ls -d "$OPENCV5_PREFIX"/include/opencv* | head -1)"
  : > "$OUT/original_vs_opencv5.log"
  for f in main corrector findCircleParameter imagesStitcher tools viewer; do
    echo "=== program/$f.cpp" >> "$OUT/original_vs_opencv5.log"
    "$CXX" -std=c++11 -g -fsyntax-only -I"$INC5" "$REPO/program/$f.cpp" >> "$OUT/original_vs_opencv5.log" 2>&1
    echo "exit $?" >> "$OUT/original_vs_opencv5.log"
  done
  echo "original program/ vs OpenCV 5: $(grep -c '^exit 0' "$OUT/original_vs_opencv5.log")/6 files compile"
fi
