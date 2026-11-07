"""Post-hoc read-only diagnosis of the frozen pilot; no scoring or gate changes."""
import json, hashlib
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation

BASE = Path('/mnt/e/githouse/RAP-main/docs/maintenance/2026-09-14/hl-v2')
PILOT = BASE / 'pilot-01'
OUT = BASE / 'diagnostic-01'
def read(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def stats(v):
    return dict(median=float(np.median(v)), p90=float(np.percentile(v, 90)), maximum=float(np.max(v)))

frozen = read(PILOT / 'artifact_hashes.json')
assert all(sha(PILOT / p) == h for p, h in frozen.items())
OUT.mkdir(exist_ok=False)
results = {}
for role, seq in [('discovery', '00'), ('confirmation', '02')]:
    folder = PILOT / role
    decisions = read(folder / 'evaluator_only_decisions.json')
    inputs = read(folder / 'inputs.json')
    oracle = read(folder / 'oracle_only.json')
    gt = np.load(BASE / 'data-expansion-01' / seq / 'evaluator_gt.npy')
    rows = []; motion = []
    for d, inp, o in zip(decisions, inputs, oracle):
        i, j = d['source_i'], d['source_j']
        assert (i, j) == (inp['source_i'], inp['source_j']) == (o['source_i'], o['source_j'])
        bank = [read(folder / 'bank' / f'{seq}_{i}_{j}_{g}.json') for g in range(4)]
        b, s = d['methods']['B4'], d['methods']['S4']
        local_errors = []
        for anchor, name in [(i, 'support_i'), (j, 'support_j')]:
            for support in inp[name]:
                expected = np.linalg.inv(gt[anchor]) @ gt[support['source_id']]
                actual = np.array(support['local_pose'])
                t = float(np.linalg.norm(actual[:3, 3] - expected[:3, 3]))
                r = float(np.degrees(Rotation.from_matrix(actual[:3, :3].T @ expected[:3, :3]).magnitude()))
                record = dict(anchor=anchor, support=support['source_id'], translation_m=t, rotation_deg=r, age_s=support['age_s'])
                motion.append(record); local_errors.append(record)
        rows.append(dict(source_i=i, source_j=j, stratum=d['stratum'],
            selection_changed=b['generation'] != s['generation'],
            gained_strict=not b['strict'] and s['strict'], lost_strict=b['strict'] and not s['strict'],
            clipped_error_delta=s['clipped_error']-b['clipped_error'],
            support_range=max(x['support']['score'] for x in bank)-min(x['support']['score'] for x in bank),
            B4=b, S4=s, R4=d['methods']['R4'], OR4=o['OR4'], local_motion=local_errors))
    strata = {}
    for name in sorted({r['stratum'] for r in rows}):
        rr = [r for r in rows if r['stratum'] == name]
        strata[name] = dict(n=len(rr), changed=sum(r['selection_changed'] for r in rr),
            gained=sum(r['gained_strict'] for r in rr), lost=sum(r['lost_strict'] for r in rr),
            clipped_delta_sum=sum(r['clipped_error_delta'] for r in rr),
            support_range=stats([r['support_range'] for r in rr]),
            B4_incorrect_accepted=sum(r['B4']['incorrect_accepted'] for r in rr),
            S4_incorrect_accepted=sum(r['S4']['incorrect_accepted'] for r in rr),
            S4_legacy_unsafe_accepted=sum(r['S4']['accepted'] and not r['S4']['legacy_safe'] for r in rr),
            oracle_correct_but_S4_rejected=sum(r['OR4']['strict'] and not r['S4']['accepted'] for r in rr))
    results[role] = dict(strata=strata, local_translation_m=stats([r['translation_m'] for r in motion]),
        local_rotation_deg=stats([r['rotation_deg'] for r in motion]), support_age_s=stats([r['age_s'] for r in motion]),
        support_records=len(motion), unique_support_links=len({(r['anchor'], r['support']) for r in motion}), pairs=rows)

with (OUT / 'diagnostics.json').open('x') as f: json.dump(results, f, indent=2, allow_nan=False)
lines = ['# HL-V2 frozen-bank failure diagnosis', '',
    'Post-hoc descriptive analysis only. Both roles are now development data. The original STOP_NEURAL_EXPANSION decision is unchanged; no new selector, threshold, generation or training.', '',
    '| Role | Stratum | Changed selection | Strict gained/lost | Sum S4-B4 clipped error | S4 incorrect accepts | Of these legacy unsafe | Oracle correct but S4 rejected |',
    '|---|---|---:|---:|---:|---:|---:|---:|']
for role, result in results.items():
    for name, s in result['strata'].items():
        lines.append(f"| {role} | {name} | {s['changed']}/25 | {s['gained']}/{s['lost']} | {s['clipped_delta_sum']:.6f} | {s['S4_incorrect_accepted']} | {s['S4_legacy_unsafe_accepted']} | {s['oracle_correct_but_S4_rejected']} |")
lines += ['', 'Confusers are excluded from positive error and recall metrics. Legacy unsafe means failing the historical 5m/10deg check; strict incorrect uses the unchanged 1m/5deg definition. Rejection here describes S4, not whether an oracle transform would pass the gate.', '',
    '## Short-motion check', '', 'Compared each saved odometry support-to-anchor transform to the corresponding GT relative pose. Statistics count all 400 support usages per role, including repeated links; unique link counts are in JSON. No GT motion is substituted into scoring.', '']
for role, r in results.items():
    t, a = r['local_translation_m'], r['local_rotation_deg']
    lines.append(f"- {role}: translation median/p90/max {t['median']:.4f}/{t['p90']:.4f}/{t['maximum']:.4f} m; rotation {a['median']:.4f}/{a['p90']:.4f}/{a['maximum']:.4f} deg.")
lines += ['', 'These measurements can bound local-motion discrepancies but do not establish the cause of ranking failures. Four nearby support scans may retain similar geometry and ambiguity; proving that mechanism requires a separately declared control. Do not infer spatial independence from exclusion of anchor source IDs.', '',
    '## Next research boundary', '',
    'Neural training remains stopped. Use these failures to formulate a bounded, prospective support-evidence question, with official R4 and equal-data/compute controls. Freeze its protocol and fresh confirmation membership before generating new outcomes. KITTI00/02 cannot be reused as unseen confirmation after this diagnosis. Preserve NCLT for external evaluation. No automatic score sweep or threshold search.', '']
(OUT / 'REPORT.md').write_text('\n'.join(lines))
assert all(sha(PILOT / p) == h for p, h in frozen.items())
with (OUT / 'validation.json').open('x') as f: json.dump(dict(passed=True, frozen_pilot_unchanged=True, input_manifest_sha256=sha(PILOT/'artifact_hashes.json'), script_sha256=sha(Path(__file__))), f, indent=2)
with (OUT / 'artifact_hashes.json').open('x') as f: json.dump({p.name:sha(p) for p in sorted(OUT.iterdir()) if p.is_file() and p.name != 'artifact_hashes.json'}, f, indent=2)
print('\n'.join(lines))
