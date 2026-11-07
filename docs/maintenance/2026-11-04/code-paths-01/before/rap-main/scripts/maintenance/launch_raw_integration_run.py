"""Current-turn owned-session controller; no scheduling or automatic resume."""
import time
START=time.monotonic()
import sys,os,json,subprocess,signal,hashlib,traceback
from pathlib import Path
import raw_system_integration02 as d
def save(p,x):return d.save(p,x)
def run():
    left=d.CAP-d.used();assert left>1;ok=False;error=None;p=None
    try:
        d.verify();save(d.BASE/'LAUNCH_BINDING.json',dict(utc=d.now(),files={str(p):d.sha(p) for p in [Path(__file__),Path(d.__file__),d.BASE/'PROTOCOL.md',d.BASE/'VARIANT02_FREEZE.json']},
            original_scope_seconds_remaining=left,owned_session_only=True,no_scheduler=True,no_automatic_reset_resume=True))
        p=subprocess.Popen([sys.executable,'-u','-B',__file__,'--controller'],start_new_session=True)
        proc=Path(f'/proc/{p.pid}');stat=(proc/'stat').read_text();start_ticks=int(stat.rsplit(')',1)[1].split()[19])
        save(d.SUP/'run/owned_session.json',dict(utc=d.now(),controller_pid=p.pid,process_group=os.getpgid(p.pid),session_id=os.getsid(p.pid),proc_start_ticks=start_ticks,
            parent_wrapper_pid=os.getpid(),controller_cmdline=(proc/'cmdline').read_bytes().decode().replace('\x00',' '),source_sha256=d.sha(__file__)))
        code=p.wait(timeout=left-1);assert code==0;ok=True
    except BaseException as e:
        error=repr(e);traceback.print_exc()
        if p is not None and p.poll() is None:
            assert os.getpgid(p.pid)==p.pid and os.getsid(p.pid)==p.pid
            os.killpg(p.pid,signal.SIGINT)
            try:p.wait(timeout=5)
            except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGTERM);p.wait(timeout=5)
    finally:
        save(d.SUP/'run/wrapper_exit.json',dict(utc=d.now(),success=ok,error=error,wall_seconds=time.monotonic()-START,
            controller_returncode=p.returncode if p is not None else None,clock_overlaps_controller_and_Windows=True))
    if not ok:sys.exit(1)
if __name__=='__main__':
    if '--controller' in sys.argv:d.run('run',False)
    else:assert sys.argv[1]=='run';run()
