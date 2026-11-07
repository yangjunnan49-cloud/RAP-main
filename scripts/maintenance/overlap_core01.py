"""P0 fixed bounded FIFO engineering; all-six native/G serial/parallel controls."""
import time
START=time.monotonic()
import os,sys,json,hashlib,resource,signal,subprocess,traceback,multiprocessing as mp,queue
from pathlib import Path
import numpy as np
import raw_input_system06 as d
BASE=d.r.MAIN/'docs/maintenance/2026-10-21/runtime-overlap-01';SUP=BASE/'supervision';CAP=9000
r=d.r;old=d.old;AD=d.AD;FINE=d.FINE;module=d.module;read=d.read;save=d.save;sha=d.sha;now=d.now;config=d.config;proper_one=d.proper_one
QUEUE_CAPACITY=4
def used():
    return sum(max([read(folder/name)['wall_seconds'] for name in ('child_exit.json','exit.json','wrapper_exit.json') if (folder/name).exists()]+[0.]) for folder in SUP.iterdir() if folder.is_dir())
def cap():
    assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024<=4*2**30
    assert sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file())<=256*2**20
def guard():
    import uuid
    nonce=uuid.uuid4().hex;begin=time.monotonic();requests=SUP/'guard_requests06';requests.mkdir(exist_ok=True)
    target=requests/(nonce+'.json');temporary=requests/(nonce+'.tmp');save(temporary,dict(nonce=nonce,utc=now()));os.replace(temporary,target)
    while time.monotonic()-begin<=2.:
        response=SUP/'guard_responses06'/(nonce+'.json')
        if response.exists():
            data=read(response)
            if data['nonce']==nonce:
                elapsed=time.monotonic()-begin;assert 0<=elapsed<=2.;assert data['headroom_bytes']>=12*2**30
                return dict(utc=now(),observed_utc=data['utc'],roundtrip_seconds=elapsed,nonce=nonce,headroom_bytes=data['headroom_bytes'])
        time.sleep(.01)
    raise TimeoutError('Original2s memory challenge failed')
def verify():
    d.verify()
    for p,h in read(BASE/'EXECUTION_FREEZE.json')['files'].items():assert sha(p)==h,p
def digest(packet):
    points=packet['map_points'];pose=packet['pose'];assert points.dtype==np.float64 and points.ndim==2 and points.shape[1]==3 and points.flags.c_contiguous
    h=hashlib.sha256();h.update(f"{packet['index']} {packet['raw_sha256']} {points.dtype.str} {points.shape}\n".encode());h.update(points.tobytes(order='C'))
    if pose is None:h.update(b'NO_EXTERNAL_POSE')
    else:
        assert pose.shape==(4,4) and pose.dtype==np.float64 and np.isfinite(pose).all();h.update(pose.tobytes(order='C'))
    return h.digest()
def packets(cell):
    from rap_slam.real_dataset import kitti_vertical_correction
    from legacy_f32_correction import legacy_f32_correction
    s=cell['sequence'];m=cell['mode'];f=read(d.BASE/'freeze.json');n=f['counts'][s]
    if m=='G':
        from rap_slam.odometry import KissOdometry
        front=KissOdometry(max_range=80.,min_range=1.5,voxel_size=.8,deskew=False);prepared_reference=read(d.BASE/'original_prepared_reference.json')['rows'][s]
    else:from kiss_icp.pybind import kiss_icp_pybind as binding
    for i in range(n):
        start=time.perf_counter();path=r.raw(s,i);body=path.read_bytes();h=hashlib.sha256(body).hexdigest();assert h==f['raw_files'][str(path)];after_read=time.perf_counter()
        raw=np.frombuffer(body,np.float32).reshape(-1,4)[:,:3];assert np.isfinite(raw).all()
        if m=='G':
            distance=np.linalg.norm(raw,axis=1);front_points=legacy_f32_correction(raw[distance>=1.5].copy()).astype(np.float32);map_points=kitti_vertical_correction(raw[(distance>=1.5)&(distance<=80.)].copy())
            point_reference=prepared_reference[i];assert len(front_points)==point_reference['points'] and hashlib.sha256(front_points.tobytes(order='C')).hexdigest()==point_reference['prepared_sha256']
        else:map_points=np.asarray(binding._correct_kitti_scan(binding._Vector3dVector(raw.astype(np.float64))))
        after_preprocess=time.perf_counter();pose=proper_one(front.register(front_points).copy()) if m=='G' else None;after_front=time.perf_counter()
        packet=dict(index=i,raw_sha256=h,map_points=np.ascontiguousarray(map_points,dtype=np.float64),pose=pose,stage_A_start=start,stage_A_clocks=[after_read-start,after_preprocess-after_read,after_front-after_preprocess])
        packet['payload_sha256']=digest(packet)
        if i%250==0:cap()
        yield packet
def process_usage():
    u=resource.getrusage(resource.RUSAGE_SELF)
    threads=next(int(line.split(':')[1]) for line in Path('/proc/self/status').read_text().splitlines() if line.startswith('Threads:'))
    return dict(peak_RSS_bytes=u.ru_maxrss*1024,user_CPU_seconds=u.ru_utime,system_CPU_seconds=u.ru_stime,observed_threads_at_receipt=threads,whole_native_tree_peak='UNKNOWN')
def producer(q,cell,dest):
    begin=time.monotonic();ok=False;error=None;hashes=[];blocking=[]
    try:
        verify()
        for packet in packets(cell):
            hashes.append(np.frombuffer(packet['payload_sha256'],dtype=np.uint8).copy());t=time.monotonic();q.put(('packet',packet));blocking.append(time.monotonic()-t)
        q.put(('end',len(hashes)));np.save(dest/'producer_hashes.npy',np.asarray(hashes));np.save(dest/'producer_blocking.npy',np.asarray(blocking));cap();ok=True
    except BaseException as e:
        error=repr(e);traceback.print_exc()
        try:q.put(('error',error),timeout=1.)
        except Exception:pass
    finally:save(dest/'producer_exit.json',dict(utc=now(),success=ok,error=error,wall_seconds=time.monotonic()-begin,**process_usage(),clock_overlaps_worker=True))
    if not ok:raise SystemExit(1)
def cleanup_child(p,identity):
    if p is None or not p.is_alive():return
    proc=Path(f'/proc/{p.pid}');ticks=int((proc/'stat').read_text().rsplit(')',1)[1].split()[19]);assert ticks==identity['start_ticks'] and os.getpgid(p.pid)==identity['process_group']
    p.terminate();p.join(timeout=5)
    if p.is_alive():p.kill();p.join(timeout=5)
def worker(cell):
    verify();from kiss_slam.slam import KissSLAM
    s=cell['sequence'];m=cell['mode'];key=cell['key'];n=read(d.BASE/'freeze.json')['counts'][s];dest=BASE/'bank'/key;dest.mkdir()
    c=config(m);slam=KissSLAM(c);recorder=r.Recorder(slam.closer);slam.closer=recorder;o=np.tile(np.eye(4),(n,1,1));fixed=None
    if m=='G':fixed_module=module('overlap_fixed_odometry',AD/'fixed_odometry.py');fixed=fixed_module.FixedOdometry(c.kiss_icp_config(),o);slam.odometry=fixed
    membership={};chain=hashlib.sha256();timing=[];pipeline=[];hashes=[];frame_ref=[-1];reset_events=[];d.observe_generate(slam,frame_ref,reset_events)
    p=None;q=None;identity=None;begin=time.monotonic();generated_hashes=[]
    try:
        if cell['scheduler']=='P':
            launch=guard();context=mp.get_context('spawn');q=context.Queue(maxsize=QUEUE_CAPACITY);p=context.Process(target=producer,args=(q,cell,dest));p.start()
            stat=Path(f'/proc/{p.pid}/stat').read_text();identity=dict(pid=p.pid,start_ticks=int(stat.rsplit(')',1)[1].split()[19]),process_group=os.getpgid(p.pid),created_by_this_worker=True)
            save(dest/'producer_ownership.json',dict(**identity,launch_guard=launch))
            def stream():
                count=0
                while True:
                    kind,value=q.get(timeout=60.)
                    if kind=='end':assert count==value==n;break
                    if kind=='error':raise RuntimeError(('producer failed',value))
                    assert kind=='packet';count+=1;yield value
            iterator=stream()
        else:iterator=packets(cell)
        prior=time.perf_counter()
        for expected,packet in enumerate(iterator):
            received=time.perf_counter();i=packet['index'];assert i==expected and i<n;frame_ref[0]=i
            assert digest(packet)==packet['payload_sha256'];hashes.append(np.frombuffer(packet['payload_sha256'],dtype=np.uint8).copy())
            chain.update(f"{i} {packet['raw_sha256']}\n".encode());map_points=packet['map_points'];timestamps=np.array([])
            if m=='G':o[i]=packet['pose']
            verified=time.perf_counter();mid=slam.local_map_graph.last_id;membership.setdefault(str(mid),[]).append(i);slam.process_scan(map_points,timestamps);after_map=time.perf_counter()
            a=packet['stage_A_clocks'];timing.append(a+[after_map-verified,sum(a)+after_map-verified]);pipeline.append([received-prior,verified-received,after_map-packet['stage_A_start']]);prior=after_map
            if cell['scheduler']=='S':generated_hashes.append(hashes[-1])
            if i%250==0:cap();print(key,i,'maps',slam.local_map_graph.last_id,'loops',len(slam.closures),flush=True)
        assert len(hashes)==n
        if p is not None:
            p.join(timeout=10.);assert not p.is_alive() and p.exitcode==0;assert read(dest/'producer_exit.json')['success'];assert np.array_equal(np.load(dest/'producer_hashes.npy'),np.asarray(hashes))
        else:
            assert np.array_equal(np.asarray(generated_hashes),np.asarray(hashes));np.save(dest/'producer_hashes.npy',np.asarray(generated_hashes));save(dest/'producer_exit.json',dict(utc=now(),success=True,same_process=True,wall_seconds=None,**process_usage(),clock_included_in_worker=True))
        np.save(dest/'consumer_hashes.npy',np.asarray(hashes));np.save(dest/'pipeline_timing.npy',np.asarray(pipeline))
        from overlap_finalize01 import finish
        finish(cell,s,m,key,n,dest,c,slam,recorder,membership,o,fixed,reset_events,begin,timing,chain)
        save(dest/'pipeline.json',dict(utc=now(),scheduler=cell['scheduler'],queue_capacity=QUEUE_CAPACITY if p is not None else None,packet_count=n,all_packet_bytes_and_order_verified=True,stage_A_fresh_G_odometry=True,
            timing_frame_total_is_service_sum_not_parallel_wall=True,actual_native_core_count_UNKNOWN=True,no_seed_or_config_changes=True,producer_receipt=read(dest/'producer_exit.json'),**process_usage()))
    finally:
        cleanup_child(p,identity)
        if q is not None:q.close();q.join_thread()
def run_bank():
    verify();assert read(BASE/'synthetic.json')['passed'];(BASE/'bank').mkdir();left=CAP-used();begin=time.monotonic()
    for cell in read(BASE/'schedule.json')['cells']:
        launch=guard();dest=SUP/'run'/cell['key'];dest.mkdir();save(dest/'launch_guard.json',launch);t=time.monotonic()
        env=os.environ.copy();env['CUDA_VISIBLE_DEVICES']='';env['OPEN3D_CPU_RENDERING']='true';env['PYTHONDONTWRITEBYTECODE']='1'
        with (dest/'stdout.log').open('x') as out,(dest/'stderr.log').open('x') as err:p=subprocess.run([r.KISS,'-u','-B',__file__,'--worker',json.dumps(cell)],env=env,stdout=out,stderr=err,timeout=left-(time.monotonic()-begin)-1)
        save(dest/'controller_exit.json',dict(utc=now(),wall_seconds=time.monotonic()-t,returncode=p.returncode));assert p.returncode==0 and read(BASE/'bank'/cell['key']/'worker_exit.json')['success'];cap();print('sealed',cell['key'],flush=True)
    save(BASE/'bank_seal.json',dict(utc=now(),cells=72,files={str(p.relative_to(BASE/'bank')):sha(p) for p in sorted((BASE/'bank').rglob('*')) if p.is_file()},GT_numeric_read=False))
    print('ALL72 predictions sealed before equivalence/GT',flush=True)
def run(stage,native=False):
    left=CAP-used();assert left>1;signal.signal(signal.SIGALRM,lambda a,b:(_ for _ in ()).throw(TimeoutError('P0 cumulative cap')));signal.alarm(max(1,int(left)));ok=False;error=None
    try:
        assert stage=='run';run_bank();cap();ok=True
    except BaseException as e:error=repr(e);traceback.print_exc();save(BASE/f'FAILURE_{stage}.json',dict(utc=now(),error=error))
    finally:signal.alarm(0);save(SUP/stage/'child_exit.json',dict(utc=now(),success=ok,error=error,wall_seconds=time.monotonic()-START,**process_usage(),GPU_calls=0))
    if not ok:sys.exit(1)
if __name__=='__main__':
    if '--worker' in sys.argv:
        cell=json.loads(sys.argv[-1]);dest=BASE/'bank'/cell['key'];ok=False;error=None
        try:worker(cell);ok=True
        except BaseException as e:error=repr(e);traceback.print_exc()
        finally:dest.mkdir(exist_ok=True);save(dest/'worker_exit.json',dict(utc=now(),success=ok,error=error,wall_seconds=time.monotonic()-START,**process_usage(),GPU_calls=0))
        if not ok:sys.exit(1)
    else:run(sys.argv[1])
