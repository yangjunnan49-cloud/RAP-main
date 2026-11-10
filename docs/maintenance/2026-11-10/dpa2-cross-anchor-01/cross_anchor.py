"""DPA2 fixed endpoint/support cross evaluation; no registration updates."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

R=Path(__file__).resolve().parent
ATOL,RTOL=1e-6,1e-3

def read(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):
    with p.open('x') as f: json.dump(x,f,indent=2,allow_nan=False);f.write('\n')

def imports():
    global np,cKDTree
    import numpy as np
    from scipy.spatial import cKDTree
    assert 'torch' not in sys.modules and 'open3d' not in sys.modules

class Queries:
    def __init__(self,limit):self.limit=limit;self.count=0
    def query(self,tree,points):
        assert self.count<self.limit,'Query budget exhausted'
        self.count+=1
        return tree.query(points,workers=1)

def rho(r):return np.where(abs(r)<=.5,.5*r*r,.5*(abs(r)-.25))
def moved(points,T):return points@T[:3,:3].T+T[:3,3]
def loss(src,tgt,normals,ids,T):
    if len(src)==0:return None
    rr=np.einsum('ij,ij->i',moved(src,T)-tgt[ids],normals[ids])
    return float(rho(rr).mean())
def preference(row):
    if any(x is None for x in row):return 'EMPTY'
    diff=row[1]-row[0];tol=ATOL+RTOL*max(abs(x) for x in row)
    return 'T0' if diff>tol else 'T1' if diff<-tol else 'FLAT'

def direction(source,target,normals,transforms,budget):
    tree=cKDTree(target);arrays={};supports=[]
    for k,T in enumerate(transforms):
        d,j=budget.query(tree,moved(source,T))
        arrays[f'd{k}']=d;arrays[f'j{k}']=j.astype(np.int32)
        supports.append(np.flatnonzero(d<=.75))
    common=np.intersect1d(*supports);union=np.union1d(*supports)
    full=[];intersection=[]
    for k,s in enumerate(supports):
        full.append([loss(source[s],target,normals,arrays[f'j{k}'][s],T) for T in transforms])
        intersection.append([loss(source[common],target,normals,arrays[f'j{k}'][common],T) for T in transforms])
    if len(common):
        j0,j1=[arrays[f'j{k}'][common] for k in [0,1]]
        angles=np.degrees(np.arccos(np.clip(abs(np.einsum('ij,ij->i',normals[j0],normals[j1])),0,1)))
        changed=float(np.mean(j0!=j1)); quantiles=np.quantile(angles,[0,.25,.5,.75,.95,1]).tolist()
    else: changed=None;quantiles=None
    return dict(counts=[len(s) for s in supports],source_count=len(source),intersection_count=len(common),union_count=len(union),
        intersection_over_union=len(common)/len(union) if len(union) else None,
        intersection_over_support=[len(common)/len(s) if len(s) else None for s in supports],
        correspondence_changed_fraction=changed,normal_abs_angle_deg_quantiles=quantiles,
        full_support_loss=full,intersection_loss=intersection,
        full_preference=[preference(row) for row in full],intersection_preference=[preference(row) for row in intersection]),arrays

def pair(a,b,na,nb,T0,T1,budget):
    f,fa=direction(b,a,na,[T0,T1],budget)
    inverse=[np.linalg.solve(T,np.eye(4)) for T in [T0,T1]]
    r,ra=direction(a,b,nb,inverse,budget)
    combined={f'f_{k}':v for k,v in fa.items()};combined.update({f'r_{k}':v for k,v in ra.items()})
    return dict(forward=f,reverse=r),combined

def synthetic():
    imports();budget=Queries(16);notes=[]
    normals=lambda n:np.tile([0.,1.,0.],(n,1))
    I=np.eye(4);t=I.copy();t[1,3]=-.2
    a=np.array([[x,0.,0.] for x in [0.,10.,20.] ]);b=a.copy();b[:,1]=.2
    x,_=pair(a,b,normals(3),normals(3),I,t,budget)
    assert all(x[d]['full_preference']==['T1','T1'] for d in ['forward','reverse'])
    np.testing.assert_allclose(x['forward']['full_support_loss'],[[.02,0.],[.02,0.]],atol=1e-12);notes.append('same surface true displacement')
    a=np.array([[x,y,0.] for x in [0.,10.,20.] for y in [0.,.6]])
    b=np.array([[x,0.,0.] for x in [0.,10.,20.] ]);t=I.copy();t[1,3]=.6
    x,_=pair(a,b,normals(6),normals(3),I,t,budget)
    assert x['forward']['full_preference']==['T0','T1'] and x['forward']['correspondence_changed_fraction']==1
    assert x['forward']['normal_abs_angle_deg_quantiles']==[0.]*6;notes.append('repeated surface anchor switch')
    a=np.array([[0.,0.,0.]]);b=np.array([[0.,y,0.] for y in [0.,.5,1.2]])
    t=I.copy();t[1,3]=-.5
    x,_=pair(a,b,normals(1),normals(3),I,t,budget)
    assert x['forward']['counts']==[2,3] and x['forward']['intersection_count']==2 and x['forward']['union_count']==3
    notes.append('changing support with common source points')
    b=np.array([[0.,0.,0.],[0.,2.,0.]]);t=I.copy();t[1,3]=-2
    x,_=pair(a,b,normals(1),normals(2),I,t,budget)
    assert x['forward']['intersection_count']==0 and x['forward']['intersection_loss']==[[None,None],[None,None]]
    assert x['forward']['intersection_preference']==['EMPTY','EMPTY'];notes.append('empty intersection remains unknown')
    q=I.copy();q[0,0]=1.000001;q[:3,3]=[1.,2.,3.]
    p=np.array([[2.,3.,4.]]);np.testing.assert_allclose(moved(moved(p,q),np.linalg.solve(q,I)),p,atol=1e-12)
    assert np.max(abs(np.linalg.solve(q,I)[:3,:3]-q[:3,:3].T))>1e-6;notes.append('strict inverse for finite precision rotations')
    np.testing.assert_allclose(rho(np.array([0.,.5,1.,-1.])),[0.,.125,.375,.375]);notes.append('Huber piecewise analytic values')
    try:Queries(0).query(cKDTree(a),a)
    except AssertionError:pass
    else:raise AssertionError('Budget must reject before query')
    notes.append('hard query cap')
    # Brute-force nearest-distance check only on this synthetic fixture.
    d,_=cKDTree(a).query(b)
    np.testing.assert_allclose(d,np.linalg.norm(b[:,None]-a[None],axis=2).min(axis=1));notes.append('synthetic nearest distance')
    assert budget.count==16
    save(R/'synthetic.json',dict(passed=True,checks=notes,synthetic_budgeted_queries=16,atol=ATOL,rtol=RTOL))
    print('PASS',len(notes),'synthetic checks')

def freeze():
    assert read(R/'preflight.json')['passed']
    expected=read(R/'INPUTS.json')['files'];total=0
    for name,entry in expected.items():
        p=R/'inputs'/name;assert sha(p)==entry['sha256'];assert p.stat().st_size<=4*2**20;total+=p.stat().st_size
    assert len(expected)==4 and total<=16*2**20
    files=['cross_anchor.py','supervise.py','verify_cross.py','PROTOCOL_CN.md','INPUTS.json','preflight.json','synthetic.json','parent/freeze.json','parent/RESULTS.json','parent/INDEPENDENT_CHECKS.json']
    save(R/'freeze.json',dict(files={name:sha(R/name) for name in files},inputs=expected,queries_limit=16,output_limit_bytes=8*2**20,
         wall_limit_s=60,AS_limit_bytes=2*2**30-64*2**20,source_status='UNKNOWN_RETAINED'))
    print('Frozen',len(files),'implementation/evidence files and 4 derived inputs')

def run():
    start=time.monotonic();frozen=read(R/'freeze.json')
    assert all(sha(R/name)==h for name,h in frozen['files'].items())
    assert all(sha(R/'inputs'/name)==entry['sha256'] for name,entry in frozen['inputs'].items())
    imports();out=R/'results';out.mkdir(exist_ok=False);budget=Queries(16);results=[]
    prior={p['pair']:p for p in read(R/'parent/RESULTS.json')['pairs']}
    for name in sorted(frozen['inputs']):
        pid=Path(name).stem
        with np.load(R/'inputs'/name,allow_pickle=False) as z:
            arrays={k:z[k] for k in ['a','b','na','nb','final','reference']}
        a,b,na,nb=[arrays[k] for k in ['a','b','na','nb']]
        for cloud,n in [(a,na),(b,nb)]:
            assert 0<len(cloud)<=30000 and cloud.shape==n.shape and cloud.shape[1]==3
            assert np.isfinite(cloud).all() and np.isfinite(n).all() and np.allclose(np.linalg.norm(n,axis=1),1,atol=1e-6)
        T0=arrays['final'];T1=T0.copy();T1[1:3,3]=arrays['reference'][1:3,3]
        for T in [T0,T1]:assert T.shape==(4,4) and np.isfinite(T).all() and np.allclose(T[3],[0,0,0,1])
        row,support=pair(a,b,na,nb,T0,T1,budget)
        old=prior[pid];row.update(pair=pid,role=old['role'],event_group=old['event_group'],T0=T0.tolist(),T1=T1.tolist())
        np.savez_compressed(out/f'{pid}-queries.npz',**support)
        save(out/f'{pid}.json',row);results.append(row)
        print(pid,[(d,row[d]['full_preference'],row[d]['intersection_preference']) for d in ['forward','reverse']],flush=True)
    assert budget.count==16
    save(out/'RESULTS.json',dict(status='COMPLETE_DEVELOPMENT_CROSS_ANCHOR_DIAGNOSTIC',pairs=results,queries=budget.count,
        original_raw_reads=0,new_model_ICP_training_calls=0,worker_wall_s=time.monotonic()-start,
        peak_rss_kib=__import__('resource').getrusage(__import__('resource').RUSAGE_SELF).ru_maxrss,
        torch_imported='torch' in sys.modules,open3d_imported='open3d' in sys.modules,numpy=np.__version__,physical_reference_certified=False))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['synthetic','freeze','run']);a=p.parse_args()
    {'synthetic':synthetic,'freeze':freeze,'run':run}[a.mode]()
