"""DS0 bounded dataset metadata/schema audit; no clouds, poses or model output.

Pose files are read only to count numeric fields/rows and finiteness. No pose
transform, relative pose, nearest point, error, label or model is computed.
"""
import hashlib
import json
import math
import time
from pathlib import Path

MAIN = Path(__file__).resolve().parents[2]
SLAM = MAIN.parent / 'RAP-SLAM'
DATA = MAIN.parent / 'Datasets'
B = MAIN / 'docs/maintenance/2026-10-07/readout-supervision-design-01'
TR0 = B.parent / 'joint-token-preflight-01'


def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))


def save(p, value):
    with Path(p).open('x', encoding='utf-8') as f:
        json.dump(value, f, indent=2, allow_nan=False)
        f.write('\n')


def schema(p, width):
    counts = {}
    rows = 0
    finite = True
    with Path(p).open(encoding='utf-8-sig') as f:
        for line in f:
            if not line.strip() or line.lstrip().startswith('#'):
                continue
            fields = [float(x) for x in line.split()]
            counts[str(len(fields))] = counts.get(str(len(fields)), 0) + 1
            finite = finite and all(math.isfinite(x) for x in fields)
            rows += 1
    return dict(path=str(p), bytes=Path(p).stat().st_size, sha256=sha(p),
                rows=rows, column_counts=counts, numeric_finite=finite,
                expected_width=width, schema_ok=finite and set(counts) == {str(width)})


def tr0_verify():
    f = read(TR0 / 'freeze.json')
    for p, h in f['files'].items():
        assert sha(p) == h, p
    s = read(TR0 / 'bank_seal.json')
    assert s['freeze_sha256'] == sha(TR0 / 'freeze.json')
    assert s['results_sha256'] == sha(TR0 / 'bank.json')
    assert set(s['files']) == {str(p.relative_to(TR0)) for p in (TR0 / 'bank').glob('*.npz')}
    for p, h in s['files'].items():
        assert sha(TR0 / p) == h, p
    v = read(TR0 / 'validation_seal.json')
    assert v['validation_sha256'] == sha(TR0 / 'validation.json')
    assert read(TR0 / 'validation.json')['passed']
    return dict(freeze_sha256=sha(TR0 / 'freeze.json'), bank_seal_sha256=sha(TR0 / 'bank_seal.json'),
                validation_seal_sha256=sha(TR0 / 'validation_seal.json'), unchanged=True)


def audit():
    start = time.monotonic()
    tr0 = tr0_verify()
    native = [SLAM / 'rap_slam' / n for n in ('real_dataset.py', 'spires_dataset.py', 'structured_motion.py')]
    native += [MAIN / 'rectified_point_flow' / n for n in ('modeling.py', 'sampler.py', 'procrustes.py',
                    'flow_model/point_cloud_dit.py', 'flow_model/embedding.py', 'flow_model/layer.py', 'utils/point_clouds.py')]
    native += [MAIN / 'config/data/data_tmp.yaml', MAIN / 'scripts/download_weights_and_demo_data.sh', MAIN / 'README.md',
               MAIN / 'docs/maintenance/2026-09-10/m3/pilot-01/splits.json', Path(__file__), B / 'AUDIT_PROTOCOL.md']
    save(B / 'source_snapshot.json', dict(files={str(p): sha(p) for p in native},
        scope='Read-only source/schema audit, not a prospective scientific experiment; initial top-level inspection already performed', tr0=tr0))
    root = DATA / 'data_odometry_velodyne/dataset'
    raw_manifest = {}
    sequences = []
    for index in range(11):
        s = f'{index:02d}'
        folder = root / 'sequences' / s
        scans = sorted((folder / 'velodyne').glob('*.bin'))
        ids = [int(p.stem) for p in scans]
        records = [dict(id=i, filename=p.name, bytes=p.stat().st_size) for i, p in zip(ids, scans)]
        raw_manifest[s] = records
        pose = schema(root / 'poses' / (s + '.txt'), 12)
        times = schema(folder / 'times.txt', 1)
        ts = [float(x) for x in (folder / 'times.txt').read_text().split()]
        keys = {}
        for line in (folder / 'calib.txt').read_text().splitlines():
            if ':' in line:
                key, values = line.split(':', 1)
                fields = [float(x) for x in values.split()]
                keys[key] = dict(columns=len(fields), numeric_finite=all(math.isfinite(x) for x in fields))
        calib = dict(path=str(folder / 'calib.txt'), sha256=sha(folder / 'calib.txt'), keys=keys,
                     lidar_to_camera_key='Tr' if 'Tr' in keys else None)
        ok = bool(scans) and ids == list(range(len(scans))) and all(r['bytes'] > 0 and r['bytes'] % 16 == 0 for r in records)
        ok = ok and pose['schema_ok'] and times['schema_ok'] and pose['rows'] == times['rows'] == len(scans)
        ok = ok and all(a < b for a, b in zip(ts, ts[1:])) and 'Tr' in keys and keys['Tr']['columns'] == 12 and keys['Tr']['numeric_finite']
        sequences.append(dict(sequence=s, raw_scans=len(scans), raw_bytes=sum(x['bytes'] for x in records),
            raw_numeric_payload_read=False, ids_contiguous=ids == list(range(len(scans))),
            raw_size_multiple_16=all(x['bytes'] % 16 == 0 and x['bytes'] > 0 for x in records),
            pose_schema=pose, timestamps_schema=times, timestamps_strictly_increasing=all(a < b for a,b in zip(ts,ts[1:])),
            calibration_schema=calib, metadata_schema_ready=ok,
            physical_label_accuracy_validated=False, physical_site_disjointness_confirmed=False,
            checkpoint_membership='UNKNOWN'))
    assert all(r['metadata_schema_ready'] for r in sequences)
    save(B / 'raw_metadata_manifest.json', raw_manifest)
    ox = DATA / 'oxford_spires'
    gt = [schema(p, 8) for p in sorted((ox / 'gt').glob('*.txt'))]
    ox_inventory = dict(root=str(ox), root_entries=[dict(name=p.name, directory=p.is_dir()) for p in sorted(ox.iterdir())],
        gt_files=gt, sequences_directory_exists=(ox / 'sequences').is_dir(),
        calibration_directory_exists=(ox / 'calibration').is_dir(),
        point_cloud_payload_available=bool(list((ox / 'sequences').glob('*/raw/lidar-clouds/*.pcd'))),
        confirmation_ready=False, checkpoint_membership='UNKNOWN',
        published_rap_training_includes_dataset=True,
        loader_caveat='Current loader does not apply base-to-LiDAR extrinsic; first-pose anchoring does not generally remove lever-arm effects')
    part2 = DATA / 'part2'
    part2_inventory = dict(root=str(part2), inspected_depth=1,
        directories=sum(p.is_dir() for p in part2.iterdir()), files=sum(p.is_file() for p in part2.iterdir()),
        relevant_dataset_archive_or_payload_observed=False,
        scope='Unrelated top-level items excluded; no names/content/deeper inspection retained')
    windows = []
    for r in sequences:
        s = r['sequence']
        role, count = ('fit', 24) if int(s) <= 5 else (('development', 12) if s == '06' else ('exposed_evaluation', 12))
        n = r['raw_scans']
        targets = [2 + (j*(n-3))//(count-1) for j in range(count)]
        assert len(set(targets)) == count
        supports = [{t-2,t-1,t} for t in targets]
        assert all(a.isdisjoint(b) for i,a in enumerate(supports) for b in supports[i+1:])
        windows += [dict(sequence=s, role=role, t=t, ids=[t-1,t,t-2]) for t in targets]
    assert len(windows) == 204
    save(B / 'WINDOW_MANIFEST_DRAFT.json', dict(status='DRAFT_NOT_EXPERIMENT_FROZEN', rule='2+floor(j*(N-3)/(m-1)); m24 fit00-05,m12 dev06/eval07-10',
        counts=dict(fit=144, development=12, exposed_evaluation=48, total=204), windows=windows,
        selected_by_gt_or_model_error=False, no_shared_raw_frame_across_windows=True, physical_site_independence=False))
    tr0_verify()
    for p,h in read(B / 'source_snapshot.json')['files'].items():
        assert sha(p) == h, p
    save(B / 'DATA_AUDIT.json', dict(stage='DS0', scope='READ_ONLY_METADATA_SCHEMA_DESIGN', kitti=sequences,
        available_sequence_directory_names=sorted(p.name for p in (root / 'sequences').iterdir() if p.is_dir()),
        oxford_spires=ox_inventory, part2=part2_inventory, tr0=tr0,
        total_labeled_kitti_raw_files=sum(r['raw_scans'] for r in sequences),
        raw_metadata_manifest_sha256=sha(B / 'raw_metadata_manifest.json'),
        pose_contents_read_for_schema=True, numeric_pose_values_retained=False,
        relative_pose_or_correspondence_labels_generated=False, gt_error_computed=False, raw_cloud_payload_read=False,
        model_inference=False, gpu_used=False, training=False, code_or_dataset_changed=False,
        source_and_tr0_recheck_passed=True, wall_s=time.monotonic()-start))
    print('DS0 read-only schema audit complete:', len(sequences), 'KITTI sequences /', len(windows), 'draft windows;', len(gt), 'Oxford GT files, no confirmed scan payload', flush=True)


if __name__ == '__main__':
    audit()
