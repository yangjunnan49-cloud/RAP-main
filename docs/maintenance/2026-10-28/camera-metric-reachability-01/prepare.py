import ast
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent;DAY=ROOT.parent;PR=DAY/'ordinary-pnp-baseline-01'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def save(name,obj):
    with (ROOT/name).open('x',encoding='utf-8') as f:json.dump(obj,f,indent=2);f.write('\n')


assert not (ROOT/'SOURCE_FREEZE.json').exists()
bindings={}
for name,parent,rel in [('PR1',PR,'evaluate/ROWS.json'),('ER1',DAY/'visual-essential-refinement-01','runtime03/evaluate/ROWS.json'),('VR1',DAY/'visual-baseline-reachability-01','controls/ROWS.json')]:
    seal=json.loads((parent/'DELIVERY_SEAL.json').read_text());e=next(e for e in seal['files'] if e['path']==rel);p=parent/rel
    assert p.stat().st_size==e['bytes'] and sha(p)==e['sha256'];bindings[name]={'path':str(p),'sha256':e['sha256'],'bytes':e['bytes']}
save('INPUT_BINDING.json',bindings)
for name in ('baseline_lib.py','host.ps1'):
    with (ROOT/name).open('xb') as f:f.write((PR/name).read_bytes())
method=json.loads((PR/'METHOD.json').read_text());method.update(scope_origin_utc='2026-10-28T12:55:44+00:00',whole_scope_seconds=900,stage_seconds={'controls':30})
save('METHOD.json',method)
roles={'PROTOCOL.md':'shared','baseline_lib.py':'shared','host.ps1':'host','METHOD.json':'shared','controls.py':'controls','INPUT_BINDING.json':'controls','prepare.py':'preparation'}
entries=[]
for name,role in roles.items():
    p=ROOT/name
    if p.suffix=='.py':ast.parse(p.read_text(encoding='utf-8'))
    entries.append({'path':name,'sha256':sha(p),'bytes':p.stat().st_size,'role':role})
save('SOURCE_FREEZE.json',{'files':entries,'no_join_outcome_read_before_freeze':True})
print('MR1 complete source/input freeze')
