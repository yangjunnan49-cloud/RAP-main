"""Independent NumPy geometry audit for the frozen F1 engineering preflight."""
import hashlib,json,sys
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
MAIN=Path('/mnt/e/githouse/RAP-main');ROOT=MAIN.parent/'RAP-SLAM'
BASE=MAIN/'docs/maintenance/2026-09-26/f1-structured-preflight-01'
sys.path[:0]=[str(ROOT),str(ROOT/'scripts'),str(MAIN)]

def save(p,x):
    with Path(p).open('x') as f:json.dump(x,f,indent=2,allow_nan=False)
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def fit(x,y):
    x=np.asarray(x,dtype=np.float64);y=np.asarray(y,dtype=np.float64)
    u,_,v=np.linalg.svd((x-x.mean(0)).T@(y-y.mean(0)))
    d=np.eye(3);d[2,2]=np.linalg.det(v.T@u.T)
    r=v.T@d@u.T;t=y.mean(0)-r@x.mean(0)
    return r,t
def apply(T,p):return p@T[:3,:3].T+T[:3,3]
def pose(r,t):
    T=np.eye(4);T[:3,:3]=r;T[:3,3]=t;return T
def synthetic():
    import torch
    from rap_slam.rap_backend import RAPBackend
    from rap_slam.structured_motion import group_coordinates,project_groups,decode_groups
    from rap_slam.rap_precision import ieee_matmul
    rng=np.random.default_rng(260926);errors=[]
    for trial in range(20):
        points=[rng.normal(size=(300 if k in [0,3] else 200,3))*5+rng.normal(size=3)*4 for k in range(6)]
        L=[pose(Rotation.random(random_state=rng).as_matrix(),rng.normal(size=3)) if k not in [0,3] else np.eye(4) for k in range(6)]
        _,s,c,n,_=RAPBackend._normalize_parts(points);c=np.asarray(c)
        q=group_coordinates(points,L,c,s,torch.device('cpu'))
        G=[pose(Rotation.random(random_state=rng).as_matrix(),rng.normal(size=3)) for _ in range(2)]
        y=np.concatenate([apply(G[0 if k<3 else 1],apply(L[k],p))/s for k,p in enumerate(points)])
        with ieee_matmul():proj,rt=project_groups(torch.tensor(y,dtype=torch.float32),q,int(sum(n[:3])))
        recovered=decode_groups(rt,c,s);truth=np.asarray(G).copy()
        # Output normalized coordinates are physical output / s, so decoding recovers G.
        delta=float(np.max(np.abs(recovered-truth)))
        assert delta<1e-4
        errors.append(delta)
        gauge=pose(Rotation.random(random_state=rng).as_matrix(),rng.normal(size=3))
        z=np.concatenate([apply(gauge,part) for part in np.split(y,[sum(n[:3])])])
        with ieee_matmul():_,rt2=project_groups(torch.tensor(z,dtype=torch.float32),q,int(sum(n[:3])))
        rec2=decode_groups(rt2,c,s)
        # Common normalized translation scales in physical space, but cancels in relative pose.
        assert np.max(np.abs(np.linalg.inv(rec2[0])@rec2[1]-np.linalg.inv(recovered[0])@recovered[1]))<1e-4
    save(BASE/'synthetic_validation.json',dict(passed=True,trials=20,max_pose_delta=max(errors),gauge_trials=20))
    print('F1 synthetic passed',max(errors),flush=True)

def validate():
    out=BASE/'attempt-01';manifest=read(out/'artifact_hashes.json')
    for p,h in manifest.items():assert sha(out/p)==h
    records=read(out/'records.json');assert len(records)==22
    inputs=read(BASE/'inputs.json');max_project=0.;max_pose=0.;constraints=[]
    for row in inputs:
        dest=out/row['key'];data=np.load(dest/'inputs.npz');counts=data['counts'];s=float(data['scale']);centers=data['centers']
        assert counts.tolist()==[2000,1000,1000,2000,1000,1000]
        parts=np.split(data['points'],np.cumsum(counts)[:-1]);motions=data['motions']
        q=np.concatenate([(apply(motions[k],p)-centers[0 if k<3 else 3])/s for k,p in enumerate(parts)])
        assert np.max(np.abs(q-data['group_source']))<1e-6
        assert np.max(np.abs(data['cond']*s+np.repeat(centers,counts,axis=0)-data['points']))<1e-4
        for arm in ['N','F','S','P','A']+(['Sminus','Splus'] if row==inputs[-1] else []):
            a=np.load(dest/f'{arm}.npz')
            assert a['end_point_trajectory'].shape[0]==5
            if arm in ['F','S','Sminus','Splus']:
                mm=motions
                if arm in ['Sminus','Splus']:mm=np.load(dest/('motions-minus.npy' if arm=='Sminus' else 'motions-plus.npy'))
                qq=np.concatenate([(apply(mm[k],p)-centers[0 if k<3 else 3])/s for k,p in enumerate(parts)])
                for step,raw in enumerate(a['end_point_trajectory']):
                    projected=[];gg=[]
                    for g,sl in enumerate([slice(0,4000),slice(4000,None)]):
                        r,t=fit(qq[sl],raw[sl]);projected.append(qq[sl]@r.T+t)
                        gg.append(pose(r,s*t-r@centers[0 if g==0 else 3]))
                    pp=np.concatenate(projected)
                    if arm!='F':
                        delta=float(np.max(np.abs(pp-a['projected_clean_trajectory'][step])))
                        max_project=max(max_project,delta);assert delta<1e-4
                        time_next=1-(step+1)/5
                        assert np.max(np.abs(pp*(1-time_next)+data['noise']*time_next-a['trajectory'][step]))<1e-4
                    if step==4:
                        assert np.max(np.abs(pp-a['decoded_final']))<1e-4
                        d=float(np.max(np.abs(np.asarray(gg)-a['group_poses'])));max_pose=max(max_pose,d);assert d<1e-3
                        assert np.max(np.abs(np.linalg.inv(gg[0])@gg[1]-a['T']))<1e-3
                        fitparts=[]
                        for p,y in zip(parts,np.split(pp,np.cumsum(counts)[:-1])):
                            rr,tt=fit(p,y*s);fitparts.append(pose(rr,tt))
                        residual=max(float(np.max(np.abs(np.linalg.inv(fitparts[0 if k<3 else 3])@fitparts[k]-mm[k]))) for k in range(6))
                        constraints.append(residual);assert residual<1e-4
            else:
                ps=parts if arm=='N' else [parts[0],parts[3]] if arm=='A' else [np.concatenate([apply(motions[k],parts[k]) for k in range(3)]).astype(np.float32),np.concatenate([apply(motions[k],parts[k]) for k in range(3,6)]).astype(np.float32)]
                cc=np.asarray([p.astype(np.float64).mean(0) for p in ps]);ss=1.5*np.max(np.abs(ps[0].astype(np.float64)-cc[0]))
                final=a['end_point_trajectory'][-1];poses=[]
                for p,y in zip(ps,np.split(final,np.cumsum([len(p) for p in ps])[:-1])):
                    rr,tt=fit(p,y*ss);poses.append(pose(rr,tt))
                d=float(np.max(np.abs(np.asarray(poses)-a['raw_poses'])));assert d<1e-3;max_pose=max(max_pose,d)
                assert np.max(np.abs(np.linalg.inv(poses[0])@poses[3 if arm=='N' else 1]-a['T']))<1e-3
        n=np.load(dest/'N.npz');f=np.load(dest/'F.npz')
        assert np.array_equal(n['end_point_trajectory'],f['end_point_trajectory'])
    execution=read(out/'execution.json');assert execution['peak_allocated']<=12*2**30 and execution['wall_s']<=1800
    assert execution['no_hooks_installed'] and execution['restoration_on_exception'] and not execution['gt_loaded_by_runner']
    assert max(r['native_max_delta'] for r in records if r['arm']=='N')<=1e-6
    # Only now load evaluator truth, after immutable generation artifact hash verification.
    gt=np.load(MAIN/'docs/maintenance/2026-09-14/hl-v2/data-expansion-01/00/evaluator_gt.npy')
    from rap_slam.measurement import transform_label
    local=[]
    for row in inputs:
        for k in [1,2,4,5]:
            anchor=row['scans'][0 if k<3 else 3]['source_id'];support=row['scans'][k]['source_id']
            label=transform_label(row['motions'][k],np.linalg.inv(gt[anchor])@gt[support])
            local.append(dict(pair=row['key'],support=support,translation_m=label['gt_translation_error_m'],rotation_deg=label['gt_rotation_error_deg']))
    save(BASE/'local_motion_evaluator_only.json',dict(gt_sha256=sha(MAIN/'docs/maintenance/2026-09-14/hl-v2/data-expansion-01/00/evaluator_gt.npy'),rows=local))
    result=dict(passed=True,decision='PASS_ENGINEERING',pairs=4,method_outputs=len(records),artifacts=len(manifest),
        max_independent_projected_delta=max_project,max_independent_pose_delta=max_pose,max_constraint_delta=max(constraints),
        native_max_delta=max(r['native_max_delta'] for r in records if r['arm']=='N'),execution=execution,
        efficacy_evaluated=False,local_motion_translation_max=max(r['translation_m'] for r in local))
    save(BASE/'validation.json',result)
    (out/'INCOMPLETE').unlink()
    print(json.dumps(result,indent=2),flush=True)
if __name__=='__main__':{'synthetic':synthetic,'validate':validate}[sys.argv[1]]()
