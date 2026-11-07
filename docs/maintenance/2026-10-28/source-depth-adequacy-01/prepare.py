import ast
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent;DAY=ROOT.parent;ER=DAY/'visual-essential-refinement-01'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def save(name,value):
    with (ROOT/name).open('x',encoding='utf-8') as f:json.dump(value,f,indent=2);f.write('\n')


assert not (ROOT/'SOURCE_FREEZE.json').exists()
for name in ('baseline_lib.py','host.ps1'):
    with (ROOT/name).open('xb') as f:f.write((ER/name).read_bytes())
seal=json.loads((ER/'DELIVERY_SEAL.json').read_text())
cf=DAY/'camera-frustum-support-01'
cfseal=json.loads((cf/'DELIVERY_SEAL.json').read_text())
item=next(e for e in cfseal['files'] if e['path']=='INPUT_BINDING.json');assert sha(cf/'INPUT_BINDING.json')==item['sha256']
b=json.loads((cf/'INPUT_BINDING.json').read_text())
inp=json.loads((ER/'PREDICTION_INPUTS.json').read_text())
evidence=[]
for pair in inp['pairs']:
    rel='runtime03/predict/'+pair['key']+'.npz';entry=next(e for e in seal['files'] if e['path']==rel);p=ER/rel
    assert p.stat().st_size==entry['bytes'] and sha(p)==entry['sha256']
    evidence.append({'key':pair['key'],'path':str(p),'bytes':p.stat().st_size,'sha256':entry['sha256']})
save('INPUT_BINDING.json',{'pairs':inp['pairs'],'images':inp['images'],'raw':b['raw'],'calibrations':b['calibrations'],'evidence':evidence,
    'raw_hashes_role':'Prior source-sealed CF1 identity, verify each occurrence at actual read','reference_or_label_paths':[]})
method=json.loads((ER/'METHOD.json').read_text());method.update(scope_origin_utc='2026-10-28T07:27:45+00:00',whole_scope_seconds=1800,dossier_bytes=16777216,stage_seconds={'controls':60,'features':300})
save('METHOD.json',method)
roles={'PROTOCOL.md':'shared','METHOD.json':'shared','baseline_lib.py':'shared','geometry.py':'shared','controls.py':'controls','features.py':'prediction','INPUT_BINDING.json':'prediction','host.ps1':'host','prepare.py':'preparation'}
entries=[]
for name,role in roles.items():
    p=ROOT/name
    if p.suffix=='.py':ast.parse(p.read_text(encoding='utf-8'))
    entries.append({'path':name,'bytes':p.stat().st_size,'sha256':sha(p),'role':role})
save('SOURCE_FREEZE.json',{'files':entries,'no_new_point_numeric_decode_before_freeze':True,'reference_decode_or_new_pose_calls':0})
print('SD1 complete input/source freeze; no raw numeric decode')
