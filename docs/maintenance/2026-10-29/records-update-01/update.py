"""Owner-requested documentary update only; preserve earlier sealed records."""
import datetime as dt
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[3]
DAY=ROOT.parent
PRIOR=DAY/'continuation-closeout-01'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def save(name,value):
    with (ROOT/name).open('x',encoding='utf-8') as handle:
        json.dump(value,handle,indent=2,ensure_ascii=False,allow_nan=False)
        handle.write('\n')


def text(name,value):
    with (ROOT/name).open('x',encoding='utf-8',newline='\n') as handle:
        handle.write(value)


assert not (ROOT/'DELIVERY_SEAL.json').exists(), 'Preserve any completed update'
origin=dt.datetime(2026,10,29,1,53,10,tzinfo=dt.timezone.utc)
prior_seal=load(PRIOR/'DELIVERY_SEAL.json')
for entry in prior_seal['files']:
    path=PRIOR/entry['path']
    assert path.resolve().is_relative_to(PRIOR.resolve())
    assert path.stat().st_size==entry['bytes'] and sha(path)==entry['sha256'],str(path)
assert sha(DAY/'PHASE_RECORD.md')==prior_seal['day_phase_sha256']
before=(REPO/'AGENTS.md').read_bytes()
assert hashlib.sha256(before).hexdigest()==load(PRIOR/'AGENTS_UPDATE_PROOF.json')['new_sha256']
ignore_sha=sha(REPO/'.gitignore')
with (ROOT/'AGENTS.before.md').open('xb') as handle:
    handle.write(before)

save('AUTHORITY.json',{
    'owner_request':'做好记录和更新，下一轮对话见',
    'scope':'Documentary update and end-of-conversation handoff only',
    'new_scientific_continuation_authorized':False,
    'new_account_query_or_background_monitor_requested':False,
    'automatic_reset_resume':False,
    'scheduler_or_goal_status_action':False
})
state={
    'state':'COMPLETE_OWNER_REQUESTED_RECORDS_UPDATE_AWAIT_NEXT_CONVERSATION',
    'research':'UNRESOLVED','manuscript':'PAUSED',
    'ER1_camera5DoF':{'pairs':200,'outputs':30,'sequence00':30,'sequence08':0,'overall_refit_gain_established':False},
    'PR1_numerical_metric_camera':{
        'pairs':200,'outputs':17,'sequence00':17,'sequence08':0,'no_evidence':183,
        'R5deg_t2m_descriptive_bin_all200':17,
        'mean_rotation_deg_denominator17':0.6233317339196243,
        'mean_translation_m_denominator17':0.6641574928437658,
        'physical_scale_or_corrected_LiDAR_equivalence_authenticated':False
    },
    'MR1':{'historical_missing_proposal_IDs':64,'PnP_outputs_on_these_IDs':0,'new_output_IDs_beyond_ER1':0},
    'PT1':{
        'complete_slots':200,'available_initializers':17,'source_kernel_cases':68,
        'conditional_pretranslation_centering_erasure':True,
        'actual_full_pipeline_or_model_invariance_proved':False,'model_calls':0
    },
    'all_old_failures_caps_and_protocol_deviations_retained':True,
    'SR1':'Approximately1.98% fitting-only loss decrease; all four noise cells FAIL',
    'HFIT0':'INCOMPLETE; original2GiB artifact stop retained',
    'last_account_observation':'Historical2026-10-29 01:16:41UTC:1%/TRUE/reset1793254601; not refreshed here',
    'preceding_window_actual_quota_exhaustion':'UNOBSERVED',
    'new_experiment_model_training_runtime_install_or_WSL_start':False,
    'next_scientific_scope_implemented_frozen_queued_or_automatically_resumed':False,
    'pending_owned_numerical_worker':False,
    'next_action':'Read this handoff in the next conversation; scientific work requires a new explicit continuation and its own justified source/control/resource contract'
}
save('CURRENT_STATE.json',state)
text('CURRENT_HANDOFF.md','''# Owner-requested documentary handoff; wait for the next conversation

The owner said: "做好记录和更新，下一轮对话见". This records the completed round and does not renew experiments or until-quota work. Read CURRENT_STATE.json, REPORT.md and CHECKS.json here; then the immutable continuation-closeout-01 report and its linked stage receipts. No background worker, monitor, scheduler or automatic reset continuation is pending.

Retained outcomes: ER1 has30/200 camera5DoF outputs, all00. PR1 has17/200 numerical metric-camera outputs, all00;08 remains0/100. Its mean0.623331734-degree rotation and0.664157493-metre translation errors have denominator17, under supplied references. All17 satisfy the descriptive5degree/2metre bin, with complete denominator200. This authenticates neither physical scale nor corrected-LiDAR/RAP equivalence. MR1 finds zero PnP outputs among64 historical missing-proposal IDs and no additional output IDs beyond ER1. No RAP increment or new training is established.

PT1 binds the actual backend normalization source. Under fixed points/counts/features, independent centering algebraically removes pure pretranslation. Floating representation checks do not establish actual preprocessing, feature, RNG or full-model invariance. The optional sampler x_1 path is a distinct untested channel; it is not an admitted experiment. Existing common-raw/strong-geometry/equal-work ideas remain prospective, with no implementation/freeze/queued execution. Do not rerun closed stages or treat historical WSL package inventory as current runtime admission.

All original control/import/serialization failures, partial continuations, SD1 rank-control ordering deviation, old source/authentication gaps and resource caps remain. SR1 is fitting-only with all four noise cells failed; HFIT0 remains INCOMPLETE at its original2GiB stop. Research UNRESOLVED; manuscript PAUSED. No production/default/environment/install/WSL/Git-index/commit/push/outreach/scheduler/goal-status change. The latest saved account receipt is historical availability, not a newly queried quota or proof that the preceding window exhausted. The next conversation should begin with an explicit continuation if scientific work is requested.
''')
text('REPORT.md','''# 2026-10-29 records update complete

This update follows the owner's request to save records and meet in the next conversation. It adds a compact current handoff/state and a dated phase addendum, verifies the preceding closeout seal, and prepends an owner-close header to AGENTS.md while retaining its exact prior bytes. Earlier sealed files and the original day phase snapshot are unchanged.

The scientific conclusions remain unchanged:17/200 numerical metric-camera PnP outputs, all00; no08 output and no PnP output among64 historical missing-proposal IDs. Available-output mean errors0.623degree/0.664metre are supplied-reference measurements with denominator17. The normalization screen establishes conditional centering erasure, not full-model invariance. No RAP gain, new training, physical/generalization authentication or corrected-LiDAR equivalence is added.

No numerical experiment, solver, source acquisition, runtime installation, WSL start, fresh account probe, background monitor, Git index/commit/push, outreach, scheduler or goal-status action was performed. The current main HEAD/tracked dirty-path inspection is retained in CHECKS; other repository/remote observations remain historical. No automatic reset resume is authorized. All old failures/caps/deviations remain. Research UNRESOLVED; manuscript PAUSED. The next scientific task is not implemented, frozen or queued by this request.
''')
save('SOURCE_REFERENCES.json',{
    'preceding_closeout_delivery_seal':{'path':str(PRIOR/'DELIVERY_SEAL.json'),'sha256':sha(PRIOR/'DELIVERY_SEAL.json')},
    'preceding_closeout_entries_freshly_verified':len(prior_seal['files']),
    'prior_scientific_seal_audit_role':'The earlier closeout verified1311 scientific delivery entries; this update verifies its seal and does not claim another full scientific audit',
    'unchanged_day_phase_sha256':sha(DAY/'PHASE_RECORD.md')
})
header='''# October29 owner records update COMPLETE; next conversation only

Owner requests "做好记录和更新，下一轮对话见". Read docs/maintenance/2026-10-29/records-update-01/CURRENT_HANDOFF.md, CURRENT_STATE.json, REPORT.md and CHECKS.json. This is documentary closure, not renewed until-quota or scientific execution. The previous closeout and all scientific seals remain immutable; exact preceding AGENTS bytes are backed up here and retained verbatim below. No automatic reset resume, queued experiment, background monitor, scheduler or goal-status action.

Latest conclusions unchanged: PR1 numerical metric-camera PnP17/200 outputs, all00;08zero. Supplied-reference meanR0.623331734deg/t0.664157493m has denominator17; no physical scale/corrected-LiDAR/RAP equivalence. MR1 zero PnP outputs among64 old missing-proposal IDs; no new output IDs beyond ER1. PT1 confirms pure pretranslation is independently recentered only under fixed-point/count/feature conditions; no actual pipeline/model invariance or model gain. No new RAP training. All old failures, source gaps, SD1 ordering deviation, SR1 four-noise FAIL and HFIT0 INCOMPLETE/original2GiB stop remain. Research UNRESOLVED; manuscript PAUSED.

No new numerical/model/runtime/install/WSL/Git-index/commit/push/outreach action. Historical account1%/TRUE/reset1793254601 at01:16:41UTC was not refreshed; preceding actual exhaustion remains UNOBSERVED. Next scientific work requires an explicit new continuation and its own justified complete controls/source/resources; do not run old closed hosts or treat future comparison ideas as admitted payloads. Start the next conversation from this handoff.

---

'''
(REPO/'AGENTS.md').write_bytes(header.encode('utf-8')+before)
assert (REPO/'AGENTS.md').read_bytes().endswith(before)
assert sha(REPO/'.gitignore')==ignore_sha
save('AGENTS_UPDATE_PROOF.json',{
    'previous_bytes':len(before),'previous_sha256':hashlib.sha256(before).hexdigest(),
    'prior_exact_suffix_retained':True,'new_sha256':sha(REPO/'AGENTS.md')
})
phase=DAY/'PHASE_RECORD_RECORDS_UPDATE_01.md'
with phase.open('x',encoding='utf-8') as handle:
    handle.write('''# 2026-10-29 owner-requested records update

The owner requested records/update and ended this conversation. records-update-01 provides the latest compact state/handoff and exact AGENTS backup. The preceding closeout seal was freshly verified; old scientific files and PHASE_RECORD.md are unchanged. No new scientific/solver/model/runtime/installation/WSL/account probe/Git write/outreach/scheduler/goal-status action. No pending worker, automatic reset continuation or queued experiment. PR1/MR1/PT1 conclusions, all old failures/caps/source limitations and SD1 deviation remain; research UNRESOLVED/manuscript PAUSED. Await the next conversation's explicit continuation.
''')
now=dt.datetime.now(dt.timezone.utc)
seconds=(now-origin).total_seconds()
assert seconds<600
save('CHECKS.json',{
    'utc':now.isoformat(),'Asia_Shanghai':now.astimezone(dt.timezone(dt.timedelta(hours=8))).isoformat(),
    'status':'COMPLETE_DOCUMENTARY_OWNER_RECORDS_UPDATE',
    'inclusive_seconds':seconds,'cap_seconds':600,'cap_pass':True,
    'freshly_verified_prior_closeout_entries':len(prior_seal['files']),
    'all_prior_closeout_hashes_lengths_match':True,'old_sealed_files_modified':False,
    'old_day_phase_unchanged':sha(DAY/'PHASE_RECORD.md')==prior_seal['day_phase_sha256'],
    'new_phase_addendum_sha256':sha(phase),'prior_AGENTS_exact_suffix':True,
    'main_HEAD_read':'4055d929c594b0033aafc6eed339c910369eef55',
    'main_tracked_dirty_paths_read':['.gitignore','AGENTS.md'],'.gitignore_unchanged_by_update':True,
    'SLAM_and_remote_freshly_rechecked':False,
    'new_scientific_runtime_WSL_account_or_scheduler_action':False,
    'pending_owned_numerical_worker':False,'new_scientific_authorization':False
})
files=[{'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(ROOT.rglob('*')) if p.is_file()]
save('DELIVERY_SEAL.json',{'utc':dt.datetime.now(dt.timezone.utc).isoformat(),'files':files,'phase_addendum_sha256':sha(phase)})
for entry in load(ROOT/'DELIVERY_SEAL.json')['files']:
    p=ROOT/entry['path'];assert p.stat().st_size==entry['bytes'] and sha(p)==entry['sha256']
print('Records update complete; verified',len(prior_seal['files']),'prior closeout entries; sealed',len(files),'new documentary files')
