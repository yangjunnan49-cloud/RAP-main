"""Dated documentary additive to already-sealed SD1 primary outputs."""
import datetime as dt
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent;DAY=ROOT.parent;REPO=ROOT.parents[3];SD=DAY/'source-depth-adequacy-01'


def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def save(p,obj):
    with p.open('x',encoding='utf-8') as f:json.dump(obj,f,indent=2);f.write('\n')


def text(p,value):
    with p.open('x',encoding='utf-8',newline='\n') as f:f.write(value)


now=dt.datetime.now(dt.timezone.utc)
for manifest in ('SOURCE_FREEZE.json','BOOL_CORRECTION_FREEZE.json','DATA_ROUTING_FREEZE.json','AUDIT_FREEZE.json'):
    for e in load(SD/manifest)['files']:
        assert sha(SD/e['path'])==e['sha256']
for stage in ('controls_runtime02','features','audit'):
    for e in load(SD/stage/'SEAL.json')['files']:
        assert sha(SD/stage/e['path'])==e['sha256']
    assert load(SD/stage/'HOST_EXIT.json')['passed']
result=load(SD/'features/RESULT.json');audit=load(SD/'audit/RESULT.json');summary=load(SD/'features/SUMMARY.json')
assert result['complete_pairs']==200 and result['pose_solver_calls']==0 and audit['unique_raw_point_identity_checks']==1636
primary_end=dt.datetime.fromisoformat(load(SD/'audit/SEAL.json')['sealed_utc'])
origin=dt.datetime(2026,10,28,7,27,45,tzinfo=dt.timezone.utc)
primary_seconds=(primary_end-origin).total_seconds();assert primary_seconds<1800
receipts=[{'stage':s,**load(SD/s/'HOST_EXIT.json')} for s in ('controls_runtime02','features','audit')]
assert all(r['no_live_owned_process'] for r in receipts)
assert load(SD/'ORIGINAL_CONTROL_PROCESS_ADDITIVE.json')['scoped_pid_absent']
size=sum(p.stat().st_size for p in SD.rglob('*') if p.is_file());assert size<16777216
save(SD/'CLOSE_CHECKS_ADDITIVE.json',{'utc':now.isoformat(),'primary_end_utc':primary_end.isoformat(),
    'primary_inclusive_seconds_to_final_audit_seal':primary_seconds,'primary_cap_seconds':1800,'primary_cap_pass':True,
    'later_documentary_additive_separate_from_primary':True,'successful_receipts':receipts,
    'original_control_child_exit_code':'NOT_RECORDED','original_control_final_host_receipt':'MISSING_JSON_PARSE_FAILURE',
    'original_control_outer_wall_seconds_charged':1.1237349,'blocked_data_precheck_outer_seconds':0.3570315,
    'current_dossier_bytes':size,'dossier_cap_bytes':16777216,'scoped_original_PID_absent_at_later_check':True,
    'protocol_deviation':'Required rank fixtures omitted before primary; added4 fixtures only in post-primary audit',
    'PnP_or_new_pose_calls':0,'reference_pose_reads':0})
text(SD/'REPORT.md',f'''# SD1 source-depth adequacy:24/200 hypothesis sets, no metric-pose result

The complete200-pair source-depth diagnostic is finished. With the single pre-frozen2-pixel source projection rule,184/200 pairs have at least one deduplicated source-point hypothesis.24/200 have at least8 distinct source-point hypotheses:00=22/100,08=2/100. All24 have recorded centered3D rank3; none ofthe>=8 sets has rank2. These are source-side proximity/depth hypotheses, not authenticated image/point identities, target correspondences, PnP solutions, pose accuracy, metric registration recovery or a RAP gain. Insufficient counts cannot establish image-only impossibility or a registration veto.

All200 original pair IDs and source match sets are retained. Every actual raw scan occurrence is checked against the existing source-sealed SHA before decode. Source LiDAR -> camera uses the unchanged suppliedTr and P0, with no0.205-degree correction, deskew or raw/corrected rigid-equivalence assumption.200 raw-scan occurrence reads were performed; no reference poses, PnP, new image features or model/training call. Existing physical calibration/timing/extraction/cohort limitations remain.

The grid assignment was independently checked by dense search on1322 deterministic source queries. The saved-output audit verified1636 unique original raw-point identities,4908 Decimal60 affine coordinates and1636 Decimal60 projected radius distances. Maximum affine difference is{audit['max_affine_absolute_difference']:.17g}. These checks verify implementation/source consistency, not physical correspondence truth.

## Retained failures and ordering deviation

The original synthetic conditions reached assert(all) but final JSON serialization failed on NumPy bool. RESULT.json is deliberately left truncated; Python stderr/OWNED_PROCESS and preflight are retained. Host WaitForExit ran before ConvertFrom-Json failed; original child exit/final HOST_EXIT were not recorded, so those remain UNKNOWN. A later scoped-PID check observes that exact PID absent, without any broad process action. The subsequent feature-host invocation was stopped by the missing preceding seal before any worker launch. The correction converts result bool values only, keeps exact conditions/math and routes to a new directory, charging original outer-host1.1237349 seconds to the original60-second control cap. The successful controls report11 conditions. A prospective source-pointer adjustment routes the data worker to that successful seal; original source files remain unchanged. No actual point-worker retry occurred.

Code review found that the protocol's promised rank fixtures were omitted before real points. That prospective requirement is NOT_MET. Four rank0/1/2/3 fixtures passed in the later source audit; this does not retroactively repair ordering. The >=8 association counts are independent of rank gating, and no subsequent PnP admission is inferred. Keep this explicit deviation in future decisions.

Primary final audit seal is{primary_end.isoformat()}, {primary_seconds:.7f}/1800 seconds from the original07:27:45UTC origin. All three successful children exited/reaped; failed-control final peak/exit are not invented. Data worker6.3623985/300 seconds, successful peak63053824bytes, new dossier{size}/16777216 bytes before small documentary closure. Source/control/primary seals remain original. This report is a later dated documentary additive at{now.isoformat()}, following a direct new human continuation and a new account window; it is not backdated into the earlier primary scope or used to replenish it.

Next potentially useful task is an independently frozen full200-case ordinary source-camera3D -> target-camera2D PnP baseline, retaining176 below-eight cases and all correspondence uncertainties. It needs complete API/solver/frame/metric-scale/degeneracy/cold-I/O controls, its own finite resources and all predictions sealed before evaluation. Only12% of pairs meet even the hypothesis-count description; no broad efficacy or novel learning case is established. No new RAP training, physical/generalization or corrected-LiDAR equivalence claim. Research UNRESOLVED/manuscript PAUSED; every prior failure/cap remains.
''')
save(SD/'STATUS.json',{'state':'COMPLETE_SOURCE_ASSOCIATION_AND_AUDIT_WITH_RETAINED_ORDERING_DEVIATION',
    'pairs':200,'pairs_at_least8':24,'sequence00':22,'sequence08':2,'pose_solver_calls':0,
    'rank_control_before_real_points':'NOT_MET','rank_control_post_primary_audit':'4_PASS',
    'research':'UNRESOLVED','manuscript':'PAUSED','next_PnP_payload_admitted':False})
files=[{'path':p.relative_to(SD).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(SD.rglob('*')) if p.is_file()]
save(SD/'DELIVERY_SEAL.json',{'utc':now.isoformat(),'files':files,'role':'Later documentary delivery; original dated primary seals distinguished'})
prior=(REPO/'AGENTS.md').read_bytes()
with (ROOT/'AGENTS.before.md').open('xb') as f:f.write(prior)
header='''# October28 explicit new-window renewal: measured visual/depth baselines complete

Owner again explicitly requests continuation until5h quota exhaustion. New actual0%/ordinaryTRUE/reset1793208661 followed12:31:02UTC; old last85%/TRUE/reset1793187718 has no observed exhaustion. Changed reset identity now observed, exact transition/cause UNKNOWN. This human renewal is not automatic reset resume. Read project-continuation-03/AUTHORITY.md and source-depth-adequacy-01/REPORT.md, STATUS.json, CLOSE_CHECKS_ADDITIVE.json and DELIVERY_SEAL.json, then preceding ER1/VR1 reports. All earlier scientific children had already exited; new documentation is later additive, not backdated primary closure.

SD1 completeall200 source-depth association/no pose solver:184 have>=1 source-side proximity hypothesis,24 have>=8unique points (00=22,08=2), all24 recordedrank3. This is a fixed2px/z-buffer heuristic, not verified image-point/target correspondence, metric pose or RAP benefit;176 below8 retained.1322 independent dense-query checks;1636 original raw IDs,4908Decimal60 affine/1636radius checks PASS,max affine delta1.8149312321738827e-14. Unchanged suppliedTr/P0/raw coordinates/no0.205 correction. No physical source/calibration/timing/cohort authentication added. No pose-reference/PnP/model/training calls.

SD1 original NumPy-bool output failure/truncatedRESULT retained; host failed parsing afterWaitForExit, original child exit/finalreceipt UNKNOWN. Later exactPID absent. Corrected11conditions preservemath; originalouter1.1237349s charged to60s; attempted featurehost stopped beforeworker due missing priorseal, then prospective successful-control pointer correction. Sole real-data worker6.3623985/300s,peak63053824bytes. Required rankfixtures were OMITTED before realpoints;4passed only in later audit, so original ordering requirement NOT_MET. This deviation remains, not retroactively repaired; no PnP admission fromcounts. Originalprimary finished07:35:22UTC within1800s; later documentary seal is separate. No workers pending.

ER1/VR1 remain:273images/200pairs/30camera5DoF outputs all00,170noevidence;08zero.5/15 bin23/200;refitmeansworse/binsunchanged. OldNmissing-proposal64 IDs intersectone strict-bin visualoutput;21/40old correctaccepted lackvisualpose, noabsenceveto. OriginalVB1outlierFAIL and all cold-import/partial-continuation/caps retained. Next possible distinct ordinary cameraPnP baseline must have its own complete implementation, API/frame/scale/degeneracy/cold controls, input/resource freeze and prediction-before-reference evaluation. It is not executed/queued by this header.

No new RAP training/metric-camera pose/full corrected-LiDAR equivalence/physical/generalization/RAP increment claim. SR1~1.98% fitting-only/all4noiseFAIL, HFIT0INCOMPLETE/old2GiBstop and all old failures/caps remain. ResearchUNRESOLVED/manuscriptPAUSED. No install/WSL startup/default/production/Git writes/outreach/scheduler/goal-status changes; priorHEAD2/9dirty observations historical, remote unchecked. Exact preceding AGENTS bytes backed up in project-continuation-03 and retained verbatim below.

---

'''
(REPO/'AGENTS.md').write_bytes(header.encode()+prior)
save(ROOT/'AGENTS_UPDATE_PROOF.json',{'utc':now.isoformat(),'previous_bytes':len(prior),'previous_sha256':hashlib.sha256(prior).hexdigest(),
    'previous_exact_suffix':(REPO/'AGENTS.md').read_bytes().endswith(prior),'new_sha256':sha(REPO/'AGENTS.md')})
text(DAY/'PHASE_RECORD_CONTINUATION_03.md','''# Explicit new-window human continuation,2026-10-28

Fresh0%/TRUE/reset1793208661 following12:31:02UTC plus direct human renewal authorizes current-window work. Old last85%/TRUE has no observed exhaustion; no inferred boundary/cause or automatic reset resume. SD1 prior primary complete before renewal:all200 source-depth adequacy rows,24>=8hypotheses (22/2), no PnP or new pose. Independent raw identity/Decimal projection audit complete; NumPy-bool failure/missing original exit and omitted prospective rank control remain explicit. Later documentary closure separate from earlier primary scope/seals. ER1/VR1 limited5DoF conclusions and all old failures/caps remain. ResearchUNRESOLVED/manuscriptPAUSED.

Prepare a separate complete ordinary cameraPnP implementation and controls/freeze next; no automatic numerical payload or training. Actual later current-scope receipts govern. No background worker, install/WSL/default/production/Git writes/outreach/scheduler/goal-status action.
''')
print('SD1 sealed with limitations; prior AGENTS retained; new human window recorded')
