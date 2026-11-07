"""N1 stages; source-bound fresh frontend, then two fixed-input serial coarse replays."""
import ast, hashlib, importlib, inspect, json, os, resource, sys, time
from pathlib import Path
from bindings import ROOT, OUT, S1, core, freeze_originals, read, save, sha, verify_originals
from capture_codec import Writer, describe, digest, read_verified
folder = Path(sys.argv[1]); stage = sys.argv[2]; start = time.monotonic()


def cap():
    assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024 <= 4*2**30, 'worker_RSS_cap'
    assert sum(p.stat().st_size for root in (ROOT, OUT) for p in root.rglob('*') if p.is_file()) <= 8*2**20, 'N1_growth_cap'


def import_core():
    c = core()
    for key, value in read(S1/'freeze.json')['relevant_env'].items():
        assert os.environ.get(key) == value, 'effective_env:'+key
    c.cap = cap  # Route resource checks only; no original numerical function is changed.
    return c


def runtime_bindings():
    libraries = {}
    for line in Path('/proc/self/maps').read_text().splitlines():
        parts = line.split(None, 5)
        if len(parts) == 6 and parts[5].startswith('/'):
            p = Path(parts[5])
            if p.is_file() and ('.so' in p.name or p.name.startswith('python')):
                libraries[str(p)] = sha(p)
    return dict(libraries=libraries, environment={key:os.environ.get(key) for key in
        ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','CUDA_VISIBLE_DEVICES','OPEN3D_CPU_RENDERING')})


def verify_runtime():
    binding = read(OUT/'RUNTIME_BINDING.json')
    for name, expected in binding['libraries'].items():
        assert sha(name) == expected, 'runtime_library_changed:'+name
    assert binding['environment'] == {key:os.environ.get(key) for key in binding['environment']}


def preflight():
    freeze_originals(); c = import_core()
    import numpy as np
    import open3d as o3d
    import rap_slam.odometry
    from native_observer import Observer, array
    from kiss_slam.voxel_map import VoxelMap
    from kiss_slam.pose_graph_optimizer import PoseGraphOptimizer
    from map_closures.map_closures import MapClosures
    checks = []
    def expect(name, condition):
        assert condition, name
        checks.append(dict(name=name, passed=True))
    points = np.asarray([[1.,2.,3.],[4.,5.,6.]], dtype=np.float32)
    a, b = array(points, 'output', True), array(points[::-1], 'output', True)
    expect('ordered_bytes_keep_row_order', a['sha256'] != b['sha256'])
    expect('secondary_multiset_preserves_duplicates_and_exact_row_bytes', a['row_multiset_sha256'] == b['row_multiset_sha256'])
    expect('strides_and_dtype_are_bound', a['strides'] != b['strides'] and a['dtype'] == 'f4')
    frame = [-1]; writer = Writer(folder/'probe_events.jsonl', {'kind':'synthetic-interface'}, frame)
    observer = Observer(writer)
    token = object(); calls = []; original = points.tobytes()
    def fn(value):
        calls.append(value); return token
    returned = observer.invoke('identity', fn, (points,), outputs=lambda _: {'none': describe(b'', 'u1', [0], 'na', [1], 'output')})
    expect('stub_argument_identity', calls[0] is points)
    expect('stub_return_identity', returned is token)
    expect('stub_exactly_one_call', len(calls) == 1)
    expect('stub_no_array_mutation', points.tobytes() == original)
    error = ValueError('same-error'); invoked = []
    def raises(value):
        invoked.append(value); raise error
    try:
        observer.invoke('exception', raises, (points,))
    except ValueError as caught:
        expect('stub_original_exception_identity', caught is error)
    expect('stub_exception_no_retry', len(invoked) == 1)
    observer.install()
    native_points = np.asarray([[x*.05,y*.05,z*.05] for x in range(4) for y in range(4) for z in range(4)], dtype=np.float64)
    vm = VoxelMap(.1); vm.add_points(native_points)
    cloud = vm.point_cloud(); normals = vm.open3d_pcd_with_normals()
    expect('native_vector_and_point_normal_capture', cloud.ndim == 2 and normals.point.positions.shape[1] == 3)
    vm.integrate_frame(native_points, np.eye(4)); vm.num_voxels(); vm.clear()
    config = c.config('G'); pgo = PoseGraphOptimizer(config.pose_graph_optimizer)
    pgo.add_variable(0,np.eye(4)); pgo.add_variable(1,np.eye(4)); pgo.fix_variable(0)
    pgo.add_factor(1,0,np.eye(4),np.eye(6)); pgo.optimize(); estimates = pgo.estimates()
    expect('native_pgo_dict_capture', set(estimates) == {0,1})
    detector = MapClosures(config.loop_closer.detector)
    expect('native_detector_entry_present', callable(detector._pipeline._GetBestClosure))
    plane_points=[]; plane_normals=[]
    for axis in range(3):
        for i in range(4):
            for j in range(4):
                value=[0.,0.,0.];normal=[0.,0.,0.];value[axis]=1.;normal[axis]=1.
                value[(axis+1)%3]=i*.2;value[(axis+2)%3]=j*.2
                plane_points.append(value);plane_normals.append(normal)
    pcd=o3d.t.geometry.PointCloud()
    pcd.point.positions=o3d.core.Tensor(np.asarray(plane_points,dtype=np.float32))
    pcd.point.normals=o3d.core.Tensor(np.asarray(plane_normals,dtype=np.float32))
    result=o3d.t.pipelines.registration.icp(pcd,pcd,.8,np.eye(4),
        o3d.t.pipelines.registration.TransformationEstimationPointToPlane(),
        o3d.t.pipelines.registration.ICPConvergenceCriteria(relative_rmse=1e-4))
    expect('native_ICP_interface_capture', result.transformation.numpy().shape == (4,4))
    writer.close()
    rows=list(read_verified(folder/'probe_events.jsonl'))
    expect('probe_event_chain_verified', len(rows) > 20)
    # The exact original G mapping expression must be present in the replay helper.
    old_ast=ast.parse(inspect.getsource(c.packets)); new_ast=ast.parse(inspect.getsource(map_input))
    def expression(tree,name):
        return [ast.dump(node.value,include_attributes=False) for node in ast.walk(tree)
                if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in node.targets)]
    expect('mapping_range_and_correction_expression_match', expression(old_ast,'map_points')[0] == expression(new_ast,'map_points')[0])
    expect('mapping_distance_expression_match', expression(old_ast,'distance')[0] == expression(new_ast,'distance')[0])
    save(OUT/'RUNTIME_BINDING.json', runtime_bindings())
    save(OUT/'PREFLIGHT.json', dict(passed=True,checks=checks,config=config.model_dump(),
        original_input_bindings_sha256=sha(OUT/'INPUT_BINDINGS.json'),runtime_binding_sha256=sha(OUT/'RUNTIME_BINDING.json'),
        no_raw=True,no_GT=True,native_interface_probes_only=True))


def map_input(raw):
    import numpy as np
    from rap_slam.real_dataset import kitti_vertical_correction
    distance=np.linalg.norm(raw,axis=1)
    map_points=kitti_vertical_correction(raw[(distance>=1.5)&(distance<=80.)].copy())
    return np.ascontiguousarray(map_points,dtype=np.float64)


def frontend():
    verify_originals(); c=import_core(); verify_runtime()
    import numpy as np
    assert read(OUT/'PREFLIGHT.json')['passed']
    bank=OUT/'frontend'; bank.mkdir()
    poses=[];rows=[];reference=read(S1/'original_prepared_reference.json')['rows']['06']
    for packet in c.packets(dict(sequence='06',mode='G')):
        i=packet['index']; poses.append(packet['pose'].copy())
        rows.append(dict(index=i,raw_sha256=packet['raw_sha256'],map_sha256=hashlib.sha256(packet['map_points'].tobytes(order='C')).hexdigest(),
                         frontend_prepared_sha256=reference[i]['prepared_sha256']))
        if i%200 == 0:
            cap(); print('FRONT',i,flush=True)
    assert len(rows)==1101
    poses=np.asarray(poses);assert poses.shape==(1101,4,4) and np.isfinite(poses).all()
    np.save(bank/'poses.npy',poses);save(bank/'packets.json',rows)
    save(bank/'SEAL.json',dict(files={p.name:sha(p) for p in bank.iterdir()},count=1101,
         generated_fresh_once=True,original_prepared_checks_inside_frozen_packet_generator=True,GT_reads=0))


def native():
    verify_originals(); c=import_core(); verify_runtime()
    import numpy as np
    from native_observer import Observer, array
    from kiss_slam.slam import KissSLAM
    bank=OUT/'frontend';seal=read(bank/'SEAL.json')
    for name,expected in seal['files'].items():assert sha(bank/name)==expected
    poses=np.load(bank/'poses.npy');reference=read(bank/'packets.json');frame=[-1]
    binding=dict(input_bindings=sha(OUT/'INPUT_BINDINGS.json'),runtime=sha(OUT/'RUNTIME_BINDING.json'),
                 frontend=sha(bank/'SEAL.json'),config=sha(S1/'config_G.json'),recorder=sha(ROOT/'native_observer.py'))
    writer=Writer(folder/'events.jsonl',binding,frame);observer=Observer(writer);observer.install()
    config=c.config('G');slam=KissSLAM(config)
    fixed_module=c.module('n1_fixed_odometry',c.AD/'fixed_odometry.py')
    fixed=fixed_module.FixedOdometry(config.kiss_icp_config(),poses)
    fixed.local_map=observer.local_map(fixed.local_map);slam.odometry=fixed
    resets=[];previous_id=0;packet_chain=hashlib.sha256()
    frozen=read(S1/'freeze.json')
    for i,item in enumerate(reference):
        path=c.r.raw('06',i);body=path.read_bytes();raw_hash=hashlib.sha256(body).hexdigest()
        assert raw_hash==item['raw_sha256']==frozen['raw_files'][str(path)]
        raw=np.frombuffer(body,np.float32).reshape(-1,4)[:,:3];assert np.isfinite(raw).all()
        points=map_input(raw);assert hashlib.sha256(points.tobytes(order='C')).hexdigest()==item['map_sha256']
        frame[0]=i
        writer.append('packet','input',dict(points=array(points,'prepared'),frontend=array(poses[i],'derived')))
        packet_chain.update(bytes.fromhex(item['map_sha256']));packet_chain.update(poses[i].tobytes(order='C'))
        slam.process_scan(points,np.array([]))
        if slam.local_map_graph.last_id != previous_id:
            resets.append(i);previous_id=slam.local_map_graph.last_id
        if i%200 == 0:
            cap();print(stage,i,'maps',previous_id,'loops',len(slam.closures),flush=True)
    output=np.asarray(slam.poses)
    assert output.shape==(1101,4,4) and np.isfinite(output).all()
    np.save(folder/'coarse_poses.npy',output)
    np.save(folder/'coarse_keyposes.npy',np.asarray(slam.get_keyposes()))
    save(folder/'COARSE_SUMMARY.json',dict(frame_calls=1101,loops=slam.closures,resets=resets,
        fixed_resets=fixed.resets,max_relative_error=fixed.max_relative_error,
        packet_chain_sha256=packet_chain.hexdigest(),frontend_seal_sha256=sha(bank/'SEAL.json'),
        observer_calls=observer.calls,snapshot_seconds=observer.snapshot_seconds,event_chain=writer.close(),
        fine_graph_calls=0,GT_reads=0,new_RAP_calls=0,global_native_state='UNKNOWN'))


def analysis():
    import itertools
    import numpy as np
    first=None;count=[0,0];primary_diffs=0;examples=[]
    left=folder.parent/'native1';right=folder.parent/'native2'
    for index,pair in enumerate(itertools.zip_longest(read_verified(left/'events.jsonl'),read_verified(right/'events.jsonl'))):
        l,r=pair
        count[0]+=l is not None;count[1]+=r is not None
        if l is None or r is None:
            if first is None:first=dict(index=index,kind='event_count_difference')
            continue
        assert l[0]==r[0], 'incomparable_event_bindings'
        if l[1] != r[1]:
            primary_diffs+=1
            if first is None:first=dict(index=index,left=l[1],right=r[1])
            if len(examples)<5:examples.append(dict(index=index,left=l[1],right=r[1]))
    a=np.load(left/'coarse_poses.npy');b=np.load(right/'coarse_poses.npy')
    sl=read(left/'COARSE_SUMMARY.json');sr=read(right/'COARSE_SUMMARY.json')
    assert sl['packet_chain_sha256']==sr['packet_chain_sha256'], 'packet_bytes_not_equal'
    save(OUT/'RESULTS.json',dict(complete=True,event_counts=count,event_content_differences=primary_diffs,
        first_observed_difference=first,first_examples=examples,
        coarse_translation_element_max=float(np.max(abs(a[:,:3,3]-b[:,:3,3]))),
        coarse_rotation_element_max=float(np.max(abs(a[:,:3,:3]-b[:,:3,:3]))),
        exact_coarse_poses=np.array_equal(a,b),same_resets=sl['resets']==sr['resets'],same_closure_endpoints=sl['loops']==sr['loops'],
        packet_chain_sha256=sl['packet_chain_sha256'],same_packet_bytes=True,
        hidden_state='UNKNOWN',causal_mechanism='UNKNOWN',GT_reads=0,new_RAP_calls=0,
        original_P0_qualification='CLOSED_EQUIVALENCE_FAIL_UNCHANGED'))


ok=False;error=None
try:
    {'preflight':preflight,'front':frontend,'native1':native,'native2':native,'analysis':analysis}[stage]()
    cap();ok=True
except BaseException as caught:
    error=repr(caught)
    import traceback;traceback.print_exc()
finally:
    save(folder/'worker_exit.json',dict(success=ok,error=error,stage=stage,elapsed=time.monotonic()-start,
        max_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
        GT_reads=0,new_RAP_calls=0))
sys.exit(0 if ok else 2)
