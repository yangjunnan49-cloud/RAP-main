"""Portable CPU packaging; remove only an unused CUDA include in a copy."""
import os,json,shutil,time,hashlib
from pathlib import Path

B=Path('/mnt/e/githouse/RAP-main/docs/maintenance/2026-10-05/geotransformer-feasibility-01')
official=B/'official-source/geotransformer/extensions'; portable=B/'compat-extensions'
if not portable.exists():
    shutil.copytree(official,portable)
    header=portable/'common/torch_helper.h'
    original=header.read_text()
    assert original.count('#include <ATen/cuda/CUDAContext.h>')==1
    header.write_text(original.replace('#include <ATen/cuda/CUDAContext.h>','// Unused CUDAContext include omitted for the CPU-only extension build.'))
build=B/'extension-build-v2'; build.mkdir(exist_ok=True)
os.environ['MAX_JOBS']='1'
from torch.utils.cpp_extension import load
names=['extra/cloud/cloud.cpp','cpu/grid_subsampling/grid_subsampling.cpp','cpu/grid_subsampling/grid_subsampling_cpu.cpp',
       'cpu/radius_neighbors/radius_neighbors.cpp','cpu/radius_neighbors/radius_neighbors_cpu.cpp','pybind.cpp']
t=time.monotonic()
ext=load(name='rap_geotransformer_ext',sources=[str(portable/n) for n in names],build_directory=str(build),
         extra_cflags=['-O2'],with_cuda=False,verbose=True)
receipt=dict(wall_s=time.monotonic()-t,extension_path=ext.__file__,max_jobs=1,
    modification='CPU extension packaging; copied helper header omits unused CUDAContext include; numerical code unchanged',
    original_header_sha256=hashlib.sha256((official/'common/torch_helper.h').read_bytes()).hexdigest(),
    portable_header_sha256=hashlib.sha256((portable/'common/torch_helper.h').read_bytes()).hexdigest())
with (B/'extension_build_v2.json').open('x') as f: json.dump(receipt,f,indent=2)
print('isolated CPU extension ready',receipt,flush=True)
