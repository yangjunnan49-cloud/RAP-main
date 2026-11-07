"""PCC0 sealed physical inputs/strong-control contract; no numeric arrays."""
import time
START = time.monotonic()
import ast
import json
import os
import resource
import signal
import struct
import sys
import traceback
import zipfile
from pathlib import Path
import physical_source_role_feasibility as s
ROOT = s.ROOT
SLAM = s.SLAM
BASE = ROOT / 'docs/maintenance/2026-10-14/physical-comparison-contract-01/layout-attempt-02'
SUP = BASE / 'supervision'
PSR = s.BASE
RLP = ROOT / 'docs/maintenance/2026-10-08/motion-supervised-readout-01'
POSS = SLAM / 'data/poss/dataset'
OLD_POSS = ROOT / 'docs/maintenance/2026-09-11/full-poss-01'
(read, sha) = (s.read, s.sha)

def size():
    return sum((p.stat().st_size for p in BASE.rglob('*') if p.is_file()))

def save(p, value):
    body = (json.dumps(value, indent=2, allow_nan=False) + '\n').encode()
    assert size() + len(body) < 32 * 2 ** 20
    with Path(p).open('xb') as stream:
        stream.write(body)

def verify():
    f = read(BASE / 'freeze.json')
    for (p, h) in f['files'].items():
        assert sha(p) == h, p
    assert s.repositories() == f['repositories']
    return f

def freeze():
    files = {}
    for row in read(PSR / 'DELIVERY_SEAL.json')['files']:
        p = PSR / row['path']
        assert sha(p) == row['sha256']
        files[str(p)] = row['sha256']
    paths = [PSR / 'DELIVERY_SEAL.json', BASE / 'PROTOCOL.md', BASE / 'OWNER_SCOPE.md', Path(__file__), Path(__file__).with_name('validate_physical_comparison_contract.py'), Path(__file__).with_name('physical_source_role_feasibility.py'), Path(__file__).with_name('invoke_mgr_supervised_wsl.ps1'), RLP / 'REPORT.md', RLP / 'STATUS.json', ROOT / 'docs/maintenance/2026-10-09/motion-readout-reassessment-01/REPORT.md', OLD_POSS / 'REPORT.md', OLD_POSS / 'input_manifest.json', OLD_POSS / 'pipeline/source_frames.json', OLD_POSS / 'pipeline/summary.json', POSS / 'poses/00.txt', POSS / 'sequences/00/calib.txt', POSS / 'sequences/00/times.txt', POSS / 'sequences/00/calib_readme.txt', SLAM / 'rap_slam/real_dataset.py', Path(__file__).with_name('rlp2_full_bank.py'), Path(__file__).with_name('rlp2_pose_targets.py')]
    for stage in ('full-bank', 'pose-targets'):
        paths += [RLP / stage / n for n in ('freeze.json', 'bank.json', 'bank_seal.json', 'validation.json')]
    for p in paths:
        files[str(p)] = sha(p)
    snap = BASE / 'source_snapshot'
    snap.mkdir()
    for p in paths:
        if p.suffix in ('.py', '.ps1'):
            name = ('slam_' if SLAM in p.parents else 'main_') + p.name
            with (snap / name).open('xb') as out:
                out.write(p.read_bytes())
    repos = s.repositories()
    assert repos == read(PSR / 'FINAL_IDENTITY_CHECK.json')['repositories']
    rows = read(RLP / 'full-bank/bank.json')['rows']
    assert len(rows) == 204
    save(BASE / 'freeze.json', dict(files=files, repositories=repos, rows=[{k: r[k] for k in ('seq', 't', 'ids', 'role', 'seed', 'paths')} for r in rows], caps=dict(Windows_seconds=900, RSS_bytes=512 * 2 ** 20, GPU_bytes=0, dossier_bytes=32 * 2 ** 20), following_candidate=dict(base='J_pose', translation_component_m=0.05, rotation_component_deg=0.2, nonlinearity='tanh'), no_numerical_source_replay=True))
    save(BASE / 'INCOMPLETE', dict(scope='PCC0', pending='audit/validation'))
    print('PCC0 frozen', len(files), 'source identities/204 fixed rows', flush=True)

def header(z, name):
    with z.open(name) as stream:
        assert stream.read(6) == b'\x93NUMPY'
        version = tuple(stream.read(2))
        assert version in ((1, 0), (2, 0), (3, 0))
        count = struct.unpack('<H' if version == (1, 0) else '<I', stream.read(2 if version == (1, 0) else 4))[0]
        assert 0 < count < 65536
        value = ast.literal_eval(stream.read(count).decode('utf-8' if version == (3, 0) else 'latin1').strip())
    assert set(value) == {'descr', 'fortran_order', 'shape'}
    dtype = value['descr']
    assert isinstance(dtype, str) and dtype[0] in '<>|=' and (dtype[1] in 'fiu b'.replace(' ', ''))
    assert all((isinstance(n, int) and n >= 0 for n in value['shape']))
    info = z.getinfo(name)
    return dict(name=name, shape=list(value['shape']), dtype=dtype, fortran_order=value['fortran_order'], uncompressed_bytes=info.file_size, compressed_bytes=info.compress_size, CRC=info.CRC)

def local_metadata(root):
    rows = []
    for seq in sorted((e.name for e in os.scandir(root / 'sequences') if e.is_dir())):
        folder = root / 'sequences' / seq
        records = []
        if (folder / 'velodyne').is_dir():
            with os.scandir(folder / 'velodyne') as entries:
                records = sorted([[e.name, e.stat().st_size] for e in entries if e.is_file() and e.name.endswith('.bin')])
        rows.append(dict(sequence=seq, names_and_sizes=records, directory_entries=sorted((p.name for p in folder.iterdir()))))
    return rows

def audit():
    f = verify()
    banks = []
    selected_files = {}
    for stage in ('full-bank', 'pose-targets'):
        seal = read(RLP / stage / 'bank_seal.json')
        assert seal['freeze_sha256'] == sha(RLP / stage / 'freeze.json')
        assert seal['manifest_sha256'] == sha(RLP / stage / 'bank.json')
        expected = {f"bank/{r['seq']}_{r['t']:06d}.npz" for r in f['rows']}
        assert set(seal['files']) == expected
        rows = []
        for row in f['rows']:
            rel = f"bank/{row['seq']}_{row['t']:06d}.npz"
            p = RLP / stage / rel
            h = sha(p)
            assert h == seal['files'][rel], p
            with zipfile.ZipFile(p) as z:
                assert len(z.namelist()) == len(set(z.namelist()))
                headers = [header(z, n) for n in sorted(z.namelist())]
            shapes = {r['name']: r['shape'] for r in headers}
            if stage == 'full-bank':
                for (key, shape) in [('points', [3000, 3]), ('features', [3000, 32]), ('J_tokens', [3, 1000, 512]), ('I_tokens', [3, 1000, 512]), ('J_pose', [4, 4]), ('I_pose', [4, 4])]:
                    assert shapes[key + '.npy'] == shape
                evaluation = row['role'] == 'exposed_evaluation'
                assert ('G3_pose.npy' in shapes) == evaluation
                assert ('KISS_pose.npy' in shapes) == (evaluation and row['seq'] in ('07', '09', '10'))
            else:
                assert shapes['angular_truth.npy'] == [3, 4, 4]
            rows.append(dict(seq=row['seq'], t=row['t'], role=row['role'], path=str(p), sha256=h, bytes=p.stat().st_size, members=headers))
            selected_files[str(p)] = h
            cap()
        banks.append(dict(stage=stage, rows=rows))
        print('PCC0 complete sealed headers', stage, len(rows), flush=True)
    poss = local_metadata(POSS)
    mirror = local_metadata(SLAM / 'data/kitti/dataset')
    canonical = {r['sequence']: r['names_and_sizes'] for r in read(PSR / 'scan_metadata.json')['records']}
    for row in mirror:
        original = dict(canonical.get(row['sequence'], []))
        row['canonical_names_sizes_match'] = all((original.get(n) == b for (n, b) in row['names_and_sizes']))
        row['byte_identity_or_independent_acquisition_established'] = False
    historic = read(OLD_POSS / 'pipeline/source_frames.json')
    assert len(poss) == 1 and poss[0]['sequence'] == '00'
    ids = [int(Path(n).stem) for (n, _) in poss[0]['names_and_sizes']]
    old_ids = historic['source_frame_ids']
    assert set(old_ids) <= set(ids) and len(old_ids) == 1419
    old_bindings = read(OLD_POSS / 'input_manifest.json')
    poss_tables = []
    for name in ('poses/00.txt', 'sequences/00/calib.txt', 'sequences/00/times.txt', 'sequences/00/calib_readme.txt'):
        p = POSS / name
        h = sha(p)
        body = p.read_text()
        poss_tables.append(dict(path=str(p), sha256=h, bytes=p.stat().st_size, nonempty_rows=sum((bool(line.strip()) for line in body.splitlines())), old_full_poss_hash=old_bindings.get(str(p)), old_hash_matches=None if str(p) not in old_bindings else old_bindings[str(p)] == h, text=body if p.name == 'calib_readme.txt' else None))
    assert all((x['old_hash_matches'] is not False for x in poss_tables))
    role_counts = {k: sum((r['role'] == k for r in f['rows'])) for k in ('fit', 'development', 'exposed_evaluation')}
    assert role_counts == {'fit': 144, 'development': 12, 'exposed_evaluation': 48}
    source_paths = [p for r in f['rows'] for p in r['paths']]
    assert len(source_paths) == len(set(source_paths)) == 612
    summary = dict(role_counts=role_counts, full_bank_files=204, target_files=204, same_point_G3_evaluation_windows=48, KISS_matched_windows=36, unique_raw_source_paths=612, POSS_local_scans=len(ids), POSS_prior_exposed_scans=len(old_ids), POSS_prior_exposed_IDs=[min(old_ids), max(old_ids)], POSS_current_IDs=[min(ids), max(ids)], independent_confirmation_established=False, full_pipeline_equal_work_established=False, numerical_array_values_read=False, old_failed_matching_head_reopened=False, FHR0_derivative_gate_inherited_for_new_head=False, next_admitted='SEPARATELY_FROZEN_BOUNDED_OUTPUT_FAMILY_NECESSARY_CONDITION_CENSUS', decision='COMPLETE_EXPOSED_COMMON_INPUT_AND_STRONG_CONTROL_BINDINGS_AVAILABLE')
    save(BASE / 'contract_audit.json', dict(summary=summary, banks=banks, POSS_metadata=poss, POSS_tables=poss_tables, sibling_KITTI_metadata=mirror, selected_current_bank_hashes=selected_files))
    save(BASE / 'audit_seal.json', dict(path='contract_audit.json', sha256=sha(BASE / 'contract_audit.json')))
    verify()

def usage():
    return dict(wall_seconds=time.monotonic() - START, peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024, peak_GPU_allocated_bytes=0, peak_GPU_reserved_bytes=0, artifact_bytes=size(), model_calls=0, optimizer_calls=0, numeric_array_values_read=False)

def cap():
    u = usage()
    assert u['peak_RSS_bytes'] <= 512 * 2 ** 20 and u['artifact_bytes'] < 32 * 2 ** 20, u
    if (SUP / 'host_latest.json').exists():
        assert read(SUP / 'host_latest.json')['headroom_bytes'] >= 4 * 2 ** 30

def run(stage):
    spent = sum((read(p)['wall_seconds'] for p in SUP.glob('*/exit.json')))
    assert spent < 900
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('PCC0 aggregate cap')))
    signal.alarm(max(1, int(900 - spent)))
    (ok, error) = (False, None)
    try:
        if stage == 'freeze':
            freeze()
        elif stage == 'audit':
            audit()
        elif stage == 'validate':
            import validate_physical_comparison_contract as v
            v.validate()
        else:
            raise ValueError(stage)
        cap()
        ok = True
    except BaseException as ex:
        error = repr(ex)
        traceback.print_exc()
        save(BASE / f'FAILURE_{stage}.json', dict(error=error, **usage()))
    finally:
        signal.alarm(0)
        save(SUP / stage / 'child_exit.json', dict(success=ok, error=error, full_resource_capture=True, **usage()))
    if not ok:
        sys.exit(1)
if __name__ == '__main__':
    run(sys.argv[1])
