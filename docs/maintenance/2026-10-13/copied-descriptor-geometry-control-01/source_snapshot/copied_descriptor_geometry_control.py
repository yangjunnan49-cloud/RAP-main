"""CDG0 fixed descriptor-only geometric ceiling on the exposed numerical fixture."""
import importlib.metadata,resource,signal,sys,time,traceback
from pathlib import Path
import shadow_prefix_storage_codec as s
ROOT=s.ROOT;PRIOR=ROOT/'docs/maintenance/2026-10-13/frozen-metric-head-derivatives-01'
INPUT=ROOT/'docs/maintenance/2026-10-10/native-conditioned-comparison-01/attempt-02/bank/synthetic_fixture.npz'
BASE=ROOT/'docs/maintenance/2026-10-13/copied-descriptor-geometry-control-01';SUP=BASE/'supervision';START=None
read,save,sha=s.read,s.save,s.sha
def freeze():
    f=read(PRIOR/'freeze.json');files=dict(f['files']);assert read(PRIOR/'validation.json')['passed'];delivery=read(PRIOR/'DELIVERY_SEAL.json');assert delivery['entries']==280
    for x in delivery['files']:
        q=(PRIOR/x['path'].replace(chr(92),'/')).resolve();assert PRIOR.resolve() in q.parents and sha(q)==x['sha256'];files[str(q)]=x['sha256']
    paths=[PRIOR/'DELIVERY_SEAL.json',Path(__file__),Path(__file__).with_name('validate_copied_descriptor_geometry.py'),Path(__file__).with_name('invoke_mgr_supervised_wsl.ps1'),INPUT,BASE/'OWNER_SCOPE.md',BASE/'PROTOCOL.md'];snap=BASE/'source_snapshot';snap.mkdir()
    for q in paths:
        files[str(q)]=sha(q)
        if q.suffix in ('.py','.ps1'):(snap/q.name).write_bytes(q.read_bytes())
    for q,h in files.items():assert sha(q)==h,q
    assert s.repositories()==f['repositories'];save(BASE/'freeze.json',dict(files=files,repositories=f['repositories'],packages=f['packages'],method='all-point mutual nearest descriptor matches then unweighted proper SVD',parts=[1,2],source_points_per_part=1000,k=2,t_gate_m=.005,R_gate_deg=.05,cap_seconds=600,cap_RSS_bytes=2*2**30,cap_GPU_bytes=0,cap_artifact_bytes=64*2**20,no_model_training_or_HFIT_partial_inputs=True));(BASE/'INCOMPLETE').write_text('CDG0 complete descriptor ambiguity/support and independent geometry ceiling audit pending.\n');print('CDG0 frozen',len(files),'identities',flush=True)
def verify():
    f=read(BASE/'freeze.json')
    for q,h in f['files'].items():assert sha(q)==h,q
    assert s.repositories()==f['repositories'] and f['packages']=={x:importlib.metadata.version(x) for x in ('torch','numpy','scipy')} and (s.OLD/'INCOMPLETE').exists() and not (s.OLD/'prediction_seal.json').exists()
def predict():
    verify()
    import numpy as np
    from scipy.spatial import cKDTree
    folder=BASE/'predictions';folder.mkdir()
    with np.load(INPUT,allow_pickle=False) as z:points=z['points'].copy();features=z['features'].copy()
    assert points.shape==(3000,3) and features.shape==(3000,32) and np.isfinite(points).all() and np.isfinite(features).all();np.savez(folder/'observations.npz',points=points,features=features);records=[];support=[];poses={}
    for part in (1,2):
        forward=reverse=None;valid=True
        for direction,left,right in [('part_to_anchor',part,0),('anchor_to_part',0,part)]:
            source=features[left*1000:(left+1)*1000].astype(float);target=features[right*1000:(right+1)*1000].astype(float);distance,index=cKDTree(target).query(source,k=2,workers=1)
            np.savez(folder/f'part{part}_{direction}.npz',distance=distance,index=index)
            ambiguity=int(np.count_nonzero(distance[:,1]==distance[:,0]));unique=len(np.unique(index[:,0]));valid=valid and ambiguity==0 and unique==1000 and np.isfinite(distance).all()
            records.append(dict(part=part,direction=direction,query_points=1000,nearest_ties=ambiguity,unique_first_indices=unique,max_first_descriptor_distance=float(distance[:,0].max()),min_second_descriptor_distance=float(distance[:,1].min())))
            if direction=='part_to_anchor':forward=index[:,0]
            else:reverse=index[:,0]
        mutual=bool(np.array_equal(reverse[forward],np.arange(1000)));valid=valid and mutual
        row=dict(part=part,all1000_used=bool(valid),mutual_all1000=mutual,full_support_and_no_ambiguity=bool(valid));support.append(row)
        if valid:
            a=points[part*1000:(part+1)*1000].astype(float);b=points[:1000][forward].astype(float);ma=a.mean(0);mb=b.mean(0);u,sv,vh=np.linalg.svd((a-ma).T@(b-mb));rank=int(np.count_nonzero(sv>1e-12*sv.max()));assert rank==3
            rot=vh.T@np.diag([1.,1.,np.linalg.det(vh.T@u.T)])@u.T;shift=mb-rot@ma;T=np.eye(4);T[:3,:3]=rot;T[:3,3]=shift;poses[f'part{part}']=T;row.update(cross_covariance_singular_values=sv.tolist(),rank=rank)
        cap()
    np.savez(folder/'poses.npz',**poses);all_support=all(x['full_support_and_no_ambiguity'] for x in support)
    save(folder/'execution.json',dict(descriptor_queries=4000,complete_pairs=2,records=records,support=support,all_support=all_support,truth_target_loaded=False,no_index_or_GT_matching=True,model_calls=0,optimizer_calls=0,retained_updates=0,HFIT_partial_predictions_used=False))
    save(BASE/'prediction_seal.json',dict(freeze_sha256=sha(BASE/'freeze.json'),files={str(q.relative_to(folder)):sha(q) for q in sorted(folder.rglob('*')) if q.is_file()}));verify();print('CDG0 all-point support gate',all_support,flush=True)
def usage():return dict(wall_seconds=time.monotonic()-START,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,peak_GPU_allocated_bytes=0,peak_GPU_reserved_bytes=0,artifact_bytes=sum(q.stat().st_size for q in BASE.rglob('*') if q.is_file()),imports_included=True,optimizer_calls=0)
def cap():
    u=usage();assert u['peak_RSS_bytes']<=2*2**30 and u['artifact_bytes']<=64*2**20,u
    if (SUP/'host_latest.json').exists():assert read(SUP/'host_latest.json')['headroom_bytes']>=4*2**30
def run(stage):
    global START
    START=time.monotonic();used=sum(read(q)['wall_seconds'] for q in SUP.glob('*/child_exit.json'));assert used<600
    signal.signal(signal.SIGALRM,lambda a,b:(_ for _ in ()).throw(TimeoutError('CDG0 aggregate child time cap')));signal.alarm(max(1,int(600-used)));ok=False;error=None
    try:
        if stage=='freeze':freeze()
        elif stage=='predict':predict()
        elif stage=='validate':
            import validate_copied_descriptor_geometry as v;v.validate()
        else:raise ValueError(stage)
        cap();ok=True
    except BaseException as ex:error=repr(ex);traceback.print_exc();save(BASE/f'FAILURE_{stage}.json',dict(error=error,**usage()))
    finally:signal.alarm(0);save(SUP/stage/'child_exit.json',dict(success=ok,error=error,full_resource_capture=True,**usage()))
    if not ok:sys.exit(1)
if __name__=='__main__':sys.modules['copied_descriptor_geometry_control']=sys.modules[__name__];run(sys.argv[1])
