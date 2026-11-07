"""Finalize validated PFG1 evidence, resource accounting and continuity."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
MAIN=Path(__file__).resolve().parents[2];ROOT=MAIN/'docs/maintenance/2026-10-07/geometric-information-screen-01';ATT=ROOT/'attempt-02'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,d):
    with p.open('x') as f:json.dump(d,f,indent=2,allow_nan=False);f.write('\n')
validation=read(ATT/'validation.json');bankval=read(ATT/'bank_validation.json');result=read(ATT/'results.json');execution=read(ROOT/'bank/execution.json')
assert validation['passed'] and bankval['passed'] and validation['decision']==result['gate']['decision']=='NO_MEASURED_INFORMATION_SHAPE_SIGNAL'
for base in [ROOT,ATT]:
    for p,h in read(base/'freeze.json')['files'].items():assert sha(p)==h,p
for p,h in read(ROOT/'bank_seal.json')['files'].items():assert sha(ROOT/'bank'/p)==h,p
assert sha(ATT/'validation.json')==read(ATT/'validation_seal.json')['validation_sha256']
assert sha(ATT/'results.json')==read(ATT/'validation_seal.json')['results_sha256']
for p,h in read(ATT/'validation_seal.json')['evaluation_files'].items():assert sha(ATT/'evaluation'/p)==h,p
wall=sum(x['wall_s'] for x in [execution,bankval,result,validation]);peak=max(x['peak_rss_bytes'] for x in [execution,bankval,result,validation]);size=sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file())
assert peak<4*2**30 and size<300*2**20
gain={g:dict(ter_gain_pp=m['N']['ter']-m['S']['ter'],ATE_gain_percent=(1-m['S']['ate']/m['N']['ate'])*100) for g,m in result['cohort_means'].items()}
resource=dict(successful_stages_wall_s=wall,maximum_stage_peak_rss_bytes=peak,artifact_bytes_before_report=size,incremental_S_s=execution['S_incremental_s'],original_verification_s=154.09,incremental_ratio=execution['S_incremental_s']/154.09,successful_only=True,original_failed_validation_wall_s=None,failed_work='Original validator stops at first00 H mismatch; time not recorded by frozen validator. Original failure/source/bank remain.',new_inference=False,new_GPU=False)
save(ROOT/'RESOURCE_AUDIT.json',resource)
lines=['# PFG1 measured geometric information shape','',
       '**VALIDATED_NEGATIVE**, decision **NO_MEASURED_INFORMATION_SHAPE_SIGNAL**.',
       'Owner requested an explicit next plan and further progress. MC1 and PFG0',
       'passed, then this direct system screen ran with original58 loop centers.',
       'It provides no material combined ter/ATE improvement or originality claim.','',
       '## Result','',
       '| Cohort | N ter % | S ter % | ter gain pp | N ATE m | S ATE m | ATE gain % |',
       '|---|---:|---:|---:|---:|---:|---:|']
for g,m in result['cohort_means'].items():
    lines.append(f"| {g} | {m['N']['ter']:.6f} | {m['S']['ter']:.6f} | {gain[g]['ter_gain_pp']:+.6f} | {m['N']['ate']:.6f} | {m['S']['ate']:.6f} | {gain[g]['ATE_gain_percent']:+.3f} |")
lines += ['', 'Both cohorts fail the conjunction of >=.01pp ter and >=5% ATE gain.',
          'S beats fixed cyclic-direction Q in ATE but loses to Q in ter in both',
          'cohorts, so physical-direction attribution also fails.07 ter rises',
          f"{result['rows']['07']['N']['ter']:.6f}->{result['rows']['07']['S']['ter']:.6f}% (+{result['rows']['07']['S']['ter']-result['rows']['07']['N']['ter']:.6f}pp), exceeding .01pp safety.",
          'All other sequence safety tests and10 no-op pass. Incremental cost passes.',
          'Do not reinterpret isolated06/09 improvements as a passing method.','',
          '| Sequence | N/S/Q ter % | N/S/Q ATE m |', '|---|---|---|']
for s,r in result['rows'].items():lines.append(f"| {s} | "+' / '.join(f"{r[a]['ter']:.6f}" for a in ['N','S','Q'])+' | '+' / '.join(f"{r[a]['ate']:.6f}" for a in ['N','S','Q'])+' |')
lines += ['', '## What ran and what is preserved','',
          'Original170 identities froze before81 measured normal caches,58 shape',
          'NPZs and18 dense/keyframe trajectory pairs. All58 edges have support,',
          'all matrices are rank6 under the frozen reporting tolerance, zero fallback.',
          'The bank has110069 mutual associations/two Jacobians each. No inferred',
          'RAP pose, keyframe, admission, odometry factor or total information changed.',
          'Native N, geometry S and spectrum/strength-preserving cyclic Q replace',
          'loop information only. Curvature at fixed centers discards surface residual',
          'offsets; it is neither calibrated covariance nor full physical bundle adjustment.','',
          'Original independent validator failed at first00 H: general inverse versus',
          'frozen rigid-transpose inverse on rounded native matrices. AMENDMENT_01',
          'preserves original source/freeze/bank/seal/failure/root INCOMPLETE. Separate',
          'validator-only attempt-02 froze362 identities before retry, no bank or model',
          'rerun and no parameter/tolerance/cohort/gate edit. All58 rigid inverse',
          'operators match native Pose3; largest serialized orthogonality defect',
          f"{bankval['max_serialized_orth_error']:.6e}<1e-5, general-inverse entry disagreement{bankval['max_rigid_vs_matrix_inverse_delta']:.6e}.",
          'Nominal rigid Jacobians are used; exact physical derivatives at nonorthogonal',
          'serialized matrices are not claimed. Read original FAILURE and AMENDMENT.','',
          f"Independent SVD/brute force reconstructs all81 normal caches,58 shapes and{bankval['brute_force_distances']} distances;",
          f"max information delta{bankval['max_information_delta']:.6e}, trajectory delta{bankval['max_trajectory_delta']:.6e}.",
          'Its GT-free seal precedes evaluator GT. Independent scalar metric validation',
          f"recomputes{validation['independent_segment_records']} segment records, max aggregate delta{validation['max_metric_delta']:.6e}; all gates reproduce.",
          'No failure in repaired validation. Root status points to attempt-02, not',
          'the original invalid validation. Original labels and baselines unchanged.','',
          '## Resources and decision','',
          f"Successful bank/validator/evaluation/final-validator wall{wall:.3f}s, peak RSS{peak/2**30:.3f}GiB, artifacts{size/2**20:.2f}MiB before reports.",
          f"S incremental normal/shape/graph processing{execution['S_incremental_s']:.3f}s/{154.09:.2f}s historical verification = {execution['S_incremental_s']/154.09*100:.3f}% (<25%).",
          'This uses warmed cached inputs, excludes N/Q, validators/evaluation and',
          'prior acquisition. Failed original validation time was not recorded and',
          'is not presented as zero or included in successful-only cost. No new GPU',
          'or inference. Per-stage caps pass. RESOURCE_AUDIT gives machine records.','',
          'Stop this exact fixed-center20-neighbor/mutual1m/trace-six construction',
          'without radius/normal/eigenaxis/scalar/cohort rescue or default promotion.',
          'This bounded negative does not reject all physical factor objectives or',
          'establish a global ceiling. Strong geometric-information prior art remains.',
          'NEXT_ROUND_PLAN selects a complete fixed-budget exposure/placement opportunity',
          'audit before a new measurement source. The separate learned-token source',
          'audit is design only; no head, new extraction, learning or training exists.',
          'All older stops/banks, checkpoint exposure uncertainty,09 physical discrepancy,',
          'official GT/metrics and original thesis-breakthrough requirement persist.',
          'Both original HEADs/branches/dirty work preserved; no production/default/',
          'model/manuscript edit, training, acquisition/install, commit or Git sync.']
(ROOT/'REPORT.md').write_text('\n'.join(lines)+'\n')
(ROOT/'HANDOFF.md').write_text('''# PFG1 current handoff

Read REPORT, PROTOCOL, NEXT_ROUND_PLAN, STATUS, RESOURCE_AUDIT, AMENDMENT_01,
FAILURE_validation_bank and original freeze/bank_seal. Then attempt-02 PROTOCOL,
freeze/bank_validation/seal/results/validation/seal. Root INCOMPLETE records the
preserved invalid original validation; current validated evidence is attempt-02.
No result bank was changed by the repair. No running process remains.

Decision NO_MEASURED_INFORMATION_SHAPE_SIGNAL. Stop this exact construction;
do not sweep normal/matching radius/information axes/scalars/cohorts. All58
shapes rank6, all supported; this does not prove physically correct loop poses.
No calibrated covariance or original RAP/system improvement exists.

Next LC0 fixed-budget complete retrieval/placement diagnostic is planned only,
not frozen/implemented/run. Its protocol must reproduce original71 attempts,
seal before GT and use evaluator-only opportunity distinct from actual recall
or a GT-free method. Learned-measurement-design-01 is source/metadata design
only:512-D token interface exists; no extraction preflight/head/training.

Preserve old stops/banks/disclosures, official GT/metrics, unknown checkpoint
membership,09 discrepancy and original breakthrough requirement. No training,
production/default/model/manuscript edit, acquisition/install, commit or sync.
Both original HEADs4055d929c594b0033aafc6eed339c910369eef55 and
6d3f2d22cedfe1f807deb11fd8796b9f5bf17cd6 and current branches/dirty work remain.
''')
status=dict(stage='PFG1',status='VALIDATED_NEGATIVE',decision=validation['decision'],validated_attempt='attempt-02',original_attempt='INCOMPLETE_VALIDATION_PRESERVED',original_bank_unchanged=True,gt_free_validation_before_evaluation=True,original_frozen_identities=170,repair_frozen_identities=362,loops=58,normal_scans=81,geometry_rank6_loops=58,matched_points=110069,cohort_gains=gain,next='LC0 PLANNED_NOT_IMPLEMENTED; learned readout DESIGN_ONLY; no training',training=False,production_edit=False,manuscript_edit=False,git_sync=False)
save(ROOT/'STATUS.json',status);save(ATT/'STATUS.json',status)
phase=MAIN/'docs/maintenance/2026-10-07/PHASE_RECORD.md'
with phase.open('a') as f:f.write(f'''
## Owner-authorized MC1, PFG0 and direct PFG1 system screen

Owner requested an explicit next plan and further progress. MC1 froze53
identities, independently validated12296 scans/1800 keyframes/1794 intervals,
maximum motion delta1.776e-15. Existing KISS/source artifacts do not provide
per-scan covariance/map correlations; complete retrieval exposure is absent.
Scan span1-94 is not a justification for propagated or sqrt(span) weights.
No GT or optimization in MC1. Separately frozen PFG0 four identities/13 NPZs
validate12 geometry cases, estimator/ties/invariance and singular GTSAM noise;
FD delta3.578e-10. A wrong2m plane translation remains invisible.

PFG1 froze170 identities and generated81 normal/58 shape NPZs and18 graph
trajectories with original loop centers/strength/admissions/odometry. Original
validator failed on first00 H at general-versus-rigid inverse of rounded native
R. Original source/freeze/complete bank/failure/root INCOMPLETE preserved;
AMENDMENT_01 and separate362-identity validator-only attempt-02 correct that
reconstruction, verify native Pose3 inverse and existing SE3 tolerance. No bank
rerun, settings/tolerance/cohort/gate change. Independent3152000000 distances,
110069 associations/58 shapes/18 trajectories pass; information delta1.228e-11,
trajectory delta1.183e-9. GT-free seal before evaluator;22194 segments and all
metrics/gates independently reproduce(max aggregate delta4.736e-13).

Decision VALIDATED_NEGATIVE, NO_MEASURED_INFORMATION_SHAPE_SIGNAL. Development
ter gain{gain['development']['ter_gain_pp']:+.6f}pp, ATE gain{gain['development']['ATE_gain_percent']:+.3f}%; exposed-transfer
ter gain{gain['transfer_exposed']['ter_gain_pp']:+.6f}pp, ATE gain{gain['transfer_exposed']['ATE_gain_percent']:+.3f}%. Both combined material gates fail;
S loses to Q in ter in both cohorts;07 ter regression+.011432pp fails safety.
All58 shapes rank6, no fallback;10 native no-op and cost pass. Successful stages
{wall:.3f}s, peak{peak/2**30:.3f}GiB; S increment9.065s/154.09s=5.883%. Failed
original validation time unavailable, preserved separately. Stop this exact
shape route without rescue/default promotion. All older stops/results remain.

After evaluation, source/metadata-only learned-measurement design audit confirms
512-D post-attention per-row token export at last flow call (not final t=0).
No runtime extraction/head/labels/training. Local00-10 scan/GT/calib/times file
presence checked, camera directories absent in observed roots, external dataset
inventory incomplete. Prior learned/generative correspondence art is strong;
learnability, runtime invariance and originality unestablished.

Next LC0 complete fixed-budget retrieval/measurement-placement opportunity audit
is PLANNED_NOT_IMPLEMENTED: no runner/protocol/freeze/scan/descriptor/oracle/bank.
It precedes a new learned-matching proposal because same-endpoint ter headroom
is limited. Current no-training boundary remains. Both original HEADs/branches
and dirty work inspected/preserved. No new RAP inference, production/default/
model/manuscript edit, download/install, commit or Git synchronization.
''')
agents=MAIN/'AGENTS.md';text=agents.read_text(encoding='utf-8-sig');heading='# AGENTS.md — RAP / RAP-SLAM current handoff\n';assert text.startswith(heading)
entry=f'''
Latest experimental boundary (2026-10-07, continued): owner requested an
explicit next plan and further progress. MC1 source/census and PFG0 analytic
geometry preflight are VALIDATED; PFG1 complete six-sequence measured geometric
information-shape system screen is VALIDATED_NEGATIVE, decision
NO_MEASURED_INFORMATION_SHAPE_SIGNAL. Read docs/maintenance/2026-10-07/
measurement-source-audit-01/REPORT.md,HANDOFF.md,STATUS.json,NEXT_ROUND_PLAN.md;
geometric-information-preflight-01/REPORT.md,PROTOCOL.md,freeze/bank_seal/
validation/seal; geometric-information-screen-01/REPORT.md,PROTOCOL.md,
NEXT_ROUND_PLAN.md,HANDOFF.md,STATUS.json,RESOURCE_AUDIT.json,AMENDMENT_01.md,
FAILURE_validation_bank.json and original/attempt-02 freeze/seals/validation.
MC1 freezes53 identities, checks12296 scans/1800 keyframes/1794 intervals,
motion delta1.776e-15; scan spans1-94 do not establish statistical harm.
Per-scan covariance/map correlations and complete retrieval exposure absent
from selected interfaces/artifacts; no propagated/sqrt(span) weights admitted.
PFG0 four identities/13 synthetic NPZs pass12 cases, FD delta3.578e-10;
wrong-consistent2m planar translation remains invisible, no confidence claim.
PFG1 original170 identities freeze before81 normals/58 shapes/18 trajectories.
All58 loops retain original centers/admissions/odom/scalar strength, rank6,
zero fallback. Original validator fails at first00 H on general vs rigid
inverse of rounded native R; original complete bank/source/freeze/failure/root
INCOMPLETE stay unchanged. Disclosed validator-only attempt-02 freezes362
identities, reconstructs native rigid inverse without bank rerun/settings/
tolerance/gate change; max serialized orthogonality1.766e-6<1e-5. Nominal
rigid Jacobians are not exact physical derivatives at rounded nonorthogonal R.
Independent3152000000 distances/110069 associations/all shapes and18 graphs
pass; max info/trajectory delta1.228e-11/1.183e-9. GT-free validation seals
before GT;22194 metric records independently reproduce(delta4.736e-13).
Dev N/S ter.388718/.387965%, ATE1.460664/1.450289m; exposed-transfer
ter.505615/.509171%, ATE.721480/.722880m. Both material conjunctions fail;
S loses to cyclic-direction Q in ter both groups;07+.011432pp violates safety.
Stop exact fixed-center20-neighbor/mutual1m/trace-six shape route, no radius/
normal/eigenaxis/scalar/cohort rescue/default promotion. Successful stages
{wall:.3f}s, peak{peak/2**30:.3f}GiB; S increment9.065s/154.09s=5.883%, caps pass.
No material metric improvement, calibrated covariance, physical correctness
or originality. Next LC0 fixed-budget complete retrieval/placement opportunity
diagnostic PLANNED_NOT_IMPLEMENTED, no protocol/runner/freeze/bank/oracle.
learned-measurement-design-01 source/metadata audit is DESIGN_ONLY:512-D
post-attention token export exists, but extraction/learnability unvalidated;
no head, new inference or training. Read its REPORT/HANDOFF/STATUS/SOURCE_AUDIT.
It is conditional after metric opportunity; prior learned matching art is
strong. All prior stops/banks/official GT/metrics, unknown checkpoint membership,
09 discrepancy and original breakthrough requirement persist. Both original
HEADs/branches/dirty work preserved; no training, production/default/model/
manuscript edit, acquisition/install, commit or Git sync.
'''
agents.write_text(heading+entry+text[len(heading):],encoding='utf-8')
sealpaths=[ROOT/x for x in ['REPORT.md','HANDOFF.md','STATUS.json','NEXT_ROUND_PLAN.md','RESOURCE_AUDIT.json','AMENDMENT_01.md']]+[agents,phase]
for folder in ['measurement-source-audit-01','geometric-information-preflight-01','learned-measurement-design-01']:
    sealpaths += [p for p in (MAIN/'docs/maintenance/2026-10-07'/folder).iterdir() if p.is_file() and p.suffix in ['.md','.json']]
save(ROOT/'DELIVERY_SEAL.json',dict(utc=datetime.now(timezone.utc).isoformat(),files={str(p.relative_to(MAIN)):sha(p) for p in sealpaths},original_bank_seal_sha256=sha(ROOT/'bank_seal.json'),validated_result_sha256=sha(ATT/'results.json')))
print(json.dumps(dict(decision=validation['decision'],gains=gain,resources=resource),indent=2))
