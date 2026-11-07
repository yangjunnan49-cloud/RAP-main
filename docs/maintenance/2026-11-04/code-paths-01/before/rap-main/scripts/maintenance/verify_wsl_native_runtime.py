"""Supervised target-free native execution check after host commit remediation."""
import hashlib,json,resource,signal,sys,time,traceback
from pathlib import Path
import numpy as np
import torch
import native_conditioned_comparison as r
from rap_slam.rap_precision import ieee_matmul
c=r.c
BASE=c.MAIN/'docs/maintenance/2026-10-10/wsl-runtime-recovery-01'
STAGE=sys.argv[1];LOG=BASE/'supervision'/STAGE
START=time.monotonic()

def usage():
    return dict(wall_seconds=time.monotonic()-START,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
        peak_GPU_allocated_bytes=torch.cuda.max_memory_allocated() if torch.cuda.is_initialized() else 0,
        peak_GPU_reserved_bytes=torch.cuda.max_memory_reserved() if torch.cuda.is_initialized() else 0)

def record(stage):
    u=usage()
    with (LOG/'child_progress.jsonl').open('a') as f: f.write(json.dumps(dict(stage=stage,**u))+'\n');f.flush()
    latest=LOG.parent/'host_latest.json'
    if latest.exists(): assert c.read(latest)['headroom_bytes']>=4*2**30,'host commit guard'
    assert u['wall_seconds']<300 and u['peak_RSS_bytes']<=4*2**30
    assert max(u['peak_GPU_allocated_bytes'],u['peak_GPU_reserved_bytes'])<=3*2**30
    print('runtime verification',STAGE,stage,flush=True)

def run():
    assert torch.get_num_threads()==1
    r.check();r.old_deliveries();r.noise_check();record('historical_bindings_checked')
    m,p,initial,audit=r.model();record('original_model_loaded')
    z=r.load(r.BASE/'bank/synthetic_fixture.npz');b=r.n.noc.batch({k:z[k] for k in r.n.OBS})
    noise=torch.tensor(r.load(r.BASE/'bank/noise/fit_00.npz')['noise'],device='cuda');kw=r.args(b,noise,1.)
    state=r.n.param_digest(p);frozen=r.frozen_digest(m.flow_model);arrays=[]
    r.old.START=START
    def cap(): record('resource_guard')
    r.old.cap=cap
    with ieee_matmul(),torch.no_grad(),torch.autocast('cuda',dtype=torch.float16):
        e=r.prefix(m.flow_model,kw);cached=r.tail(m.flow_model,e,kw);torch.cuda.synchronize()
        record('cached_forward_completed')
        for i in range(3):
            value=m.flow_model(**kw);torch.cuda.synchronize()
            assert torch.equal(cached,value),'cache/full mismatch'
            arrays.append(value.cpu().numpy().copy());record(f'full_forward_{i+1}_completed')
        assert all(np.array_equal(arrays[0],a) for a in arrays)
        trace=r.generate(m,b,noise)
        assert len(trace['taus'])==5 and all(np.isfinite(a).all() for a in trace.values())
        record('native_five_step_completed')
    assert state==r.n.param_digest(p) and frozen==r.frozen_digest(m.flow_model)
    assert all(value.grad is None for value in p.values())
    np.savez(LOG/'trace.npz',**trace)
    result=dict(passed=True,strict_model=audit,full_forwards=3,cache_full_byteexact=True,repeated_full_forward_byteexact=True,
        actual_native_steps=5,target_or_cache_at_inference=False,optimizer_calls=0,backward_calls=0,parameter_state_unchanged=True,
        output_sha256=hashlib.sha256(arrays[0].tobytes()).hexdigest(),**usage())
    c.save(LOG/'verification.json',result);record('complete');return result

signal.signal(signal.SIGALRM,lambda a,b:(_ for _ in ()).throw(TimeoutError('runtime verification300s cap')))
signal.alarm(300)
try:
    result=run();success=True
except BaseException as ex:
    traceback.print_exc();result=dict(error=repr(ex));success=False
finally:
    signal.alarm(0)
    c.save(LOG/'child_exit.json',dict(success=success,full_resource_capture=True,**usage(),result=result))
if not success: sys.exit(1)
