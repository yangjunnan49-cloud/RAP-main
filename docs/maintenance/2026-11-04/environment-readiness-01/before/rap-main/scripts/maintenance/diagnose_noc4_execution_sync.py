"""Synchronize frozen native blocks to localize an external execution failure."""
import json,resource,time
import torch
import native_conditioned_comparison as r
from rap_slam.rap_precision import ieee_matmul
start=time.monotonic();path=r.BASE/'execution_diagnosis_sync.jsonl';assert not path.exists()
def record(stage,**kwargs):
    row=dict(stage=stage,wall_seconds=time.monotonic()-start,
        RSS_peak_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
        GPU_allocated_peak_bytes=torch.cuda.max_memory_allocated() if torch.cuda.is_initialized() else 0,
        GPU_reserved_peak_bytes=torch.cuda.max_memory_reserved() if torch.cuda.is_initialized() else 0,**kwargs)
    with path.open('a') as f: f.write(json.dumps(row)+'\n');f.flush()
    print(row,flush=True)
    assert row['RSS_peak_bytes']<4*2**30 and row['GPU_reserved_peak_bytes']<3*2**30 and row['wall_seconds']<120
record('imports_complete');r.check();m,params,initial,audit=r.model();record('model_loaded')
z=r.load(r.BASE/'bank/synthetic_fixture.npz');b=r.n.noc.batch({k:z[k] for k in r.n.OBS})
noise=torch.tensor(r.load(r.BASE/'bank/noise/fit_00.npz')['noise'],device='cuda');kw=r.args(b,noise,1.)
with ieee_matmul(),torch.no_grad(),torch.autocast('cuda',dtype=torch.float16):
    e=r.prefix(m.flow_model,kw);torch.cuda.synchronize();record('prefix_synchronized')
    for i in (10,11):
        e=m.flow_model.transformer_layers[i](e,kw['timesteps'],kw['cu_seqlens_batch'],kw['cu_seqlens_part'])
        torch.cuda.synchronize();record(f'block{i}_synchronized',finite=bool(torch.isfinite(e).all()),
            max_abs=float(e.abs().max()),stride=list(e.stride()),dtype=str(e.dtype))
    with torch.autocast('cuda',enabled=False):
        e=e.float();torch.cuda.synchronize();record('float_input_synchronized')
        for i,layer in enumerate(m.flow_model.final_mlp):
            e=layer(e);torch.cuda.synchronize();record(f'mlp{i}_synchronized',finite=bool(torch.isfinite(e).all()))
record('complete_no_gradient_no_optimizer')
