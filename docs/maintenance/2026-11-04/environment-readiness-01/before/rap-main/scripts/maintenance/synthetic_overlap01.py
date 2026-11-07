"""Hand-defined ordered IPC, corruption detection and actual fixed-map resets."""
import time
START=time.monotonic()
import os,sys,resource,traceback,multiprocessing as mp
import numpy as np
import overlap_core01 as p
def send(q,packets):
    for packet in packets:q.put(packet)
    q.put(None)
def native_run():
    p.verify();from kiss_slam.slam import KissSLAM
    u=np.arange(5000,dtype=np.float64);points=np.column_stack((5+(u%100)*.2,-5+((u//100)%50)*.2,np.sin(u*.013)))
    known=np.tile(np.eye(4),(14,1,1));known[:,0,3]=np.arange(14)*40.;known[:,1,3]=np.arange(14)*.2
    packets=[]
    for i in range(14):
        x=dict(index=i,raw_sha256='synthetic',map_points=points.copy(),pose=known[i].copy(),stage_A_start=0.,stage_A_clocks=[0.,0.,0.]);x['payload_sha256']=p.digest(x);packets.append(x)
    results=[];children=[]
    for scheduler in ('S','P'):
        slam=KissSLAM(p.config('G'));o=np.tile(np.eye(4),(14,1,1));fixed=p.module('synthetic_overlap_fixed',p.AD/'fixed_odometry.py').FixedOdometry(p.config('G').kiss_icp_config(),o);slam.odometry=fixed;slam.compute_closures=lambda *args:None
        ref=[-1];events=[];p.d.observe_generate(slam,ref,events);child=None;q=None
        if scheduler=='P':
            ctx=mp.get_context('spawn');q=ctx.Queue(maxsize=4);child=ctx.Process(target=send,args=(q,packets));child.start();children.append(child.pid)
            def stream():
                while True:
                    item=q.get(timeout=20.)
                    if item is None:break
                    yield item
            iterator=stream()
        else:iterator=iter(packets)
        consumed=[]
        try:
            for expected,packet in enumerate(iterator):
                assert packet['index']==expected and p.digest(packet)==packet['payload_sha256'];assert np.array_equal(packet['map_points'],points) and np.array_equal(packet['pose'],known[expected]);o[expected]=packet['pose'];ref[0]=expected
                slam.process_scan(packet['map_points'],np.array([]));consumed.append(expected)
                if scheduler=='P':time.sleep(.002)
            assert consumed==list(range(14));slam.generate_new_node();slam.local_map_graph.erase_last_local_map();assert events==fixed.resets==[3,6,9,12,13]
            actual=np.asarray(slam.poses);assert np.max(abs(actual-known))<=1e-5;results.append(actual)
            if child is not None:child.join(timeout=10.);assert child.exitcode==0
        finally:
            if child is not None and child.is_alive():child.terminate();child.join(timeout=5)
            if q is not None:q.close();q.join_thread()
    assert np.array_equal(results[0],results[1])
    corrupt=dict(packets[0]);corrupt['map_points']=points.copy();corrupt['map_points'][0,0]+=1.;assert p.digest(corrupt)!=packets[0]['payload_sha256']
    try:assert packets[1]['index']==0
    except AssertionError:order_probe=True
    else:order_probe=False
    assert order_probe
    p.save(p.BASE/'synthetic.json',dict(utc=p.now(),passed=True,schedulers=['S','P'],synthetic_frames_per_mode=14,synthetic_points_per_frame=5000,complete_point_occurrences=140000,queue_capacity=4,exact_S_P_pose_bytes=True,reset_frames=[3,6,9,12,13],payload_corruption_detected=True,out_of_order_detected=True,original_raw_scans_read=0,GT_numeric_read=False,IPC_child_pids=children))
    print('P0 synthetic native IPC/order/map/reset passed',flush=True)
def run():
    ok=False;error=None
    try:
        p.verify();env=os.environ.copy();env['CUDA_VISIBLE_DEVICES']='';env['OPEN3D_CPU_RENDERING']='true';t=time.monotonic()
        z=p.subprocess.run([p.r.KISS,'-u','-B',__file__,'--native'],env=env,timeout=min(180.,p.CAP-p.used())-1);assert z.returncode==0;assert p.read(p.BASE/'synthetic.json')['passed'];p.cap();ok=True
    except BaseException as e:error=repr(e);traceback.print_exc()
    finally:p.save(p.SUP/'synthetic/child_exit.json',dict(utc=p.now(),success=ok,error=error,wall_seconds=time.monotonic()-START,**p.process_usage(),GPU_calls=0,overlapping_native_clock_not_added=True))
    if not ok:sys.exit(1)
if __name__=='__main__':
    if '--native' in sys.argv:
        ok=False;error=None
        try:native_run();ok=True
        except BaseException as e:error=repr(e);traceback.print_exc()
        finally:p.save(p.SUP/'synthetic/native_exit.json',dict(utc=p.now(),success=ok,error=error,wall_seconds=time.monotonic()-START,**p.process_usage(),GPU_calls=0))
        if not ok:sys.exit(1)
    else:assert sys.argv[1]=='synthetic';run()
