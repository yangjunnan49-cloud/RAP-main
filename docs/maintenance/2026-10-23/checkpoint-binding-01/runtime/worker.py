"""Authenticate unchanged CPU model constructors against safe-loaded state tensors."""
import hashlib, json, os, resource, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parent;SCOPE=ROOT.parent
OUT=Path(sys.argv[1]);CASE=sys.argv[2];START=time.monotonic()
REPO=Path('/mnt/e/githouse/RAP-main')
COUNTERS=dict(checkpoints_safe_loaded=0,backend_constructor_attempts=0,backend_constructor_completed=False,neural_forward_calls=0,point_reads=0,private_reference_reads=0)
def write(name,value):
    with (OUT/name).open('x') as f:json.dump(value,f,indent=2)
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest().upper()
def path(p):return Path('/mnt/'+p[0].lower()+'/'+p[3:].replace('\\','/'))
def audit(event,args):
    if event=='socket.connect':raise PermissionError('CB1 network forbidden')
    if event=='open' and args and isinstance(args[0],(str,bytes)):
        p=os.fsdecode(args[0])
        if any(t in p for t in ('regx-interface-contract-01/inputs','regx-interface-contract-01/private','regx-reference-package-01/transfer','regx-reference-code-01/transfer')):raise PermissionError('CB1 point/reference access forbidden')
sys.addaudithook(audit)
ok=False;error=None
try:
    freeze=json.loads((OUT.parent/'SOURCE_FREEZE.json').read_text())
    code=SCOPE/'CODE_BINDINGS.json';weights=SCOPE/'WEIGHT_BINDINGS.json'
    assert sha(code)==freeze['code_bindings_sha256'] and sha(weights)==freeze['weight_bindings_sha256']
    for row in json.loads(code.read_text()):assert sha(path(row['path']))==row['sha256']
    binding=json.loads(weights.read_text())
    for row in binding:assert path(row['path']).stat().st_size==row['bytes'] and sha(path(row['path']))==row['sha256']
    if CASE=='preflight':
        assert not any(k in sys.modules for k in ('numpy','torch'))
        write('RESULTS.json',dict(passed=True,stdlib_only=True,source_files=78,weights=2,CUDA_disabled=True,python_version=sys.version,interpreter_sha256=sha(Path(sys.executable).resolve())))
    else:
        import torch
        assert not torch.cuda.is_initialized() and not torch.cuda.is_available()
        state=[];schema=[]
        for row in binding:
            checkpoint=torch.load(path(row['path']),map_location='cpu',weights_only=True)
            COUNTERS['checkpoints_safe_loaded']+=1
            assert isinstance(checkpoint,dict)
            schema.append(dict(name=Path(row['path'].replace('\\','/')).name,top_keys=sorted(checkpoint),top_value_types={str(k):type(v).__name__ for k,v in checkpoint.items()}))
            sd=checkpoint['state_dict'] if 'state_dict' in checkpoint else checkpoint
            assert isinstance(sd,dict) and sd and all(isinstance(k,str) and isinstance(v,torch.Tensor) for k,v in sd.items())
            state.append(sd)
        rap_state=state[0]
        mini_state={k[5:]:v for k,v in state[1].items() if k.startswith('Desc.')}
        assert mini_state
        write('SAFE_CHECKPOINT_SCHEMAS.json',schema)
        calls=[];real_load=torch.nn.Module.load_state_dict
        def observed_load(module,*args,**kwargs):
            row=dict(module=type(module).__name__,argument_keys=len(args[0]),strict=kwargs.get('strict',args[1] if len(args)>1 else True))
            calls.append(row)
            try:
                result=real_load(module,*args,**kwargs)
                row.update(missing_keys=list(result.missing_keys),unexpected_keys=list(result.unexpected_keys),success=True)
                return result
            except BaseException as e:
                row.update(success=False,error=repr(e));raise
        torch.nn.Module.load_state_dict=observed_load
        os.environ['HF_HUB_OFFLINE']='1';os.environ['WANDB_MODE']='disabled'
        sys.path.insert(0,str(REPO));sys.path.insert(0,'/mnt/e/githouse/RAP-SLAM')
        from rap_slam.rap_backend import RAPBackend
        COUNTERS['backend_constructor_attempts']+=1
        try:
            backend=RAPBackend(rap_root=str(REPO),ckpt_path=str(path(binding[0]['path'])),spinnet_ckpt=str(path(binding[1]['path'])),sampling_steps=5,voxel_size=.4,max_points_per_scan=4000,des_r=5.,remove_outliers=True,feature_extraction_on=True,seed=42)
            COUNTERS['backend_constructor_completed']=True
        finally:
            torch.nn.Module.load_state_dict=real_load
            write('LOAD_CALLS.json',calls)
        assert str(backend.device)=='cpu' and not backend.model.training and backend.feature_extractor is not None
        assert len(calls)==2 and all(r['success'] and not r['missing_keys'] and not r['unexpected_keys'] for r in calls),'Missing/unexpected keys or silent load failure'
        reports=[]
        for name,model,expected in [('RAP',backend.model,rap_state),('miniSpinNet',backend.feature_extractor.model,mini_state)]:
            actual=model.state_dict();assert set(actual)==set(expected),name+'_state_keys'
            rows=[];count=0
            for key,a in actual.items():
                b=expected[key]
                assert a.device.type=='cpu' and a.dtype==b.dtype and tuple(a.shape)==tuple(b.shape),name+':'+key+':shape_or_dtype'
                assert torch.isfinite(a).all() and torch.equal(a,b),name+':'+key+':values'
                rows.append(dict(key=key,shape=list(a.shape),dtype=str(a.dtype),elements=a.numel(),exact_match=True));count+=a.numel()
            reports.append(dict(model=name,state_tensors=len(rows),state_elements=count,parameters=sum(p.numel() for p in model.parameters()),rows=rows,exact_match=True))
        assert not torch.cuda.is_initialized()
        write('RESULTS.json',dict(passed=True,load_calls=calls,states=reports,counters=COUNTERS,CUDA_initialized=False,torch_version=torch.__version__,actual_forward_calls=0,configuration='unchanged RI1 backend explicit configuration on CPU',claim='Initialization/checkpoint compatibility only'))
    ok=True
except BaseException as caught:
    error=repr(caught)
    import traceback
    write('FAILURE.json',dict(error=error,traceback=traceback.format_exc(),counters=COUNTERS));raise
finally:
    write('worker_exit.json',dict(success=ok,error=error,elapsed_seconds=time.monotonic()-START,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,data_class='CB1_existing_CPU_model_initialization_only',counters=COUNTERS))
