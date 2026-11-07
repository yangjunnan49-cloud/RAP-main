"""Literal independent terminal/stale decision oracles; no live-state mutation."""
import json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT));START=time.monotonic()
from ledger_policy import decide
def rec(status,t):return dict(classification=dict(status=status),following_clock=dict(current_time=t))
a=rec('ACTIVE','2026-10-23 09:37:41 UTC');b=rec('ACTIVE','2026-10-23 09:49:44 UTC');d=rec('ACCOUNT_ORDINARY_USAGE_DISABLED','2026-10-23 09:30:00 UTC')
cases=[('forward_active',a,b,False,'WRITE_ACTIVE'),('stale_active',b,a,False,'REJECT_STALE_ACTIVE'),('marker_prevents_reactivation',a,b,True,'RETAIN_TERMINAL'),('terminal_pointer_prevents_reactivation',d,b,False,'RETAIN_TERMINAL'),('disabled_evidence_clock_priority',b,d,False,'WRITE_DISABLED'),('changed_window_stop',b,rec('WINDOW_CHANGED_STOP','2026-10-23 09:50:00 UTC'),False,'WRITE_OBSERVATION_STOP'),('invalid_active_clock',b,rec('ACTIVE','unknown'),False,'WRITE_CLOCK_UNCERTAINTY_STOP')]
rows=[]
for name,previous,new,terminal,expected in cases:
    assert decide(previous,new,terminal)==expected,name
    rows.append(dict(case=name,expected=expected,passed=True))
with (ROOT/'RESULTS.json').open('x') as f:json.dump(dict(passed=True,controls=rows,count=len(rows),actual_account_state_mutations=0,elapsed_seconds=time.monotonic()-START),f,indent=2)
print(json.dumps(dict(passed=True,count=len(rows))))
