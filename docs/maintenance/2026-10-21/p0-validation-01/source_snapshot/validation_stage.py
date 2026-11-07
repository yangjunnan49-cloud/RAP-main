"""Owned validation process with live Linux timing and host nonce guard."""
import os,sys,time,json,hashlib,threading,signal,traceback,resource,uuid
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parent
OUT=ROOT.parents[1]/'outputs/overlap_validation_20261021'
STAGE=sys.argv[1];LOG=OUT/'supervision'/STAGE;LOG.mkdir(parents=True,exist_ok=True)
os.setsid();PID=os.getpid();TICK=Path('/proc/self/stat').read_text().rsplit(')',1)[1].split()[19]
def atomic(p,obj):
    tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(obj,indent=2));os.replace(tmp,p)
started=time.monotonic();initial=json.loads((ROOT/'live_host.json').read_text())['elapsed']
atomic(ROOT/'local_clock.json',dict(start_monotonic=started,initial_global_elapsed=initial))
atomic(LOG/'owned_session.json',dict(pid=PID,pgid=os.getpgid(PID),start_ticks=TICK,script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),stage=STAGE))
finished=threading.Event()
def heartbeat():
    while not finished.is_set():
        atomic(LOG/'linux_heartbeat.json',dict(monotonic=time.monotonic(),global_elapsed=initial+time.monotonic()-started,pid=PID))
        finished.wait(.2)
threading.Thread(target=heartbeat,daemon=True).start()
ok=False;error=None
try:
    nonce=uuid.uuid4().hex;begin=time.monotonic();atomic(LOG/'memory_request.json',dict(nonce=nonce))
    response=LOG/'memory_response.json'
    while not response.exists() and time.monotonic()-begin<2:time.sleep(.01)
    received=json.loads(response.read_text());assert received['nonce']==nonce and time.monotonic()-begin<=2 and received['headroom_bytes']>=12*2**30
    atomic(LOG/'memory_guard_pass.json',dict(roundtrip=time.monotonic()-begin,**received))
    remaining=1200-60-initial;assert remaining>1
    signal.signal(signal.SIGALRM,lambda a,b:(_ for _ in ()).throw(TimeoutError('new validation deadline')));signal.alarm(int(remaining))
    if STAGE=='probe':
        while True:time.sleep(.1)
    elif STAGE=='synthetic':
        import synthetic_validation
        synthetic_validation.run()
    else:
        import validation_core as c
        module=__import__('audit_adapted' if STAGE=='audit_bindings' else 'assess_adapted')
        c.verify();module.run();c.cap()
    ok=True
except BaseException as e:error=repr(e);traceback.print_exc()
finally:
    signal.alarm(0);finished.set()
    atomic(LOG/'process_exit.json',dict(success=ok,error=error,wall_seconds=time.monotonic()-started,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,utc=datetime.now(timezone.utc).isoformat()))
sys.exit(0 if ok else 1)
