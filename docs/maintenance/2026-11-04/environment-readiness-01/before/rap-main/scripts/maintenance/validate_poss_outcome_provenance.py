"""Independent POP0 saved-outcome matching, structure and source rule checks."""
import ast
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'docs/maintenance/2026-10-14/poss-outcome-provenance-01'
SLAM = ROOT.parent / 'RAP-SLAM'


def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))


def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as stream:
        for body in iter(lambda: stream.read(65536), b''):
            h.update(body)
    return h.hexdigest()


def validate():
    f, c = read(BASE / 'freeze.json'), read(BASE / 'outcome_census.json')
    seal = read(BASE / 'census_seal.json')
    assert sha(BASE / seal['path']) == seal['sha256']
    for p, row in f['files'].items():
        assert sha(p) == row['sha256'] and Path(p).stat().st_size == row['bytes']
    b = SLAM / 'output_possb_smoke'
    summary = read(b / 'summary.json')
    assert [summary['config'][k] for k in ('real_start', 'real_end')] == c['reported_B_range']
    assert summary['config']['real_stride'] == 1
    assert summary['n_scans'] == c['reported_scans'] == 2751
    assert summary['n_keyframes'] == c['reported_keyframes'] == 153
    loops = summary['accepted_loops']
    edges = read(SLAM / 'output_calibrated/edge_dataset.json')
    saved = [e for e in edges if e['ds'] == 'possb']
    assert len(saved) == len(loops) == c['reported_and_downstream_matching_loops'] == 12
    assert len({(r['i'], r['j']) for r in loops}) == 12
    for row in loops:
        candidates = [e for e in saved if (e['i'], e['j']) == (row['i'], row['j'])]
        assert len(candidates) == 1
        e = candidates[0]
        for old, new in (('gt_trans_err', 'gt_te'), ('gt_rot_err_deg', 'gt_re'), ('overlap', 'overlap')):
            assert row[old] == e[new] and math.isfinite(e[new])
        assert not math.isfinite(e['mean_dist']) and math.isnan(e['mean_dist'])
        assert 'T_rel' not in e and 'T_rel' not in row
    tags = ('kitti02', 'poss_off', 'poss_live', 'possb')
    counts = Counter(e['ds'] for e in edges if e['ds'] in tags and math.isfinite(e['mean_dist']))
    expected = {tag: counts[tag] for tag in tags}
    assert expected == c['old_predicate_fit_membership']
    assert sum(expected.values()) == c['old_predicate_fit_total'] == 188
    assert counts['possb'] == c['B_old_calibration_fit_members'] == c['finite_mean_dist_B'] == 0
    for record in c['trajectory_structure']:
        lengths = []
        with Path(record['path']).open() as stream:
            for line in stream:
                if line.strip() and not line.lstrip().startswith('#'):
                    lengths.append(len(line.split()))
        assert len(lengths) == record['data_rows'] == 2751 and set(lengths) == {8}
        assert not record['coordinates_interpreted']
    for path, records in c['source_citations'].items():
        lines = Path(path).read_text().splitlines()
        assert records
        for record in records:
            assert lines[record['line']-1] == record['text']
    for path in ('scripts/eval_calibrated_weighting.py', 'scripts/eval_gnc_backend.py'):
        tree = ast.parse((SLAM / path).read_text())
        comps = [n for n in ast.walk(tree) if isinstance(n, ast.ListComp)
                 and isinstance(n.elt, ast.Name) and n.elt.id == 'e']
        candidates = [n for n in comps if 'possb' in ast.unparse(n)
                      and "np.isfinite(e['mean_dist'])" in ast.unparse(n)]
        assert len(candidates) == 1
    downloader = ast.parse((SLAM / 'scripts/download_poss_segment.py').read_text())
    url = next(n.value.value for n in downloader.body if isinstance(n, ast.Assign)
               and any(isinstance(t, ast.Name) and t.id == 'URL' for t in n.targets))
    assert url == c['saved_downloader_URL']
    fetch = next(n for n in downloader.body if isinstance(n, ast.FunctionDef) and n.name == 'fetch')
    guards = [n for n in fetch.body if isinstance(n, ast.If)]
    assert len(guards) == 1 and ast.unparse(guards[0].test) == c['existing_file_resume_guard']
    assert not any(isinstance(n, ast.Constant) and isinstance(n.value, str)
                   and ('receipt' in n.value.lower() or 'sha256' in n.value.lower())
                   for n in ast.walk(downloader))
    for name, exists in c['missing_B_manifest_queries'].items():
        assert exists == (b / name).exists() is False
    assert not c['source_frames_or_pose_timing_authenticated']
    assert not c['historical_complete_execution_or_full_access_log_proven']
    assert not c['B_untouched_or_confirmation_admitted']
    assert not c['transfer_CRC_checks_ruled_out']
    assert c['new_model_solver_fit_or_metric_calls'] == 0 and c['old_PEL_partition_immutable']
    result = dict(passed=True, frozen_identities=len(f['files']),
        matched_outcome_rows=12, B_fit_members=0, complete_old_fit_predicate_total=188,
        source_citations=sum(map(len, c['source_citations'].values())),
        structural_trajectory_rows=5502, no_new_pose_metric_or_fit=True,
        decision=c['decision'])
    with (BASE / 'validation.json').open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps(result), flush=True)
