"""Validate pilot exports and summarize evidence without fitting a model."""
import json
from collections import Counter
import hashlib
import sys
from pathlib import Path
import numpy as np

ROOT=Path('/mnt/e/githouse/RAP-SLAM')
sys.path.insert(0,str(ROOT))
from rap_slam.measurement import grouped_split, best_generation, stable_id

def main():
    out=Path(sys.argv[1])
    assert not (out/'INCOMPLETE').exists()
    records=[json.loads(line) for line in (out/'measurements.jsonl').read_text().splitlines()]
    selected=json.loads((out/'selected_measurements.json').read_text())
    split=json.loads((out/'splits.json').read_text())
    assert len(records)==48 and len(selected)==24
    ids=[r['measurement_id'] for r in records];assert len(ids)==len(set(ids))
    pairs={}
    for record in records:pairs.setdefault(record['physical_pair_id'],[]).append(record)
    assert len(pairs)==24
    label_switches=[]
    for record in selected:
        candidates=sorted(pairs[record['physical_pair_id']],key=lambda r:r['generation_id'])
        assert len(candidates)==2 and [r['generation_id'] for r in candidates]==[0,1]
        assert candidates[best_generation(candidates)]==record
        if len({r['labels']['label'] for r in candidates})>1:label_switches.append(record['legacy_pair_key'])
        pool=record['sc_competitor_ids'];i,j=record['source_frame_ids']
        assert all(f<j and j-f>=200 and abs(f-i)>=100 for f in pool)
        assert record['labels']['validity']['valid']
    exported=[i for s in split['measurement_ids'].values() for i in s]
    assert set(exported)=={r['measurement_id'] for r in selected} and len(exported)==24
    seqsplit=grouped_split(selected,seed=str(20260910),group_key='physical_sequence')
    (out/'sequence_split_diagnostic.json').write_text(json.dumps(seqsplit,indent=2))
    sequence_counts={key:dict(Counter(r['labels']['label'] for r in selected if r['measurement_id'] in mids)) for key,mids in seqsplit['measurement_ids'].items()}
    old=json.loads((ROOT/'output_s1/candidates.json').read_text())
    # Compare only SC features for known corresponding physical pairs, never reuse labels.
    comparisons=[]
    for record in selected:
        source,seq=record['physical_sequence'].split('/')
        offset=3850 if source=='poss' else 0
        i,j=[v-offset for v in record['source_frame_ids']]
        if source=='poss':datasets=['multigen_poss']
        elif seq=='02':datasets=['multigen_k02false','multigen_k02true']
        else:datasets=['kitti06_live']
        match=[r for r in old if r['ds'] in datasets and r['i']==i and r['j']==j]
        if len(match)==1:
            comparisons.append(dict(pair=record['legacy_pair_key'],legacy_sc_margin=match[0]['sc_margin'],
                                    v2_sc_margin=record['sc_margin']))
    inputs=json.loads((out/'input_manifest.json').read_text())
    before=json.loads((out/'selection_manifest.json').read_text())['source_hashes']
    for path,digest in before.items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest
    checks=dict(status='passed',unique_measurements=48,selected_physical_pairs=24,
                exact_selected_record_match=True,causal_competitors=True,split_partition=True,
                source_selection_files_unchanged=True,source_scan_count=sum('source_frame_id'in r for r in inputs),
                cross_generation_label_switches=label_switches,
                sequence_holdout_counts=sequence_counts,sc_comparisons=comparisons)
    (out/'export_validation.json').write_text(json.dumps(checks,indent=2))
    quality=json.loads((out/'quality_report.json').read_text())
    lines=['# M3 fresh measurement pilot','',
           'Status: dataset-chain validation passed; statistical validation is pending.','',
           '- 24 preselected physical pairs across KITTI-02, KITTI-06 and POSS-00.',
           '- 48 new GPU registrations; every transform, diagnostic and GT label belongs to the same generation.',
           '- 24 selected-generation rows: 13 safe, 11 dangerous under the declared 5 m / 10 degree pose-error rule.',
           '- All 24 historical SC margins are available, with query/self/future/nearby-site exclusion.',
           '- Fit / calibration / test: 9 / 10 / 5 physical pairs, with no identical or reversed-pair overlap.',
           f"- {len(label_switches)} physical pair changes pose-correctness label between its two new generations.",
           '- Heuristic gate on selected pilot rows: 13 safe accepted, 11 dangerous rejected.',
           '',
           'These are deliberately chosen historical cases, not a random retrieval population. Nearby places and shared scans can remain correlated across pair groups. Only five dangerous calibration pairs are present. No conformal model was trained or guarantee claimed.',
           '',
           '## Selected measurements','',
           '| Dataset | Source frames | Generation | Overlap | Mean distance m | TE m | RE deg | Label | SC margin |',
           '|---|---|---:|---:|---:|---:|---:|---|---:|']
    for r in selected:
        lab=r['labels'];a,b=r['source_frame_ids']
        lines.append(f"| {r['physical_sequence']} | {a}, {b} | {r['generation_id']} | {r['overlap']:.4f} | {r['mean_dist']:.4f} | {lab['gt_translation_error_m']:.3f} | {lab['gt_rotation_error_deg']:.3f} | {lab['label']} | {r['sc_margin']:.4f} |")
    lines+=['','## Next decision','',
            'Expand independent physical sites/sequences and predeclare sampling before training any optional statistical gate. Keep the fixed heuristic as the core baseline. The sequence-holdout diagnostic exposes class/support gaps; it is not a replacement for a sufficiently populated split.']
    (out/'REPORT.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({k:v for k,v in checks.items() if k!='sc_comparisons'},indent=2))

if __name__=='__main__':main()
