"""Close PG-DEV-V1 after both independent audits; never rerun completed outputs."""
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone

MAIN = Path('/mnt/e/githouse/RAP-main')
BASE = MAIN / 'docs/maintenance/2026-09-15/proposal-context-dev-01'
METHODS = ['A1', 'A-R4', 'A-S4', 'A-OR4', 'P1', 'P-R4', 'P-OR4']


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)


def main():
    assert not (BASE / 'REPORT.md').exists()
    metrics = {}
    for seq in ['00', '08']:
        out = BASE / seq
        assert not (out / 'INCOMPLETE').exists()
        assert read(out / 'independent_validation.json')['passed']
        metrics[seq] = read(out / 'metrics.json')
    for path, digest in read(BASE / 'execution_freeze.json')['hashes'].items():
        assert sha(Path(path)) == digest, path
    for path, digest in read(BASE / 'dependency_validation.json')['checks'].items():
        assert sha(Path(path)) == digest, path
    for path, digest in read(BASE / '00_frozen.json').items():
        assert sha(BASE / '00' / path) == digest, path
    parents = {}
    for rel in ['2026-09-14/hl-v2/pilot-01', '2026-09-14/support-control-02']:
        root = MAIN / 'docs/maintenance' / rel
        hashes = read(root / 'artifact_hashes.json')
        for path, digest in hashes.items():
            assert sha(root / path) == digest, path
        parents[rel] = len(hashes)
    used = {}
    for seq in metrics:
        for path, digest in read(BASE / seq / 'input_hashes.json').items():
            assert sha(Path(path)) == digest, path
            used[path] = digest
    passed = all(all(m['conditions'].values()) for m in metrics.values())
    decision = 'DEVELOPMENT_SIGNAL' if passed else 'NO_DEVELOPMENT_CONTEXT_SIGNAL'
    times = {seq: read(BASE / seq / 'timings.json') for seq in metrics}
    status = dict(decision=decision, role='observed_development_only',
                  sequences={s: m['decision'] for s, m in metrics.items()},
                  completed_utc=datetime.now(timezone.utc).isoformat(),
                  new_pooled_generations=800, timing_only_anchor_replays=80,
                  inherited_anchor_hypotheses=800, neural_expansion='STOPPED',
                  production_change=False, independent_confirmation=False)
    save(BASE / 'decision.json', status)
    transitions = {}
    lines = ['# PG-DEV-V1: proposal-context development screen', '',
             f'Decision: **{decision}**.', '',
             'Both KITTI00 and KITTI08 are observed development data. This screen',
             'does not establish independent generalization, a new contribution,',
             'or end-to-end SLAM improvement. All historical negative results remain.', '',
             '| Sequence | Method | Strict successes /75 | Correct accepts /75 | Incorrect accepted /100 | Clipped positive error |',
             '|---|---|---:|---:|---:|---:|']
    for seq, m in metrics.items():
        for name in METHODS:
            v = m['overall'][name]
            lines.append(f"| {seq} | {name} | {v['strict_positive_successes']} | "
                         f"{v['correct_positive_accepts']} | {v['incorrect_accepted']} | "
                         f"{v['mean_clipped_positive_error']:.9f} |")
    lines += ['', '## Fixed conditions and paired transitions', '']
    for seq, m in metrics.items():
        rows = read(BASE / seq / 'evaluator_only_decisions.json')
        transitions[seq] = {}
        lines += [f'### KITTI{seq}', '', f"Decision: {m['decision']}.", '']
        for name, ok in m['conditions'].items():
            lines.append(f'- {name}: {"PASS" if ok else "FAIL"}.')
        for baseline in ['A-R4', 'A-S4']:
            def key(row):
                return f"{row['source_i']}_{row['source_j']}"
            transitions[seq][baseline] = dict(
                positive_gained=[key(r) for r in rows if r['stratum'] != 'confuser'
                                 and r['methods']['P-R4']['strict'] and not r['methods'][baseline]['strict']],
                positive_lost=[key(r) for r in rows if r['stratum'] != 'confuser'
                               and not r['methods']['P-R4']['strict'] and r['methods'][baseline]['strict']],
                new_incorrect=m['new_incorrect_pairs'][baseline],
                resolved_incorrect=[key(r) for r in rows if not r['methods']['P-R4']['incorrect_accepted']
                                    and r['methods'][baseline]['incorrect_accepted']])
            v = transitions[seq][baseline]
            lines += ['', f"Versus {baseline}: {len(v['positive_gained'])} positive successes gained, "
                      f"{len(v['positive_lost'])} lost; {len(v['new_incorrect'])} newly incorrectly "
                      f"accepted pairs, {len(v['resolved_incorrect'])} resolved. Helpful transitions do not cancel harm."]
        lines += ['', '| Stratum | A-R4 successes | A-S4 successes | P-R4 successes |',
                  '|---|---:|---:|---:|']
        for stratum, table in m['by_stratum'].items():
            if stratum == 'confuser':
                continue
            lines.append(f"| {stratum} | {table['A-R4']['strict_positive_successes']} | "
                         f"{table['A-S4']['strict_positive_successes']} | {table['P-R4']['strict_positive_successes']} |")
    save(BASE / 'paired_transitions.json', transitions)
    lines += ['', '## Cost and validation', '',
              '| Sequence | Timed pairs | A-R4 (s) | A-S4 (s) | P-R4 (s) | P/A-S4 |',
              '|---|---:|---:|---:|---:|---:|']
    for seq, t in times.items():
        c = t['sampled_cost']
        lines.append(f"| {seq} | 10 | {c['A_R4_full_s']:.3f} | {c['A_S4_full_s']:.3f} | "
                     f"{c['P_R4_full_s']:.3f} | {c['ratio_P_to_A_S4']:.4f} |")
    peak = max(p['peak_allocated'] for t in times.values() for p in t['pairs'])
    lines += ['', 'Costs use fixed first10 pairs per sequence, alternating execution order,',
              'fresh pair-local raw caches and warm OS cache. They include preprocessing,',
              'generation, selection and common-anchor gate, excluding evidence I/O/model',
              'load. No separate GPU warmup was run; the first timed arm was A, so startup',
              'overhead can favor P in the sampled ratio. No speed superiority is claimed.',
              'These are sampled development costs, not full-cohort equal-time evidence.', '',
              f"Total process wall: {sum(t['process_wall_s'] for t in times.values()):.3f}s; "
              f'peak allocated memory: {peak / 2**30:.3f}GiB.', '',
              '800 new pooled generations,80 timing-only anchor replays and800 inherited',
              'anchor hypotheses. All80 replays reproduce within1e-6; old banks remain the',
              'selection source. Independent audits cover1400 selections,1600 candidate',
              f'gates, all stratum aggregates and decisions; {len(used)} distinct raw files',
              'and1664 historical artifacts were rehashed. KITTI00 was validated and frozen',
              'before KITTI08 generation. Exact deltas are in the per-sequence validations.', '',
              '## Decision boundary', '']
    lines += (['The fixed development screen passes on both sequences. Next is a bounded',
               'fresh Boreas confirmation/adapter annex with full matched costs. This does',
               'not authorize a trained head, production replacement or novelty claim.']
              if passed else
              ['The fixed pooled-context route does not pass the development screen.',
               'Do not expand its Boreas acquisition, tune support distances/thresholds, or',
               'train a selector to rescue this outcome. Preserve the positive and adverse',
               'transitions as diagnostic evidence; do not claim all contextual methods fail.',
               'Next is a scope/direction decision grounded in these measured limitations,',
               'not another automatic variant or data acquisition campaign.'])
    (BASE / 'REPORT.md').write_text('\n'.join(lines) + '\n')
    save(BASE / 'validation.json', dict(passed=True, parent_counts=parents,
         raw_files=len(used), selections=1400, gates=1600, source_freeze_unchanged=True,
         discovery_freeze_unchanged=True, finalizer_sha256=sha(Path(__file__))))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), sharey=True)
    for ax, (seq, m) in zip(axes, metrics.items()):
        names = ['A-R4', 'A-S4', 'P-R4', 'A-OR4', 'P-OR4']
        vals = [m['overall'][n]['strict_positive_successes'] for n in names]
        ax.bar(names, vals, color=['#6d849b', '#9aadc0', '#d47a3d', '#9caaa0', '#b8c6bd'])
        for k, v in enumerate(vals):
            ax.text(k, v + .7, str(v), ha='center')
        ax.set_title(f'KITTI{seq} — observed development')
        ax.set_ylim(0, 75)
        ax.set_ylabel('Strict successful positive pairs /75')
        ax.spines[['right', 'top']].set_visible(False)
    fig.suptitle('Fixed proposal-context screen; oracle bars are evaluator-only')
    fig.tight_layout()
    fig.savefig(BASE / 'results.png', dpi=170)
    save(BASE / 'artifact_hashes.json', {p.relative_to(BASE).as_posix(): sha(p)
         for p in sorted(BASE.rglob('*')) if p.is_file()})
    print(json.dumps(status, indent=2))


if __name__ == '__main__':
    main()
