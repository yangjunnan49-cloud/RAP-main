"""Execute predeclared O2 on explicitly bound, fresh frozen frontends."""
import hashlib
import json
import os
from pathlib import Path
import sys
import time
from collections import Counter
import numpy as np

ROOT = Path('/mnt/e/githouse/RAP-SLAM')
HOME = Path('/mnt/e/githouse/RAP-main')
BASE = HOME/'docs/maintenance/2026-09-13'
sys.path[:0] = [str(ROOT), str(ROOT/'scripts')]
from replay_core_candidates import LazyScans
from rap_slam import scan_context, loop_closure, pose_graph, sequence
from rap_slam.verification_log import VerificationLog
from rap_slam.measurement import transform_label
import eval_paper_metrics as metrics


def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for block in iter(lambda: f.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def save(p, value):
    p.write_text(json.dumps(value, indent=2, allow_nan=False))


def main():
    out = BASE/'optimization-o2-01'
    out.mkdir(exist_ok=False)
    (out/'INCOMPLETE').write_text('O2 execution and validation pending\n')
    sources = [Path(__file__), BASE/'O2_BUDGET_PROTOCOL.md']
    sources += list((ROOT/'rap_slam').glob('*.py'))
    sources += [ROOT/'scripts'/n for n in ['eval_paper_metrics.py', 'replay_core_candidates.py']]
    sources += list((HOME/'rectified_point_flow').rglob('*.py'))
    sources += list((HOME/'config').rglob('*.yaml'))
    sources += [HOME/'weights'/n for n in ['rap_model_12.ckpt', 'mini_spinnet_t.pth']]
    identities = {str(p): sha(p) for p in sources}
    save(out/'source_manifest.json', identities)
    import torch
    from rap_slam.rap_backend import RAPBackend
    start = time.perf_counter()
    backend = RAPBackend(sampling_steps=5, voxel_size=.4, max_points_per_scan=4000, seed=42)
    startup = time.perf_counter()-start
    rows = []
    for name in ['poss', 'kitti06', 'kitti05', 'kitti00']:
        parent = HOME/'docs/maintenance/2026-09-11'/('full-'+name+'-01')
        src = parent/'pipeline'
        assert not (parent/'INCOMPLETE').exists() and not (src/'INCOMPLETE').exists()
        dest = out/name
        dest.mkdir()
        cfg = json.loads((src/'summary.json').read_text())['config']
        frames = json.loads((src/'source_frames.json').read_text())
        ids = np.asarray(frames['source_frame_ids'])
        np.testing.assert_array_equal(ids, np.arange(cfg['real_start'], cfg['real_end']+1, cfg['real_stride']))
        scans = LazyScans([Path(p) for p in frames['scan_files']])
        assert all(p.stem == f'{i:06d}' for p,i in zip(scans.paths,ids))
        odom = metrics.load_kitti_format(str(src/'odom_poses.txt'))
        gt = metrics.gt_from_summary(str(src))
        kfs = json.loads((src/'keyframes.json').read_text())
        assert len(odom) == len(gt) == len(ids) == len(scans.paths)
        oldhash = json.loads((parent/'input_manifest.json').read_text())
        for p in sources:
            if str(p) in oldhash:
                assert identities[str(p)] == oldhash[str(p)], str(p)
        tracked = [src/n for n in ['summary.json','source_frames.json','odom_poses.txt','keyframes.json','verification_measurements.jsonl']]
        tracked += [parent/'paper_metrics.json', parent/'input_manifest.json']
        data = Path(cfg['real_root'])/'dataset'
        tracked += [data/'poses'/(cfg['real_seq']+'.txt'), data/'sequences'/cfg['real_seq']/'calib.txt']
        for p in tracked:
            identities[str(p)] = sha(p)
            if str(p) in oldhash:
                assert identities[str(p)] == oldhash[str(p)]
        save(dest/'source_frames.json', frames)
        start = time.perf_counter()
        descriptors = scan_context.build_descriptors(scans, kfs, n_rings=20, n_sectors=60, max_radius=80)
        descriptor_seconds = time.perf_counter()-start
        arms = []
        for budget in [12, 40]:
            arm = dest/str(budget)
            arm.mkdir()
            start = time.perf_counter()
            prox = loop_closure.find_candidates(odom,kfs,dist_thresh=15,min_separation=200,max_candidates=budget)
            sc = scan_context.find_candidates_sc(descriptors,kfs,min_separation=200,dist_thresh=.25,shortlist=10,max_candidates=budget)
            pairs = loop_closure.merge_candidates(prox,sc,max_candidates=budget)
            retrieval_seconds = time.perf_counter()-start
            save(arm/'candidates.json', dict(proximity=prox,scan_context=sc,merged=pairs))
            print(f'{name} budget {budget}: verifying {len(pairs)} pairs', flush=True)
            log = VerificationLog(arm/'verification_measurements.jsonl',f'o2-01-{name}-{budget}',
                'kitti' if cfg['real_apply_calib'] else 'poss', cfg['real_seq'], ids, gt,
                dict(source_manifest=str(out/'source_manifest.json'),frame_binding='persisted_source_frame_ids',budget=budget,seed=42))
            torch.manual_seed(42)
            np.random.seed(42)
            start = time.perf_counter()
            edges = loop_closure.verify_candidates(pairs,scans,odom,backend,gt_poses=gt,
                min_overlap=.7,max_mean_dist=2.5,multigen_k=1,measurement_log=log)
            verification_seconds = time.perf_counter()-start
            assert not log.summary()['failed'] and not log.summary()['started']
            save(arm/'accepted_loops.json', [{k:v.tolist() if isinstance(v,np.ndarray) else v for k,v in e.items()} for e in edges])
            start = time.perf_counter()
            optimized = pose_graph.optimize_pose_graph(odom,kfs,edges,loop_weighting='relfloor',robust_kernel='huber',loop_nms_width=0)
            full = np.asarray(pose_graph.propagate_to_full_trajectory(odom,kfs,optimized))
            pgo_seconds = time.perf_counter()-start
            assert full.shape == (len(ids),4,4) and np.isfinite(full).all()
            sequence.save_kitti_poses(full,str(arm/'optimized_poses.txt'))
            saved = metrics.load_kitti_format(str(arm/'optimized_poses.txt'))
            np.testing.assert_allclose(saved,full,atol=1e-9,rtol=0)
            result = metrics.evaluate_pair(gt,saved,ids)
            if cfg['real_apply_calib']:
                tr = metrics.real_dataset._read_calib_transform(str(data/'sequences'/cfg['real_seq']/'calib.txt'))
                inv = np.linalg.inv(tr)
                result['camera_kitti'] = metrics.kitti_drift([tr@p@inv for p in gt],[tr@p@inv for p in saved],source_frame_ids=ids)
            events = [json.loads(s) for s in (arm/'verification_measurements.jsonl').read_text().splitlines()]
            starts = [e for e in events if e['event']=='candidate_started']
            ends = [e for e in events if e['event']=='candidate_finished']
            gen = {e['measurement']['measurement_id']:e['measurement'] for e in events if e['event']=='generation'}
            assert [(e['i'],e['j']) for e in starts] == pairs
            assert len(starts)==len(ends)==len(gen)==len(pairs)
            assert {e['attempt_id'] for e in starts}=={e['attempt_id'] for e in ends}
            accepted_ids = set()
            for e in ends:
                r = gen[e['selected_measurement_id']]
                assert (e['status']=='accepted') == (r['overlap']>=.7 and r['mean_dist']<=2.5)
                i,j = [int(np.flatnonzero(ids==v)[0]) for v in r['source_frame_ids']]
                label = transform_label(r['T_rel'],np.linalg.inv(gt[i])@gt[j])
                assert label['validity']['valid'] and label['label']==r['labels']['label']
                if e['status']=='accepted': accepted_ids.add(r['measurement_id'])
            disk_edges = json.loads((arm/'accepted_loops.json').read_text())
            assert {e['measurement_id'] for e in disk_edges}==accepted_ids
            for e in disk_edges:
                r = gen[e['measurement_id']]
                np.testing.assert_array_equal(e['T_rel'],r['T_rel'])
                assert r['source_frame_ids']==[int(ids[e['i']]),int(ids[e['j']])]
            entry = dict(budget=budget,candidates=len(pairs),counts=log.summary(),metrics=result,
                labels=dict(Counter(r['labels']['label'] for r in gen.values())),
                accepted_labels=dict(Counter(gen[v]['labels']['label'] for v in accepted_ids)),
                timings_s=dict(retrieval=retrieval_seconds,verification=verification_seconds,pgo=pgo_seconds))
            save(arm/'metrics.json',entry)
            save(arm/'validation.json',dict(attempts=len(pairs),complete=True,gates_rechecked=True,rigid_transforms=True,exact_edge_associations=True,saved_trajectory_evaluated=True))
            arms.append(entry)
            print(f"{name} budget {budget}: APE {result['ape_unaligned_rmse']:.6f}, {len(edges)}/{len(pairs)} accepted",flush=True)
        for i,h in scans.hashes.items():
            p = str(scans.paths[i])
            assert h == oldhash[p] and sha(p)==h
            identities[p] = h
        reference = json.loads((parent/'paper_metrics.json').read_text())['pgo']
        original = [json.loads(s) for s in (src/'verification_measurements.jsonl').read_text().splitlines()]
        original_pairs = [[e['i'],e['j']] for e in original if e['event']=='candidate_started']
        pairs12 = json.loads((dest/'12/candidates.json').read_text())['merged']
        pairs40 = json.loads((dest/'40/candidates.json').read_text())['merged']
        shared = set(map(tuple,pairs12)) & set(map(tuple,pairs40))
        row = dict(sequence=name,arms=arms,descriptor_seconds=descriptor_seconds,
            shared_pairs=len(shared),added_pairs=len(pairs40)-len(shared),removed_pairs=len(pairs12)-len(shared),
            budget12_matches_reference_order=pairs12==original_pairs,
            budget12_reference_ape_delta=arms[0]['metrics']['ape_unaligned_rmse']-reference['ape_unaligned_rmse'])
        rows.append(row)
        save(dest/'comparison.json',row)
    for p,h in identities.items(): assert sha(p)==h,p
    changes = [r['arms'][1]['metrics']['ape_unaligned_rmse']/r['arms'][0]['metrics']['ape_unaligned_rmse']-1 for r in rows]
    passed = sum(v<0 for v in changes)>=3 and max(changes)<=.05 and all(r['arms'][1]['accepted_labels'].get('dangerous',0)==0 for r in rows)
    save(out/'summary.json',dict(screen_passed=passed,relative_ape_changes=changes,sequences=rows,
        shared_model_startup_seconds=startup,threads={k:os.environ.get(k) for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS']},input_hashes_rechecked=len(identities)))
    save(out/'source_manifest.json',identities)
    lines = ['# O2 candidate budget comparison','',f'Predeclared development screen passed: {passed}. Production default unchanged.','',
        '| Sequence | Budget | Candidates / accepted | First APE m | Aligned APE m | Translation drift % | Verification s |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for row in rows:
        for a in row['arms']:
            m=a['metrics']; drift=m.get('camera_kitti',m)
            lines.append(f"| {row['sequence']} | {a['budget']} | {a['candidates']} / {a['counts']['accepted']} | {m['ape_unaligned_rmse']:.6f} | {m['ape_aligned_rmse']:.6f} | {drift['kitti_ter_pct']:.6f} | {a['timings_s']['verification']:.3f} |")
    lines += ['', 'Drift is camera-frame for KITTI, custom LiDAR for POSS. First APE uses first-pose LiDAR alignment. Timings are warm loop verification only, not total pipeline throughput. Model startup and descriptor/retrieval/PGO costs are separate in JSON.', '',
        'Both budgets regenerate measurements with seed 42 in candidate order. Candidate overlap and reference reproduction are recorded per sequence. These are development sequences; no independent risk calibration or generalization guarantee. All persisted attempts, gates, rotation validity, edge associations, saved trajectories and source hashes were checked.']
    (out/'REPORT.md').write_text('\n'.join(lines)+'\n')
    (out/'INCOMPLETE').unlink()
    print('\n'.join(lines),flush=True)


if __name__=='__main__':
    main()
