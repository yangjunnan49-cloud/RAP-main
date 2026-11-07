"""Independent checks of frozen synthetic GeoTransformer artifacts; no runner import."""
import hashlib,json
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
B=Path('/mnt/e/githouse/RAP-main/docs/maintenance/2026-10-05/geotransformer-feasibility-01')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
freeze=json.loads((B/'preflight_freeze.json').read_text()); result=json.loads((B/'preflight_results.json').read_text())
checks={}
for p,h in freeze['files'].items(): assert sha(p)==h,p
checks['frozen_identities']=len(freeze['files'])
bank=B/'synthetic-bank'
for p,h in result['bank_files'].items(): assert sha(bank/p)==h,p
g=np.load(bank/'geometry.npz'); src,ref,T=g['src'],g['ref'],g['known']
assert np.max(np.abs(src@T[:3,:3].T+T[:3,3]-ref))<1e-5
x=src.astype('float64'); y=ref.astype('float64'); xc=x.mean(0); yc=y.mean(0)
u,_,vt=np.linalg.svd((x-xc).T@(y-yc)); R=vt.T@np.diag([1,1,np.linalg.det(vt.T@u.T)])@u.T
ind=np.eye(4); ind[:3,:3]=R; ind[:3,3]=yc-R@xc
assert np.max(np.abs(ind-g['fitted']))<=1e-4 and np.max(np.abs(T-g['fitted']))<=1e-4
checks['source_to_reference_procrustes']=float(np.max(np.abs(ind-g['fitted'])))
points,lengths,neighbors=g['points'],g['lengths'],g['neighbors']; offset=0
for length in lengths:
    cloud=points[offset:offset+length]; tree=cKDTree(cloud)
    for i,c in enumerate(cloud):
        expected=tree.query_ball_point(c,1.275)
        expected=sorted(expected,key=lambda j:(float(np.sum((cloud[j]-c)**2)),j))[:128]
        actual=neighbors[offset+i]; actual=actual[actual<len(points)]-offset
        assert set(actual)==set(expected),(offset,i)
    offset+=length
checks['isolated_radius_rows']=len(points)
# Independent voxel centroid content, allowing unordered C++ hash iteration.
offset=0; suboffset=0
for n,m in zip(lengths,g['sublengths']):
    cloud=points[offset:offset+n]
    # Official subsampler uses a grid aligned to floor(min/.6)*.6.
    origin=np.floor(cloud.min(0)/np.float32(.6))*np.float32(.6)
    cells=np.floor((cloud-origin)/np.float32(.6)).astype('int64')
    groups={}
    for cell,p in zip(cells,cloud): groups.setdefault(tuple(cell),[]).append(p)
    centroids=np.asarray([np.asarray(ps,dtype='float64').mean(0) for ps in groups.values()])
    out=g['subpoints'][suboffset:suboffset+m]
    assert len(centroids)==m
    distances,idx=cKDTree(centroids).query(out)
    assert len(set(idx))==m and distances.max()<1e-5
    offset+=n; suboffset+=m
checks['independent_voxel_centroids']=len(g['subpoints'])
outputs=[np.load(bank/f'forward-{i}.npz') for i in range(3)]
for out in outputs:
    t=out['estimated_transform']; assert t.shape==(4,4) and np.isfinite(t).all()
    assert np.max(np.abs(t[3]-[0,0,0,1]))<1e-6
    assert np.max(np.abs(t[:3,:3].T@t[:3,:3]-np.eye(3)))<1e-4 and abs(np.linalg.det(t[:3,:3])-1)<1e-4
for k in outputs[0].files:
    if k.startswith('gt_'): continue
    for out in outputs[1:]:
        assert out[k].shape==outputs[0][k].shape and np.isfinite(out[k]).all()
        assert np.max(np.abs(out[k]-outputs[0][k]))<=1e-6 if out[k].size else True
checks['dummy_transform_invariance_and_repeatability']=len(result['invariance'])
assert result['strict_load'] and result['missing_keys']==result['unexpected_keys']==[]
assert result['wall_s']<600 and result['peak_gpu_gib']<6
checks['strict_load_and_caps']=result['model_state_keys']
record=dict(passed=True,decision='PASS_ISOLATED_SYNTHETIC_FEASIBILITY',check_groups=checks,freeze_sha256=sha(B/'preflight_freeze.json'),results_sha256=sha(B/'preflight_results.json'))
with (B/'validation.json').open('x') as f: json.dump(record,f,indent=2)
print(json.dumps(record,indent=2))
