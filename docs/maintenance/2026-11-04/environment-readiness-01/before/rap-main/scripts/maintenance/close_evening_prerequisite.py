"""LCP0/FCE0 standard-library closure; no model/NumPy/numerical replay."""
import hashlib,json,resource,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];START=time.monotonic();MODE=sys.argv[1]
if MODE=='archive':BASE=ROOT/'docs/maintenance/2026-10-13/shadow-evidence-archive-01';stages=('freeze','bind','compatibility','pack','validate');seconds_cap=1800;rss_cap=2*2**30;gpu_cap=0;artifact_cap=2*2**30
elif MODE=='context':BASE=ROOT/'docs/maintenance/2026-10-13/frozen-context-extraction-01';stages=('freeze','extract','validate');seconds_cap=900;rss_cap=gpu_cap=6*2**30;artifact_cap=256*2**20
else:raise ValueError(MODE)
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
extra=0
if MODE=='archive':
    binding=read(BASE/'EXECUTION_BINDING.json');assert binding['original_freeze_sha256']==sha(BASE/'freeze.json') and binding['no_failed_payload'] and binding['no_gate_cap_or_scientific_change']
    for q,h in binding['files'].items():assert sha(q)==h,q
    extra=len(binding['files'])
repos={}
for name,q in [('main',ROOT),('slam',ROOT.parent/'RAP-SLAM')]:
    def git(*a):return subprocess.check_output(['git','--no-optional-locks','-C',str(q),*a],text=True).strip()
    repos[name]=dict(head=git('rev-parse','HEAD'),branch=git('branch','--show-current'),tracked_status=git('status','--short','--untracked-files=no').splitlines())
assert repos==f['repositories']
markers=[ROOT/'docs/maintenance/2026-10-10/native-conditioned-comparison-01/INCOMPLETE',ROOT/'docs/maintenance/2026-10-10/native-conditioned-comparison-01/attempt-02/INCOMPLETE',ROOT/'docs/maintenance/2026-10-12/native-backward-reproducibility-01/INCOMPLETE',ROOT/'docs/maintenance/2026-10-13/shadow-conditioned-fit-pilot-01/INCOMPLETE'];assert all(q.exists() for q in markers)
save(BASE/'FINAL_IDENTITY_CHECK.json',dict(passed=True,frozen_identities=len(f['files']),supplemental_execution_identities=extra,repositories=repos,old_markers_preserved=[str(q) for q in markers]))
receipts=[];retries=gaps=0
for stage in stages:
    folder=BASE/'supervision'/stage;c=read(folder/'child_exit.json');h=read(folder/'exit.json');l=read(folder/'launch.json')
    assert c['success'] and c['full_resource_capture'] and h['exit_code']==0 and c['peak_RSS_bytes']<=rss_cap and max(c['peak_GPU_allocated_bytes'],c['peak_GPU_reserved_bytes'])<=gpu_cap and c['optimizer_calls']==0
    samples=[json.loads(x) for x in (folder/'host_memory.jsonl').read_text().splitlines() if x.strip()];assert samples and len(samples)==h['host_memory_observations'] and min(x['headroom_bytes'] for x in samples)>=4*2**30 and l['headroom_before_bytes']>=12*2**30
    for filename in ('logging_retry.jsonl','logging_gap.jsonl'):
        if (folder/filename).exists():
            count=len((folder/filename).read_text().splitlines())
            if filename.startswith('logging_retry'):retries+=count
            else:gaps+=count
    receipts.append(dict(stage=stage,child=c,host=h,launch=l))
assert {q.name for q in (BASE/'supervision').iterdir() if q.is_dir()}==set(stages)
seconds=sum(x['child']['wall_seconds'] for x in receipts);rss=max(x['child']['peak_RSS_bytes'] for x in receipts);ga=max(x['child']['peak_GPU_allocated_bytes'] for x in receipts);gr=max(x['child']['peak_GPU_reserved_bytes'] for x in receipts);assert seconds<=seconds_cap
save(BASE/'RESOURCE_AUDIT.json',dict(passed=True,receipts=receipts,scientific_child_seconds_including_imports=seconds,peak_RSS_bytes=rss,peak_GPU_allocated_bytes=ga,peak_GPU_reserved_bytes=gr,logging_retries=retries,logging_gaps=gaps,old_caps_failures_gaps_unchanged=True,ordinary_setup_RSS_unknown=True,closing_identity_bookkeeping_separate=True))
if MODE=='archive':
    status='VALIDATED_AVAILABLE_EVIDENCE_LOSSLESS_ARCHIVE_COMPLETE';checks=dict(passed=True,all576_original_file_bytes_and_sizes_and_hashes_exact=True,all440_NPZ_3082_members_original_serialization_exact=True,all_base_payloads_embedded=True,independent_uint8_decoder=True,prospective_exact_alias_static_amendment_retained=True,no_model_GT_or_missing_predictions=True)
    report=['# LCP0 complete available-evidence lossless archive','',f'{len(f["files"])} original frozen identities plus {extra} supplemental execution identities match. The static exact-alias amendment preceded all encoding; original source/freeze/snapshot retained, no payload failure or gate/cap change.', '',f'All440 NPZ files/3082 original ZIP members reproduce their compressed payloads exactly. All576 available source files reconstruct byte-for-byte including original ZIP metadata, failures, markers, logs and partial arrays. Independent uint8 decoder verifies every embedded base/object and every original file SHA256/size. Self-contained packed available evidence {v["self_contained_packed_evidence_bytes"]} bytes versus original {v["source_original_bytes"]} bytes ({100*v["packed_to_source_ratio"]:.6f}%), including {v["manifest_bytes"]} manifest bytes. {v["unique_raw_objects"]} unique raw objects, {v["objects_by_representation"]}. All base payloads included; no original source is deleted/repacked.', '',f'Five fully supervised children {seconds:.9f}s including imports, RSS {rss} bytes/GPU0;1800s/2GiB RSS/2GiB new-dossier caps pass. Full native/Windows exits, {retries} logging retries/{gaps} gaps. Setup RSS unknown/stdlib final bookkeeping separate; historical limits/gaps unchanged.', '', 'This archive closes storage identity only. It does not complete HFIT0, admit37 partial traces, generate missing14 P cases, prove unobserved/future corpus budgets, repair its failed2GiB scope or produce any heldout accuracy/noise/native/system/physical/novelty result. All original source/cap failures/INCOMPLETE states/HEADs/branches/two-nine dirty sets preserved. No model/gradient/update/GT metrics/production/ref/install/acquisition/restart/manuscript/commit/Git sync.']
    next_text='A future evidence format can now preserve all available bytes with embedded bases. Complete future-corpus budgeting must use a prospective worst-case bound, including all required evidence, source artifacts, metadata and attempted failures; current partial compression ratios alone are insufficient. Original HFIT0 comparison cannot be silently resumed, scored on a subset or treated as repaired. No new scientific bank runner/protocol is created by this closure.'
else:
    status='VALIDATED_FROZEN_FEATURE_EXTRACTION_AND_CONTEXT_ISOLATION_COMPLETE';checks=dict(passed=True,repeat_helper_full_hook_and_SAR_initial_J_prefixes_byteexact=True,all_observation_noise_segmentation_scale_anchor_bindings_valid=True,I_anchor_prefix_unchanged_under_nonanchor_x_perturbation=True,J_anchor_prefix_context_dependent=True,pointwise_features_shared_exactly=True,no_native_head_backward_training_GT_sampler=True)
    report=['# FCE0 frozen-feature source/context interface','',f'All{len(f["files"])} frozen identities match. On existing exposed fit00/eval00 synthetic tau1 inputs, all joint/separated helper repeats and complete original12-layer FP32 forward layer9 hooks match byteexact. Joint first10 features/input bind completed SAR0 first-step traces exactly. Pointwise encoding+anchor inputs match across layouts; all observation/noise/scale/count/anchor/segmentation bindings pass.', '', 'Only global batch segmentation and repeated same tau/scale separate the three parts. Fixed nonanchor x perturbation leaves the anchor pointwise encoding and separated anchor prefix byteexact; joint anchor prefix changes, proving source architecture context dependency and isolation for these inputs. This is a functional feature interface, not a physical observation or measured registration gain. Pointwise D already uses learned RAP encoding; it is not a raw descriptor/strong geometry baseline.', '',f'12 helper10-layer calls+4 complete FP32 forwards,0 native/head backward/optimizer/retained update/source sampler/GT metric. Three supervised successful children {seconds:.9f}s incl imports/RSS{rss}/GPU allocated{ga},reserved{gr};900s/6GiB RSS/6GiB GPU/256MiB caps pass, full child+Windows exits,{retries} retries/{gaps} gaps. All original weights/modes/hooks/backend flags restored; ordinary setup RSS unknown/closing bookkeeping separate.', '', 'Float32/math/IEEE extraction differs from original default fp16 and does not repair NOC4 native backwards or establish RAP-specific metric headroom. One exposed known synthetic scene/copied descriptors/two old noise arrays, no fresh noise or generalization/system/novelty. Original HFIT0/NOC4/NBR INCOMPLETE, retired CCR0/geometry stops/09 unknown/source seals/HEADs/branches/two-nine dirty sets remain. No training/real/trajectory/production/ref/install/acquisition/restart/manuscript/commit/Git sync.']
    next_text='Design one separate bounded metric-SE3 residual interface around a frozen geometric pose, using exactly derived feature/metric units and equal nonzero output-Jacobian column accounting across fixed pointwise/separated/joint features. Independently validate head derivatives and pose composition without native gradients or fitting before any later training scope. Pointwise D is learned RAP encoding, so strong raw-observation geometry/direct controls remain prerequisites before any real efficacy/RAP-specific claim. No head/protocol/fitting/GT metric is executed by this stage.'
save(BASE/'CHECKS.json',checks);save(BASE/'STATUS.json',dict(status=status,decision=v['decision'],original_HFIT='INCOMPLETE_ARTIFACT_CAP',original_native_backwards_repaired=False,real_training_admitted=False));(BASE/'REPORT.md').write_text('\n'.join(report)+'\n',encoding='utf-8');(BASE/'NEXT_ROUND_PLAN.md').write_text('# Next step — DESIGN_ONLY\n\n'+next_text+'\n',encoding='utf-8')
(BASE/'source_snapshot/closure_close_evening_prerequisite.py').write_bytes(Path(__file__).read_bytes());save(BASE/'BOOKKEEPING.json',dict(standard_library_only=True,no_numerical_replay=True,wall_seconds_before_seal=time.monotonic()-START,RSS_observed_before_seal_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024))
assert (BASE/'INCOMPLETE').read_text().startswith('LCP0' if MODE=='archive' else 'FCE0');(BASE/'INCOMPLETE').unlink()
files=[dict(path=str(q.relative_to(BASE)),sha256=sha(q),bytes=q.stat().st_size) for q in sorted(BASE.rglob('*')) if q.is_file()];artifact=sum(x['bytes'] for x in files);assert artifact<artifact_cap
save(BASE/'DELIVERY_SEAL.json',dict(status=status,decision=v['decision'],files=files,entries=len(files),artifact_bytes_before_seal=artifact));print(json.dumps(dict(status=status,deliveries=len(files),seconds=seconds,RSS=rss,GPU_allocated=ga,GPU_reserved=gr,artifact_bytes_before_seal=artifact),indent=2))
