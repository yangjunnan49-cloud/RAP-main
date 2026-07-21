#!/bin/bash
set -e
source /root/miniconda3/bin/activate rap-inference
export TORCH_CUDA_ARCH_LIST=12.0
export CUDA_HOME=/usr/local/cuda-12.8
export FORCE_CUDA=1
export MAX_JOBS=2

cd /tmp
rm -rf pytorch3d-build
git clone --depth 1 https://github.com/facebookresearch/pytorch3d.git pytorch3d-build
cd pytorch3d-build
pip install -v --no-build-isolation . 2>&1 | tee /root/pytorch3d_build2.log
