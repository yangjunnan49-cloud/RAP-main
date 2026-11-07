"""Separately frozen RLP1 weak-label/proper-solver/gradient prerequisites."""
import sys
from pathlib import Path
import numpy as np
import local_motion_common as c
import rlp1_attempt03_common as r


def freeze():
    r.validated(r.ENG);r.check(r.ENG);r.check_seal(r.ENG)
    selected=c.read(r.ENG/'freeze.json')['rows']
    extra=[r.ENG/x for x in ('freeze.json','bank.json','bank_seal.json','validation.json','validation_seal.json')]
    extra += [r.ENG/'bank'/f"{r.stem(row)}_J.npz" for row in selected]
    extra += [Path(__file__).with_name('rlp1_attempt03_common.py'),Path(__file__).with_name('rlp1_validation_math.py')]
    r.freeze(r.WEAK,selected,__file__,Path(__file__).with_name('validate_rlp1_weak_preflight.py'),gt=True,
        extra_files=extra,minimum_positive_rows=20,physical_labels_verified=False,training=False)
    r.finish('weak_preflight_freeze');print('RLP1 weak-label preflight frozen',flush=True)


def synthetic(folder):
    import torch
    from scipy.spatial.transform import Rotation
    from measured_point_readout import labels,proper,weighted_pose,soft_pose,Readout,training_loss
    rng=np.random.default_rng(13);x=rng.normal(size=(64,3))*[2,3,4]
    poses=np.repeat(np.eye(4)[None],3,0)
    for k in (1,2):
        poses[k,:3,:3]=Rotation.from_rotvec(np.array([.1,-.2,.3])*k).as_matrix()
        poses[k,:3,3]=np.array([.3,-.2,.1])*k
    pp=np.array([(np.linalg.inv(P)@np.c_[x,np.ones(64)].T).T[:,:3] for P in poses])
    records=[]
    variants={'exact':pp.copy(),'ambiguous':pp.copy(),'unmatched':pp.copy(),
              'third_absent_dynamic_toy':pp.copy(),'nonfinite_ignored':pp.copy()}
    variants['ambiguous'][:,1]=variants['ambiguous'][:,0]
    variants['unmatched'][1]+=1000
    variants['third_absent_dynamic_toy'][2]+=1000
    variants['nonfinite_ignored'][0,0]=np.nan
    for name,parts in variants.items():
        z=labels(parts.reshape(-1,3),poses)
        if name=='exact':assert all((z[f'class_{a}{b}']==1).all() for a in range(3) for b in range(3) if a!=b)
        if name=='ambiguous':assert np.unpackbits(z['positive_01'],axis=1,bitorder='little',count=64)[0].sum()>=2
        if name=='unmatched':assert (z['class_01']==2).all()
        if name=='third_absent_dynamic_toy':assert (z['class_01']==0).all()
        if name=='nonfinite_ignored':assert z['class_01'][0]==0 and (z['class_01'][1:]==1).all()
        np.savez_compressed(folder/f'synthetic_{name}.npz',points=parts.reshape(-1,3),poses=poses,**z)
        records.append(dict(kind='labels',name=name))
    T=poses[1];target=x@T[:3,:3].T+T[:3,3];w=rng.uniform(.5,2,64)
    for name,source in [('rigid',x),('planar',x*np.array([1,1,0]))]:
        target=source@T[:3,:3].T+T[:3,3]
        fitted,gap=weighted_pose(source,target,w);assert abs(fitted-T).max()<1e-10
        np.savez_compressed(folder/f'synthetic_solver_{name}.npz',source=source,target=target,weights=w,expected=T,pose=fitted,gap=gap)
        records.append(dict(kind='solver',name=name))
    line=np.c_[np.arange(64),np.zeros((64,2))]
    try:weighted_pose(line,line,w)
    except ValueError:pass
    else:raise AssertionError('rank1 not rejected')
    np.savez_compressed(folder/'synthetic_rank1.npz',source=line,target=line,weights=w)
    records.append(dict(kind='expected_rejection',name='rank1'))
    fixtures=np.array([np.eye(3),T[:3,:3]@np.diag([1+1e-6,1-2e-6,1+3e-6]),np.diag([-1.,2.,3.])])
    rotations=np.array([proper(A) for A in fixtures])
    assert np.max(abs(rotations.transpose(0,2,1)@rotations-np.eye(3)))<1e-12
    assert np.allclose(np.linalg.det(rotations),1)
    np.savez_compressed(folder/'synthetic_proper.npz',raw=fixtures,proper=rotations)
    C=np.eye(4);C[:3,:3]=Rotation.from_rotvec([.7,-.1,.2]).as_matrix();C[:3,3]=[.8,-.4,.3]
    camera=C[None]@poses@np.linalg.inv(C)[None]
    from measured_point_readout import poses_from_camera
    recovered=poses_from_camera(camera,C);assert abs(recovered-poses).max()<1e-12
    np.savez_compressed(folder/'synthetic_calibration.npz',C=C,camera=camera,expected=poses,recovered=recovered)
    torch.manual_seed(13)
    source=torch.tensor(x,device='cuda',dtype=torch.float64)
    target=source@torch.tensor(T[:3,:3].T,device='cuda')+torch.tensor(T[:3,3],device='cuda')
    W=torch.diag(torch.tensor(w,device='cuda',dtype=torch.float64))+torch.full((64,64),1e-5,device='cuda')
    W.requires_grad_();fit,gap=soft_pose(source,target,W);assert fit is not None
    loss=fit[0].square().sum()+fit[1].square().sum();loss.backward()
    assert torch.isfinite(W.grad).all() and W.grad.abs().max()>0
    np.savez_compressed(folder/'synthetic_soft_gradient.npz',source=x,target=target.cpu().numpy(),W=W.detach().cpu().numpy(),R=fit[0].detach().cpu().numpy(),t=fit[1].detach().cpu().numpy(),gradient=W.grad.cpu().numpy(),gap=gap)
    lab=labels(pp.reshape(-1,3),poses);tl={}
    for key,val in lab.items():
        if key.startswith('positive'):val=np.unpackbits(val,axis=1,bitorder='little',count=64)
        tl[key]=torch.tensor(val,device='cuda')
    common=torch.randn(3,64,9,device='cuda');pts=torch.tensor(pp,device='cuda')
    grads=[]
    for dim in (32,512):
        torch.manual_seed(20261007);head=Readout().cuda();feature=torch.randn(3,64,dim,device='cuda')
        for update in (1,101):
            head.zero_grad(set_to_none=True);loss,meta=training_loss(head,feature,common,pts,tl,update)
            assert torch.isfinite(loss);loss.backward()
            assert all(p.grad is not None and torch.isfinite(p.grad).all() for p in head.parameters())
            grads.append(dict(dim=dim,update=update,loss=float(loss.detach()),**meta))
    return records,grads


def bank():
    import torch
    from measured_point_readout import labels,class_counts,poses_from_camera
    f=r.check(r.WEAK);r.validated(r.ENG);assert r.runtime()==f['runtime']
    (r.WEAK/'bank').mkdir();torch.cuda.reset_peak_memory_stats()
    cases,gradients=synthetic(r.WEAK/'bank');records=[]
    for row in f['rows']:
        camera=np.loadtxt(c.DATA/'poses'/f"{row['seq']}.txt").reshape(-1,3,4)
        calibration=np.eye(4)
        for line in (c.DATA/'sequences'/row['seq']/'calib.txt').read_text().splitlines():
            if line.startswith('Tr:'):calibration[:3]=np.fromstring(line.split(':',1)[1],sep=' ').reshape(3,4)
        selected=np.repeat(np.eye(4)[None],3,0);selected[:,:3]=camera[row['ids']]
        poses=poses_from_camera(selected,calibration)
        with np.load(r.ENG/'bank'/f"{r.stem(row)}_J.npz",allow_pickle=False) as z:points=z['points']
        output=labels(points,poses);counts=class_counts(output)
        np.savez_compressed(r.WEAK/'bank'/f"{r.stem(row)}.npz",points=points,**output)
        records.append(dict(**row,counts=counts))
        assert all(x['positive']>=20 for x in counts.values()),counts
        r.cap();print('RLP1 weak labels',row['seq'],{key:value['positive'] for key,value in counts.items()},flush=True)
    c.save(r.WEAK/'bank.json',dict(utc=c.now(),rows=records,synthetic=cases,gradient_checks=gradients,training_updates=0,**r.usage()))
    r.seal(r.WEAK);r.finish('weak_preflight_bank')
    print('RLP1 weak preflight bank sealed',flush=True)


if __name__=='__main__':
    try:{'freeze':freeze,'bank':bank}[sys.argv[1]]()
    except Exception as ex:r.fail('weak_preflight_'+sys.argv[1],ex);raise

