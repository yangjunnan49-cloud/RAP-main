"""GT-free frozen saved-flow response extraction. No inference/graph edits."""
import hashlib,json,sys,time,resource
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
from scipy.spatial.transform import Rotation

MAIN=Path('/mnt/e/githouse/RAP-main')
B=MAIN/'docs/maintenance/2026-10-05/flow-directional-response-01'
OLD=MAIN/'docs/maintenance/2026-09-27/f2-structured-dev-01'
D=np.array([.03]*3+[.20]*3)
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def now(): return datetime.now(timezone.utc).isoformat()
def save(p,x):
    with Path(p).open('x') as f: json.dump(x,f,indent=2,allow_nan=False); f.write('\n')
def state(s,**kw): (B/'STATUS.json').write_text(json.dumps(dict(stage=s,utc=now(),**kw),indent=2)+'\n')
def selection(): return [dict(seq=s,key=r['key']) for s in ['00','08'] for r in read(OLD/f'inputs_{s}.json')[:4]]
def files():
    p=[B/'PROTOCOL.md',B/'RESEARCH_MEMO.md',Path(__file__),Path(__file__).with_name('validate_flow_directional_response.py'),OLD/'artifact_hashes.json',OLD/'validation.json',MAIN/'rectified_point_flow/sampler.py',MAIN/'rectified_point_flow/procrustes.py']
    p += [OLD/f'inputs_{s}.json' for s in ['00','08']]
    p += [OLD/r['seq']/r['key']/n for r in selection() for n in ['inputs.npz','N0.npz']]
    return sorted(set(p))
def verify():
    assert read(B/'freeze.json')['files']=={str(p):sha(p) for p in files()}
def freeze():
    assert not (B/'bank').exists()
    original=read(OLD/'artifact_hashes.json')
    for r in selection():
        for n in ['inputs.npz','N0.npz']:
            rel=f"{r['seq']}/{r['key']}/{n}"; assert sha(OLD/rel)==original[rel]
    save(B/'freeze.json',dict(utc=now(),files={str(p):sha(p) for p in files()},selection=selection(),gt_files_read=False)); state('FROZEN')
    print('frozen',len(files()),'identities',len(selection()),'pairs',flush=True)
def fit(x,y):
    u,_,v=np.linalg.svd((x-x.mean(0)).T@(y-y.mean(0))); f=np.eye(3); f[2,2]=np.linalg.det(v.T@u.T)
    T=np.eye(4); T[:3,:3]=v.T@f@u.T; T[:3,3]=y.mean(0)-T[:3,:3]@x.mean(0); return T
def apply(T,x): return x@T[:3,:3].T+T[:3,3]
def inv(T):
    Q=np.eye(4); Q[:3,:3]=T[:3,:3].T; Q[:3,3]=-Q[:3,:3]@T[:3,3]; return Q
def log(T):
    w=Rotation.from_matrix(T[:3,:3]).as_rotvec(); th=np.linalg.norm(w)
    W=np.array([[0,-w[2],w[1]],[w[2],0,-w[0]],[-w[1],w[0],0]])
    c=1/12+th*th/720 if th<1e-4 else (1-.5*th/np.tan(.5*th))/(th*th)
    return np.r_[w,(np.eye(3)-.5*W+c*W@W)@T[:3,3]]
def regions(q):
    idx=[int(np.argmax(np.sum((q-q.mean(0))**2,axis=1)))]; dist=np.sum((q-q[idx[0]])**2,axis=1)
    for _ in range(7):
        idx.append(int(np.argmax(dist))); dist=np.minimum(dist,np.sum((q-q[idx[-1]])**2,axis=1))
    labels=np.argmin(np.sum((q[:,None,:]-q[idx][None,:,:])**2,axis=2),axis=1)
    return np.asarray(idx),labels
def cov(x):
    z=x-x.mean(0); return 7/8*z.T@z
def extract(x,ys):
    full=[]; poses=[]
    for y in ys:
        A=fit(x[0],y[0]); C=fit(x[1],y[1]); poses.append([A,C]); full.append(inv(A)@C)
    idx,labels=regions(np.concatenate([apply(poses[-1][k],x[k]) for k in [0,1]])); labs=np.split(labels,[len(x[0])])
    joint=[]; ia=[]; ib=[]; remaining=[]
    for (A,C),T,y in zip(poses,full,ys):
        j=[]; a=[]; b=[]
        for r in range(8):
            masks=[labs[k]!=r for k in [0,1]]; remaining.append([int(m.sum()) for m in masks]); assert min(remaining[-1])>=200
            U,V=[fit(x[k][masks[k]],y[k][masks[k]]) for k in [0,1]]
            j.append(log(inv(T)@inv(U)@V)); a.append(log(inv(T)@inv(U)@C)); b.append(log(inv(T)@inv(A)@V))
        joint.append(j); ia.append(a); ib.append(b)
    full=np.asarray(full); joint=np.asarray(joint); ia=np.asarray(ia); ib=np.asarray(ib)
    late=np.array([log(inv(full[-1])@T) for T in full]); Ctime=late.T@late/3
    Cjoint=np.mean([cov(j) for j in joint],axis=0); Cind=np.mean([cov(a)+cov(b) for a,b in zip(ia,ib)],axis=0)
    return dict(full=full,landmarks=idx,labels=labels,remaining=np.asarray(remaining),joint=joint,independent_a=ia,independent_b=ib,late=late,C_time=Ctime,C_joint=Cjoint,C_independent=Cind,C_total=Cjoint+Ctime,C_control=Cind+Ctime)
def sources(r):
    p=OLD/r['seq']/r['key']
    with np.load(p/'inputs.npz',allow_pickle=False) as z:
        counts=z['counts']; cuts=np.r_[0,np.cumsum(counts)]; scale=float(z['scale']); centers=z['centers']; cond=z['cond'].astype(float)
        x=[cond[cuts[k]:cuts[k+1]]*scale+centers[k] for k in [0,3]]
    with np.load(p/'N0.npz',allow_pickle=False) as z:
        ys=[[y[cuts[k]:cuts[k+1]].astype(float)*scale for k in [0,3]] for y in z['end_point_trajectory'][-3:]]; T=z['T'].copy()
    return x,ys,T
def synthetic():
    rng=np.random.Generator(np.random.PCG64(20261005)); x=[rng.normal(size=(1024,3))*[10,7,3] for _ in range(2)]
    identity=[[p.copy() for p in x] for _ in range(3)]
    deform=[[p.copy() for p in x] for _ in range(3)]
    for y in deform: y[1][:,2]+=.5*np.sin(x[1][:,0]/3)+.2*np.tanh(x[1][:,1]/4)
    wrong=[[x[0].copy(),x[1]+[0,0,2]] for _ in range(3)]
    return [('synthetic-rigid',x,identity,np.eye(4)),('synthetic-deformed',x,deform,None),('synthetic-wrong-rigid',x,wrong,np.eye(4))]
def gauge():
    G=np.eye(4); G[:3,:3]=Rotation.from_rotvec([.21,-.13,.09]).as_matrix(); G[:3,3]=[7,-3,2]; return G
def describe(a):
    C=a['C_total']/D[:,None]/D[None,:]; eig=np.linalg.eigvalsh(C)
    return dict(trace_normalized=float(np.trace(C)),max_eigen_share=float(eig[-1]/sum(eig)) if sum(eig)>1e-20 else None,joint_independent_relative_difference=float(np.linalg.norm(a['C_joint']-a['C_independent'])/max(np.linalg.norm(a['C_independent']),1e-20)),min_retained=int(a['remaining'].min()))
def build():
    verify(); t=time.monotonic(); (B/'bank').mkdir(); (B/'INCOMPLETE').write_text('Independent preflight validation pending\n'); state('RUNNING')
    cases=synthetic()+[(r['key'],*sources(r)) for r in selection()]; rows=[]
    for name,x,ys,T in cases:
        a=extract(x,ys); np.savez_compressed(B/'bank'/f'{name}.npz',**a)
        g=extract(x,[[apply(gauge(),p) for p in y] for y in ys]); np.savez_compressed(B/'bank'/f'{name}-gauge.npz',**g)
        assert np.array_equal(a['labels'],g['labels']) and np.array_equal(a['landmarks'],g['landmarks'])
        row=dict(name=name,decode_max_delta=float(np.max(np.abs(a['full'][-1]-T))) if T is not None else None,gauge_pose_delta=float(np.max(np.abs(a['full']-g['full']))),gauge_matrix_delta=float(np.max(np.abs(a['C_total']-g['C_total']))),**describe(a)); rows.append(row)
        print(name,'decode',row['decode_max_delta'],'gauge',row['gauge_matrix_delta'],flush=True)
    save(B/'bank/summary.json',dict(rows=rows,wall_s=time.monotonic()-t,peak_rss_gib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/2**20,gt_files_read=False))
    verify(); assert time.monotonic()-t<300
    save(B/'bank_seal.json',dict(utc=now(),freeze_sha256=sha(B/'freeze.json'),files={str(p.relative_to(B/'bank')):sha(p) for p in (B/'bank').iterdir()})); state('BANK_SEALED')
if __name__=='__main__': {'freeze':freeze,'bank':build}[sys.argv[1]]()
