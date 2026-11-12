#!/usr/bin/env bash
# Build the C++ test harness and the original navigator from the UNMODIFIED program/ sources.
# OpenCV 4.x is required (program/ uses the C headers highgui_c.h / core_c.h / imgproc_c.h,
# which were removed in OpenCV 5). Default: Homebrew `opencv@4`; override with OPENCV_PREFIX.
#   bash research/cpp_harness/build.sh
# Compiler flags follow the repository's build.sh (clang++ -std=c++11 -g, no -O).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
OUT="$HERE/build"
mkdir -p "$OUT"

if [ -z "${OPENCV_PREFIX:-}" ]; then
  OPENCV_PREFIX="$(brew --prefix opencv@4 2>/dev/null || true)"
fi
if [ ! -d "$OPENCV_PREFIX/include/opencv4" ]; then
  echo "OpenCV 4 not found (set OPENCV_PREFIX, or: brew install opencv@4)" >&2
  exit 1
fi
INC="-I$OPENCV_PREFIX/include/opencv4"
LIBS="-L$OPENCV_PREFIX/lib -lopencv_core -lopencv_imgproc -lopencv_imgcodecs -lopencv_highgui \
      -lopencv_stitching -lopencv_features2d -lopencv_calib3d -lopencv_flann -Wl,-rpath,$OPENCV_PREFIX/lib"
CXX="${CXX:-clang++}"
FLAGS="-std=c++11 -g"

"$OPENCV_PREFIX/bin/opencv_version" > "$OUT/opencv_version.txt" 2>/dev/null || echo unknown > "$OUT/opencv_version.txt"
"$CXX" --version | head -1 > "$OUT/compiler_version.txt"

# 1. per-file compile log of the original sources (BUG-26: do the OpenCV 1.x C macros still compile?)
: > "$OUT/compile_program.log"
for f in main corrector findCircleParameter imagesStitcher tools viewer; do
  echo "=== program/$f.cpp" >> "$OUT/compile_program.log"
  "$CXX" $FLAGS -Wall -Wextra -c "$REPO/program/$f.cpp" $INC -o "$OUT/$f.o" >> "$OUT/compile_program.log" 2>&1
  echo "exit 0" >> "$OUT/compile_program.log"
done

# 2. the original program, exactly as build.sh links it (but against $OPENCV_PREFIX)
"$CXX" $FLAGS "$OUT"/{main,corrector,findCircleParameter,imagesStitcher,tools,viewer}.o $LIBS -o "$OUT/navigator"
# 3. the same with AddressSanitizer (BUG-12: main.cpp L52 reads imagePaths[size()])
(cd "$REPO/program" && "$CXX" $FLAGS -fsanitize=address -fno-omit-frame-pointer \
  main.cpp corrector.cpp findCircleParameter.cpp imagesStitcher.cpp tools.cpp viewer.cpp $INC $LIBS \
  -o "$OUT/navigator_asan")
# 4. the harness (unity build of program/*.cpp except main.cpp) with the build.sh flags.
#    Note: without -DNDEBUG, OpenCV's inline Mat::at() keeps its CV_DbgAssert bounds check.
"$CXX" $FLAGS "$HERE/harness.cpp" $INC $LIBS -o "$OUT/harness"
# timing-fairness variant: same sources with -O2 (the original build.sh uses -g only)
"$CXX" -std=c++11 -O2 "$HERE/harness.cpp" $INC $LIBS -o "$OUT/harness_O2"
# 5. release-style variant (-DNDEBUG: Mat::at unchecked) + ASan, to observe BUG-06 as a raw out-of-bounds read
"$CXX" $FLAGS -DNDEBUG -fsanitize=address -fno-omit-frame-pointer "$HERE/harness.cpp" $INC $LIBS -o "$OUT/harness_asan_ndebug"
echo "built: $(ls "$OUT" | grep -vE '\.o$|\.txt$|\.log$|dSYM' | tr '\n' ' ')"
