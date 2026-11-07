"""Synthetic lease client: immutable nonce files, local deadlines, self-stop."""
import os,sys,json,time,uuid,signal,hashlib,resource,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parent
OUT=ROOT.parents[1]/'outputs/guard_hardening_20261021/run02'
case=sys.argv[1];cap=float(sys.argv[2]);duration=float(sys.argv[3]);folder=OUT/case
if os.getpgrp()!=os.getpid():os.setsid()
pid=os.getpid();start=time.monotonic();last=None;count=0;ok=False;error=None;host_elapsed=0.;last_reply_at=start;stop_at=None
def write(name,obj):
    target=folder/name;temp=target.with_suffix('.tmp')
    with temp.open('x') as f:json.dump(obj,f,indent=2)
    os.rename(temp,target)  # Every final name is unique and immutable.
def interrupted(signum,frame):raise RuntimeError('owned_stop_signal')
signal.signal(signal.SIGTERM,interrupted)
write('owned.json',dict(pid=pid,pgid=os.getpgid(pid),start_ticks=Path('/proc/self/stat').read_text().rsplit(')',1)[1].split()[19],script=str(Path(__file__).resolve()),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),case=case))
try:
    while time.monotonic()-start<duration:
        elapsed=time.monotonic()-start
        if max(elapsed,host_elapsed+time.monotonic()-last_reply_at)>=cap:raise RuntimeError('linux_or_host_elapsed_deadline')
        nonce=uuid.uuid4().hex;begin=time.monotonic();name=f'{count:05d}_{nonce}'
        write(name+'_request.json',dict(nonce=nonce,sequence=count,linux_elapsed=elapsed))
        response=folder/(name+'_response.json')
        while not response.exists():
            elapsed=time.monotonic()-start
            if max(elapsed,host_elapsed+time.monotonic()-last_reply_at)>=cap:raise RuntimeError('linux_or_host_elapsed_deadline')
            if time.monotonic()-begin>2:raise RuntimeError('host_lease_expired')
            time.sleep(.01)
        reply=json.loads(response.read_text());assert reply['nonce']==nonce and reply['sequence']==count,'nonce_or_sequence_mismatch'
        assert reply['headroom_bytes']>=12*2**30,'host_memory_guard'
        assert time.monotonic()-begin<=2,'stale_response'
        host_elapsed=reply['host_elapsed'];last_reply_at=time.monotonic();last=last_reply_at;count+=1
        if max(time.monotonic()-start,host_elapsed)>=cap:raise RuntimeError('linux_or_host_elapsed_deadline')
        assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024<=512*2**20
        time.sleep(.05)
    ok=True
except BaseException as e:error=str(e);stop_at=time.monotonic()
finally:
    write('child_exit.json',dict(success=ok,error=error,elapsed=time.monotonic()-start,accepted_leases=count,last_accepted_reply_monotonic=last,stop_monotonic=stop_at,stop_after_last_accepted_reply=(stop_at-last if stop_at is not None and last is not None else None),peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,synthetic=True,GT_reads=0))
sys.exit(0 if ok else 2)

