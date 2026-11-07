"""Exact DMF validator math; only per-chunk filesystem guard frequency changes."""
import time
START=time.monotonic()
import inspect
import resource
import signal
import sys
import traceback
import numpy as np
import direct_matching_factors as r
r.imports()
import validate_direct_matching_factors as v

def fast_brute(q,p):
    ds=[]; ix=[]
    for k in range(0,len(q),64):
        d=np.sum((q[k:k+64,None,:]-p[None,:,:])**2,axis=2); ids=np.argmin(d,axis=1)
        ix.extend(ids); ds.extend(np.sqrt(d[np.arange(len(ids)),ids])); assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024<=4*2**30
    return np.asarray(ds),np.asarray(ix)

def run():
    remaining=1800-r.used(); assert remaining>0
    signal.signal(signal.SIGALRM,lambda a,b:(_ for _ in ()).throw(TimeoutError('original DMF remaining budget'))); signal.alarm(max(1,int(remaining)))
    ok=False; err=None
    try:
        r.verify(); r.verify_bank(); r.cap()
        expected=inspect.getsource(v.brute).replace('def brute(', 'def fast_brute(').replace('r.cap()','assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024<=4*2**30')
        assert inspect.getsource(fast_brute).strip()==expected.strip()
        paths=[__file__,r.BASE/'AMENDMENT_01.md']
        r.save(r.BASE/'VALIDATION02_FREEZE.json',dict(utc=r.now(),sources={str(p):r.sha(p) for p in paths},original_freeze_sha256=r.sha(r.BASE/'freeze.json'),
            bank_seal_sha256=r.sha(r.BASE/'bank_seal.json'),remaining_original_seconds=remaining,sole_function_difference='per-chunk guard only; textual equivalence passed'))
        (r.BASE/'source_snapshot/validation02.py').write_bytes(open(__file__,'rb').read())
        v.brute=fast_brute; v.bank(); r.cap(); ok=True
    except BaseException as e:
        err=repr(e); traceback.print_exc(); r.save(r.BASE/'FAILURE_validate_bank02.json',dict(utc=r.now(),error=err))
    finally:
        signal.alarm(0); r.save(r.SUP/'validate_bank02/child_exit.json',dict(utc=r.now(),success=ok,error=err,wall_seconds=time.monotonic()-START,
            peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,GPU_calls=0))
    if not ok: sys.exit(1)
if __name__=='__main__':
    assert sys.argv[1]=='validate_bank02'; run()
