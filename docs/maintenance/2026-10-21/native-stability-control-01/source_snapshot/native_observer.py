"""Uninstalled in-memory observer. Original arguments and native return objects forwarded."""
import hashlib, sys, time
import numpy as np
from capture_codec import describe


def array(value, role, multiset=False):
    a = np.asarray(value)
    kind = a.dtype.kind + str(a.dtype.itemsize)
    endian = 'na' if a.dtype.itemsize == 1 else ('little' if a.dtype.byteorder == '<' else 'big' if a.dtype.byteorder == '>' else sys.byteorder)
    body = a.tobytes(order='C')  # Never passed back to the original algorithm.
    result = describe(body, kind, list(a.shape), endian, list(a.strides), role)
    if multiset:
        if a.ndim != 2:
            raise ValueError('row multiset requires matrix')
        width = a.shape[1]*a.dtype.itemsize
        rows = [body[i:i+width] for i in range(0, len(body), width)] if width else []
        result['row_multiset_sha256'] = hashlib.sha256(b''.join(sorted(rows))).hexdigest()
    return result


def sample(value, role, prefix='value'):
    if value is None:
        return {prefix: describe(b'', 'u1', [0], 'na', [1], role, 'none')}
    if isinstance(value, (int, np.integer)):
        return {prefix: array(np.asarray(value, dtype=np.int64), role)}
    if isinstance(value, (float, np.floating)):
        return {prefix: array(np.asarray(value, dtype=np.float64), role)}
    if isinstance(value, dict):
        result = {prefix+'/id_order': array(np.asarray(list(value), dtype=np.int64), role)}
        for key, pose in value.items():
            result[prefix+'/pose/'+str(int(key))] = array(pose, role)
        return result
    if isinstance(value, tuple):
        result = {}
        for index, part in enumerate(value):
            result.update(sample(part, role, prefix+'/'+str(index)))
        return result
    if hasattr(value, 'number_of_inliers') and hasattr(value, 'pose'):
        return {prefix+'/source': array(np.asarray(int(value.source_id), dtype=np.int64), role),
                prefix+'/inliers': array(np.asarray(int(value.number_of_inliers), dtype=np.int64), role),
                prefix+'/pose': array(value.pose, role)}
    return {prefix: array(value, role)}


class Observer:
    def __init__(self, writer):
        self.writer = writer; self.counters = {}; self.snapshot_seconds = 0.; self.calls = 0

    def components(self, args, role):
        result = {}
        for index, value in enumerate(args):
            result.update(sample(value, role, 'arg'+str(index)))
        if not result:
            result = sample(None, role)
        return result

    def invoke(self, label, fn, args, inputs=None, outputs=None, kwargs=None):
        begin = time.perf_counter()
        before = inputs() if inputs else self.components(args, 'input')
        self.writer.append(label, 'before', before)
        self.snapshot_seconds += time.perf_counter()-begin
        self.calls += 1
        try:
            result = fn(*args, **(kwargs or {}))
        except BaseException as error:
            text = (type(error).__name__+':'+str(error)).encode()
            self.writer.append(label, 'exception', {'error': describe(text, 'u1', [len(text)], 'na', [1], 'output', 'exception')})
            raise
        begin = time.perf_counter()
        self.writer.append(label, 'after', outputs(result) if outputs else sample(result, 'output'))
        self.snapshot_seconds += time.perf_counter()-begin
        return result

    def proxy(self, value, kind, methods):
        index = self.counters.get(kind, 0); self.counters[kind] = index+1
        observer = self; label = kind+str(index)
        class Proxy:
            def __getattr__(self, name):
                original = getattr(value, name)
                if name not in methods:
                    return original
                def call(*args, **kwargs):
                    if kwargs:
                        raise RuntimeError('Unexpected native keyword boundary')
                    outputs = None
                    if name in {'_point_cloud','point_cloud'}:
                        outputs = lambda result: {'value': array(result, 'output', True)}
                    if name == '_per_voxel_point_and_normal':
                        def outputs(result):
                            points, normals = (np.asarray(x) for x in result)
                            recorded = sample(result, 'output')
                            recorded['paired_rows'] = array(np.concatenate([points, normals], axis=1), 'output', True)
                            return recorded
                    return observer.invoke(label+'.'+name, original, args, outputs=outputs)
                return call
        return Proxy()

    def install(self):
        from kiss_slam.voxel_map import VoxelMap
        from kiss_slam.pose_graph_optimizer import PoseGraphOptimizer
        from map_closures.map_closures import MapClosures
        import open3d as o3d
        observer = self
        voxel_init = VoxelMap.__init__
        def init_voxel(value, *args, **kwargs):
            voxel_init(value, *args, **kwargs)
            value.map = observer.proxy(value.map, 'voxel', {'_integrate_frame','_add_points','_point_cloud','_per_voxel_point_and_normal','_clear','_num_voxels'})
        VoxelMap.__init__ = init_voxel
        pgo_init = PoseGraphOptimizer.__init__
        def init_pgo(value, *args, **kwargs):
            pgo_init(value, *args, **kwargs)
            value.pgo = observer.proxy(value.pgo, 'pgo', {'_add_variable','_fix_variable','_add_factor','_optimize','_estimates'})
        PoseGraphOptimizer.__init__ = init_pgo
        detector_init = MapClosures.__init__
        def init_detector(value, *args, **kwargs):
            detector_init(value, *args, **kwargs)
            value._pipeline = observer.proxy(value._pipeline, 'detector', {'_GetBestClosure'})
        MapClosures.__init__ = init_detector
        original_icp = o3d.t.pipelines.registration.icp
        def icp(*args, **kwargs):
            if kwargs:
                raise RuntimeError('Unexpected ICP keyword boundary')
            def inputs():
                source, target = args[:2]
                result = dict(source_points=array(source.point.positions.numpy(), 'input'),
                              source_normals=array(source.point.normals.numpy(), 'input'),
                              target_points=array(target.point.positions.numpy(), 'input'),
                              target_normals=array(target.point.normals.numpy(), 'input'),
                              threshold=array(np.asarray(args[2]), 'input'),
                              initial_guess=array(args[3], 'input'))
                criteria = args[5]
                result['criteria'] = array(np.asarray([criteria.relative_fitness, criteria.relative_rmse, criteria.max_iteration], dtype=np.float64), 'input')
                return result
            def outputs(value):
                return dict(transform=array(value.transformation.numpy(), 'output'),
                            fitness=array(np.asarray(value.fitness), 'output'),
                            inlier_rmse=array(np.asarray(value.inlier_rmse), 'output'))
            return observer.invoke('ICP', original_icp, args, inputs, outputs)
        o3d.t.pipelines.registration.icp = icp

    def local_map(self, value):
        return self.proxy(value, 'odometry_map_public', {'update','clear','add_points','point_cloud'})
