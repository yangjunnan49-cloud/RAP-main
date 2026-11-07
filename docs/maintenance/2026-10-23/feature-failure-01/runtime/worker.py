"""Characterize the exact feature wrapper with synthetic descriptor stubs."""
import ast
import hashlib
import json
import logging
from pathlib import Path
import resource
import sys
import time
from types import SimpleNamespace
from typing import Dict, Optional, Union
ROOT=Path(__file__).resolve().parent;SCOPE=ROOT.parent
OUT=Path(sys.argv[1]);START=time.monotonic()
def write(name,value):
    with (OUT/name).open('x') as f:json.dump(value,f,indent=2)
ok=False;error=None
try:
    freeze=json.loads((OUT.parent/'SOURCE_FREEZE.json').read_text())
    source=Path('/mnt/e/githouse/RAP-main/dataset_process/extract_sample_features.py')
    raw=source.read_bytes();assert hashlib.sha256(raw).hexdigest().upper()==freeze['feature_source_sha256']
    tree=ast.parse(raw);nodes=[n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='extract_features']
    assert len(nodes)==1
    compile(ast.Module(body=nodes,type_ignores=[]),str(source),'exec')
    import numpy as np
    import torch
    assert not torch.cuda.is_initialized()
    ns=dict(np=np,torch=torch,Dict=Dict,Optional=Optional,Union=Union,logger=logging.getLogger('FF1_source'))
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(source),'exec'),ns)
    source_call=ns['extract_features'];cases=[];source_calls=0;stub_calls=[0]
    def desc(**kw):
        stub_calls[0]+=1
        return {'desc':kw['kpts'][...,0:1].repeat(1,1,32)}
    def check_result(features,rows):
        a=features.detach().cpu().numpy() if isinstance(features,torch.Tensor) else np.asarray(features)
        if a.shape!=(rows,32) or not np.isfinite(a).all() or not np.any(a!=0):raise ValueError('strict_descriptor_result_rejected')
        return a
    def invoke(obj,points,keypoints=None):
        global source_calls
        source_calls+=1
        return source_call(obj,points,keypoints)
    base=np.array([[1.,0.,2.],[2.,3.,1.],[3.,-1.,4.],[4.,2.,-3.]],dtype=np.float32)
    for tensor in (False,True):
        for provided in (False,True):
            points=torch.from_numpy(base.copy()) if tensor else base.copy()
            kp=(points[[3,1]].clone() if tensor else points[[3,1]].copy()) if provided else None
            obj=SimpleNamespace(device='cpu',des_r=5.,is_aligned_to_global_z=True,model=desc)
            result=invoke(obj,points,kp)
            expected=np.array([4.,2.],dtype=np.float32) if provided else base[:,0]
            f=check_result(result['features'],len(expected))
            assert np.array_equal(f,np.repeat(expected[:,None],32,axis=1))
            assert np.array_equal(points.cpu().numpy() if tensor else points,base)
            if provided: assert result['keypoints'] is kp
            cases.append(dict(case='positive_routing',tensor=tensor,provided_keypoints=provided,passed=True))
    def raised(**kw):
        stub_calls[0]+=1
        raise RuntimeError('synthetic_feature_model_failure')
    obj=SimpleNamespace(device='cpu',des_r=5.,is_aligned_to_global_z=True,model=raised)
    try:invoke(obj,base.copy())
    except AttributeError as caught:
        assert 'dim' in str(caught) and isinstance(caught.__context__,RuntimeError)
        cases.append(dict(case='numpy_model_exception',passed=True,observed='AttributeError in fallback keypoints.dim masks the synthetic original RuntimeError',production_bug_confirmed=True))
    else:raise AssertionError('Expected the source NumPy fallback defect')
    result=invoke(obj,torch.from_numpy(base.copy()))
    assert torch.count_nonzero(result['features'])==0
    try:check_result(result['features'],4)
    except ValueError:pass
    else:raise AssertionError('Zero fallback passed strict boundary')
    cases.append(dict(case='tensor_model_exception',passed=True,observed='Source returns zeros; isolated strict boundary rejects',fallback_is_not_descriptor_success=True))
    for tensor in (False,True):
        empty=torch.empty((0,3)) if tensor else np.empty((0,3))
        result=invoke(obj,empty)
        assert tuple(result['features'].shape)==(0,)
        cases.append(dict(case='empty_input',tensor=tensor,passed=True,observed_shape=[0],not_admitted_as_model_input=True))
    for name,a in [('nonfinite',np.full((4,32),np.nan)),('shape',np.ones((4,31)))]:
        try:check_result(a,4)
        except ValueError:pass
        else:raise AssertionError('Strict guard failed:'+name)
        cases.append(dict(case='strict_reject_'+name,passed=True))
    assert not torch.cuda.is_initialized()
    write('RESULTS.json',dict(passed=True,cases=cases,case_count=len(cases),source_wrapper_calls=source_calls,synthetic_stub_calls=stub_calls[0],actual_feature_model_or_RAP_calls=0,confirmed_numpy_fallback_bug=True,source_file_unchanged=True,strict_boundary_is_uninstalled=True,CUDA_initialized=False))
    ok=True
except BaseException as caught:
    error=repr(caught)
    import traceback
    write('FAILURE.json',dict(error=error,traceback=traceback.format_exc()))
    raise
finally:
    write('worker_exit.json',dict(success=ok,error=error,elapsed_seconds=time.monotonic()-START,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,data_class='CPU_synthetic_feature_wrapper',actual_neural_models=0,raw_point_reads=0,private_reference_reads=0))
print(json.dumps(dict(success=ok,elapsed=time.monotonic()-START)))
