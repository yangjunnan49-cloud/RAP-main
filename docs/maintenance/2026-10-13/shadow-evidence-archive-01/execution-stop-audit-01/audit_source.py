"""LCP0 standard-library available-artifact/resource stop audit, no codec replay."""
import hashlib,json,resource,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'docs/maintenance/2026-10-13/shadow-evidence-archive-01';OUT=BASE/'execution-stop-audit-01';START=time.monotonic();OUT.mkdir()
def read(q):return json.loads(Path(q).read_text(encoding='utf-8-sig'))
def sha(q):
    h=hashlib.sha256()
    with Path(q).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def save(q,v):
    with Path(q).open('x',encoding='utf-8') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
f=read(BASE/'freeze.json');b=read(BASE/'EXECUTION_BINDING.json');assert b['original_freeze_sha256']==sha(BASE/'freeze.json')
for q,h in {**f['files'],**b['files']}.items():assert sha(q)==h,q
repos={}
for name,q in [('main',ROOT),('slam',ROOT.parent/'RAP-SLAM')]:
    def git(*a):return subprocess.check_output(['git','--no-optional-locks','-C',str(q),*a],text=True).strip()
    repos[name]=dict(head=git('rev-parse','HEAD'),branch=git('branch','--show-current'),tracked_status=git('status','--short','--untracked-files=no').splitlines())
assert repos==f['repositories'];assert (BASE/'INCOMPLETE').exists();assert not (BASE/'packed/manifest.json').exists() and not (BASE/'packed_seal.json').exists() and not (BASE/'validation.json').exists() and not (BASE/'DELIVERY_SEAL.json').exists()
compat=read(BASE/'compatibility.json');assert compat['passed'] and compat['NPZ_files']==440 and compat['members']==3082
stages=('freeze','bind','compatibility','pack');receipts=[];retry=gap=0
for stage in stages:
    q=BASE/'supervision'/stage;c=read(q/'child_exit.json');h=read(q/'exit.json');l=read(q/'launch.json');assert c['full_resource_capture'] and c['success']==(stage!='pack') and h['exit_code']==(1 if stage=='pack' else 0)
    assert c['peak_GPU_allocated_bytes']==c['peak_GPU_reserved_bytes']==c['optimizer_calls']==c['neural_calls']==0
    samples=[json.loads(x) for x in (q/'host_memory.jsonl').read_text().splitlines() if x.strip()];assert samples and len(samples)==h['host_memory_observations'] and min(x['headroom_bytes'] for x in samples)>=4*2**30 and l['headroom_before_bytes']>=12*2**30
    for name in ('logging_retry.jsonl','logging_gap.jsonl'):
        if (q/name).exists():
            n=len((q/name).read_text().splitlines())
            if name.startswith('logging_retry'):retry+=n
            else:gap+=n
    receipts.append(dict(stage=stage,child=c,host=h,launch=l))
assert {q.name for q in (BASE/'supervision').iterdir() if q.is_dir()}==set(stages)
failure=read(BASE/'FAILURE_pack.json');assert 'aggregate attempted-child time cap' in failure['error'];seconds=sum(x['child']['wall_seconds'] for x in receipts);rss=max(x['child']['peak_RSS_bytes'] for x in receipts);assert seconds>1800 and rss<2*2**30
stderr=(BASE/'supervision/pack/stderr.log').read_text(encoding='utf-8',errors='replace');assert 'is_file' in stderr and 'aggregate attempted-child time cap' in stderr
blobs=[q for q in (BASE/'packed/blobs').iterdir() if q.is_file()];blob_bytes=sum(q.stat().st_size for q in blobs)
status=dict(status='AUDITED_AVAILABLE_EVIDENCE_ARCHIVE_STOP_AT_TIME_CAP',decision='ZIP_SERIALIZATION_VALID_PARTIAL_PACK_UNSEALED_NO_COMPLETE_RECONSTRUCTION',archive_complete=False,scientific_model_execution=False,original_HFIT='INCOMPLETE_ARTIFACT_CAP',LCP0='INCOMPLETE_TIME_CAP',retry=False)
save(BASE/'STATUS.json',status)
files=[dict(path=str(q.relative_to(BASE)),sha256=sha(q),bytes=q.stat().st_size) for q in sorted(BASE.rglob('*')) if q.is_file() and OUT not in q.parents and q.name!='AVAILABLE_DELIVERY_SEAL.json'];save(BASE/'AVAILABLE_DELIVERY_SEAL.json',dict(status=status['status'],complete_archive=False,original_time_cap_failed=True,files=files,entries=len(files)))
save(OUT/'IDENTITY_CHECKS.json',dict(passed=True,original_frozen_identities=len(f['files']),supplemental_execution_identities=len(b['files']),repositories=repos,all_source_and_partial_output_files_hashed=True,available_entries=len(files)))
save(OUT/'RESOURCE_AUDIT.json',dict(complete_capture=True,receipts=receipts,attempted_scientific_child_seconds_including_imports=seconds,cap_seconds=1800,time_cap_PASS=False,timer_failure_snapshot=failure,peak_RSS_bytes=rss,RSS_cap_PASS=True,GPU_bytes=0,GPU_cap_PASS=True,partial_new_artifact_bytes_at_child_exit=receipts[-1]['child']['artifact_bytes'],artifact_cap_PASS=receipts[-1]['child']['artifact_bytes']<=2*2**30,logging_retries=retry,logging_gaps=gap,full_child_and_Windows_exits=True,ordinary_setup_RSS_unknown=True,stdlib_stop_bookkeeping_separate=True,old_caps_gaps_unchanged=True))
save(OUT/'CHECKS.json',dict(passed=True,scope='identity/count/resource available-evidence stop audit only',ZIP_compatibility_files=440,ZIP_compatibility_members=3082,partial_payload_objects=len(blobs),partial_payload_bytes=blob_bytes,no_manifest_or_packed_seal_or_reconstruction_validation=True,no_full_archive_claim=True,no_model_numpy_GT_or_codec_replay=True,old_HFIT_INCOMPLETE=True))
save(OUT/'STATUS.json',status)
(OUT/'REPORT.md').write_text('\n'.join(['# LCP0 available-evidence archive stop audit','',f'Original{len(f["files"])} identities plus{len(b["files"])} separately bound exact-alias execution identities match; static amendment preceded any encoding and original source retained. All440 NPZ/3082 member raw-deflate byte compatibility gates pass.', '',f'Packing stops at the original aggregate1800s timer, inside cap -> usage -> repeated file-size census -> pathlib.is_file/stat. Failure snapshot{failure["wall_seconds"]:.9f}s for pack, completed child receipt{receipts[-1]["child"]["wall_seconds"]:.9f}s; all four attempted child receipts total{seconds:.9f}s including imports, exceeding1800s after full stop bookkeeping. TIME cap FAIL, not all-caps-pass. Full RSS{rss}/GPU0 and partial output{receipts[-1]["child"]["artifact_bytes"]} bytes pass their separate2GiB bounds; full native+Windows exits/host logs,{retry} retries/{gap} gaps. Stack location does not uniquely apportion all elapsed time or establish an external runtime failure.', '',f'Partial{len(blobs)} payload objects/{blob_bytes} bytes are preserved and hashed; no complete576-file manifest, packed seal, independent whole-file reconstruction or archive completion. {len(files)} available deliveries sealed separately, not a completed lossless archive. Keep LCP0 INCOMPLETE. No cap raise/deletion/packing retry or inference from unsealed object sizes. Ordinary setup RSS unknown/stdlib stop audit separate; old caps/gaps unchanged.', '', 'LPC0 all100 prefix bytes remain validated. FCE0 feature/context and FHR0 head derivatives are separate valid prerequisites; this time failure does not amend their gates or prove accuracy. HFIT0 original2GiB artifact failure/37 unsealed cases/no noise metrics/INCOMPLETE and NOC4/NBR markers remain. No model/gradient/update/GT metrics/missing cases/production/ref/install/acquisition/restart/manuscript/commit/Git sync; original HEADs/branches/two-nine dirty sets retained.'])+'\n',encoding='utf-8')
(OUT/'NEXT_ROUND_PLAN.md').write_text('# Next storage step — DESIGN_ONLY\n\nA prospective resource-accounting prerequisite may compare complete directory census with a rigorously validated incremental output ledger on immutable files before any different archive execution. The observed timeout stack is evidence of its interrupted location, not a measured full-time decomposition. No new accounting runner/protocol/packing retry or cap change is created here. Preserve every unsealed payload and all original failures. Continue unrelated frozen-feature/strong-baseline prerequisites under their own scopes.\n',encoding='utf-8')
(OUT/'audit_source.py').write_bytes(Path(__file__).read_bytes());save(OUT/'BOOKKEEPING.json',dict(standard_library_only=True,no_numerical_or_codec_replay=True,wall_seconds_before_seal=time.monotonic()-START,RSS_observed_before_seal_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024));auditfiles=[dict(path=str(q.relative_to(OUT)),sha256=sha(q),bytes=q.stat().st_size) for q in sorted(OUT.rglob('*')) if q.is_file()];save(OUT/'DELIVERY_SEAL.json',dict(status=status['status'],files=auditfiles,entries=len(auditfiles)));print(json.dumps(dict(status=status['status'],available_entries=len(files),audit_entries=len(auditfiles),partial_objects=len(blobs),partial_bytes=blob_bytes,attempted_seconds=seconds,RSS=rss),indent=2))
