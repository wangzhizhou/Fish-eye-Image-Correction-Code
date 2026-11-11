# cmake -DEXE=<harness> -DOUT=<file> -P check_getphi.cmake
# Runs the ORIGINAL getPhi (via the harness) for l = 4j/1920 and checks row 960 (l = 2):
# the bisection of program/corrector.cpp stops at 1.5830681730979816 instead of pi/2 (BUG-01).
execute_process(COMMAND ${EXE} getphi 1920 ${OUT} RESULT_VARIABLE rc)
if(NOT rc EQUAL 0)
  message(FATAL_ERROR "harness getphi failed: ${rc}")
endif()
file(STRINGS ${OUT} lines)
list(LENGTH lines n)
if(NOT n EQUAL 1920)
  message(FATAL_ERROR "expected 1920 rows, got ${n}")
endif()
list(GET lines 960 row)
# compare the first 12 significant digits (robust to last-ulp libm differences between platforms)
if(NOT row MATCHES "^960 2 1\\.5830681730")
  message(FATAL_ERROR "unexpected getPhi(2): '${row}'")
endif()
message(STATUS "getPhi(2) row: ${row}")
