"""Interrupt only the exact owned P0 controller group at recorded owner/quota stop."""
import os,sys,json,hashlib,signal,time
from pathlib import Path
from datetime import datetime,timezone
BASE=Path('/mnt/e/githouse/RAP-main/docs/maintenance/2026-10-21/runtime-overlap-01')
def read(p):return json.loads(p.read_text())
boundary=read(BASE/'ACCOUNT_STOP.json');assert boundary['primary_used_percent']>=100 or boundary['ordinaryUsageAllowed'] is False
owned=read(BASE/'supervision/run02/owned_session.json');pid=owned['controller_pid'];proc=Path(f'/proc/{pid}')
result=dict(utc=datetime.now(timezone.utc).isoformat(),pid=pid,requested_signal='SIGINT',no_other_processes=True)
if not proc.exists():result['already_exited']=True
else:
    stat=(proc/'stat').read_text();ticks=int(stat.rsplit(')',1)[1].split()[19]);cmd=(proc/'cmdline').read_bytes().decode().replace('\0',' ')
    assert ticks==owned['proc_start_ticks'] and cmd==owned['controller_cmdline']
    assert os.getpgid(pid)==owned['process_group']==pid and os.getsid(pid)==owned['session_id']==pid
    source=Path('/mnt/e/githouse/RAP-main/scripts/maintenance/launch_overlap02.py')
    assert hashlib.sha256(source.read_bytes()).hexdigest()==owned['source_sha256']
    os.killpg(pid,signal.SIGINT);result.update(signal_sent=True,identity_checks_passed=True,cmdline=cmd,proc_start_ticks=ticks)
    for _ in range(50):
        if not proc.exists():break
        time.sleep(.1)
    result['controller_proc_exists_after_wait']=proc.exists()
with (BASE/'OWNED_STOP_RECEIPT.json').open('x') as f:json.dump(result,f,indent=2)
print(json.dumps(result),flush=True)
