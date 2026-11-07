"""Freeze one output-only visualization and reuse the tested OC1 watchdog."""
import datetime,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
OLD=ROOT.parent/'output-contract-01'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def write(p,obj):
    with p.open('x') as f:json.dump(obj,f,indent=2)
rows=json.loads((OLD/'SOURCE_INPUTS.json').read_text())
selected=[r for r in rows if Path(r['path']).name.endswith(('_prepared.npy','_RAP_OUTPUT.json','_RAP_SEAL.json')) or Path(r['path']).name=='RESULTS.json']
assert len(selected)==10 and sum(r['bytes'] for r in selected)<512*1024
for row in selected:
    p=Path(row['path']);assert p.stat().st_size==row['bytes'] and sha(p)==row['sha256']
write(ROOT/'INPUTS.json',selected)
runtime=ROOT/'runtime'
for name in ('identity.py','stop_identity.py'):
    with (runtime/name).open('xb') as f:f.write((OLD/'runtime02'/name).read_bytes())
runner=(OLD/'runtime02/lease_runner.py').read_text()
runner=runner.replace('sealed_output_consistency_only=True','sealed_output_visualization_only=True')
with (runtime/'lease_runner.py').open('x') as f:f.write(runner)
host=(OLD/'runtime02/host.ps1').read_text()
assert host.count('output-contract-01')==2
host=host.replace('output-contract-01/runtime02','output-visualization-01/runtime')
host=host.replace('output-contract-01/','output-visualization-01/')
with (runtime/'host.ps1').open('x') as f:f.write(host)
print(json.dumps(dict(prepared=True,input_files=len(selected),input_bytes=sum(r['bytes'] for r in selected))))
