"""Independent scalar checks and identity-aware evaluation after geometry scoring."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=R/'INDEPENDENT_CHECKS.json');args=p.parse_args()
read=lambda p:json.loads(p.read_text())
frozen=read(R/'freeze.json');x=read(R/'results/RESULTS.json');truth=read(R/'EVALUATION_ONLY.json')
assert hashlib.sha256((R/'EVALUATION_ONLY.json').read_bytes()).hexdigest()==frozen['evaluation_only_sha256']
assert x['NN_queries']==32 and not x['evaluation_truth_read_by_scorer'] and x['real_data_reads']==x['model_ICP_training_calls']==0
for name,h in frozen['files'].items():assert hashlib.sha256((R/name).read_bytes()).hexdigest()==h
score_checks=0;distance_checks=0;gram_checks=0;case_eval=[]
methods=['nn_mean','plane_huber','block_score'];summary={m:dict(identified_correct=0,identified_wrong=0,abstained=0,ambiguous_forced=0) for m in methods}
def decision(vals):
 finite=[i for i,v in enumerate(vals) if v is not None]
 if len(finite)==0:return None
 if len(finite)==1:return finite[0]
 gap=vals[1]-vals[0];eps=1e-6+1e-3*max(abs(v) for v in vals)
 return None if abs(gap)<=eps else (0 if gap>0 else 1)
def close(a,b):
 if b is None:assert a is None
 else:np.testing.assert_allclose(a,b,atol=1e-12,rtol=1e-12)
for row in x['cases']:
 name=row['case'];e=truth[name]
 with np.load(R/'inputs'/(name+'.npz'),allow_pickle=False) as z:a,b,na,nb,Ts=[z[k] for k in ['a','b','na','nb','candidates']]
 with np.load(R/'results'/(name+'-queries.npz'),allow_pickle=False) as z:q={k:z[k] for k in z.files}
 trueT=np.array(e['true_transform']);np.testing.assert_array_equal(Ts[e['physical_true_index']],trueT)
 aid={int(i):p for i,p in zip(e['a_physical_ids'],a)}
 world=(trueT[:3,:3]@b.T).T+trueT[:3,3]
 for pid,point in zip(e['b_physical_ids'],world):np.testing.assert_allclose(point,aid[pid],atol=1e-12,rtol=0)
 if e['expected']=='ambiguous':
  for pid,point in zip(e['b_physical_ids'],world):np.testing.assert_allclose(point+[0,8,0],aid[10000+pid],atol=1e-12,rtol=0)
 vals={m:[] for m in methods}
 for k,T in enumerate(Ts):
  inv=np.linalg.inv(T)
  for direction,source,target,sn,tn,t,dkey,jkey,odkey,ojkey in [('forward',b,a,nb,na,T,'df','jf','dr','jr'),('reverse',a,b,na,nb,inv,'dr','jr','df','jf')]:
   d=q[f'{k}_{dkey}'];j=q[f'{k}_{jkey}'];od=q[f'{k}_{odkey}'];oj=q[f'{k}_{ojkey}']
   points=(t[:3,:3]@source.T).T+t[:3,3]
   close(np.sqrt(np.sum((points-target[j])**2,axis=1)),d);distance_checks+=1
   ns=(t[:3,:3]@sn.T).T;ns/=np.sqrt(np.sum(ns**2,axis=1))[:,None]
   nt=tn[j];nt/=np.sqrt(np.sum(nt**2,axis=1))[:,None]
   cos=np.clip(abs(np.sum(ns*nt,axis=1)),0,1);mask=d<=.75
   residual=np.sum((points-target[j])*nt,axis=1);rr=residual[mask]
   plane=sum(.5*float(v)**2 if abs(v)<=.5 else .5*abs(float(v))-.125 for v in rr)/len(rr) if len(rr) else None
   cells={}
   for point,dist,c in zip(source,d,cos):
    key=tuple(np.floor(point/2).astype(int));loss=.5*(min(1.,max(0.,float(dist)/.1))+min(1.,max(0.,(1-float(c))/(1-np.cos(np.deg2rad(15))))))
    cells.setdefault(key,[]).append(loss)
   block=sum(sum(v)/len(v) for v in cells.values())/len(cells)
   nn=sum(float(v) for v in d)/len(d);got=row['candidates'][k][direction]
   for m,v in [('nn_mean',nn),('plane_huber',plane),('block_score',block)]:close(got[m],v);score_checks+=1
   assert got['gate_count']==int(mask.sum()) and got['source_count']==len(source)
   mutual=sum(bool(d[i]<=.75 and od[j[i]]<=.75 and oj[j[i]]==i) for i in range(len(source)));assert got['mutual_count']==mutual
   if len(rr):
    n=nt[mask];yy=sum(float(v)**2 for v in n[:,1])/len(n);yz=sum(float(v)*float(w) for v,w in zip(n[:,1],n[:,2]))/len(n);zz=sum(float(v)**2 for v in n[:,2])/len(n)
    eig=[(yy+zz-np.hypot(yy-zz,2*yz))/2,(yy+zz+np.hypot(yy-zz,2*yz))/2];close(got['yz_eigenvalues'],eig);gram_checks+=1
   else:assert got['yz_eigenvalues'] is None
   np.testing.assert_allclose(got['normal_median_deg'],np.median(np.degrees(np.arccos(cos))),atol=1e-5,rtol=1e-6)
   if direction=='forward':
    for m,v in [('nn_mean',nn),('plane_huber',plane),('block_score',block)]:vals[m].append(v)
 results={}
 for m in methods:
  selected=decision(vals[m]);assert row['decisions'][m]==selected
  if selected is None:label='abstained'
  elif e['expected']=='ambiguous':label='ambiguous_forced'
  elif selected==e['physical_true_index']:label='identified_correct'
  else:label='identified_wrong'
  summary[m][label]+=1;results[m]=dict(selected=selected,label=label,scores=vals[m])
 case_eval.append(dict(case=name,group=e['group'],density=e['density'],expected=e['expected'],physical_true_index=e['physical_true_index'],methods=results))
assert score_checks==96 and distance_checks==32
ambiguous=[r for r in case_eval if r['expected']=='ambiguous'];assert len(ambiguous)==4
assert all(r['methods'][m]['selected'] is None for r in ambiguous for m in methods),'Equivalent observations must not force an answer'
new=[r['case'] for r in case_eval if r['methods']['block_score']['label']=='identified_correct' and r['methods']['nn_mean']['label']!='identified_correct']
report=dict(passed=True,score_checks=score_checks,saved_distance_checks=distance_checks,Gram_groups=gram_checks,truth_identity_checks=8,extra_NN_queries=0,real_data_reads=0,summary=summary,cases=case_eval,new_correct_over_nn_cases=new,decision='STOP_THIS_BLOCK_SCORE_RECIPE' if not new else 'CONTROLLED_ONLY_REQUIRES_NEW_REAL_CONTRACT')
with args.output.open('x') as f:json.dump(report,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in report.items() if k!='cases'},indent=2))
