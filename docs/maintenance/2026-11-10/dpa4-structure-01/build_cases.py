"""Create fixed analytic controls; truth is written separately from scorer inputs."""
import hashlib,json
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent

def patch(u,center=(0.,0.,0.)):
 points=[];normals=[]
 for axis in range(3):
  other=[k for k in range(3) if k!=axis]
  for a in u:
   for b in u:
    p=np.array(center,dtype=float);p[other[0]]+=a;p[other[1]]+=b
    n=np.zeros(3);n[axis]=1.;points.append(p);normals.append(n)
 return np.array(points),np.array(normals)
def generate():
 out=R/'inputs';out.mkdir(exist_ok=False);rng=np.random.default_rng(311)
 core,ncore=patch([-.5,-.3,-.1,.1,.3,.5]);anchor,nanchor=patch([-.3,-.1,.1,.3],(2.8,2.6,2.4))
 angle=np.deg2rad(17.);G=np.eye(4);G[:3,:3]=[[np.cos(angle),-np.sin(angle),0],[np.sin(angle),np.cos(angle),0],[0,0,1]];G[:3,3]=[.37,-.41,.22]
 H=G.copy();H[1,3]+=8.;inv=np.linalg.inv(G)
 inputs={};truth={}
 for group in ['unique','repeat','visible_anchor','missing_anchor']:
  for density in ['uniform','uneven']:
   k=len(inputs);name=f'case{k:02d}';a=core.copy();na=ncore.copy();aids=np.arange(len(core))
   if group!='unique':
    a=np.concatenate([a,core+[0,8,0]]);na=np.concatenate([na,ncore]);aids=np.concatenate([aids,10000+np.arange(len(core))])
   if group in ['visible_anchor','missing_anchor']:
    a=np.concatenate([a,anchor]);na=np.concatenate([na,nanchor]);aids=np.concatenate([aids,20000+np.arange(len(anchor))])
   ids=np.arange(len(core))
   if density=='uneven':ids=np.concatenate([ids,np.tile(np.arange(36,72),4)])
   world=core[ids];nb=ncore[ids];bids=ids.copy()
   if group=='visible_anchor':world=np.concatenate([world,anchor]);nb=np.concatenate([nb,nanchor]);bids=np.concatenate([bids,20000+np.arange(len(anchor))])
   b=world@inv[:3,:3].T+inv[:3,3];nb=nb@inv[:3,:3].T
   pa=rng.permutation(len(a));pb=rng.permutation(len(b));a,na,aids=a[pa],na[pa],aids[pa];b,nb,bids=b[pb],nb[pb],bids[pb]
   order=rng.permutation(2);Ts=np.stack([G,H])[order];true_index=int(np.flatnonzero(order==0)[0])
   assert max(len(a),len(b))<=2048
   path=out/(name+'.npz');np.savez_compressed(path,a=a,b=b,na=na,nb=nb,candidates=Ts)
   inputs[path.name]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size}
   truth[name]={'group':group,'density':density,'physical_true_index':true_index,'expected':'identify' if group in ['unique','visible_anchor'] else 'ambiguous','a_physical_ids':aids.tolist(),'b_physical_ids':bids.tolist(),'true_transform':G.tolist(),'alias_offset_y':8.}
 with (R/'INPUTS.json').open('x') as f:json.dump({'files':inputs,'seed':311,'raw_reads':0,'real_cloud_reads':0},f,indent=2);f.write('\n')
 with (R/'EVALUATION_ONLY.json').open('x') as f:json.dump(truth,f,indent=2);f.write('\n')
 print('Generated',len(inputs),'fixed controls,',sum(x['bytes'] for x in inputs.values()),'bytes')
if __name__=='__main__':generate()
