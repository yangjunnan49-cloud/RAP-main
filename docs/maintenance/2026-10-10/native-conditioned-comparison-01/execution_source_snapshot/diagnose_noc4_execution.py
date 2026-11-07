"""Read-only stage-local execution diagnosis, not a fitting rescue."""
import json
import resource
import sys
import time
import numpy as np
import torch
import native_conditioned_comparison as r
from rap_slam.rap_precision import ieee_matmul

start=time.monotonic();path=r.BASE/'execution_diagnosis_progress.jsonl'
assert not path.exists()
def record(stage):
    row=dict(stage=stage,wall_seconds=time.monotonic()-start,
        RSS_peak_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
        GPU_allocated_peak_bytes=torch.cuda.max_memory_allocated() if torch.cuda.is_initialized() else 0,
        GPU_reserved_peak_bytes=torch.cuda.max_memory_reserved() if torch.cuda.is_initialized() else 0)
    with path.open('a') as f: f.write(json.dumps(row)+'\n');f.flush()
    print(stage,flush=True)
    assert row['RSS_peak_bytes']<4*2**30 and row['GPU_reserved_peak_bytes']<3*2**30
    assert row['wall_seconds']<120

record('imports_complete');r.check();record('source_check_complete')
m,params,initial,audit=r.model();record('strict_checkpoint_and_original_init_loaded')
z=r.load(r.BASE/'bank/synthetic_fixture.npz');b=r.n.noc.batch({k:z[k] for k in r.n.OBS})
noise=torch.tensor(r.load(r.BASE/'bank/noise/fit_00.npz')['noise'],device='cuda');kw=r.args(b,noise,1.)
with ieee_matmul(),torch.no_grad(),torch.autocast('cuda',dtype=torch.float16):
    e=r.prefix(m.flow_model,kw);torch.cuda.synchronize();record('prefix_complete')
    hooks=[]
    for name,module in m.flow_model.named_modules():
        if name.startswith(('transformer_layers.10','transformer_layers.11','final_mlp')):
            hooks.append(module.register_forward_pre_hook(lambda m,a,n=name:record('enter_'+n)))
            hooks.append(module.register_forward_hook(lambda m,a,b,n=name:record('return_'+n)))
    v=r.tail(m.flow_model,e,kw);torch.cuda.synchronize();record('tail_complete')
    for hook in hooks: hook.remove()
    whole=m.flow_model(**kw);torch.cuda.synchronize();record('full_forward_complete')
    assert float(abs(v-whole).max())==0
record('complete_no_optimizer_no_gradient')
