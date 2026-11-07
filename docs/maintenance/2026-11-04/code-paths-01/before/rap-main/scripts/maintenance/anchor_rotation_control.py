"""Finite noncommuting relative-rotation/no-op contract check."""
import time
START=time.monotonic()
import os,sys,subprocess,signal,resource,traceback
from pathlib import Path
import numpy as np
import e0_local_map_six as x
r=x.r
def native():
    from coarse_anchor_fine_control import fine
    from scipy.spatial.transform import Rotation
    o=np.tile(np.eye(4),(12,1,1))
    for i in range(12):
        o[i,:3,:3]=Rotation.from_euler('xyz',[.09*i,.13*np.sin(i),-.07*i]).as_matrix()
        o[i,:3,3]=[i,.2*i*i,np.sin(i)]
    ids=[0,4,8];t=fine(o,o,ids,o[ids]);err=float(np.max(abs(t-o)));assert err<=1e-7
    relative=float(np.max(abs(np.linalg.solve(t[:-1],t[1:])-np.linalg.solve(o[:-1],o[1:]))));assert relative<=1e-7
    g=np.eye(4);g[:3,:3]=Rotation.from_euler('zyx',[.41,-.2,.17]).as_matrix();g[:3,3]=[3,-5,2]
    q=fine(g@o,g@o,ids,g@o[ids]);gauge=float(np.max(abs(q-g@t)));assert gauge<=1e-7
    r.save(x.BASE/'rotation_control.json',dict(utc=r.now(),passed=True,source_poses=o.tolist(),anchor_frames=ids,no_op_max=err,
        adjacent_motion_max=relative,world_transform_max=gauge,real_prediction_calls=0,new_metric_selection=False))
    print('Noncommuting rotation contract passed',err,relative,gauge,flush=True)
def run():
    left=1800-x.used();assert left>1;signal.signal(signal.SIGALRM,lambda a,b:(_ for _ in ()).throw(TimeoutError('original LMB cap')));signal.alarm(max(1,int(left)))
    ok=False;err=None;peak=0
    try:
        x.verify();paths=[Path(__file__),x.BASE/'ROTATION_CONTROL_SCOPE.md',Path(r.__file__).with_name('coarse_anchor_fine_control.py')]
        r.save(x.BASE/'ROTATION_CONTROL_FREEZE.json',dict(utc=r.now(),files={str(p):r.sha(p) for p in paths},remaining_original_seconds=left))
        env=os.environ.copy();env['CUDA_VISIBLE_DEVICES']='';p=subprocess.run([r.KISS,'-u','-B',__file__,'--native'],env=env,timeout=left-1)
        peak=r.read(x.SUP/'rotation_control'/'native_exit.json')['peak_RSS_bytes'];assert p.returncode==0;x.cap();ok=True
    except BaseException as e:err=repr(e);traceback.print_exc();r.save(x.BASE/'FAILURE_rotation_control.json',dict(utc=r.now(),error=err))
    finally:
        signal.alarm(0);r.save(x.SUP/'rotation_control'/'child_exit.json',dict(utc=r.now(),success=ok,error=err,wall_seconds=time.monotonic()-START,
            peak_RSS_bytes=max(peak,resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024),GPU_calls=0))
    if not ok:sys.exit(1)
if __name__=='__main__':
    if '--native' in sys.argv:
        try:native()
        finally:r.save(x.SUP/'rotation_control'/'native_exit.json',dict(utc=r.now(),wall_seconds=time.monotonic()-START,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024))
    else:assert sys.argv[1]=='rotation_control';run()
