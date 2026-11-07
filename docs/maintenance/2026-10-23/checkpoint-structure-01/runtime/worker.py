"""Compare uninitialized CPU architecture against inert checkpoint metadata."""
import hashlib,json,os,resource,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent;SCOPE=ROOT.parent
OUT=Path(sys.argv[1]);CASE=sys.argv[2];START=time.monotonic()
REPO=Path('/mnt/e/githouse/RAP-main')
COUNTERS=dict(architectures_constructed=0,checkpoint_load_calls=0,forward_attempts=0,point_reads=0,private_reference_reads=0)
def write(name,value):
    with (OUT/name).open('x') as f:json.dump(value,f,indent=2)
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest().upper()
def path(p):return Path('/mnt/'+p[0].lower()+'/'+p[3:].replace('\\','/'))
def audit(event,args):
    if event=='socket.connect':raise PermissionError('CS1 network forbidden')
    if event=='open' and args and isinstance(args[0],(str,bytes)):
        p=os.fsdecode(args[0])
        if any(t in p for t in ('regx-interface-contract-01/inputs','regx-interface-contract-01/private','regx-reference-package-01/transfer','regx-reference-code-01/transfer')):raise PermissionError('CS1 points/reference forbidden')
        if CASE!='preflight' and p.endswith(('.ckpt','.pth')):raise PermissionError('CS1 checkpoint open forbidden during architecture construction')
ok=False;error=None
try:
    freeze=json.loads((OUT.parent/'SOURCE_FREEZE.json').read_text())
    for name,expected in freeze['binding_files'].items():assert sha(SCOPE/name)==expected,name
    for row in json.loads((SCOPE/'CODE_BINDINGS.json').read_text()):assert sha(path(row['path']))==row['sha256']
    inventory=json.loads((SCOPE/'STATE_METADATA.json').read_text());assert inventory['passed'] and not inventory['class_execution']
    if CASE=='preflight':
        for row in json.loads((SCOPE/'WEIGHT_BINDINGS.json').read_text()):assert sha(path(row['path']))==row['sha256']
        assert not any(k in sys.modules for k in ('torch','numpy'))
        write('RESULTS.json',dict(passed=True,stdlib_only=True,source_files=78,metadata_sha256=sha(SCOPE/'STATE_METADATA.json'),weights=2))
    else:
        sys.addaudithook(audit)
        os.environ['HF_HUB_OFFLINE']='1';os.environ['WANDB_MODE']='disabled'
        sys.path.insert(0,str(REPO));sys.path.insert(0,str(REPO/'dataset_process'))
        import torch
        import hydra
        assert not torch.cuda.is_initialized() and not torch.cuda.is_available()
        real_load=torch.load;real_call=torch.nn.Module._call_impl
        def forbidden_load(*args,**kwargs):
            COUNTERS['checkpoint_load_calls']+=1;raise RuntimeError('CS1 torch.load forbidden')
        def forbidden_forward(*args,**kwargs):
            COUNTERS['forward_attempts']+=1;raise RuntimeError('CS1 neural forward forbidden')
        torch.load=forbidden_load;torch.nn.Module._call_impl=forbidden_forward
        try:
            overrides=['model=rap_12','model.inference_sampling_steps=5','model.rigidity_forcing=true','model.n_generations=1','model.save_results=false']
            with hydra.initialize_config_dir(config_dir=str(REPO/'config'),version_base='1.3'):
                cfg=hydra.compose(config_name='RAP_inference',overrides=overrides)
            assert cfg.model.encoder_ckpt is None and cfg.model.flow_model_ckpt is None
            rap=hydra.utils.instantiate(cfg.model);COUNTERS['architectures_constructed']+=1
            from utils.spinnet.patch_embedder import MiniSpinNet
            mini=MiniSpinNet(num_points_per_patch=512,rad_n=3,azi_n=20,ele_n=7,delta=.8,voxel_sample=10,des_r=5.,is_aligned_to_global_z=True);COUNTERS['architectures_constructed']+=1
            expected_rap=inventory['archives'][0]['state']
            expected_mini={k[5:]:v for k,v in inventory['archives'][1]['state'].items() if k.startswith('Desc.')}
            reports=[]
            for name,model,expected in [('RAP',rap,expected_rap),('miniSpinNet',mini,expected_mini)]:
                actual=model.state_dict()
                missing=sorted(set(actual)-set(expected));unexpected=sorted(set(expected)-set(actual));mismatches=[];rows=[]
                for key in sorted(set(actual)&set(expected)):
                    a=actual[key];e=expected[key]
                    match=list(a.shape)==e['shape'] and str(a.dtype)==e['dtype'] and a.device.type=='cpu'
                    if not match:mismatches.append(dict(key=key,actual_shape=list(a.shape),actual_dtype=str(a.dtype),expected=e))
                    rows.append(dict(key=key,shape=list(a.shape),dtype=str(a.dtype),metadata_match=match))
                reports.append(dict(model=name,actual_state_tensors=len(actual),checkpoint_state_tensors=len(expected),parameters=sum(p.numel() for p in model.parameters()),missing=missing,unexpected=unexpected,mismatches=mismatches,rows=rows,structural_match=not(missing or unexpected or mismatches)))
            write('COMPARISON.json',dict(models=reports,configuration_overrides=overrides,counters=COUNTERS,checkpoint_values_loaded=False,forward_executed=False))
            assert all(r['structural_match'] for r in reports),'Checkpoint/architecture structural incompatibility'
            assert not torch.cuda.is_initialized() and COUNTERS['checkpoint_load_calls']==0 and COUNTERS['forward_attempts']==0
            write('RESULTS.json',dict(passed=True,models=[{k:v for k,v in r.items() if k!='rows'} for r in reports],torch_version=torch.__version__,counters=COUNTERS,CUDA_initialized=False,claim='Key/shape/dtype compatibility only; values, load success and efficacy unproved'))
        finally:torch.load=real_load;torch.nn.Module._call_impl=real_call
    ok=True
except BaseException as caught:
    error=repr(caught)
    import traceback
    write('FAILURE.json',dict(error=error,traceback=traceback.format_exc(),counters=COUNTERS));raise
finally:write('worker_exit.json',dict(success=ok,error=error,elapsed_seconds=time.monotonic()-START,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,data_class='CS1_CPU_architecture_no_weights_or_forward',counters=COUNTERS))
