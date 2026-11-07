"""CV2 delivery identity and handoff bookkeeping; no new scientific computation."""
import subprocess
from pathlib import Path
import rotation_protected_map_pilot as run


def main():
    base = run.BASE
    assert not (base/'DELIVERY_SEAL.json').exists()
    frozen = run.verify()
    bank_validation = run.read(base/'bank_validation.json')
    validation = run.read(base/'validation.json')
    assert bank_validation['passed'] and validation['passed']
    assert not (base/'INCOMPLETE').exists()
    result = run.read(base/'results.json')
    summary = run.read(base/'bank/summary.json')
    gate = result['primary_gate']
    assert gate['eligible'] is False and validation['eligible'] is False
    assert gate['all_three_supported_valid'] and gate['rotation_invariance']
    assert gate['mean_fractional_joint_ate_gain'] < .05
    assert not gate['joint_ate_safety'] and not gate['endpoint_t_safety']
    assert bank_validation['old_CV1_00_array_max_delta'] == 0
    assert len(frozen['files']) == 104
    frozen_checks = []
    cache = {}
    for path in (base/'freeze.json', base/'objective-diagnosis-01/freeze.json'):
        entries = run.read(path)['files']
        for name, digest in entries.items():
            if name not in cache:
                cache[name] = run.sha(name)
            assert cache[name] == digest, name
        frozen_checks.append(dict(path=str(path),entries=len(entries),all_match=True))
    bank_seal = run.read(base/'bank_seal.json')
    for name,digest in bank_seal['files'].items():
        assert run.sha(base/'bank'/name) == digest
    diagnosis = base/'objective-diagnosis-01'
    diagnosis_seal = run.read(diagnosis/'output_seal.json')
    assert diagnosis_seal['optimizer_calls'] == 0
    assert diagnosis_seal['primary_CV2_outcome_unchanged']
    for name,digest in diagnosis_seal['files'].items():
        assert run.sha(diagnosis/name) == digest
    diagnosis_validation = run.read(diagnosis/'validation.json')
    assert diagnosis_validation['passed']
    prior_roots = dict(CV1=run.cv.BASE,SMP2=run.cv.previous.BASE,
                       SMP1=run.cv.previous.prior.BASE,MMR0=run.old.ROOT_BASE)
    prior_counts = {name:run.cv.previous.check_delivery(root) for name,root in prior_roots.items()}
    models = run.read(run.cv.BASE/'CHECKS.json')
    for entry in models['model_source_checks']:
        assert run.sha(run.old.MAIN/entry['path']) == entry['sha256']
    checkpoint = run.sha(run.old.MAIN/'weights/rap_model_12.ckpt')
    assert checkpoint == models['opaque_checkpoint_sha256']
    expected = run.read(run.cv.BASE/'REPOSITORY_STATE.json')['repositories']
    repositories = []
    for directory,wanted in zip((run.old.MAIN,run.old.SLAM),expected):
        def git(*args):
            return subprocess.check_output(['git','-C',str(directory),*args],text=True).rstrip('\n')
        actual = dict(root=wanted['root'],HEAD=git('rev-parse','HEAD'),branch=git('branch','--show-current'),
                      tracked_dirty=git('status','--porcelain','--untracked-files=no').splitlines())
        assert actual == wanted, actual
        repositories.append(actual)
    logs = run.read(base/'RESOURCE_LOG.json')
    assert len(logs) == 7 and all(row['passed'] for row in logs)
    total = sum(row['wall_s'] for row in logs)
    peak = max(row['peak_rss_bytes'] for row in logs)
    assert total < 1800 and peak < 2*2**30
    assert f'{total:.6f}' == '23.201185'
    decision = 'NO_SAFE_ROTATION_PROTECTED_COHORT_SIGNAL'
    status = 'VALIDATED_EXPLORATORY_COMPLETE'
    run.save(base/'STATUS.json',dict(task='rotation-protected-map-pilot-01',status=status,decision=decision,
        owner_authorization='执行下一轮方案;继续',execution_log_date='2026-10-09',delivery_date='2026-10-10',
        freeze_entries=104,raw_scans=48,retained_points=288000,all_supported=True,all_T_valid=True,
        primary_gate=gate,rotation_byte_identity=True,scientific_implementation_repair=False,
        research_finding='HELDOUT_GEOMETRY_IMPROVEMENT_DOES_NOT_CALIBRATE_POSE_IMPROVEMENT',
        independent_or_system_gain=False,posthoc_oracle_diagnosis=True,posthoc_optimizer_calls=0,
        unique_physical_cause_identified=False,next_membership_audit_design_only=True,
        new_membership_or_full_trajectory_executed=False,full_optimizer_replay=False,
        official_GT_metrics_changed=False,model_training_RAP_inference=False))
    run.save(base/'CHECKS.json',dict(all_match=True,frozen_checks=frozen_checks,
        bank_seal_entries_checked=len(bank_seal['files']),diagnosis_seal_entries_checked=len(diagnosis_seal['files']),
        prior_delivery_entries_unchanged=prior_counts,model_source_checks=models['model_source_checks'],
        opaque_checkpoint_sha256=checkpoint,checkpoint_deserialized=False,
        numerical_preflight_passed=True,all_raw_bank_validation_passed=True,
        complete_independent_primary_conjunction_checked=True,primary_eligible=False,
        posthoc_explicit_point_validation_passed=True,full_optimizer_replay=False,
        independent_rejected_feature_census=False,INCOMPLETE_absent=True,
        closing_script=dict(path=str(Path(__file__)),sha256=run.sha(__file__))))
    run.save(base/'REPOSITORY_STATE.json',dict(repositories=repositories,heads_branches_tracked_sets_preserved=True,
        new_isolated_helper='scripts/rotation_protected_map.py',new_main_maintenance_scripts=[
            'rotation_protected_map_pilot.py','validate_rotation_protected_map_pilot.py',
            'rotation_protected_objective_diagnosis.py','close_rotation_protected_map_pilot.py'],
        no_commit_or_sync=True,no_production_default_backbone_manuscript_change=True))
    resource = dict(recorded_stages=len(logs),core_stage_wall_s=sum(row['wall_s'] for row in logs[:6]),
        posthoc_stage_wall_s=logs[-1]['wall_s'],total_accounted_wall_s=total,peak_rss_bytes=peak,
        failed_stages=0,all_attempted_rss_captured=True,no_double_count=True,wall_cap_s=1800,
        rss_cap_bytes=2*2**30,artifact_cap_bytes=512*2**20,wall_cap_pass=True,rss_cap_pass=True,gpu_used=False,
        excluded='Imports/WSLstartup/design/docs/delivery bookkeeping;not production runtime',
        stage_ledger_sha256=run.sha(base/'RESOURCE_LOG.json'))
    header = f'''Latest owner/execution boundary (2026-10-10, continued): owner said
"执行下一轮方案" then "继续". CV2 rotation-protected-map-pilot-01 is
VALIDATED_EXPLORATORY_COMPLETE;decision {decision}.
Read docs/maintenance/2026-10-09/rotation-protected-map-pilot-01 REPORT,PROTOCOL,
NEXT_ROUND_PLAN,HANDOFF,STATUS,RESOURCE_AUDIT,CHECKS,REPOSITORY_STATE,DELIVERY_SEAL;
104entry freeze/source_snapshot/preflight/bank_seal/bank_validation/results/
validation;separate POSTHOC_DIAGNOSIS_SCOPE and objective-diagnosis-01 freeze/
results/validation/output_seal. Execution stages2026-10-09;delivery2026-10-10.

Fixed first original accepted index0 00/05/06:2429->3373,538->1302,150->978;
two8scanvisits each,48scans/288000points. Cross2m patches216/132/204,train
163/102/163,wholehashholdout53/30/41;all supported,F/T valid. BsavedRAPZ with
fixedOinternal shapes,F frozen6DOF,T3translation only,24updates. T every scan
rotation byte-identical toB/maxchange0,internaldelta<=1.59e-14m.00Farrays exactly
reproduceCV1. No J/prior/calibration/time/membership/point/threshold changes.

TvsB jointATE gains00/05/06 +2.549/-6.334/+16.108%,endpointt +2.813/-18.559/
+55.314%;meanfractionalATE4.107817%<5,t13.189352%,2/3bothpositive.05ATE/t
>5%regressionfail,absoluteharm3.96mm/11.62mm. Rotation/internal/holdoutpass,
holdoutT/B.989300/.984474/.977039. Primaryconjunctionfalse,not safe/systemgain.
F06 improvesATE17.409%,t75.680%,R-.067445deg;blanketRlock loses usefulrotation,
does not protect05translation. Do not build GT-oracleB/F/Tcase selector.

Separate posthoc15conditions/0optimizer calls:fixedBlabels,oracle reference
internal/endpoint substitutions only cost/gradient,no newperformancecandidate.
05costslope towardsreferencet flips +.042115 to-.068461 withreferenceinternals;
fullreferenceposes stillhighercostinall3. Internalshape affectsobjective,
notuniquephysicalcause/GTwrong/calibratedaccuracy. Initialmembership/alias/
dynamics/timing/calibration/referenceconflict remain unresolved. Heldoutresidual
improvement does not calibrateposeimprovement. Explicitcost/FD checks pass.

Stop extraexactCV2steps/axes/scale/hash/density/window/gaterescue orJexpansion.
NextDESIGN_ONLY:same3cases/points,B-versusreference-formed membership crossed
cost/coverage/pointID/rejectedcensus audit,0optimizer,oracle diagnostic only.
No newmembership orcohortfreeze/fulltrajectory executed. Ifmembership doesnot
explainconflict,needverifiedmeasurement/physicalsurfaceevidence orstopobjective.
Alloldstops,seals,09/checkpoint/site/exposure unknowns persist;owneroriginality/
rigorrelaxationpersists,conventionalgeometry credited,no originalbreakthrough.

PreflightH/g1.9540e-14/3.5527e-15,FD8.1950e-9,noop/recovery8.6042e-16/8.8818e-16,
planarblindrank1. Independent48rawdelta1.4211e-14,moments0,explicitgeom5.6342e-13,
selectedrealFD2.0817e-10,metrics8.0616e-14/fullgate. Posthocexplicitcost/FD
1.6249e-13/1.4794e-11. Boundedchecks,no fulloptimizer/rejectedcensus replay.
7successfulstages{total:.6f}s,peakRSS{peak}bytes,allattemptedRSScaptured,noGPU,
1800s/2GiB/512MiBcaps pass;imports/WSLstartup/design/docs/bookkeeping excluded,
notproductionlatency. No CV2 implementationrepair orfailedstages.

BothoriginalHEADs/branches/2and9trackeddirtysets retained;CV1{prior_counts['CV1']}/SMP2{prior_counts['SMP2']}/
SMP1{prior_counts['SMP1']}/MMR0{prior_counts['MMR0']}deliveryidentities,8model/config+opaquecheckpoint unchanged.
Onlynewisolatedhelper/mainmaintenance/docs+mutablehandoffs;no model/checkpointload,
training/RAPinference/GPU/fulltrajectory/officialGTmetricreplacement/acquisition/
install/production/default/backbone/manuscriptedit/commit/Gitsync.

'''
    handoff = '# CV2 handoff\n\n'+header+'\nSee REPORT and NEXT_ROUND_PLAN for interpretation and design-only decision branches.\n'
    (base/'HANDOFF.md').write_text(handoff,encoding='utf-8')
    resource['dossier_bytes_before_audit_seal'] = sum(p.stat().st_size for p in base.rglob('*') if p.is_file())
    resource['artifact_cap_pass'] = resource['dossier_bytes_before_audit_seal'] < 512*2**20
    assert resource['artifact_cap_pass']
    run.save(base/'RESOURCE_AUDIT.json',resource)
    agents = run.old.MAIN/'AGENTS.md'
    title,body = agents.read_text(encoding='utf-8-sig').split('\n',1)
    assert 'Latest owner/execution boundary (2026-10-10, continued)' not in body[:1000]
    agents.write_text(title+'\n\n'+header+body.lstrip('\n'),encoding='utf-8')
    with (run.old.MAIN/'docs/maintenance/2026-10-09/PHASE_RECORD.md').open('a',encoding='utf-8') as stream:
        stream.write('\n## CV2 rotation-protected development cohort;2026-10-10 delivery\n\n'+header)
    entries = [dict(path=str(p.relative_to(base)),sha256=run.sha(p),bytes=p.stat().st_size)
               for p in sorted(base.rglob('*')) if p.is_file()]
    run.save(base/'DELIVERY_SEAL.json',dict(status=status,decision=decision,files=entries,
        scientific_implementation_repair=False,primary_conjunction_pass=False,
        posthoc_oracle_diagnosis_separately_sealed=True,mutable_AGENTS_PHASE_outside_seal=True))
    assert run.cv.previous.check_delivery(base) == len(entries)
    for name,root in prior_roots.items():
        assert run.cv.previous.check_delivery(root) == prior_counts[name]
    size = sum(p.stat().st_size for p in base.rglob('*') if p.is_file())
    assert size < 512*2**20
    print('CV2 closed',decision,len(entries),'files',total,'seconds',peak,'RSS',size,'bytes',flush=True)


if __name__ == '__main__':
    main()
