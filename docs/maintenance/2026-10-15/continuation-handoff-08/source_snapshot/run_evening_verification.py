"""Separate finite bookkeeping enclosure; does not amend research caps."""
import time
START=time.monotonic()
import ast,json,resource,runpy,signal,sys
from pathlib import Path
root=Path(__file__).resolve().parents[2];base=root/'docs/maintenance/2026-10-15/continuation-handoff-08';sup=base/'supervision'/sys.argv[1]
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('verification300s')));signal.alarm(300)
ok=False;err=None
try:
    target=Path(__file__).with_name('final_evening_identity.py');ast.parse(target.read_text());runpy.run_path(str(target),run_name='__main__')
    assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024<=128*2**20 and time.monotonic()-START<=300
    assert sum(p.stat().st_size for p in base.rglob('*') if p.is_file())<16*2**20;ok=True
except BaseException as ex:err=repr(ex);raise
finally:
    with (sup/'child_exit.json').open('x') as out:json.dump(dict(success=ok,error=err,wall_seconds=time.monotonic()-START,peak_Linux_process_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,model_pose_network_calls=0,setup_and_observer_lifetime_RSS='UNKNOWN'),out,indent=2)
