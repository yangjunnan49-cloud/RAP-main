"""Reuse the existing supervised runtime with an independent environment-only worker."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[3]
old=REPO/'docs/maintenance/2026-10-24/real-interface-02/runtime'
runtime=ROOT/'runtime'
for n in ('identity.py','stop_identity.py'):
    with (runtime/n).open('xb') as f:f.write((old/n).read_bytes())
runner=(old/'lease_runner.py').read_text(encoding='utf-8')
runner=runner.replace('scope_cap = 1320.0','scope_cap = 480.0')
runner=runner.replace('synthetic=False, real_public_operability=True, payload_counters_in_worker_exit=True','synthetic=True, environment_check_only=True, actual_model_or_adapter_training=False')
with (runtime/'lease_runner.py').open('x') as f:f.write(runner)
host=(old/'host.ps1').read_text(encoding='utf-8')
host=host.replace('2026-10-24/real-interface-02','2026-10-25/adapter-readiness-01').replace('-ge 1320','-ge 480').replace('$hostCap=180.;$linuxCap=180.','$hostCap=60.;$linuxCap=60.')
with (runtime/'host.ps1').open('x') as f:f.write(host)
files={p.name:hashlib.sha256(p.read_bytes()).hexdigest().upper() for p in runtime.iterdir()}
print(json.dumps(dict(prepared=True,runtime_files=len(files))))
