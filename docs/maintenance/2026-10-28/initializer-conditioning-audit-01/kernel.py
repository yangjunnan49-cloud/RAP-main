"""Execute the exact isolated public normalization method, without backend imports."""
import ast
import hashlib
from pathlib import Path


def load(np,root,binding):
    source=(root/'rap_backend.snapshot.py').read_bytes()
    assert hashlib.sha256(source).hexdigest()==binding['backend_sha256']
    tree=ast.parse(source.decode('utf-8'))
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='RAPBackend')
    method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='_normalize_parts')
    assert hashlib.sha256(ast.dump(method,include_attributes=False).encode()).hexdigest()==binding['normalize_AST_sha256']
    holder=ast.ClassDef(name='SourceKernel',bases=[],keywords=[],body=[method],decorator_list=[])
    if 'type_params' in ast.ClassDef._fields:holder.type_params=[]
    isolated=ast.Module(body=[holder],type_ignores=[])
    ast.fix_missing_locations(isolated);namespace={'np':np}
    exec(compile(isolated,'<source-bound RAPBackend._normalize_parts>','exec'),namespace)
    return namespace['SourceKernel']._normalize_parts


def compare(np,normalize,parts,delta,quantized):
    base,s0,c0,counts0,anchor0=normalize(parts)
    shifted=[parts[0],parts[1].astype(np.float64)+delta]
    if quantized:shifted[1]=shifted[1].astype(np.float32)
    changed,s1,c1,counts1,anchor1=normalize(shifted)
    assert np.array_equal(counts0,counts1) and anchor0==anchor1
    original=np.concatenate(parts).astype(np.float64);moved=np.concatenate(shifted).astype(np.float64)
    offsets=np.r_[0,np.cumsum(counts0)];expected0=np.empty_like(original);expected1=np.empty_like(moved)
    center_error=0.;closed_error=0.
    for i in range(2):
        a,b=int(offsets[i]),int(offsets[i+1]);mean0=original[a:b].mean(axis=0);mean1=moved[a:b].mean(axis=0)
        expected0[a:b]=(original[a:b]-mean0)/s0;expected1[a:b]=(moved[a:b]-mean1)/s1
        center_error=max(center_error,float(np.max(np.abs(c0[i]-mean0))),float(np.max(np.abs(c1[i]-mean1))))
    closed_error=max(float(np.max(np.abs(base.astype(float)-expected0))),float(np.max(np.abs(changed.astype(float)-expected1))))
    magnitude=max(1.,float(np.max(np.abs(original))),float(np.max(np.abs(moved))),float(np.max(np.abs(delta))))
    cond_magnitude=max(1.,float(np.max(np.abs(base))))
    budget=256*float(np.finfo(np.float32).eps)*(1+magnitude)/s0*cond_magnitude
    difference=float(np.max(np.abs(base.astype(float)-changed.astype(float))))
    assert difference<=budget and closed_error<=budget and center_error<=1e-9*magnitude
    return {'primary_part':int(anchor0),'counts':counts0.tolist(),'base_scale':s0,'shifted_scale':s1,
        'scale_difference':abs(s1-s0),'source_delta_raw_m':delta.tolist(),'quantized_source_float32':bool(quantized),
        'condition_byte_equal':bool(np.array_equal(base,changed)),'max_condition_difference':difference,
        'independent_closed_form_error':closed_error,'max_center_error':center_error,'representation_budget':budget},(base,changed,c0,c1,s0,s1,shifted)
