"""All-six source-bound descriptive audit; no new prediction or gating."""
import time
START=time.monotonic()
import sys,resource,signal,traceback
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
import e0_local_map_six as x
r=x.r
def run():
    left=1800-x.used();assert left>1;signal.signal(signal.SIGALRM,lambda a,b:(_ for _ in ()).throw(TimeoutError('original LMB cap')));signal.alarm(max(1,int(left)))
    ok=False;err=None
    try:
        x.verify();primary=r.read(x.BASE/'results.json');assert primary['independent_validation_passed']
        paths=[Path(__file__),x.BASE/'MECHANISM_AUDIT_SCOPE.md',x.BASE/'results.json',x.BASE/'odometry_control.json',
            x.OLD/'source_snapshot/012-loop_closer.py',x.OLD/'source_snapshot/017-slam.py']
        for s in x.SEQS:
            paths.append((x.BASE if s in x.NEW else x.OLD)/f'bank/{s}/source_binding.json')
        r.save(x.BASE/'MECHANISM_AUDIT_FREEZE.json',dict(utc=r.now(),files={str(p):r.sha(p) for p in paths},remaining_original_seconds=left,post_hoc=True))
        import validate_scan_level_graph as v
        control=r.read(x.BASE/'odometry_control.json');rows={};total=0
        for s in x.SEQS:
            o=r.proper(r.poses(x.src(s)/'odom_poses.txt'));b=r.poses(x.src(s)/'optimized_poses.txt');g=np.load(x.BASE/f'bank/{s}/G.npy') if s in x.NEW else np.load(x.OLD/f'anchor_corrected_bank/{s}/G.npy')
            binding=r.read((x.BASE if s in x.NEW else x.OLD)/f'bank/{s}/source_binding.json');cam=v.load(r.DATA/f'poses/{s}.txt');tr=v.calibration(s);gt=np.linalg.inv(tr)@cam@tr
            anchors={int(mid):0 if int(mid)==0 else binding['reset_anchors'][int(mid)-1] for mid in binding['map_consumed_frames']}
            measurements=[]
            for q in binding['loop_attempts']:
                if not q['accepted']:continue
                ai=anchors[q['source']];aj=anchors[q['target']];z=np.asarray(q['pose']);ref=np.linalg.solve(gt[aj],gt[ai]);arms={}
                for a,t in [('measurement',z),('O',np.linalg.solve(o[aj],o[ai])),('B',np.linalg.solve(b[aj],b[ai])),('G',np.linalg.solve(g[aj],g[ai]))]:
                    e=np.linalg.solve(ref,t);arms[a]=dict(translation_m=float(np.linalg.norm(e[:3,3])),rotation_deg=float(np.degrees(np.linalg.norm(Rotation.from_matrix(e[:3,:3]).as_rotvec()))))
                measurements.append(dict(source_map=q['source'],target_map=q['target'],source_frame=ai,target_frame=aj,reference_relative=ref.tolist(),arms=arms))
            total+=len(measurements)
            seg={'O':v.segments(cam,tr@o@np.linalg.inv(tr)),'B':r.read(x.BASE/f'evaluation/{s}/B_segments.json'),'G':r.read(x.BASE/f'evaluation/{s}/G_segments.json')}
            assert len({len(p) for p in seg.values()})==1
            assert abs(np.mean([p['translation_fraction'] for p in seg['O']])*100-control['rows'][s]['O']['ter'])<=1e-8
            groups={}
            for length in sorted({p['length_m'] for p in seg['O']}):
                ix=[i for i,p in enumerate(seg['O']) if p['length_m']==length];group={}
                for a in seg:
                    for i in ix:
                        for k in ('first','last','length_m'):assert seg['O'][i][k]==seg[a][i][k]
                    group[a]=dict(ter=float(np.mean([seg[a][i]['translation_fraction'] for i in ix])*100),
                        rer=float(np.mean([seg[a][i]['rotation_rad_per_m'] for i in ix])*180/np.pi*100))
                delta=np.asarray([seg['G'][i]['translation_fraction']-seg['O'][i]['translation_fraction'] for i in ix])
                groups[str(length)]=dict(count=len(ix),metrics=group,G_minus_O_ter_pp=float(np.mean(delta)*100),G_better_count=int(np.sum(delta<-1e-10)),G_worse_count=int(np.sum(delta>1e-10)),equal_count=int(np.sum(abs(delta)<=1e-10)))
            noop=float(np.max(abs(g-o)))
            if len(measurements)==0:assert noop<=1e-7
            rows[s]=dict(accepted_closures=len(measurements),all_compute_calls=len(binding['loop_attempts']),G_minus_O_pose_max=noop,
                no_loop_no_op_passed=noop<=1e-7 if not measurements else None,measurements=measurements,all_official_lengths=groups)
        r.save(x.BASE/'mechanism_audit.json',dict(utc=r.now(),post_hoc_descriptive_only=True,rows=rows,all_accepted_closures=total,
            new_predictions=0,new_solver_calls=0,new_gate_or_threshold=False,primary_gate_unchanged=primary['gate'],physical_reference_authentication=False))
        print('All-six deformation audit',total,'closures; zero-loop no-ops',{s:rows[s]['G_minus_O_pose_max'] for s in ('09','10')},flush=True);x.cap();ok=True
    except BaseException as e:err=repr(e);traceback.print_exc();r.save(x.BASE/'FAILURE_mechanism_audit.json',dict(utc=r.now(),error=err))
    finally:
        signal.alarm(0);r.save(x.SUP/'mechanism_audit'/'child_exit.json',dict(utc=r.now(),success=ok,error=err,wall_seconds=time.monotonic()-START,
            peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,GPU_calls=0))
    if not ok:sys.exit(1)
if __name__=='__main__':assert sys.argv[1]=='mechanism_audit';run()
