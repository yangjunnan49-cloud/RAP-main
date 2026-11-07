"""Fixed tensor-only parameter transfer candidate, CPU and no forward."""
import hashlib,json,os,resource,struct,sys,time,zipfile
from pathlib import Path,PurePosixPath
from tensor_candidate import byte_hash,decode,tensor_hash
ROOT=Path(__file__).resolve().parent;SCOPE=ROOT.parent
OUT=Path(sys.argv[1]);CASE=sys.argv[2];START=time.monotonic()
REPO=Path('/mnt/e/githouse/RAP-main')
COUNTERS=dict(architectures_constructed=0,checkpoint_unpickle_calls=0,forward_attempts=0,loaded_state_tensors=0,point_reads=0,reference_reads=0)
def write(name,value):
    with (OUT/name).open('x') as f:json.dump(value,f,indent=2)
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest().upper()
def path(p):return Path('/mnt/'+p[0].lower()+'/'+p[3:].replace('\\','/'))
def audit(event,args):
    if event=='socket.connect':raise PermissionError('TT1 network forbidden')
    if event=='open' and args and isinstance(args[0],(str,bytes)):
        p=os.fsdecode(args[0])
        if any(t in p for t in ('regx-interface-contract-01/inputs','regx-interface-contract-01/private','regx-reference-package-01/transfer','regx-reference-code-01/transfer')):raise PermissionError('TT1 points/reference forbidden')
sys.addaudithook(audit)
ok=False;error=None
try:
    freeze=json.loads((OUT.parent/'SOURCE_FREEZE.json').read_text())
    for name,expected in freeze['binding_files'].items():assert sha(SCOPE/name)==expected,name
    for row in json.loads((SCOPE/'CODE_BINDINGS.json').read_text()):assert sha(path(row['path']))==row['sha256']
    weights=json.loads((SCOPE/'WEIGHT_BINDINGS.json').read_text())
    if CASE=='preflight':
        for row in weights:assert sha(path(row['path']))==row['sha256']
        assert not any(k in sys.modules for k in ('numpy','torch'))
        write('RESULTS.json',dict(passed=True,stdlib_only=True,source_files=78,weights=2))
    else:
        os.environ['HF_HUB_OFFLINE']='1';os.environ['WANDB_MODE']='disabled'
        import torch
        assert not torch.cuda.is_initialized() and not torch.cuda.is_available()
        real_load=torch.load;real_call=torch.nn.Module._call_impl
        def forbidden_load(*args,**kwargs):
            COUNTERS['checkpoint_unpickle_calls']+=1;raise RuntimeError('TT1 torch.load forbidden')
        def forbidden_forward(*args,**kwargs):
            COUNTERS['forward_attempts']+=1;raise RuntimeError('TT1 forward forbidden')
        torch.load=forbidden_load;torch.nn.Module._call_impl=forbidden_forward
        try:
            if CASE=='controls':
                controls=[]
                fixtures=[('float32','<2f',(0.5,-1.25),[2],[1]),('float64','<2d',(0.001,2.),[2],[1]),('int64','<2q',(0,3),[2],[1]),('int64','<q',(4,),[],[]),('uint8','<2B',(0,255),[2],[1])]
                for dtype,fmt,values,shape,stride in fixtures:
                    raw=struct.pack(fmt,*values);meta=dict(dtype='torch.'+dtype,shape=shape,stride=stride,elements=len(values),storage_elements=len(values),storage_offset=0)
                    a=decode(raw,meta,byte_hash(raw),torch)
                    assert tuple(a.reshape(-1).tolist())==values and tensor_hash(a)==byte_hash(raw)
                    controls.append(dict(case='independent_struct_'+dtype+('_scalar' if not shape else ''),passed=True))
                raw=struct.pack('<2f',1.,2.);meta=dict(dtype='torch.float32',shape=[2],stride=[1],elements=2,storage_elements=2,storage_offset=0)
                bad=[('hash',raw,meta,'0'*64),('byte_length',raw[:-1],meta,byte_hash(raw[:-1])),('offset',raw,dict(meta,storage_offset=1),byte_hash(raw)),('stride',raw,dict(meta,stride=[2]),byte_hash(raw)),('dtype',raw,dict(meta,dtype='torch.float16'),byte_hash(raw))]
                for label,value in [('nan',float('nan')),('inf',float('inf'))]:
                    r=struct.pack('<2f',value,2.);bad.append((label,r,meta,byte_hash(r)))
                for name,r,m,h in bad:
                    try:decode(r,m,h,torch)
                    except ValueError:pass
                    else:raise AssertionError('Bad storage admitted:'+name)
                    controls.append(dict(case='reject_'+name,passed=True))
                write('RESULTS.json',dict(passed=True,controls=controls,count=len(controls),CUDA_initialized=False,actual_checkpoint_tensors_decoded=0))
            elif CASE=='transfer':
                sys.path.insert(0,str(REPO));sys.path.insert(0,str(REPO/'dataset_process'))
                import hydra
                with hydra.initialize_config_dir(config_dir=str(REPO/'config'),version_base='1.3'):
                    cfg=hydra.compose(config_name='RAP_inference',overrides=['model=rap_12','model.inference_sampling_steps=5','model.rigidity_forcing=true','model.n_generations=1','model.save_results=false'])
                assert cfg.model.encoder_ckpt is None and cfg.model.flow_model_ckpt is None
                rap=hydra.utils.instantiate(cfg.model);COUNTERS['architectures_constructed']+=1
                from utils.spinnet.patch_embedder import MiniSpinNet
                mini=MiniSpinNet(num_points_per_patch=512,rad_n=3,azi_n=20,ele_n=7,delta=.8,voxel_sample=10,des_r=5.,is_aligned_to_global_z=True);COUNTERS['architectures_constructed']+=1
                inventory=json.loads((SCOPE/'STATE_METADATA.json').read_text())['archives']
                archives=json.loads((SCOPE/'ARCHIVE_BINDINGS.json').read_text())['archives']
                reports=[]
                for index,(name,model) in enumerate([('RAP',rap),('miniSpinNet',mini)]):
                    p=path(weights[index]['path']);assert sha(p)==weights[index]['sha256']
                    records=inventory[index]['state']
                    records=records if index==0 else {k[5:]:v for k,v in records.items() if k.startswith('Desc.')}
                    modelstate=model.state_dict();assert set(modelstate)==set(records)
                    decoded={};hashes={};byteorder=None
                    with zipfile.ZipFile(p) as z:
                        members=z.infolist();names=[m.filename for m in members];assert len(names)==len(set(names))
                        pkl=[m for m in members if PurePosixPath(m.filename).name=='data.pkl'];assert len(pkl)==1
                        prefix=pkl[0].filename.rsplit('/',1)[0]
                        order=prefix+'/byteorder'
                        if order in names:byteorder=z.read(order).decode();assert byteorder=='little'
                        elif index==0:raise ValueError('RAP requires explicit byteorder')
                        elif torch.serialization.get_default_load_endianness() not in (None,torch.serialization.LoadEndianness.LITTLE):raise ValueError('legacy_default_byteorder')
                        expected_members={r['name']:r for r in archives[index]['entries']}
                        for key,meta in records.items():
                            a=modelstate[key];assert list(a.shape)==meta['shape'] and str(a.dtype)==meta['dtype']
                            member=prefix+'/data/'+meta['storage'];record=expected_members[member]
                            assert record['bytes']<=64*2**20 and z.getinfo(member).file_size==record['bytes']
                            raw=z.read(member);decoded[key]=decode(raw,meta,record['sha256'],torch);hashes[key]=record['sha256']
                    result=model.load_state_dict(decoded,strict=True)
                    assert not result.missing_keys and not result.unexpected_keys
                    model.eval();rows=[]
                    for key,a in model.state_dict().items():
                        got=tensor_hash(a);assert got==hashes[key]
                        assert not a.is_floating_point() or torch.isfinite(a).all()
                        rows.append(dict(key=key,sha256=got,exact_archive_bytes=True,finite=True))
                    COUNTERS['loaded_state_tensors']+=len(rows)
                    reports.append(dict(model=name,loaded_tensors=len(rows),bytes=sum(a.numel()*a.element_size() for a in decoded.values()),strict_load=True,missing=[],unexpected=[],rows=rows,byteorder_marker=byteorder,legacy_default_little=index==1 and byteorder is None,ignored_non_Desc_tensors=0 if index==0 else inventory[index]['state_tensors']-len(rows)))
                    del decoded
                assert COUNTERS['loaded_state_tensors']==402 and not torch.cuda.is_initialized()
                write('RESULTS.json',dict(passed=True,models=reports,counters=COUNTERS,CUDA_initialized=False,torch_version=torch.__version__,candidate_installed=False,claim='Fixed CPU tensor byte transfer only; no checkpoint config/RNG objects or inference'))
            else:raise ValueError('unknown_case')
        finally:torch.load=real_load;torch.nn.Module._call_impl=real_call
        assert COUNTERS['checkpoint_unpickle_calls']==0 and COUNTERS['forward_attempts']==0
    ok=True
except BaseException as caught:
    error=repr(caught)
    import traceback
    write('FAILURE.json',dict(error=error,traceback=traceback.format_exc(),counters=COUNTERS));raise
finally:write('worker_exit.json',dict(success=ok,error=error,elapsed_seconds=time.monotonic()-START,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,data_class='TT1_CPU_candidate_tensor_transfer_no_forward',counters=COUNTERS))
