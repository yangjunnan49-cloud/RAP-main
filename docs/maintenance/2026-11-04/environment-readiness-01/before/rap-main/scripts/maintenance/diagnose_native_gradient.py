"""Zero-update NOC0 mixed-precision gradient scaling diagnosis."""
import importlib.util
import time
from pathlib import Path
import numpy as np
import local_motion_common as c
spec=importlib.util.spec_from_file_location('noc_original',Path(__file__).with_name('native_output_capability.py'))
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)


def run():
    import torch
    from native_output_capability import adapt,trainables,tail
    from rap_slam.rap_precision import ieee_matmul
    root=r.BASE;r.check();r.BASE=root/'gradient-diagnosis-01';r.BASE.mkdir()
    source=[Path(__file__),root/'freeze.json',root/'FAILURE_run.json',root/'RESOURCE_LOG.json',r.HELPER,
        Path(__file__).with_name('native_output_capability.py')]
    c.save(r.BASE/'freeze.json',dict(files={str(p):c.sha(p) for p in source},optimizer_updates=0,
        original_failure_preserved=True,scales=[1,1024]))
    model,audit=r.load_model();z=r.fixture();b=r.batch(z)
    with c.rng(20261010): adapt(model.flow_model)
    with ieee_matmul():
        cache=r.caches(model,b,torch.tensor(z['target'],device='cuda'),torch.tensor(z['noise'],device='cuda'))
        params=trainables(model.flow_model);e,kw=cache[0];records=[]
        for scale in (1,1024):
            model.zero_grad(set_to_none=True)
            with torch.autocast('cuda',dtype=torch.float16): v=tail(model.flow_model,e,kw)
            loss=(v-torch.tensor(z['noise']-z['target'],device='cuda')).square().mean()
            (loss*scale).backward()
            for p in params.values(): p.grad.div_(scale)
            groups=r.inspect_grad(params)
            stats={n:dict(norm=float(p.grad.double().norm()),nonzero=int(torch.count_nonzero(p.grad)),elements=p.numel()) for n,p in params.items()}
            np.savez(r.BASE/f'gradient_scale_{scale}.npz',**{n:p.grad.cpu().numpy() for n,p in params.items()})
            records.append(dict(scale=scale,loss=float(loss.detach()),groups=groups,parameters=stats))
        assert records[0]['groups']['B']==0 and records[1]['groups']['B']>0
        assert all(x['norm']>0 for n,x in records[1]['parameters'].items() if n.endswith('.B'))
        assert records[0]['loss']==records[1]['loss']
    c.save(r.BASE/'results.json',dict(optimizer_updates=0,records=records,
        decision='UNSCALED_FP16_ADAPTER_GRADIENT_UNDERFLOW_CONFIRMED',intended_loss_unchanged=True,
        loss_scale_1024_restores_all_B_gradients=True,**r.usage()))
    r.record('zero_update_gradient_diagnosis',True)
    c.save(r.BASE/'output_seal.json',dict(files={p.name:c.sha(p) for p in r.BASE.iterdir() if p.is_file()}))
    print('NOC0 zero-update gradient diagnosis',[(x['scale'],x['groups']) for x in records],flush=True)


if __name__=='__main__':
    import torch
    r.START=time.monotonic()
    try: run()
    except Exception as ex:
        r.record('zero_update_gradient_diagnosis',False,error=repr(ex));raise
