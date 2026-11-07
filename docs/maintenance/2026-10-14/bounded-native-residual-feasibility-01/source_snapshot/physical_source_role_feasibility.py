"""PSR0 current source/role audit; no numerical point-cloud or pose parsing."""
import time
START = time.monotonic()
import hashlib
import json
import os
import resource
import signal
import subprocess
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SLAM = ROOT.parent / 'RAP-SLAM'
DATA = ROOT.parent / 'Datasets/data_odometry_velodyne/dataset'
BASE = ROOT / 'docs/maintenance/2026-10-14/physical-source-role-feasibility-01'
SUP = BASE / 'supervision'
DS0 = ROOT / 'docs/maintenance/2026-10-07/readout-supervision-design-01'
BOREAS = ROOT / 'docs/maintenance/2026-09-15/boreas-access-01'
HANDOFF = ROOT / 'docs/maintenance/2026-10-14/continuation-handoff-03'
QUERIES = ('oxts', 'velodyne/timestamps.txt', 'velodyne/timestamps_start.txt',
           'velodyne/timestamps_end.txt', 'calib_velo_to_cam.txt',
           'calib_imu_to_velo.txt', 'calib_cam_to_cam.txt', 'tracklet_labels.xml',
           'labels', 'archive_receipt.json')
MARKERS = (
    '2026-10-10/native-conditioned-comparison-01/INCOMPLETE',
    '2026-10-10/native-conditioned-comparison-01/attempt-02/INCOMPLETE',
    '2026-10-12/native-backward-reproducibility-01/INCOMPLETE',
    '2026-10-13/shadow-conditioned-fit-pilot-01/INCOMPLETE',
    '2026-10-13/shadow-evidence-archive-01/INCOMPLETE')
DOCS = (
    '2026-10-07/readout-supervision-design-01/DATA_AUDIT.json',
    '2026-10-07/readout-supervision-design-01/DATA_ROLES.md',
    '2026-10-07/readout-supervision-design-01/REPORT.md',
    '2026-09-29/rap-information-path-audit-01/REPORT.md',
    '2026-09-28/conditioning-source-audit-01/REPORT.md',
    '2026-09-15/boreas-access-01/REPORT.md',
    '2026-09-15/boreas-access-01/download_manifest.json',
    '2026-10-12/reference-physical-consistency-01/REPORT.md',
    '2026-10-12/reference-physical-consistency-01/SOURCE_NOTES.md',
    '2026-10-12/measured-gicp-registration-01/REPORT.md',
    '2026-10-12/causal-context-registration-01/REPORT.md',
    '2026-10-13/frozen-context-extraction-01/REPORT.md',
    '2026-10-13/frozen-context-extraction-01/PROTOCOL.md',
    '2026-10-13/frozen-metric-head-derivatives-01/REPORT.md',
    '2026-10-13/frozen-metric-head-derivatives-01/PROTOCOL.md',
    '2026-10-13/geometry-signature-control-01/REPORT.md',
    '2026-10-14/artifact-payload-ledger-01/REPORT.md')
SOURCE_NAMES = ('rap_backend.py', 'real_dataset.py', 'odometry.py')

def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))

def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for block in iter(lambda: f.read(1048576), b''):
            h.update(block)
    return h.hexdigest()

def save(p, value):
    data = (json.dumps(value, indent=2, allow_nan=False) + '\n').encode()
    assert census_bytes() + len(data) < 32 * 2**20
    with Path(p).open('xb') as f:
        f.write(data)

def census_bytes():
    return sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file())

def repositories():
    result = {}
    for name, folder in [('main', ROOT), ('slam', SLAM)]:
        def git(*args):
            return subprocess.check_output(['git', '--no-optional-locks', '-C',
                                            str(folder), *args], text=True).strip()
        result[name] = dict(head=git('rev-parse', 'HEAD'),
                            branch=git('branch', '--show-current'),
                            tracked_status=git('status', '--short', '--untracked-files=no').splitlines())
    return result

def verify():
    f = read(BASE / 'freeze.json')
    for p, h in f['files'].items():
        assert sha(p) == h, p
    assert repositories() == f['repositories']
    assert all((ROOT / 'docs/maintenance' / x).exists() for x in MARKERS)
    return f

def freeze():
    paths = [ROOT / 'docs/maintenance' / n for n in DOCS + MARKERS]
    paths += [SLAM / 'rap_slam' / n for n in SOURCE_NAMES]
    paths += [ROOT / 'rectified_point_flow/flow_model' / n
              for n in ('embedding.py', 'point_cloud_dit.py')]
    paths += [BASE / 'OWNER_SCOPE.md', BASE / 'PROTOCOL.md', Path(__file__),
              Path(__file__).with_name('validate_physical_source_roles.py'),
              Path(__file__).with_name('invoke_mgr_supervised_wsl.ps1')]
    seal = read(HANDOFF / 'DELIVERY_SEAL.json')
    assert seal['entries'] == 11
    for row in seal['files']:
        p = HANDOFF / row['path']
        assert sha(p) == row['sha256'] and p.stat().st_size == row['bytes']
        paths.append(p)
    paths.append(HANDOFF / 'DELIVERY_SEAL.json')
    old = read(DS0 / 'DATA_AUDIT.json')
    for row in old['kitti']:
        for key in ('pose_schema', 'timestamps_schema', 'calibration_schema'):
            p = Path(row[key]['path'])
            assert sha(p) == row[key]['sha256']
            paths.append(p)
    for row in read(BOREAS / 'download_manifest.json'):
        p = BOREAS / row['path']
        assert sha(p) == row['sha256'] and p.stat().st_size == row['bytes']
        paths.append(p)
    files = {str(p): sha(p) for p in paths}
    repos = repositories()
    assert repos == read(HANDOFF / 'IDENTITY_CHECKS.json')['repositories']
    snap = BASE / 'source_snapshot'
    snap.mkdir()
    for p in paths:
        if p.suffix in ('.py', '.ps1'):
            name = ('slam_' if SLAM in p.parents else 'main_') + p.name
            with (snap / name).open('xb') as out:
                out.write(p.read_bytes())
    save(BASE / 'freeze.json', dict(files=files, repositories=repos,
         provenance_queries=QUERIES, caps=dict(seconds=900, RSS_bytes=512*2**20,
         GPU_bytes=0, whole_dossier_bytes=32*2**20), inherited_scientific_replay=False))
    save(BASE / 'INCOMPLETE', dict(scope='PSR0', pending='inventory/independent validation'))
    print('PSR0 frozen', len(files), 'identities', flush=True)

def listing(folder):
    p = Path(folder)
    if not p.exists():
        return dict(path=str(p), exists=False, entries=[])
    rows = []
    with os.scandir(p) as entries:
        for e in entries:
            rows.append(dict(name=e.name, directory=e.is_dir(follow_symlinks=False),
                             symlink=e.is_symlink()))
    return dict(path=str(p), exists=True, entries=sorted(rows, key=lambda x: x['name']))

def inventory():
    verify()
    old = {r['sequence']: r for r in read(DS0 / 'DATA_AUDIT.json')['kitti']}
    sequences = sorted(e.name for e in os.scandir(DATA / 'sequences') if e.is_dir())
    rows = []
    scan_records = []
    for seq in sequences:
        q = DATA / 'sequences' / seq
        scans = []
        if (q / 'velodyne').is_dir():
            with os.scandir(q / 'velodyne') as entries:
                for e in entries:
                    if e.is_file() and e.name.endswith('.bin'):
                        scans.append((e.name, e.stat().st_size))
        scans.sort()
        ids = [int(Path(n).stem) for n, _ in scans]
        meta = []
        if seq in old:
            assert len(scans) == old[seq]['raw_scans']
            for key in ('pose_schema', 'timestamps_schema', 'calibration_schema'):
                record = old[seq][key]
                assert sha(record['path']) == record['sha256']
                meta.append(dict(kind=key, path=record['path'], sha256=record['sha256']))
        role = ('EXPOSED_FIT_CALIBRATION_OR_DEVELOPMENT' if seq <= '05' else
                'EXPOSED_DEVELOPMENT' if seq == '06' else
                'EXPOSED_EVALUATION_OR_DEVELOPMENT' if seq <= '10' else
                'NO_LOCAL_SUPERVISED_ROLE_ESTABLISHED')
        rows.append(dict(sequence=seq, raw_scans=len(scans), raw_bytes=sum(b for _, b in scans),
             IDs_contiguous=bool(scans) and ids == list(range(len(ids))),
             positive_16byte_sizes=bool(scans) and all(b > 0 and b % 16 == 0 for _, b in scans),
             directory=listing(q), metadata=meta,
             independent_provenance_queries=[dict(relative_path=n, exists=(q/n).exists()) for n in QUERIES],
             role=role, checkpoint_membership='UNKNOWN', physical_site_disjointness='UNKNOWN'))
        scan_records.append(dict(sequence=seq, names_and_sizes=scans))
        print('PSR0 sequence', seq, len(scans), 'metadata records', flush=True)
        cap()
    mirrors = [SLAM/'data/kitti/dataset', SLAM/'data/poss/dataset',
               ROOT.parent/'Datasets/oxford_spires', ROOT.parent/'Datasets/oxford_spires/gt']
    other = [listing(p) for p in mirrors]
    boreas = []
    for row in read(BOREAS / 'download_manifest.json'):
        p = BOREAS / row['path']
        boreas.append(dict(path=str(p), bytes=p.stat().st_size, sha256=sha(p),
                           old_manifest_identity_match=sha(p) == row['sha256']))
    citations = []
    terms = ('deskew', 'timestamp', 'miniSpinNet', 'MiniSpinNet', 'extract_features',
             'local_feat', 'batch_indices', 'part_indices', 'scale', 'checkpoint')
    for p in [SLAM/'rap_slam'/n for n in SOURCE_NAMES] + [ROOT/'rectified_point_flow/flow_model'/n for n in ('embedding.py','point_cloud_dit.py')]:
        for i, line in enumerate(p.read_text().splitlines(), 1):
            if any(term in line for term in terms):
                citations.append(dict(path=str(p), line=i, text=line))
    assert set(old) == {r['sequence'] for r in rows if r['metadata']}
    assert all(r['IDs_contiguous'] and r['positive_16byte_sizes'] for r in rows if r['metadata'])
    save(BASE / 'scan_metadata.json', dict(records=scan_records, raw_numeric_payload_parsed=False))
    save(BASE / 'inventory.json', dict(sequences=rows, other_roots=other,
        boreas_objects=boreas, source_citations=citations,
        labeled_KITTI_scans=sum(r['raw_scans'] for r in rows if r['metadata']),
        exposure_evidence=str(DS0/'DATA_ROLES.md'),
        checkpoint_exclusion_authenticated=False, independent_confirmation_established=False,
        independent_physical_truth_established=False,
        decision='EXPOSED_KITTI_DEVELOPMENT_AVAILABLE_INDEPENDENT_CONFIRMATION_UNESTABLISHED',
        raw_numeric_payload_parsed=False, pose_numeric_payload_parsed=False,
        new_labels_or_pose_metrics_or_models=False, inherited_DS0_schema_checks_replayed=False))
    files = [dict(path=n, sha256=sha(BASE/n), bytes=(BASE/n).stat().st_size)
             for n in ('scan_metadata.json', 'inventory.json')]
    save(BASE / 'inventory_seal.json', dict(files=files, entries=len(files)))
    verify()

def usage():
    return dict(wall_seconds=time.monotonic()-START,
        peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
        peak_GPU_allocated_bytes=0, peak_GPU_reserved_bytes=0,
        artifact_bytes=census_bytes(), model_calls=0, optimizer_calls=0,
        raw_numeric_payload_parsed=False, imports_after_time_bootstrap_included=True)

def cap():
    u = usage()
    assert u['peak_RSS_bytes'] <= 512*2**20 and u['artifact_bytes'] < 32*2**20, u
    if (SUP/'host_latest.json').exists():
        assert read(SUP/'host_latest.json')['headroom_bytes'] >= 4*2**30

def run(stage):
    spent = sum(read(p)['wall_seconds'] for p in SUP.glob('*/exit.json'))
    assert spent < 900
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('PSR0 aggregate cap')))
    signal.alarm(max(1, int(900-spent)))
    ok = False
    error = None
    try:
        if stage == 'freeze':
            freeze()
        elif stage == 'inventory':
            inventory()
        elif stage == 'validate':
            import validate_physical_source_roles as v
            v.validate()
        else:
            raise ValueError(stage)
        cap()
        ok = True
    except BaseException as ex:
        error = repr(ex)
        traceback.print_exc()
        save(BASE/f'FAILURE_{stage}.json', dict(error=error, **usage()))
    finally:
        signal.alarm(0)
        save(SUP/stage/'child_exit.json', dict(success=ok, error=error,
             full_resource_capture=True, **usage()))
    if not ok:
        sys.exit(1)

if __name__ == '__main__':
    run(sys.argv[1])
