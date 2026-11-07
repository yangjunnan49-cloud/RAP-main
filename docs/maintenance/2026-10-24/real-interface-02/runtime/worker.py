"""Fixed public-only functional probe; no private reference or physical scoring."""
import datetime as dt,hashlib,json,math,os,resource,subprocess,sys,time
from pathlib import Path
from constructor_bridge import FixedTensorBridge,validate_request
from fixed_state import path,sha_file
from tensor_candidate import byte_hash,tensor_hash
from public_reader import load as public_load
ROOT=Path(__file__).resolve().parent;SCOPE=ROOT.parent;OUT=Path(sys.argv[1]);CASE=sys.argv[2];START=time.monotonic();REPO=Path('/mnt/e/githouse/RAP-main')
PUBLIC=REPO/'docs/maintenance/2026-10-16/regx-interface-contract-01/inputs'
C=dict(point_occurrences_decoded=0,point_occurrences_submitted=0,public_reader_attempted=False,public_reader_completed=False,backend_constructor_attempts=0,backend_constructor_completed=False,feature_calls_attempted=0,feature_calls_completed=0,descriptor_forward_attempts=0,descriptor_forward_completed=0,RAP_calls_attempted=0,RAP_calls_completed=0,flow_forward_attempts=0,flow_forward_completed=0,ICP_calls_completed=0,private_reference_reads=0,original_torch_load_calls=0)
def write(name,value):
    with (OUT/name).open('x') as f:json.dump(value,f,indent=2)
def audit(event,args):
    if event=='socket.connect':raise PermissionError('RI2 network forbidden')
    if event=='open' and args and isinstance(args[0],(str,bytes)):
        p=Path(os.fsdecode(args[0])).absolute()
        if any(p==r or r in p.parents for r in (PUBLIC.parent/'private',REPO/'docs/maintenance/2026-10-16/regx-reference-package-01/transfer-01',REPO/'docs/maintenance/2026-10-16/regx-reference-code-01/transfer-01')):
            C['private_reference_reads']+=1;raise PermissionError('RI2 private/reference access forbidden')
sys.addaudithook(audit)
def gpu(label):
    begin=time.monotonic();p=subprocess.run(['/usr/lib/wsl/lib/nvidia-smi','--query-gpu=name,driver_version,memory.free,memory.used,memory.total','--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=10)
    write('GPU_QUERY_'+label+'.json',dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(),duration_seconds=time.monotonic()-begin,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr))
    assert p.returncode==0,'GPU metadata query failed'
    fields=[x.strip() for x in p.stdout.strip().split(',')];assert len(fields)==5
    obs=dict(name=fields[0],driver=fields[1],free_MiB=int(fields[2]),used_MiB=int(fields[3]),total_MiB=int(fields[4]),required_free_MiB=9216)
    write('GPU_OBSERVATION_'+label+'.json',obs)
    assert obs['free_MiB']>=9216,'Original GPU free admission >=9216MiB failed'
    return obs
def row_admitted(rows,expected):return len(rows)==expected and all(len(r)==32 and all(math.isfinite(float(v)) for v in r) and sum(float(v)*float(v) for v in r)>0 for r in rows)
ok=False;error=None
try:
    freeze=json.loads((OUT.parent/'SOURCE_FREEZE.json').read_text())
    for name,expected in freeze['binding_files'].items():assert sha_file(SCOPE/name)==expected
    for row in json.loads((SCOPE/'CODE_BINDINGS.json').read_text()):assert sha_file(path(row['path']))==row['sha256']
    bi=json.loads((SCOPE/'BI1_RESULTS.json').read_text());assert bi['passed'] and sum(m['tensors'] for m in bi['models'])==402
    weights=json.loads((SCOPE/'WEIGHT_BINDINGS.json').read_text());catalog=json.loads((SCOPE/'PINNED_INPUTS.json').read_text())
    if CASE=='preflight':
        for r in weights:assert sha_file(path(r['path']))==r['sha256']
        for rel,row in catalog.items():assert (PUBLIC/rel).stat().st_size==row['bytes'] and sha_file(PUBLIC/rel)==row['sha256'].upper()
        observed=gpu('preflight');assert not any(k in sys.modules for k in ('numpy','torch'))
        write('RESULTS.json',dict(passed=True,stdlib_only=True,public_files=8,weights=2,GPU=observed,point_decode_count=0))
    elif CASE=='controls':
        cases=[];kw=dict(map_location='cuda',weights_only=False)
        assert validate_request(path(weights[1]['path']),(),kw,weights,1,allowed_target='cuda')==1;cases.append('declared_cuda_route')
        assert validate_request(path(weights[0]['path']),(),dict(kw,map_location='cpu'),weights,0,allowed_target='cuda')==0;cases.append('RAP_CPU_storage_route')
        for target in ('cuda:1','mps'):
            try:validate_request(path(weights[1]['path']),(),dict(kw,map_location=target),weights,1,allowed_target='cuda')
            except ValueError:pass
            else:raise AssertionError('Unadmitted target accepted')
            cases.append('reject_'+target)
        assert row_admitted([[1.]*32,[.5]*32],2);cases.append('positive_descriptor_rows')
        for name,rows in [('one_zero_row',[[1.]*32,[0.]*32]),('nan',[[math.nan]*32,[1.]*32]),('channels',[[1.]*31,[1.]*32]),('rows',[[1.]*32])]:
            assert not row_admitted(rows,2);cases.append('reject_'+name)
        assert 'torch' not in sys.modules
        write('RESULTS.json',dict(passed=True,controls=cases,count=len(cases),stdlib_only=True,actual_points_or_model_calls=0))
    else:
        os.environ['HF_HUB_OFFLINE']='1';os.environ['WANDB_MODE']='disabled';sys.path.insert(0,str(REPO));sys.path.insert(0,'/mnt/e/githouse/RAP-SLAM')
        import numpy as np
        import torch
        import open3d as o3d
        from rap_slam.rap_backend import RAPBackend
        assert torch.cuda.is_available();observed=gpu('before_model');torch.cuda.set_per_process_memory_fraction(.65,0)
        assert torch.cuda.is_initialized();rngs={}
        def capture(tag):
            tb=torch.get_rng_state().numpy().tobytes();cb=torch.cuda.get_rng_state(0).cpu().numpy().tobytes();s=np.random.get_state()
            nb=json.dumps(dict(algorithm=s[0],keys=s[1].tolist(),position=s[2],has_gauss=s[3],cached_gaussian=s[4]),sort_keys=True).encode()
            for suffix,raw in (('TorchCPU.bin',tb),('TorchCUDA0.bin',cb),('NumPy.json',nb)):
                assert len(raw)<128*1024;(OUT/(tag+'_'+suffix)).write_bytes(raw)
            result=dict(tag=tag,Torch_CPU_sha256=byte_hash(tb),Torch_CUDA0_sha256=byte_hash(cb),NumPy_sha256=byte_hash(nb));rngs[tag]=result;return result
        bridge=FixedTensorBridge(weights,json.loads((SCOPE/'STATE_METADATA.json').read_text())['archives'],json.loads((SCOPE/'ARCHIVE_BINDINGS.json').read_text())['archives'],torch,capture,allowed_target='cuda')
        real_load=torch.load
        def forbidden_load(*a,**k):C['original_torch_load_calls']+=1;raise RuntimeError('RI2 original torch.load forbidden')
        torch.load=bridge
        try:
            C['backend_constructor_attempts']+=1
            backend=RAPBackend(rap_root=str(REPO),ckpt_path=str(path(weights[0]['path'])),spinnet_ckpt=str(path(weights[1]['path'])),sampling_steps=5,voxel_size=.4,max_points_per_scan=4000,des_r=5.,remove_outliers=True,feature_extraction_on=True,seed=42)
            C['backend_constructor_completed']=True
        finally:torch.load=forbidden_load;write('LOAD_CALLS.json',bridge.calls)
        assert len(bridge.calls)==2 and all(r['success'] for r in bridge.calls) and str(backend.device)=='cuda'
        for i in (0,1):assert rngs['load'+str(i)+'_before']['Torch_CUDA0_sha256']==rngs['load'+str(i)+'_after']['Torch_CUDA0_sha256']
        def verify_gpu_models(tag):
            reports=[]
            for i,(name,model) in enumerate([('RAP',backend.model),('miniSpinNet',backend.feature_extractor.model)]):
                state=model.state_dict();assert set(state)==set(bridge.expected_hashes[i]);rows=[]
                for key,a in state.items():
                    b=a.detach().cpu();got=tensor_hash(b);assert got==bridge.expected_hashes[i][key] and (not b.is_floating_point() or torch.isfinite(b).all())
                    rows.append(dict(key=key,sha256=got))
                reports.append(dict(model=name,tensors=len(rows),rows=rows))
            write(tag+'_PARAMETERS.json',dict(passed=True,models=reports,total_tensors=sum(r['tensors'] for r in reports)))
        verify_gpu_models('CONSTRUCTOR');assert torch.cuda.max_memory_allocated()<=8*2**30
        original_preprocess=backend.preprocess;original_feature=backend.feature_extractor.extract_features;original_descriptor=backend.feature_extractor.model.forward;original_sample=backend.model.sample_rectified_flow;original_flow=backend.model.flow_model.forward
        prepared=[];captures=[];current=[''];counter=[0]
        def saved(name,array):
            assert array.nbytes<=64*2**20
            with (OUT/name).open('xb') as f:np.save(f,array,allow_pickle=False)
            return dict(file=name,shape=list(array.shape),dtype=str(array.dtype),sha256=sha_file(OUT/name))
        def features(*a,**k):
            C['feature_calls_attempted']+=1;result=original_feature(*a,**k);C['feature_calls_completed']+=1;return result
        def descriptor(*a,**k):
            C['descriptor_forward_attempts']+=1;result=original_descriptor(*a,**k);C['descriptor_forward_completed']+=1;return result
        def preprocess(points,max_points=None):
            counter[0]+=1;tag=current[0]+'_prep'+str(counter[0]);capture(tag+'_before')
            xyz,feat=original_preprocess(points,max_points=max_points);capture(tag+'_after')
            assert xyz.ndim==2 and xyz.shape[1]==3 and 200<=len(xyz)<=4000 and np.isfinite(xyz).all()
            assert feat.shape==(len(xyz),32) and row_admitted(feat,len(xyz)),'RI2 fixed per-row descriptor admission'
            prepared.append((xyz.copy(),feat.copy()));assert torch.cuda.max_memory_allocated()<=8*2**30
            return xyz,feat
        def flow(*a,**k):
            C['flow_forward_attempts']+=1;result=original_flow(*a,**k);C['flow_forward_completed']+=1;return result
        def sample(*a,**k):
            b=a[0];assert set(b)=={'pointclouds','pointclouds_gt','features','scales','anchor_indices','points_per_part','cu_seqlens'}
            cond=b['pointclouds'];assert cond.dtype==torch.float32 and cond.ndim==2 and cond.shape[1]==3 and torch.isfinite(cond).all()
            counts=[len(x) for x,f in prepared];assert b['points_per_part'].cpu().tolist()==[counts] and b['cu_seqlens'].cpu().tolist()==[0,len(cond)] and sum(counts)==len(cond)
            assert b['features'].shape==(len(cond),32) and torch.isfinite(b['features']).all() and torch.equal(b['pointclouds_gt'],cond)
            assert b['scales'].shape==(1,) and torch.isfinite(b['scales']).all() and float(b['scales'][0])>0
            mask=np.zeros(len(cond),dtype=bool);primary=int(np.argmax(counts));lo=sum(counts[:primary]);mask[lo:lo+counts[primary]]=True
            assert np.array_equal(b['anchor_indices'].cpu().numpy(),mask)
            capture(current[0]+'_sample_before');C['RAP_calls_attempted']+=1;result=original_sample(*a,**k);C['RAP_calls_completed']+=1;capture(current[0]+'_sample_after')
            endpoint=result['end_point_trajectory'][-1].detach().float().cpu().numpy();condition=cond.detach().cpu().numpy()
            rec=dict(case=current[0],cond=saved(current[0]+'_cond.npy',condition),endpoint=saved(current[0]+'_endpoint.npy',endpoint),counts=counts,primary=primary,fields=sorted(b),endpoint_dtype=str(result['end_point_trajectory'].dtype))
            captures.append(rec);assert endpoint.shape==condition.shape and np.isfinite(endpoint).all() and torch.cuda.max_memory_allocated()<=8*2**30
            return result
        backend.feature_extractor.extract_features=features;backend.feature_extractor.model.forward=descriptor;backend.preprocess=preprocess;backend.model.sample_rectified_flow=sample;backend.model.flow_model.forward=flow
        def rigid(T):
            assert T.shape==(4,4) and np.isfinite(T).all() and np.array_equal(T[3],np.array([0.,0.,0.,1.]))
            R=T[:3,:3];assert np.max(np.abs(R.T@R-np.eye(3)))<=1e-4 and abs(np.linalg.det(R)-1)<=1e-4
        C['public_reader_attempted']=True;C['point_occurrences_decoded']=None
        cases,access=public_load(PUBLIC,catalog);outputs=[];C['public_reader_completed']=True;C['point_occurrences_decoded']=access['point_occurrences']
        for case in cases:
            current[0]=case.case_id;arrays=[np.asarray(v.xyz,dtype=np.float64) for v in case.views];C['point_occurrences_submitted']+=sum(len(x) for x in arrays)
            prepared.clear();counter[0]=0;begin=time.monotonic()
            if len(arrays)==2:
                relative,diag=backend.register(*arrays,return_registered=True);Ts=diag['T_parts'];rigid(relative)
                assert np.max(np.abs(relative-np.linalg.inv(Ts[0])@Ts[1]))<=1e-10
            else:Ts,diag=backend.register_multi(arrays)
            elapsed=time.monotonic()-begin;assert len(Ts)==len(arrays)==len(prepared)
            for T in Ts:rigid(T)
            records=[dict(xyz=saved(case.case_id+f'_v{i:02d}_prepared.npy',x),features=saved(case.case_id+f'_v{i:02d}_features.npy',f)) for i,(x,f) in enumerate(prepared)]
            payload=dict(case=case.case_id,T_parts=[T.tolist() for T in Ts],observed_RAP_seconds=elapsed,prepared=records,physical_scoring=False)
            file=case.case_id+'_RAP_OUTPUT.json';write(file,payload);write(case.case_id+'_RAP_SEAL.json',dict(file=file,sha256=sha_file(OUT/file)))
            target=o3d.geometry.PointCloud();target.points=o3d.utility.Vector3dVector(prepared[0][0].astype(np.float64));controls=[]
            for i in range(1,len(prepared)):
                source=o3d.geometry.PointCloud();source.points=o3d.utility.Vector3dVector(prepared[i][0].astype(np.float64));before=time.monotonic()
                r=o3d.pipelines.registration.registration_icp(source,target,1.,np.eye(4),o3d.pipelines.registration.TransformationEstimationPointToPoint(),o3d.pipelines.registration.ICPConvergenceCriteria(max_iteration=30))
                C['ICP_calls_completed']+=1;rigid(np.asarray(r.transformation));controls.append(dict(view=i,transform=np.asarray(r.transformation).tolist(),fitness=float(r.fitness),inlier_RMSE=float(r.inlier_rmse),observed_seconds=time.monotonic()-before,role='fixed_operability_control_only'))
            write(case.case_id+'_ICP_CONTROL.json',controls);outputs.append(dict(case=case.case_id,RAP_seal=case.case_id+'_RAP_SEAL.json',ICP_controls=len(controls)))
            assert sum(p.stat().st_size for p in SCOPE.rglob('*') if p.is_file())<32*2**20
        verify_gpu_models('AFTER_OUTPUTS');torch.load=real_load
        assert C['RAP_calls_completed']==2 and C['feature_calls_completed']==5 and C['descriptor_forward_completed']==5 and C['ICP_calls_completed']==3 and C['flow_forward_completed']==10 and C['point_occurrences_decoded']==C['point_occurrences_submitted']==56557
        write('RNG_PHASES.json',dict(phases=rngs,full_tracked_states_saved=True,complete_native_state_claim=False))
        write('RESULTS.json',dict(passed=True,cases=outputs,captures=captures,counters=C,public_access=access,GPU=observed,peak_torch_allocated_bytes=torch.cuda.max_memory_allocated(),peak_torch_reserved_bytes=torch.cuda.max_memory_reserved(),private_reference_evaluation=False,physical_efficacy_claim=False,speed_comparison_qualified=False,candidate_installed=False))
    ok=True
except BaseException as caught:
    error=repr(caught)
    import traceback
    write('FAILURE.json',dict(error=error,traceback=traceback.format_exc(),counters=C));raise
finally:write('worker_exit.json',dict(success=ok,error=error,elapsed_seconds=time.monotonic()-START,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,data_class='RI2_real_public_operability_only',counters=C))
