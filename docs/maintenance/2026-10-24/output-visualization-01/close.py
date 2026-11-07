"""Close OV1 without modifying its failed or successful frozen attempts."""
import ast,datetime,hashlib,json
from pathlib import Path
from PIL import Image
root=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
bindings=json.loads((root/'INPUTS.json').read_text())
for row in bindings:
    p=Path(row['path']);assert p.stat().st_size==row['bytes'] and sha(p)==row['sha256']
for run,runtime in [('run01','runtime'),('run02','runtime02')]:
    seal=json.loads((root/run/'SOURCE_FREEZE.json').read_text())
    for name,expected in seal['files'].items():assert sha(root/runtime/name)==expected
    assert sha(root/'INPUTS.json')==seal['inputs_sha256']
    assert sha(root/'PROTOCOL.md')==seal['protocol_sha256']
result=json.loads((root/'run02/plots/RESULTS.json').read_text());assert result['passed']
for row in result['plots']:
    p=root/'run02/plots'/row['file'];assert sha(p)==row['sha256']
    with Image.open(p) as im:
        assert im.size==(1920,1184);im.verify()
assert json.loads((root/'run01/preflight/worker_exit.json').read_text())['success'] is False
assert json.loads((root/'SCOPED_PROCESS_CHECK.json').read_text())['exact_scoped_script_matches']==[]
assert json.loads((root/'WSL_FINAL.json').read_text())['initial_stopped_restored'] is True
for p in root.rglob('*.json'):json.loads(p.read_text(encoding='utf-8'))
for p in root.rglob('*.py'):ast.parse(p.read_text(encoding='utf-8'))
start=datetime.datetime(2026,10,24,7,23,19,tzinfo=datetime.timezone.utc)
elapsed=(datetime.datetime.now(datetime.timezone.utc)-start).total_seconds()
with (root/'COSTS_FINAL.json').open('x') as f:json.dump(dict(status='SEALED_OUTPUT_VISUALIZATION_COMPLETE_WITH_RETAINED_PRELAUNCH_AND_BINDING_FAILURES',
    elapsed_seconds=elapsed,cap_seconds=900,budget_status='PASS' if elapsed<=900 else 'FAIL',
    original_UTC_origin=start.isoformat(),all_attempts_and_repairs_same_origin=True,
    old_caps_reset=False,model_replays=0,plots=2,WSL_initial_stopped_restored=True),f,indent=2)
files={str(p.relative_to(root)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in root.rglob('*') if p.is_file() and p.name!='DELIVERY_SEAL.json'}
assert sum(r['bytes'] for r in files.values())<8*1024*1024
with (root/'DELIVERY_SEAL.json').open('x') as f:json.dump(dict(files=files,visual_QA_pass=True,
    original_failures_preserved=True,all10_input_hashes_unchanged=True),f,indent=2)
print(json.dumps(dict(closed=True,elapsed_seconds=elapsed,files=len(files),output_bytes=sum(r['bytes'] for r in files.values()))))
