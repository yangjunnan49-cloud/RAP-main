"""Seal available NOC4 retry evidence without claiming completed neural comparison."""
import json
from pathlib import Path
import native_conditioned_comparison as r
c=r.c;ORIGINAL=r.BASE;BASE=ORIGINAL/'attempt-02';AUDIT=BASE/'execution-stop-audit-01'
r.BASE=r.old.BASE=BASE
SUPERVISION=c.MAIN/'docs/maintenance/2026-10-10/native-conditioned-comparison-supervision-02'
for p,h in c.read(BASE/'CLOSURE_SOURCE_FREEZE.json')['files'].items():assert c.sha(p)==h,p
f=r.check();r.check_seal(AUDIT);v=c.read(AUDIT/'validation.json');assert v['passed']
for p,h in c.read(AUDIT/'freeze.json')['files'].items():assert c.sha(p)==h,p
for row in c.read(ORIGINAL/'DELIVERY_SEAL.json')['files']:assert c.sha(ORIGINAL/row['path'])==row['sha256']
assert r.old_deliveries()==[103,188,53,5,37]
assert not (BASE/'bank/synthetic_V').exists() and not (BASE/'bank/synthetic_P').exists()
assert not (BASE/'bank/synthetic_predictions').exists() and (BASE/'INCOMPLETE').exists()
repos=r.n.noc.git_state();assert repos==f['repositories']
receipts=[]
for stage in ('freeze','prepare','preflight','validate_preflight','audit_stop'):
    child=c.read(SUPERVISION/stage/'child_exit.json');host=c.read(SUPERVISION/stage/'exit.json')
    assert child['full_resource_capture']
    assert child['success']==(stage!='validate_preflight') and host['exit_code']==(1 if stage=='validate_preflight' else 0)
    assert host['minimum_observed_headroom_bytes']>=4*2**30
    assert child['peak_RSS_bytes']<=4*2**30
    assert max(child['peak_GPU_allocated_bytes'],child['peak_GPU_reserved_bytes'])<=3*2**30
    receipts.append(dict(stage=stage,child=child,host=host))
wall=sum(x['child']['wall_seconds'] for x in receipts);assert wall<=1800
rss=max(x['child']['peak_RSS_bytes'] for x in receipts)
ga=max(x['child']['peak_GPU_allocated_bytes'] for x in receipts);gr=max(x['child']['peak_GPU_reserved_bytes'] for x in receipts)
resource=dict(passed=True,all_attempted_native_and_CPU_audit_peaks_captured=True,all_failed_stages_counted=True,
    receipts=receipts,payload_wall_seconds=wall,external_Windows_wall_seconds=sum(x['host']['wall_seconds'] for x in receipts),
    peak_RSS_bytes=rss,peak_GPU_allocated_bytes=ga,peak_GPU_reserved_bytes=gr,
    minimum_host_headroom_bytes=min(x['host']['minimum_observed_headroom_bytes'] for x in receipts),
    limits=f['limits'],old_resource_gaps_not_amended=True,exclusions=['imports','WSL startup','design/docs','final identity/delivery bookkeeping'],production_latency=False)
c.save(BASE/'RESOURCE_AUDIT.json',resource);c.save(BASE/'SUPERVISED_RESOURCE_AUDIT.json',resource)
c.save(BASE/'REPOSITORY_STATE.json',dict(repositories=repos,heads_branches_tracked_sets_preserved=True,
    source_model_config_checkpoint_sibling_helpers_unchanged=True,no_commit_or_sync=True))
c.save(BASE/'CHECKS.json',dict(status='AVAILABLE_ARTIFACT_AUDIT_PASSED',scientific_native_comparison_incomplete=True,
    freeze_entries=len(f['files']),audit_freeze_entries=len(c.read(AUDIT/'freeze.json')['files']),
    old_delivery_counts_unchanged=v['old_delivery_counts_unchanged'],original_optimizer_probe_calls=2,
    validator_optimizer_probe_calls=2,retained_probe_updates=0,fit_updates=0,native_comparison_prediction_traces=0,
    real_windows=0,full_forward_validator_passed=False,CPU_artifact_audit=v))
rows=[]
for cell in v['records']:
    for p in cell['paths']:
        rows.append(f"| {cell['arm']} | {p['forward']} | {p['loss_before']:.12g} | {p['loss_after']:.12g} | {p['gradient_dot_actual_update']:.12g} | {p['parameter_delta_L2']:.9g} |")
report=f'''# NOC4 supervised retry: audited native preflight stop

**AUDITED_NATIVE_PREFLIGHT_STOP_WITH_REPLAY_MISMATCH**; decision **{v['decision']}**. The runtime recovery succeeded, and this separate attempt reached the original native probes normally. Both V/P original probes fail the prospective loss-decrease prerequisite. The original full-forward validator succeeds for V arrays but fails P byte equality. The scientific comparison remains INCOMPLETE; the delivery seal certifies available evidence and its bounded artifact audit, not completed neural training or independent full-forward validation.

## Executed versus planned

Exactly four restored one-step AdamW calls occurred: two original cached probes and two full-forward validation probes. All metadata/arrays are retained; zero probe updates are used for training. No400-update arm, fitted adapter,72 comparison sampler traces, held-out performance gate, real/nearby window or trajectory was executed. The separate WSL recovery performed target-free five-step checks; those are runtime checks rather than NOC4 comparison predictions. All24 original noises/fixture were reused byte-exactly; only fit00 enters the probes. No new seed, setting or threshold was selected.

## Actual probe evidence

Same443904 trainables, original initialization, AdamW1e-4/eps1e-8/betas(.9,.999), no clipping/decay, fixed unscaled V1024/P1/1024 backward policy. Every B tensor and MLP group has finite active gradients and actual finite updates. A is inactive at B0 and unchanged as expected. Selected output-weight FD and per-parameter maximum-update tests pass. Each original probe fails only loss_decreases; both full-forward probes also increase their respective objectives.

| Arm | Forward | Loss before | Loss after | Gradient dot actual update | Total parameter delta L2 |
| --- | --- | --- | --- | --- | --- |
{chr(10).join(rows)}

The negative linearized gradient dot update and positive observed loss change coexist. A1e-4 maximum coordinate change corresponds to approximately.0603/.0650 total parameter movement. These observations motivate checking functional update scale; they do not uniquely establish overshoot, curvature, fp16 nondeterminism or a cache implementation cause. Selected output FD does not certify the entire parameter-direction derivative. Do not interpret an active gradient as convergence or native learnability evidence.

V initial/gradient/updated-parameter/optimizer/before-after output arrays match exactly. P initial arrays and pre-update output match exactly, but gradients differ at7268 values(max.375), updated parameters at4329(max.000199999245524), and endpoint output at8997(max.000820875168). The P MLP group norms agree; differences appear in the B gradient group. No byte-equality tolerance was relaxed and no new replay was executed after the failure. Both P paths fail the same loss-decrease prerequisite; their mismatch remains unresolved.

## Bounded audit, resources and preservation

The failed validator's source/folders/exception/exit/full resource receipts remain unchanged. An independently scoped CPU-only audit reads existing arrays: NumPy first-Adam formula maximum difference{v['independent_numpy_first_Adam_step_max_delta']:.9g}; independent Horn/direct stored objective maximum difference{v['independent_stored_objective_max_delta']:.9g}. Stored selected-FD outcomes and all gate metadata are checked. This is not fresh neural FD/gradient replay, a full training replay or a validator repair. No additional model load/native forward/backward/optimizer/GPU occurs in the stop audit.

All five attempted payloads including failed validation and CPU audit total{wall:.6f}s; RSS{rss}bytes, GPU allocated/reserved{ga}/{gr}bytes. Every child full peak and Windows exit is captured. New1800s/3GiB GPU/4GiB RSS/512MiB caps pass, CPU audit120s/1GiB/64MiB passes; external Windows walls/headroom records are retained. Imports/WSL startup/design/docs/final identity/delivery bookkeeping excluded, not production latency. Historical NOC4 resource gaps are not retrospectively amended. Whole dossier plus external supervisor logs remain below512MiB.

Original NOC4 stopped60-entry delivery, prior103/188/53/5/37 delivery identities, both HEADs/branches/two and nine tracked dirty sets, model/config/checkpoint/sibling helpers are preserved. Original INCOMPLETE and all stops remain. No production/default/backbone/manuscript/reference edit, install, commit or Git sync. This exposed copied-descriptor synthetic task establishes neither physical accuracy, generalization, system gain nor an original mechanism. NOC3's rigid-control positive signal and NOC2's affine stop remain unchanged.

Next work is DESIGN_ONLY in NEXT_ROUND_PLAN.md. Stop exact current optimizer/rate/scale/steps/seeds/init/gate rescue and dependent fitted/native/real expansion.
'''
(BASE/'REPORT.md').write_text(report)
(BASE/'NEXT_ROUND_PLAN.md').write_text('''# Next design after native preflight stop

DESIGN_ONLY, no new protocol freeze or numerical execution. Preserve the declared prerequisite failure and P replay mismatch; do not run400 updates or relax loss-decrease/byte-equality gates.

First design a bounded computational reproducibility diagnosis, separately from optimizer fitting: distinguish repeated full-forward backward from cached versus full backward on identical immutable inputs, retaining upstream endpoint gradients and each trainable tensor rather than only group norms. Predeclare numeric precision/determinism checks, matching criteria, zero retained update policy and failure/resource boundaries. The current P discrepancy does not prove caching is its unique cause; V exact replay also prevents a blanket cache-failure conclusion. Such a new diagnostic is not executed or frozen here.

Only after justified reproducible parameter-direction evidence should a distinct optimizer policy be designed around whole-parameter/functional update magnitude and directional finite differences. The current selected output-weight FD and coordinate bound do not certify actual-step descent. NOC3's twelve-dimensional scaled float64 L-BFGS cannot be imported as proof of neural conditioning. Do not rescue this exact pilot with extra rates/steps/scales/seeds/init, retain old affine stops, and require a fresh prospective scope before any new neural numerical execution. No real/nearby/trajectory or production promotion follows.
''')
(BASE/'HANDOFF.md').write_text('# NOC4 retry handoff\n\nAUDITED_NATIVE_PREFLIGHT_STOP_WITH_REPLAY_MISMATCH; PROBE_LOSS_INCREASE_AND_P_REPLAY_MISMATCH. Read REPORT/NEXT_ROUND_PLAN/PROTOCOL/OWNER_SCOPE/STATUS/CHECKS/RESOURCE_AUDIT/SUPERVISED_RESOURCE_AUDIT/DELIVERY_SEAL; original204-entry freeze and execution-stop-audit-01 scope/freeze/validation/seal. Four restored optimizer probes, zero retained updates/fits/predictions/real windows. Available artifact audit passes; original full-forward P replay validation fails and comparison remains INCOMPLETE. All failures/sources/old identities remain. Next DESIGN_ONLY; no exact numerical rescue.\n')
c.status(BASE,'audited_stop',status='AUDITED_NATIVE_PREFLIGHT_STOP_WITH_REPLAY_MISMATCH',decision=v['decision'],
    scientific_comparison_complete=False,keep_INCOMPLETE=True,fit_updates=0,optimizer_probe_calls=4,retained_probe_updates=0)
size=sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file())
external_size=sum(p.stat().st_size for p in SUPERVISION.rglob('*') if p.is_file())
assert size+external_size<512*2**20
entries=[dict(path=str(p.relative_to(BASE)),sha256=c.sha(p),bytes=p.stat().st_size)
    for p in sorted(BASE.rglob('*')) if p.is_file() and p.name!='DELIVERY_SEAL.json']
c.save(BASE/'DELIVERY_SEAL.json',dict(status='AUDITED_NATIVE_PREFLIGHT_STOP_WITH_REPLAY_MISMATCH',decision=v['decision'],
    scientific_comparison_complete=False,files=entries,artifact_bytes_before_seal=size,external_supervision_bytes=external_size,
    recorded_payload_wall_seconds=wall,new_caps_pass=True,legacy_gaps_not_amended=True))
print('NOC4 available stop dossier sealed',len(entries),'entries',wall,'seconds',size,'bytes',flush=True)
