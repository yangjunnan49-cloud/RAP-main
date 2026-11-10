"""Independently recompute DPA3 statistics from whitelist-only saved arrays."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=R/'INDEPENDENT_CHECKS.json');arg=p.parse_args()
read=lambda p:json.loads(p.read_text())
x=read(R/'results/RESULTS.json');freeze=read(R/'freeze.json')
for rel,h in freeze['files'].items():assert hashlib.sha256((R/rel).read_bytes()).hexdigest()==h
allowed={'a','b','na','nb','final','f_d0','f_j0','r_d0','r_j0'}
assert set(x['loaded_members'])==allowed and x['NN_queries']==x['raw_reads']==x['forbidden_array_reads']==0
counts={'Gram_matrices':0,'spectra':0,'eigenvector_checks':0,'angle_distributions':0,'loss_weight_distributions':0,'saved_distances':0,'reciprocity_sets':0}
percent=[0,10,25,50,75,90,95,99,100]
def equal(actual,expected):np.testing.assert_allclose(actual,expected,atol=1e-12,rtol=1e-12)
def group(row,nn,angle,residual):
 assert row['count']==len(nn)
 if not len(nn):
  assert row['unit_gram'] is row['huber_gram'] is row['normal_angle_deg_quantiles'] is None
  return
 np.testing.assert_allclose(row['normal_angle_deg_quantiles'],np.percentile(angle,percent),atol=1e-5,rtol=1e-6)
 hist=[sum((angle>=lo)&(angle<(hi if hi<90 else 90+1e-10))) for lo,hi in zip([0,15,30,60],[15,30,60,90])]
 assert row['normal_angle_bin_counts']==hist;counts['angle_distributions']+=1
 equal(row['abs_residual_quantiles'],np.percentile(abs(residual),percent))
 w=np.array([1. if abs(r)<=.5 else .5/abs(r) for r in residual]);equal(row['huber_weight_quantiles'],np.percentile(w,percent))
 loss=sum(.5*float(r)**2 if abs(r)<=.5 else .5*abs(float(r))-.125 for r in residual)/len(residual);equal(row['huber_loss'],loss);counts['loss_weight_distributions']+=1
 for name,weight in [('unit_gram',np.ones(len(nn))),('huber_gram',w)]:
  yy=sum(float(ww)*float(n[1])**2 for ww,n in zip(weight,nn))/len(nn)
  yz=sum(float(ww)*float(n[1])*float(n[2]) for ww,n in zip(weight,nn))/len(nn)
  zz=sum(float(ww)*float(n[2])**2 for ww,n in zip(weight,nn))/len(nn)
  G=np.array([[yy,yz],[yz,zz]]);g=row[name];equal(g['matrix'],G);equal(g['trace'],yy+zz);counts['Gram_matrices']+=1
  ev=np.array([(yy+zz-np.hypot(yy-zz,2*yz))/2,(yy+zz+np.hypot(yy-zz,2*yz))/2]);equal(g['eigenvalues'],ev)
  if ev[1]>0:equal(g['lambda_min_over_max'],ev[0]/ev[1])
  else:assert g['lambda_min_over_max'] is None
  counts['spectra']+=1
  v=np.array(g['eigenvectors_yz_columns']);equal(v.T@v,np.eye(2));equal(G@v,v*np.array(g['eigenvalues']));counts['eigenvector_checks']+=1
summaries=[]
for row in x['pairs']:
 with np.load(R/'inputs'/f"{row['pair']}.npz",allow_pickle=False) as f:
  assert set(f.files)==allowed;z={k:f[k] for k in allowed}
 T=z['final'];inv=np.linalg.inv(T)
 for direction,s,t,sn,tn,pose,prefix,oprefix in [('forward','b','a','nb','na',T,'f','r'),('reverse','a','b','na','nb',inv,'r','f')]:
  source,target=z[s],z[t];d,j=z[prefix+'_d0'],z[prefix+'_j0'];od,oj=z[oprefix+'_d0'],z[oprefix+'_j0']
  forward_set={(i,int(j[i])) for i in range(len(j)) if d[i]<=.75}
  reverse_set={(int(oj[i]),i) for i in range(len(oj)) if od[i]<=.75}
  mutual=forward_set&reverse_set
  all_ids=np.array([i for i in range(len(j)) if d[i]<=.75]);mutual_ids=np.array(sorted(s for s,t in mutual),dtype=int)
  q=row[direction];assert q['all_count']==len(forward_set) and q['mutual_count']==len(mutual)
  equal(q['distance_support_fraction'],len(forward_set)/len(source));equal(q['mutual_fraction'],len(mutual)/len(forward_set));counts['reciprocity_sets']+=1
  ns=(pose[:3,:3]@z[sn].T).T;ns=ns/np.sqrt(np.sum(ns**2,axis=1))[:,None]
  nt=z[tn][j];nt=nt/np.sqrt(np.sum(nt**2,axis=1))[:,None]
  angle=np.degrees(np.arccos(np.clip(abs(np.sum(ns*nt,axis=1)),0,1)))
  points=(pose[:3,:3]@source.T).T+pose[:3,3];equal(np.sqrt(np.sum((points-target[j])**2,axis=1)),d);counts['saved_distances']+=1
  residual=np.sum((points-target[j])*nt,axis=1)
  group(q['all'],nt[all_ids],angle[all_ids],residual[all_ids]);group(q['mutual'],nt[mutual_ids],angle[mutual_ids],residual[mutual_ids])
 assert row['forward']['mutual_count']==row['reverse']['mutual_count']
 summaries.append(dict(pair=row['pair'],role=row['role'],**{d:dict(all_count=row[d]['all_count'],mutual_count=row[d]['mutual_count'],mutual_fraction=row[d]['mutual_fraction'],mutual_angle_median=row[d]['mutual']['normal_angle_deg_quantiles'][3],mutual_unit_eigenvalues=row[d]['mutual']['unit_gram']['eigenvalues'],mutual_unit_ratio=row[d]['mutual']['unit_gram']['lambda_min_over_max']) for d in ['forward','reverse']}))
assert counts['Gram_matrices']==counts['spectra']==counts['eigenvector_checks']==32 and counts['angle_distributions']==16 and counts['saved_distances']==8
with arg.output.open('x') as f:json.dump(dict(passed=True,checks=counts,extra_NN_queries=0,raw_reads=0,forbidden_array_reads=0,summaries=summaries,limits='Gram matrices are local fixed-support statistics in each target frame, not physical information or correctness certificates.'),f,indent=2);f.write('\n')
print('PASS',json.dumps(counts))
