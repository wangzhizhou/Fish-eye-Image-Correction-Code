# !/usr/bin/env bash
# -*- coding: utf-8 -*-
# OpenCV Install Tutorial: https://docs.opencv.org/4.x/d0/d3d/tutorial_general_install.html

# use the correct opencv version, so checkout the correct tag
OPENCV_VERSION="4.9.0"
OPENCV_DIR=opencv
OPENCV_MAIN=$OPENCV_DIR/main
OPENCV_CONTRIB=$OPENCV_DIR/contrib
OPENCV_EXTRA=$OPENCV_DIR/extra
git -C $OPENCV_MAIN checkout $OPENCV_VERSION
git -C $OPENCV_CONTRIB checkout $OPENCV_VERSION
git -C $OPENCV_EXTRA checkout $OPENCV_VERSION

# use cmake to config project
MAIN_BUILD_DIR=opencv_build
MAIN_INSTALL_DIR=opencv_install

# config opencv main feature repo
cmake -S $OPENCV_MAIN -B $MAIN_BUILD_DIR \
    -Wno-dev \
    -DCMAKE_BUILD_TYPE=Release \
    -DBUILD_EXAMPLES=OFF \
    -DBUILD_JAVA=OFF \
    -DBUILD_ITT=OFF \
    -DBUILD_TIFF=OFF \
    -DBUILD_WEBP=OFF \
    -DBUILD_ZLIB=OFF \
    -DBUILD_JASPER=OFF \
    -DBUILD_PERF_TESTS=OFF \
    -DBUILD_TESTS=OFF \
    -DBUILD_PROTOBUF=OFF \
    -DBUILD_opencv_dnn=OFF \
    -DBUILD_opencv_objc_bindings_generator=OFF \
    -DBUILD_opencv_objdetect=OFF \
    -DBUILD_opencv_photo=OFF \
    -DBUILD_opencv_apps=OFF \
    -DBUILD_opencv_gapi=OFF \
    -DBUILD_opencv_java_bindings_generator=OFF \
    -DBUILD_opencv_js_bindings_generator=OFF \
    -DBUILD_opencv_ml=OFF \
    -DBUILD_opencv_python_bindings_generator=OFF \
    -DBUILD_opencv_python_tests=OFF \
    -DBUILD_opencv_video=OFF \
    -DBUILD_opencv_videoio=OFF \
    -DBUILD_opencv_ts=OFF \
    -DBUILD_ZLIB=OFF \
    -DWITH_CAROTENE=OFF \
    -DWITH_ITT=OFF \
    -DWITH_OPENCL=OFF \
    -DWITH_TIFF=OFF \
    -DWITH_WEBP=OFF \
    -DWITH_LAPACK=OFF \
    -DWITH_JASPER=OFF \
    -DWITH_OPENCLAMDBLAS=OFF \
    -DWITH_OPENCLAMDFFT=OFF \
    -DWITH_OPENEXR=OFF \
    -DWITH_PROTOBUF=OFF \
    -DWITH_PTHREADS_PF=OFF \
    -DWITH_VTK=OFF \
    -DWITH_1394=OFF \
    -DWITH_EIGEN=OFF \
    -DWITH_ARITH_DEC=OFF \
    -DWITH_ARITH_ENC=OFF \
    -DWITH_AVFOUNDATION=OFF \
    -DWITH_FFMPEG=OFF \
    -DWITH_FLATBUFFERS=OFF \
    -DWITH_ADE=OFF \
    -DWITH_GSTREAMER=OFF \
    -DENABLE_CCACHE=OFF \
    -DENABLE_PIC=OFF \
    -DENABLE_LIBJPEG_TURBO_SIMD=OFF \
    -DOPENCV_ENABLE_ALLOCATOR_STATS=OFF \
    -DOPENCV_GENERATE_SETUPVARS=OFF \
    -DCV_TRACE=OFF \
    -DCV_ENABLE_INTRINSICS=OFF \
    -DNEON_INTRINSICS=OFF \
    -DOPENCV_DNN_TFLITE=OFF \
    -DOPENCV_TEST_DNN_TFLITE=OFF \
    -DOPJ_USE_THREAD=OFF \
    -DPARALLEL_ENABLE_PLUGINS=OFF \
    -DCMAKE_INSTALL_PREFIX=$MAIN_INSTALL_DIR \
    -DBUILD_SHARED_LIBS=ON \
    -DBUILD_opencv_world=ON #--fresh #-DOPENCV_EXTRA_MODULES_PATH="contrib/modules"
    

# build and install opencv main feature in local path
if [ -d "$MAIN_INSTALL_DIR" ]; then
    rm -rf $MAIN_INSTALL_DIR/
fi
cmake --build $MAIN_BUILD_DIR \
    -j8 \
    --target install

# uninstall opencv
# cmake --build $MAIN_BUILD_DIR --target uninstall


# show all config options
# cmake -S main -B $MAIN_BUILD_DIR -L


# build navigator executable
clang++ -working-directory=program \
    -std=c++11 -g \
    main.cpp \
    corrector.cpp \
    findCircleParameter.cpp \
    imagesStitcher.cpp \
    tools.cpp \
    viewer.cpp \
    -I$(pwd)/opencv_install/include/opencv4 \
    -Lopencv_install/lib \
    -lopencv_world \
    -rpath opencv_install/lib \
    -o product/navigator