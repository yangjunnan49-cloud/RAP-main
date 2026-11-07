"""RLP2 fixed nine fits with a separately implemented complete replay."""
import sys
from pathlib import Path
import numpy as np
import local_motion_common as c
import rlp2_common as r

def step_cap(previous):
    """No artifacts are written inside updates; avoid repeated whole-bank stats."""
    import resource
    import time
    import torch
    elapsed=time.monotonic()-r._r.PROCESS_START
    assert elapsed<=300 and previous+elapsed<=3600,elapsed
    assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/2**20<=4
    assert torch.cuda.max_memory_allocated()/2**30<=3

def location(seed,arm):
    assert seed in r.SEEDS and arm in ('D','I','J')
    return r.FIT/f'{seed}_{arm}'

def arrays(head):return {k:v.detach().cpu().numpy() for k,v in head.state_dict().items()}

def load(row,arm,independent=False):
    import torch
    with np.load(r.FULL/'bank'/f'{r.stem(row)}.npz',allow_pickle=False) as z:
        small={k:z[k] for k in ('points','cond','noise','scale')}
        feature=z['features'].reshape(3,1000,32) if arm=='D' else z[arm+'_tokens']
    if independent:
        from rlp2_independent import common
    else:
        from motion_supervised_readout import common
    with np.load(r.LAB/'bank'/f'{r.stem(row)}.npz',allow_pickle=False) as z:truth=z['angular_truth']
    return tuple(torch.tensor(a,device='cuda') for a in (feature,common(small),small['points'].reshape(3,1000,3),truth))

def freeze(seed,arm):
    r.check(r.FULL);r.check_seal(r.FULL);r.validated(r.FULL)
    r.check(r.LAB);r.check_seal(r.LAB);r.validated(r.LAB)
    selected=r.order(seed)
    extra=[base/name for base in (r.FULL,r.LAB) for name in ('freeze.json','bank.json','bank_seal.json','validation.json','validation_seal.json')]
    extra += [base/'bank'/f'{r.stem(row)}.npz' for base in (r.FULL,r.LAB) for row in selected]
    extra += [Path(__file__).with_name('rlp2_fit_math.py')]
    r.FIT.mkdir(exist_ok=True)
    r.freeze(location(seed,arm),selected,__file__,__file__,gt=True,extra_files=extra,
        fit_seed=seed,arm=arm,updates=1000,optimizer=dict(name='AdamW',lr=1e-3,weight_decay=1e-4,clip=1.),
        evaluation_inputs_used=False)
    r.finish(f'fit_{seed}_{arm}_freeze');print('RLP2 fit frozen',seed,arm,flush=True)

def train(seed,arm):
    import torch
    from rap_slam.rap_precision import ieee_matmul
    from motion_supervised_readout import Readout,loss
    base=location(seed,arm);f=r.check(base);assert r.runtime()==f['runtime']
    folder=base/'bank';folder.mkdir();torch.cuda.reset_peak_memory_stats()
    with c.rng(seed):head=Readout().cuda()
    np.savez(folder/'initial.npz',**arrays(head))
    opt=torch.optim.AdamW(head.parameters(),lr=1e-3,weight_decay=1e-4);records=[]
    previous=sum(x['wall_s'] for x in c.read(r.B/'RESOURCE_LOG.json'));r.cap(300)
    with ieee_matmul():
        for k in range(1000):
            row=f['rows'][k%144];opt.zero_grad(set_to_none=True)
            objective,meta=loss(head,*load(row,arm));objective.backward()
            assert all(p.grad is not None and torch.isfinite(p.grad).all() for p in head.parameters())
            norm=torch.nn.utils.clip_grad_norm_(head.parameters(),1.);assert torch.isfinite(norm)
            opt.step();assert all(torch.isfinite(p).all() for p in head.parameters())
            records.append(dict(update=k+1,seq=row['seq'],t=row['t'],loss=float(objective.detach()),gradient_norm=float(norm),**meta))
            step_cap(previous)
            if (k+1)%100==0:print('RLP2 fit',seed,arm,k+1,'/1000 loss',records[-1]['loss'],flush=True)
    np.savez(folder/'final.npz',**arrays(head))
    optimizer={f'{ix}_{key}':v.detach().cpu().numpy() for ix,p in enumerate(head.parameters()) for key,v in opt.state[p].items()}
    np.savez(folder/'optimizer.npz',**optimizer)
    c.save(folder/'trace.json',records);r.check(base);r.cap(300)
    c.save(base/'bank.json',dict(utc=c.now(),seed=seed,arm=arm,optimizer_updates=1000,
        initial_sha256=c.sha(folder/'initial.npz'),final_sha256=c.sha(folder/'final.npz'),eval_inputs_used=False,**r.usage()))
    r.seal(base);r.finish(f'fit_{seed}_{arm}');print('RLP2 fit complete sealed',seed,arm,flush=True)

def validate(seed,arm):
    import torch
    from rap_slam.rap_precision import ieee_matmul
    from rlp2_fit_math import IndependentHead,loss
    base=location(seed,arm);f=r.check(base);r.check_seal(base);assert r.runtime()==f['runtime']
    trace=c.read(base/'bank/trace.json');assert len(trace)==1000
    with c.rng(seed):head=IndependentHead().cuda()
    with np.load(base/'bank/initial.npz',allow_pickle=False) as z:
        assert all(np.array_equal(arrays(head)[key],z[key]) for key in z.files)
    opt=torch.optim.AdamW(head.parameters(),lr=1e-3,weight_decay=1e-4)
    maximum=0.;pairmax=0.;normmax=0.;gapmax=0.
    previous=sum(x['wall_s'] for x in c.read(r.B/'RESOURCE_LOG.json'));r.cap(300)
    with ieee_matmul():
        for k in range(1000):
            row=f['rows'][k%144];old=trace[k]
            assert old['update']==k+1 and old['seq']==row['seq'] and old['t']==row['t']
            assert row['role']=='fit' and int(row['seq'])<=5
            opt.zero_grad(set_to_none=True);objective,meta=loss(head,*load(row,arm,independent=True));objective.backward()
            assert all(p.grad is not None and torch.isfinite(p.grad).all() for p in head.parameters())
            norm=torch.nn.utils.clip_grad_norm_(head.parameters(),1.);opt.step()
            ld=abs(float(objective.detach())-old['loss']);nd=abs(float(norm)-old['gradient_norm'])
            pd=float(abs(np.array(meta['pair_losses'])-old['pair_losses']).max())
            gd=float(abs(np.array(meta['gaps'])-old['gaps']).max())
            maximum=max(maximum,ld);normmax=max(normmax,nd);pairmax=max(pairmax,pd);gapmax=max(gapmax,gd)
            assert ld<1e-8 and pd<1e-8 and nd<1e-8 and gd<1e-10
            step_cap(previous)
            if (k+1)%200==0:print('RLP2 independent fit replay',seed,arm,k+1,'/1000',flush=True)
    actual=arrays(head)
    with np.load(base/'bank/final.npz',allow_pickle=False) as z:
        assert all(np.array_equal(actual[key],z[key]) for key in z.files)
    with np.load(base/'bank/optimizer.npz',allow_pickle=False) as z:
        assert all(np.array_equal(value.detach().cpu().numpy(),z[f'{ix}_{key}']) for ix,p in enumerate(head.parameters()) for key,value in opt.state[p].items())
    r.pass_validation(base,dict(decision='PASS_COMPLETE_FIXED_FIT_REPLAY',optimizer_updates=1000,seed=seed,arm=arm,
        initial_final_optimizer_exact=True,max_loss_delta=maximum,max_pair_loss_delta=pairmax,max_gradient_norm_delta=normmax,
        max_quaternion_gap_delta=gapmax,evaluation_inputs_used=False,**r.usage()))
    r.finish(f'fit_{seed}_{arm}_validation');print('RLP2 fit independent replay VALIDATED',seed,arm,flush=True)

if __name__=='__main__':
    mode,seed,arm=sys.argv[1],int(sys.argv[2]),sys.argv[3]
    try:{'freeze':freeze,'train':train,'validate':validate}[mode](seed,arm)
    except Exception as ex:r.fail(f'fit_{seed}_{arm}_{mode}',ex);raise
