"""Finite post-hoc source contract diagnosis; no real-data optimization."""
import time
START=time.monotonic()
import sys,os,signal,resource,traceback,subprocess
from pathlib import Path
import numpy as np
import e0_local_map_bundle as r
r.imports()
BASE=r.BASE
def native():
    from kiss_slam.slam import KissSLAM
    from kiss_slam.local_map_graph import LocalMapGraph,LocalMap
    slam=KissSLAM.__new__(KissSLAM); slam.config=r.config(); graph=LocalMapGraph(); graph.graph.clear()
    for k,x in enumerate((0.,3.3,6.)):
        pose=np.eye(4); pose[0,3]=x; node=LocalMap(k,pose)
        node.local_trajectory=[]
        for j in range(4):
            p=np.eye(4); p[0,3]=j; node.local_trajectory.append(p)
        graph.graph[k]=node
    slam.local_map_graph=graph
    out,_=slam.fine_grained_optimization(); out=np.asarray(out); anchors=[0,3,6]; expected=[0.,3.3,6.]
    assert out.shape==(10,4,4)
    errors=[float(abs(out[i,0,3]-x)) for i,x in zip(anchors,expected)]
    r.save(BASE/'native_fine_contract.json',dict(utc=r.now(),anchors=anchors,expected_x=expected,actual_x=out[anchors,0,3].tolist(),
        absolute_errors=errors,contract_preserved=max(errors)<=1e-8,all_output_x=out[:,0,3].tolist(),known_input=True,real_data_optimizer_calls=0))

def inspect_real():
    import validate_scan_level_graph as m
    r.verify_bank(); assert r.read(BASE/'validation.json')['passed']; rows={}
    for s in r.SEQS:
        o=r.proper(r.poses(r.src(s)/'odom_poses.txt')); before=np.load(BASE/f'bank/{s}/before_fine.npy'); final=np.load(BASE/f'bank/{s}/M.npy')
        binding=r.read(BASE/f'bank/{s}/source_binding.json'); coarse=[]; maximum=0.
        for key,frames in binding['map_consumed_frames'].items():
            mapid=int(key); anchor=0 if mapid==0 else binding['reset_anchors'][mapid-1]; first=frames[0]
            pose=before[first]@np.linalg.solve(o[first],o[anchor])
            for i in frames: maximum=max(maximum,float(np.max(abs(pose@np.linalg.solve(o[anchor],o[i])-before[i]))))
            delta=np.linalg.solve(pose,final[anchor]); coarse.append(dict(map_id=mapid,anchor_frame=anchor,pose=pose.tolist(),
                fine_anchor_translation_change=float(np.linalg.norm(delta[:3,3])),fine_anchor_rotation_change_deg=float(np.degrees(np.linalg.norm(m.Rotation.from_matrix(delta[:3,:3]).as_rotvec())))))
        assert maximum<=1e-8,maximum
        tr=m.calibration(s); ti=np.linalg.inv(tr); camera=m.load(r.DATA/f'poses/{s}.txt'); lidar=ti@camera@tr; measures={}
        for name,t in [('O',o),('B',r.poses(r.src(s)/'optimized_poses.txt')),('before_fine',before),('M',final)]:
            seg=m.segments(camera,tr@t@ti); measures[name]=dict(ate=m.horn_rmse(lidar,t),ter=float(np.mean([x['translation_fraction'] for x in seg])*100),
                rer=float(np.mean([x['rotation_rad_per_m'] for x in seg])*180/np.pi*100),segments=len(seg))
        rows[s]=dict(metrics=measures,coarse_anchors=coarse,reconstruction_max_delta=maximum)
    r.save(BASE/'fine_graph_diagnosis.json',dict(utc=r.now(),post_hoc=True,not_a_promoted_arm=True,rows=rows,real_data_optimizer_calls=0))
    print({s:x['metrics'] for s,x in rows.items()},flush=True)

def run():
    left=1800-r.used(); assert left>0; signal.signal(signal.SIGALRM,lambda a,b:(_ for _ in ()).throw(TimeoutError('original LMB cap'))); signal.alarm(max(1,int(left)))
    ok=False; error=None; peak=0
    try:
        r.verify_bank(); paths=[Path(__file__),BASE/'DIAGNOSTIC_SCOPE.md']
        r.save(BASE/'DIAGNOSTIC_FREEZE.json',dict(utc=r.now(),sources={str(p):r.sha(p) for p in paths},bank_seal_sha256=r.sha(BASE/'bank_seal.json'),remaining_original_seconds=left))
        env=os.environ.copy(); env['CUDA_VISIBLE_DEVICES']=''
        p=subprocess.run([r.KISS,'-u','-B',__file__,'--native'],env=env,timeout=left-1); assert p.returncode==0
        peak=r.read(BASE/'supervision/diagnose/native_exit.json')['peak_RSS_bytes']; inspect_real(); r.cap(); ok=True
    except BaseException as e:
        error=repr(e); traceback.print_exc(); r.save(BASE/'FAILURE_diagnose.json',dict(utc=r.now(),error=error))
    finally:
        signal.alarm(0); r.save(BASE/'supervision/diagnose/child_exit.json',dict(utc=r.now(),success=ok,error=error,wall_seconds=time.monotonic()-START,
            peak_RSS_bytes=max(peak,resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024),GPU_calls=0))
    if not ok: sys.exit(1)
if __name__=='__main__':
    if '--native' in sys.argv:
        try:native()
        finally:r.save(BASE/'supervision/diagnose/native_exit.json',dict(utc=r.now(),wall_seconds=time.monotonic()-START,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024))
    else:
        assert sys.argv[1]=='diagnose'; run()
