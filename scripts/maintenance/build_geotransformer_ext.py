"""Compile the unchanged official CPU extension into a workspace-only build."""
import os,json,time
from pathlib import Path

B=Path('/mnt/e/githouse/RAP-main/docs/maintenance/2026-10-05/geotransformer-feasibility-01')
S=B/'official-source'; build=B/'extension-build'; build.mkdir(exist_ok=True)
os.environ['MAX_JOBS']='1'
from torch.utils.cpp_extension import load
names=['extra/cloud/cloud.cpp','cpu/grid_subsampling/grid_subsampling.cpp','cpu/grid_subsampling/grid_subsampling_cpu.cpp',
       'cpu/radius_neighbors/radius_neighbors.cpp','cpu/radius_neighbors/radius_neighbors_cpu.cpp','pybind.cpp']
start=time.monotonic()
ext=load(name='rap_geotransformer_ext',sources=[str(S/'geotransformer/extensions'/n) for n in names],
         build_directory=str(build),extra_cflags=['-O2'],with_cuda=False,verbose=True)
receipt=dict(wall_s=time.monotonic()-start,extension_path=ext.__file__,symbols=['radius_neighbors','grid_subsampling'],
             modification='build unchanged CPU sources with torch C++ loader instead of CUDAExtension packaging',max_jobs=1)
with (B/'extension_build.json').open('x') as f: json.dump(receipt,f,indent=2)
print('workspace-only extension ready',receipt,flush=True)
