"""Finalize documentation only after independent screen validation."""
import hashlib
import json
from pathlib import Path

b=Path(__file__).resolve().parent
r=json.loads((b/'results.json').read_text())
v=json.loads((b/'validation.json').read_text())
assert v['passed'] and v['decision']==r['gate']['decision']
lines=['# Fixed dense-pose correction screen — 2026-10-05','',
       '**VALIDATED: NO_FIXED_INTERPOLATION_SIGNAL.** Stop this exact interpolation route.','',
       'The fixed SE(3) interpolation was constructed without GT on unchanged saved E0 A',
       'odometry and optimized keyframes. No graph reoptimization or RAP inference.','',
       '| Sequence | Odom ter % | Native P ter % | Interpolated S ter % | P minus S, pp | P ATE m | S ATE m |',
       '| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
for seq,row in r['rows'].items():
    o,p,s=(row[a] for a in ('odom','P','S'))
    lines.append(f"| {seq} | {o['ter']:.6f} | {p['ter']:.6f} | {s['ter']:.6f} | {p['ter']-s['ter']:.6f} | {p['ate']:.6f} | {s['ate']:.6f} |")
lines+=['','## Frozen decision','']
for group,m in r['cohort_means'].items():
    p,s=m['P'],m['S']
    lines.append(f"- {group}: mean ter {p['ter']:.9f}% -> {s['ter']:.9f}%; gain {p['ter']-s['ter']:.9f} pp versus required >=0.01. Mean ATE {p['ate']:.9f} -> {s['ate']:.9f} m.")
lines+=['','Both material ter gates fail; all fifteen other safety/identity gates pass.',
        'The actual small improvements are retained; failure is not zero numerical effect.',
        '06 and 09 still have clear ter regression versus their odometry. This fixed',
        'interpolation does not remove it. No general impossibility or exclusive causal',
        'attribution follows, and no interpolation-space/weight rescue is licensed.','',
        '## Validation and provenance','',
        '49 protocol/source/input/preflight identities froze before the full output.',
        'The complete 25-file GT-free bank sealed before evaluator GT. The independent',
        'validator reconstructed all S poses with SciPy/analytic SE(3), independently',
        'computed rigid-alignment ATE and all strict-endpoint KITTI segment records,',
        'verified baseline reproduction, correction diagnostics and all seventeen gates.',
        f"It passed {len(v['check_groups'])} groups and {v['independent_segment_records']:,} segment records. Maximum analytic trajectory difference is {max(x['independent_S_max_delta'] for x in v['trajectory_crosscheck'].values()):.3g}; native saved-path difference <={max(x['native_saved_max_delta'] for x in v['trajectory_crosscheck'].values()):.3g}.",
        f"Sequence10 P/S difference {v['sequence10_P_S_max_delta']:.3g}. Bank/evaluation/validation wall {v['total_screen_wall_s']:.3f}s, max stage RSS {v['maximum_stage_peak_rss_gib']:.3f} GiB; artifacts before report {v['artifact_bytes_before_report']/2**20:.3f} MiB. All resource caps pass. Setup/preflight time is recorded separately.",
        '', '## Next question','',
        'A separately frozen joint same-endpoint GT replacement diagnostic can ask',
        'whether current accepted poses have coupled trajectory headroom. It must',
        'keep native propagation, endpoints, odometry, graph settings and base noise',
        'fixed. This is evaluator-only, not a deployable method or global ceiling.',
        'Generic interpolation is prior art; no original RAP gain or new independent',
        'confirmation is established. No default/production edit, training, manuscript',
        'change, commit or Git sync. Earlier negative stops and old banks persist.']
(b/'REPORT.md').write_text('\n'.join(lines)+'\n')
(b/'HANDOFF.md').write_text('''# Fixed propagation screen handoff

Read PROTOCOL.md, freeze.json, bank_seal.json, results.json, validation.json
and REPORT.md. Outcome VALIDATED / NO_FIXED_INTERPOLATION_SIGNAL. Do not rerun
or mutate frozen files, bank or evaluator products. No space/weight sweep.
Native production propagation remains unchanged. All six sequences are exposed
development for future research. The next question is a separate joint accepted-
edge oracle diagnostic; no method claim follows from that proposal.
''')
status=json.loads((b/'STATUS.json').read_text())
status.update(report='REPORT.md',route='stopped: no interpolation space/weight rescue',next_action='Separate joint accepted-edge GT diagnostic; preserve native propagation and all prior stops')
(b/'STATUS.json').write_text(json.dumps(status,indent=2)+'\n')
assert (b/'INCOMPLETE').is_file()
(b/'INCOMPLETE').unlink()
files={str(p.relative_to(b)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(b.rglob('*')) if p.is_file() and p.name!='artifact_hashes.json'}
with (b/'artifact_hashes.json').open('x') as f: json.dump(dict(files=files),f,indent=2)
print('report finalized and artifacts sealed',len(files))
