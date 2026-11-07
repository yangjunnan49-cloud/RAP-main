"""Documentary current-window boundary closeout; no numerical payload replay."""
import datetime as dt
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[3];OLD=REPO/'docs/maintenance/2026-10-28'


def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))


def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1024**2),b''):h.update(block)
    return h.hexdigest()


def save(name,obj):
    with (ROOT/name).open('x',encoding='utf-8') as f:json.dump(obj,f,indent=2);f.write('\n')


def text(name,value):
    with (ROOT/name).open('x',encoding='utf-8',newline='\n') as f:f.write(value)


now=dt.datetime.now(dt.timezone.utc)
scopes=['visual-baseline-execution-01','visual-control-diagnostic-01','visual-essential-refinement-01',
        'visual-baseline-reachability-01','source-depth-adequacy-01','ordinary-pnp-baseline-01',
        'camera-metric-reachability-01','initializer-conditioning-audit-01']
verified=[];entries=0
for name in scopes:
    directory=OLD/name;seal=load(directory/'DELIVERY_SEAL.json')
    for e in seal['files']:
        p=directory/e['path'];assert p.resolve().is_relative_to(directory.resolve())
        assert p.stat().st_size==e['bytes'] and sha(p)==e['sha256'],str(p)
    entries+=len(seal['files']);verified.append({'scope':name,'entries':len(seal['files']),'seal_sha256':sha(directory/'DELIVERY_SEAL.json')})
assert load(OLD/'ordinary-pnp-baseline-01/STATUS.json')['pose_outputs']==17
assert load(OLD/'camera-metric-reachability-01/CLOSE_CHECKS.json')['PnP_outputs_in_missing_IDs']==0
assert load(OLD/'initializer-conditioning-audit-01/features/RESULT.json')['model_or_registration_or_reference_calls']==0
save('WINDOW_BOUNDARY.json',{'observed_following_clock_utc':'2026-10-29 01:16:41 UTC','Asia_Shanghai':'2026-10-29 09:16:41',
    'old_window':{'reset_identity':1793208661,'last_actual_used_percent':54,'last_actual_ordinary_usage_allowed':True,
                  'last_following_clock_utc':'2026-10-28 13:25:40 UTC','actual_exhaustion_observed':False},
    'new_observation':{'reset_identity':1793254601,'used_percent':1,'ordinary_usage_allowed':True},
    'exact_reset_transition_or_cause':'UNOBSERVED','latest_message_only_environment_date_change_not_new_explicit_scientific_renewal':True,
    'numerical_work_resumed_after_this_reset':False,'automatic_reset_resume':False,
    'state':'CURRENT_AUTHORIZED_WINDOW_ENDED_BY_OBSERVED_RESET_CHANGE_NOT_CLAIMED_EXHAUSTION'})
save('CURRENT_STATE.json',{'utc':now.isoformat(),'research':'UNRESOLVED','manuscript':'PAUSED',
    'ER1':{'images':273,'pairs':200,'camera5DoF_outputs':30,'00_outputs':30,'08_outputs':0,'R5_direction15_all200':23,'refit_overall_gain':False},
    'SD1':{'pairs':200,'at_least8_depth_hypotheses':24,'00':22,'08':2,'actual_correspondence_authenticated':False,
           'rank_controls_before_real_points':'NOT_MET','rank_controls_later_audit':'4_PASS','old_failed_control_exit':'NOT_RECORDED'},
    'PR1':{'pairs':200,'numerical_metric_camera_outputs':17,'00_outputs':17,'08_outputs':0,'no_evidence':183,
           'R5_t2_all200':17,'mean_rotation_deg_available17':0.6233317339196243,'mean_translation_m_available17':0.6641574928437658,
           'controls':23,'independent_Decimal60_reference_solves':200,'independent_scalar_projection_checks':1129,
           'physical_scale_or_corrected_LiDAR_equivalence_authenticated':False},
    'MR1':{'old_missing_proposal_IDs':64,'PnP_outputs_on_those_IDs':0,'old_correct_accepted_IDs_in_PnP_outputs':15,
           'old_correct_rejected_IDs_in_PnP_outputs':2,'additional_output_IDs_beyond_ER1':0,'no_operational_fusion_or_absence_veto':True},
    'PT1':{'actual_initializers':17,'all_pair_slots':200,'source_kernel_cases':68,'raw_point_occurrences':4059861,'Decimal60_scalar_checks':1632,
           'float64_shift_condition_byte_equal':33,'float64_shift_cases':34,'max_float64_shift_condition_delta':7.105427357601002e-15,
           'float32_shift_condition_byte_equal':0,'float32_shift_cases':34,'max_float32_shift_condition_delta':5.960464477539063e-8,
           'conditional_centering_erasure_not_full_pipeline_or_model_invariance':True,'model_calls':0},
    'new_RAP_training':False,'old_SR1_four_noise_failures_and_HFIT0_2GiB_stop_unchanged':True,
    'new_WSLEncoder_or_package_or_environment_change':False,'new_WSL_start':False,
    'next_strong_geometry_runtime_or_model_payload_frozen_or_launched':False,'pending_owned_worker':False,
    'new_scientific_scope_after_reset_admitted':False,'scheduler_or_goal_status_changed':False})
text('REPORT.md','''# Continuation closeout: actual ordinary-camera results, no observed quota exhaustion

The current authorized account window is now over by an observed reset-identity change, not an observed quota denial. At2026-10-29 01:16:41UTC (09:16:41Asia/Shanghai), the new receipt is1%/ordinaryTRUE/reset1793254601. The preceding window's last actual receipt was54%/TRUE/reset1793208661 at13:25:40UTC onOctober28. Its actual exhaustion and exact reset-transition cause/time are UNOBSERVED. The latest message changed client date; it did not explicitly renew scientific work after this reset. Per AGENTS.md's no-automatic-reset-resume instruction, no new experiment is started. This is documentary closure of already-authorized completed work, not a goal-status or scheduler action.

## Results worth retaining

| Complete-cohort stage | Result | Limit |
|---|---|---|
| ER1 ordinary camera5DoF |30/200 outputs,all00;23/200 within5deg/15deg |08 has0/100; refit worsens means and adds no bin successes |
| SD1 source depth |24/200 sets have>=8 unique hypotheses,22/2 bysequence |Proximity hypotheses,not authenticated correspondences; prospective rank-control omission retained |
| PR1 ordinary source-depth PnP |17/200 numerical metric-camera poses,all00;all17 within5deg/2m |183noevidence;meanR0.623deg/t0.664m denominator17;no physical scale or corrected-LiDAR/RAP equivalence |
| MR1 complete category join |15PnP outputs were old correct-accepted IDs,two correct-rejected |0PnP outputs among64 old missing-correct-proposal IDs;0new output IDs beyondER1 |
| PT1 actual-backend source screen |68cases/17initializers,1632Decimal checks |Pure pretranslation is independently recentered in exact arithmetic; floating cases differ,not a full-model/pipeline invariance proof |

All predictions were sealed before their separate supplied-reference evaluations. PR1 passed23 prospective controls,200 independent Decimal60 relative transforms and1129 scalar projection checks. Its nativeEPNP flag is1 in this installedOpenCV5 build, confirmed from actual API. PR1 four children all passed/exited/reaped,3.2537946s host walls/max47,562,752-byte lifetime peak; no retry. ER1 original raw-outlier control failure, two lazy-import failures/seven-row continuation, SD1 NumPy-bool/truncatedJSON/missing original final exit record and post-primary rank controls remain visible. No old failure, cap or negative conclusion is erased.

PT1 is tied to the exact current RAPBackend._normalize_parts AST and public raw subsets. At fixed point/count/features,cond_i=(p_i-c_i)/s. Independent pretranslation shifts c_i but is algebraically removed.33/34float64-shift cases are byte-equal;maximumdifference7.105e-15.0/34float32-shift cases are byte-equal;maximumdifference5.960e-8. These satisfy a representation budget but cannot prove two neural trajectories equal. Actual voxel/outlier/feature/RNG behavior was not run. The existing recovery composition conditionally cancels pretranslation as well. This blocks a naive claim that moving a cloud alone preserves a new metric-translation conditioning channel.

Source inspection finds a distinct optional sampler x_1 channel; it is untested as a pose prior. _prepare_data consumes timestep RNG even in this inference path. Any future common-random model comparison must handle that explicitly and retain public-only inputs; no source comment authenticates canonical training/checkpoint/physical semantics. No model, Torch/GPU forward, backward or new RAP training was executed in this continuation. All old SR1/HFIT0/native/joint/equivalence/provenance failures and caps remain. ResearchUNRESOLVED/manuscriptPAUSED.

## Reviewable next step, not queued execution

Current images provide no new metric-pose coverage of the64 missing-proposal IDs. There is no evidence here for automatic training or a useful new hard-loop claim. Before any model study, define a distinct input-information mechanism and a common-raw point-cloud comparison with strong geometry/equal-work controls. Raw camera/LiDAR conversion can use the declared supplied affine actionTr_j^-1*Tcam*Tr_i; the old point-dependent0.205-degree correction has no global rigid inverse/conjugation. Windows metadata finds noSciPy/Open3D. Existing saved WSL inventory namesOpen3D0.19.0/SciPy1.15.2/NumPy1.26.4, but those are historical metadata,not current API/runtime admission. No WSL query/start, runtime import, ICP implementation/freeze, new model scope or installation was performed for that possible follow-up. Do not run old closed hosts or use a weak replacement to fill a dependency.

The oldNJE0 strong comparison's FGR/GICP parameters were read only as existing-source context. That old4group/29view/32measurement screen remains closed/failed; no group/seed/point/step rescue or old cap reset. A prospective new full200 raw-frame geometry/image-initializer comparison,if justified and explicitly renewed,must declare its separate task/inputs, resource limits, optional WSL lifecycle and reference separation before execution. It is not admitted by this report.

Both repository HEAD/dirty observations were rechecked earlier in this window (main4055d929...,SLAM6d3f2d2...,tracked2/9dirty);remote synchronization remains unchecked. Only maintenance helpers/documents and additive AGENTS were changed. No production/default/Git index/commit/push/install/WSL/source-environment/outreach/scheduler/goal-status action. All finite owned workers have completed receipts; no pending background numerical job or automatic reset continuation.
''')
text('CURRENT_HANDOFF.md','''# Window ended by reset; no automatic scientific continuation

Read CURRENT_STATE.json,WINDOW_BOUNDARY.json,REPORT.md and CHECKS.json here. PR1 complete200 outputs/evaluation/audit:17numerical metric-camera poses/all00,none08;no added coverage of64 old missing-proposal IDs. PT1 real-backend normalization screen complete68cases:plain pretranslation is analytically recentered under fixed-point conditions,not actual model/pipeline invariance. No model/training/WSL/install. All old failures/caps/source limitations remain; researchUNRESOLVED/manuscriptPAUSED.

Current account changed to1%/TRUE/reset1793254601 after priorlast54%/TRUE/reset1793208661. PrioractualexhaustionUNOBSERVED. No new explicit scientific renewal after this reset; stop at documentary handoff. No pending worker,automation or goal-status action. Do not rerun closed hosts. A future direct renewal may prepare a distinct justified full-cohort common-raw geometry/public-initializer comparison under its own controls/source/resources,not automatically run a model or old failed family.
''')
prior=(REPO/'AGENTS.md').read_bytes()
with (ROOT/'AGENTS.before.md').open('xb') as f:f.write(prior)
header='''# October29 observed account-window change; ordinary camera/depth work complete

Read docs/maintenance/2026-10-29/continuation-closeout-01/CURRENT_HANDOFF.md, CURRENT_STATE.json, WINDOW_BOUNDARY.json, REPORT.md and CHECKS.json. Current1%/ordinaryTRUE/reset1793254601 followed01:16:41UTC onOct29; precedinglast54%/TRUE/reset1793208661 followedOct28 13:25:40UTC. Oldactualquotaexhaustion and exactresettransition/cause UNOBSERVED. Latestclientdate change is not an explicit new scientific renewal. No automatic reset resume: this is documentary closure only, no newly admitted numerical/runtime/model payload.

PR1 ordinaryPnP COMPLETEall200source-depth sets,23prospectivecontrols/predictionseal-before-reference/independentaudit:17numerical metric-camera poses all00,08zero;183noevidence. All17 within frozenR5deg/t2m descriptivebin,denominator200;meanR0.623331734deg/t0.664157493m denominator17. This new supplied-unit metric-camera quantity does not retroactively give ER1 scale or establishphysicalscale/correctedLiDARequivalence/RAPgain.200Decimal60reference matrices/1129scalarprojection checksPASS. Fourchildrenexit0/reaped,3.2537946s total/max47562752bytes. Sources/resources/deliverysealed in ordinary-pnp-baseline-01.

MR1 complete200-ID join:17PnPposes=15oldNcorrectaccepted+2correctrejected,nonein64oldmissing-correct-proposal IDs,noneinselectionmiss;all17alreadyER1outputIDs.14PnPR5/d15bins overlap13ofER1's23plusoneoldcorrectrejected ID;posthocbinunionisnotreference-freefusion. MissingPnPwouldalsoaffect27/40oldcorrectaccepted, noabsenceveto. camera-metric-reachability-01 closed/sealed. No learning-specific hard-loop contribution established.

PT1 source-bound actualRAPBackend._normalize_parts screen COMPLETE:all200slots/17availablecamera translations/68fixed-point cases,4059861rawpointoccurrences/1632Decimal60coords,nomodel/GT/registration. Independentcentering algebraicallyremoves purepretranslation atfixedpoint/count/features;33/34float64 casesbyteequal,maxdifference7.105e-15;0/34float32 casesbyteequal,maxdifference5.960e-8. Representationcheck,notfullpreprocessing/model/RNGinvariance orcanonicalnormalizationauthentication. Realbackendregister(a,b)mapsb->a;source_i->target_j requires[target_j,source_i]. Native sampleroptionalx_1 isadifferentuntestedchannel; _prepare_dataconsumestimestepRNG. No automaticmodel/training fromthis sourceaudit. Initializer-conditioning-audit-01 closed/sealed;oldCN1stageunchanged.

ER1/VR1/SD1 conclusions and all failedcontrol/import/serialization/partial-continuation/SD1rank-ordering deviations remain explicit. OriginalVB1outlierFAIL,SR1~1.98%fitonly/all4noiseFAIL,HFIT0INCOMPLETE/old2GiBstop,oldnative/joint/equivalence/provenance failures/capsunchanged. ResearchUNRESOLVED/manuscriptPAUSED.

Possible next step requires directrenewal and a justified common-raw/public-prior/strong-geometry/equal-work protocol;noICP/modelscopeisimplemented/frozen/queued. WindowsexistingSciPy/Open3Dabsent;historicalWSLOpen3D0.19.0/SciPy1.15.2/NumPy1.26.4metadataisnotcurrentAPIadmission. OldNJE0FGR/GICPsourcewasreadonly;donotrelabel/retryit. NoWSLquery/start/installation,production/default/Gitwrites/outreach/scheduler/goal-statuschange. PriorHEAD4055d929/6d3f2d2+tracked2/9dirtyobservationsretained,remoteunchecked. No pendingownednumericalworker. ExactprecedingAGENTSbytesbackeduphereandretainedverbatimbelow.

---

'''
(REPO/'AGENTS.md').write_bytes(header.encode('utf-8')+prior)
save('AGENTS_UPDATE_PROOF.json',{'utc':now.isoformat(),'previous_bytes':len(prior),'previous_sha256':hashlib.sha256(prior).hexdigest(),
    'previous_exact_suffix':(REPO/'AGENTS.md').read_bytes().endswith(prior),'new_sha256':sha(REPO/'AGENTS.md')})
save('CHECKS.json',{'utc':now.isoformat(),'status':'COMPLETE_DOCUMENTARY_WINDOW_CLOSEOUT',
    'verified_delivery_seals':verified,'verified_entries':entries,'all_hashes_and_lengths_match':True,
    'old_sealed_files_modified':False,'prior_AGENTS_exact_suffix':True,'new_numerical_payload_or_WSL_start':False,
    'old_quota_exhaustion_claimed':False,'automatic_reset_resume':False,'pending_worker':False})
phase=ROOT.parent/'PHASE_RECORD.md'
assert not phase.exists()
phase.write_text('''# 2026-10-29 documentary closeout after observed account-window change

Read continuation-closeout-01. Priorexplicitrenewal producedPR1 complete200case ordinaryPnP (17camera-metric poses/all00,none08),MR1 completecategoryjoin (noneof64oldmissing-proposalIDscovered),PT1 actualbackendnormalization source/metamorphic screen (purepretranslation recentered underfixed-pointconditions,notfullmodelinvariance). Allfinitechildrencompleted/sealedbeforethiscloseout. No model/training/WSL/install/newstronggeometry experiment.

Actualnewaccount1%/TRUE/reset1793254601 following01:16:41UTC;oldlast54%/TRUE/reset1793208661 hasnoobservedexhaustion. Clientdateupdateisnotnewscientificrenewal;noautomaticresetresume. Thisisnewdateddocumentaryadditive,notbackdatedprimaryclosure. ResearchUNRESOLVED/manuscriptPAUSED;alloldfailures/caps/deviationspreserved. ExactpriorAGENTSbytesretained. No scheduler/goal-status/Gitwrite/outreachaction orpendingworker.
''',encoding='utf-8')
files=[{'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(ROOT.rglob('*')) if p.is_file()]
save('DELIVERY_SEAL.json',{'utc':dt.datetime.now(dt.timezone.utc).isoformat(),'files':files,'day_phase_sha256':sha(phase)})
print('Documentary closeout complete; verified',entries,'prior sealed entries; no scientific resume')
