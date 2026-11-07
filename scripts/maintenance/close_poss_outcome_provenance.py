"""Close POP0, retaining the original parser assertion and its full receipts."""
import time
START = time.monotonic()
import json
import resource
from pathlib import Path
import physical_source_role_feasibility as s
import poss_outcome_layout02 as layout

ROOT, OLD, BASE = layout.ROOT, layout.OLD, layout.BASE
read, sha = s.read, s.sha
f = layout.check()
c, v = read(BASE/'outcome_census.json'), read(BASE/'validation.json')
assert v['passed'] and sha(BASE/'outcome_census.json') == read(BASE/'census_seal.json')['sha256']


def save(name, value):
    layout.save(BASE/name, value)


def text(name, value):
    with (BASE/name).open('x', encoding='utf-8') as stream:
        stream.write(value+'\n')


receipts = []
retries = gaps = 0
expected = [(OLD/'supervision', 'freeze', True), (OLD/'supervision', 'census', False),
            (BASE/'supervision', 'bind', True), (BASE/'supervision', 'census', True),
            (BASE/'supervision', 'validate', True)]
for sup, stage, success in expected:
    q = sup/stage
    child, windows, launch = [read(q/n) for n in ('child_exit.json', 'exit.json', 'launch.json')]
    assert child['success'] is success and windows['exit_code'] == (0 if success else 1)
    assert child['full_resource_capture'] and child['peak_RSS_bytes'] <= 512*2**20
    assert child['peak_GPU_allocated_bytes'] == child['peak_GPU_reserved_bytes'] == 0
    assert all(child[k] == 0 for k in ('new_model_calls', 'new_solver_calls', 'new_fit_calls', 'new_pose_metric_calls'))
    samples = [json.loads(line) for line in (q/'host_memory.jsonl').read_text().splitlines()]
    assert len(samples) == windows['host_memory_observations'] > 0
    assert min(row['headroom_bytes'] for row in samples) >= 4*2**30
    assert launch['headroom_before_bytes'] >= 12*2**30
    for name in ('logging_retry.jsonl', 'logging_gap.jsonl'):
        if (q/name).exists():
            if name.startswith('logging_retry'):
                retries += len((q/name).read_text().splitlines())
            else:
                gaps += len((q/name).read_text().splitlines())
    receipts.append(dict(directory=str(q.relative_to(OLD)), child=child, Windows=windows, launch=launch))
assert {p.name for p in (OLD/'supervision').iterdir() if p.is_dir()} == {'freeze', 'census'}
assert {p.name for p in (BASE/'supervision').iterdir() if p.is_dir()} == {'bind', 'census', 'validate'}
seconds = sum(row['Windows']['wall_seconds'] for row in receipts)
child_seconds = sum(row['child']['wall_seconds'] for row in receipts)
assert seconds <= 600
peak = max(row['child']['peak_RSS_bytes'] for row in receipts)
status = 'VALIDATED_SURVIVING_POSS_B_OUTCOME_LINEAGE_COMPLETE_NO_SOURCE_AUTHENTICATION'
save('RESOURCE_AUDIT.json', dict(passed=True, receipts=receipts, attempts=5, successes=4,
    retained_original_layout_failure=1, Windows_seconds_including_startup_imports=seconds,
    child_seconds_after_time_bootstrap=child_seconds, peak_RSS_bytes=peak, GPU_bytes=0,
    logging_retries=retries, logging_gaps=gaps, original_combined_caps_unchanged=True,
    ordinary_preparation_RSS_unknown=True, stdlib_closure_separate=True))
save('CHECKS.json', dict(passed=True, frozen_identities=len(f['files']),
    independently_matched_outcome_rows=12, trajectory_structure_rows=5502,
    source_citations=v['source_citations'], B_fit_members=0, complete_old_fit_total=188,
    original_failure_and_PEL_partition_preserved=True, no_new_metric_or_model=True))
save('FINAL_IDENTITY_CHECK.json', dict(passed=True, repositories=f['repositories'],
    original_frozen_inputs_and_failure_available_seal_match=True,
    frozen_identities=len(f['files']), all_old_markers_preserved=True))
save('STATUS.json', dict(status=status, decision=c['decision'],
    outcome_exposure_confirmed=True, exact_raw_frame_execution_authenticated=False,
    B_old_calibration_fit_members=0, independent_confirmation_admitted=False))
text('REPORT.md', '\n'.join([
    '# POP0 POSS-B Saved Outcome Lineage', '',
    'Decision: '+c['decision']+'. This updates the current interpretation, not '
    'the immutable earlier PEL0 source-ID partition.', '',
    'The original B summary reports range6750-9500/stride1,2751 scans,153 '
    'keyframes and12 accepted loops, with stored GT translation/rotation errors '
    'but no T_rel matrices. Independent validation matches all12 (i,j), overlap '
    'and stored error values into output_calibrated/edge_dataset.json. The two '
    'saved trajectories each have2751 rows and12 columns; only structure was '
    'read, not pose coordinates or newly calculated errors.', '',
    'Both calibrated-weighting and GNC source rules require finite mean_dist. '
    'All12 saved B rows have NaN mean_dist and are excluded. The saved complete '
    'table gives188 eligible rows: KITTI02=182/POSS offline=4/POSS live=2/B=0. '
    'The old report correctly prints total188 but its fixed prose parenthesis '
    'says KITTI02 182+POSS18. That prose does not establish200 fitted rows, B '
    'fitting, or any new fit. No fit/solver/model was executed in this scope.', '',
    'POSS-B therefore has surviving reported pipeline and outcome-analysis '
    'exposure; it is not merely an unused configuration and cannot be called '
    'untouched confirmation. Saved counts/trajectories/outcomes still do not '
    'authenticate execution of every claimed source frame: the four exact B '
    'source_frames/keyframes/run_manifest/archive_receipt paths are absent, '
    'and the source-ID mapping remains a historical assumption. No global '
    'absence/all-history completeness/checkpoint or site exclusion is proven.', '',
    'The saved downloader URL and size-only existing-file skip are source '
    'evidence, not current-byte or provider authentication. This script does '
    'not persist an archive receipt; no assertion is made that its ZIP library '
    'performed no CRC check during transfer. The camera projection readme '
    'and loader horizontal-trajectory justification do not authenticate '
    'the pose frame, reference measurement method or sensor timing. The '
    'bounded public HTML retrieval failures establish no permanent outage. '
    'SemanticPOSS author documentation is a different dataset description; '
    'its conventions were not imported into these odometry files.', '',
    'Original parser assertion incorrectly expected8-column TUM. Its source, '
    'freeze, failure, INCOMPLETE and full native/Windows receipts are preserved. '
    'Separate exact AST variants change only two driver/one validator integer '
    'column literals8->12 and one output route per source. Current writer '
    'sources are bound as corroboration, not asserted historical source identity. '
    'All original plus correction attempts share the unchanged original cap.', '',
    f'All{len(f["files"])} frozen identities and25 source citations match. '
    f'Five supervised CPU attempts/four successes/one retained layout failure: '
    f'Windows{seconds:.9f}s including startup/imports, child{child_seconds:.9f}s '
    f'after bootstrap, peakRSS{peak}bytes/GPU0.600s/512MiB/16MiB combined caps '
    f'pass; full exits/host samples,{retries} logging retries/{gaps} gaps. '
    'Ordinary preparation RSS unknown/stdlib closure separate/old gaps unchanged.', '',
    'No new cohort, learned fit, pose metric, physical/system/generalization/novelty '
    'gain or acquisition/install/production/default/reference/manuscript/restart/'
    'commit/Git sync. BRF0 exact-family stop, all retired families, official '
    'references/09 unknown, original repositories/two-nine dirty sets and '
    'latest2026-10-11 complete system benchmark persist.'
]))
text('NEXT_EVIDENCE_DEPENDENCY.md', '# Next Evidence Boundary\n\n'
    'Use POSS-B only as outcome-exposed development evidence with unverified '
    'source-ID mapping and reference/timing lineage. Do not equate missing '
    'mean_dist/exclusion from one fit with no information exposure. Authenticate '
    'exact raw acquisition/member identities, per-frame reference/time mapping, '
    'pose/world/sensor conventions and measurement method before physical '
    'reference claims. New data acquisition is not authorized automatically. '
    'A different efficacy study still needs a distinct mechanism, strong '
    'ordinary controls and complete common-input/total-work contract; do '
    'not rescue the stopped BRF0 family or keep collecting irrelevant gates.\n')
with (BASE/'source_snapshot/closure_close_poss_outcome_provenance.py').open('xb') as stream:
    stream.write(Path(__file__).read_bytes())
save('BOOKKEEPING.json', dict(stdlib_only=True, no_scientific_replay=True,
    wall_seconds_before_seal=time.monotonic()-START,
    RSS_before_seal_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024))
assert read(BASE/'INCOMPLETE')['scope'] == 'POP0_LAYOUT02'
(BASE/'INCOMPLETE').unlink()
files = [dict(path=str(p.relative_to(BASE)), sha256=sha(p), bytes=p.stat().st_size)
         for p in sorted(BASE.rglob('*')) if p.is_file()]
save('DELIVERY_SEAL.json', dict(status=status, entries=len(files), files=files,
    artifact_bytes_before_seal=layout.size(), original_failure_retained=True))
assert layout.size() < 16*2**20
print(json.dumps(dict(status=status, entries=len(files), bytes=layout.size(),
    Windows_seconds=seconds, child_seconds=child_seconds, peak_RSS_bytes=peak)), flush=True)
