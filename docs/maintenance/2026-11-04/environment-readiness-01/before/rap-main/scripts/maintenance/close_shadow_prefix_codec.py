"""LPC0 standard-library final identity/resource bookkeeping; no numerical replay."""
import hashlib,json,resource,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; BASE=ROOT/'docs/maintenance/2026-10-13/shadow-prefix-storage-codec-01'; START=time.monotonic()
def read(q):return json.loads(Path(q).read_text(encoding='utf-8-sig'))
def sha(q):
    h=hashlib.sha256()
    with Path(q).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def save(q,v):
    with Path(q).open('x',encoding='utf-8') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
f=read(BASE/'freeze.json');v=read(BASE/'validation.json');assert v['passed']
for q,h in f['files'].items():assert sha(q)==h,q
repos={}
for name,q in [('main',ROOT),('slam',ROOT.parent/'RAP-SLAM')]:
    def git(*a):return subprocess.check_output(['git','--no-optional-locks','-C',str(q),*a],text=True).strip()
    repos[name]=dict(head=git('rev-parse','HEAD'),branch=git('branch','--show-current'),tracked_status=git('status','--short','--untracked-files=no').splitlines())
assert repos==f['repositories']
markers=[ROOT/'docs/maintenance/2026-10-10/native-conditioned-comparison-01/INCOMPLETE',ROOT/'docs/maintenance/2026-10-10/native-conditioned-comparison-01/attempt-02/INCOMPLETE',ROOT/'docs/maintenance/2026-10-12/native-backward-reproducibility-01/INCOMPLETE',ROOT/'docs/maintenance/2026-10-13/shadow-conditioned-fit-pilot-01/INCOMPLETE']
assert all(q.exists() for q in markers)
save(BASE/'FINAL_IDENTITY_CHECK.json',dict(passed=True,frozen_identities=len(f['files']),repositories=repos,old_markers_preserved=[str(q) for q in markers]))
receipts=[]; retries=gaps=0
for stage in ('freeze','encode','validate'):
    folder=BASE/'supervision'/stage;c=read(folder/'child_exit.json');h=read(folder/'exit.json');l=read(folder/'launch.json')
    assert c['success'] and c['full_resource_capture'] and h['exit_code']==0 and c['peak_RSS_bytes']<=f['cap_RSS_bytes']
    assert c['peak_GPU_allocated_bytes']==c['peak_GPU_reserved_bytes']==c['optimizer_calls']==c['neural_calls']==0
    samples=[json.loads(x) for x in (folder/'host_memory.jsonl').read_text().splitlines() if x.strip()]
    assert samples and len(samples)==h['host_memory_observations'] and min(x['headroom_bytes'] for x in samples)>=4*2**30 and l['headroom_before_bytes']>=12*2**30
    for filename in ('logging_retry.jsonl','logging_gap.jsonl'):
        if (folder/filename).exists():
            count=len((folder/filename).read_text().splitlines())
            if filename.startswith('logging_retry'):retries+=count
            else:gaps+=count
    receipts.append(dict(stage=stage,child=c,host=h,launch=l))
assert {q.name for q in (BASE/'supervision').iterdir() if q.is_dir()}=={'freeze','encode','validate'}
seconds=sum(x['child']['wall_seconds'] for x in receipts);rss=max(x['child']['peak_RSS_bytes'] for x in receipts);assert seconds<=600
save(BASE/'RESOURCE_AUDIT.json',dict(passed=True,receipts=receipts,scientific_child_seconds_including_imports=seconds,peak_RSS_bytes=rss,GPU_bytes=0,logging_retries=retries,logging_gaps=gaps,old_caps_and_failures_unchanged=True,ordinary_setup_RSS_unknown=True,closing_identity_bookkeeping_separate=True))
save(BASE/'CHECKS.json',dict(passed=True,bit_identity_conjunction=True,source_freeze_match=True,independent_byte_decoder=True,all100_source_arrays_and_NPY_members_byteexact=True,bit_fixtures=4,old_HFIT_scientific_comparison_INCOMPLETE=True,no_neural_GT_or_missing_cases=True))
status=dict(status='VALIDATED_AVAILABLE_PREFIX_LOSSLESS_REPRESENTATION_COMPLETE',decision=v['decision'],original_HFIT='INCOMPLETE_ARTIFACT_CAP',future_bank_protocol_created=False,scientific_retry=False)
save(BASE/'STATUS.json',status)
(BASE/'REPORT.md').write_text('\n'.join(['# LPC0 available-prefix lossless representation', '',f'All {len(f["files"])} frozen identities match. All 100 available V/P prefix matrices reconstruct byte-for-byte, including complete original NPY members, against immutable same-noise/time U bases. Independent stdlib NPY parsing and byte-chunk decoder plus four signed-zero/subnormal/infinity/NaN-bit fixtures pass.', '',f'{v["source_aliases"]} source aliases and {v["encoded_deltas"]} XOR deltas require {v["encoded_delta_bytes"]} encoded payload bytes, versus {v["baseline_compressed_prefix_member_bytes"]} original compressed member bytes ({100*v["delta_to_old_member_ratio"]:.6f}%). Raw source arrays total {v["raw_source_bytes"]} bytes. U bases remain explicitly bound external source files, not copied new output. Metadata/dossier counts are recorded separately; this is not a self-contained archive size or a bound for missing cases.', '',f'Three supervised successful children: {seconds:.9f}s including imports, peak RSS {rss} bytes, GPU0; 600s/2GiB RSS/512MiB artifact caps pass, full native/Windows exits, {retries} logging retries/{gaps} gaps. Setup RSS unknown and stdlib final bookkeeping separate; old gaps/caps unchanged.', '', 'HFIT0 still has 37 unsealed partial cases and its original failed 2GiB cap/INCOMPLETE. No missing14 P traces, model/backward/update/GT metric, full noise comparison, original-native repair, physical/system gain or novelty. All original files/markers/reference/HEADs/branches/two-nine dirty sets remain; no deletion/repacking/cap increase/scientific retry/production/install/restart/commit/Git sync.'])+'\n',encoding='utf-8')
(BASE/'NEXT_ROUND_PLAN.md').write_text('# Next prerequisite — DESIGN_ONLY\n\nReview a self-contained, lossless evidence representation including immutable base dependencies, archive layout and a conservative total budget. Verify complete fit-array alias chains and serialization identities before any future execution. Available-data compression does not guarantee unobserved-case sizes. The failed HFIT0 prediction bank must not be resumed or scored as a partial comparison; no new scientific runner/protocol/retry is created here.\n',encoding='utf-8')
(BASE/'source_snapshot/closure_close_shadow_prefix_codec.py').write_bytes(Path(__file__).read_bytes())
save(BASE/'BOOKKEEPING.json',dict(standard_library_only=True,no_numerical_replay=True,wall_seconds_before_seal=time.monotonic()-START,RSS_observed_before_seal_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024))
assert (BASE/'INCOMPLETE').read_text().startswith('LPC0');(BASE/'INCOMPLETE').unlink()
files=[dict(path=str(q.relative_to(BASE)),sha256=sha(q),bytes=q.stat().st_size) for q in sorted(BASE.rglob('*')) if q.is_file()];artifact=sum(x['bytes'] for x in files);assert artifact<512*2**20
save(BASE/'DELIVERY_SEAL.json',dict(status=status['status'],decision=v['decision'],files=files,entries=len(files),artifact_bytes_before_seal=artifact))
print(json.dumps(dict(status=status['status'],deliveries=len(files),encoded_delta_bytes=v['encoded_delta_bytes'],ratio=v['delta_to_old_member_ratio'],aliases=v['source_aliases'],seconds=seconds,RSS=rss,artifact_bytes_before_seal=artifact),indent=2))
