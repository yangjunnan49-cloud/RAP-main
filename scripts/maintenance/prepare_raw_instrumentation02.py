"""Bind pre-payload timing/source-event instrumentation; numerical calls unchanged."""
import time
START=time.monotonic()
import ast,json,sys,resource,hashlib,traceback
from pathlib import Path
MAIN=Path(__file__).resolve().parents[2];BASE=MAIN/'docs/maintenance/2026-10-20/raw-system-integration-01'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):
    with p.open('x',encoding='utf-8') as f:json.dump(x,f,indent=2);f.write('\n')
def run():
    ok=False;error=None
    try:
        original=Path(__file__).with_name('raw_system_integration.py');out=original.with_name('raw_system_integration02.py');text=original.read_text();assert read(BASE/'freeze.json')['files'][str(original)]==sha(original);source=text
        def replace(a,b):
            nonlocal source
            assert source.count(a)==1,(a,source.count(a));source=source.replace(a,b)
        replace("    for p,h in read(BASE/'freeze.json')['files'].items():assert sha(p)==h,p", "    for p,h in read(BASE/'freeze.json')['files'].items():assert sha(p)==h,p\n    for p,h in read(BASE/'VARIANT02_FREEZE.json')['files'].items():assert sha(p)==h,p")
        observer="""def observe_generate(slam,frame_ref,events):
    original=slam.generate_new_node
    def wrapped():
        value=original();events.append(int(frame_ref[0]));return value
    slam.generate_new_node=wrapped
"""
        replace('def worker(cell):',observer+'def worker(cell):')
        replace("    for i in range(n):\n        start=time.perf_counter()", "    frame_ref=[-1];reset_events=[];observe_generate(slam,frame_ref,reset_events)\n    for i in range(n):\n        frame_ref[0]=i\n        start=time.perf_counter()")
        oldio="        np.save(dest/'odometry.npy',o);np.save(dest/'before_fine.npy',initial);save(dest/'anchors.json',dict(anchor_frames=anchors,coarse_poses=coarse.tolist(),maximum_reconstruction=reconstruction,maximum_preservation=anchor_max))"
        replace(oldio,"        anchor_record=dict(anchor_frames=anchors,coarse_poses=coarse.tolist(),maximum_reconstruction=reconstruction,maximum_preservation=anchor_max)")
        replace("        resets=fixed.resets;relative=fixed.max_relative_error;assert relative<=1e-9","        resets=fixed.resets;relative=fixed.max_relative_error;assert relative<=1e-9 and resets==reset_events")
        replace("        t,pgo=slam.fine_grained_optimization();t=np.asarray(t);resets=None;relative=None;pgo.write_graph(str(dest/'trajectory.g2o'))","        t,pgo=slam.fine_grained_optimization();t=np.asarray(t);resets=reset_events;relative=None")
        replace("    fine_seconds=time.monotonic()-fine_begin;assert t.shape==", "    fine_seconds=time.monotonic()-fine_begin;serialization_begin=time.monotonic()\n    if m=='G':\n        np.save(dest/'odometry.npy',o);np.save(dest/'before_fine.npy',initial);save(dest/'anchors.json',anchor_record)\n    else:pgo.write_graph(str(dest/'trajectory.g2o'))\n    assert t.shape==")
        replace("        fine_seconds=fine_seconds,frame_timing_columns=", "        fine_seconds=fine_seconds,serialization_seconds=time.monotonic()-serialization_begin,private_evidence_outputs_identical=False,frame_timing_columns=")
        marker="    assert maximum<=1e-5\n    # Noncommuting"
        test="""    assert maximum<=1e-5
    known=np.tile(np.eye(4),(14,1,1));known[:,0,3]=np.arange(14)*40.;known[:,1,3]=np.arange(14)*.2
    smoke=KissSLAM(config('G'));adapter=fixed_module.FixedOdometry(config('G').kiss_icp_config(),known);smoke.odometry=adapter;smoke.compute_closures=lambda *args:None
    frame_ref=[-1];events=[];observe_generate(smoke,frame_ref,events)
    for i in range(14):frame_ref[0]=i;smoke.process_scan(corrected.copy(),np.array([]))
    smoke.generate_new_node();smoke.local_map_graph.erase_last_local_map()
    assert events==adapter.resets==[3,6,9,12,13] and np.max(abs(np.asarray(smoke.poses)-known))<=1e-5
    # Noncommuting"""
        replace(marker,test)
        compile(source,str(out),'exec')
        def calls(code):
            worker=next(n for n in ast.parse(code).body if isinstance(n,ast.FunctionDef) and n.name=='worker')
            names={'front.register','slam.process_scan','slam.generate_new_node','slam.local_map_graph.erase_last_local_map','fine_module.fine','slam.fine_grained_optimization','np.linalg.solve','kitti_vertical_correction','binding._correct_kitti_scan','proper_one'}
            return [ast.dump(n,include_attributes=False) for n in ast.walk(worker) if isinstance(n,ast.Call) and ast.unparse(n.func) in names]
        assert calls(text)==calls(source)
        with out.open('x',encoding='utf-8') as f:f.write(source)
        save(BASE/'VARIANT02_FREEZE.json',dict(files={str(p):sha(p) for p in (original,out,Path(__file__),BASE/'INSTRUMENTATION02.md')},original_freeze_sha256=sha(BASE/'freeze.json'),numerical_call_AST_equal=True,syntax_compiled=True,real_numeric_payloads_before_variant=0,new_cap=False))
        print('Instrumentation02 prepared; numerical call AST unchanged',flush=True);ok=True
    except BaseException as e:error=repr(e);traceback.print_exc()
    finally:save(BASE/'supervision/prepare02/child_exit.json',dict(success=ok,error=error,wall_seconds=time.monotonic()-START,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,GPU_calls=0))
    if not ok:sys.exit(1)
if __name__=='__main__':assert sys.argv[1]=='prepare02';run()
