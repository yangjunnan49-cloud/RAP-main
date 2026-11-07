"""Independent PSR0 metadata/role validator; no runner construction imports."""
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'docs/maintenance/2026-10-14/physical-source-role-feasibility-01'
DATA = ROOT.parent/'Datasets/data_odometry_velodyne/dataset'

def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))

def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as stream:
        while True:
            body = stream.read(65536)
            if not body:
                break
            h.update(body)
    return h.hexdigest()

def validate():
    f = read(BASE/'freeze.json')
    for p, expected in f['files'].items():
        assert sha(p) == expected, p
    for row in read(BASE/'inventory_seal.json')['files']:
        assert sha(BASE/row['path']) == row['sha256']
        assert os.stat(BASE/row['path']).st_size == row['bytes']
    inv = read(BASE/'inventory.json')
    records = read(BASE/'scan_metadata.json')['records']
    seqs = sorted(n for n in os.listdir(DATA/'sequences') if os.path.isdir(DATA/'sequences'/n))
    assert seqs == [r['sequence'] for r in inv['sequences']] == [r['sequence'] for r in records]
    nfiles = nqueries = 0
    expected_sizes = {}
    for actual, record in zip(inv['sequences'], records):
        seq = actual['sequence']
        folder = DATA/'sequences'/seq
        raw = folder/'velodyne'
        names = os.listdir(raw) if os.path.isdir(raw) else []
        independent = sorted([[n, os.stat(raw/n).st_size] for n in names
                              if n.endswith('.bin') and os.path.isfile(raw/n)])
        assert independent == record['names_and_sizes']
        assert [n for n, _ in independent] == [f'{i:06d}.bin' for i in range(len(independent))]
        assert all(size > 0 and size % 16 == 0 for _, size in independent)
        assert actual['IDs_contiguous'] == bool(independent)
        assert actual['positive_16byte_sizes'] == bool(independent)
        assert len(independent) == actual['raw_scans']
        assert sum(s for _, s in independent) == actual['raw_bytes']
        nfiles += len(independent)
        for m in actual['metadata']:
            assert sha(m['path']) == m['sha256']
        assert len(actual['independent_provenance_queries']) == 10
        for query, name in zip(actual['independent_provenance_queries'], f['provenance_queries']):
            assert query == dict(relative_path=name, exists=os.path.exists(folder/name))
            nqueries += 1
        index = int(seq)
        role = ('EXPOSED_FIT_CALIBRATION_OR_DEVELOPMENT' if index < 6 else
                'EXPOSED_DEVELOPMENT' if index == 6 else
                'EXPOSED_EVALUATION_OR_DEVELOPMENT' if index < 11 else
                'NO_LOCAL_SUPERVISED_ROLE_ESTABLISHED')
        assert actual['role'] == role
        assert actual['checkpoint_membership'] == actual['physical_site_disjointness'] == 'UNKNOWN'
        expected_sizes[seq] = len(independent)
    for r in inv['other_roots']:
        exists = os.path.exists(r['path'])
        assert exists == r['exists']
        entries = []
        if exists:
            for name in sorted(os.listdir(r['path'])):
                p = Path(r['path'])/name
                entries.append(dict(name=name, directory=p.is_dir() and not p.is_symlink(), symlink=p.is_symlink()))
        assert entries == r['entries']
    manifest_root = ROOT/'docs/maintenance/2026-09-15/boreas-access-01'
    old = read(manifest_root/'download_manifest.json')
    assert len(old) == len(inv['boreas_objects']) == 10
    for row, actual in zip(old, inv['boreas_objects']):
        p = manifest_root/row['path']
        assert str(p) == actual['path'] and sha(p) == row['sha256'] == actual['sha256']
        assert os.stat(p).st_size == row['bytes'] == actual['bytes']
    citations = inv['source_citations']
    assert citations
    for row in citations:
        assert Path(row['path']).read_text().splitlines()[row['line']-1] == row['text']
    assert inv['labeled_KITTI_scans'] == sum(expected_sizes[s] for s in expected_sizes if int(s) < 11) == 23201
    assert inv['decision'] == 'EXPOSED_KITTI_DEVELOPMENT_AVAILABLE_INDEPENDENT_CONFIRMATION_UNESTABLISHED'
    assert not any(inv[k] for k in ('checkpoint_exclusion_authenticated',
        'independent_confirmation_established', 'independent_physical_truth_established',
        'raw_numeric_payload_parsed', 'pose_numeric_payload_parsed',
        'new_labels_or_pose_metrics_or_models', 'inherited_DS0_schema_checks_replayed'))
    result = dict(passed=True, decision=inv['decision'], frozen_identities=len(f['files']),
        sequences=len(seqs), scan_metadata_files=nfiles, independent_provenance_queries=nqueries,
        labeled_KITTI_scans=23201, boreas_old_objects_verified=10,
        source_citations_verified=len(citations), numerical_or_model_replay=False,
        local_absence_is_not_global_absence=True)
    with (BASE/'validation.json').open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps(result), flush=True)
