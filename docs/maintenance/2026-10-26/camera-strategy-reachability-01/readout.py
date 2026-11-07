import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[3]
freeze = json.loads((ROOT / 'FREEZE.json').read_text(encoding='utf-8'))
for item in freeze['files']:
    path = Path(item['path'])
    assert path.stat().st_size == item['bytes']
    assert hashlib.sha256(path.read_bytes()).hexdigest() == item['sha256']
rows = json.loads(Path(freeze['cu1_rows']).read_text(encoding='utf-8'))
old = json.loads(Path(freeze['old_analysis']).read_text(encoding='utf-8'),
                 parse_int=str, parse_float=str)
by_pair = {}
for row in rows:
    by_pair.setdefault(row['key'], []).append(row)
assert len(rows) == 400 and len(by_pair) == 200 and all(len(v) == 2 for v in by_pair.values())
zero = {key for key, value in by_pair.items() if all(v['numerical_upper_count'] == 0 for v in value)}
out = []
for seq, expected in (('00', {'correct_accepted': 23, 'correct_rejected': 26,
                              'selection_miss': 3, 'proposal_unavailable': 23}),
                       ('08', {'correct_accepted': 17, 'correct_rejected': 13,
                               'selection_miss': 4, 'proposal_unavailable': 41})):
    arm = old['sequences'][seq]['arms']['N']
    seen = set()
    for category, count in expected.items():
        keys = set(arm['category_pairs'][category])
        assert len(keys) == count and not (keys & seen) and keys <= set(by_pair)
        seen |= keys
        out.append(dict(sequence=seq, historical_N_category=category, total_pairs=len(keys),
                        zero_support_both_pairs=len(keys & zero),
                        nonzero_optimistic_support_pairs=len(keys - zero),
                        zero_support_keys=sorted(keys & zero)))
    assert len(seen) == 75
    wrong = set(arm['incorrect_accept_pairs'])
    assert wrong <= seen
    out.append(dict(sequence=seq, historical_N_category='incorrect_accepted_subset',
                    total_pairs=len(wrong), zero_support_both_pairs=len(wrong & zero),
                    nonzero_optimistic_support_pairs=len(wrong - zero),
                    zero_support_keys=sorted(wrong & zero)))
result = dict(passed=True, cells=out, complete_CU1_pairs=len(by_pair),
    all_CU1_rows_retained=True, historical_category_counts_match=True,
    role='Post-hoc exposed categorical join only; not efficacy or an executable selector',
    raw_pose_image_model_calls=0)
with (ROOT / 'RESULTS.json').open('x', encoding='utf-8') as stream:
    json.dump(result, stream, indent=2)
print(json.dumps(out, indent=2))
