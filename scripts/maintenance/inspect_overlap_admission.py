"""P0 prestart source/dataflow and old-repeat stability; no new raw computation."""
import time
START=time.monotonic()
import sys,ast,itertools,resource,traceback
from pathlib import Path
import numpy as np
import raw_input_system06 as d
BASE=d.r.MAIN/'docs/maintenance/2026-10-21/runtime-overlap-01';SUP=BASE/'supervision'
def run():
    ok=False;error=None
    try:
        d.verify();assert sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file())<256*2**20
        seal=d.read(d.BASE/'bank_seal06.json');sources=[Path(__file__),BASE/'OWNER_SCOPE.md',BASE/'DESIGN.md',d.BASE/'bank_seal06.json',d.r.SLAM/'rap_slam/odometry.py',d.AD/'fixed_odometry.py',d.BASE/'legacy_f32_correction.py']
        d.save(BASE/'ADMISSION_SOURCE_FREEZE.json',dict(utc=d.now(),files={str(p):d.sha(p) for p in sources},no_new_predictions=True,no_new_GT=True))
        tree=ast.parse((d.r.SLAM/'rap_slam/odometry.py').read_text());front=next(x for x in tree.body if isinstance(x,ast.ClassDef) and x.name=='KissOdometry')
        assert not any(isinstance(x,ast.Name) and x.id in ('slam','local_map_graph','closer','optimizer') for x in ast.walk(front))
        own_attributes=sorted(set(x.attr for x in ast.walk(front) if isinstance(x,ast.Attribute) and isinstance(x.value,ast.Name) and x.value.id=='self'))
        assert set(own_attributes)=={'_odom','_deskew','_poses','backend_name'}
        rows={};all_G=True
        for s in d.SEQS:
            rows[s]={}
            for m in ('G','K'):
                poses=[];bindings=[]
                for rep in (1,2,3):
                    root=d.BASE/'bank06'/f'r{rep}_{s}_{m}'
                    for name in ('poses.npy','source_binding.json'):
                        p=root/name;assert d.sha(p)==seal['files'][str(p.relative_to(d.BASE/'bank06'))]
                    poses.append(np.load(root/'poses.npy'));bindings.append(d.read(root/'source_binding.json'))
                translation=rotation=0.
                for i,j in itertools.combinations(range(3),2):
                    translation=max(translation,float(np.max(abs(poses[i][:,:3,3]-poses[j][:,:3,3]))))
                    rotation=max(rotation,float(np.max(abs(poses[i][:,:3,:3]-poses[j][:,:3,:3]))))
                resets=all(x['reset_anchors']==bindings[0]['reset_anchors'] for x in bindings)
                def loops(x):return [(q['source'],q['target']) for q in x['loop_attempts'] if q['accepted']]
                loop_equal=all(loops(x)==loops(bindings[0]) for x in bindings)
                numerical=translation<=.001 and rotation<=1e-5
                rows[s][m]=dict(pairwise_translation_max_m=translation,pairwise_rotation_max=rotation,reset_lists_equal=resets,accepted_loop_endpoints_equal=loop_equal,numerical_limits_passed=numerical)
                if m=='G':all_G=all_G and numerical and resets and loop_equal
        result=dict(utc=d.now(),G_repeat_admission_passed=all_G,rows=rows,translation_limit_m=.001,rotation_limit=1e-5,source_frontend_own_attributes=own_attributes,
            frontend_has_no_map_feedback_by_review=True,native_randomness_cause_UNKNOWN=True,no_seed_change=True,new_raw_decodes=0,new_registration_calls=0,new_pose_metrics=0,
            status='ELIGIBLE_FOR_IMPLEMENTATION_AND_SYNTHETIC_ONLY' if all_G else 'CLOSED_PRESTART_G_REPEAT_EQUIVALENCE_NOT_ESTABLISHED',raw_launch_admitted=False)
        d.save(BASE/'ADMISSION.json',result);print('P0 prestart admission',result,flush=True);ok=True
    except BaseException as e:error=repr(e);traceback.print_exc()
    finally:d.save(SUP/'admission/child_exit.json',dict(utc=d.now(),success=ok,error=error,wall_seconds=time.monotonic()-START,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,GPU_calls=0,new_P0_account_seconds=9000))
    if not ok:sys.exit(1)
if __name__=='__main__':assert sys.argv[1]=='admission';run()
