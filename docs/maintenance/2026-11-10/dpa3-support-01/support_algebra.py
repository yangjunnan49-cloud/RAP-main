"""DPA3 algebra on T0 saved correspondences; no tree, pose search or reference."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
R=Path(__file__).resolve().parent
ALLOWED=['a','b','na','nb','final','f_d0','f_j0','r_d0','r_j0']
Q=[0.,.1,.25,.5,.75,.9,.95,.99,1.]
BINS=[0.,15.,30.,60.,90.]
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
def imports():
 global np
 import numpy as np
 assert all(name not in sys.modules for name in ['scipy','torch','open3d'])
def normalize(n):
 norm=np.linalg.norm(n,axis=1)
 assert np.isfinite(n).all() and np.all(norm>0)
 return n/norm[:,None]
def weights(r):
 w=np.ones(len(r));np.divide(.5,abs(r),out=w,where=abs(r)>.5);return w
def gram(normals,w):
 if not len(normals):return None
 v=normals[:,1:3];G=(v.T*w)@v/len(v)
 eigenvectors_values,vectors=np.linalg.eigh(G)
 for j in range(2):
  if vectors[np.argmax(abs(vectors[:,j])),j]<0:vectors[:,j]*=-1
 return dict(matrix=G.tolist(),eigenvalues=eigenvectors_values.tolist(),eigenvectors_yz_columns=vectors.tolist(),trace=float(np.trace(G)),lambda_min_over_max=float(eigenvectors_values[0]/eigenvectors_values[1]) if eigenvectors_values[1]>0 else None)
def subset(normals,angles,residual,mask):
 n=normals[mask];a=angles[mask];r=residual[mask]
 if not len(n):return dict(count=0,normal_angle_deg_quantiles=None,normal_angle_bin_counts=[0]*4,abs_residual_quantiles=None,huber_weight_quantiles=None,huber_loss=None,unit_gram=None,huber_gram=None)
 w=weights(r);huber=np.where(abs(r)<=.5,.5*r*r,.5*(abs(r)-.25))
 return dict(count=len(n),normal_angle_deg_quantiles=np.quantile(a,Q).tolist(),normal_angle_bin_counts=np.histogram(a,BINS)[0].tolist(),
     abs_residual_quantiles=np.quantile(abs(r),Q).tolist(),huber_weight_quantiles=np.quantile(w,Q).tolist(),huber_loss=float(huber.mean()),unit_gram=gram(n,np.ones(len(n))),huber_gram=gram(n,w))
def direction(source,target,source_n,target_n,T,d,j,reverse_d,reverse_j):
 assert d.shape==j.shape==(len(source),) and len(reverse_d)==len(target)==len(reverse_j)
 assert np.isfinite(d).all() and np.all(d>=0) and np.all((j>=0)&(j<len(target)))
 assert np.all((reverse_j>=0)&(reverse_j<len(source))) and np.isfinite(reverse_d).all()
 all_mask=d<=.75
 mutual=all_mask&(reverse_d[j]<=.75)&(reverse_j[j]==np.arange(len(source)))
 sn=normalize(source_n@T[:3,:3].T);tn=normalize(target_n[j])
 angles=np.degrees(np.arccos(np.clip(abs(np.einsum('ij,ij->i',sn,tn)),0,1)))
 transformed=source@T[:3,:3].T+T[:3,3]
 np.testing.assert_allclose(np.linalg.norm(transformed-target[j],axis=1),d,atol=1e-12,rtol=1e-12)
 residual=np.einsum('ij,ij->i',transformed-target[j],tn)
 return dict(source_count=len(source),all_count=int(all_mask.sum()),mutual_count=int(mutual.sum()),
     distance_support_fraction=float(all_mask.mean()),mutual_fraction=float(mutual.sum()/all_mask.sum()) if all_mask.any() else None,
     all=subset(tn,angles,residual,all_mask),mutual=subset(tn,angles,residual,mutual))
def pair(z):
 f=direction(z['b'],z['a'],z['nb'],z['na'],z['final'],z['f_d0'],z['f_j0'],z['r_d0'],z['r_j0'])
 r=direction(z['a'],z['b'],z['na'],z['nb'],np.linalg.solve(z['final'],np.eye(4)),z['r_d0'],z['r_j0'],z['f_d0'],z['f_j0'])
 assert f['mutual_count']==r['mutual_count']
 return dict(forward=f,reverse=r)
def synthetic():
 imports();notes=[]
 # Identity one-to-one and one-to-many from saved exact distance pairs.
 I=np.eye(4);a=np.array([[0.,0.,0.],[2.,0.,0.] ]);b=np.array([[0.,0.,0.],[.2,0.,0.],[2.,0.,0.] ])
 na=np.tile([0.,1.,0.],(2,1));nb=np.tile([0.,1.,0.],(3,1))
 x=direction(b,a,nb,na,I,np.array([0.,.2,0.]),np.array([0,0,1]),np.array([0.,0.]),np.array([0,2]))
 assert x['all_count']==3 and x['mutual_count']==2;notes.append('many-to-one reciprocity')
 y=direction(a,a,na,na,I,np.zeros(2),np.arange(2),np.zeros(2),np.arange(2));assert y['mutual_count']==2 and y['mutual_fraction']==1;notes.append('one-to-one reciprocity')
 ny=np.array([[0.,1.,0.],[0.,-1.,0.] ]);g=gram(ny,np.ones(2));np.testing.assert_allclose(g['eigenvalues'],[0.,1.]);notes.append('one-direction yz spectrum')
 nyz=np.array([[0.,1.,0.],[0.,0.,1.] ]);np.testing.assert_allclose(gram(nyz,np.ones(2))['eigenvalues'],[.5,.5]);notes.append('two-direction yz spectrum')
 np.testing.assert_allclose(weights(np.array([0.,.25,.5,1.,-2.])),[1.,1.,1.,.5,.25]);notes.append('Huber weights including zero residual')
 assert gram(np.empty((0,3)),np.empty(0)) is None
 empty=subset(nyz,np.zeros(2),np.zeros(2),np.array([False,False]));assert empty['unit_gram'] is None and empty['normal_angle_deg_quantiles'] is None;notes.append('empty support preserved')
 nx=np.tile([1.,0.,0.],(2,1));zero=gram(nx,np.ones(2));assert zero['eigenvalues']==[0.,0.] and zero['lambda_min_over_max'] is None;notes.append('zero yz spectrum preserved')
 T=I.copy();T[:3,:3]=[[0.,-1.,0.],[1.,0.,0.],[0.,0.,1.]]
 src=np.tile([1.,0.,0.],(2,1));target=np.tile([0.,1.,0.],(2,1));q=normalize(src@T[:3,:3].T)
 assert np.max(np.degrees(np.arccos(np.clip(abs((q*target).sum(axis=1)),0,1))))==0;notes.append('normal rotation to target frame')
 for sign in [-1.,1.]:np.testing.assert_allclose(abs((q*target).sum(axis=1)),abs((sign*q*target).sum(axis=1)))
 np.testing.assert_allclose(gram(nyz,np.ones(2))['matrix'],gram(-nyz,np.ones(2))['matrix']);notes.append('normal sign invariance')
 assert np.histogram(np.array([0.,15.,30.,60.,90.]),BINS)[0].tolist()==[1,1,1,2];notes.append('fixed angle-bin boundaries')
 save(R/'synthetic.json',dict(passed=True,checks=notes,NN_queries=0,raw_reads=0));print('PASS',len(notes),'synthetic algebra cases')
def freeze():
 assert read(R/'preflight.json')['passed']
 inputs=read(R/'INPUTS.json');assert len(inputs['files'])==4
 for name,entry in inputs['files'].items():assert sha(R/'inputs'/name)==entry['sha256']
 names=['support_algebra.py','supervise.py','verify_algebra.py','PROTOCOL_CN.md','INPUTS.json','synthetic.json','preflight.json','prepare_inputs.py']
 save(R/'freeze.json',dict(files={name:sha(R/name) for name in names},inputs=inputs['files'],allowed_members=ALLOWED,NN_queries_limit=0,
     wall_limit_s=30,AS_limit_bytes=2*2**30-64*2**20,output_limit_bytes=4*2**20))
 print('Frozen implementation and whitelist-only inputs')
def run():
 start=time.monotonic();frozen=read(R/'freeze.json');assert all(sha(R/p)==h for p,h in frozen['files'].items())
 assert all(sha(R/'inputs'/p)==e['sha256'] for p,e in frozen['inputs'].items());imports()
 out=R/'results';out.mkdir(exist_ok=False);rows=[]
 for name,entry in frozen['inputs'].items():
  with np.load(R/'inputs'/name,allow_pickle=False) as f:
   assert set(f.files)==set(ALLOWED)
   z={key:f[key] for key in ALLOWED}
  for cloud,n in [(z['a'],z['na']),(z['b'],z['nb'])]:
   assert 0<len(cloud)<=30000 and cloud.shape==n.shape and cloud.shape[1]==3 and np.isfinite(cloud).all()
   assert np.allclose(np.linalg.norm(n,axis=1),1,atol=1e-6)
  T=z['final'];assert T.shape==(4,4) and np.isfinite(T).all() and np.allclose(T[3],[0,0,0,1])
  x=pair(z);x.update(pair=entry['pair'],role=entry['role'],event_group=entry['event_group'],gram_frames={'forward':'target a native yz','reverse':'target b native yz'})
  rows.append(x);save(out/(entry['pair']+'.json'),x)
  print(entry['pair'],[(d,x[d]['mutual_fraction'],x[d]['mutual']['normal_angle_deg_quantiles'][3],x[d]['mutual']['unit_gram']['eigenvalues']) for d in ['forward','reverse']],flush=True)
 save(out/'RESULTS.json',dict(status='COMPLETE_FIXED_T0_SUPPORT_DIAGNOSTIC',pairs=rows,NN_queries=0,raw_reads=0,forbidden_array_reads=0,
      model_ICP_training_calls=0,loaded_members=ALLOWED,worker_wall_s=time.monotonic()-start,
      peak_rss_kib=__import__('resource').getrusage(__import__('resource').RUSAGE_SELF).ru_maxrss,
      scipy_torch_open3d_imported=any(k in sys.modules for k in ['scipy','torch','open3d']),physical_reference_certified=False))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('mode',choices=['synthetic','freeze','run']);a=p.parse_args();{'synthetic':synthetic,'freeze':freeze,'run':run}[a.mode]()
