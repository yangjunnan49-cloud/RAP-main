"""M2 focused regressions and direct official KITTI C++ crosscheck."""
import ast
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch
import numpy as np

ROOT = Path('/mnt/e/githouse/RAP-SLAM')
HOME = Path('/mnt/e/githouse/RAP-main')
sys.path[:0] = [str(ROOT), str(ROOT/'scripts')]
from rap_slam import real_dataset, odometry, pose_graph
from rap_slam.trajectory_protocol import kitti_drift, validate_ids, validate_stamps
import eval_paper_metrics as metrics
from eval_map_consistency import crispness, build_map

checks = []

def rejects(name, fn):
    try:
        fn()
    except (ValueError, RuntimeError):
        checks.append(name)
    else:
        raise AssertionError(f'{name}: did not reject')

def poses(n):
    p = np.tile(np.eye(4), (n, 1, 1))
    p[:, 0, 3] = np.arange(n) * 10.
    p[:, 1, 3] = np.sin(np.arange(n)/10.)
    return p

def main():
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=False)
    for rel in ['rap_slam/trajectory_protocol.py', 'rap_slam/real_dataset.py',
                'rap_slam/odometry.py', 'rap_slam/pose_graph.py',
                'scripts/eval_paper_metrics.py', 'scripts/run_pipeline.py',
                'scripts/eval_map_consistency.py']:
        ast.parse((ROOT/rel).read_text())
    checks.append('changed_source_AST')
    gt = poses(140)
    rejects('length_mismatch', lambda: metrics.evaluate_pair(gt, gt[:-1]))
    rejects('duplicate_ids', lambda: validate_ids([0, 1, 1]))
    rejects('out_of_order_ids', lambda: validate_ids([0, 2, 1]))
    rejects('fractional_ids', lambda: validate_ids([0., 1.2]))
    rejects('duplicate_stamps', lambda: validate_stamps([0, 0]))
    rejects('decreasing_stamps', lambda: validate_stamps([1, 0]))
    rejects('nonfinite_stamps', lambda: validate_stamps([0, np.nan]))
    rejects('live_empty_prefix', lambda: metrics.gt_for_live('kitti','00',0))
    rejects('live_segment_overrun', lambda: metrics.gt_for_live('poss','A',1420))
    line = poses(140); line[:, 1, 3] = 0
    exact = kitti_drift(line, line)
    assert exact['kitti_segment_records'][0]['last'] == 11
    assert exact['kitti_ter_pct'] == 0
    assert exact['kitti_segments'] == len(exact['kitti_segment_records']) > 8
    checks.append('strict_endpoint_and_real_segment_count')
    with tempfile.TemporaryDirectory() as temporary:
        tmp = Path(temporary)
        ds = tmp/'dataset'; scans = ds/'sequences/00/velodyne'
        scans.mkdir(parents=True); (ds/'poses').mkdir()
        np.savetxt(ds/'poses/00.txt', poses(6)[:, :3].reshape(6, 12))
        np.savetxt(scans.parent/'times.txt', np.arange(6)*.1)
        for i in [0, 2, 3, 4, 5]:
            np.array([[i, 2, 3, 1]], dtype=np.float32).tofile(scans/f'{i:06d}.bin')
        loaded = real_dataset.load_real_sequence(str(tmp), end=5, stride=2)
        assert loaded['source_frame_ids'] == [0, 2, 4]
        np.testing.assert_equal(loaded['gt_poses'], poses(6)[[0, 2, 4]])
        assert loaded['timestamps'] == [0., .2, .4]
        checks.append('stride_missing_unselected_frame_still_matches_GT')
        rejects('missing_requested_frame', lambda: real_dataset.load_real_sequence(str(tmp), end=5))
        rejects('zero_stride', lambda: real_dataset.load_scans(str(scans), stride=0))
        (tmp/'summary.json').write_text(json.dumps({'config': dict(real_root=str(tmp), real_seq='00', real_start=0, real_end=5, real_stride=2)}))
        np.testing.assert_equal(metrics.gt_from_summary(str(tmp)), poses(6)[[0,2,4]])
        checks.append('summary_stride_applied')
        (tmp/'source_frames.json').write_text(json.dumps({'source_frame_ids': [0,3,5], 'timestamps':[0,.3,.5]}))
        np.testing.assert_equal(metrics.gt_from_summary(str(tmp)), poses(6)[[0,3,5]])
        checks.append('persisted_ids_override_legacy_range')
        rows = np.c_[np.arange(4)*.1, poses(4)[:, :3, 3], np.tile([0,0,0,1],(4,1))]
        odom = tmp/'odom.txt'; mapped = tmp/'map.txt'
        np.savetxt(odom, rows); np.savetxt(mapped, rows)
        rejects('live_manifest_required', lambda: metrics.eval_live('probe', str(odom), str(mapped), 'kitti','00'))
        manifest = dict(source_frame_ids=[0,1,2,3], timestamps=rows[:,0].tolist())
        Path(str(odom)+'.frames.json').write_text(json.dumps(manifest))
        with patch.object(metrics, 'gt_for_live', return_value=poses(4)):
            result = metrics.eval_live('probe', str(odom), str(mapped), 'kitti','00')
            assert result['frame_binding'] == 'persisted_source_frame_ids'
            checks.append('live_manifest_timestamp_binding')
            rows[2,0] += .01; np.savetxt(mapped, rows)
            rejects('map_timestamp_mismatch', lambda: metrics.eval_live('probe', str(odom), str(mapped), 'kitti','00'))
        manifest['timestamps'][1] += .01
        Path(str(odom)+'.frames.json').write_text(json.dumps(manifest))
        rejects('source_timestamp_mismatch', lambda: metrics.eval_live('probe', str(odom), str(mapped),'kitti','00'))
    # Foreign observation lies beyond eight neighbors for a dense own scan.
    x = np.c_[np.r_[np.arange(10)*.001, .05], np.zeros((11,2))]
    labels = np.r_[np.zeros(10, dtype=int), 1]
    brute = np.array([min(1., np.linalg.norm(x[labels != lab] - p, axis=1).min()) for p,lab in zip(x,labels)])
    np.testing.assert_allclose(crispness(x,labels), [brute.mean(),np.quantile(brute,.95)], atol=1e-12)
    assert crispness(x[:2], np.zeros(2,dtype=int)) == (1.,1.)
    assert crispness(np.zeros((2,3)), np.array([0,1])) == (0.,0.)
    checks.append('exact_foreign_NN_dense_small_single_and_coincident')
    class Scans:
        def raw(self, idx):
            return np.array([[1.,2.,3.]])
    points, labs = build_map(Scans(), [0,1], [np.eye(4),np.eye(4)])
    assert len(points) == 2 and len(np.unique(labs)) == 2
    checks.append('map_voxel_preserves_foreign_observations')
    with patch.object(odometry, 'KissOdometry', side_effect=RuntimeError('injected')):
        rejects('KISS_failure_no_silent_fallback', lambda: odometry.run_odometry([np.zeros((3,3))]))
        class Fallback:
            backend_name = 'open3d-icp'
            def __init__(self, **kwargs): self.poses = []
            def register(self, points): self.poses.append(np.eye(4))
        with patch.object(odometry, 'Open3DICPOdometry', Fallback):
            p, backend = odometry.run_odometry([np.zeros((3,3))],allow_fallback=True)
            assert len(p)==1 and backend=='open3d-icp'
            checks.append('explicit_fallback_allowed')
    rejects('empty_odometry', lambda: odometry.run_odometry([]))
    optimized = pose_graph.optimize_pose_graph(list(poses(3)), [0,1,2], [], loop_clique_width=10)
    assert len(optimized) == 3
    checks.append('empty_loop_clique_optimizes')
    # Nonzero lever arm and changing orientation: verify conjugation after anchoring.
    tr = np.eye(4); tr[:3,3] = [.7,-.2,.5]
    tr[:3,:3] = [[0,-1,0],[1,0,0],[0,0,1]]
    cam = poses(20)
    for i,p in enumerate(cam):
        a = i*.03; p[:3,:3] = [[np.cos(a),-np.sin(a),0],[np.sin(a),np.cos(a),0],[0,0,1]]
    lidar = np.array([np.linalg.inv(tr) @ p @ tr for p in cam])
    recovered = np.array([tr @ p @ np.linalg.inv(tr) for p in lidar])
    np.testing.assert_allclose(recovered, cam, atol=1e-12)
    checks.append('camera_lidar_lever_arm_roundtrip')
    # Use the unmodified official C++ implementation behind a standalone harness.
    cpp = HOME/'docs/maintenance/2026-09-10/m2-evaluation/devkit/devkit/cpp'
    harness = out/'crosscheck.cpp'
    # The downloaded devkit main references an absent Mail.finalize method.
    # Keep its complete metric prefix byte-for-text unchanged; omit reporting/main.
    prefix = (cpp/'evaluate_odometry.cpp').read_text().split('void saveSequenceErrors')[0]
    harness.write_text(prefix + '\nint main(int argc,char**argv) { auto gt=loadPoses(argv[1]); auto est=loadPoses(argv[2]); auto d=trajectoryDistances(gt); auto e=calcSequenceErrors(gt,est); for(auto v:e) printf("%d %d %.12g %.12g %.12g %.12g\\n", v.first_frame,lastFrameFromSegmentLength(d,v.first_frame,v.len),v.len,v.t_err,v.r_err,v.speed); }\n')
    exe = out/'crosscheck'
    compilation = subprocess.run(['g++','-O2','-I',str(cpp),'-o',str(exe),str(harness),str(cpp/'matrix.cpp')], capture_output=True, text=True)
    (out/'compile.log').write_text(compilation.stderr)
    compilation.check_returncode()
    # Exact-distance fixture catches endpoint semantics; curved real path checks normal usage.
    fixtures = [('synthetic_exact', line, line.copy())]
    fixtures[0][2][:,0,3] *= 1.01
    d = ROOT/'output_prods/kitti06'
    real_gt = np.array(metrics.gt_from_summary(str(d)))
    real_est = np.array(metrics.load_kitti_format(str(d/'odom_poses.txt')))
    fixtures.append(('kitti06_lidar',real_gt,real_est))
    crosschecks=[]
    for name,g,e in fixtures:
        gf,ef = out/(name+'_gt.txt'),out/(name+'_est.txt')
        np.savetxt(gf,g[:,:3].reshape(-1,12)); np.savetxt(ef,e[:,:3].reshape(-1,12))
        output = subprocess.check_output([str(exe),str(gf),str(ef)],text=True)
        (out/(name+'_official_segments.txt')).write_text(output)
        from io import StringIO
        official = np.loadtxt(StringIO(output))
        current = kitti_drift(g,e)
        records = current['kitti_segment_records']
        python = np.array([[s['first'],s['last'],s['length_m'],s['translation_fraction'],s['rotation_rad_per_m'],s['speed_mps']] for s in records])
        np.testing.assert_array_equal(python[:,:3],official[:,:3])
        np.testing.assert_allclose(python[:,3],official[:,3],atol=2e-7,rtol=2e-5)
        np.testing.assert_allclose(python[:,4],official[:,4],atol=4e-6,rtol=2e-3)
        np.testing.assert_allclose(python[:,5],official[:,5],atol=2e-5,rtol=2e-6)
        crosschecks.append(dict(fixture=name, segments=len(records), max_abs_error=np.max(abs(python-official),axis=0).tolist()))
    checks.append('official_CPP_segment_by_segment')
    (out/'validation.json').write_text(json.dumps(dict(status='passed',checks=checks,official_crosschecks=crosschecks),indent=2))
    print(json.dumps(dict(status='passed',checks=checks,official_crosschecks=crosschecks),indent=2))

if __name__ == '__main__':
    main()
