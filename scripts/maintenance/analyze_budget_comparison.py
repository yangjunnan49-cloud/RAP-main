"""Saved O2 candidate coverage and common-measurement comparison."""
import json
from pathlib import Path
import numpy as np

BASE = Path('/mnt/e/githouse/RAP-main/docs/maintenance/2026-09-13/optimization-o2-01')


def main():
    assert not (BASE/'INCOMPLETE').exists()
    report = json.loads((BASE/'summary.json').read_text())
    details = []
    for row in report['sequences']:
        name = row['sequence']
        arms = []
        records = []
        for budget in [12,40]:
            dest = BASE/name/str(budget)
            c = json.loads((dest/'candidates.json').read_text())
            pairs = set(map(tuple,c['merged']))
            prox = set(map(tuple,c['proximity']))
            events = [json.loads(s) for s in (dest/'verification_measurements.jsonl').read_text().splitlines()]
            gen = [e['measurement'] for e in events if e['event']=='generation']
            records.append({tuple(r['source_frame_ids']):r for r in gen})
            arms.append(dict(budget=budget,proximity_priority_pairs=len(pairs & prox),
                sc_only_pairs=len(pairs-prox),distinct_keyframes=len({i for p in pairs for i in p}),
                min_frame_gap=min((j-i for i,j in pairs),default=None),
                max_frame_gap=max((j-i for i,j in pairs),default=None)))
        shared = records[0].keys() & records[1].keys()
        delta = max((float(np.max(np.abs(np.asarray(records[0][p]['T_rel'])-np.asarray(records[1][p]['T_rel'])))) for p in shared),default=0)
        details.append(dict(sequence=name,arms=arms,shared_measurements=len(shared),
            shared_transform_max_abs_delta=delta,reference_order_matches=row['budget12_matches_reference_order'],
            reference_ape_delta=row['budget12_reference_ape_delta']))
    (BASE/'coverage_validation.json').write_text(json.dumps(details,indent=2))
    print(json.dumps(details,indent=2))


if __name__=='__main__':
    main()
