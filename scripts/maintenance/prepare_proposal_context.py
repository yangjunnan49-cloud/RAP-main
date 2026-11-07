"""PG0 data-only orchestration; unchanged SLAM data algorithms, no RAP calls."""
import hashlib
import json
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

MAIN=Path('/mnt/e/githouse/RAP-main')
SLAM=Path('/mnt/e/githouse/RAP-SLAM')
OUT=MAIN/'docs/maintenance/2026-09-15/proposal-context-01'
DATA=OUT/'data'
sys.path[:0]=[str(SLAM),str(SLAM/'scripts')]
import hl2_data_bridge as bridge
import validate_hl_v2_data as validator

def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
    with p.open('x') as f:json.dump(v,f,indent=2,allow_nan=False)
def pairhash(s,i,j):return hashlib.sha256(f'PG-V1|kitti|{s}|{i}|{j}'.encode()).hexdigest()

start=time.monotonic()
DATA.mkdir(exist_ok=False)
(DATA/'INCOMPLETE').write_text('Data eligibility pending\n')
parents={}
for folder in [MAIN/'docs/maintenance/2026-09-14/hl-v2/pilot-01',
               MAIN/'docs/maintenance/2026-09-14/support-control-02']:
    m=read(folder/'artifact_hashes.json')
    assert all(sha(folder/p)==h for p,h in m.items())
    parents[str(folder)]=dict(files=len(m),manifest_sha256=sha(folder/'artifact_hashes.json'))
sources=[Path(__file__),SLAM/'scripts/hl2_data_bridge.py',SLAM/'scripts/validate_hl_v2_data.py',
         SLAM/'scripts/hl1_cohort_audit.py',SLAM/'scripts/hl0_preflight.py',
         SLAM/'rap_slam/odometry.py',SLAM/'rap_slam/rap_backend.py']
source_hash={str(p):sha(p) for p in sources}
save(DATA/'declaration.json',dict(frozen_utc=datetime.now(timezone.utc).isoformat(),
     protocol_sha256=sha(OUT/'PROTOCOL.md'),parents=parents,source_hashes=source_hash,new_outcomes=0))
bridge.OUT=DATA
bridge.pairhash=pairhash
validator.OUT=DATA
validator.pairhash=pairhash
bridge.run('09')
validator.validate('09')
assert time.monotonic()-start<3600
assert sum(p.stat().st_size for p in DATA.rglob('*') if p.is_file())<10*2**30
assert all(sha(Path(p))==h for p,h in source_hash.items())
assert sha(OUT/'PROTOCOL.md')==read(DATA/'declaration.json')['protocol_sha256']
summary=read(DATA/'09/adequacy.json')
old=MAIN/'docs/maintenance/2026-09-14/hl-v2/data-expansion-01'
for role,source in [('discovery',old/'discovery_inputs.json'),('confirmation',DATA/'09/selected_inputs.json')]:
    save(DATA/f'{role}_inputs.json',read(source))
save(DATA/'discovery_evaluator.json',read(old/'discovery_evaluator.json'))
save(DATA/'confirmation_evaluator.json',read(DATA/'09/selected_evaluator.json'))
save(DATA/'cohort_freeze.json',dict(frozen_utc=datetime.now(timezone.utc).isoformat(),
     protocol='PG-V1',discovery='exact observed HL-V2 KITTI00 membership',confirmation=summary,
     input_hashes={p.name:sha(p) for p in DATA.glob('*_inputs.json')},
     evaluator_hashes={p.name:sha(p) for p in DATA.glob('*_evaluator.json')},new_outcomes=0))
save(DATA/'decision.json',dict(decision='READY_FOR_PREFLIGHT' if summary['adequate'] else 'INCONCLUSIVE_DATA',
     confirmation=summary,new_generations=0,training=False,wall_s=time.monotonic()-start))
(DATA/'09/INCOMPLETE').unlink()
(DATA/'INCOMPLETE').unlink()
save(DATA/'artifact_hashes.json',{str(p.relative_to(DATA)):sha(p) for p in sorted(DATA.rglob('*')) if p.is_file()})
print('PG0:', 'READY_FOR_PREFLIGHT' if summary['adequate'] else 'INCONCLUSIVE_DATA',flush=True)
