"""Freeze and run LMF0, without evaluator GT reads."""
import itertools,os,resource,sys,time
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
import local_motion_common as c
B=c.PREFLIGHT/'attempt-02'

def synthetic(b):
    world=np.random.default_rng(71005).normal(size=(120,3))*3;As=[];points=[]
    for k in range(3):
        A=np.eye(4);A[:3,:3]=Rotation.from_rotvec([.03*k,-.02*k,.07*k]).as_matrix();A[:3,3]=[2*k,-k,.4*k]
        As.append(A);points.append(c.transform(world,np.linalg.inv(A)))
    for ix,order in enumerate(itertools.permutations(range(3))):
        for j,m in enumerate([1.,2.5]):
            pp=[points[k]*m+[4.,-2.,7.] for k in order];expected=[]
            for k in order:
                T=As[k].copy();T[:3,3]=m*T[:3,3]-T[:3,:3]@np.array([4.,-2.,7.]);expected.append(T)
            cond,scale,centers,counts,_=b._normalize_parts(pp)
            raw=np.concatenate([c.transform(p,T)/scale for p,T in zip(pp,expected)])
            parts=c.decode(cond,raw,np.array(centers),counts,scale)
            assert abs(parts-np.array(expected)).max()<2e-6
            Q=np.eye(4);Q[:3,:3]=Rotation.from_rotvec([.4,-.3,.2]).as_matrix();Q[:3,3]=[-2.,3.,5.]
            gauged=c.transform(raw*scale,Q)/scale;gp=c.decode(cond,gauged,np.array(centers),counts,scale)
            assert abs(np.linalg.inv(parts[0])@parts[1]-np.linalg.inv(gp[0])@gp[1]).max()<1e-10
            np.savez_compressed(B/'bank'/f'synthetic_{2*ix+j:02d}.npz',points=np.concatenate(pp),cond=cond,
                raw=raw,scale=scale,centers=centers,counts=counts,expected=expected,parts=parts,gauge=Q,gauged=gauged,gauge_parts=gp)
    geo,trace=c.geometric(points)
    assert abs(geo['G2']-np.linalg.inv(As[0])@As[1]).max()<1e-10
    assert abs(geo['G3']-geo['G2']).max()<1e-10
    np.savez_compressed(B/'bank'/'synthetic_icp.npz',points=np.concatenate(points),**geo)
    return trace

def freeze():
    assert not (B/'freeze.json').exists();cc=c.census()
    paths=c.frozen_sources()+[B/'PROTOCOL.md',Path(__file__),Path(__file__).with_name('validate_local_motion_feasibility_v2.py'),
        B.parent/'PROTOCOL.md',B.parent/'AMENDMENT_01.md',B.parent/'FAILURE_01.json',B.parent/'freeze.json',
        Path(__file__).with_name('local_motion_feasibility.py'),Path(__file__).with_name('validate_local_motion_feasibility.py')]
    for r in cc['rows']:paths+=list(map(Path,r['paths']))
    native=[]
    for s in ['00','08']:
        pair=c.read(c.F2/f'inputs_{s}.json')[0]['key'];native.append(dict(seq=s,pair=pair))
        paths += [c.F2/f'inputs_{s}.json',c.F2/s/pair/'inputs.npz',c.F2/s/pair/'N0.npz',c.C1/s/f'{pair}.npz']
    paths += [c.F2/'artifact_hashes.json',c.F2/'validation.json',c.C1/'bank_seal.json',c.C1/'validation.json']
    c.save(B/'freeze.json',dict(utc=c.now(),census=cc,engineering=[r for r in cc['rows'] if r['t']==200],native=native,
        files={str(p):c.sha(p) for p in sorted(set(paths))}));c.status(B,'FROZEN');print('LMF0 frozen',len(set(paths)),len(cc['rows']),flush=True)

def bank():
    import torch
    f=c.check_freeze(B);assert torch.cuda.is_available() and os.environ['OMP_NUM_THREADS']=='1'
    (B/'bank').mkdir();(B/'INCOMPLETE').write_text('Engineering validation pending\n');c.status(B,'RUNNING');t=time.monotonic()
    b,audit=c.make_backend();torch.cuda.reset_peak_memory_stats();trace=synthetic(b);rows=[]
    for row in f['native']:
        folder=c.F2/row['seq']/row['pair'];parent=c.read(c.F2/'artifact_hashes.json')
        for p in [folder/'inputs.npz',folder/'N0.npz']:assert c.sha(p)==parent[str(p.relative_to(c.F2))]
        with np.load(folder/'inputs.npz',allow_pickle=False) as z:cond=z['cond'];counts=z['counts'];scale=float(z['scale']);noise=z['noise'][0]
        with np.load(c.C1/row['seq']/f"{row['pair']}.npz",allow_pickle=False) as z:feat=z['features']
        bb=dict(pointclouds=torch.tensor(cond,device='cuda'),pointclouds_gt=torch.tensor(cond,device='cuda'),
            features=torch.tensor(feat,device='cuda'),scales=torch.tensor([scale],device='cuda'),
            anchor_indices=torch.tensor(np.arange(len(cond))<counts[0],device='cuda'),
            points_per_part=torch.tensor(counts[None],device='cuda'),cu_seqlens=torch.tensor([0,len(cond)],device='cuda'))
        rr=c.generate(b,bb,torch.tensor(noise,device='cuda'))
        with np.load(folder/'N0.npz',allow_pickle=False) as z:delta=max(float(abs(rr[k]-z[k]).max()) for k in rr)
        assert delta<=1e-5;np.savez_compressed(B/'bank'/f"native_{row['seq']}.npz",**rr)
        rows.append(dict(**row,kind='native',max_delta=delta));print('native replay',row['seq'],delta,flush=True)
    for row in f['engineering']:
        arrays,tr=c.inference_row(b,row);again,_=c.inference_row(b,row)
        delta=max(float(np.max(np.abs(arrays[k]-again[k]))) for k in arrays);assert delta<=1e-5
        for arm,num in [('R3',3),('R2',2)]:
            bb,_,_,_=c.batch(b,np.split(arrays['points'][:num*1000],num),np.split(arrays['features'][:num*1000],num))
            bb['pointclouds_gt']=torch.full_like(bb['pointclouds_gt'],123.)
            dummy=c.generate(b,bb,torch.tensor(arrays['noise'][:num*1000],device='cuda'))
            assert all(np.array_equal(dummy[k],arrays[arm+'_'+k]) for k in dummy)
        np.savez_compressed(B/'bank'/f"local_{row['seq']}.npz",**arrays)
        rows.append(dict(**row,kind='local',repeat_max_delta=delta,dummy_gt_invariant=True,icp_trace=tr))
        print('local engineering',row['seq'],delta,round(time.monotonic()-t,2),flush=True);assert time.monotonic()-t<1000
    c.check_freeze(B)
    c.save(B/'bank.json',dict(checkpoint=audit,rows=rows,synthetics=12,synthetic_icp_trace=trace,wall_s=time.monotonic()-t,
        peak_allocated_gib=torch.cuda.max_memory_allocated()/2**30,peak_rss_gib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/2**20,gt_files_read=False))
    c.seal(B);c.status(B,'BANK_SEALED')
if __name__=='__main__':
    try:{'freeze':freeze,'bank':bank}[sys.argv[1]]()
    except Exception as e:c.status(B,'STOPPED',error=repr(e));raise
