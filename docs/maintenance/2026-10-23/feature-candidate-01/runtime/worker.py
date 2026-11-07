"""Source-bound original/candidate wrappers with synthetic descriptor stubs."""
import ast, hashlib, json, logging, resource, sys, time
from pathlib import Path
from types import SimpleNamespace
from typing import Dict, Optional, Union
ROOT=Path(__file__).resolve().parent;SCOPE=ROOT.parent
OUT=Path(sys.argv[1]);CASE=sys.argv[2];START=time.monotonic()
def write(name,value):
    with (OUT/name).open('x') as f:json.dump(value,f,indent=2)
ok=False;error=None;calls={'original':0,'candidate':0};stub_calls=[0]
try:
    freeze=json.loads((OUT.parent/'SOURCE_FREEZE.json').read_text())
    raw={k:(SCOPE/'source_snapshot'/f'{k}.py').read_bytes() for k in ('original','candidate')}
    for k,v in raw.items():assert hashlib.sha256(v).hexdigest().upper()==freeze[k+'_sha256']
    live=Path('/mnt/e/githouse/RAP-main/dataset_process/extract_sample_features.py')
    assert hashlib.sha256(live.read_bytes()).hexdigest().upper()==freeze['original_sha256']
    nodes={k:[n for n in ast.walk(ast.parse(v)) if isinstance(n,ast.FunctionDef) and n.name=='extract_features'] for k,v in raw.items()}
    assert all(len(v)==1 for v in nodes.values())
    if CASE=='preflight':
        assert not any(m in sys.modules for m in ('numpy','torch'))
        write('RESULTS.json',dict(passed=True,stdlib_only=True,binding_pass=True,production_unchanged=True))
    else:
        import numpy as np
        import torch
        assert not torch.cuda.is_initialized()
        logs=[]
        class Capture(logging.Handler):
            def emit(self,record):logs.append(record.getMessage())
        logger=logging.getLogger('FC1');logger.addHandler(Capture());logger.setLevel(logging.WARNING)
        functions={}
        for k,v in nodes.items():
            ns=dict(np=np,torch=torch,Dict=Dict,Optional=Optional,Union=Union,logger=logger)
            exec(compile(ast.Module(body=v,type_ignores=[]),str(SCOPE/'source_snapshot'/f'{k}.py'),'exec'),ns)
            functions[k]=ns['extract_features']
        def array(a):return a.detach().cpu().numpy() if isinstance(a,torch.Tensor) else np.asarray(a)
        def input_gate(p,k):
            p=array(p);k=array(k)
            if p.ndim!=2 or k.ndim!=2 or p.shape[1:]!=(3,) or k.shape[1:]!=(3,) or len(p)==0 or len(k)==0 or not np.isfinite(p).all() or not np.isfinite(k).all():raise ValueError('input_rejected')
        def descriptor_gate(a,rows):
            a=array(a)
            if a.shape!=(rows,32) or rows==0 or not np.isfinite(a).all() or not np.any(a!=0):raise ValueError('descriptor_rejected')
            return a
        def invoke(k,obj,p,kp):
            calls[k]+=1
            return functions[k](obj,p,kp)
        def descriptor(**kw):
            stub_calls[0]+=1
            assert not torch.is_grad_enabled() and kw['pts'].dtype==torch.float32 and kw['kpts'].dtype==torch.float32
            assert kw['des_r']==5. and kw['is_aligned_to_global_z'] is True
            return {'desc':kw['kpts'][...,0:1].repeat(1,1,32)}
        def raised(**kw):
            stub_calls[0]+=1
            raise RuntimeError('FC1_deliberate_descriptor_failure')
        controls=[]
        base=np.array([[1.,0.,2.],[2.,3.,1.],[3.,-1.,4.],[4.,2.,-3.]],dtype=np.float64)
        for points_tensor in (False,True):
            for kp_kind in ('default','numpy','tensor'):
                p=torch.from_numpy(base.copy()) if points_tensor else base.copy()
                kp=None if kp_kind=='default' else (torch.from_numpy(base[[3,1]].copy()) if kp_kind=='tensor' else base[[3,1]].copy())
                expected=base[:,0] if kp is None else base[[3,1],0]
                input_gate(p,p if kp is None else kp)
                obj=SimpleNamespace(device='cpu',des_r=5.,is_aligned_to_global_z=True,model=descriptor)
                answers=[]
                for k in functions:
                    result=invoke(k,obj,p,kp);f=descriptor_gate(result['features'],len(expected))
                    assert np.array_equal(f,np.repeat(expected[:,None].astype(np.float32),32,axis=1))
                    assert isinstance(result['features'],torch.Tensor)==points_tensor
                    assert np.array_equal(array(p),base)
                    if kp is not None:assert result['keypoints'] is kp and np.array_equal(array(kp),base[[3,1]])
                    answers.append(f)
                assert np.array_equal(*answers)
                controls.append(dict(case='positive_agreement',points_tensor=points_tensor,keypoints=kp_kind,passed=True))
                obj.model=raised
                before=len(logs)
                original_expected_error=kp_kind=='numpy' or (kp_kind=='default' and not points_tensor)
                if original_expected_error:
                    try:invoke('original',obj,p,kp)
                    except AttributeError as caught:assert isinstance(caught.__context__,RuntimeError) and 'dim' in str(caught)
                    else:raise AssertionError('Original NumPy failure unexpectedly absent')
                else:
                    original=invoke('original',obj,p,kp)
                    assert not np.any(array(original['features']))
                result=invoke('candidate',obj,p,kp)
                assert array(result['features']).shape==(len(expected),32) and not np.any(array(result['features']))
                assert isinstance(result['features'],torch.Tensor)==points_tensor
                assert len(logs)==before+2 and all('FC1_deliberate_descriptor_failure' in s for s in logs[before:])
                try:descriptor_gate(result['features'],len(expected))
                except ValueError:pass
                else:raise AssertionError('Zero fallback accepted')
                controls.append(dict(case='exception_fallback',points_tensor=points_tensor,keypoints=kp_kind,original_secondary_error=original_expected_error,candidate_zero_rejected=True,passed=True))
        for tensor in (False,True):
            p=torch.empty((0,3)) if tensor else np.empty((0,3))
            for k in functions:
                result=invoke(k,obj,p,None);assert tuple(result['features'].shape)==(0,)
            try:input_gate(p,p)
            except ValueError:pass
            else:raise AssertionError('Empty input admitted')
            controls.append(dict(case='empty_unchanged_rejected',tensor=tensor,passed=True))
        for name,bad in [('zero',np.zeros((4,32))),('nan',np.full((4,32),np.nan)),('infinity',np.full((4,32),np.inf)),('wrong_rows',np.ones((3,32))),('wrong_channels',np.ones((4,31))),('batched',np.ones((1,4,32)))]:
            try:descriptor_gate(bad,4)
            except ValueError:pass
            else:raise AssertionError('Descriptor gate accepted '+name)
            controls.append(dict(case='descriptor_reject_'+name,passed=True))
        for name,bad in [('batched',np.ones((1,4,3))),('nonfinite',np.full((4,3),np.nan)),('wrong_xyz',np.ones((4,4)))]:
            try:input_gate(bad,bad)
            except ValueError:pass
            else:raise AssertionError('Input gate accepted '+name)
            controls.append(dict(case='input_reject_'+name,passed=True))
        assert not torch.cuda.is_initialized()
        write('RESULTS.json',dict(passed=True,controls=controls,control_count=len(controls),wrapper_calls=calls,stub_calls=stub_calls[0],warnings=len(logs),CUDA_initialized=False,
            actual_neural_models=0,production_unchanged=True,candidate_installed=False,strict_guard_installed=False,
            limitation='Zero fallback is still descriptor failure; invalid and batched input excluded; no model/checkpoint-quality or physical-efficacy claim'))
    ok=True
except BaseException as caught:
    error=repr(caught)
    import traceback
    write('FAILURE.json',dict(error=error,traceback=traceback.format_exc()));raise
finally:
    write('worker_exit.json',dict(success=ok,error=error,elapsed_seconds=time.monotonic()-START,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
        data_class='FC1_CPU_synthetic_only',actual_neural_models=0,raw_point_reads=0,private_reference_reads=0))
