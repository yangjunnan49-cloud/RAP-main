"""Read-only evidence checks and report for the completed SC-V1.1 experiment."""
import hashlib
import json
import platform
from datetime import datetime, timezone
from pathlib import Path
import importlib.metadata
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

MAIN = Path('/mnt/e/githouse/RAP-main')
OUT = MAIN/'docs/maintenance/2026-09-14/support-control-02'


def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def save(p, v):
    with Path(p).open('x') as f:
        json.dump(v, f, indent=2, allow_nan=False)


freeze = read(OUT/'execution_freeze.json')
assert sha(OUT/'ANNEX.md') == freeze['annex_sha256']
assert all(sha(p) == h for p, h in freeze['source_hashes'].items())
assert all(sha(p) == h for p, h in freeze['input_hashes'].items())
discovery = read(OUT/'discovery_frozen.json')
assert all(sha(OUT/'discovery'/p) == h for p, h in discovery['hashes'].items())
parents = {}
for folder in [MAIN/'docs/maintenance/2026-09-14/hl-v2/pilot-01',
               MAIN/'docs/maintenance/2026-09-14/support-control-01']:
    manifest = read(folder/'artifact_hashes.json')
    assert all(sha(folder/p) == h for p, h in manifest.items())
    parents[str(folder.relative_to(MAIN))] = len(manifest)

metrics, times, raw = {}, {}, {}
for role in ['discovery', 'confirmation']:
    out = OUT/role
    v = read(out/'independent_validation.json')
    assert v['passed'] and v['checked_selections'] == 1000
    hashes = read(out/'bank_hashes.json')
    assert len(hashes) == 400 and all(sha(out/'bank'/p) == h for p, h in hashes.items())
    assert read(out/'score_validation.json')['valid_hypotheses'] == 400
    raw.update(read(out/'input_hashes.json'))
    metrics[role] = read(out/'metrics.json')
    times[role] = read(out/'timings.json')
assert all(sha(p) == h for p, h in raw.items())
assert times['discovery']['new_generations'] == 0
assert times['confirmation']['new_generations'] == 400

methods = ['B1', 'B4', 'R4', 'A4', 'S4', 'P4', 'P4x2', 'G4', 'OR4', 'REJ']
lines = ['# SC-V1.1 observation-versus-score control', '',
         f"Confirmation decision: **{metrics['confirmation']['decision']}**. "
         '**Neural expansion remains STOPPED.**', '',
         'Both roles have 100 pairs, 25 per stratum, and 400 valid hypotheses. '
         'KITTI00 discovery reuses its already observed HL-V2 bank; KITTI08 is the '
         'new frozen confirmation membership. Discovery was independently checked '
         'and hash-frozen before KITTI08 inference. SC-V1 data insufficiency and '
         'HL-V2 H2 failure remain separate, unchanged results.', '',
         '## Fixed contrasts', '',
         'A4 uses the same clipped-distance objective as S4 on duplicated anchors. '
         'S4 uses four causal support combinations. P4 pools exactly the same '
         'support points; P4x2 repeats pooling scoring to match S4 NN query count. '
         'R4 uses official RAP trajectory rigidity. G4 changes only local transport '
         'to GT and is evaluator-only; OR4 is a GT pose oracle. No trained selector, '
         'threshold change or new rejection rule was introduced.', '',
         '| Role | Method | Strict positive success | Correct accepts | Incorrect / accepted | Mean clipped positive error |',
         '|---|---|---:|---:|---:|---:|']
for role, m in metrics.items():
    for method in methods:
        v = m['overall'][method]
        lines.append(f"| {role} | {method} | {v['strict_positive_successes']}/{v['positives']} | "
                     f"{v['correct_positive_accepts']} | {v['incorrect_accepted']}/{v['accepted']} | "
                     f"{v['mean_clipped_positive_error']:.9f} |")
lines += ['', '## Predeclared decision conditions', '',
          '| Role | A4/oracle discrepant positives | Gap recovery | Ordinary recall loss | New incorrect vs A4 / R4 | No worse than R4 | Decision |',
          '|---|---:|---:|---:|---:|---|---|']
for role, m in metrics.items():
    recovery = 'N/A' if m['gap_recovery'] is None else f"{m['gap_recovery']:.4%}"
    lines.append(f"| {role} | {m['discrepant_positives']} | {recovery} | {m['ordinary_recall_loss']:.4%} | "
                 f"{len(m['new_incorrect_pairs']['A4'])} / {len(m['new_incorrect_pairs']['R4'])} | "
                 f"{m['conditions']['no_worse_than_R4']} | {m['decision']} |")
lines += ['', 'The primary contrast is clipped positive error, not a post-hoc recall '
          'switch. All five conditions must pass. Harmful transitions are separate '
          'pair lists; beneficial transitions never cancel a newly incorrect accept.', '',
          '## Every stratum', '',
          '| Role | Stratum | A4/S4/P4/R4 strict successes | S4 minus A4 mean clipped error | S4 incorrect accepts |',
          '|---|---|---:|---:|---:|']
for role, m in metrics.items():
    for s, table in m['by_stratum'].items():
        values = '/'.join(str(table[x]['strict_positive_successes']) for x in ['A4','S4','P4','R4'])
        a, b = table['A4']['mean_clipped_positive_error'], table['S4']['mean_clipped_positive_error']
        delta = 'N/A (not positives)' if a is None else f'{b-a:+.9f}'
        lines.append(f"| {role} | {s} | {values} | {delta} | {table['S4']['incorrect_accepted']} |")
lines += ['', 'Confusers are excluded from positive-error and positive-recall '
          'denominators; all strata contain25 pairs. Full error quantiles, failure '
          'counts, accepted-confuser rates and exact pair transitions are retained '
          'in each role metrics/evaluator file.', '', '## Local transport and pooling', '']
for role, m in metrics.items():
    a = m['overall']
    lines.append(f"- {role}: G4 minus S4 clipped error = "
                 f"{a['G4']['mean_clipped_positive_error']-a['S4']['mean_clipped_positive_error']:+.9f}; "
                 f"G4/S4 strict successes = {a['G4']['strict_positive_successes']}/{a['S4']['strict_positive_successes']}. "
                 f"P4 minus S4 clipped error = {a['P4']['mean_clipped_positive_error']-a['S4']['mean_clipped_positive_error']:+.9f}.")
lines += ['', 'These contrasts test only the declared geometry and score. GT-motion '
          'sensitivity does not establish physical sensor-error causation. A failure '
          'to benefit does not prove that every possible support representation lacks '
          'information. P4x2 is identical in scores and selections to P4.', '',
          '## Cost and validation', '',
          '| Role | New RAP generations | Generation wall s | Preparation wall s | A4/S4/P4/P4x2 scoring wall s | Total study-process wall s | Peak allocated/reserved GiB |',
          '|---|---:|---:|---:|---|---:|---|']
for role, t in times.items():
    p = t['pairs']
    costs = '/'.join(f"{t['controls_wall_s'][m]:.3f}" for m in ['A4','S4','P4','P4x2'])
    lines.append(f"| {role} | {t['new_generations']} | {sum(x['generation_wall_s'] for x in p):.3f} | "
                 f"{sum(x['preprocess_wall_s'] for x in p):.3f} | {costs} | {t['wall_s']:.3f} | "
                 f"{max(x['peak_allocated'] for x in p)/2**30:.3f}/{max(x['peak_reserved'] for x in p)/2**30:.3f} |")
lines += ['', 'Shared preparation includes anchors and supports and is not a '
          'standalone deployment-time estimate for A4. P4/S4 use the same support '
          'points; P4x2/S4 match query count, while tree sizes and runtime differ. '
          'No exact equal-wall-time claim. Scores are CPU monotonic wall times; '
          'generation is CUDA synchronized. Total includes G4, I/O and initial '
          'loading, but excludes independent validation/reporting. Historical00 '
          'generation is not charged as new work. Active-kernel time and human '
          'labour are not measured.', '',
          '- Synthetic transport, duplicate-anchor, pooled brute-force, empty and tie checks passed.',
          '- All400 inherited S4 scores reproduce exactly; original discovery bank bytes and B1/B4/R4/S4 decisions are unchanged.',
          '- Each role passed1000 independent selections, independent pose errors, all-stratum metrics and full decision recomputation.',
          f'- Rehashed all800 bank files and {len(raw)} distinct used raw scans; parent/source/protocol/input identities remain unchanged.',
          '- Original observer wrapper/backend and relevant rigid-fit dependencies match preserved identities; prior RNG/hook invariance evidence is inherited.',
          '- A pre-execution PowerShell input-list construction error was corrected before scoring. The declaration parent-count field is an array of one per file; manifest checks and independently counted totals are authoritative. Neither issue affected sampling, hashes, scores or gates.', '',
          '## Research decision and next boundary', '',
          'Retain this complete mechanism result; do not start a learned head, search '
          'score/acceptance/support parameters, or reuse08 as new confirmation after '
          'these outcomes. All00/02/08 are now observed development evidence. This '
          'bounded result does not establish a new method advantage over pooled RAP '
          'or strong registration/system baselines.', '',
          'Next: synthesize HL-V2 and SC-V1.1 into a short direction decision, '
          'separating proposal headroom, ranking benefit and incorrect acceptance. '
          'Any new research mechanism or data role needs a justified prospective '
          'protocol and fresh confirmation before outcomes. Do not force another '
          'selector variant from these development results. Keep manuscript drafting '
          'paused pending the research-direction decision.', '',
          'No weights, backbone, production defaults or upstream model sources '
          'changed. Two research helpers were added in RAP-SLAM, with maintenance '
          'documents/reporting in RAP-main. Original HEADs4055d92/6d3f2d2 and prior '
          'dirty changes remain; no commit/push/pull/reset/cleanup/download. No '
          'background experiment remains after validation.', '']

fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
shown = ['R4','A4','S4','P4','G4','OR4']
x = np.arange(len(shown))
for idx, (role, m) in enumerate(metrics.items()):
    for ax, field in zip(axes, ['mean_clipped_positive_error','strict_positive_successes']):
        ax.bar(x+(idx-.5)*.36, [m['overall'][s][field] for s in shown], width=.36, label=role)
for ax in axes:
    ax.set_xticks(x, shown)
    ax.legend(frameon=False)
    ax.grid(axis='y', alpha=.2)
axes[0].set_ylabel('Mean clipped error (lower is better)')
axes[1].set_ylabel('Strict successes / 75 positives')
fig.suptitle('SC-V1.1 fixed controls; G4 / OR4 are GT-only diagnostics')
fig.tight_layout()
fig.savefig(OUT/'results.png', dpi=160)
plt.close(fig)
lines += ['![Fixed control results](results.png)', '']
with (OUT/'REPORT.md').open('x') as f:
    f.write('\n'.join(lines))
save(OUT/'decision.json', dict(protocol='SC-V1.1', decision=metrics['confirmation']['decision'],
     discovery_decision=metrics['discovery']['decision'], neural_expansion='STOPPED',
     completed_utc=datetime.now(timezone.utc).isoformat(), new_hypotheses=400,
     inherited_hypotheses=400, training_started=False, original_HL_V2='STOP_NEURAL_EXPANSION unchanged'))
save(OUT/'validation.json', dict(passed=True, parent_artifact_counts=parents,
     discovery_freeze_unchanged=True, execution_inputs_sources_unchanged=True,
     independent_selections=2000, bank_files=800, raw_scans_rehashed=len(raw),
     python=platform.python_version(), versions={p:importlib.metadata.version(p)
       for p in ['numpy','scipy','torch','open3d']}, report_generator_sha256=sha(Path(__file__))))
(OUT/'confirmation/INCOMPLETE').unlink()
save(OUT/'artifact_hashes.json', {str(p.relative_to(OUT)):sha(p)
     for p in sorted(OUT.rglob('*')) if p.is_file()})
print('Final SC-V1.1:', metrics['confirmation']['decision'], flush=True)
