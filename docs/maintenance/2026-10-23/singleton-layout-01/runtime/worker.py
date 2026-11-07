"""Exact integer address oracle and small independent Torch layout checks."""
import hashlib,itertools,json,math,os,resource,sys,time
from pathlib import Path
from layout_contract import row_major_storage
ROOT=Path(__file__).resolve().parent;OUT=Path(sys.argv[1]);START=time.monotonic()
def write(name,value):
    with (OUT/name).open('x') as f:json.dump(value,f,indent=2)
def audit(event,args):
    if event=='socket.connect':raise PermissionError('SL1 network forbidden')
    if event=='open' and args and isinstance(args[0],(str,bytes)):
        p=os.fsdecode(args[0])
        if p.endswith(('.ckpt','.pth')) or 'STATE_METADATA.json' in p or 'ARCHIVE_BINDINGS.json' in p or 'regx-interface-contract-01' in p or 'regx-reference-' in p:raise PermissionError('SL1 actual weights/metadata/points/reference forbidden')
sys.addaudithook(audit)
ok=False;error=None
try:
    counts=dict(valid_layouts=0,valid_coordinate_addresses=0,corrupt_non_singleton_axes=0)
    representatives=[((),())]
    for rank in range(5):
        for shape in itertools.product(range(1,5),repeat=rank):
            step=1;canonical=[]
            for d in reversed(shape):canonical.append(step);step*=d
            canonical=tuple(reversed(canonical))
            choices=[tuple(sorted({0,c,17})) if d==1 else (c,) for d,c in zip(shape,canonical)]
            for stride in itertools.product(*choices):
                assert row_major_storage(shape,stride,math.prod(shape))
                addresses=[sum(i*s for i,s in zip(index,stride)) for index in itertools.product(*(range(d) for d in shape))]
                assert addresses==list(range(math.prod(shape)))
                counts['valid_layouts']+=1;counts['valid_coordinate_addresses']+=len(addresses)
                if len(representatives)<16 and any(d==1 and a!=b for d,a,b in zip(shape,stride,canonical)):representatives.append((shape,stride))
            for axis,d in enumerate(shape):
                if d==1:continue
                corrupt=list(canonical);corrupt[axis]+=1
                assert not row_major_storage(shape,corrupt,math.prod(shape))
                addresses=[sum(i*s for i,s in zip(index,corrupt)) for index in itertools.product(*(range(d) for d in shape))]
                assert addresses!=list(range(math.prod(shape)))
                counts['corrupt_non_singleton_axes']+=1
    rejected=[('transpose',(2,3),(1,2),6,0),('overlap',(2,3),(0,1),6,0),('hole',(2,3),(4,1),6,0),('negative_singleton',(1,2),(-1,1),2,0),('offset',(2,3),(3,1),6,1),('wrong_count',(2,3),(3,1),7,0),('empty',(0,3),(3,1),0,0),('bool_dimension',(True,3),(3,1),3,0),('rank_mismatch',(2,3),(1,),6,0)]
    for label,shape,stride,elements,offset in rejected:assert not row_major_storage(shape,stride,elements,offset),label
    assert len(representatives)==16
    representatives.append(((16,3,1,1),(3,1,3,3)))
    import torch
    assert not torch.cuda.is_initialized() and not torch.cuda.is_available()
    real_load=torch.load
    def forbidden(*args,**kwargs):raise AssertionError('SL1 torch.load forbidden')
    torch.load=forbidden
    try:
        probes=[]
        for shape,stride in representatives:
            n=math.prod(shape);base=torch.arange(n,dtype=torch.float64)
            actual=torch.as_strided(base,shape,stride)
            assert actual.is_contiguous() and torch.equal(actual.contiguous().reshape(-1),base)
            probes.append(dict(shape=list(shape),stride=list(stride),elements=n,is_contiguous=True,exact_synthetic_values=True))
        assert not torch.cuda.is_initialized()
    finally:torch.load=real_load
    write('RESULTS.json',dict(passed=True,counts=counts,fixed_negative_count=len(rejected),torch_probes=probes,torch_probe_count=len(probes),torch_version=torch.__version__,CUDA_initialized=False,actual_weight_reads=0,TT1_changed=False,TT1_retried=False,real_transfer_or_inference_admitted=False,claim='Synthetic future-layout feasibility only'))
    ok=True
except BaseException as caught:
    error=repr(caught)
    import traceback
    write('FAILURE.json',dict(error=error,traceback=traceback.format_exc()));raise
finally:write('worker_exit.json',dict(success=ok,error=error,elapsed_seconds=time.monotonic()-START,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,data_class='SL1_synthetic_integer_and_small_Torch_layouts_only'))
