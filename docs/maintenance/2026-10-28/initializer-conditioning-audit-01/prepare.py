import ast
import datetime as dt
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent;DAY=ROOT.parent;PR=DAY/'ordinary-pnp-baseline-01';CF=DAY/'camera-frustum-support-01'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def save(name,obj):
    with (ROOT/name).open('x',encoding='utf-8') as f:json.dump(obj,f,indent=2);f.write('\n')


assert not (ROOT/'SOURCE_FREEZE.json').exists()
assert (dt.datetime.now(dt.timezone.utc)-dt.datetime(2026,10,28,13,6,4,tzinfo=dt.timezone.utc)).total_seconds()<1800
for name in ('baseline_lib.py','host.ps1'):
    with (ROOT/name).open('xb') as f:f.write((PR/name).read_bytes())
host=(ROOT/'host.ps1').read_text();host=host.replace("ValidateSet('controls','predict','evaluate','audit')","ValidateSet('controls','features')")
with (ROOT/'host.ps1').open('w',encoding='utf-8',newline='\n') as f:f.write(host)
source=(ROOT/'rap_backend.snapshot.py').read_text(encoding='utf-8');tree=ast.parse(source)
cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='RAPBackend')
normal=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='_normalize_parts')
save('SOURCE_BINDING.json',{'backend_original_path':'E:/githouse/RAP-SLAM/rap_slam/rap_backend.py','backend_sha256':sha(ROOT/'rap_backend.snapshot.py'),
    'normalize_AST_sha256':hashlib.sha256(ast.dump(normal,include_attributes=False).encode()).hexdigest(),
    'modeling_original_path':'E:/githouse/RAP-main/rectified_point_flow/modeling.py','modeling_sha256':sha(ROOT/'modeling.snapshot.py'),
    'method_only_execution_no_backend_import':True,'runtime':'Isolated WindowsNumPy2.3.5, not a nativeWSL/model replay'})
seal=json.loads((PR/'DELIVERY_SEAL.json').read_text());entry=next(e for e in seal['files'] if e['path']=='predict/PREDICTIONS.json')
p=PR/'predict/PREDICTIONS.json';assert sha(p)==entry['sha256']
cfseal=json.loads((CF/'DELIVERY_SEAL.json').read_text());cfe=next(e for e in cfseal['files'] if e['path']=='INPUT_BINDING.json');assert sha(CF/'INPUT_BINDING.json')==cfe['sha256']
cf=json.loads((CF/'INPUT_BINDING.json').read_text())
save('INPUT_BINDING.json',{'predictions':{'path':str(p),'sha256':entry['sha256'],'bytes':entry['bytes']},
    'raw':cf['raw'],'calibrations':cf['calibrations'],'reference_or_evaluation_paths':[],
    'selection':'All200 records; process all17 statusPOSE initializers, no metric/error threshold selection'})
method=json.loads((PR/'METHOD.json').read_text());method.update(scope_origin_utc='2026-10-28T13:06:04+00:00',whole_scope_seconds=2400,stage_seconds={'controls':60,'features':180})
save('METHOD.json',method)
roles={'PROTOCOL.md':'shared','baseline_lib.py':'shared','kernel.py':'shared','rap_backend.snapshot.py':'shared','modeling.snapshot.py':'shared',
    'SOURCE_BINDING.json':'shared','METHOD.json':'shared','controls.py':'controls','features.py':'prediction','INPUT_BINDING.json':'prediction',
    'host.ps1':'host','prepare.py':'preparation'}
entries=[]
for name,role in roles.items():
    p=ROOT/name
    if p.suffix=='.py':ast.parse(p.read_text(encoding='utf-8'))
    entries.append({'path':name,'bytes':p.stat().st_size,'sha256':sha(p),'role':role})
save('SOURCE_FREEZE.json',{'files':entries,'source_kernel_AST_unchanged':True,'new_raw_point_numeric_decodes_before_freeze':0,'model_calls':0})
print('PT1 actual-backend source/method/input freeze complete')
