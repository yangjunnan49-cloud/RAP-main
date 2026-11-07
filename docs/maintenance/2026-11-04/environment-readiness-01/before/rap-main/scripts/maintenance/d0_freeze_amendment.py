"""Seal the pre-label D0 numerical-reference amendment."""
from __future__ import annotations
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

MAIN=Path(__file__).resolve().parents[2]
BASE=MAIN/'docs/maintenance/2026-09-28/d0-flow-trajectory-01'
files=[BASE/'freeze.json',BASE/'AMENDMENT_01.md',Path(__file__).resolve(),
       MAIN/'scripts/maintenance/d0_flow_trajectory_v2.py',
       MAIN/'scripts/maintenance/validate_d0_flow_trajectory_v2.py',
       MAIN/'scripts/maintenance/d0_gate_diagnose.py']
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for part in iter(lambda:f.read(1024*1024),b''):
            h.update(part)
    return h.hexdigest()
assert all(p.is_file() for p in files)
with (BASE/'amendment_freeze.json').open('x',encoding='utf-8') as f:
    json.dump({'utc':datetime.now(timezone.utc).isoformat(),
               'files':{str(p):sha(p) for p in files}},f,indent=2)
    f.write('\n')
print('D0 amendment frozen',len(files),'files',flush=True)
