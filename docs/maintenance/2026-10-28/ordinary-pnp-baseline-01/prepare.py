"""PR1 complete source/input/fixture freeze; no measured PnP or reference decode."""
import ast
import datetime as dt
import hashlib
import json
import math
import random
from pathlib import Path

ROOT=Path(__file__).resolve().parent;DAY=ROOT.parent;ER=DAY/'visual-essential-refinement-01';SD=DAY/'source-depth-adequacy-01'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name,obj):
    with (ROOT/name).open('x',encoding='utf-8') as f:json.dump(obj,f,indent=2,allow_nan=False);f.write('\n')


def require(parent,name):
    entry=next(e for e in json.loads((parent/'DELIVERY_SEAL.json').read_text())['files'] if e['path']==name)
    p=parent/name;assert p.stat().st_size==entry['bytes'] and sha(p)==entry['sha256'];return entry


assert not (ROOT/'SOURCE_FREEZE.json').exists()
origin=dt.datetime(2026,10,28,12,37,44,tzinfo=dt.timezone.utc)
assert (dt.datetime.now(dt.timezone.utc)-origin).total_seconds()<1200
require(ER,'PREDICTION_INPUTS.json');require(ER,'EVALUATION_INPUTS.json');require(SD,'INPUT_BINDING.json')
old=json.loads((ER/'PREDICTION_INPUTS.json').read_text());sdseal=json.loads((SD/'DELIVERY_SEAL.json').read_text())
hypotheses=[]
for pair in old['pairs']:
    name='features/'+pair['key']+'.npz';entry=next(e for e in sdseal['files'] if e['path']==name);p=SD/name
    assert p.stat().st_size==entry['bytes'] and sha(p)==entry['sha256']
    hypotheses.append({'key':pair['key'],'path':str(p),'bytes':p.stat().st_size,'sha256':entry['sha256']})
for entry in old['calibrations']+old['runtime_files']:
    assert Path(entry['path']).stat().st_size==entry['bytes'] and sha(Path(entry['path']))==entry['sha256']
save('PREDICTION_INPUTS.json',{'pairs':old['pairs'],'hypotheses':hypotheses,'calibrations':old['calibrations'],
    'source_depth_delivery_seal_sha256':sha(SD/'DELIVERY_SEAL.json'),'reference_or_label_paths':[]})
save('RUNTIME_BINDING.json',{'runtime_files':old['runtime_files'],'native_version':'5.0.0','distribution':'5.0.0.93','numpy':'2.3.5',
    'installed_PnP_doc_source_sha256':sha(DAY/'vision-runtime-local-01/INSTALLED_API_DOCS.json')})
with (ROOT/'EVALUATION_INPUTS.json').open('xb') as f:f.write((ER/'EVALUATION_INPUTS.json').read_bytes())
with (ROOT/'baseline_lib.py').open('xb') as f:f.write((ER/'baseline_lib.py').read_bytes())
host=(ER/'host.ps1').read_text()
host=host.replace("ValidateSet('controls','features','predict','evaluate','audit')","ValidateSet('controls','predict','evaluate','audit')")
host=host.replace("predict='features'","predict='controls'")
old_parse="if(Test-Path -LiteralPath $taskResultPath){$taskResult=Get-Content -LiteralPath $taskResultPath -Raw | ConvertFrom-Json;$taskChildPeak=$taskResult.child_lifetime_peak_bytes;$taskChildPass=$taskResult.passed}"
new_parse="if(Test-Path -LiteralPath $taskResultPath){try{$taskResult=Get-Content -LiteralPath $taskResultPath -Raw | ConvertFrom-Json;$taskChildPeak=$taskResult.child_lifetime_peak_bytes;$taskChildPass=$taskResult.passed}catch{$taskError='Child RESULT parse failed: '+$_.Exception.Message}}"
assert host.count(old_parse)==1;host=host.replace(old_parse,new_parse)
with (ROOT/'host.ps1').open('x',encoding='utf-8',newline='\n') as f:f.write(host)
method={'minimum_hypotheses':8,'iterations':1000,'reprojection_px':2.,'confidence':.999,'rotation_tolerance':1e-6,'translation_epsilon_m':1e-9,
    'scope_origin_utc':origin.isoformat(),'whole_scope_seconds':3600,'closure_reserve_seconds':180,'dossier_bytes':16777216,
    'stage_seconds':{'controls':60,'predict':180,'evaluate':120,'audit':120},'child_peak_bytes':1073741824,'headroom_bytes':12884901888,'query_seconds':2}
save('METHOD.json',method)
rng=random.Random(902817);xyz=[[rng.uniform(-4,4),rng.uniform(-2,2),rng.uniform(8,24)] for _ in range(80)]
angle=math.radians(7);rotation=[[math.cos(angle),0.,math.sin(angle)],[0.,1.,0.],[-math.sin(angle),0.,math.cos(angle)]]
translation=[1.2,.15,.3];k=[[700.,0.,620.],[0.,700.,180.],[0.,0.,1.]]
xy=[]
for point in xyz:
    camera=[sum(rotation[i][j]*point[j] for j in range(3))+translation[i] for i in range(3)]
    image=[sum(k[i][j]*camera[j] for j in range(3)) for i in range(3)];xy.append([image[0]/image[2],image[1]/image[2]])
save('SYNTHETIC_FIXTURE.json',{'xyz':xyz,'xy':xy,'R':rotation,'t':translation,'K':k,'role':'Known artificial control oracle, not dataset/reference'})
roles={'PROTOCOL.md':'shared','baseline_lib.py':'shared','pnp_lib.py':'shared','METHOD.json':'shared','RUNTIME_BINDING.json':'shared',
    'controls.py':'controls','SYNTHETIC_FIXTURE.json':'controls','predict.py':'prediction','PREDICTION_INPUTS.json':'prediction',
    'evaluate.py':'evaluation','EVALUATION_INPUTS.json':'evaluation','audit.py':'audit','host.ps1':'host','prepare.py':'preparation'}
entries=[]
for name,role in roles.items():
    path=ROOT/name
    if path.suffix=='.py':ast.parse(path.read_text(encoding='utf-8'),filename=name)
    entries.append({'path':name,'bytes':path.stat().st_size,'sha256':sha(path),'role':role})
save('SOURCE_FREEZE.json',{'utc':dt.datetime.now(dt.timezone.utc).isoformat(),'files':entries,
    'measured_PnP_calls_before_freeze':0,'reference_pose_decodes_before_freeze':0,'complete_pairs':200,
    'all_prediction_evaluation_audit_implementation_included':True})
print('PR1 complete implementation/fixture/input/resource freeze; no measured pose calls')
