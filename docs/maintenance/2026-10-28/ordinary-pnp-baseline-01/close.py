"""Finite PR1 documentary closure, no numerical replay."""
import datetime as dt
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent


def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def save(name,obj):
    with (ROOT/name).open('x',encoding='utf-8') as f:json.dump(obj,f,indent=2);f.write('\n')


for e in load(ROOT/'SOURCE_FREEZE.json')['files']:
    assert (ROOT/e['path']).stat().st_size==e['bytes'] and sha(ROOT/e['path'])==e['sha256']
receipts=[]
for stage in ('controls','predict','evaluate','audit'):
    for e in load(ROOT/stage/'SEAL.json')['files']:
        assert (ROOT/stage/e['path']).stat().st_size==e['bytes'] and sha(ROOT/stage/e['path'])==e['sha256']
    r=load(ROOT/stage/'HOST_EXIT.json');assert r['passed'] and r['no_live_owned_process'];receipts.append({'stage':stage,**r})
now=dt.datetime.now(dt.timezone.utc);origin=dt.datetime(2026,10,28,12,37,44,tzinfo=dt.timezone.utc)
inclusive=(now-origin).total_seconds();assert inclusive<3600
size=sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file());assert size<16777216
groups=load(ROOT/'evaluate/SUMMARY.json')['groups'];overall=groups[0];audit=load(ROOT/'audit/RESULT.json')
assert overall['pairs']==200 and overall['pose_outputs']==17 and overall['bin_counts']['R5_t2']==17
save('RESOURCE_AUDIT.json',{'utc':now.isoformat(),'origin_utc':origin.isoformat(),'inclusive_seconds':inclusive,'whole_scope_cap_seconds':3600,
    'cap_pass':True,'stage_receipts':receipts,'sum_child_host_wall_seconds':sum(r['elapsed_seconds'] for r in receipts),
    'max_child_lifetime_peak_bytes':max(r['child_lifetime_peak_bytes'] for r in receipts),'dossier_bytes_before_closure':size,
    'dossier_cap_bytes':16777216,'all_owned_children_reaped':True,'no_other_process_or_WSL_state_claim':True})
report=f'''# PR1 ordinary source-depth PnP:17/200 numerical camera poses

Complete200-pair inference/evaluation/audit is finished.17/200 outputs (all00 original positives),183 explicit no-evidence.00=17/100;08=0/100. All50 confusers remain without output.176 cases have fewer than8 unique input depth hypotheses; five further00 cases have insufficient independently verified native-inlier support, and both08>=8-hypothesis cases fail native PnP. All cases/denominators remain.

| Quantity | Complete result |
|---|---:|
| Pose coverage |17/200 (8.5%)|
| Rotation mean /median,17 outputs |{overall['rotation_mean_deg']:.9f} /{overall['rotation_median_deg']:.9f} degrees|
| Translation mean /median,17 outputs |{overall['translation_mean_m']:.9f} /{overall['translation_median_m']:.9f} supplied metres|
| Direction mean /median,17 outputs |{overall['direction_mean_deg']:.9f} /{overall['direction_median_deg']:.9f} degrees|
| R<=5deg andt_error<=2m,all200 denominator |17/200|
| R<=10deg andt_error<=5m,all200 denominator |17/200|
| R<=5deg anddirection<=15deg,all200 |14/200|
| R<=10deg anddirection<=30deg,all200 |15/200|

These are supplied-reference exposed-cohort engineering measurements. The17 output errors do not describe the183 missing outputs, and no universal accuracy/safety guarantee follows from all17 satisfying the descriptive bin. Full200 rows and15 complete summary groups are under evaluate. Do not promote the per-output error means into complete-cohort or population accuracy.

## New quantity and limits

Unlike ER1's scale-free camera5DoF, PR1 uses source3D depth hypotheses to estimate camera_i->camera_j rotation and translation in supplied raw-LiDAR coordinate units. This is numerical metric-camera6DoF estimation, not physical-scale authentication, corrected-LiDAR rigid equivalence, RAP/native-N metric comparability or a system/manuscript contribution. SD1 assignments remain fixed2px nearest-projection/z-buffer hypotheses, not verified texture/point/target identities; timing/occlusion/extraction/calibration/cohort independence is not added. Original raw points/suppliedTr/archiveP0 are unchanged. Old point-dependent0.205-degree correction has no assumed constant conjugation.

## Prospective implementation and controls

All source/input/fixture/parameters/resources were frozen before any measured PnP. Exactly one estimator:SOLVEPNP_EPNP RANSAC1000iterations/confidence0.999/2px/seedSHA('PR1:'+key), no LM/model/fit/seed/threshold rescue. Native inliers are independently reprojected and require positive target depth,<=2px residual and>=8 support. The installedOpenCV5.0.0 EPNP flag is1, confirmed directly; do not substitute values recalled from another version.

All23 pre-measured controls passed: actual API, first solver call after strict I/O gate, clean/nonplanar direction/inverse/metric scaling, exact fixed outliers, deterministic outputs, ranks0/1/2/3, planar/duplicate/collinear/2D/nonfinite/invalidK fallbacks, support/positive depth, zero/unit direction, cold NPZ and reference-binding denial. The rank tests run before real data here; they do not retroactively repair SD1's omitted prospective rank test. No failed PR1 child/retry or settings change occurred. The copied launcher console prefix 'VB1' identifies this PR1 folder's receipt, not a reversal of original VB1's failure.

All200 prediction records/evidence were sealed2026-10-28 12:47:07.8857930UTC; reference-read begin is12:47:33.895155UTC. Prediction's exact Python read allowlist contains only200 sealed source hypothesis files and two archive calibration files. No reference/labels/outcome values; native APIs receive arrays only. This is source-reviewed Python I/O separation, not OS security isolation.

Independent audit passes all200 masks/order and complete summaries,1129 scalar projection checks (max pixel delta{audit['max_projection_delta_px']:.17g},zero threshold-boundary ambiguities),200 Decimal60 relative reference solves and independent scalar rotation/translation/direction errors. Max Q/R/t/direction differences are{audit['maximum_metric_differences']['Q']:.17g}/{audit['maximum_metric_differences']['R']:.17g}/{audit['maximum_metric_differences']['t']:.17g}/{audit['maximum_metric_differences']['direction']:.17g}. No prediction replay was used in audit.

Resource audit:inclusive{inclusive:.6f}/3600s including preparation/closure, child host walls{sum(r['elapsed_seconds'] for r in receipts):.7f}s, max lifetime peak{max(r['child_lifetime_peak_bytes'] for r in receipts)}bytes,new dossier{size}/16777216bytes before small closure additions. All four stages passed fresh12GiB/2s gates, their60/180/120/120s limits, exit0 and reaping. No live owned worker remains. No installation/network/WSL/GPU/Torch/model/training/existing-environment/default/production/Git writes/outreach/scheduler/goal-status action.

Next saved-output categorical comparison must keep all200 IDs and the frame/task distinctions. If any future point-cloud initializer uses these17 camera poses, first establish raw LiDAR<->camera/public normalization action explicitly. Do not infer a constant transform for the old point-dependent correction or automatic RAP benefit. No new model experiment is admitted by this closeout. ResearchUNRESOLVED/manuscriptPAUSED; SR1/HFIT0/all older failures/caps/source restrictions unchanged.
'''
with (ROOT/'REPORT.md').open('x',encoding='utf-8',newline='\n') as f:f.write(report)
save('STATUS.json',{'state':'COMPLETE_200_PREDICTIONS_EVALUATION_AND_INDEPENDENT_AUDIT','pose_outputs':17,'no_evidence':183,
    'sequence00_outputs':17,'sequence08_outputs':0,'R5_t2_all200':17,'numerical_metric_camera_pose_estimated':True,
    'physical_scale_authenticated':False,'corrected_LiDAR_equivalence_established':False,'RAP_increment_or_new_training':False,
    'research':'UNRESOLVED','manuscript':'PAUSED','all_owned_children_reaped':True})
with (ROOT/'CURRENT_HANDOFF.md').open('x',encoding='utf-8') as f:f.write('''# PR1 finite baseline complete

Read REPORT.md/STATUS.json/RESOURCE_AUDIT.json/DELIVERY_SEAL.json. All200 predictions sealed before reference evaluation and independently audited.17 numerical metric-camera poses/all00;08zero;183noevidence. All17 in frozen5deg/2m bin, denominator200; meanR0.623331734deg/t0.664157493m has denominator17. Source-depth hypotheses remain unverified correspondences, no physical scale/corrected-LiDAR/RAP claim.23 prospective controls passed. No retries or model/training. No pending worker or automatic resume; do not rerun closed hosts. All old failures/caps remain; researchUNRESOLVED/manuscriptPAUSED. Current owner/account continuation is separate in project-continuation-03.
''')
files=[{'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(ROOT.rglob('*')) if p.is_file()]
save('DELIVERY_SEAL.json',{'utc':dt.datetime.now(dt.timezone.utc).isoformat(),'files':files})
print('PR1 complete final seal',len(files),'entries; all children reaped')
