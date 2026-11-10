"""Independent DPA2 table/distance checks; no nearest-neighbor queries."""
import hashlib
import json
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text())
result=read(R/'results/RESULTS.json');frozen=read(R/'freeze.json')
assert result['queries']==16 and result['original_raw_reads']==0 and not result['torch_imported'] and not result['open3d_imported']
for name,h in frozen['files'].items():assert hashlib.sha256((R/name).read_bytes()).hexdigest()==h
prior={p['pair']:p for p in read(R/'parent/RESULTS.json')['pairs']}
checks=0;distance_checks=0;summaries=[]
def cost(source,target,normals,ids,T):
    if not len(source):return None
    transformed=(T[:3,:3]@source.T).T+T[:3,3]
    residual=np.sum((transformed-target[ids])*normals[ids],axis=1)
    return sum(.5*float(v)**2 if abs(v)<=.5 else .5*abs(float(v))-.125 for v in residual)/len(residual)
def close(actual,expected):
    if expected is None:assert actual is None
    else:assert actual is not None and abs(actual-expected)<=1e-12,(actual,expected)
for p in result['pairs']:
    z=np.load(R/'inputs'/f"{p['pair']}.npz",allow_pickle=False);q=np.load(R/'results'/f"{p['pair']}-queries.npz",allow_pickle=False)
    t0=z['final'];t1=t0.copy();t1[1:3,3]=z['reference'][1:3,3]
    np.testing.assert_array_equal(t0,p['T0']);np.testing.assert_array_equal(t1,p['T1'])
    for direction,prefix,source,target,normals,ts,oldprefix in [
        ('forward','f',z['b'],z['a'],z['na'],[t0,t1],'forward'),
        ('reverse','r',z['a'],z['b'],z['nb'],[np.linalg.inv(t0),np.linalg.inv(t1)],'reverse')]:
        x=p[direction];supports=[]
        for k,t in enumerate(ts):
            d=q[f'{prefix}_d{k}'];ids=q[f'{prefix}_j{k}'];assert len(d)==len(source)==len(ids)
            assert np.all((ids>=0)&(ids<len(target)))
            transformed=(t[:3,:3]@source.T).T+t[:3,3]
            np.testing.assert_allclose(np.sqrt(np.sum((transformed-target[ids])**2,axis=1)),d,atol=1e-12,rtol=1e-12)
            supports.append(np.flatnonzero(d<=.75));distance_checks+=1
        s0,s1=[set(s.tolist()) for s in supports];intersection=np.array(sorted(s0&s1),dtype=int)
        assert x['counts']==[len(s0),len(s1)] and x['intersection_count']==len(intersection) and x['union_count']==len(s0|s1)
        np.testing.assert_array_equal(supports[0],z[oldprefix+'_i'])
        np.testing.assert_array_equal(q[f'{prefix}_j0'][supports[0]],z[oldprefix+'_j'])
        for scope,ss in [('full_support_loss',supports),('intersection_loss',[intersection,intersection])]:
            for k,source_ids in enumerate(ss):
                target_ids=q[f'{prefix}_j{k}'][source_ids]
                for j,t in enumerate(ts):
                    c=cost(source[source_ids],target,normals,target_ids,t);close(c,x[scope][k][j]);checks+=1
        for k,j in [(0,0),(3,1)]:close(x['full_support_loss'][0][j],prior[p['pair']]['rows'][k][direction]['fixed_loss'])
        assert x['counts']==[prior[p['pair']]['rows'][k][direction]['dynamic_count'] for k in [0,3]]
        if len(intersection):
            j0,j1=[q[f'{prefix}_j{k}'][intersection] for k in [0,1]]
            close(float(np.mean(j0!=j1)),x['correspondence_changed_fraction'])
            angles=np.degrees(np.arccos(np.clip(abs(np.sum(normals[j0]*normals[j1],axis=1)),0,1)))
            np.testing.assert_allclose(np.quantile(angles,[0,.25,.5,.75,.95,1]),x['normal_abs_angle_deg_quantiles'],atol=1e-5,rtol=1e-6)
        for key,label in [('full_support_loss','full_preference'),('intersection_loss','intersection_preference')]:
            expected=[]
            for row in x[key]:
                if None in row:expected.append('EMPTY');continue
                delta=row[1]-row[0];eps=1e-6+1e-3*max(abs(v) for v in row)
                expected.append('T0' if delta>eps else 'T1' if delta<-eps else 'FLAT')
            assert x[label]==expected
    summaries.append({'pair':p['pair'],'role':p['role'],'event_group':p['event_group'],**{d:{k:p[d][k] for k in ['full_preference','intersection_preference','counts','intersection_count','intersection_over_union','correspondence_changed_fraction','normal_abs_angle_deg_quantiles']} for d in ['forward','reverse']}})
assert checks==64 and distance_checks==16
with (R/'INDEPENDENT_CHECKS.json').open('x') as f:json.dump(dict(passed=True,loss_checks=checks,saved_distance_checks=distance_checks,extra_NN_queries=0,raw_reads=0,DPA1_endpoints_matched=True,summaries=summaries,limitations='Saved returned distances checked from point/index pairs; no independent exhaustive nearest search on real clouds.'),f,indent=2);f.write('\n')
print('PASS',checks,'loss checks;',distance_checks,'saved query distances; DPA1 endpoints matched')
