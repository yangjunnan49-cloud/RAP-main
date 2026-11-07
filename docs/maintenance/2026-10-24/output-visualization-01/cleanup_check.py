"""Read-only exact scoped process reconciliation before restoring WSL state."""
import json
from pathlib import Path
root=Path(__file__).resolve().parent
scripts={str(root/'runtime'/n) for n in ('worker.py','lease_runner.py')}
scripts.update(str(root/'runtime02'/n) for n in ('worker.py','lease_runner.py'))
matches=[]
for p in Path('/proc').iterdir():
    if not p.name.isdecimal():continue
    try:args=(p/'cmdline').read_bytes().split(b'\0')
    except (FileNotFoundError,PermissionError,ProcessLookupError):continue
    if any(s.encode() in args for s in scripts):matches.append(int(p.name))
assert not matches,matches
value=dict(passed=True,exact_scoped_script_matches=matches,processes_killed=0,
    no_global_process_absence_claim=True)
with (root/'SCOPED_PROCESS_CHECK.json').open('x') as f:json.dump(value,f,indent=2)
print(json.dumps(value))
