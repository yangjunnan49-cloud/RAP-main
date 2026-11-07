"""Independent Horn, direct normalization and brute-force ICP LMF0 validation."""
import time
import numpy as np
from scipy.spatial.distance import cdist
import local_motion_common as c

def horn(x,y):
    x=np.asarray(x,dtype=np.float64);y=np.asarray(y,dtype=np.float64);a=x.mean(0);b=y.mean(0);H=(x-a).T@(y-b)
    xx,xy,xz,yx,yy,yz,zx,zy,zz=H.ravel()
    K=np.array([[xx+yy+zz,yz-zy,zx-xz,xy-yx],[yz-zy,xx-yy-zz,xy+yx,zx+xz],
        [zx-xz,xy+yx,-xx+yy-zz,yz+zy],[xy-yx,zx+xz,yz+zy,-xx-yy+zz]])
    _,v=np.linalg.eigh(K);w,xq,yq,zq=v[:,-1]
    R=np.array([[1-2*(yq*yq+zq*zq),2*(xq*yq-zq*w),2*(xq*zq+yq*w)],
        [2*(xq*yq+zq*w),1-2*(xq*xq+zq*zq),2*(yq*zq-xq*w)],
        [2*(xq*zq-yq*w),2*(yq*zq+xq*w),1-2*(xq*xq+yq*yq)]])
    T=np.eye(4);T[:3,:3]=R;T[:3,3]=b-R@a;return T
def decode(z,arm=''):
    cond=z[arm+'cond'];raw=z[arm+'raw'] if not arm else z[arm+'end_point_trajectory'][-1]
    counts=z[arm+'counts'];centers=z[arm+'centers'];scale=float(z[arm+'scale']);parts=[];cuts=np.r_[0,np.cumsum(counts)]
    for k,(a,b) in enumerate(zip(cuts[:-1],cuts[1:])):
        T=horn(cond[a:b],raw[a:b]);T[:3,3]=scale*T[:3,3]-T[:3,:3]@centers[k];parts.append(T)
    return np.array(parts)
def icp(a,b,init=None):
    T=np.eye(4) if init is None else init.copy();trace=[]
    for _ in range(30):
        q=b@T[:3,:3].T+T[:3,3];dd=cdist(q,a);ids=dd.argmin(1);d=dd[np.arange(len(b)),ids];keep=d<=3;assert keep.sum()>=20
        delta=horn(q[keep],a[ids[keep]]);T=delta@T;trace.append([int(keep.sum()),float(d[keep].mean())])
        if abs(delta-np.eye(4)).max()<1e-7:break
    return T,trace
def normalize(points):
    points=[p.astype(np.float64) for p in points];counts=np.array([len(p) for p in points]);anchor=int(np.argmax(counts))
    centers=np.array([p.mean(0) for p in points]);scale=float(abs(points[anchor]-centers[anchor]).max()*1.5)
    return np.concatenate([(p-centers[k])/scale for k,p in enumerate(points)]).astype(np.float32),scale,centers,counts
def causal(ids,times,t):return ids==[t-1,t,t-2] and times[2]<times[0]<times[1] and max(ids)<=t
def validate():
    B=c.PREFLIGHT;t0=time.monotonic();f=c.check_freeze(B);c.check_seal(B);bank=c.read(B/'bank.json');md=0.;ms=0.
    assert not bank['gt_files_read'] and bank['checkpoint']['rap_keys']==344 and bank['checkpoint']['descriptor_keys']==58
    assert bank['checkpoint']['strict'] and bank['checkpoint']['weights_only']
    assert len(f['census']['rows'])==58 and len(f['census']['exclusions'])==6
    for seq,n in c.SEQS.items():
        m=c.read(c.source(seq)/'source_frames.json');ts=np.loadtxt(c.DATA/'sequences'/seq/'times.txt')
        for t in range(200,n,200):
            ids=[t-1,t,t-2];r=next(r for r in f['census']['rows'] if r['seq']==seq and r['t']==t)
            assert r['ids']==ids and r['times']==ts[ids].tolist() and causal(ids,r['times'],t)
            assert r['paths']==[m['scan_files'][i] for i in ids]
    for ids,ts in [([199,200,201],[1,2,3]),([199,200,199],[1,2,1]),([198,200,199],[1,3,2])]:assert not causal(ids,ts,200)
    for p in sorted((B/'bank').glob('synthetic_[0-9]*.npz')):
        with np.load(p,allow_pickle=False) as z:
            pp=np.split(z['points'],3);cond,scale,centers,counts=normalize(pp)
            assert np.array_equal(cond,z['cond']) and abs(scale-float(z['scale']))<1e-12 and abs(centers-z['centers']).max()<1e-12
            parts=decode(z);assert abs(parts-z['parts']).max()<1e-9;ms=max(ms,float(abs(parts-z['expected']).max()));assert ms<2e-6
            gp=[];cuts=np.r_[0,np.cumsum(counts)]
            for k,(a,b) in enumerate(zip(cuts[:-1],cuts[1:])):
                T=horn(cond[a:b],z['gauged'][a:b]);T[:3,3]=scale*T[:3,3]-T[:3,:3]@centers[k];gp.append(T)
            assert abs(np.array(gp)-z['gauge_parts']).max()<1e-9
            assert abs(np.linalg.inv(parts[0])@parts[1]-np.linalg.inv(gp[0])@gp[1]).max()<1e-9
    with np.load(B/'bank'/'synthetic_icp.npz',allow_pickle=False) as z:
        pp=np.split(z['points'],3);two,_=icp(pp[0],pp[1]);support,_=icp(pp[0],pp[2]);three,_=icp(np.concatenate([pp[0],pp[2]@support[:3,:3].T+support[:3,3]]),pp[1],two)
        assert max(abs(two-z['G2']).max(),abs(three-z['G3']).max(),abs(support-z['support']).max())<1e-9
    for row in bank['rows']:
        if row['kind']=='native':
            with np.load(B/'bank'/f"native_{row['seq']}.npz",allow_pickle=False) as z,np.load(c.F2/row['seq']/row['pair']/'N0.npz',allow_pickle=False) as old:
                d=max(float(abs(z[k]-old[k]).max()) for k in ['trajectory','end_point_trajectory']);assert d==row['max_delta'] and d<=1e-5
            continue
        with np.load(B/'bank'/f"local_{row['seq']}.npz",allow_pickle=False) as z:
            pp=np.split(z['points'],3)
            for arm,num in [('R3_',3),('R2_',2)]:
                cond,scale,centers,counts=normalize(pp[:num]);assert np.array_equal(cond,z[arm+'cond'])
                assert abs(centers-z[arm+'centers']).max()<1e-12 and abs(scale-float(z[arm+'scale']))<1e-12
                parts=decode(z,arm);pose=np.linalg.inv(parts[0])@parts[1];d=max(float(abs(parts-z[arm+'parts']).max()),float(abs(pose-z[arm+'pose']).max()));md=max(md,d);assert d<1e-8
                assert np.isfinite(z[arm+'end_point_trajectory']).all() and np.isfinite(z[arm+'trajectory']).all()
            two,tr2=icp(pp[0],pp[1]);support,trs=icp(pp[0],pp[2]);three,tr3=icp(np.concatenate([pp[0],pp[2]@support[:3,:3].T+support[:3,3]]),pp[1],two)
            for key,T,tr in [('G2',two,tr2),('G3',three,tr3),('support',support,trs)]:
                d=float(abs(T-z[key+'_pose']).max());md=max(md,d);assert d<1e-8
                assert np.asarray(tr).shape==np.asarray(row['icp_trace'][key]).shape and abs(np.asarray(tr)-np.asarray(row['icp_trace'][key])).max()<1e-8
            assert row['repeat_max_delta']<=1e-5 and row['dummy_gt_invariant']
            for key in ['R2','R3','G2','G3']:
                R=z[key+'_pose'][:3,:3];assert abs(R.T@R-np.eye(3)).max()<1e-9 and abs(np.linalg.det(R)-1)<1e-9
    total=bank['wall_s']+time.monotonic()-t0;size=sum(p.stat().st_size for p in B.rglob('*') if p.is_file())
    assert total<1200 and bank['peak_allocated_gib']<12 and bank['peak_rss_gib']<4 and size<100000000
    c.check_freeze(B);c.check_seal(B)
    c.save(B/'validation.json',dict(utc=c.now(),passed=True,decision='PASS_CAUSAL_LOCAL_MOTION_FEASIBILITY',census_windows=58,
        structural_exclusions=6,local_windows=6,native_replays=2,synthetic_cases=12,max_independent_delta=md,
        max_synthetic_known_pose_delta=ms,total_wall_s=total,validator_wall_s=time.monotonic()-t0,artifact_bytes_before_report=size,gt_files_read=False,
        checks=['freeze/strict restricted loading','census IDs/paths/times and causal negative controls','direct normalization and synthetic order/gauge checks',
                'two saved native raw/state replays','six repeated pipelines and dummy-label invariance','all Horn part/relative fits',
                'brute-force ICP controls and support transport','resource caps and immutable banks']))
    c.status(B,'VALIDATED',decision='PASS_CAUSAL_LOCAL_MOTION_FEASIBILITY');print('LMF0 independent validation passed',md,flush=True)
if __name__=='__main__':validate()
