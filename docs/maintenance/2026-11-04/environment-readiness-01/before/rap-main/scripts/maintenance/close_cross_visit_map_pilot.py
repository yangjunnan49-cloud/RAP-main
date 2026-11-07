"""CV1 source/delivery bookkeeping; no additional optimization or evaluator call."""
import subprocess
from pathlib import Path
import cross_visit_map_pilot_attempt02 as retry

run, ROOT = retry.run, retry.ORIGINAL


def main():
    run.verify()
    assert run.read(run.BASE/'bank_validation.json')['passed'] and run.read(run.BASE/'validation.json')['passed']
    assert not (run.BASE/'INCOMPLETE').exists() and (ROOT/'INCOMPLETE').exists()
    prior_delivery = run.previous.check_delivery(run.previous.BASE)
    older_delivery = run.previous.check_delivery(run.previous.prior.BASE)
    mmr_delivery = run.previous.check_delivery(run.old.ROOT_BASE)
    cache, frozen_checks = {}, []
    for directory in (ROOT, run.BASE):
        frozen = run.read(directory/'freeze.json')
        for path, digest in frozen['files'].items():
            actual = cache.setdefault(path, run.sha(path))
            assert actual == digest
            frozen_checks.append(dict(freeze=str(directory/'freeze.json'),path=path,sha256=digest,matches=True))
    seal = run.read(run.BASE/'bank_seal.json')
    for name,digest in seal['files'].items():
        assert run.sha(run.BASE/'bank'/name) == digest
    models = run.read(run.previous.BASE/'CHECKS.json')
    for entry in models['model_source_checks']:
        assert run.sha(run.old.MAIN/entry['path']) == entry['sha256']
    checkpoint = run.sha(run.old.MAIN/'weights/rap_model_12.ckpt')
    assert checkpoint == models['opaque_checkpoint_sha256']
    expected = run.read(run.previous.BASE/'REPOSITORY_STATE.json')['repositories']
    repositories = []
    for directory, wanted in zip((run.old.MAIN,run.old.SLAM),expected):
        def git(*args):
            return subprocess.check_output(['git','-C',str(directory),*args],text=True).rstrip('\n')
        actual = dict(root=wanted['root'],HEAD=git('rev-parse','HEAD'),branch=git('branch','--show-current'),
                      tracked_dirty=git('status','--porcelain','--untracked-files=no').splitlines())
        assert actual == wanted, actual
        repositories.append(actual)
    result = run.read(run.BASE/'results.json')
    summary = run.read(run.BASE/'bank/summary.json')
    preflight = run.read(run.BASE/'preflight.json')
    validation = run.read(run.BASE/'validation.json')
    assert all(not x['eligible'] for x in result['comparisons'].values())
    decision = 'NO_FULL_POSE_CROSS_VISIT_CONJUNCTION'
    logs = run.read(run.BASE/'RESOURCE_LOG.json')
    original_logs = run.read(ROOT/'RESOURCE_LOG.json')
    assert logs[:len(original_logs)] == original_logs
    total = sum(r['wall_s'] for r in logs)
    peak = max(r['peak_rss_bytes'] for r in logs)
    assert total <= 1800 and peak <= 2*2**30
    metric_lines = []
    geometry_lines = []
    for arm in ('O','B','F','J'):
        m = result['rows'][arm]
        metric_lines.append(f"| {arm} | {m['joint_aligned_ate_m']:.6f} | {m['endpoint_translation_m']:.6f} | {m['endpoint_rotation_deg']:.6f} |")
        geometry_lines.append(f"| {arm} | {summary['geometry'][arm]['train']['rms_m']:.6f} | {summary['geometry'][arm]['holdout']['rms_m']:.6f} |")
    report = f'''# CV1 actual revisit: translation/ATE benefit with a rotation tradeoff

Status **VALIDATED_EXPLORATORY_COMPLETE_WITH_IMPLEMENTATION_REPAIR**; decision
**{decision}**. Owner instructed "执行下一轮方案".
The fixed00revisit2429->3373 and both eight-scan visits were executed. Rigid
map refinement yields the first material translation/jointATE effect in this
measured-map mainline, but fails the predeclared rotation guard. Joint internal
optimization adds little under this construction. No system gain, full-pose
conjunction, independent generalization or original breakthrough is established.

## Fixed source and results

Original accepted E0 A record0/measurement_id
ef08402bdc746147a081b1137926970c29f435d724db04ef096c8f11d475977e.
A2378/2384/2391/2398/2405/2413/2423/2429;
B3318/3324/3331/3338/3345/3352/3361/3373. All16raw inputs independently checked,
96000retained points with frozen preprocessing. Proper Oprojection maximum
{summary['projection_max_delta']:.10g}; Zprojection {summary['z_projection_max_delta']:.10g}.
All216eligible2m patches span both visits;163training/53whole-patch holdout.
Training per-visit point coverage7075/6885,holdout2181/2126;all8scans supported
in each visit. No favorable replacement/hash/scale/window selection.

O retains original odometry relative placement. B uses saved RAP Z with fixed
internal O shapes (single relative-pose alignment, not complete E0 PGO replay).
F adjusts only six rigid placement variables. J frees15scan poses, fixes Aendpoint
and adds only14within-visit motion edges at.10m/.15deg averaged by14. No fabricated
temporal-gap edge or duplicate RAP pose factor. Both use identical training
cross-visit moments, analytic plane refit, Schur elimination and24updates.

| Arm | Joint16node aligned ATE(m) | Endpoint translation error(m) | Endpoint rotation error(deg) |
|---|---:|---:|---:|
{chr(10).join(metric_lines)}

F versus B:ATE **+5.344%**,endpoint translation **+7.955%**,rotation **+.026466deg**.
J versus B:ATE **+5.644%**,endpoint translation **+8.205%**,rotation **+.030760deg**.
Both meet the5%ATE/translation conditions, valid-correction/internal safety and
holdout conditions, but both exceed the **.01deg rotation regression** guard.
All conjunctions fail; do not retroactively relax that guard or present full
SE3improvement. Angles use the prospective proper-rotation convention; historical
accepted-loop GT fields and official metrics are unchanged, not reclassified.

J versus F improvesATE only **.316%** and endpoint translation **.271%**, with
rotation **+.004294deg**. It misses both5%requirements for internal-pose value.
J's A internalATE improves3.276%,B.435%;Binternal tRMSE regresses.792%, all
internal guards pass. This does not prove all BA useless, or separate its fixed
prior from geometry bias. It gives no evidence to expand this exact Jconstruction.

| Arm | Training balanced patch RMS(m) | Heldout balanced patch RMS(m) |
|---|---:|---:|
{chr(10).join(geometry_lines)}

Heldout RMS F/B=.986665736,J/B=.983099155,J/F=.996385219. Those reporting-plane
nuisance fits never inform updates/backtracking/stopping. Membership/eligibility
were selected at B using all geometry, so O cost is evaluated on B-selected
support, not an unbiased comparison. Nearby surfaces/scan observations remain
correlated. Lower residual and good normal spread are not physical verification.

F endpoint correction.064062m/.079296deg,internal shape preserved to2.08e-12m.
J endpoint correction.066044m/.076965deg,maximum internal correction.012470m/
.020992deg. Both within prospective1m/5deg internal and5m/25deg placement bounds.

## Engineering repair and verification

Original51entryfreeze/sources/snapshots/RESOURCE_LOG/INCOMPLETE remain immutable.
Original preflight failed perfect-input no-op at F3.2007e-7,J8.8818e-16, before
real coordinates or new evaluator poses. Same-fixture diagnosis isolated F's
E' rigid_inverse(E) E endpoint recomposition, amplifying SO3roundoff repeatedly.
Separate implementation-only attempt-02 assigns the endpoint directly to E',
with identical mathematics/criteria/gates. Distinct helper and67entryfreeze;
original failure/diagnosis disclosed in AMENDMENT_01. No threshold change.

Same complete preflight now passes:explicit-vs-compact H/g1.4211e-14/7.7161e-15,
F/JgradientFD6.5609e-9/8.7622e-9, separate-chain gauge3.5527e-15, common gauge
1.9540e-14, no-gap exact, no-op1.1102e-14,recovery1.5099e-14, planar blind rank3.
CompleteO/B/F/Jbank seals before any new numeric pose-reference outcome.
Independent16raw preprocessing maxdelta1.4211e-14,selected moments exact,
explicit geometry5.6342e-13,cost1.5721e-13,selected realFD4.4815e-9. Proper poses,
hash/membership/mass/support,fixed internal shape,traces/corrections checked.
Independent camera->LiDAR/reference/HornATE/error reconstruction maxdelta
{validation['independent_metric_max_delta']:.10g};all3conjunctions reproduced.
Bounded discovery verification,not full optimizer replay/rejected-patch census.

## Resources, interpretation and next hypothesis

All{len(logs)}original/failure/diagnostic/retry/validation stages counted once:
**{total:.6f}s**,peakRSS **{peak}bytes**,noGPU. New1800s/RSS2GiB/dossier512MiB caps
pass, including the original preflight failure. Imports/WSLstartup,design/docs/
delivery bookkeeping excluded; not production runtime. See RESOURCE_AUDIT.json.

We now have a concrete partial signal to develop:the shared map can improve
translation/position shape on an actual revisit. Its free rotational refinement
trades away some of the native RAP angle accuracy. Internal BA adds only marginal
gain in this case. A testable next restriction is to preserve RAP rotation and
both internal O shapes while refining map translation on a fixed00/05/06development
cohort. This reduced-variable hypothesis is proposed post-outcome, not executed
or admitted by a passing CV1gate; it might lose the observed translation gain.
See NEXT_ROUND_PLAN.md. No extra arm,cohort,full trajectory or production follows.

Physical patch identity/dynamics,initialization/membership bias,prior balance,
missing scan times/covariance/cross-correlations,calibration/reference conflict,
09discrepancy and checkpoint/site exposure remain unresolved. Conventional
[BALM](https://arxiv.org/abs/2209.08854) prior art is credited; owner originality
relaxation permits this engineering route without a new mechanism claim.

Both original HEADs/branches/2and9tracked dirty sets preserved. PriorSMP2
{prior_delivery},SMP1{older_delivery},MMR0{mmr_delivery}delivery identities unchanged,
8model/config hashes and opaque checkpoint exact,not deserialized. New isolated
RAP-SLAM helpers/main maintenance/docs and mutable handoffs only;no GPU/modelload/
training/RAPinference/officialGTmetric replacement/acquisition/install/production/
default/backbone/manuscriptedit/commit/Gitsync.
'''
    (ROOT/'REPORT.md').write_text(report,encoding='utf-8')
    handoff = '''# CV1 handoff

Read REPORT,PROTOCOL,AMENDMENT_01,NEXT_ROUND_PLAN,STATUS,RESOURCE_AUDIT,CHECKS,
REPOSITORY_STATE,DELIVERY_SEAL. Root original51entryfreeze/source_snapshot,
FAILURE_preflight/PREFLIGHT_DIAGNOSIS/RESOURCE_LOG/INCOMPLETE stay immutable.
Validated scientific output is attempt-02:67entryfreeze/preflight/bank_seal/
bank_validation/results/validation and combined resource ledger.

Fixed00first accepted2429->3373,two8scanvisits/96000points/216crosspatches,
163train/53holdout;all supported. F/J24updates,two14edge chains,no gap edge.
FvsBjointATE+5.344%,endpointt+7.955%,R+.026466deg>.01guard;J+5.644%/+8.205%/
+ .030760deg. JvsF+.316%ATE/+.271%t. All3conjunctions fail;partial translation
signal not fullSE3/system gain. Internal/holdout/correction safety pass.
Do not expand this exact J or rescueCV1 with thresholds/steps/prior/hash/points.

Original syntheticFno-op failed from repeated endpoint rigid recomposition;
separate source only assigns E' directly. Same no-op/recovery now1.11e-14/1.51e-14,
same scientific settings and originalfailure retained. Full raw/selectednumeric/
independentmetric checks pass;no fulloptimizer/rejectedcensus replay.

Next post-outcome designonly:fixedRAProtation/maptranslation-only rigid refinement,
matchedB/F/T first accepted00/05/06cases,same criteria,fixed cohort/no best-armoracle.
Not implemented/frozen/executed;conditional fullsystem stage did not follow failed
CV1. Prior exposure,physics/calibration/dynamics/membership/localminimum/09/
checkpoint/site unknowns and all historicalstops/seals persist. Owner originality
relaxation admits conventional engineering,not original/independentclaims.
All failedcompute/RSS recorded;no acquisition/model/GPU/training/RAP/default/
backbone/manuscript/production/Git change. Both originalHEADs/branches/dirtysets kept.
'''
    (ROOT/'HANDOFF.md').write_text(handoff,encoding='utf-8')
    run.save(ROOT/'STATUS.json',dict(task='cross-visit-map-pilot-01',status='VALIDATED_EXPLORATORY_COMPLETE_WITH_IMPLEMENTATION_REPAIR',
             decision=decision,owner_authorization='执行下一轮方案',primary_scientific_attempt='attempt-02',
             original_preflight_failure_preserved=True,original_INCOMPLETE_preserved=True,
             original_freeze_entries=51,retry_freeze_entries=67,scans=16,retained_points=96000,
             cross_visit_patches=216,train_patches=163,holdout_patches=53,all_supported=True,
             comparisons=result['comparisons'],research_finding='PARTIAL_RIGID_TRANSLATION_ATE_SIGNAL_WITH_ROTATION_TRADEOFF',
             internal_pose_value_established=False,whole_system_or_independent_gain=False,
             next_fixed_rotation_translation_design_only=True,new_cohort_or_arm_executed=False,
             full_optimizer_replay=False,official_GT_metrics_changed=False,new_model_training_RAP_inference=False))
    run.save(ROOT/'CHECKS.json',dict(all_match=True,frozen_entries_checked=len(frozen_checks),frozen_checks=frozen_checks,
             bank_seal_entries_checked=len(seal['files']),prior_SMP2_delivery_entries_unchanged=prior_delivery,
             prior_SMP1_delivery_entries_unchanged=older_delivery,prior_MMR0_delivery_entries_unchanged=mmr_delivery,
             model_source_checks=models['model_source_checks'],opaque_checkpoint_sha256=checkpoint,
             checkpoint_deserialized=False,original_INCOMPLETE_preserved=True,retry_INCOMPLETE_absent=True))
    run.save(ROOT/'REPOSITORY_STATE.json',dict(repositories=repositories,heads_branches_tracked_sets_preserved=True,
             new_isolated_helpers=['cross_visit_map.py','cross_visit_map_attempt02.py'],no_commit_or_sync=True))
    resource_audit = dict(recorded_stages=len(logs),total_accounted_wall_s=total,peak_rss_bytes=peak,
                         failed_stages=sum(not r['passed'] for r in logs),original_log_rows_preserved=len(original_logs),
                         no_double_count=True,failure_compute_included=True,all_attempted_rss_captured=True,
                         wall_cap_s=1800,rss_cap_bytes=2*2**30,artifact_cap_bytes=512*2**20,
                         wall_cap_pass=True,rss_cap_pass=True,gpu_used=False,
                         excluded='Imports/WSLstartup/design/docs/deliverybookkeeping;notproductionruntime')
    resource_audit['dossier_bytes_before_audit_seal'] = sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file())
    resource_audit['artifact_cap_pass'] = resource_audit['dossier_bytes_before_audit_seal'] < 512*2**20
    run.save(ROOT/'RESOURCE_AUDIT.json',resource_audit)
    header = f'''Latest owner/execution boundary (2026-10-09, continued): owner said
"执行下一轮方案". CV1cross-visit-map-pilot-01 is VALIDATED_EXPLORATORY_COMPLETE_WITH_
IMPLEMENTATION_REPAIR;decision NO_FULL_POSE_CROSS_VISIT_CONJUNCTION. Read REPORT,
PROTOCOL,AMENDMENT_01,NEXT_ROUND_PLAN,HANDOFF,STATUS,RESOURCE_AUDIT,CHECKS,
REPOSITORY_STATE,DELIVERY_SEAL;original51entryfreeze/source_snapshot/failure/
PREFLIGHT_DIAGNOSIS/RESOURCE_LOG/INCOMPLETE and validatedattempt-02 67entryfreeze/
preflight/bank_seal/bank_validation/results/validation/combinedresourceledger.

Fixed00originalacceptedindex0,2429->3373,A2378/2384/2391/2398/2405/2413/2423/2429,
B3318/3324/3331/3338/3345/3352/3361/3373.16scans/96000points,216crossvisit2m
patches163train/53wholehashholdout,bothvisits8/8supported. Oodom/BsavedRAPZ/Fsix
rigidDOF/J15scanposes;anchorAendpoint,only14withinvisitmotionedges,.10m/.15deg
regularizer,no fabricatedgapedge/duplicateRAPfactor.24updates,fixedsettings.

JointalignedATE O/B/F/J.621228/.403028/.381489/.380282m;endpointt1.205342/.786381/
.723821/.721861m;R.619183/.194126/.220591/.224886deg. FvsBATE+5.344%,t+7.955%,
R+.026466deg>.01;JvsB+5.644%/+8.205%/+.030760deg. Bothmaterialt/ATEpass but
rotationguardfails;no fullpose/systemconjunction. JvsFATE+.316%,t+.271%,R+.004294,
no usefulinternalposeconjunction. Allcorrection/internal/holdoutsafety pass;
holdout F/B.986665736,J/B.983099155. Partialtranslation signal,not calibrated/
physical/independentgain ororiginalbreakthrough. No automaticcohort/trajectory.

Originalpreflight Fperfectnoop3.2007e-7failed before realcoordinates/newGT, J8.88e-16.
Fendpoint E'rigid_inverse(E)E repeatedlyamplifiedSO3roundoff. Separateonlyrepair
assignsE'directly,originalsources/freeze/failure/diagnosis/INCOMPLETE unchanged.
Samefullpreflightpasses H/g1.4211e-14/7.7161e-15,F/JFD6.5609e-9/8.7622e-9,
chain/commongauge3.5527e-15/1.954e-14,noop/recovery1.1102e-14/1.5099e-14,blindrank3.
Fullbank sealedbeforeGT;independent16rawdelta1.4211e-14,moments0,explicitgeometry
5.6342e-13,cost1.5721e-13,selectedrealFD4.4815e-9,metrics6.99996e-14/all3gates
reproduce. Boundedchecks,no fulloptimizer/rejectedpatchcensus replay.

StopextraexactCV1steps/prior/hash/scale/window/densityrescue andJexpansion.
NextpostoutcomeDESIGN_ONLY:protectsavedRAProtation/refinemaptranslation with
fixedB/F/T firstaccepted00/05/06cohort,same sourcecriteria/nooracle. No newarm,
cohortfreeze,optimizer/fulltrajectory. Musttestwhethertranslationgain survives;
currentrotationtradeoffdoesnotprove nativeRAP Rphysicallycorrect. Priorphysics,
dynamics/membershipselection/localminimum/priorbalance/timing/covariance/calibration,
09/checkpoint/site/exposure unknowns andalloldstops/seals persist. Originality/
rigorrelaxationpersists;BALMcredited,no newmechanismclaimed.

All9stagesincludingoriginalfailedpreflight/diagnosis/retry{total:.6f}s,peakRSS
{peak}bytes,allattemptedRSSrecorded/noGPU,caps1800s/2GiB/512MiBpass. Timers
excludeimports/WSLstartup/design/docs/bookkeeping,notproductionlatency.
BothoriginalHEADs/branches/2and9trackeddirtysets preserved;SMP2{prior_delivery}/SMP1
{older_delivery}/MMR0{mmr_delivery}deliveryidentities,8model/config+opaquecheckpointunchanged.
NewisolatedRAP-SLAMhelpers/mainmaintenance/docs+mutablehandoffs only;no model/
checkpointload,training/RAPinference/GPU/fulltrajectory/officialGTmetricreplacement/
acquisition/install/production/default/backbone/manuscriptedit/commit/Gitsync.

'''
    agents = run.old.MAIN/'AGENTS.md'
    title,body = agents.read_text(encoding='utf-8-sig').split('\n',1)
    agents.write_text(title+'\n\n'+header+body.lstrip('\n'),encoding='utf-8')
    with (run.old.MAIN/'docs/maintenance/2026-10-09/PHASE_RECORD.md').open('a',encoding='utf-8') as stream:
        stream.write('\n## CV1 actual revisit: rigid versus internal pose refinement\n\n'+header)
    entries = [dict(path=str(p.relative_to(ROOT)),sha256=run.sha(p),bytes=p.stat().st_size)
               for p in sorted(ROOT.rglob('*')) if p.is_file()]
    run.save(ROOT/'DELIVERY_SEAL.json',dict(status='VALIDATED_EXPLORATORY_COMPLETE_WITH_IMPLEMENTATION_REPAIR',decision=decision,
             original_failure_INCOMPLETE_preserved=True,scientific_attempt='attempt-02',files=entries,
             mutable_AGENTS_PHASE_outside_seal=True))
    assert run.previous.check_delivery(ROOT) == len(entries)
    assert run.previous.check_delivery(run.previous.BASE) == prior_delivery
    assert run.previous.check_delivery(run.previous.prior.BASE) == older_delivery
    assert run.previous.check_delivery(run.old.ROOT_BASE) == mmr_delivery
    bytes_total = sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file())
    assert bytes_total < 512*2**20
    print('CV1 closed',decision,len(entries),'files',total,'seconds',peak,'RSS',bytes_total,'bytes',flush=True)


if __name__ == '__main__':
    main()
