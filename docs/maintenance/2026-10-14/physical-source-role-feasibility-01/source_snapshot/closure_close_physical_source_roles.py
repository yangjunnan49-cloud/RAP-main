"""PSR0 stdlib documentation closure, distinct from supervised audit payloads."""
import time
START = time.monotonic()
import hashlib
import json
import resource
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'docs/maintenance/2026-10-14/physical-source-role-feasibility-01'

def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))

def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as stream:
        for body in iter(lambda: stream.read(1048576), b''):
            h.update(body)
    return h.hexdigest()

def save(name, value):
    with (BASE/name).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')

def text(name, value):
    with (BASE/name).open('x', encoding='utf-8') as stream:
        stream.write(value+'\n')

f = read(BASE/'freeze.json')
v = read(BASE/'validation.json')
a = read(BASE/'inventory.json')
assert v['passed']
for p, h in f['files'].items():
    assert sha(p) == h, p
repos = {}
for key, folder in [('main', ROOT), ('slam', ROOT.parent/'RAP-SLAM')]:
    def git(*args):
        return subprocess.check_output(['git', '--no-optional-locks', '-C', str(folder), *args], text=True).strip()
    repos[key] = dict(head=git('rev-parse', 'HEAD'), branch=git('branch', '--show-current'),
                     tracked_status=git('status', '--short', '--untracked-files=no').splitlines())
assert repos == f['repositories']
receipts = []
retries = gaps = 0
for stage in ('freeze', 'inventory', 'validate'):
    folder = BASE/'supervision'/stage
    c, w, launch = [read(folder/n) for n in ('child_exit.json', 'exit.json', 'launch.json')]
    assert c['success'] and c['full_resource_capture'] and w['exit_code'] == 0
    assert c['peak_RSS_bytes'] <= 512*2**20
    assert c['peak_GPU_allocated_bytes'] == c['peak_GPU_reserved_bytes'] == c['model_calls'] == c['optimizer_calls'] == 0
    samples = [json.loads(line) for line in (folder/'host_memory.jsonl').read_text().splitlines()]
    assert len(samples) == w['host_memory_observations'] and samples
    assert min(s['headroom_bytes'] for s in samples) >= 4*2**30
    assert launch['headroom_before_bytes'] >= 12*2**30
    for name in ('logging_retry.jsonl', 'logging_gap.jsonl'):
        p = folder/name
        if p.exists():
            count = len(p.read_text().splitlines())
            if name.startswith('logging_retry'):
                retries += count
            else:
                gaps += count
    receipts.append(dict(stage=stage, child=c, Windows=w, launch=launch))
assert {p.name for p in (BASE/'supervision').iterdir() if p.is_dir()} == {'freeze', 'inventory', 'validate'}
windows_seconds = sum(r['Windows']['wall_seconds'] for r in receipts)
child_seconds = sum(r['child']['wall_seconds'] for r in receipts)
assert windows_seconds <= 900
status = 'VALIDATED_EXISTING_PHYSICAL_SOURCE_AND_EXPOSURE_ROLE_FEASIBILITY_COMPLETE'
save('RESOURCE_AUDIT.json', dict(passed=True, receipts=receipts,
    attempted_Windows_seconds_including_startup_and_imports=windows_seconds,
    scientific_child_seconds_after_time_bootstrap=child_seconds,
    peak_RSS_bytes=max(r['child']['peak_RSS_bytes'] for r in receipts), GPU_bytes=0,
    logging_retries=retries, logging_gaps=gaps, ordinary_preparation_RSS_unknown=True,
    initial_sandbox_WSL_syntax_nonexecution=True, escalated_syntax_check_passed=True,
    stdlib_closure_separate=True, historical_gaps_and_caps_unchanged=True))
save('FINAL_IDENTITY_CHECK.json', dict(passed=True, frozen_identities=len(f['files']),
    repositories=repos, selected_historical_bindings_only=True, all_history_replay=False))
save('CHECKS.json', dict(passed=True, **{k:v[k] for k in ('sequences','scan_metadata_files',
    'independent_provenance_queries','labeled_KITTI_scans','boreas_old_objects_verified',
    'source_citations_verified')}, no_new_numeric_schema_or_raw_pose_model_metric=True,
    existing_data_exposure_and_unknown_membership_preserved=True))
save('STATUS.json', dict(status=status, decision=v['decision'],
    independent_confirmation_established=False, real_residual_fit_admitted=False,
    next='BOUNDED_REMAINING_SOURCE_ROLE_AND_COMMON_INPUT_STRONG_CONTROL_CONTRACT'))
text('REPORT.md', '\n'.join([
    '# PSR0 existing physical source and role feasibility', '',
    f'All{len(f["files"])} frozen identities match. Independent stdlib validation checks '
    f'{v["sequences"]} KITTI directories/{v["scan_metadata_files"]} scan filename-size records, '
    f'{v["labeled_KITTI_scans"]} labeled00-10 records,33 old DS0 metadata hashes, '
    f'{v["independent_provenance_queries"]} exact provenance paths,10 old Boreas objects '
    f'and{v["source_citations_verified"]} production source line citations.', '',
    'All22 canonical sequences contain contiguous positive16-byte-aligned scan files. '
    'This is file metadata readiness, not finite XYZ, acquisition identity or physical '
    'reference validation. All220 exact independent-provenance paths are absent in '
    'the queried sequence directories only; no global absence is asserted. Existing '
    'DS0 pose/time/calibration hashes match without numeric pose parsing or schema replay.', '',
    'KITTI00-05 remains exposed fit/calibration/development,06 development,07-10 '
    'exposed evaluation/development.11-21 raw availability does not supply local '
    'official supervised labels. Checkpoint membership and physical site exclusion '
    'remain UNKNOWN throughout. Oxford has only the five known GT text files; '
    'Boreas retains the ten original access objects including only two first-scan '
    'examples. Neither is an authenticated complete independent confirmation cohort. '
    'POSS and sibling KITTI roots exist but only immediate entries were inspected; '
    'their deeper availability/exposure remains for a distinct bounded inventory.', '',
    'Decision: '+v['decision']+'. An honestly labeled exposed engineering design is '
    'possible; no new residual fit is admitted by this inventory. Next must establish '
    'the exact common observations/statistics/base pose, strong raw geometry/direct '
    'controls, active capacity, data roles and measured total-work contract. Existing '
    'RLP2/CCR0/MGR0 failures must be considered before calling a proposed route new. '
    'Changed head/normalizer/bounds require new numerical gates.', '',
    f'Three successful supervised CPU stages: Windows total{windows_seconds:.9f}s '
    '(includes startup/imports), child total'+f'{child_seconds:.9f}s after time bootstrap; '
    f'peakRSS{max(r["child"]["peak_RSS_bytes"] for r in receipts)},GPU0; '
    '900s/512MiB/32MiB caps pass. Full child and Windows exits/host records; '
    f'{retries} logging retries/{gaps} gaps. Initial sandbox WSL syntax nonexecution '
    'was resolved by authorized execution of the existing runtime; no restart/install. '
    'Ordinary preparation RSS unknown, final stdlib closure separate.', '',
    'No numerical point-cloud/pose parsing, labels, geometry, descriptor/model load, '
    'backward/fit/trajectory or metric evaluation. This does not resolve09 or establish '
    'physical/generalization/system/RAP-specific gain. All five old INCOMPLETE markers, '
    'original HEADs/branches/two-nine tracked dirty sets and historical stops/gaps '
    'remain. No production/default/reference/manuscript/environment/acquisition/commit/Git sync.'
]))
text('NEXT_ROUND_PLAN.md', '# Conditional next round\n\n'
    'Inspect only existing POSS and sibling KITTI source metadata plus historical '
    'role/binding records under a separately frozen scope; distinguish mirror bytes '
    'from independent acquisition. Then define a common-input/strong-control design '
    'whose observable question differs from retired RLP2/CCR0 and the congruent '
    'fixture. No fresh confirmation label, solver/head fit or archive retry follows '
    'automatically. Physical truth/checkpoint exclusion may remain unknown without '
    'blocking a clearly limited engineering prerequisite.\n')
with (BASE/'source_snapshot/closure_close_physical_source_roles.py').open('xb') as out:
    out.write(Path(__file__).read_bytes())
save('BOOKKEEPING.json', dict(standard_library_only=True,
    wall_seconds_before_delivery_seal=time.monotonic()-START,
    RSS_before_delivery_seal_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
    no_numeric_replay=True))
assert read(BASE/'INCOMPLETE')['scope'] == 'PSR0'
(BASE/'INCOMPLETE').unlink()
files = [dict(path=str(p.relative_to(BASE)), sha256=sha(p), bytes=p.stat().st_size)
         for p in sorted(BASE.rglob('*')) if p.is_file()]
size = sum(p['bytes'] for p in files)
assert size < 32*2**20
save('DELIVERY_SEAL.json', dict(status=status, entries=len(files), files=files,
                              artifact_bytes_before_seal=size))
print(json.dumps(dict(status=status, entries=len(files), bytes=size,
                      Windows_seconds=windows_seconds, child_seconds=child_seconds)), flush=True)
