"""DPA4 geometry-only fixed candidate scoring; never read evaluation identities."""
import argparse,hashlib,json,sys,time
from pathlib import Path
R=Path(__file__).resolve().parent
ATOL,RTOL=1e-6,1e-3

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
def imports():
 global np,cKDTree
 import numpy as np
 from scipy.spatial import cKDTree
 assert 'torch' not in sys.modules and 'open3d' not in sys.modules
class Budget:
 def __init__(self,n):self.n=n;self.count=0
 def query(self,tree,points):
  assert self.count<self.n,'Query cap';self.count+=1;return tree.query(points,workers=1)
def decide(scores):
 finite=[i for i,s in enumerate(scores) if s is not None]
 if len(finite)==0:return None
 if len(finite)==1:return finite[0]
 delta=scores[1]-scores[0];tol=ATOL+RTOL*max(abs(s) for s in scores)
 return None if abs(delta)<=tol else (0 if delta>0 else 1)
def block_score(points,d,cosines):
 _,indices=np.unique(np.floor(points/2).astype(np.int64),axis=0,return_inverse=True)
 per=.5*(np.clip(d/.1,0,1)+np.clip((1-cosines)/(1-np.cos(np.deg2rad(15))),0,1))
 return float(np.mean(np.bincount(indices,weights=per)/np.bincount(indices)))
def direction(source,target,sn,tn,T,d,j):
 transformed=source@T[:3,:3].T+T[:3,3]
 n=sn@T[:3,:3].T;n/=np.linalg.norm(n,axis=1)[:,None]
 matched=tn[j];matched=matched/np.linalg.norm(matched,axis=1)[:,None]
 cosines=np.clip(abs(np.sum(n*matched,axis=1)),0,1)
 residual=np.sum((transformed-target[j])*matched,axis=1);mask=d<=.75
 if mask.any():
  r=residual[mask];loss=float(np.mean(np.where(abs(r)<=.5,.5*r*r,.5*(abs(r)-.25))))
  yz=matched[mask,1:3];eigen=np.linalg.eigvalsh(yz.T@yz/len(yz)).tolist()
 else:loss=None;eigen=None
 return dict(nn_mean=float(d.mean()),plane_huber=loss,block_score=block_score(source,d,cosines),source_count=len(source),gate_count=int(mask.sum()),
   normal_median_deg=float(np.median(np.degrees(np.arccos(cosines)))),yz_eigenvalues=eigen)
def selftest():
 imports();notes=[]
 assert decide([0.,0.]) is None and decide([0.,1e-7]) is None and decide([0.,.01])==0;notes.append('stable tie band')
 assert decide([None,None]) is None and decide([None,0.])==1;notes.append('empty support handling')
 p=np.array([[.1,.1,.1],[2.1,.1,.1]]);d=np.array([0.,.1]);c=np.ones(2)
 assert abs(block_score(p,d,c)-.25)<1e-12;notes.append('equal spatial cell weighting')
 assert abs(block_score(np.repeat(p,[9,1],axis=0),np.repeat(d,[9,1]),np.ones(10))-.25)<1e-12;notes.append('duplicate zero-score cell does not add votes')
 assert block_score(p,np.zeros(2),np.ones(2))==0;notes.append('exact normal and distance score')
 assert abs(block_score(p,np.ones(2),np.zeros(2))-1)<1e-12;notes.append('clipped residual limits')
 T=np.eye(4);T[:3,:3]=[[0,-1,0],[1,0,0],[0,0,1]];T[:3,3]=[.3,.2,.1];v=p@T[:3,:3].T+T[:3,3];inv=np.linalg.solve(T,np.eye(4));np.testing.assert_allclose(v@inv[:3,:3].T+inv[:3,3],p,atol=1e-12);notes.append('strict reverse transform')
 q=np.array([[0.,0.,0.],[2.,0.,0.]]);r=np.array([[.1,0.,0.],[1.8,0.,0.] ]);dd,_=cKDTree(q).query(r);np.testing.assert_allclose(dd,np.linalg.norm(r[:,None]-q[None],axis=2).min(axis=1));notes.append('synthetic NN versus exhaustive distances')
 try:Budget(0).query(cKDTree(q),r)
 except AssertionError:pass
 else:raise AssertionError('cap must reject')
 notes.append('query cap rejection')
 save(R/'synthetic.json',dict(passed=True,checks=notes));print('PASS',len(notes),'preflight geometry checks')
def freeze():
 assert read(R/'preflight.json')['passed'];entries=read(R/'INPUTS.json')['files'];assert len(entries)==8
 assert all(sha(R/'inputs'/p)==e['sha256'] for p,e in entries.items())
 names=['mechanism.py','build_cases.py','verify_mechanism.py','supervise.py','PROTOCOL_CN.md','INPUTS.json','synthetic.json','preflight.json']
 save(R/'freeze.json',dict(files={p:sha(R/p) for p in names},inputs=entries,evaluation_only_sha256=sha(R/'EVALUATION_ONLY.json'),query_limit=32))
 print('Frozen generator, scorer, evaluator and eight inputs')
def run():
 start=time.monotonic();frozen=read(R/'freeze.json');assert all(sha(R/p)==h for p,h in frozen['files'].items())
 assert all(sha(R/'inputs'/p)==e['sha256'] for p,e in frozen['inputs'].items());imports()
 out=R/'results';out.mkdir(exist_ok=False);budget=Budget(32);rows=[]
 for name in sorted(frozen['inputs']):
  with np.load(R/'inputs'/name,allow_pickle=False) as z:
   assert set(z.files)=={'a','b','na','nb','candidates'};a,b,na,nb,Ts=[z[k] for k in ['a','b','na','nb','candidates']]
  assert max(len(a),len(b))<=2048 and len(Ts)==2
  trees=[cKDTree(a),cKDTree(b)];candidates=[];saved={}
  for k,T in enumerate(Ts):
   inv=np.linalg.solve(T,np.eye(4));df,jf=budget.query(trees[0],b@T[:3,:3].T+T[:3,3]);dr,jr=budget.query(trees[1],a@inv[:3,:3].T+inv[:3,3])
   f=direction(b,a,nb,na,T,df,jf);r=direction(a,b,na,nb,inv,dr,jr)
   mutual=(df<=.75)&(dr[jf]<=.75)&(jr[jf]==np.arange(len(b)));f['mutual_count']=int(mutual.sum())
   mutualr=(dr<=.75)&(df[jr]<=.75)&(jf[jr]==np.arange(len(a)));r['mutual_count']=int(mutualr.sum());assert f['mutual_count']==r['mutual_count']
   candidates.append(dict(index=k,forward=f,reverse=r))
   saved.update({f'{k}_df':df,f'{k}_jf':jf.astype(np.int32),f'{k}_dr':dr,f'{k}_jr':jr.astype(np.int32)})
  decisions={m:decide([c['forward'][m] for c in candidates]) for m in ['nn_mean','plane_huber','block_score']}
  row=dict(case=Path(name).stem,candidates=candidates,decisions=decisions)
  rows.append(row);np.savez_compressed(out/(row['case']+'-queries.npz'),**saved);save(out/(row['case']+'.json'),row)
  print(row['case'],decisions,flush=True)
 assert budget.count==32
 save(out/'RESULTS.json',dict(status='COMPLETE_CONTROLLED_MECHANISM_TEST',cases=rows,NN_queries=budget.count,evaluation_truth_read_by_scorer=False,real_data_reads=0,model_ICP_training_calls=0,
    worker_wall_s=time.monotonic()-start,peak_rss_kib=__import__('resource').getrusage(__import__('resource').RUSAGE_SELF).ru_maxrss))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('mode',choices=['selftest','freeze','run']);arg=p.parse_args();{'selftest':selftest,'freeze':freeze,'run':run}[arg.mode]()
