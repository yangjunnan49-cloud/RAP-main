"""Record only an actually observed final quota boundary, never infer completion."""
import json
import sys
from pathlib import Path
import physical_source_role_feasibility as s

ROOT=s.ROOT
DAY=ROOT/'docs/maintenance/2026-10-15'
BASE=DAY/'continuation-handoff-06'
record=json.loads(sys.argv[1])
assert record['primary_used_percent']>=100 or record['ordinaryUsageAllowed'] is False
record.update(scientific_goal_complete=False,automatic_quota_reset_resume=False,
    no_new_scientific_or_network_payload_after_four_closures=True,
    stop_kind='ACCOUNT_ALLOWANCE_BOUNDARY_NOT_SCIENTIFIC_COMPLETION')
with (BASE/'ACCOUNT_STOP.json').open('x',encoding='utf-8') as out:json.dump(record,out,indent=2);out.write('\n')
snap=BASE/'account_boundary_snapshot';snap.mkdir()
paths=[BASE/'ACCOUNT_STOP.json',BASE/'PREPARATORY_ACCOUNT.json',BASE/'DELIVERY_SEAL.json',BASE/'FINAL_VERIFICATION_SEAL.json']
for q in (Path(__file__),ROOT/'AGENTS.md',DAY/'PHASE_RECORD.md'):
    target=snap/q.name
    with target.open('xb') as out:out.write(q.read_bytes())
    paths.append(target)
rows=[dict(path=str(q.relative_to(BASE)),bytes=q.stat().st_size,sha256=s.sha(q)) for q in paths]
with (BASE/'ACCOUNT_STOP_SEAL.json').open('x',encoding='utf-8') as out:json.dump(dict(files=rows),out,indent=2);out.write('\n')
print(json.dumps(dict(primary_used_percent=record['primary_used_percent'],ordinaryUsageAllowed=record['ordinaryUsageAllowed'],account_seal_entries=len(rows))),flush=True)
