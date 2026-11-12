# Cross-platform build of
#   navigator      - the ORIGINAL program/ sources, unchanged (needs OpenCV 4.x: it uses C headers
#                    such as highgui_c.h that OpenCV 5 removed)
#   harness        - research/cpp_harness: non-interactive driver around the original sources
#   improved_cli   - research/improved/cpp: improved implementation (OpenCV 4.x or 5.x)
# plus non-interactive CTest tests. Usage:
#   cmake -S . -B build [-DOpenCV_DIR=...] && cmake --build build --config Release
#   ctest --test-dir build -C Release --output-on-failure
cmake_minimum_required(VERSION 3.16)
project(FisheyeImageCorrection LANGUAGES CXX)

find_package(OpenCV REQUIRED)
message(STATUS "OpenCV ${OpenCV_VERSION} (${OpenCV_DIR})")

if(OpenCV_VERSION VERSION_LESS 5.0)
  set(_orig_default ON)
else()
  set(_orig_default OFF)
endif()
option(FISHEYE_BUILD_ORIGINAL "Build the original program/ (navigator) and the research harness (OpenCV 4.x only)" ${_orig_default})
option(FISHEYE_BUILD_IMPROVED "Build research/improved (improved_cli)" ON)
if(FISHEYE_BUILD_ORIGINAL AND NOT OpenCV_VERSION VERSION_LESS 5.0)
  message(FATAL_ERROR "program/ cannot be built with OpenCV ${OpenCV_VERSION}: it includes opencv2/highgui/highgui_c.h (removed in OpenCV 5)")
endif()

if(MSVC)
  add_compile_options(/utf-8 /EHsc /bigobj)   # sources contain UTF-8 (Chinese) comments
endif()

enable_testing()
set(REPO ${CMAKE_CURRENT_SOURCE_DIR})
set(T ${CMAKE_CURRENT_BINARY_DIR}/test_out)
file(MAKE_DIRECTORY ${T})

# ------------------------------------------------------------------ original program (unchanged)
if(FISHEYE_BUILD_ORIGINAL)
  add_executable(navigator
    program/main.cpp program/corrector.cpp program/findCircleParameter.cpp
    program/imagesStitcher.cpp program/tools.cpp program/viewer.cpp)
  target_link_libraries(navigator PRIVATE ${OpenCV_LIBS})
  target_include_directories(navigator PRIVATE ${OpenCV_INCLUDE_DIRS})
  set_target_properties(navigator PROPERTIES CXX_STANDARD 11 CXX_STANDARD_REQUIRED ON)

  add_executable(harness research/cpp_harness/harness.cpp)
  target_link_libraries(harness PRIVATE ${OpenCV_LIBS})
  target_include_directories(harness PRIVATE ${OpenCV_INCLUDE_DIRS})
  set_target_properties(harness PROPERTIES CXX_STANDARD 11 CXX_STANDARD_REQUIRED ON)
endif()

# ------------------------------------------------------------------ improved implementation
if(FISHEYE_BUILD_IMPROVED)
  add_executable(improved_cli research/improved/cpp/fisheye_improved.cpp research/improved/cpp/improved_cli.cpp)
  target_link_libraries(improved_cli PRIVATE ${OpenCV_LIBS})
  target_include_directories(improved_cli PRIVATE ${OpenCV_INCLUDE_DIRS})
  set_target_properties(improved_cli PROPERTIES CXX_STANDARD 17 CXX_STANDARD_REQUIRED ON)
endif()

# ------------------------------------------------------------------ tests (no GUI, no stdin)
set(IMG1 ${REPO}/ImagesForTest/1/1.JPG)
if(FISHEYE_BUILD_ORIGINAL)
  # `-h` prints the help and exits before any window is created
  add_test(NAME original_navigator_help COMMAND navigator -h)
  set_tests_properties(original_navigator_help PROPERTIES PASS_REGULAR_EXPRESSION "Usage: navigator")

  # getPhi: closed form at l = 2 is pi/2; the original bisection stops at 1.5830681730979816 (BUG-01)
  add_test(NAME original_getphi_equator
    COMMAND ${CMAKE_COMMAND} -DEXE=$<TARGET_FILE:harness> -DOUT=${T}/getphi.txt -P ${REPO}/ci/check_getphi.cmake)

  # Correction3 with the circle that reproduces the repository's own output images
  add_test(NAME original_c3_run COMMAND harness c3 ${IMG1} 946 634 623 ${T}/corrected0_ci.jpg)
  set_tests_properties(original_c3_run PROPERTIES FIXTURES_SETUP c3out)
endif()

if(FISHEYE_BUILD_IMPROVED)
  add_test(NAME improved_statics COMMAND improved_cli statics)
  foreach(lens STEREOGRAPHIC EQUIDISTANCE EQUISOLID ORTHOGONAL)
    add_test(NAME improved_roundtrip_${lens}
      COMMAND improved_cli roundtrip out=${T}/rt_${lens}.txt check=1 step=5 cx=945 cy=634 r=623 lens=${lens})
  endforeach()
  add_test(NAME improved_correct_real
    COMMAND improved_cli correct in=${IMG1} out=${T}/improved_1.png cx=947.27 cy=634.42 r=627.2 lens=EQUISOLID fov=3.2049)
  add_test(NAME improved_missing_input_fails
    COMMAND improved_cli correct in=${T}/does_not_exist.jpg out=${T}/x.png cx=1 cy=1 r=1)
  set_tests_properties(improved_missing_input_fails PROPERTIES WILL_FAIL TRUE)
  add_test(NAME improved_viewer COMMAND improved_cli viewer in=${REPO}/resources/panorama.jpg out=${T}/view_improved.png)
  set_tests_properties(improved_viewer PROPERTIES FIXTURES_SETUP viewimp)
endif()

if(FISHEYE_BUILD_ORIGINAL AND FISHEYE_BUILD_IMPROVED)
  # the original output must match resources/corrected0.jpg (byte-identical on macOS arm64 with
  # OpenCV 4.14; other platforms may differ by FP/JPEG-encoder details, hence an MAE bound)
  add_test(NAME original_c3_matches_repo_output
    COMMAND improved_cli imgdiff a=${T}/corrected0_ci.jpg b=${REPO}/resources/corrected0.jpg max_mae=1.5)
  set_tests_properties(original_c3_matches_repo_output PROPERTIES FIXTURES_REQUIRED c3out)
  # same viewer geometry: original viewer::updataWindow vs improved Viewer::render
  add_test(NAME original_viewer COMMAND harness viewer ${REPO}/resources/panorama.jpg ${T}/view_original.png)
  set_tests_properties(original_viewer PROPERTIES FIXTURES_SETUP vieworig)
  add_test(NAME viewer_original_vs_improved
    COMMAND improved_cli imgdiff a=${T}/view_original.png b=${T}/view_improved.png max_mae=5)
  set_tests_properties(viewer_original_vs_improved PROPERTIES FIXTURES_REQUIRED "vieworig;viewimp")
endif()
