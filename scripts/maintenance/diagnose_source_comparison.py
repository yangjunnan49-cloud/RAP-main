"""Descriptive O3 measurement diagnostics; never selects edges using GT."""
import json
from pathlib import Path
import numpy as np
from source_allocation import select

BASE = Path('/mnt/e/githouse/RAP-main/docs/maintenance/2026-09-13')


def read_records(path):
    events = [json.loads(s) for s in path.read_text().splitlines()]
    return {tuple(e['measurement']['source_frame_ids']): e['measurement']
            for e in events if e['event']=='generation'}


def stats(records):
    return dict(n=len(records), **{key: float(np.median([r['labels'][key] for r in records]))
        if records else None for key in ['gt_translation_error_m','gt_rotation_error_deg']})


def main():
    out = BASE/'optimization-o3-01'
    assert not (out/'INCOMPLETE').exists()
    rows = []
    for name in ['poss','kitti06','kitti05','kitti00']:
        dest = out/name/'12'
        candidates = json.loads((dest/'candidates.json').read_text())
        selected, allocation = select(candidates['proximity'],candidates['scan_context'])
        assert [list(p) for p in selected] == candidates['merged']
        assert allocation == candidates['allocation']
        old = read_records(BASE/'optimization-o2-01'/name/'12/verification_measurements.jsonl')
        new = read_records(dest/'verification_measurements.jsonl')
        common = old.keys() & new.keys()
        added = new.keys()-old.keys()
        removed = old.keys()-new.keys()
        rows.append(dict(sequence=name,common=len(common),added=len(added),removed=len(removed),
            common_transform_max_abs_delta=max((float(np.max(np.abs(np.asarray(old[k]['T_rel'])-np.asarray(new[k]['T_rel'])))) for k in common),default=0),
            baseline=stats(list(old.values())),balanced=stats(list(new.values())),
            added_measurements=stats([new[k] for k in added]),removed_measurements=stats([old[k] for k in removed])))
    (out/'diagnostics.json').write_text(json.dumps(dict(selection_recomputed=True,sequences=rows),indent=2))
    print(json.dumps(rows,indent=2))


if __name__=='__main__':
    main()
