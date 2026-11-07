"""Independent Horn quaternion fits and matrix-log response validation."""
import time,resource
import numpy as np
from scipy.linalg import logm
from scipy.spatial.transform import Rotation
import flow_directional_response as f

def fit(x,y):
    X=x-x.mean(0); Y=y-y.mean(0); H=X.T@Y; t=np.trace(H)
    z=np.array([H[1,2]-H[2,1],H[2,0]-H[0,2],H[0,1]-H[1,0]])
    N=np.empty((4,4)); N[0,0]=t; N[0,1:]=z; N[1:,0]=z; N[1:,1:]=H+H.T-t*np.eye(3)
    _,v=np.linalg.eigh(N); q=v[:,-1]; R=Rotation.from_quat(np.r_[q[1:],q[0]]).as_matrix()
    T=np.eye(4); T[:3,:3]=R; T[:3,3]=y.mean(0)-R@x.mean(0); return T
def tangent(T):
    L=logm(T); assert np.max(np.abs(np.imag(L)))<1e-10; L=np.real(L)
    return np.array([L[2,1],L[0,2],L[1,0],*L[:3,3]])
def partition(q):
    ids=[int(np.argmax(np.linalg.norm(q-q.mean(0),axis=1)))]; d=np.linalg.norm(q-q[ids[0]],axis=1)
    for k in range(7):
        ids.append(int(np.argmax(d))); d=np.minimum(d,np.linalg.norm(q-q[ids[-1]],axis=1))
    labels=np.argmin(np.linalg.norm(q[:,None]-q[ids],axis=2),axis=1); return ids,labels
def matrix(a):
    centered=a-a.mean(axis=0); return sum(np.outer(v,v) for v in centered)*.875
def recompute(x,ys):
    ps=[[fit(x[k],y[k]) for k in [0,1]] for y in ys]; full=np.array([np.linalg.solve(A,B) for A,B in ps])
    ids,labels=partition(np.concatenate([x[k]@ps[-1][k][:3,:3].T+ps[-1][k][:3,3] for k in [0,1]])); labs=np.split(labels,[len(x[0])]); joint=[]; ia=[]; ib=[]; remaining=[]
    for y,(A,B),T in zip(ys,ps,full):
        j=[]; a=[]; b=[]
        for region in range(8):
            masks=[l!=region for l in labs]; remaining.append([int(m.sum()) for m in masks]); assert min(remaining[-1])>=200
            U,V=[fit(x[k][masks[k]],y[k][masks[k]]) for k in [0,1]]
            j.append(tangent(np.linalg.solve(T,np.linalg.solve(U,V)))); a.append(tangent(np.linalg.solve(T,np.linalg.solve(U,B)))); b.append(tangent(np.linalg.solve(T,np.linalg.solve(A,V))))
        joint.append(j); ia.append(a); ib.append(b)
    joint=np.array(joint); ia=np.array(ia); ib=np.array(ib); late=np.array([tangent(np.linalg.solve(full[-1],T)) for T in full]); Ct=sum(np.outer(v,v) for v in late)/3
    Cj=sum(matrix(a) for a in joint)/3; Ci=sum(matrix(a)+matrix(b) for a,b in zip(ia,ib))/3
    return dict(full=full,landmarks=np.array(ids),labels=labels,remaining=np.array(remaining),joint=joint,independent_a=ia,independent_b=ib,late=late,C_time=Ct,C_joint=Cj,C_independent=Ci,C_total=Cj+Ct,C_control=Ci+Ct)
def main():
    t=time.monotonic(); f.verify(); B=f.B; bank=B/'bank'; seal=f.read(B/'bank_seal.json'); assert seal['freeze_sha256']==f.sha(B/'freeze.json') and seal['files']=={str(p.relative_to(bank)):f.sha(p) for p in bank.iterdir()}
    cases=f.synthetic()+[(r['key'],*f.sources(r)) for r in f.selection()]; maximum=0.; poses=0.; gauge=0.; known={}; counter=0.
    for name,x,ys,T in cases:
        for suffix,Y in [('',ys),('-gauge',[[p@f.gauge()[:3,:3].T+f.gauge()[:3,3] for p in y] for y in ys])]:
            a=recompute(x,Y)
            with np.load(bank/f'{name}{suffix}.npz',allow_pickle=False) as z:
                for k,v in a.items():
                    delta=float(np.max(np.abs(v-z[k]))); assert delta<=1e-8,(name,suffix,k,delta); maximum=max(maximum,delta)
            for k in ['C_joint','C_independent','C_time','C_total','C_control']:
                assert np.all(np.isfinite(a[k])) and np.max(np.abs(a[k]-a[k].T))<1e-10 and np.linalg.eigvalsh(a[k]).min()>=-1e-10
            if not suffix: original=a; known[name]=np.linalg.norm(a['C_total'])
            else:
                assert np.array_equal(original['labels'],a['labels']) and np.array_equal(original['landmarks'],a['landmarks'])
                delta=max(np.max(np.abs(original['full']-a['full'])),np.max(np.abs(original['C_total']-a['C_total']))); assert delta<=1e-8; gauge=max(gauge,float(delta))
        if name not in ['synthetic-deformed','synthetic-wrong-rigid']:
            delta=float(np.max(np.abs(original['full'][-1]-T))); assert delta<=2e-4; poses=max(poses,delta)
        if name=='synthetic-wrong-rigid': counter=float(np.linalg.norm(original['full'][-1][:3,3]-T[:3,3])); assert counter>=1.9 and known[name]<=1e-16
        if name=='synthetic-deformed': assert np.trace(original['C_total'])>=1e-6
        print('independent',name,flush=True)
    assert known['synthetic-rigid']<=1e-16
    summary=f.read(bank/'summary.json'); wall=summary['wall_s']+time.monotonic()-t; peak=max(summary['peak_rss_gib'],resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/2**20); size=sum(p.stat().st_size for p in B.rglob('*') if p.is_file()); assert wall<300 and peak<1 and size<10000000; f.verify()
    f.save(B/'validation.json',dict(passed=True,decision='PASS_GT_FREE_RESPONSE_PREFLIGHT',utc=f.now(),pairs=8,synthetic_cases=3,gauged_cases=11,max_independent_delta=maximum,max_decode_delta=poses,max_gauge_delta=gauge,rigid_wrong_error_m=counter,rigid_wrong_response_norm=known['synthetic-wrong-rigid'],total_wall_s=wall,peak_rss_gib=peak,artifact_bytes_before_report=size,gt_files_read=False,checks=['original selected F2 identities and pre-output freeze','Horn quaternion fits vs SVD','matrix logarithms vs analytic SE3 log','all partitions/deletions/full poses/matrices','PSD and common-gauge invariance','rigid/deformed/wrong-rigid analytic controls','resource caps and final frozen integrity']))
    f.state('VALIDATED',decision='PASS_GT_FREE_RESPONSE_PREFLIGHT',report='pending'); print('passed preflight',maximum,flush=True)
if __name__=='__main__': main()
