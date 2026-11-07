"""Tiny installed-runtime/CUDA capabilities; no real model or optimizer."""
import importlib.metadata,json,os,resource,shutil,subprocess,sys,time
from pathlib import Path
OUT=Path(sys.argv[1]);CASE=sys.argv[2];START=time.monotonic()
def write(n,v):
    payload=json.dumps(v,indent=2,allow_nan=False)
    with (OUT/n).open('x') as f:f.write(payload)
def audit(event,args):
    if event=='socket.connect':raise PermissionError('AR1 no network')
    if event=='open' and args and isinstance(args[0],(str,bytes)):
        p=os.fsdecode(args[0])
        if p.endswith(('.ckpt','.pth','.npy','.npz','.ply','.xyz64')) or 'regx-interface-contract-01' in p:
            raise PermissionError('AR1 model/data/reference payload forbidden')
sys.addaudithook(audit);ok=False;error=None;cuda=False
try:
    result=subprocess.run(['nvidia-smi','--query-gpu=index,name,driver_version,memory.total,memory.free','--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=10,check=True)
    lines=result.stdout.strip().splitlines();assert len(lines)==1
    fields=[s.strip() for s in lines[0].split(',')]
    gpu=dict(index=int(fields[0]),name=fields[1],driver=fields[2],total_MiB=int(fields[3]),free_MiB=int(fields[4]))
    write('GPU_PREFLIGHT.json',gpu);assert gpu['index']==0 and gpu['free_MiB']>=9216
    packages={}
    for name in ('torch','numpy','einops','omegaconf','hydra-core'):
        try:packages[name]=importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:packages[name]='MISSING'
    import numpy as np
    import torch
    torch.set_num_threads(1)
    assert torch.cuda.is_available() and torch.cuda.device_count()==1
    cuda=True;torch.cuda.set_per_process_memory_fraction(.10,0);torch.cuda.reset_peak_memory_stats()
    torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
    probes=[]
    for dtype in (torch.float32,torch.float64):
        x=torch.arange(96,device='cuda',dtype=dtype).reshape(3,32)/96
        A=torch.full((4,32),.01,device='cuda',dtype=dtype,requires_grad=True)
        B=torch.full((32,4),.02,device='cuda',dtype=dtype,requires_grad=True)
        y=x+(x@A.T)@B.T;loss=y.square().mean();loss.backward()
        assert torch.isfinite(loss) and torch.isfinite(A.grad).all() and torch.isfinite(B.grad).all()
        assert torch.count_nonzero(A.grad)>0 and torch.count_nonzero(B.grad)>0
        probes.append(dict(probe='tiny_low_rank_matrix_backward',dtype=str(dtype),passed=True))
    from torch.nn.attention import sdpa_kernel,SDPBackend
    q=(torch.arange(256,device='cuda',dtype=torch.float64).reshape(1,2,8,16)/256).requires_grad_()
    k=(q.detach()+.01).requires_grad_();v=(q.detach()+.02).requires_grad_()
    with sdpa_kernel(SDPBackend.MATH):
        out=torch.nn.functional.scaled_dot_product_attention(q,k,v);out.square().mean().backward()
    assert all(torch.isfinite(a.grad).all() for a in (q,k,v))
    probes.append(dict(probe='tiny_float64_math_SDPA_backward',passed=True))
    H=torch.tensor([[3.,.1,.2],[.1,2.,.3],[.2,.3,1.]],device='cuda',dtype=torch.float64,requires_grad=True)
    u,s,vh=torch.linalg.svd(H);(s*s).sum().backward();assert torch.isfinite(H.grad).all()
    probes.append(dict(probe='tiny_float64_matrix_SVD_backward',passed=True))
    torch.cuda.synchronize();allocated=torch.cuda.max_memory_allocated();reserved=torch.cuda.max_memory_reserved()
    assert allocated<=256*2**20 and reserved<=256*2**20
    disk=shutil.disk_usage('/root')
    write('RESULTS.json',dict(passed=True,python=sys.version,executable=sys.executable,packages=packages,
        torch_CUDA_build=torch.version.cuda,device=torch.cuda.get_device_name(0),device_capability=list(torch.cuda.get_device_capability(0)),
        GPU_preflight=gpu,probes=probes,torch_peak_allocated_bytes=allocated,torch_peak_reserved_bytes=reserved,
        WSL_logical_free_bytes=disk.free,WSL_logical_disk_bytes=disk.total,
        actual_RAP_model_or_checkpoint_loads=0,adapter_training_or_optimizer_calls=0,real_data_or_reference_reads=0,
        actual_native_adapter_backward_validated=False,old_loss_descent_replay_or_artifact_failures_repaired=False,
        scope='Generic installed-runtime and tiny CUDA capabilities only'))
    ok=True
except BaseException as caught:
    error=repr(caught)
    import traceback
    write('FAILURE.json',dict(error=error,traceback=traceback.format_exc()));raise
finally:
    write('worker_exit.json',dict(success=ok,error=error,elapsed_seconds=time.monotonic()-START,
        peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
        actual_adapter_updates=0,actual_model_loads=0))
