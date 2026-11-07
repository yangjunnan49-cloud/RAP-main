"""VR1 complete categorical join of already-sealed saved outputs only."""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'controls'
ER = ROOT.parent / 'visual-essential-refinement-01'
spec = importlib.util.spec_from_file_location('er1_saved_helpers', ER / 'baseline_lib.py')
lib = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lib)

try:
    freeze = lib.load(ROOT / 'SOURCE_FREEZE.json')
    for e in freeze['files']:
        assert Path(e['path']).stat().st_size == e['bytes'] and lib.sha(e['path']) == e['sha256']
    binding = lib.load(ROOT / 'INPUT_BINDING.json')
    for name in ('ER1_rows', 'CF1_rows', 'old_analysis'):
        e = binding[name]
        assert Path(e['path']).stat().st_size == e['bytes'] and lib.sha(e['path']) == e['sha256']
    visual = lib.load(Path(binding['ER1_rows']['path']))
    support = lib.load(Path(binding['CF1_rows']['path']))
    old = lib.load(Path(binding['old_analysis']['path']))
    assert len(visual) == 200 and len({r['key'] for r in visual}) == 200 and len(support) == 400
    bysupport = {}
    for r in support:
        bysupport.setdefault(r['key'], []).append(r)
    assert set(bysupport) == {r['key'] for r in visual} and all(len(v) == 2 for v in bysupport.values())
    categories, wrong = {}, set()
    expected = {'00': {'correct_accepted': 23, 'correct_rejected': 26, 'selection_miss': 3, 'proposal_unavailable': 23},
                '08': {'correct_accepted': 17, 'correct_rejected': 13, 'selection_miss': 4, 'proposal_unavailable': 41}}
    for seq in ('00', '08'):
        arm = old['sequences'][seq]['arms']['N']
        for category, count in expected[seq].items():
            keys = arm['category_pairs'][category]
            assert len(keys) == count
            for key in keys:
                assert key not in categories
                categories[key] = category
        wrong.update(arm['incorrect_accept_pairs'])
    rows = []
    for r in visual:
        pose = r['status'] == 'POSE'
        category = 'confuser' if r['stratum'] == 'confuser' else categories[r['key']]
        rows.append({'key': r['key'], 'sequence': r['sequence'], 'stratum': r['stratum'],
            'historical_N_category': category, 'historical_N_incorrect_accepted_overlay': r['key'] in wrong,
            'visual_status': r['status'], 'visual_pose': pose,
            'visual_joint_5_15': bool(pose and r['rotation_error_deg'] <= 5 and r['direction_error_deg'] is not None and r['direction_error_deg'] <= 15),
            'visual_joint_10_30': bool(pose and r['rotation_error_deg'] <= 10 and r['direction_error_deg'] is not None and r['direction_error_deg'] <= 30),
            'CF1_both_zero_upper': all(s['half_pixel_edge_upper'] == 0 for s in bysupport[r['key']])})

    def summarize(data, name):
        return {'group': name, 'pairs': len(data), 'visual_pose': sum(r['visual_pose'] for r in data),
            'visual_no_evidence': sum(not r['visual_pose'] for r in data),
            'visual_joint_5_15': sum(r['visual_joint_5_15'] for r in data),
            'visual_joint_10_30': sum(r['visual_joint_10_30'] for r in data),
            'CF1_both_zero_upper': sum(r['CF1_both_zero_upper'] for r in data),
            'joint_5_15_with_CF1_both_zero': sum(r['visual_joint_5_15'] and r['CF1_both_zero_upper'] for r in data)}

    groups = [summarize(rows, 'all200')]
    for seq in ('00', '08'):
        data = [r for r in rows if r['sequence'] == seq]
        assert len(data) == 100 and sum(r['historical_N_category'] == 'confuser' for r in data) == 25
        groups.append(summarize(data, seq + '/all100'))
        for category in (*expected[seq], 'confuser'):
            cell = [r for r in data if r['historical_N_category'] == category]
            assert len(cell) == (25 if category == 'confuser' else expected[seq][category])
            groups.append(summarize(cell, seq + '/' + category))
        groups.append(summarize([r for r in data if r['historical_N_incorrect_accepted_overlay']], seq + '/incorrect_accepted_overlay'))
        groups.append(summarize([r for r in data if r['CF1_both_zero_upper']], seq + '/CF1_both_zero_upper'))
        groups.append(summarize([r for r in data if not r['CF1_both_zero_upper']], seq + '/CF1_not_both_zero_upper'))
    lib.save(OUT / 'ROWS.json', rows)
    lib.save(OUT / 'SUMMARY.json', {'groups': groups, 'role': 'Complete exposed saved-output categorical intersection, not metric-pose rescue or efficacy'})
    lib.complete(OUT, {'complete_pairs': 200, 'groups': len(groups), 'historical_partitions_match': True,
        'raw_image_pose_model_calls': 0, 'new_angles_or_metrics_computed': False})
    print('VR1 complete200-pair categorical join')
except BaseException as exc:
    lib.failure(OUT, exc)
    raise
