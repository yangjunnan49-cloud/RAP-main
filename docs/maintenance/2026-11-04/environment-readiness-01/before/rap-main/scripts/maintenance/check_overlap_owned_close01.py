"""Read-only exact-scope /proc bookkeeping; no model/array/GT imports."""
import time
START = time.monotonic()
import json
import os
from pathlib import Path
from datetime import datetime, timezone

BASE = Path('/mnt/e/githouse/RAP-main/docs/maintenance/2026-10-21/runtime-overlap-01')
owned = json.loads((BASE / 'supervision/run02/owned_session.json').read_text())
targets = [
    '/mnt/e/githouse/RAP-main/scripts/maintenance/launch_overlap02.py',
    '/mnt/e/githouse/RAP-main/scripts/maintenance/overlap_core02.py',
]
matches = []
unreadable = []
observed = 0
original_controller_alive = False
for folder in Path('/proc').iterdir():
    if not folder.name.isdecimal():
        continue
    try:
        cmdline = (folder / 'cmdline').read_bytes().replace(b'\x00', b' ').decode(errors='replace')
        tail = (folder / 'stat').read_text().rsplit(')', 1)[1].split()
        observed += 1
        start = int(tail[19])
        original = int(folder.name) == owned['controller_pid'] and start == owned['proc_start_ticks']
        original_controller_alive |= original
        if original or any(target in cmdline for target in targets):
            matches.append(dict(pid=int(folder.name), start_ticks=start, process_group=int(tail[2]),
                                session_id=int(tail[3]), cmdline=cmdline, original_controller=original))
    except FileNotFoundError:
        pass  # Process exited during read; no absence certification for other work.
    except (PermissionError, OSError) as exc:
        unreadable.append(dict(pid=folder.name, error=repr(exc)))
result = dict(utc=datetime.now(timezone.utc).isoformat(), passed=not matches and not unreadable,
              original_controller_alive=original_controller_alive, scoped_live_matches=matches,
              process_rows_read=observed, unreadable_rows=unreadable,
              original_owned_identity=owned, read_only=True, no_signal_or_process_control=True,
              no_other_task_absence_claim=True, no_model_array_or_GT_imports=True,
              additional_documentary_wall_seconds=time.monotonic()-START)
with (BASE / 'OWNED_PROCESS_CLOSE_CHECK.json').open('x') as output:
    json.dump(result, output, indent=2, allow_nan=False)
    output.write('\n')
print(json.dumps({key: result[key] for key in ['passed', 'original_controller_alive', 'scoped_live_matches',
                                            'process_rows_read', 'unreadable_rows', 'additional_documentary_wall_seconds']}))
if not result['passed']:
    raise SystemExit(1)
