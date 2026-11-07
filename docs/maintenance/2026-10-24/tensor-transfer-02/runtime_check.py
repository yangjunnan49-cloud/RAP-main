"""Inspect only exact owned helper script arguments; never stop processes."""
import json
from pathlib import Path
root='/mnt/e/githouse/RAP-main/docs/maintenance/2026-10-24/tensor-transfer-02/runtime/'
targets={root+'worker.py',root+'lease_runner.py'}
matches=[]
for p in Path('/proc').iterdir():
    if not p.name.isdecimal():continue
    try:args=(p/'cmdline').read_bytes().decode(errors='replace').split('\0')
    except (FileNotFoundError,PermissionError,ProcessLookupError):continue
    if any(a in targets for a in args):matches.append(dict(pid=int(p.name),args=args))
print(json.dumps(dict(exact_scoped_matches=matches,global_process_certification=False)))
assert not matches
