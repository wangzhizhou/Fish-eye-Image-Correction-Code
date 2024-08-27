#!/usr/bin/env bash
#-*- coding: utf-8 -*-

script_dir=$(dirname "$0")
python3 ${script_dir}/main/platforms/apple/build_xcframework.py \
--macos_archs arm64,arm64e \
--build_only_specified_archs \
--out ${script_dir}/build_xcframework

# --iphoneos_archs arm64 \
# --iphonesimulator_archs arm64 \
# --catalyst_archs arm64 \