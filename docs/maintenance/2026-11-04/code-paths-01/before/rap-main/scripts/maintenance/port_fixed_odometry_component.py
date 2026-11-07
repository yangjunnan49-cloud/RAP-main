"""Exact class extraction and native interface smoke test, original LMB account."""
import time
START=time.monotonic()
import os,sys,ast,resource,signal,subprocess,traceback,importlib.util
from pathlib import Path
import numpy as np
import e0_local_map_six as x
r=x.r
BASE=r.MAIN/'docs/maintenance/2026-10-20/e0-odometry-adapter-component-01'
SUP=BASE/'supervision'
OLDTOTAL=r.read(BASE.parent/'weekly-system-handoff-01/COST_SUPPLEMENT.json')['LMB_total_seconds']
def native():
    spec=importlib.util.spec_from_file_location('portable_fixed_odometry',BASE/'fixed_odometry.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    from kiss_slam.slam import KissSLAM
    o=np.tile(np.eye(4),(14,1,1));o[:,0,3]=np.arange(14)*40.;o[:,1,3]=np.arange(14)*.2
    slam=KissSLAM(r.config());fixed=module.FixedOdometry(r.config().kiss_icp_config(),o);slam.odometry=fixed;slam.compute_closures=lambda *args:None
    points=np.random.default_rng(20261020).uniform([5,-8,-2],[25,8,3],(5000,3))
    for i in range(len(o)):slam.process_scan(points,np.array([]))
    out=np.asarray(slam.poses);error=float(np.max(abs(out-o)));assert out.shape==o.shape and error<=1e-5 and fixed.resets==[3,6,9,12]
    slam.generate_new_node();slam.local_map_graph.erase_last_local_map();assert fixed.resets==[3,6,9,12,13] and fixed.max_relative_error<=1e-10
    r.save(BASE/'INTERFACE_CHECKS.json',dict(utc=r.now(),passed=True,frames=14,synthetic_point_seed=20261020,known_odometry_max=error,relative_expression_max=fixed.max_relative_error,
        reset_anchors=fixed.resets,odometry_alignment_calls=0,real_scans_read=0,GT_numeric_read=False,new_accuracy_metrics=False))
def run():
    left=1800-OLDTOTAL;assert left>1;signal.signal(signal.SIGALRM,lambda a,b:(_ for _ in ()).throw(TimeoutError('original LMB cap')));signal.alarm(max(1,int(left)))
    ok=False;err=None;peak=0
    try:
        x.verify();source=Path(r.__file__);text=source.read_text();node=next(n for n in ast.parse(text).body if isinstance(n,ast.ClassDef) and n.name=='FixedOdometry')
        module='"""Fixed external odometry adapter; requires the existing KISS-SLAM environment."""\nimport numpy as np\n\n'+ast.get_source_segment(text,node)+'\n'
        (BASE/'fixed_odometry.py').write_text(module,encoding='utf-8');outnode=next(n for n in ast.parse(module).body if isinstance(n,ast.ClassDef));assert ast.dump(node,include_attributes=False)==ast.dump(outnode,include_attributes=False)
        r.save(BASE/'FREEZE.json',dict(utc=r.now(),files={str(p):r.sha(p) for p in (Path(__file__),source,BASE/'fixed_odometry.py',BASE/'OWNER_SCOPE.md')},AST_class_exact=True,original_LMB_seconds=OLDTOTAL,remaining_original_seconds=left))
        env=os.environ.copy();env['CUDA_VISIBLE_DEVICES']='';p=subprocess.run([r.KISS,'-u','-B',__file__,'--native'],env=env,timeout=left-1)
        receipt=r.read(SUP/'adapter_portability/native_exit.json');peak=receipt['peak_RSS_bytes'];assert p.returncode==0 and receipt['success'];assert max(peak,resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024)<=4*2**30
        assert sum(p.stat().st_size for d in (x.OLD,x.BASE,BASE,BASE.parent/'e0-anchor-capsule-01') for p in d.rglob('*') if p.is_file())<=128*2**20;ok=True
    except BaseException as e:err=repr(e);traceback.print_exc();r.save(BASE/'FAILURE_adapter_portability.json',dict(utc=r.now(),error=err))
    finally:
        signal.alarm(0);r.save(SUP/'adapter_portability/child_exit.json',dict(utc=r.now(),success=ok,error=err,wall_seconds=time.monotonic()-START,peak_RSS_bytes=max(peak,resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024),GPU_calls=0,original_LMB_cap=True))
    if not ok:sys.exit(1)
if __name__=='__main__':
    if '--native' in sys.argv:
        good=False
        try:native();good=True
        finally:r.save(SUP/'adapter_portability/native_exit.json',dict(utc=r.now(),success=good,wall_seconds=time.monotonic()-START,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,GPU_calls=0))
    else:assert sys.argv[1]=='adapter_portability';run()
