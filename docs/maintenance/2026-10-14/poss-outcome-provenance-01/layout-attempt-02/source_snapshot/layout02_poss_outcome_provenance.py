"""POP0 surviving outcome lineage, without pose computation or model imports."""
import time
START = time.monotonic()
import ast
import json
import math
import resource
import signal
import sys
import traceback
from pathlib import Path
import physical_source_role_feasibility as s
(ROOT, SLAM) = (s.ROOT, s.SLAM)
BASE = ROOT / 'docs/maintenance/2026-10-14/poss-outcome-provenance-01/layout-attempt-02'
SUP = BASE / 'supervision'
PEL = ROOT / 'docs/maintenance/2026-10-14/poss-exposure-lineage-01'
B = SLAM / 'output_possb_smoke'
CAL = SLAM / 'output_calibrated'
POSS = SLAM / 'data/poss/dataset'
(read, sha) = (s.read, s.sha)

def size():
    return sum((p.stat().st_size for p in BASE.rglob('*') if p.is_file()))

def save(name, value):
    body = (json.dumps(value, indent=2, allow_nan=False) + '\n').encode()
    assert size() + len(body) < 16 * 2 ** 20
    with (BASE / name).open('xb') as stream:
        stream.write(body)

def freeze():
    paths = [BASE / n for n in ('OWNER_SCOPE.md', 'PROTOCOL.md', 'PUBLIC_SOURCE_NOTES.md')]
    paths += [Path(__file__), Path(__file__).with_name('validate_poss_outcome_provenance.py'), Path(__file__).with_name('physical_source_role_feasibility.py'), Path(__file__).with_name('invoke_mgr_supervised_wsl.ps1')]
    paths += [PEL / n for n in ('freeze.json', 'source_census.json', 'REPORT.md', 'STATUS.json', 'DELIVERY_SEAL.json')]
    paths += [ROOT / 'docs/maintenance' / n for n in s.MARKERS]
    paths += [ROOT / 'docs/maintenance/2026-10-14/physical-comparison-contract-01/INCOMPLETE']
    paths += sorted((p for p in B.iterdir() if p.is_file()))
    paths += [CAL / n for n in ('edge_dataset.json', 'fit_report.json', 'fit_report.md')]
    paths += [SLAM / 'scripts' / n for n in ('download_poss_segment.py', 'eval_calibrated_weighting.py', 'eval_gnc_backend.py', 'build_s1_features.py')]
    paths += [SLAM / 'rap_slam/real_dataset.py', SLAM / 'data/poss/download_b.log', POSS / 'sequences/00/calib_readme.txt']
    assert not (BASE / 'freeze.json').exists()
    files = {str(p): dict(sha256=sha(p), bytes=p.stat().st_size) for p in paths}
    assert set((p.name for p in B.iterdir())) == {'summary.json', 'odom_poses.txt', 'optimized_poses.txt', 'merged_map_odometry.ply', 'merged_map_optimized.ply', 'trajectory_plot.png'}
    snap = BASE / 'source_snapshot'
    snap.mkdir()
    for p in paths:
        if p.suffix in ('.py', '.ps1'):
            name = ('slam_' if SLAM in p.parents else 'main_') + p.name
            with (snap / name).open('xb') as stream:
                stream.write(p.read_bytes())
    save('freeze.json', dict(files=files, repositories=s.repositories(), caps=dict(Windows_seconds=600, RSS_bytes=512 * 2 ** 20, GPU_bytes=0, whole_dossier_bytes=16 * 2 ** 20)))
    save('INCOMPLETE', dict(scope='POP0', pending='census and independent validation'))
    print('POP0 frozen', len(files), 'identities', flush=True)

def verify():
    f = read(BASE / 'freeze.json')
    for (path, row) in f['files'].items():
        assert sha(path) == row['sha256'] and Path(path).stat().st_size == row['bytes'], path
    assert s.repositories() == f['repositories']
    return f

def citations(path, terms):
    lines = path.read_text().splitlines()
    return [dict(line=i + 1, text=line) for (i, line) in enumerate(lines) if any((term in line for term in terms))]

def census():
    verify()
    summary = read(B / 'summary.json')
    config = summary['config']
    assert (config['real_start'], config['real_end'], config['real_stride']) == (6750, 9500, 1)
    assert config['source'] == 'real' and config['real_root'].endswith('/data/poss')
    assert config['real_apply_calib'] is False
    assert summary['n_scans'] == 2751 and summary['n_keyframes'] == 153
    loops = summary['accepted_loops']
    assert len(loops) == summary['n_loops_accepted'] == summary['n_loop_candidates'] == 12
    assert all(('T_rel' not in e for e in loops))
    for e in loops:
        assert all((isinstance(e[k], int) and 0 <= e[k] < 2751 for k in ('i', 'j')))
        assert all((math.isfinite(e[k]) for k in ('overlap', 'gt_trans_err', 'gt_rot_err_deg')))
    rows = []
    for name in ('odom_poses.txt', 'optimized_poses.txt'):
        lines = [line.split() for line in (B / name).read_text().splitlines() if line.strip() and (not line.lstrip().startswith('#'))]
        assert len(lines) == 2751 and {len(line) for line in lines} == {12}
        rows.append(dict(path=str(B / name), data_rows=len(lines), columns=12, coordinates_interpreted=False))
    edges = read(CAL / 'edge_dataset.json')
    subset = [e for e in edges if e['ds'] == 'possb']
    assert len(subset) == 12
    keyed = {(e['i'], e['j']): e for e in subset}
    assert len(keyed) == 12
    for e in loops:
        saved = keyed[e['i'], e['j']]
        assert (saved['gt_te'], saved['gt_re'], saved['overlap']) == (e['gt_trans_err'], e['gt_rot_err_deg'], e['overlap'])
        assert math.isnan(saved['mean_dist']) and 'T_rel' not in saved
    fit_tags = {'kitti02', 'poss_off', 'poss_live', 'possb'}
    members = [e for e in edges if e['ds'] in fit_tags and math.isfinite(e['mean_dist'])]
    counts = {tag: sum((e['ds'] == tag for e in members)) for tag in sorted(fit_tags)}
    assert counts == dict(kitti02=182, poss_off=4, poss_live=2, possb=0)
    report_first = next((line for line in (CAL / 'fit_report.md').read_text().splitlines() if line.startswith('Fit set:')))
    assert report_first.startswith('Fit set: 188 edges') and len(members) == 188
    downloader = SLAM / 'scripts/download_poss_segment.py'
    tree = ast.parse(downloader.read_text())
    urls = [n.value.value for n in tree.body if isinstance(n, ast.Assign) and any((isinstance(t, ast.Name) and t.id == 'URL' for t in n.targets))]
    assert urls == ['http://www.poss.pku.edu.cn/OpenDataResource/poss_odomotry/data_odometry_velodyne.zip']
    fetch = next((n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'fetch'))
    assert isinstance(fetch.body[3], ast.If)
    condition = ast.unparse(fetch.body[3].test)
    assert condition == 'os.path.exists(dest) and os.path.getsize(dest) == info.file_size'
    cited = {}
    specs = [('download_poss_segment.py', ('URL =', 'getsize', 'rz.read', 'os.replace')), ('eval_calibrated_weighting.py', ('output_possb_smoke/summary.json', 'add("possb"', 'float(lc["gt_trans_err"])', 'float(lc["gt_rot_err_deg"])', 'fit_edges =', '"poss_live", "possb"', 'np.isfinite(e["mean_dist"])', 'Fit set:')), ('eval_gnc_backend.py', ('"edge_dataset.json"', '"poss_live", "possb"', 'np.isfinite(e["mean_dist"])')), ('build_s1_features.py', ('POSS segment B:', 'output_possb_smoke/odom_poses.txt', 'reg["possb"]'))]
    for (name, terms) in specs:
        path = SLAM / 'scripts' / name
        cited[str(path)] = citations(path, terms)
        assert cited[str(path)]
    loader = SLAM / 'rap_slam/real_dataset.py'
    cited[str(loader)] = citations(loader, ('POSS convention', 'z-up horizontal', 'calib similarity', 'apply_calib: bool = False', 'times_file ='))
    missing = {name: (B / name).exists() for name in ('source_frames.json', 'keyframes.json', 'run_manifest.json', 'archive_receipt.json')}
    assert not any(missing.values())
    old = read(PEL / 'source_census.json')
    assert old['category_counts']['configured_only_execution_unproven'] == 2751
    result = dict(decision='SURVIVING_POSS_B_OUTCOME_EXPOSURE_CONFIRMED_SOURCE_IDENTITY_UNAUTHENTICATED', reported_B_range=[6750, 9500], reported_scans=2751, reported_keyframes=153, reported_and_downstream_matching_loops=12, stored_relative_transforms=0, trajectory_structure=rows, finite_mean_dist_B=0, old_predicate_fit_membership=counts, old_predicate_fit_total=len(members), old_report_prose_parenthetical_inconsistent=True, B_old_calibration_fit_members=0, source_citations=cited, missing_B_manifest_queries=missing, saved_downloader_URL=urls[0], existing_file_resume_guard=condition, durable_archive_receipt_written_by_this_downloader=False, transfer_CRC_checks_ruled_out=False, source_frames_or_pose_timing_authenticated=False, old_PEL_partition_immutable=True, B_untouched_or_confirmation_admitted=False, historical_complete_execution_or_full_access_log_proven=False, new_model_solver_fit_or_metric_calls=0)
    save('outcome_census.json', result)
    save('census_seal.json', dict(path='outcome_census.json', sha256=sha(BASE / 'outcome_census.json')))
    verify()
    print(json.dumps({k: result[k] for k in ('decision', 'reported_and_downstream_matching_loops', 'old_predicate_fit_membership')}), flush=True)

def usage():
    return dict(wall_seconds=time.monotonic() - START, peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024, peak_GPU_allocated_bytes=0, peak_GPU_reserved_bytes=0, artifact_bytes=size(), new_model_calls=0, new_solver_calls=0, new_fit_calls=0, new_pose_metric_calls=0)

def cap():
    u = usage()
    assert u['peak_RSS_bytes'] <= 512 * 2 ** 20 and u['artifact_bytes'] < 16 * 2 ** 20, u
    if (SUP / 'host_latest.json').exists():
        assert read(SUP / 'host_latest.json')['headroom_bytes'] >= 4 * 2 ** 30

def run(stage):
    spent = sum((read(p)['wall_seconds'] for p in SUP.glob('*/exit.json')))
    assert spent < 600
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('POP0 cap')))
    signal.alarm(max(1, int(600 - spent)))
    (ok, error) = (False, None)
    try:
        if stage == 'freeze':
            freeze()
        elif stage == 'census':
            census()
        elif stage == 'validate':
            import validate_poss_outcome_provenance as v
            v.validate()
        else:
            raise ValueError(stage)
        cap()
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
