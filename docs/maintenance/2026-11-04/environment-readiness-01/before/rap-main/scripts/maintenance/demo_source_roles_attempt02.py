"""DSR0 byte/header/static-source audit, no scientific library imports."""
import time
START = time.monotonic()
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
import resource
import signal
import sys
import traceback
import physical_source_role_feasibility as s
ROOT = s.ROOT
BASE = ROOT / 'docs/maintenance/2026-10-15/demo-source-role-01/source-attempt-02'
DATA = ROOT / 'demo_example_data'
SUP = BASE / 'supervision'
(read, sha) = (s.read, s.sha)
SOURCES = ('demo.py', 'dataset_process/utils/io_utils.py', 'rectified_point_flow/data/dataset.py', 'rectified_point_flow/data/datamodule.py', 'rectified_point_flow/eval/evaluator.py', 'config/RAP_inference.yaml', 'config/data/data_tmp.yaml', 'README.md', 'scripts/download_weights_and_demo_data.sh')
MARKERS = s.MARKERS + ('2026-10-14/physical-comparison-contract-01/INCOMPLETE', '2026-10-14/poss-outcome-provenance-01/INCOMPLETE', '2026-10-14/windows-pipe-capture-01/INCOMPLETE', '2026-10-14/native-memory-query-01/INCOMPLETE')

def size():
    return sum((q.stat().st_size for q in BASE.parent.rglob('*') if q.is_file()))

def save(name, value):
    body = (json.dumps(value, indent=2, allow_nan=False) + '\n').encode()
    assert size() + len(body) < 8 * 2 ** 20
    with (BASE / name).open('xb') as out:
        out.write(body)

def inventory():
    return {str(p.relative_to(DATA)): dict(bytes=p.stat().st_size, sha256=sha(p)) for p in sorted(DATA.rglob('*')) if p.is_file()}

def freeze():
    paths = [ROOT / q for q in SOURCES] + [Path(__file__), Path(__file__).with_name('validate_demo_source_roles_attempt02.py'), Path(__file__).with_name('physical_source_role_feasibility.py'), Path(__file__).with_name('invoke_mgr_supervised_wsl.ps1')]
    paths += [BASE / n for n in ('OWNER_SCOPE.md', 'PROTOCOL.md')]
    paths += [ROOT / 'docs/maintenance' / n for n in MARKERS]
    paths += [ROOT / 'docs/maintenance/2026-10-15/public-release-identity-01/identity-attempt-02/DELIVERY_SEAL.json']
    paths += [BASE / n for n in ('AMENDMENT.md', 'ORIGINAL_AVAILABLE_SEAL.json', 'VARIANT_BINDING.json')]
    for (rel, row) in read(BASE / 'ORIGINAL_AVAILABLE_SEAL.json')['files'].items():
        q = BASE.parent / rel
        assert sha(q) == row['sha256'] and q.stat().st_size == row['bytes']
        paths.append(q)
    inv = inventory()
    files = {str(p): dict(bytes=p.stat().st_size, sha256=sha(p)) for p in paths}
    files.update({str(DATA / n): v for (n, v) in inv.items()})
    snap = BASE / 'source_snapshot'
    for q in paths:
        if q.suffix in ('.py', '.ps1', '.sh', '.yaml'):
            target = snap / q.relative_to(ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as out:
                out.write(q.read_bytes())
    save('freeze.json', dict(files=files, inventory=inv, repositories=s.repositories(), scope='DSR0', caps=dict(Windows_seconds=300, Linux_RSS_bytes=128 * 2 ** 20, GPU_bytes=0, artifact_bytes=8 * 2 ** 20)))
    save('INCOMPLETE', dict(scope='DSR0', pending='source audit and independent validation'))
    print('DSR0 frozen', len(files), 'identities', len(inv), 'input files', flush=True)

def verify():
    f = read(BASE / 'freeze.json')
    assert inventory() == f['inventory']
    for (name, row) in f['files'].items():
        q = Path(name)
        assert sha(q) == row['sha256'] and q.stat().st_size == row['bytes']
    assert s.repositories() == f['repositories']
    return f

def header(q):
    body = b''
    with q.open('rb') as stream:
        while True:
            line = stream.readline(4097)
            assert line and len(line) <= 4096 and (len(body) + len(line) <= 65536)
            body += line
            if q.suffix == '.ply' and line.strip() == b'end_header':
                break
            if q.suffix == '.pcd' and line.split()[:1] == [b'DATA']:
                break
    text = body.decode('ascii')
    if q.suffix == '.ply':
        assert text.splitlines()[0] == 'ply'
        count = [int(t.split()[2]) for t in text.splitlines() if t.startswith('element vertex ')]
    else:
        count = [int(t.split()[1]) for t in text.splitlines() if t.startswith('POINTS ')]
    assert len(count) == 1 and count[0] >= 0
    return dict(header_bytes=len(body), header_SHA256=hashlib.sha256(body).hexdigest(), declared_points=count[0], raw_header=text, coordinate_payload_decoded=False)

def tree(path):
    return ast.parse((ROOT / path).read_text())

def function(path, name):
    found = [n for n in ast.walk(tree(path)) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name]
    assert len(found) == 1
    return found[0]

def audit():
    f = verify()
    rows = []
    for (name, row) in f['inventory'].items():
        q = DATA / name
        assert q.suffix in ('.ply', '.pcd')
        rows.append(dict(path=name, scene=str(Path(name).parent), extension=q.suffix, bytes=row['bytes'], sha256=row['sha256'], **header(q)))
    snippets = []
    specs = [('demo.py', 'process_point_clouds'), ('demo.py', 'main'), ('dataset_process/utils/io_utils.py', 'save_processed_sample'), ('rectified_point_flow/data/dataset.py', '_load_from_folder'), ('rectified_point_flow/data/dataset.py', '_transform'), ('rectified_point_flow/data/datamodule.py', 'setup'), ('rectified_point_flow/eval/evaluator.py', '_compute_metrics')]
    for (path, name) in specs:
        node = function(path, name)
        lines = (ROOT / path).read_text().splitlines(keepends=True)
        excerpt = ''.join(lines[node.lineno - 1:node.end_lineno])
        snippets.append(dict(path=path, function=name, line_start=node.lineno, line_end=node.end_lineno, source_SHA256=sha(ROOT / path), excerpt=excerpt))
    demo = tree('demo.py')
    savecalls = [n for n in ast.walk(demo) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and (n.func.id == 'save_processed_sample')]
    assert len(savecalls) == 1 and len(savecalls[0].args) == 3 and (not savecalls[0].keywords)
    loader = ast.unparse(function('rectified_point_flow/data/dataset.py', '_load_from_folder'))
    transform = ast.unparse(function('rectified_point_flow/data/dataset.py', '_transform'))
    assert "'pointclouds_gt': pcs" in loader and "glob.glob(os.path.join(folder, '*.ply'))" in loader
    assert "pcs_gt = data['pointclouds_gt']" in transform
    assert 'rot = np.eye(3)' in transform and "results['translations'] = trans.astype(np.float32)" in transform
    assert '(pts_gt, gt_trans) = center_pcd(pts_gt)' in transform
    assert "'*.txt'" not in loader and 'loadtxt' not in loader
    main_source = ast.unparse(function('demo.py', 'main'))
    assert "f.endswith('.ply')" in main_source
    assert 'if args.eval_on:' in main_source and 'print_eval_table(' in main_source
    setup = ast.unparse(function('rectified_point_flow/data/datamodule.py', 'setup'))
    assert "elif stage in ['test', 'predict']:" in setup and "split='val'" in setup
    evaluator = ast.unparse(function('rectified_point_flow/eval/evaluator.py', '_compute_metrics'))
    assert "pts_gt = data['pointclouds_gt']" in evaluator and "trans_gt = data['translations']" in evaluator
    scenes = sorted({r['scene'] for r in rows})
    scene_rows = [dict(scene=name, files=sum((r['scene'] == name for r in rows)), demo_PLY_files=sum((r['scene'] == name and r['extension'] == '.ply' for r in rows)), PCD_files=sum((r['scene'] == name and r['extension'] == '.pcd' for r in rows)), role='SOURCE_IDENTITY_REFERENCE_TRAINING_MEMBERSHIP_UNAUTHENTICATED_NOT_UNTOUCHED') for name in scenes]
    result = dict(decision='EXISTING_DEMO_DEFAULT_REFERENCE_IS_SUPPLIED_COORDINATES_NOT_AUTHENTICATED_EXTERNAL_POSES', files=rows, scenes=scene_rows, complete_local_files=len(rows), complete_local_scenes=len(scenes), extensions=dict(Counter((r['extension'] for r in rows))), total_bytes=sum((r['bytes'] for r in rows)), scoped_external_reference_sidecar_files=0, all_history_access_complete=False, header_pose_fields_are_not_authenticated_cross_scan_reference=True, author_RegX_scene_byte_link_established=False, checkpoint_training_exclusion_established=False, default_eval_on_only_prints=True, source_supplied_reference_not_measured_accuracy=True, demo_clouds_wrong_or_unregistered_established=False, point_payload_or_GT_or_model_calls=0, new_cohort_or_efficacy_admitted=False)
    save('headers_and_roles.json', result)
    save('source_citations.json', dict(citations=snippets))
    save('audit_seal.json', dict(files={n: dict(sha256=sha(BASE / n), bytes=(BASE / n).stat().st_size) for n in ('headers_and_roles.json', 'source_citations.json')}))
    verify()
    print(json.dumps({k: result[k] for k in ('decision', 'complete_local_files', 'complete_local_scenes', 'extensions', 'total_bytes')}), flush=True)

def usage():
    return dict(wall_seconds=time.monotonic() - START, peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024, peak_GPU_allocated_bytes=0, peak_GPU_reserved_bytes=0, artifact_bytes=size(), point_payload_model_GT_metric_calls=0)

def run(stage):
    spent = sum((read(q)['wall_seconds'] for folder in (BASE.parent / 'supervision', SUP) for q in folder.glob('*/exit.json')))
    assert spent < 300
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('DSR0 aggregate cap')))
    signal.alarm(max(1, int(300 - spent)))
    (ok, error) = (False, None)
    try:
        if stage == 'freeze':
            freeze()
        elif stage == 'audit':
            audit()
        elif stage == 'validate':
            import validate_demo_source_roles_attempt02 as v
            v.validate()
        else:
            raise ValueError(stage)
        u = usage()
        assert u['peak_RSS_bytes'] <= 128 * 2 ** 20 and u['artifact_bytes'] < 8 * 2 ** 20
        if (SUP / 'host_latest.json').exists():
            assert read(SUP / 'host_latest.json')['headroom_bytes'] >= 4 * 2 ** 30
        ok = True
    except BaseException as ex:
        error = repr(ex)
        traceback.print_exc()
        save('FAILURE_' + stage + '.json', dict(error=error, **usage()))
    finally:
        signal.alarm(0)
        save('supervision/' + stage + '/child_exit.json', dict(success=ok, error=error, full_resource_capture=True, **usage()))
    if not ok:
        sys.exit(1)
if __name__ == '__main__':
    run(sys.argv[1])
