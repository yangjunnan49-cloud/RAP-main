"""Descriptive no-loop E0 control on existing source poses; no new prediction."""
import time
START=time.monotonic()
import sys,signal,resource,traceback
from pathlib import Path
import numpy as np
import e0_local_map_six as x
r=x.r
def run():
    left=1800-x.used();assert left>1;signal.signal(signal.SIGALRM,lambda a,b:(_ for _ in ()).throw(TimeoutError('original LMB cap')));signal.alarm(max(1,int(left)))
    ok=False;err=None
    try:
        x.verify();primary=r.read(x.BASE/'results.json');assert primary['independent_validation_passed'] and primary['bank_sealed_before_GT']
        paths=[Path(__file__),x.BASE/'ODOMETRY_CONTROL_SCOPE.md',x.BASE/'results.json']+[x.src(s)/n for s in x.SEQS for n in ('source_frames.json','odom_poses.txt')]
        r.save(x.BASE/'ODOMETRY_CONTROL_FREEZE.json',dict(utc=r.now(),files={str(p):r.sha(p) for p in paths},remaining_original_seconds=left,descriptive_only=True))
        from rap_slam.real_dataset import load_gt_poses,_read_calib_transform
        import eval_paper_metrics as epm
        import validate_scan_level_graph as v
        rows={};maximum=0.;count=0
        for s in x.SEQS:
            o=r.proper(r.poses(x.src(s)/'odom_poses.txt'));tr=_read_calib_transform(str(r.DATA/f'sequences/{s}/calib.txt'));ti=np.linalg.inv(tr)
            gt=np.asarray(load_gt_poses(str(r.DATA/f'poses/{s}.txt'),str(r.DATA/f'sequences/{s}/calib.txt'),apply_calib=True));assert o.shape==gt.shape
            li=epm.evaluate_pair(list(gt),list(o),list(range(len(o))));ca=epm.evaluate_pair(list(tr@gt@ti),list(tr@o@ti),list(range(len(o))))
            a=dict(ate=li['ape_aligned_rmse'],ter=ca['kitti_ter_pct'],rer=ca['kitti_rer_deg100m'],segments=ca['kitti_segments'])
            cg=v.load(r.DATA/f'poses/{s}.txt');ct=v.calibration(s);seg=v.segments(cg,ct@o@np.linalg.inv(ct));count+=len(seg)
            b=dict(ate=v.horn_rmse(np.linalg.inv(ct)@cg@ct,o),ter=float(np.mean([p['translation_fraction'] for p in seg])*100),rer=float(np.mean([p['rotation_rad_per_m'] for p in seg])*180/np.pi*100),segments=len(seg))
            for k in a:maximum=max(maximum,abs(a[k]-b[k]));assert abs(a[k]-b[k])<=1e-8
            rows[s]=dict(O=a,G=primary['rows'][s]['G'],B=primary['rows'][s]['B'])
        means={arm:{k:float(np.mean([rows[s][arm][k] for s in x.SEQS])) for k in ('ate','ter','rer')} for arm in ('O','B','G')}
        r.save(x.BASE/'odometry_control.json',dict(utc=r.now(),rows=rows,means=means,descriptive_only=True,independent_validation_passed=True,
            independent_segments=count,maximum_metric_delta=maximum,new_predictions=0,new_solver_calls=0,primary_gate_unchanged=primary['gate']))
        print('Descriptive O control',means,flush=True);x.cap();ok=True
    except BaseException as e:err=repr(e);traceback.print_exc();r.save(x.BASE/'FAILURE_odometry_control.json',dict(utc=r.now(),error=err))
    finally:
        signal.alarm(0);r.save(x.SUP/'odometry_control'/'child_exit.json',dict(utc=r.now(),success=ok,error=err,wall_seconds=time.monotonic()-START,
            peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,GPU_calls=0))
    if not ok:sys.exit(1)
if __name__=='__main__':assert sys.argv[1]=='odometry_control';run()
