"""Unchanged strict gate and independent metrics for sealed corrected anchors."""
import time
START=time.monotonic()
import sys,signal,resource,traceback
from pathlib import Path
import numpy as np
import e0_local_map_bundle as r
r.imports()
import validate_scan_level_graph as v
BASE=r.BASE
def run():
    left=1800-r.used(); assert left>0; signal.signal(signal.SIGALRM,lambda a,b:(_ for _ in ()).throw(TimeoutError('original LMB cap'))); signal.alarm(max(1,int(left)))
    ok=False; err=None
    try:
        r.verify_bank(); seal=r.read(BASE/'anchor_corrected_seal.json')
        for p,h in seal['files'].items():assert r.sha(BASE/'anchor_corrected_bank'/p)==h
        r.save(BASE/'ANCHOR_METRIC_FREEZE.json',dict(utc=r.now(),sources={str(p):r.sha(p) for p in [Path(__file__),BASE/'ANCHOR_METRIC_SCOPE.md']},corrected_seal_sha256=r.sha(BASE/'anchor_corrected_seal.json'),remaining_original_seconds=left))
        from rap_slam.real_dataset import load_gt_poses,_read_calib_transform
        import eval_paper_metrics as epm
        started=r.now(); rows={}; original=r.read(BASE/'results.json'); count=0; maximum=0.
        for s in r.SEQS:
            t=np.load(BASE/f'anchor_corrected_bank/{s}/G.npy'); tr=_read_calib_transform(str(r.DATA/f'sequences/{s}/calib.txt')); ti=np.linalg.inv(tr)
            gt=np.asarray(load_gt_poses(str(r.DATA/f'poses/{s}.txt'),str(r.DATA/f'sequences/{s}/calib.txt'),apply_calib=True)); ids=list(range(len(t)))
            lidar=epm.evaluate_pair(list(gt),list(t),ids); camera=epm.evaluate_pair(list(tr@gt@ti),list(tr@t@ti),ids)
            x=dict(ate=lidar['ape_aligned_rmse'],ter=camera['kitti_ter_pct'],rer=camera['kitti_rer_deg100m'],segments=camera['kitti_segments'])
            cg=v.load(r.DATA/f'poses/{s}.txt'); ct=v.calibration(s); independent=v.segments(cg,ct@t@np.linalg.inv(ct)); count+=len(independent)
            y=dict(ate=v.horn_rmse(np.linalg.inv(ct)@cg@ct,t),ter=float(np.mean([a['translation_fraction'] for a in independent])*100),
                rer=float(np.mean([a['rotation_rad_per_m'] for a in independent])*180/np.pi*100),segments=len(independent))
            for k in x:maximum=max(maximum,abs(x[k]-y[k]));assert abs(x[k]-y[k])<=1e-8
            for a,b in zip(independent,camera['kitti_segment_records']):
                for k in ('first','last','length_m'):assert a[k]==b[k]
                for k in ('translation_fraction','rotation_rad_per_m'):assert abs(a[k]-b[k])<=2e-10
            rows[s]={'B':original['rows'][s]['B'],'M':original['rows'][s]['M'],'G':x}
        strict=r.gates({s:{'B':rows[s]['B'],'M':rows[s]['G']} for s in r.SEQS})
        r.save(BASE/'anchor_results.json',dict(utc=r.now(),gt_read_started_utc=started,corrected_seal_sha256=r.sha(BASE/'anchor_corrected_seal.json'),rows=rows,
            original_strict_gate_against_B=strict,independent_validation_passed=True,independent_segment_records=count,independent_metric_max_delta=maximum))
        print(rows,'strict pass',strict['passed'],flush=True);r.cap();ok=True
    except BaseException as e:
        err=repr(e);traceback.print_exc();r.save(BASE/'FAILURE_evaluate_anchor.json',dict(utc=r.now(),error=err))
    finally:
        signal.alarm(0);r.save(BASE/'supervision/evaluate_anchor/child_exit.json',dict(utc=r.now(),success=ok,error=err,wall_seconds=time.monotonic()-START,
            peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,GPU_calls=0))
    if not ok:sys.exit(1)
if __name__=='__main__':assert sys.argv[1]=='evaluate_anchor';run()
