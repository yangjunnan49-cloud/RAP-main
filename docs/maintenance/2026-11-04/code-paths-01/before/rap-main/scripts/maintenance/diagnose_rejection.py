"""Bounded post-hoc diagnostic of immutable PG-DEV decisions; no fitted rule."""
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation

MAIN = Path('/mnt/e/githouse/RAP-main')
DOC = MAIN / 'docs/maintenance'
PG = DOC / '2026-09-15/proposal-context-dev-01'
SC = DOC / '2026-09-14/support-control-02'
OUT = DOC / '2026-09-15/rejection-diagnostic-01'


def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def save(name, data):
    with (OUT / name).open('x') as f:
        json.dump(data, f, indent=2, allow_nan=False)


def angle(a, b):
    # Polar projection removes only saved floating-point non-orthogonality.
    return float(np.degrees(Rotation.from_matrix(a.T @ b).magnitude()))


def stats(values):
    return dict(zip(['min', 'q25', 'median', 'q75', 'max'],
                    map(float, np.quantile(values, [0, .25, .5, .75, 1])))) if values else None


def main():
    assert not (OUT / 'summary.json').exists()
    (OUT / 'INCOMPLETE').write_text('Diagnostic running; no new inference.\n')
    manifests = [PG, SC, DOC / '2026-09-14/hl-v2/pilot-01']
    verified = {}
    for root in manifests:
        manifest = read(root / 'artifact_hashes.json')
        for rel, digest in manifest.items():
            assert sha(root / rel) == digest, root / rel
        verified[str(root.relative_to(DOC))] = len(manifest)
    gt_paths = {
        '00': DOC / '2026-09-14/hl-v2/data-expansion-01/00/evaluator_gt.npy',
        '08': DOC / '2026-09-14/support-control-01/data/08/evaluator_gt.npy'}
    # Bind GT to the existing data manifests, rather than only a new checksum.
    for seq, gp in gt_paths.items():
        candidates = list(gp.parent.parent.glob('*hash*.json'))
        found = False
        for mp in candidates:
            manifest = read(mp)
            for key, value in manifest.items():
                if isinstance(value, str) and value == sha(gp) and key.endswith('evaluator_gt.npy'):
                    found = True
        assert found, ('GT hash not found in data manifest', gp, candidates)
    sources = [Path(__file__), OUT / 'SCOPE.md'] + [r / 'artifact_hashes.json' for r in manifests] + list(gt_paths.values())
    save('input_freeze_v2.json', dict(utc=datetime.now(timezone.utc).isoformat(),
         hashes={str(p): sha(p) for p in sources}, verified_parent_counts=verified,
         scope='Observed development; old raw clouds not rehashed or regenerated'))
    all_rows = []
    summaries = {}
    checked_labels = 0
    max_t_delta = max_a_delta = 0.
    for seq in ['00', '08']:
        role = 'discovery' if seq == '00' else 'confirmation'
        decisions = read(PG / seq / 'evaluator_only_decisions.json')
        gates = read(PG / seq / 'gates.json')
        metrics = read(PG / seq / 'metrics.json')['overall']
        gt = np.load(gt_paths[seq])
        assert len(decisions) == 100
        for row in decisions:
            i, j = row['source_i'], row['source_j']
            key = f'{seq}_{i}_{j}'
            truth = np.linalg.solve(gt[i], gt[j])
            for arm, root in [('A', SC / role), ('P', PG / seq)]:
                bank = [read(root / 'bank' / f'{key}_{k}.json') for k in range(4)]
                assert all(b['validity']['valid'] for b in bank)
                transforms = [np.asarray(b['T'], dtype=float) for b in bank]
                labels = []
                for k, t in enumerate(transforms):
                    assert np.linalg.norm(t[:3, :3].T @ t[:3, :3] - np.eye(3)) < 1e-4
                    error = np.linalg.solve(truth, t)
                    te = float(np.linalg.norm(error[:3, 3]))
                    r = error[:3, :3]
                    sine = np.linalg.norm([r[2, 1]-r[1, 2], r[0, 2]-r[2, 0], r[1, 0]-r[0, 1]]) / 2
                    ae = float(np.degrees(np.arctan2(sine, np.clip((np.trace(r)-1)/2, -1, 1))))
                    labels.append(dict(RTE_m=te, RRE_deg=ae, strict=te <= 1 and ae <= 5))
                    g = gates[key][arm][k]
                    assert g['accepted'] == (g['overlap_ratio'] >= .7 and g['mean_dist'] <= 2.5)
                for name, v in row['methods'].items():
                    if not name.startswith(arm):
                        continue
                    lab = labels[v['generation']]
                    td, ad = abs(v['RTE_m'] - lab['RTE_m']), abs(v['RRE_deg'] - lab['RRE_deg'])
                    max_t_delta, max_a_delta = max(max_t_delta, td), max(max_a_delta, ad)
                    assert td < 1e-7 and ad < 1e-7, (key, name, td, ad)
                    assert lab['strict'] == v['strict']
                    assert v['accepted'] == gates[key][arm][v['generation']]['accepted']
                    checked_labels += 1
                name = arm + '-R4'
                v = row['methods'][name]
                k = min(range(4), key=lambda z: (bank[z]['rigidity_rmse_m'], z))
                assert k == v['generation']
                dt = np.array([[np.linalg.norm(a[:3, 3] - b[:3, 3]) for b in transforms] for a in transforms])
                da = np.array([[angle(a[:3, :3], b[:3, :3]) for b in transforms] for a in transforms])
                neighbors = int(sum(dt[k, z] <= 1 and da[k, z] <= 5 for z in range(4) if z != k))
                g = gates[key][arm][k]
                category = ('correct' if v['strict'] else 'incorrect') + ('_accepted' if v['accepted'] else '_rejected')
                clauses = []
                if g['overlap_ratio'] < .7:
                    clauses.append('overlap')
                if g['mean_dist'] > 2.5:
                    clauses.append('distance')
                all_rows.append(dict(sequence=seq, method=name, key=key, source_i=i, source_j=j,
                    stratum=row['stratum'], category=category, legacy_safe=v['legacy_safe'],
                    RTE_m=v['RTE_m'], RRE_deg=v['RRE_deg'], generation=k,
                    overlap=g['overlap_ratio'], mean_distance=g['mean_dist'],
                    rigidity=bank[k]['rigidity_rmse_m'], translation_spread_m=float(dt.max()),
                    rotation_spread_deg=float(da.max()), selected_neighbors=neighbors,
                    candidate_strict_count=sum(l['strict'] for l in labels),
                    rejected_clauses='+'.join(clauses) or 'none'))
        for method in ['A-R4', 'P-R4']:
            rr = [r for r in all_rows if r['sequence'] == seq and r['method'] == method]
            counts = Counter(r['category'] for r in rr)
            assert counts['correct_accepted'] == metrics[method]['correct_positive_accepts']
            assert counts['incorrect_accepted'] == metrics[method]['incorrect_accepted']
            assert counts['correct_accepted'] + counts['correct_rejected'] == metrics[method]['strict_positive_successes']
            features = ['overlap', 'mean_distance', 'rigidity', 'translation_spread_m', 'rotation_spread_deg', 'selected_neighbors']
            groups = {c: [r for r in rr if r['category'] == c] for c in ['correct_accepted', 'incorrect_accepted', 'correct_rejected', 'incorrect_rejected']}
            good, bad = groups['correct_accepted'], groups['incorrect_accepted']
            auc = {}
            for feature in features:
                # Higher overlap/neighbors and lower distance/dispersion are the stated confidence directions.
                sign = 1 if feature in ['overlap', 'selected_neighbors'] else -1
                comparisons = [sign * (g[feature] - b[feature]) for g in good for b in bad]
                auc[feature] = sum((x > 0) + .5 * (x == 0) for x in comparisons) / len(comparisons)
            summaries[f'{seq}/{method}'] = dict(counts=dict(counts),
                by_stratum={s: dict(Counter(r['category'] for r in rr if r['stratum'] == s)) for s in sorted({r['stratum'] for r in rr})},
                correct_rejected_clauses=dict(Counter(r['rejected_clauses'] for r in groups['correct_rejected'])),
                incorrect_accepted_legacy_unsafe=sum(not r['legacy_safe'] for r in bad),
                groups={c: dict(n=len(rows), features={f: stats([r[f] for r in rows]) for f in features},
                    selected_neighbor_histogram=dict(Counter(r['selected_neighbors'] for r in rows))) for c, rows in groups.items()},
                accepted_correctness_auc=auc,
                incorrect_accepted_pairs=[r['key'] for r in bad],
                incorrect_unique_source_i=len({r['source_i'] for r in bad}),
                incorrect_unique_source_j=len({r['source_j'] for r in bad}),
                accepted_unique_scan_ids=len({r[f] for r in good + bad for f in ['source_i', 'source_j']}))
    save('pairs.json', all_rows)
    save('summary.json', summaries)
    for p, digest in read(OUT / 'input_freeze_v2.json')['hashes'].items():
        assert sha(Path(p)) == digest
    save('validation.json', dict(passed=True, selections_and_labels=checked_labels,
        candidate_gates=1600, diagnostic_rows=len(all_rows), verified_parent_counts=verified,
        max_translation_label_delta=max_t_delta, max_rotation_label_delta_deg=max_a_delta,
        rotation_note='Labels reconstructed with linear solves and the original atan2 definition; dispersion uses scipy rotation projection.',
        recovery_note='First attempt stopped before diagnostic outputs: translation subtraction did not preserve inverse-GT metric under finite GT precision. Original freeze retained; corrected exact metric semantics in v2.',
        raw_geometry_recomputed=False, raw_clouds_rehashed=False))
    print(json.dumps({k: {f: v[f] for f in ['counts', 'correct_rejected_clauses', 'incorrect_accepted_legacy_unsafe', 'accepted_correctness_auc']} for k, v in summaries.items()}, indent=2))


if __name__ == '__main__':
    main()
