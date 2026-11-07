"""Fixed coarse-anchor contract control, independent of trajectory accuracy gates."""
import time
START=time.monotonic()
import os,sys,resource,signal,subprocess,traceback
from pathlib import Path
import numpy as np
import e0_local_map_bundle as r
r.imports()
BASE=r.BASE

def fine(o,initial,anchors,coarse):
    from kiss_slam.pose_graph_optimizer import PoseGraphOptimizer
    p=PoseGraphOptimizer(r.config().pose_graph_optimizer); initial=initial.copy()
    for i,t in zip(anchors,coarse): initial[i]=t
    for i,t in enumerate(initial): p.add_variable(i,t)
    for i in anchors:p.fix_variable(i)
    for i in range(len(o)-1):p.add_factor(i+1,i,np.linalg.solve(o[i],o[i+1]),np.eye(6))
    p.optimize(); estimates=p.estimates(); return np.asarray([estimates[i] for i in range(len(o))])

def native():
    o=np.tile(np.eye(4),(10,1,1)); o[:,0,3]=np.arange(10); anchors=[0,3,6]; coarse=o[anchors].copy(); coarse[1,0,3]=3.3
    out=fine(o,o,anchors,coarse); expected=np.array([0,1.1,2.2,3.3,4.2,5.1,6,7,8,9.])
    error=float(np.max(abs(out[:,0,3]-expected))); anchor=float(np.max(abs(out[anchors]-coarse))); assert max(error,anchor)<=1e-8
    noop=fine(o,o,anchors,o[anchors]); ne=float(np.max(abs(noop-o))); assert ne<=1e-8
    angle=.3; g=np.eye(4); g[:3,:3]=[[np.cos(angle),-np.sin(angle),0],[np.sin(angle),np.cos(angle),0],[0,0,1]]; g[:3,3]=[4,-3,2]
    gauged=fine(g@o,g@o,anchors,g@coarse); ge=float(np.max(abs(gauged-g@out))); assert ge<=1e-7
    r.save(BASE/'coarse_anchor_control.json',dict(utc=r.now(),passed=True,anchor_max=anchor,analytic_translation_max=error,no_op_max=ne,common_world_max=ge,
        known_output_x=out[:,0,3].tolist(),real_data_optimizer_calls=0,changed_installed_sources=False))

def run():
    left=1800-r.used(); assert left>0; signal.signal(signal.SIGALRM,lambda a,b:(_ for _ in ()).throw(TimeoutError('original LMB cap'))); signal.alarm(max(1,int(left)))
    ok=False; err=None; peak=0
    try:
        r.verify_bank(); assert not r.read(BASE/'native_fine_contract.json')['contract_preserved']
        paths=[Path(__file__),BASE/'FIX_CONTROL_SCOPE.md']
        r.save(BASE/'FIX_CONTROL_FREEZE.json',dict(utc=r.now(),sources={str(p):r.sha(p) for p in paths},bank_seal_sha256=r.sha(BASE/'bank_seal.json'),remaining_original_seconds=left))
        env=os.environ.copy(); env['CUDA_VISIBLE_DEVICES']=''; p=subprocess.run([r.KISS,'-u','-B',__file__,'--native'],env=env,timeout=left-1); assert p.returncode==0
        peak=r.read(BASE/'supervision/fix_control/native_exit.json')['peak_RSS_bytes']; r.cap(); ok=True
    except BaseException as e:
        err=repr(e); traceback.print_exc(); r.save(BASE/'FAILURE_fix_control.json',dict(utc=r.now(),error=err))
    finally:
        signal.alarm(0); r.save(BASE/'supervision/fix_control/child_exit.json',dict(utc=r.now(),success=ok,error=err,wall_seconds=time.monotonic()-START,
            peak_RSS_bytes=max(peak,resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024),GPU_calls=0))
    if not ok:sys.exit(1)
if __name__=='__main__':
    if '--native' in sys.argv:
        try:native()
        finally:r.save(BASE/'supervision/fix_control/native_exit.json',dict(utc=r.now(),wall_seconds=time.monotonic()-START,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024))
    else:
        assert sys.argv[1]=='fix_control';run()
