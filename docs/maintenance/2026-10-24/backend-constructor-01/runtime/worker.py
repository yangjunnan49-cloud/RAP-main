"""Source constructor integration only, with no learned forward or unsafe load."""
import hashlib,json,os,resource,sys,time
from pathlib import Path
from fixed_state import path,sha_file,verify_model
from tensor_candidate import byte_hash
from constructor_bridge import validate_request,format_state,FixedTensorBridge
ROOT=Path(__file__).resolve().parent;SCOPE=ROOT.parent;OUT=Path(sys.argv[1]);CASE=sys.argv[2];START=time.monotonic();REPO=Path('/mnt/e/githouse/RAP-main')
COUNTERS=dict(backend_constructor_attempts=0,backend_constructor_completed=False,neural_forward_attempts=0,original_torch_load_calls=0,point_reads=0,reference_reads=0)
def write(name,value):
    with (OUT/name).open('x') as f:json.dump(value,f,indent=2)
def audit(event,args):
    if event=='socket.connect':raise PermissionError('BI1 network forbidden')
    if event=='open' and args and isinstance(args[0],(str,bytes)) and any(t in os.fsdecode(args[0]) for t in ('regx-interface-contract-01/inputs','regx-interface-contract-01/private','regx-reference-package-01/transfer','regx-reference-code-01/transfer')):raise PermissionError('BI1 point/reference forbidden')
sys.addaudithook(audit);ok=False;error=None
try:
    freeze=json.loads((OUT.parent/'SOURCE_FREEZE.json').read_text())
    for name,expected in freeze['binding_files'].items():assert sha_file(SCOPE/name)==expected
    for row in json.loads((SCOPE/'CODE_BINDINGS.json').read_text()):assert sha_file(path(row['path']))==row['sha256']
    tt2=json.loads((SCOPE/'TT2_RESULTS.json').read_text());assert tt2['passed'] and tt2['counters']['loaded_state_tensors']==402
    weights=json.loads((SCOPE/'WEIGHT_BINDINGS.json').read_text())
    if CASE=='preflight':
        for row in weights:assert sha_file(path(row['path']))==row['sha256']
        assert 'torch' not in sys.modules
        write('RESULTS.json',dict(passed=True,stdlib_only=True,source_files=78,TT2_complete402=True))
    elif CASE=='controls':
        controls=[];fake=[dict(path='E:\\synthetic\\rap.ckpt'),dict(path='E:\\synthetic\\mini.pth')]
        kw=dict(map_location='cpu',weights_only=False)
        for i in (0,1):
            assert validate_request(path(fake[i]['path']),(),kw,fake,i)==i;controls.append(dict(case='ordered_route_'+str(i),passed=True))
        sentinel=object();d={'a':sentinel};assert format_state(0,d)['state_dict'] is d and format_state(1,d)=={'Desc.a':sentinel}
        controls.append(dict(case='exact_state_format_and_identity',passed=True))
        bad=[('unknown_path',Path('/tmp/not_admitted'),(),kw,0),('replay',path(fake[0]['path']),(),kw,1),('wrong_order',path(fake[1]['path']),(),kw,0),('positional',path(fake[0]['path']),(1,),kw,0),('unexpected_kw',path(fake[0]['path']),(),dict(kw,mmap=True),0),('different_weights_only',path(fake[0]['path']),(),dict(kw,weights_only=True),0),('unadmitted_device',path(fake[0]['path']),(),dict(kw,map_location='cuda'),0)]
        for name,f,a,k,i in bad:
            try:validate_request(f,a,k,fake,i)
            except ValueError:pass
            else:raise AssertionError('Unexpected route admitted:'+name)
            controls.append(dict(case='reject_'+name,passed=True))
        assert 'torch' not in sys.modules
        write('RESULTS.json',dict(passed=True,count=len(controls),controls=controls,stdlib_only=True,actual_weight_reads=0))
    else:
        import torch
        import numpy as np
        assert not torch.cuda.is_available() and not torch.cuda.is_initialized()
        os.environ['HF_HUB_OFFLINE']='1';os.environ['WANDB_MODE']='disabled';sys.path.insert(0,str(REPO));sys.path.insert(0,'/mnt/e/githouse/RAP-SLAM')
        from rap_slam.rap_backend import RAPBackend
        seed_calls=[];load_calls=[]
        def capture(tag):
            tb=torch.get_rng_state().numpy().tobytes();s=np.random.get_state();nb=json.dumps(dict(algorithm=s[0],keys=s[1].tolist(),position=s[2],has_gauss=s[3],cached_gaussian=s[4]),sort_keys=True).encode()
            (OUT/(tag+'_torch_rng.bin')).write_bytes(tb);(OUT/(tag+'_numpy_rng.json')).write_bytes(nb)
            return dict(tag=tag,Torch_CPU_sha256=byte_hash(tb),NumPy_sha256=byte_hash(nb))
        bridge=FixedTensorBridge(weights,json.loads((SCOPE/'STATE_METADATA.json').read_text())['archives'],json.loads((SCOPE/'ARCHIVE_BINDINGS.json').read_text())['archives'],torch,capture)
        real_load=torch.load;real_state=torch.nn.Module.load_state_dict;real_call=torch.nn.Module._call_impl;real_tseed=torch.manual_seed;real_nseed=np.random.seed
        precision_before=torch.get_float32_matmul_precision();cudnn_before=(torch.backends.cudnn.benchmark,torch.backends.cudnn.deterministic,torch.backends.cudnn.allow_tf32)
        def tseed(seed):seed_calls.append(dict(library='Torch',seed=seed));return real_tseed(seed)
        def nseed(seed):seed_calls.append(dict(library='NumPy',seed=seed));return real_nseed(seed)
        def forbidden(*args,**kwargs):COUNTERS['neural_forward_attempts']+=1;raise RuntimeError('BI1 neural forward forbidden')
        def observed_state(module,*args,**kwargs):
            incoming=args[0];actual=module.state_dict();assert set(actual)==set(incoming)
            for k,a in actual.items():assert tuple(a.shape)==tuple(incoming[k].shape) and a.dtype==incoming[k].dtype
            result=real_state(module,*args,**kwargs)
            row=dict(module=type(module).__name__,source_strict=kwargs.get('strict',True),tensors=len(incoming),missing=list(result.missing_keys),unexpected=list(result.unexpected_keys));load_calls.append(row)
            assert not result.missing_keys and not result.unexpected_keys
            return result
        torch.load=bridge;torch.nn.Module.load_state_dict=observed_state;torch.nn.Module._call_impl=forbidden;torch.manual_seed=tseed;np.random.seed=nseed
        try:
            COUNTERS['backend_constructor_attempts']+=1
            backend=RAPBackend(rap_root=str(REPO),ckpt_path=str(path(weights[0]['path'])),spinnet_ckpt=str(path(weights[1]['path'])),sampling_steps=5,voxel_size=.4,max_points_per_scan=4000,des_r=5.,remove_outliers=True,feature_extraction_on=True,seed=42)
            COUNTERS['backend_constructor_completed']=True
        finally:
            torch.load=real_load;torch.nn.Module.load_state_dict=real_state;torch.nn.Module._call_impl=real_call;torch.manual_seed=real_tseed;np.random.seed=real_nseed
            write('LOAD_CALLS.json',dict(bridge_calls=bridge.calls,source_state_calls=load_calls,seed_calls=seed_calls))
        assert seed_calls==[dict(library='Torch',seed=42),dict(library='NumPy',seed=42)]
        assert len(bridge.calls)==2 and all(r['success'] for r in bridge.calls) and len(load_calls)==2
        assert str(backend.device)=='cpu' and not backend.model.training and not backend.feature_extractor.model.training
        reports=[]
        for i,(name,model) in enumerate([('RAP',backend.model),('miniSpinNet',backend.feature_extractor.model)]):
            rows=verify_model(model,bridge.expected_hashes[i],torch);file=name+'_SOURCE_CONSTRUCTOR.json';write(file,dict(model=name,rows=rows,source_constructor_values_verified=True))
            write(name+'_SEAL.json',dict(file=file,sha256=sha_file(OUT/file),tensors=len(rows)));reports.append(dict(model=name,tensors=len(rows),receipt=file,sha256=sha_file(OUT/file)))
        assert sum(r['tensors'] for r in reports)==402 and COUNTERS['neural_forward_attempts']==0 and not torch.cuda.is_initialized()
        assert precision_before==torch.get_float32_matmul_precision() and cudnn_before==(torch.backends.cudnn.benchmark,torch.backends.cudnn.deterministic,torch.backends.cudnn.allow_tf32)
        write('RESULTS.json',dict(passed=True,models=reports,bridge_calls=bridge.calls,source_state_calls=load_calls,seed_calls=seed_calls,counters=COUNTERS,precision_policy_preserved=True,CUDA_initialized=False,torch_version=torch.__version__,numpy_version=np.__version__,candidate_installed=False,claim='Original CPU backend constructor integration and complete fixed tensor values only'))
    ok=True
except BaseException as caught:
    error=repr(caught)
    import traceback
    write('FAILURE.json',dict(error=error,traceback=traceback.format_exc(),counters=COUNTERS));raise
finally:write('worker_exit.json',dict(success=ok,error=error,elapsed_seconds=time.monotonic()-START,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,data_class='BI1_original_CPU_backend_constructor_no_forward',counters=COUNTERS))
