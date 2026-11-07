"""Independent CPU AST/runtime-mode/initial-state artifact validation; no torch import."""
import ast,hashlib
from pathlib import Path
import numpy as np
import native_backward_reproducibility as r

def validate():
    r.verify(); value=r.read(r.BASE/'mode_inventory.json'); inv=value['inventory']
    expected={f'transformer_layers.{layer}.{projection}' for layer in (10,11) for projection in ('global_qkv_proj','global_out_proj')}
    assert set(name for name,flag in inv['modes'].items() if flag)==expected
    assert len(inv['exceptions'])==4 and {z['name'] for z in inv['exceptions']}==expected and inv['mode_mutations']==0
    for z in inv['exceptions']:
        assert z['type_name']=='LowRank' and z['type_module']=='native_output_capability' and z['training'] is True
        assert z['children']==[dict(name='base',type='Linear',training=False)] and z['A_shape'][0]==z['B_shape'][1]==8 and z['B_nonzero']==0
    source=Path(inv['source_path']); assert r.sha(source)==inv['source_sha256']==r.read(r.BASE/'freeze.json')['files'][str(source)]
    cls=next(z for z in ast.parse(source.read_text()).body if isinstance(z,ast.ClassDef) and z.name=='LowRank')
    forward=next(z for z in cls.body if isinstance(z,ast.FunctionDef) and z.name=='forward')
    assert len(forward.body)==1 and isinstance(forward.body[0],ast.Return)
    expression=forward.body[0].value; assert isinstance(expression,ast.BinOp) and isinstance(expression.op,ast.Add)
    left,right=expression.left,expression.right; assert isinstance(left,ast.Call) and ast.unparse(left.func)=='self.base' and [ast.unparse(z) for z in left.args]==['x']
    assert ast.unparse(right.func)=='F.linear' and len(right.args)==2 and ast.unparse(right.args[1])=='self.B'
    nested=right.args[0]; assert ast.unparse(nested.func)=='F.linear' and [ast.unparse(z) for z in nested.args]==['x','self.A']
    assert not any(isinstance(z,(ast.If,ast.IfExp,ast.For,ast.While,ast.Try)) for z in ast.walk(forward))
    assert not any(isinstance(z,ast.Attribute) and z.attr in ('training','dropout','train','eval') for z in ast.walk(forward))
    with np.load(r.OLD/'preflight/P/initial.npz') as old:
        assert set(old.files)==set(value['trainable_hashes']); count=0
        for name in old.files:
            z=old[name]; record=value['trainable_hashes'][name]; assert list(z.shape)==record['shape'] and str(z.dtype)==record['dtype']
            assert hashlib.sha256(z.tobytes()).hexdigest()==record['sha256']; count+=z.size
    assert count==value['trainable_count']==443904 and value['native_forwards']==value['backwards']==value['optimizer_calls']==0
    assert value['strict_checkpoint']['strict'] and value['strict_checkpoint']['weights_only']
    r.save(r.BASE/'mode_validation.json',dict(utc=r.now(),passed=True,module_count=len(inv['modes']),exact_linear_exceptions=4,all_original_modules_eval=True,
        original_initialized_values_byteexact=True,independent_AST_contract=True,mode_changes=0,native_forwards=0,backwards=0,optimizer_calls=0))
    print('Independent mode/source/443904-parameter identity audit passes',flush=True)
