"""Finalize the validated joint diagnostic without touching old products."""
import hashlib
import json
from pathlib import Path

b=Path(__file__).resolve().parent
r=json.loads((b/'results.json').read_text()); v=json.loads((b/'validation.json').read_text())
assert v['passed'] and v['decision']==r['decision']
lines=['# Joint accepted-loop pose diagnostic — 2026-10-05','',
       '**VALIDATED: MATERIAL_CURRENT_EDGE_JOINT_HEADROOM (ATE branch only).**','',
       'This is an evaluator-only diagnostic, not a RAP improvement or global ceiling.',
       'All current accepted poses were jointly replaced by their same-endpoint GT',
       'poses. Endpoints, odometry, base noise, kernel settings and native propagation',
       'were unchanged; robust effective influence could change with residuals.','',
       '| Sequence | Native P ter % | Joint J ter % | Native P ATE m | Joint J ATE m |',
       '| --- | ---: | ---: | ---: | ---: |']
for s,row in r['rows'].items():
    p,j=row['P'],row['J']
    lines.append(f"| {s} | {p['ter']:.6f} | {j['ter']:.6f} | {p['ate']:.6f} | {j['ate']:.6f} |")
lines+=['','## What changed in our understanding','']
for g,m in r['cohort_means'].items():
    p,j=m['P'],m['J']
    lines.append(f"- {g}: mean ter {p['ter']:.9f}% -> {j['ter']:.9f}% (P minus J {p['ter']-j['ter']:.9f} pp); mean ATE {p['ate']:.9f} -> {j['ate']:.9f} m ({(1-j['ate']/p['ate'])*100:.4f}% improvement).")
lines+=['','The exposed-transfer cohort passes the prospectively frozen ATE opportunity',
        'criterion (>=5% ATE gain, ter worsening <=0.01 pp). Neither cohort passes',
        'the >=0.01 pp ter-gain branch. The development cohort passes neither branch.',
        '09 drives most of the ATE opportunity: its ATE drops about 30.53% and ter',
        'improves 0.015954 pp. 07 improves ATE too; 10 remains identical with no edges.',
        'This demonstrates coupled current-edge opportunity missed by reading the',
        'single-edge interventions as an all-edge ceiling. It does not establish',
        'statistical independence, a GT-blind selector, or a practical pose generator.','',
        'Joint GT loops still leave mean ter above odometry in both cohorts, and',
        'sequence09 J ter 0.577698% is above odometry 0.519444%. 05 ter worsens',
        'under the joint replacement. Perfect current loop poses alone therefore',
        'do not remove the regression in this specific frozen graph configuration.',
        'No conclusion follows about all possible graph designs or added loops.',
        '09 rotation drift worsens from 0.106938 to 0.129841 deg/100m; preserve this',
        'secondary tradeoff rather than calling all metrics improved.','',
        '## Validation','',
        '63 identities froze; the complete 19-file GT-free native bank sealed before',
        'the new evaluator loaded GT. A separate validator explicitly rebuilt every',
        'native/oracle graph, checked all 58 replacement poses and unchanged metadata/',
        'base sigmas, independently calibrated GT and recomputed Kabsch ATE and',
        f"{v['independent_segment_records']:,} segment records. It passed {len(v['check_groups'])} check groups; maximum native/oracle graph difference is {max(max(d.values()) for d in v['graph_crosscheck'].values()):.3g}.",
        f"Bank/evaluation/validation wall {v['total_wall_s']:.3f}s; max stage RSS {v['peak_rss_gib']:.3f} GiB; artifacts before report {v['artifact_bytes_before_report']/2**20:.3f} MiB. Caps passed.",
        '', '## Next step','',
        'Proceed to feasibility and prospective design for one strong official',
        'outdoor registrar on actual online E0 inputs, initially GeoTransformer.',
        'Use all 71 attempted pairs rather than selecting the ten exposed 09 errors',
        'as the only efficacy sample. Separate its pure fixed-edge pose diagnostic',
        'from common-gate acceptance and full executable system behavior. Freeze',
        'training/checkpoint/source identities, actual input points, direction and',
        'resource/decision rules before any new pair output. A direct matcher gain',
        'would be a baseline, not a RAP innovation. Reserve independent trajectories',
        'for later method confirmation. No training/default/production edit,',
        'manuscript change, commit or Git synchronization. All old stops persist.']
(b/'REPORT.md').write_text('\n'.join(lines)+'\n')
(b/'HANDOFF.md').write_text('''# Joint-loop diagnostic handoff

Read PROTOCOL.md, freeze.json, bank_seal.json, results.json, validation.json
and REPORT.md. VALIDATED / MATERIAL_CURRENT_EDGE_JOINT_HEADROOM, ATE branch
only on the exposed-transfer cohort. No executable algorithm gain exists.
Keep GT counterfactual products evaluator-only and immutable. The failed
fixed interpolation route stops. Next: one official system-relevant outdoor
matcher feasibility/design, no outcome-driven pose/gate sweep. Defaults and
old banks stay unchanged; no training, manuscript or Git sync.
''')
status=json.loads((b/'STATUS.json').read_text())
status.update(report='REPORT.md',next_action='One official outdoor registrar feasibility/design on exact E0 online attempts; no pair output before a new freeze')
(b/'STATUS.json').write_text(json.dumps(status,indent=2)+'\n')
(b/'INCOMPLETE').unlink()
with (b/'artifact_hashes.json').open('x') as f:
    json.dump(dict(files={str(p.relative_to(b)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(b.rglob('*')) if p.is_file() and p.name!='artifact_hashes.json'}),f,indent=2)
print('joint report finalized and sealed')
