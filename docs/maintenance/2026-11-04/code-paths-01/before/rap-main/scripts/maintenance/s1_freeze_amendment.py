"""Seal S1's pre-generation import-path repair."""
from __future__ import annotations
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
MAIN=Path(__file__).resolve().parents[2]
BASE=MAIN/'docs/maintenance/2026-09-28/s1-stepcount-dev-01'
files=[BASE/'freeze.json',BASE/'AMENDMENT_01.md',Path(__file__).resolve(),
       MAIN/'scripts/maintenance/s1_stepcount_dev_v2.py',
       MAIN/'scripts/maintenance/validate_s1_stepcount_dev_v2.py']
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):
            h.update(chunk)
    return h.hexdigest()
assert all(p.is_file() for p in files)
with (BASE/'amendment_freeze.json').open('x',encoding='utf-8') as f:
    json.dump({'utc':datetime.now(timezone.utc).isoformat(),
               'files':{str(p):sha(p) for p in files}},f,indent=2)
    f.write('\n')
print('S1 amendment frozen',len(files),'files',flush=True)
