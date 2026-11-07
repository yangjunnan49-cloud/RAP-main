"""GSG0 coordinate-only full-distance signature control, no descriptor/model input."""
import importlib.metadata,resource,signal,sys,time,traceback
from pathlib import Path
import shadow_prefix_storage_codec as s
ROOT=s.ROOT;PRIOR=ROOT/'docs/maintenance/2026-10-13/copied-descriptor-geometry-control-01';INPUT=ROOT/'docs/maintenance/2026-10-10/native-conditioned-comparison-01/attempt-02/bank/synthetic_fixture.npz'
BASE=ROOT/'docs/maintenance/2026-10-13/geometry-signature-control-01';SUP=BASE/'supervision';START=None;EPS=1e-8
read,save,sha=s.read,s.save,s.sha
def freeze():
    f=read(PRIOR/'freeze.json');files=dict(f['files']);assert read(PRIOR/'validation.json')['passed'];delivery=read(PRIOR/'DELIVERY_SEAL.json')
    for x in delivery['files']:
        q=(PRIOR/x['path'].replace(chr(92),'/')).resolve();assert PRIOR.resolve() in q.parents and sha(q)==x['sha256'];files[str(q)]=x['sha256']
    paths=[PRIOR/'DELIVERY_SEAL.json',Path(__file__),Path(__file__).with_name('validate_geometry_signature.py'),Path(__file__).with_name('invoke_mgr_supervised_wsl.ps1'),BASE/'OWNER_SCOPE.md',BASE/'PROTOCOL.md'];snap=BASE/'source_snapshot';snap.mkdir()
    for q in paths:
        files[str(q)]=sha(q)
        if q.suffix in ('.py','.ps1'):(snap/q.name).write_bytes(q.read_bytes())
    for q,h in files.items():assert sha(q)==h,q
    assert s.repositories()==f['repositories'];save(BASE/'freeze.json',dict(files=files,repositories=f['repositories'],packages=f['packages'],point_only=True,signature='sorted complete point-to-point Euclidean distance row',candidate_epsilon_m=EPS,all_points_per_part=1000,t_gate_m=.005,R_gate_deg=.05,cap_seconds=900,cap_RSS_bytes=2*2**30,cap_GPU_bytes=0,cap_artifact_bytes=128*2**20,no_CDG_matches_or_descriptors_or_model=True));(BASE/'INCOMPLETE').write_text('GSG0 coordinate-only invariant signature/full support/independent geometry control pending.\n');print('GSG0 frozen',len(files),'identities',flush=True)
def verify():
    f=read(BASE/'freeze.json')
    for q,h in f['files'].items():assert sha(q)==h,q
    assert s.repositories()==f['repositories'] and f['packages']=={x:importlib.metadata.version(x) for x in ('torch','numpy','scipy')} and (s.OLD/'INCOMPLETE').exists() and not (s.OLD/'prediction_seal.json').exists()
def signature(points):
    import numpy as np
    from scipy.spatial.distance import pdist,squareform
    return np.sort(squareform(pdist(points,metric='euclidean')),axis=1)
def match(source,target,target_points):
    import numpy as np
    from scipy.spatial import cKDTree
    tree=cKDTree(target);distance,index=tree.query(source,k=2,workers=1);candidates=tree.query_ball_point(source,r=distance[:,0]+EPS,workers=1);offset=[0];allids=[];chosen=[];ambiguity=0
    for ids in candidates:
        ids=sorted(ids);assert ids;allids.extend(ids);offset.append(len(allids));chosen.append(ids[0])
        coords=target_points[ids]
        if not np.array_equal(coords,np.broadcast_to(coords[0],coords.shape)):ambiguity+=1
    valid=ambiguity==0 and np.isfinite(distance).all() and float(distance[:,0].max())<=EPS
    return dict(distance=distance,index=index,candidate_offsets=np.array(offset,dtype=np.int64),candidate_indices=np.array(allids,dtype=np.int64),chosen=np.array(chosen,dtype=np.int64)),dict(full_coordinate_support=bool(valid),different_coordinate_candidate_ambiguity=ambiguity,candidate_count=len(allids),coincident_extra_candidates=len(allids)-len(source),max_first_signature_distance_m=float(distance[:,0].max()))
def rigid(a,b):
    import numpy as np
    ma=a.mean(0);mb=b.mean(0);u,sv,vh=np.linalg.svd((a-ma).T@(b-mb));assert np.count_nonzero(sv>1e-12*sv.max())==3
    R=vh.T@np.diag([1.,1.,np.linalg.det(vh.T@u.T)])@u.T;T=np.eye(4);T[:3,:3]=R;T[:3,3]=mb-R@ma;return T
def preflight():
    verify();import numpy as np
    folder=BASE/'preflight';folder.mkdir();p=np.array([[0.,0.,0.],[1.,0.,0.],[0.,2.,0.],[0.,0.,3.],[1.,1.,.5],[.2,-.8,1.7]]);cube=np.array([[i,j,k] for i in (-1.,1.) for j in (-1.,1.) for k in (-1.,1.)]);R=np.array([[0.,-1.,0.],[1.,0.,0.],[0.,0.,1.]]);t=np.array([.5,-.2,.1]);rows=[]
    for name,a,expected in [('asymmetric',p,True),('coincident_coordinate',np.vstack([p,p[0]]),True),('distinct_coordinate_cube_symmetry',cube,False)]:
        b=a@R.T+t;sa=signature(a);sb=signature(b);nn,support=match(sa,sb,b);assert support['full_coordinate_support']==expected
        T=rigid(a,b[nn['chosen']]) if expected else np.empty((0,4,4));truth=np.eye(4);truth[:3,:3]=R;truth[:3,3]=t
        if expected:assert np.max(abs(T-truth))<=1e-10
        np.savez(folder/(name+'.npz'),source=a,target=b,source_signature=sa,target_signature=sb,pose=T,known_fixture_transform=truth,**nn);rows.append(dict(name=name,expected_full_support=expected,support=support));cap()
    save(folder/'execution.json',dict(passed=True,fixtures=rows,model_or_descriptor_calls=0));save(BASE/'preflight_seal.json',dict(freeze_sha256=sha(BASE/'freeze.json'),files={str(q.relative_to(folder)):sha(q) for q in sorted(folder.rglob('*')) if q.is_file()}));verify();print('GSG0 three prospective geometry fixtures pass',flush=True)
def predict():
    verify();import numpy as np
    assert read(BASE/'preflight/execution.json')['passed'];folder=BASE/'predictions';folder.mkdir()
    with np.load(INPUT,allow_pickle=False) as z:points=z['points'].astype(float)
    assert points.shape==(3000,3) and np.isfinite(points).all();np.save(folder/'points.npy',points);sig=[]
    for k in range(3):
        sig.append(signature(points[k*1000:(k+1)*1000]));np.save(folder/f'signature_part{k}.npy',sig[-1]);cap()
    rows=[];poses={}
    for part in (1,2):
        nnf,sf=match(sig[part],sig[0],points[:1000]);nnr,sr=match(sig[0],sig[part],points[part*1000:(part+1)*1000]);np.savez(folder/f'part{part}_forward.npz',**nnf);np.savez(folder/f'part{part}_reverse.npz',**nnr)
        a=points[part*1000:(part+1)*1000];mutual=bool(np.array_equal(a[nnr['chosen'][nnf['chosen']]],a));valid=sf['full_coordinate_support'] and sr['full_coordinate_support'] and mutual
        rows.append(dict(part=part,forward=sf,reverse=sr,reciprocal_coordinates_all1000=mutual,all1000_support=bool(valid)))
        if valid:poses[f'part{part}']=rigid(a,points[:1000][nnf['chosen']])
        cap()
    np.savez(folder/'poses.npz',**poses);save(folder/'execution.json',dict(records=rows,signature_point_pairs=3000000,signature_NN_queries=4000,all_support=all(x['all1000_support'] for x in rows),descriptors_truth_target_or_CDG_matches_loaded=False,model_calls=0,optimizer_calls=0,retained_updates=0,ordinary_full_distance_geometry=True))
    save(BASE/'prediction_seal.json',dict(freeze_sha256=sha(BASE/'freeze.json'),files={str(q.relative_to(folder)):sha(q) for q in sorted(folder.rglob('*')) if q.is_file()}));verify();print('GSG0 full coordinate support',all(x['all1000_support'] for x in rows),flush=True)
def usage():return dict(wall_seconds=time.monotonic()-START,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,peak_GPU_allocated_bytes=0,peak_GPU_reserved_bytes=0,artifact_bytes=sum(q.stat().st_size for q in BASE.rglob('*') if q.is_file()),imports_included=True,optimizer_calls=0)
def cap():
    u=usage();assert u['peak_RSS_bytes']<=2*2**30 and u['artifact_bytes']<=128*2**20,u
    if (SUP/'host_latest.json').exists():assert read(SUP/'host_latest.json')['headroom_bytes']>=4*2**30
def run(stage):
    global START
    START=time.monotonic();used=sum(read(q)['wall_seconds'] for q in SUP.glob('*/child_exit.json'));assert used<900
    signal.signal(signal.SIGALRM,lambda a,b:(_ for _ in ()).throw(TimeoutError('GSG0 aggregate child time cap')));signal.alarm(max(1,int(900-used)));ok=False;error=None
    try:
        if stage=='freeze':freeze()
        elif stage=='preflight':preflight()
        elif stage=='predict':predict()
        elif stage=='validate':
            import validate_geometry_signature as v;v.validate()
        else:raise ValueError(stage)
        cap();ok=True
    except BaseException as ex:error=repr(ex);traceback.print_exc();save(BASE/f'FAILURE_{stage}.json',dict(error=error,**usage()))
    finally:signal.alarm(0);save(SUP/stage/'child_exit.json',dict(success=ok,error=error,full_resource_capture=True,**usage()))
    if not ok:sys.exit(1)
if __name__=='__main__':sys.modules['geometry_signature_control']=sys.modules[__name__];run(sys.argv[1])
