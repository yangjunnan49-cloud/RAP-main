"""TT2 synthetic admission and complete fixed CPU parameter transfer."""
import hashlib,json,os,resource,struct,sys,time
from pathlib import Path
from tensor_candidate import byte_hash,decode,tensor_hash
from fixed_state import decode_archive,verify_model,path,sha_file
ROOT=Path(__file__).resolve().parent;SCOPE=ROOT.parent;OUT=Path(sys.argv[1]);CASE=sys.argv[2];START=time.monotonic()
REPO=Path('/mnt/e/githouse/RAP-main')
COUNTERS=dict(architectures_constructed=0,checkpoint_unpickle_calls=0,forward_attempts=0,loaded_state_tensors=0,point_reads=0,reference_reads=0)
def write(name,value):
    with (OUT/name).open('x') as f:json.dump(value,f,indent=2)
def audit(event,args):
    if event=='socket.connect':raise PermissionError('TT2 network forbidden')
    if event=='open' and args and isinstance(args[0],(str,bytes)):
        p=os.fsdecode(args[0])
        if any(t in p for t in ('regx-interface-contract-01/inputs','regx-interface-contract-01/private','regx-reference-package-01/transfer','regx-reference-code-01/transfer')):raise PermissionError('TT2 points/reference forbidden')
sys.addaudithook(audit);ok=False;error=None
try:
    freeze=json.loads((OUT.parent/'SOURCE_FREEZE.json').read_text())
    for name,expected in freeze['binding_files'].items():assert sha_file(SCOPE/name)==expected,name
    for row in json.loads((SCOPE/'CODE_BINDINGS.json').read_text()):assert sha_file(path(row['path']))==row['sha256']
    weights=json.loads((SCOPE/'WEIGHT_BINDINGS.json').read_text())
    if CASE=='preflight':
        for row in weights:assert sha_file(path(row['path']))==row['sha256']
        assert not any(k in sys.modules for k in ('numpy','torch'))
        write('RESULTS.json',dict(passed=True,stdlib_only=True,source_files=78,weights=2,SL1_predicate_sha256=sha_file(ROOT/'layout_contract.py')))
    else:
        os.environ['HF_HUB_OFFLINE']='1';os.environ['WANDB_MODE']='disabled'
        import torch
        assert not torch.cuda.is_initialized() and not torch.cuda.is_available()
        real_load=torch.load;real_call=torch.nn.Module._call_impl
        def forbidden_load(*args,**kwargs):COUNTERS['checkpoint_unpickle_calls']+=1;raise RuntimeError('TT2 torch.load forbidden')
        def forbidden_forward(*args,**kwargs):COUNTERS['forward_attempts']+=1;raise RuntimeError('TT2 forward forbidden')
        torch.load=forbidden_load;torch.nn.Module._call_impl=forbidden_forward
        try:
            if CASE=='controls':
                controls=[]
                fixtures=[('float32','<2f',(0.5,-1.25),[2],[1]),('float64','<2d',(0.001,2.),[2],[1]),('int64','<2q',(0,3),[2],[1]),('int64','<q',(4,),[],[]),('uint8','<2B',(0,255),[2],[1]),('float32','<2f',(.5,-1.25),[1,2,1],[17,1,0]),('float32','<48f',tuple((i-24)/8 for i in range(48)),[16,3,1,1],[3,1,3,3])]
                for i,(dtype,fmt,values,shape,stride) in enumerate(fixtures):
                    raw=struct.pack(fmt,*values);meta=dict(dtype='torch.'+dtype,shape=shape,stride=stride,elements=len(values),storage_elements=len(values),storage_offset=0)
                    a=decode(raw,meta,byte_hash(raw),torch);assert tuple(a.reshape(-1).tolist())==values and tensor_hash(a)==byte_hash(raw)
                    controls.append(dict(case='independent_struct_'+str(i),shape=shape,stride=stride,passed=True))
                raw=struct.pack('<2f',1.,2.);meta=dict(dtype='torch.float32',shape=[2],stride=[1],elements=2,storage_elements=2,storage_offset=0)
                bad=[('hash',raw,meta,'0'*64),('bytes',raw[:-1],meta,byte_hash(raw[:-1])),('offset',raw,dict(meta,storage_offset=1),byte_hash(raw)),('stride',raw,dict(meta,stride=[2]),byte_hash(raw)),('dtype',raw,dict(meta,dtype='torch.float16'),byte_hash(raw)),('alias',raw,dict(meta,stride=[0]),byte_hash(raw)),('negative_singleton',raw,dict(meta,shape=[1,2],stride=[-1,1]),byte_hash(raw))]
                r=struct.pack('<6f',*range(6));bad.append(('transpose',r,dict(meta,shape=[2,3],stride=[1,2],elements=6,storage_elements=6),byte_hash(r)))
                for label,v in [('nan',float('nan')),('inf',float('inf'))]:
                    r=struct.pack('<2f',v,2.);bad.append((label,r,meta,byte_hash(r)))
                for name,r,m,h in bad:
                    try:decode(r,m,h,torch)
                    except ValueError:pass
                    else:raise AssertionError('Bad storage admitted:'+name)
                    controls.append(dict(case='reject_'+name,passed=True))
                assert len(controls)==17
                write('RESULTS.json',dict(passed=True,controls=controls,count=len(controls),actual_checkpoint_tensors_decoded=0,CUDA_initialized=False))
            elif CASE=='transfer':
                sys.path.insert(0,str(REPO));sys.path.insert(0,str(REPO/'dataset_process'))
                import numpy as np
                import hydra
                torch.manual_seed(42);np.random.seed(42)
                def rng(tag):
                    tb=torch.get_rng_state().numpy().tobytes();state=np.random.get_state()
                    nb=json.dumps(dict(algorithm=state[0],keys=state[1].tolist(),position=state[2],has_gauss=state[3],cached_gaussian=state[4]),sort_keys=True).encode()
                    (OUT/(tag+'_torch_rng.bin')).write_bytes(tb);(OUT/(tag+'_numpy_rng.json')).write_bytes(nb)
                    return dict(tag=tag,Torch_CPU_sha256=byte_hash(tb),NumPy_sha256=byte_hash(nb),Torch_bytes=len(tb),NumPy_bytes=len(nb))
                phases=[rng('seeded_before_architectures')]
                with hydra.initialize_config_dir(config_dir=str(REPO/'config'),version_base='1.3'):
                    cfg=hydra.compose(config_name='RAP_inference',overrides=['model=rap_12','model.inference_sampling_steps=5','model.rigidity_forcing=true','model.n_generations=1','model.save_results=false'])
                assert cfg.model.encoder_ckpt is None and cfg.model.flow_model_ckpt is None
                inventory=json.loads((SCOPE/'STATE_METADATA.json').read_text())['archives'];archives=json.loads((SCOPE/'ARCHIVE_BINDINGS.json').read_text())['archives'];reports=[]
                for index,name in enumerate(('RAP','miniSpinNet')):
                    if index==0:model=hydra.utils.instantiate(cfg.model)
                    else:
                        from utils.spinnet.patch_embedder import MiniSpinNet
                        model=MiniSpinNet(num_points_per_patch=512,rad_n=3,azi_n=20,ele_n=7,delta=.8,voxel_sample=10,des_r=5.,is_aligned_to_global_z=True)
                    COUNTERS['architectures_constructed']+=1;before=rng(name+'_before_transfer');phases.append(before)
                    decoded,hashes,info=decode_archive(weights[index],inventory[index],archives[index],torch,descriptor_only=index==1)
                    assert set(model.state_dict())==set(decoded)
                    result=model.load_state_dict(decoded,strict=True);assert not result.missing_keys and not result.unexpected_keys
                    model.eval();rows=verify_model(model,hashes,torch);after=rng(name+'_after_transfer');phases.append(after)
                    assert before['Torch_CPU_sha256']==after['Torch_CPU_sha256'] and before['NumPy_sha256']==after['NumPy_sha256']
                    COUNTERS['loaded_state_tensors']+=len(rows)
                    report=dict(model=name,loaded_tensors=len(rows),strict_load=True,missing=[],unexpected=[],rows=rows,archive=info,transfer_tracked_RNG_unchanged=True)
                    filename=name+'_TRANSFER.json';write(filename,report);write(name+'_TRANSFER_SEAL.json',dict(file=filename,sha256=sha_file(OUT/filename),fully_verified=True))
                    reports.append(dict(model=name,loaded_tensors=len(rows),receipt=filename,receipt_sha256=sha_file(OUT/filename),transfer_tracked_RNG_unchanged=True));del decoded,model
                assert COUNTERS['loaded_state_tensors']==402 and not torch.cuda.is_initialized()
                write('RNG_PHASES.json',dict(phases=phases,seed42_once_before_construction=True,full_tracked_states_saved=True,hidden_native_or_GPU_RNG_certified=False))
                write('RESULTS.json',dict(passed=True,models=reports,counters=COUNTERS,CUDA_initialized=False,torch_version=torch.__version__,numpy_version=np.__version__,candidate_installed=False,claim='Complete fixed CPU tensor bytes and tracked transfer-RNG invariance only'))
            else:raise ValueError('unknown_case')
        finally:torch.load=real_load;torch.nn.Module._call_impl=real_call
        assert COUNTERS['checkpoint_unpickle_calls']==0 and COUNTERS['forward_attempts']==0
    ok=True
except BaseException as caught:
    error=repr(caught)
    import traceback
    write('FAILURE.json',dict(error=error,traceback=traceback.format_exc(),counters=COUNTERS));raise
finally:write('worker_exit.json',dict(success=ok,error=error,elapsed_seconds=time.monotonic()-START,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,data_class='TT2_CPU_parameter_transfer_no_forward',counters=COUNTERS))
