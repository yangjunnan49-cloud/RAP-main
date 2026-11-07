"""Verify and report the completed SC0 data screen without changing its products."""
import hashlib
import importlib.metadata
import json
import platform
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path('/mnt/e/githouse/RAP-main')
OUT = ROOT/'docs/maintenance/2026-09-14/support-control-01'
DATA = OUT/'data'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, obj):
    with path.open('x') as f:
        json.dump(obj, f, indent=2, allow_nan=False)


assert not (DATA/'INCOMPLETE').exists()
checks = {}
for folder in [DATA, ROOT/'docs/maintenance/2026-09-14/hl-v2/pilot-01',
               ROOT/'docs/maintenance/2026-09-14/hl-v2/diagnostic-01']:
    manifest = read(folder/'artifact_hashes.json')
    assert all(sha(folder/p) == h for p,h in manifest.items())
    checks[str(folder.relative_to(ROOT))] = len(manifest)
freeze = read(DATA/'cohort_freeze.json')
assert sha(OUT/'PROTOCOL.md') == freeze['protocol_sha256']
assert all(sha(Path(p)) == h for p,h in freeze['source_hashes'].items())
decision = read(DATA/'decision.json')
assert decision['decision'] == 'INCONCLUSIVE_DATA'
seqs = sorted({s for r in decision['roles'].values() for s in r['sequences']})
details = [read(DATA/s/'adequacy.json') for s in seqs]
validations = [read(DATA/s/'validation.json') for s in seqs]
assert all(v['passed'] for v in validations)
for s in seqs:
    meta = read(DATA/s/'data.json')
    assert all(sha(Path(p)) == h for p,h in meta['metadata_sha256'].items())
count = sum(d['frames'] for d in details)
lines = [
    '# SC-V1 data feasibility and control declaration', '',
    '**SC0 complete: INCONCLUSIVE_DATA. SC1 not started. Neural expansion remains stopped.**', '',
    'This result concerns the newly declared cohort, not the adequate HL-V2 H2 failure.', '',
    '## Concrete research advance', '',
    'The fixed comparison previously changed both observations and scoring objective: '
    'B4 ranks overlap, S4 ranks clipped distances. The new protocol isolates additional '
    'observations with A4 (same distance score on anchors), S4, identical-support pooled '
    'P4 and a query-budget P4x2 control. Official R4 and evaluator-only GT transport '
    'remain explicit. This identifies a testable confound, not a demonstrated cause.', '',
    '[Prospective protocol](PROTOCOL.md) was hash-frozen before data labels. '
    'No new selector was implemented or scored; no weights, score constants or '
    'acceptance thresholds changed.', '',
    '## Data screen', '',
    '| Role | Sequences | Candidates | Confuser | Ambiguous | Low overlap | Ordinary | Selected | Adequate |',
    '|---|---|---:|---:|---:|---:|---:|---:|---|',
]
for role, r in decision['roles'].items():
    c = r['counts']
    lines.append(f"| {role} | {','.join(r['sequences'])} | {r['candidate_count']} | "
                 f"{c['confuser']} | {c['ambiguous_positive']} | {c['low_overlap']} | "
                 f"{c['ordinary']} | {r['selected']} | {r['adequate']} |")
lines += ['', 'Minimum is 60 total and 10 in each stratum in both roles; target 25 each. '
          'The physical query cap and stratum priority are unchanged. Sequence expansion '
          'followed the predeclared order, before any RAP outcomes.', '',
          '| Sequence | Raw scans | Candidates | Supported ambiguous / ordinary | Selected |',
          '|---|---:|---:|---|---:|']
for d in details:
    st = {r['stratum']:r for r in d['strata']}
    lines.append(f"| {d['sequence']} | {d['frames']} | {d['candidates']} | "
                 f"{st['ambiguous_positive']['supported']} / {st['ordinary']['supported']} | {d['selected']} |")
lines += ['', 'Per-sequence selection is diagnostic; final role membership is resampled '
          'once over its pooled population under the declared hash and sequence-qualified '
          'query cap. Therefore role counts need not equal the sum of sequence selections.', '',
          'Discovery 07+10 has only 3 supported ambiguous positives and 9 supported '
          'ordinary positives even before the query cap. Its failure is not repaired '
          'merely by changing sample order. These two sequences cannot supply the fixed '
          'minimum under this protocol. No padding, label relaxation or outcome-based '
          'replacement was used.', '',
          '[Exact membership freeze](data/cohort_freeze.json) and '
          '[decision](data/decision.json) preserve all selected inputs and evaluator labels. '
          'Frozen membership with inadequate counts is not a valid confirmation experiment.', '',
          '## Validation and scope', '',
          f'- Read and hashed {count:,} finite raw scans; checked source IDs, timestamps, '
          'GT/calibration, and constructed fresh KISS-ICP odometry without loop optimization.',
          '- Independent checks passed proposal union, causal raw support and local poses, '
          'strata, per-sequence sampling, GT-free selector input schema and bounded '
          'brute-force GT-overlap examples. Pooled role selection was separately reconstructed.',
          '- Reverified all new data artifact hashes, unchanged source/protocol hashes and '
          'metadata hashes. Original 829 pilot and 3 diagnosis artifact hashes still match.',
          '- The M0 snapshot exists without INCOMPLETE and its manifest hash matches. '
          'Archived payload was not rehashed; the same-volume backup limitation remains.',
          f"- Data orchestration wall time: {decision['wall_s']:.3f} s. "
          'This includes reads, odometry, labels and validation; no RAP GPU inference or '
          'training occurred. Human labour and active-kernel time were not measured.',
          '- KITTI07-10 names had no match in the two recorded historical inventory '
          'documents. This limited search does not prove exhaustive historical non-use, '
          'site independence or RAP pretraining exclusion.', '',
          '## Next decision', '',
          'SC-V1 ends at its predeclared data stop. Do not rerun these completed folders '
          'or implement SC1 against an inadequate discovery cohort. The control question '
          'remains untested. KITTI08 already has an adequate frozen 100-pair membership '
          'with no registration outcomes. The exact next task is a prospective SC-V1.1 '
          'data-role annex: use the frozen HL-V2 KITTI00 bank as explicitly observed '
          'development discovery and retain this exact KITTI08 confirmation membership. '
          'Declare inherited discovery seed/bank identities versus fresh confirmation '
          'seeds, preserve all fixed controls and score/gate definitions, and hash-freeze '
          'the annex before new scores. Then implement/validate the controls in RAP-SLAM, '
          'freeze discovery before confirmation outcomes and keep neural training stopped. '
          'Do not use 00/02 as unseen confirmation or resample08. This avoids insisting '
          'that discovery itself be unseen. No more raw data are needed for that proposed '
          'amendment; it is not yet declared or executed. Preserve SC-V1 INCONCLUSIVE_DATA '
          'as a separate result, without threshold/support-rule relaxation.', '',
          'Public-download authorization remains; no download or identity submission was '
          'needed for this audit. MulRan access still needs owner-provided identity; NCLT '
          'remains external and manuscript drafting remains paused.', '',
          'Only RAP-main maintenance orchestration/documents/artifacts changed. RAP-SLAM '
          'algorithms were reused read-only; production defaults and upstream source remain '
          'unchanged. HEADs remain 4055d92 / 6d3f2d2 on main with earlier dirty changes; '
          'no commit, push, pull, reset or cleanup. The initial sandbox WSL denial was '
          'resolved by scoped approved execution. No unresolved execution error remains.', '']
with (OUT/'REPORT.md').open('x') as f:
    f.write('\n'.join(lines))
save(OUT/'validation.json', dict(passed=True, checked_utc=datetime.now(timezone.utc).isoformat(),
     artifact_counts=checks, protocol_unchanged=True, sources_unchanged=True,
     raw_scans_read_hashed_finite=count, raw_rehash_at_closure=False,
     python=platform.python_version(), versions={p:importlib.metadata.version(p)
         for p in ['numpy','scipy','kiss-icp','open3d']}, report_generator_sha256=sha(Path(__file__))))
save(OUT/'artifact_hashes.json', {str(p.relative_to(OUT)):sha(p)
     for p in sorted(OUT.rglob('*')) if p.is_file()})
print('SC0 report complete; verified', checks, flush=True)
