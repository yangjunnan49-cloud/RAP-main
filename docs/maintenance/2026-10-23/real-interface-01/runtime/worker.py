"""Direct public-only real RAP operability, with unchanged backend calls."""
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parent; SCOPE=ROOT.parent
FOLDER=Path(sys.argv[1]); STAGE=sys.argv[2]; START=time.monotonic()
REPO=Path('/mnt/e/githouse/RAP-main')
PUBLIC=REPO/'docs/maintenance/2026-10-16/regx-interface-contract-01/inputs'
COUNTERS=dict(point_occurrences_decoded=0,model_constructor_attempts=0,model_constructor_completed=False,RAP_calls_attempted=0,RAP_calls_completed=0,ICP_calls_completed=0,private_reference_reads=0)
DENIED=[str(PUBLIC.parent/'private'),str(REPO/'docs/maintenance/2026-10-16/regx-reference-package-01/transfer-01'),str(REPO/'docs/maintenance/2026-10-16/regx-reference-code-01/transfer-01')]
ACCESS=[]

def audit(event,args):
    if event=='socket.connect': raise PermissionError('Network forbidden in local functional scope')
    if event=='open' and args and isinstance(args[0],(str,bytes)):
        p=os.fsdecode(args[0])
        if any(p==r or p.startswith(r+'/') for r in DENIED): raise PermissionError('Private/source-world read forbidden:'+p)
sys.addaudithook(audit)

def path(s): return Path('/mnt/'+s[0].lower()+'/'+s[3:].replace('\\','/'))
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest().upper()
def write(name,value):
    with (FOLDER/name).open('x') as f:json.dump(value,f,indent=2)
def gpu_metadata():
    p=subprocess.run(['/usr/lib/wsl/lib/nvidia-smi','--query-gpu=name,memory.free,memory.total','--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=10,check=True)
    rows=[r.strip() for r in p.stdout.strip().split(',')]
    assert len(rows)==3
    assert int(rows[1])>=9216,'GPU free memory admission'
    return dict(name=rows[0],free_MiB=int(rows[1]),total_MiB=int(rows[2]))

def validate_bindings():
    freeze=json.loads((FOLDER.parent/'SOURCE_FREEZE.json').read_text())
    p=SCOPE/'INPUT_BINDINGS.json';assert sha(p)==freeze['input_bindings_sha256']
    b=json.loads(p.read_text())
    for row in b['public_files']+b['weights']:
        p=path(row['path']);assert p.stat().st_size==row['bytes'] and sha(p)==row['sha256']
    for row in b['source_bindings']:
        assert sha(path(row['source']))==row['sha256']
    code=json.loads((SCOPE/'CODE_BINDINGS.json').read_text())
    assert sha(SCOPE/'CODE_BINDINGS.json')==freeze['code_bindings_sha256']
    for row in code:assert sha(path(row['path']))==row['sha256']
    return b

def public_read(relative, bindings):
    p=PUBLIC/relative
    assert not p.is_symlink() and p.resolve().is_relative_to(PUBLIC.resolve())
    assert all(not q.is_symlink() for q in p.parents if q!=PUBLIC and q.is_relative_to(PUBLIC))
    expected=next(r for r in bindings['public_files'] if r['relative']==relative)
    raw=p.read_bytes();assert len(raw)==expected['bytes'] and hashlib.sha256(raw).hexdigest().upper()==expected['sha256']
    ACCESS.append(relative);return raw

def run(b):
    import numpy as np
    import torch
    import open3d as o3d
    assert torch.cuda.is_available()
    torch.cuda.set_per_process_memory_fraction(.65,0)
    os.environ['HF_HUB_OFFLINE']='1';os.environ['WANDB_MODE']='disabled'
    sys.path.insert(0,str(REPO));sys.path.insert(0,'/mnt/e/githouse/RAP-SLAM')
    from rap_slam.rap_backend import RAPBackend
    index=json.loads(public_read('INDEX.json',b))
    assert set(index)=={'version','cases'} and index['version']==1
    assert index['cases']==['case-000/manifest.json','case-001/manifest.json']
    COUNTERS['model_constructor_attempts']+=1
    backend=RAPBackend(rap_root=str(REPO),ckpt_path=str(REPO/'weights/rap_model_12.ckpt'),spinnet_ckpt=str(REPO/'weights/mini_spinnet_t.pth'),sampling_steps=5,voxel_size=.4,max_points_per_scan=4000,des_r=5.,remove_outliers=True,feature_extraction_on=True,seed=42)
    COUNTERS['model_constructor_completed']=True
    original_preprocess=backend.preprocess;original_sample=backend.model.sample_rectified_flow
    prepared=[]; captures=[];current_case=['']
    def save_array(name,array):
        assert array.nbytes<=64*2**20
        with (FOLDER/name).open('xb') as f:np.save(f,array,allow_pickle=False)
        return dict(file=name,shape=list(array.shape),dtype=str(array.dtype),sha256=sha(FOLDER/name))
    def observed_preprocess(points,max_points=None):
        ds,feat=original_preprocess(points,max_points=max_points)
        assert ds.ndim==2 and ds.shape[1]==3 and len(ds)>=200
        assert feat.shape==(len(ds),32) and np.isfinite(feat).all() and np.any(feat!=0),'Invalid or zero descriptors; no fallback admitted'
        assert np.isfinite(ds).all()
        prepared.append((ds.copy(),feat.copy()))
        return ds,feat
    def observed_sample(*args,**kwargs):
        batch=args[0]
        assert set(batch)=={'pointclouds','pointclouds_gt','features','scales','anchor_indices','points_per_part','cu_seqlens'}
        assert torch.equal(batch['pointclouds_gt'],batch['pointclouds'])
        COUNTERS['RAP_calls_attempted']+=1
        result=original_sample(*args,**kwargs)
        COUNTERS['RAP_calls_completed']+=1
        endpoint=result['end_point_trajectory'][-1].detach().float().cpu().numpy()
        cond=batch['pointclouds'].detach().float().cpu().numpy()
        assert endpoint.shape==cond.shape and np.isfinite(endpoint).all()
        captures.append(dict(case=current_case[0],fields=sorted(batch),cond=save_array(current_case[0]+'_cond.npy',cond),endpoint=save_array(current_case[0]+'_endpoint.npy',endpoint),endpoint_dtype=str(result['end_point_trajectory'].dtype),device=str(batch['pointclouds'].device),scale=float(batch['scales'][0]),counts=batch['points_per_part'].cpu().tolist()))
        return result
    backend.preprocess=observed_preprocess;backend.model.sample_rectified_flow=observed_sample
    def rigid(T):
        assert T.shape==(4,4) and np.isfinite(T).all()
        assert np.array_equal(T[3],np.array([0.,0.,0.,1.]))
        R=T[:3,:3];assert np.max(np.abs(R.T@R-np.eye(3)))<=1e-4
        assert abs(np.linalg.det(R)-1)<=1e-4
    cases=[]
    for manifest_relative in index['cases']:
        manifest=json.loads(public_read(manifest_relative,b))
        assert set(manifest)=={'version','format','view_count','views'}
        assert manifest['version']==1 and manifest['format']=='xyz-f64le-v1'
        n=manifest['view_count'];assert type(n)is int and n in (2,3) and len(manifest['views'])==n
        arrays=[]
        for i,view in enumerate(manifest['views']):
            assert set(view)=={'id','file','points','bytes','SHA256'}
            assert view['id']==f'v{i:02d}' and view['file']==f'v{i:02d}.xyz64'
            assert type(view['points'])is int and 0<view['points']<1000000 and view['bytes']==view['points']*24
            raw=public_read(str(Path(manifest_relative).parent/view['file']),b)
            assert hashlib.sha256(raw).hexdigest()==view['SHA256'] and len(raw)==view['bytes']
            x=np.frombuffer(raw,dtype='<f8').reshape(-1,3).copy();assert len(x)==view['points'] and np.isfinite(x).all()
            COUNTERS['point_occurrences_decoded']+=len(x);arrays.append(x)
        current_case[0]=Path(manifest_relative).parent.name
        prepared.clear();begin=time.monotonic()
        if n==2:
            relative,diag=backend.register(*arrays,return_registered=True);Ts=diag['T_parts'];rigid(relative)
        else:Ts,diag=backend.register_multi(arrays)
        elapsed=time.monotonic()-begin
        assert len(prepared)==n and len(Ts)==n
        for T in Ts:rigid(T)
        prep_records=[]
        for i,(xyz,feat) in enumerate(prepared):
            prep_records.append(dict(xyz=save_array(current_case[0]+f'_v{i:02d}_prepared.npy',xyz),features=save_array(current_case[0]+f'_v{i:02d}_features.npy',feat)))
        case=dict(case=current_case[0],RAP_T_parts=[T.tolist() for T in Ts],RAP_observed_seconds=elapsed,prepared=prep_records,geometry_control=[],quality='Not scored against any private reference')
        target=o3d.geometry.PointCloud();target.points=o3d.utility.Vector3dVector(prepared[0][0].astype(np.float64))
        for i in range(1,n):
            source=o3d.geometry.PointCloud();source.points=o3d.utility.Vector3dVector(prepared[i][0].astype(np.float64))
            before=time.monotonic()
            out=o3d.pipelines.registration.registration_icp(source,target,1.,np.eye(4),o3d.pipelines.registration.TransformationEstimationPointToPoint(),o3d.pipelines.registration.ICPConvergenceCriteria(max_iteration=30))
            COUNTERS['ICP_calls_completed']+=1;rigid(np.asarray(out.transformation))
            case['geometry_control'].append(dict(view=i,transform=np.asarray(out.transformation).tolist(),fitness=float(out.fitness),inlier_RMSE=float(out.inlier_rmse),observed_seconds=time.monotonic()-before,role='Identity ICP operability only; not a qualified global accuracy baseline'))
        cases.append(case)
        write(current_case[0]+'_OUTPUT.json',case)
        assert torch.cuda.max_memory_allocated()<=8*2**30
        assert sum(p.stat().st_size for p in SCOPE.rglob('*') if p.is_file())<32*2**20
    assert COUNTERS['point_occurrences_decoded']==56557 and COUNTERS['RAP_calls_completed']==2 and COUNTERS['ICP_calls_completed']==3
    return dict(passed=True,cases=cases,captures=captures,counters=COUNTERS,requested_public_files=ACCESS,peak_torch_allocated_bytes=torch.cuda.max_memory_allocated(),peak_torch_reserved_bytes=torch.cuda.max_memory_reserved(),GPU=torch.cuda.get_device_name(0),private_reference_evaluation=False,physical_efficacy_claim=False,canonical_loader_used=False,timing_comparison_qualified=False)

ok=False;error=None
try:
    bindings=validate_bindings();gpu=gpu_metadata();write('GPU_ADMISSION.json',gpu)
    if STAGE=='preflight':
        assert 'numpy' not in sys.modules and 'torch' not in sys.modules
        result=dict(passed=True,public_files=8,weights=2,source_hashes_verified=True,GPU=gpu,numerical_imports_requested=0,private_reference_reads=0)
    elif STAGE=='numeric':result=run(bindings)
    else:raise ValueError('unknown_stage')
    write('RESULTS.json',result);ok=True
except BaseException as caught:
    error=repr(caught)
    import traceback
    write('FAILURE.json',dict(error=error,traceback=traceback.format_exc(),counters=COUNTERS))
    raise
finally:
    write('worker_exit.json',dict(success=ok,error=error,elapsed_seconds=time.monotonic()-START,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,data_class='real_public_interface_operability',counters=COUNTERS,private_reference_evaluation=False))
print(json.dumps(dict(success=ok,stage=STAGE,elapsed=time.monotonic()-START)))
