"""Complete six frontend correspondence control, no maps or GT."""
import time
START=time.monotonic()
import os,sys,resource,signal,subprocess,traceback,importlib.util,hashlib
from pathlib import Path
import numpy as np
import certify_raw_input_contract as c
d=c.d;BASE=c.BASE;SUP=c.SUP
def native():
    from rap_slam.odometry import KissOdometry
    spec=importlib.util.spec_from_file_location('explicit_legacy_f32',BASE/'legacy_f32_correction.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    reference=d.read(BASE/'original_prepared_reference.json');f=d.read(c.R0/'freeze.json');dest=BASE/'frontend_eligibility';dest.mkdir();rows={}
    for s in d.SEQS:
        engine=KissOdometry(max_range=80.,min_range=1.5,voxel_size=.8,deskew=False);poses=[];begin=time.monotonic()
        for i in range(f['counts'][s]):
            p=d.r.raw(s,i);body=p.read_bytes();assert hashlib.sha256(body).hexdigest()==f['raw_files'][str(p)];raw=np.frombuffer(body,np.float32).reshape(-1,4)[:,:3]
            prepared=m.legacy_f32_correction(raw[np.linalg.norm(raw,axis=1)>=1.5].copy());ref=reference['rows'][s][i];assert len(prepared)==ref['points'] and hashlib.sha256(prepared.tobytes(order='C')).hexdigest()==ref['prepared_sha256']
            poses.append(engine.register(prepared).copy())
            if i%500==0:c.cap();print('frontend eligibility',s,i,flush=True)
        o=np.asarray(poses);np.save(dest/f'{s}_fresh.npy',o);proper=d.r.proper(o);old=d.r.proper(d.r.poses(d.old.src(s)/'odom_poses.txt'));delta=abs(proper-old);maximum=float(np.max(delta));where=np.unravel_index(int(np.argmax(delta)),delta.shape)
        record=dict(frames=len(o),maximum_matrix_difference=maximum,maximum_index=[int(v) for v in where],seconds=time.monotonic()-begin,pose_file_sha256=d.sha(dest/f'{s}_fresh.npy'),passed=maximum<=1e-5)
        d.save(dest/f'{s}_check.json',record);rows[s]=record;assert maximum<=1e-5,('original E0 correspondence failed',s,maximum)
    d.save(BASE/'FRONTEND_ELIGIBILITY.json',dict(utc=d.now(),passed=True,all_six=True,rows=rows,GT_numeric_read=False,old_pose_cache_supplied_frontend=False,eligibility_poses_used_as_benchmark_input=False))
def run():
    left=7200-c.used();assert left>1;signal.signal(signal.SIGALRM,lambda a,b:(_ for _ in ()).throw(TimeoutError('shared campaign cap')));signal.alarm(max(1,int(left)))
    ok=False;err=None;peak=0
    try:
        d.verify();assert d.read(BASE/'INPUT_CERTIFICATE.json')['passed']
        d.save(BASE/'ELIGIBILITY_FREEZE.json',dict(utc=d.now(),files={str(p):d.sha(p) for p in (Path(__file__),BASE/'FRONTEND_ELIGIBILITY_SCOPE.md',BASE/'legacy_f32_correction.py',BASE/'INPUT_CERTIFICATE.json',BASE/'original_prepared_reference.json')},shared_remaining_seconds=left))
        env=os.environ.copy();env['CUDA_VISIBLE_DEVICES']='';p=subprocess.run([d.r.KISS,'-u','-B',__file__,'--native'],env=env,timeout=left-1);receipt=d.read(SUP/'frontend_eligibility/native_exit.json');peak=receipt['peak_RSS_bytes'];assert p.returncode==0 and receipt['success'];c.cap();ok=True
    except BaseException as e:err=repr(e);traceback.print_exc();d.save(BASE/'FAILURE_frontend_eligibility.json',dict(utc=d.now(),error=err))
    finally:
        signal.alarm(0);d.save(SUP/'frontend_eligibility/child_exit.json',dict(utc=d.now(),success=ok,error=err,wall_seconds=time.monotonic()-START,peak_RSS_bytes=max(peak,resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024),GPU_calls=0,shared_R0_cap=True))
    if not ok:sys.exit(1)
if __name__=='__main__':
    if '--native' in sys.argv:
        good=False
        try:native();good=True
        finally:d.save(SUP/'frontend_eligibility/native_exit.json',dict(utc=d.now(),success=good,wall_seconds=time.monotonic()-START,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,GPU_calls=0))
    else:assert sys.argv[1]=='frontend_eligibility';run()
