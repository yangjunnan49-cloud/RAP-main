"""Prospectively frozen RLP2 numerical and initialized-head preflight."""
import sys
from pathlib import Path
import numpy as np
import local_motion_common as c
import rlp2_common as r

def freeze():
    r.check(r.ENG);r.check_seal(r.ENG);r.validated(r.ENG)
    r.check(r.STOP);r.check_seal(r.STOP);r.validated(r.STOP)
    allrows=r.rows();selected=[x for x in c.read(r.ENG/'freeze.json')['rows'] if x['seq'] in ('00','05')]
    extra=[base/name for base in (r.ENG,r.STOP) for name in ('freeze.json','bank.json','bank_seal.json','validation.json','validation_seal.json')]
    extra += [r.ENG/'bank'/f"{r.stem(x)}_{mode}.npz" for x in selected for mode in ('I','J')]
    extra += [r.OLD/'weak-label-preflight/bank'/f'{r.stem(x)}.npz' for x in selected]
    r.freeze(r.NUM,selected,__file__,Path(__file__).with_name('validate_rlp2_preflight.py'),extra_files=extra,
        full_manifest=allrows,seeds=list(r.SEEDS),optimizer_updates=0,tolerances=dict(horn=1e-8,gradient=1e-6,embedding=5e-5),
        reused_engineering=True)
    (r.B/'INCOMPLETE').write_text('RLP2 authorized; prerequisites and fixed learning pilot pending.\n')
    c.status(r.B,'numerical-preflight',status='AUTHORIZED_PREFLIGHT_FROZEN',training_authorized=True,optimizer_updates=0)
    r.finish('numerical_freeze');print('RLP2 numerical preflight frozen',flush=True)

def run():
    import torch
    from scipy.spatial.transform import Rotation
    from rap_slam.rap_precision import ieee_matmul
    from motion_supervised_readout import Readout,weights,solve,loss,common,encode_prediction
    f=r.check(r.NUM);assert r.runtime()==f['runtime']
    folder=r.NUM/'bank';folder.mkdir();torch.cuda.reset_peak_memory_stats()
    rng=np.random.default_rng(13);x=rng.normal(size=(64,3))*[2,3,4]
    T=np.eye(4);T[:3,:3]=Rotation.from_rotvec([.1,-.2,.3]).as_matrix();T[:3,3]=[.3,-.2,.1]
    cases=[]
    configurations=[('rigid',x,x@T[:3,:3].T+T[:3,3],np.diag(rng.uniform(.5,2,64)),False),
        ('planar',x*[1,1,0],(x*[1,1,0])@T[:3,:3].T+T[:3,3],np.eye(64),False),
        ('partial_unequal',x[:47],x@T[:3,:3].T+T[:3,3],np.eye(64,47),False)]
    duplicate=x.copy();duplicate[1]=duplicate[0]
    configurations.append(('ambiguous_duplicate',duplicate,duplicate@T[:3,:3].T+T[:3,3],np.eye(64),False))
    line=np.c_[np.arange(64),np.zeros((64,2))]
    configurations += [('rank1',line,line,np.eye(64),True),('uniform',x,x,np.ones((64,64)),True)]
    with ieee_matmul():
        for name,source,target,w,rejected in configurations:
            args=[torch.tensor(a,device='cuda',dtype=torch.float64) for a in (source,target,w)]
            try:
                R,t,meta=solve(*args)
                if rejected:raise AssertionError('Expected rejection '+name)
                pose=np.eye(4);pose[:3,:3]=R.cpu().numpy();pose[:3,3]=t.cpu().numpy()
                assert abs(pose-T).max()<1e-10
                z=dict(source=source,target=target,W=w,pose=pose,expected=T,gap=np.array(float(meta['gap'])))
            except ValueError:
                if not rejected:raise
                z=dict(source=source,target=target,W=w)
            np.savez(folder/f'synthetic_{name}.npz',**z);cases.append(dict(name=name,rejected=rejected))
        target=x@T[:3,:3].T+T[:3,3]+rng.normal(size=x.shape)*.01
        w=np.diag(rng.uniform(.5,2,64))+np.ones((64,64))*.001
        wt=torch.tensor(w,device='cuda',requires_grad=True)
        R,t,m=solve(torch.tensor(x,device='cuda'),torch.tensor(target,device='cuda'),wt)
        objective=R.square().sum()+t.square().sum();objective.backward()
        assert torch.isfinite(wt.grad).all()
        np.savez(folder/'synthetic_gradient.npz',source=x,target=target,W=w,gradient=wt.grad.cpu().numpy(),R=R.detach().cpu().numpy(),t=t.detach().cpu().numpy())
        records=[]
        for seed in r.SEEDS:
            with c.rng(seed):head=Readout().cuda()
            np.savez(folder/f'initial_{seed}.npz',**{k:v.detach().cpu().numpy() for k,v in head.state_dict().items()})
            for row in f['rows']:
                with np.load(r.ENG/'bank'/f'{r.stem(row)}_J.npz',allow_pickle=False) as bank:
                    z={k:bank[k] for k in ('points','features','cond','noise','scale','tokens')}
                pts=torch.tensor(z['points'].reshape(3,1000,3),device='cuda')
                channels=torch.tensor(common(z),device='cuda')
                with np.load(r.OLD/'weak-label-preflight/bank'/f'{r.stem(row)}.npz',allow_pickle=False) as targetbank:
                    truth=torch.tensor(targetbank['angular_truth'],device='cuda')
                for arm in ('D','I','J'):
                    if arm=='D':feature=z['features'].reshape(3,1000,32)
                    elif arm=='J':feature=z['tokens']
                    else:
                        with np.load(r.ENG/'bank'/f'{r.stem(row)}_I.npz',allow_pickle=False) as zz:feature=zz['tokens']
                    feature=torch.tensor(feature,device='cuda')
                    head.zero_grad(set_to_none=True)
                    objective,meta=loss(head,feature,channels,pts,truth);objective.backward()
                    assert all(p.grad is not None and torch.isfinite(p.grad).all() for p in head.parameters())
                    gradient=float(torch.sqrt(sum(p.grad.double().square().sum() for p in head.parameters())))
                    assert np.isfinite(gradient) and gradient>0
                    predicted=encode_prediction(head,feature,channels,pts)
                    np.savez(folder/f'real_{seed}_{arm}_{r.stem(row)}.npz',**predicted)
                    records.append(dict(seed=seed,arm=arm,seq=row['seq'],t=row['t'],loss=float(objective.detach()),gradient_norm=gradient,**meta))
                    r.cap()
                    print('RLP2 initialized forward/backward',seed,arm,row['seq'],'finite',flush=True)
    r.check(r.NUM)
    c.save(r.NUM/'bank.json',dict(utc=c.now(),cases=cases,real_checks=records,optimizer_updates=0,**r.usage()))
    r.seal(r.NUM);r.finish('numerical_bank');print('RLP2 numerical bank sealed',flush=True)

if __name__=='__main__':
    try:{'freeze':freeze,'run':run}[sys.argv[1]]()
    except Exception as ex:r.fail('numerical_'+sys.argv[1],ex);raise
