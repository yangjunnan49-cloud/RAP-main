"""Serialization/output-routing only; retain all original synthetic conditions."""
import ast
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def save(name,obj):
    with (ROOT/name).open('x',encoding='utf-8') as f:json.dump(obj,f,indent=2);f.write('\n')


assert not (ROOT/'BOOL_CORRECTION_FREEZE.json').exists()
for e in json.loads((ROOT/'SOURCE_FREEZE.json').read_text())['files']:
    assert sha(ROOT/e['path'])==e['sha256']
source=(ROOT/'controls.py').read_text()
changed=source.replace("OUT = lib.ROOT/'controls'","OUT = lib.ROOT/'controls_runtime02'").replace("'controls':checks","'controls':[bool(value) for value in checks]")
assert changed!=source
assert changed.replace("OUT = lib.ROOT/'controls_runtime02'","OUT = lib.ROOT/'controls'").replace("'controls':[bool(value) for value in checks]","'controls':checks")==source
with (ROOT/'controls_runtime02.py').open('x',encoding='utf-8',newline='\n') as f:f.write(changed)
ast.parse(changed)
host=(ROOT/'host.ps1').read_text()
host=host.replace("$taskOut=Join-Path $taskRoot $Stage","$taskOut=Join-Path $taskRoot $(if($Stage -eq 'controls'){'controls_runtime02'}else{$Stage})")
host=host.replace("($Stage+'.PREFLIGHT.json')","($(if($Stage -eq 'controls'){'controls_runtime02'}else{$Stage})+'.PREFLIGHT.json')")
host=host.replace("$taskOwnHash=($taskFreeze.files | Where-Object path -EQ 'host.ps1').sha256","$taskOwnHash=(Get-Content -LiteralPath (Join-Path $taskRoot 'BOOL_CORRECTION_FREEZE.json') -Raw|ConvertFrom-Json).host_sha256")
host=host.replace("features='controls'","features='controls_runtime02'")
host=host.replace("$taskTimer=[Diagnostics.Stopwatch]::StartNew()","$taskLimit=if($Stage -eq 'controls'){60-1.1237349}else{[double]$taskMethod.stage_seconds.$Stage}\n$taskTimer=[Diagnostics.Stopwatch]::StartNew()")
host=host.replace("(Join-Path $taskRoot ($Stage+'.py'))","(Join-Path $taskRoot $(if($Stage -eq 'controls'){'controls_runtime02.py'}else{$Stage+'.py'}))")
host=host.replace('$taskMethod.stage_seconds.$Stage','$taskLimit')
# Correct only the new limit initializer, not the existing source cap.
host=host.replace("else{[double]$taskLimit}","else{[double]$taskMethod.stage_seconds.$Stage}")
header="\n$taskExtra=Get-Content -LiteralPath (Join-Path $taskRoot 'BOOL_CORRECTION_FREEZE.json') -Raw|ConvertFrom-Json\nforeach($taskExtraFile in $taskExtra.files){if((Get-FileHash -LiteralPath (Join-Path $taskRoot $taskExtraFile.path) -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskExtraFile.sha256){throw 'Serialization correction hash'}}\n"
host=host.replace("$taskPrior=@",header+"$taskPrior=@",1)
with (ROOT/'host_bool_correction.ps1').open('x',encoding='utf-8',newline='\n') as f:f.write(host)
save('BOOL_CORRECTION_PROOF.json',{'original_controls_sha256':sha(ROOT/'controls.py'),'new_controls_sha256':sha(ROOT/'controls_runtime02.py'),
    'reverse_transform_recovers_exact_source':True,'change':'Serialize bool(value) only and new output directory; all original conditions/math identical',
    'failed_outer_host_wall_seconds_charged_to_original60s':1.1237349,'feature_precheck_outer_seconds':0.3570315,
    'original_child_exit_and_final_host_receipt':'UNKNOWN: host WaitForExit executed before ConvertFrom-Json rejected truncated NumPy-bool output; preserve partial RESULT/stderr/OWNED_PROCESS',
    'real_data_worker_precheck_blocked_before_launch':True})
names=['prepare_bool_correction.py','controls_runtime02.py','host_bool_correction.ps1','BOOL_CORRECTION_PROOF.json']
save('BOOL_CORRECTION_FREEZE.json',{'host_sha256':sha(ROOT/'host_bool_correction.ps1'),
    'files':[{'path':n,'sha256':sha(ROOT/n),'bytes':(ROOT/n).stat().st_size} for n in names],
    'original_scope_and_caps_unchanged':True})
print('Bool serialization/output correction frozen; no numerical method change')
