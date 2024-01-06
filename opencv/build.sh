# !/usr/bin/env bash
# -*- coding: utf-8 -*-
# OpenCV Install Tutorial: https://docs.opencv.org/4.x/d0/d3d/tutorial_general_install.html

# use the correct opencv version, so checkout the correct tag
OPENCV_VERSION="4.9.0"
git -C main checkout $OPENCV_VERSION
git -C contrib checkout $OPENCV_VERSION
git -C extra checkout $OPENCV_VERSION

# use cmake to config project
MAIN_BUILD_DIR=opencv_build
MAIN_INSTALL_DIR=opencv_install
# config opencv main feature repo
cmake -S main -B $MAIN_BUILD_DIR \
    -Wno-dev \
    -DCMAKE_BUILD_TYPE=Release \
    -DBUILD_EXAMPLES=OFF \
    -DBUILD_JAVA=OFF \
    -DCMAKE_INSTALL_PREFIX=$MAIN_INSTALL_DIR \
    -DBUILD_SHARED_LIBS=OFF # -DOPENCV_EXTRA_MODULES_PATH="../contrib;../extra" 

# build and install opencv main feature in local path
if [ -d "$MAIN_INSTALL_DIR" ]; then
    rm -rf $MAIN_INSTALL_DIR/
fi
cmake --build $MAIN_BUILD_DIR \
    -j8 \
    --target install


