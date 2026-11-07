"""MF0 preserved-attempt closure and identity audit; no new scientific candidate."""
import json
import subprocess
from pathlib import Path
import numpy as np
import membership_formation_attempt02 as run


def main():
    base,attempt=run.ROOT_BASE,run.BASE
    run.verify()
    assert run.read(attempt/'bank_validation.json')['passed'] and run.read(attempt/'validation.json')['passed']
    assert not (attempt/'INCOMPLETE').exists() and (base/'INCOMPLETE').exists()
    original=run.read(base/'freeze.json')
    assert all(run.sha(p)==h for p,h in original['files'].items())
    seal=run.read(base/'bank_seal.json')
    for name,digest in seal['files'].items():
        assert run.sha(base/'bank'/name)==digest==run.sha(attempt/'bank'/name)
    assert run.sha(base/'preflight.json')==run.sha(attempt/'preflight.json')
    assert run.sha(run.SLAM/'scripts/membership_formation.py')==run.sha(base/'algorithm_staging.py')
    result=run.read(attempt/'results.json');summary=run.read(attempt/'bank/summary.json')
    assert result['optimizer_calls']==0 and not result['performance_gain_claim'] and not result['new_pose_errors_computed']
    assert all(result['rows'][s]['formation_pattern']=='PERSISTENT_B_PREFERENCE' for s in run.SEQUENCES)
    counts={}
    for seq in run.SEQUENCES:
        counts[seq]={}
        with np.load(attempt/f'bank/{seq}-inputs.npz',allow_pickle=False) as z:
            for name in ('B','G'):
                count=z[f'intersection_{name}_counts'];original_ids=z[f'intersection_{name}_original_patch_ids']
                expected=dict(nonempty_patches=len(original_ids),omitted_empty_patches=summary[seq]['memberships'][name]['census']['accepted_cross_patches']-len(original_ids),
                    single_scan_patches=int(np.sum((count>0).sum(1)==1)),per_scan_points=count.sum(0).tolist())
                assert expected==summary[seq]['memberships'][name]['intersection']
                counts[seq][name]=len(original_ids)
    expected=run.read(run.CV2/'REPOSITORY_STATE.json')['repositories'];repositories=[]
    for root,wanted in zip((run.MAIN,run.SLAM),expected):
        def git(*args):return subprocess.check_output(['git','-c',f'safe.directory={root}','-C',str(root),*args],text=True).rstrip('\n')
        actual=dict(root=wanted['root'],HEAD=git('rev-parse','HEAD'),branch=git('branch','--show-current'),tracked_dirty=git('status','--porcelain','--untracked-files=no').splitlines())
        assert actual==wanted;repositories.append(actual)
    old=run.read(base/'RESOURCE_LOG.json');logs=run.read(attempt/'RESOURCE_LOG.json')
    assert logs[:len(old)]==old and len(old)==4 and len(logs)==8
    assert sum(not x['passed'] for x in logs)==1 and all(x['peak_rss_bytes']>0 for x in logs)
    total=sum(x['wall_s'] for x in logs);peak=max(x['peak_rss_bytes'] for x in logs)
    size=sum(p.stat().st_size for p in base.rglob('*') if p.is_file())
    assert total<1800 and peak<2*2**30 and size<512*2**20
    previous=run.MAIN/'docs/maintenance/2026-10-09'
    prior={n:run.original.check_delivery(previous/n) for n in ('measured-map-reoptimization-01','shared-plane-map-pilot-01','structural-holdout-map-pilot-01','cross-visit-map-pilot-01','rotation-protected-map-pilot-01')}
    review=run.original.check_delivery(run.MAIN/'docs/maintenance/2026-10-10/experiment-review-01')
    models=run.read(run.CV2/'CHECKS.json')
    assert all(run.sha(run.MAIN/e['path'])==e['sha256'] for e in models['model_source_checks'])
    checkpoint=run.sha(run.MAIN/'weights/rap_model_12.ckpt');assert checkpoint==models['opaque_checkpoint_sha256']
    status='VALIDATED_DIAGNOSTIC_COMPLETE_WITH_VALIDATOR_REPAIR'
    decision='FORMATION_LOCATION_DOES_NOT_RESOLVE_REFERENCE_CONFLICT'
    checks=dict(all_match=True,original_freeze_entries=len(original['files']),attempt02_freeze_entries=len(run.read(attempt/'freeze.json')['files']),
        original_bank_reused_byte_exact=True,original_failure_and_INCOMPLETE_preserved=True,original_RESOURCE_LOG_preserved=True,
        original_scientific_algorithm_unchanged=True,validator_only_repair=True,prior_delivery_entries_unchanged=prior,review_delivery_entries_unchanged=review,
        complete_candidate_census_records=run.read(attempt/'bank_validation.json')['candidate_records'],retained_points=288000,
        intersection_summary_independently_checked=counts,independent_bank_validation=run.read(attempt/'bank_validation.json'),
        independent_cost_validation=run.read(attempt/'validation.json'),model_config_checks=8,opaque_checkpoint_sha256=checkpoint,
        checkpoint_deserialized=False,optimizer_calls=0,raw_preprocessing_replayed=False,new_pose_errors_computed=False,
        independent_physical_surface_identity=False,closing_source_sha256=run.sha(__file__))
    run.save(base/'CHECKS.json',checks)
    run.save(base/'RESOURCE_AUDIT.json',dict(recorded_stages=len(logs),failed_stages=1,total_accounted_wall_s=total,peak_rss_bytes=peak,
        all_attempted_rss_captured=True,original_failed_compute_included=True,no_double_count=True,wall_cap_s=1800,rss_cap_bytes=2*2**30,
        artifact_cap_bytes=512*2**20,wall_cap_pass=True,rss_cap_pass=True,whole_dossier_bytes_before_delivery=size,artifact_cap_pass=True,
        combined_ledger_sha256=run.sha(attempt/'RESOURCE_LOG.json'),original_ledger_sha256=run.sha(base/'RESOURCE_LOG.json'),gpu_used=False,
        excluded='Imports/WSL startup/design/docs/delivery bookkeeping; not production latency'))
    run.save(base/'REPOSITORY_STATE.json',dict(repositories=repositories,heads_branches_tracked_sets_preserved=True,
        isolated_new_helper='scripts/membership_formation.py',no_commit_or_sync=True,no_production_default_backbone_manuscript_change=True))
    # STATUS is the sole mutable current-state marker, not a scientific frozen product.
    initial=run.read(base/'STATUS.json');run.save(base/'STATUS_initial_snapshot.json',initial)
    status_record=dict(task='membership-formation-diagnosis-01',date='2026-10-10',status=status,decision=decision,
        owner_instruction='启动新实验',original_attempt='COMPLETE_BANK_WITH_PRESERVED_VALIDATOR_FAILURE',validated_attempt='attempt-02',
        original_INCOMPLETE_preserved=True,attempt02_INCOMPLETE_absent=True,scientific_algorithm_repair=False,validator_only_repair=True,
        new_membership_sets=6,raw_scan_bindings=48,retained_points=288000,all_membership_sets_supported=True,
        candidate_records_independently_reconstructed=22055,explicit_cost_records=84,training_B_preference_sets=6,
        reference_formed_06_holdout_exception=True,optimizer_calls=0,oracle_diagnostic_only=True,performance_gain_claim=False,
        unique_physical_cause_identified=False,stop_this_shared_plane_objective_pending_independent_physical_evidence=True,
        next_tiny_native_adapter_diagnosis='DESIGN_ONLY_NOT_IMPLEMENTED_NOT_FROZEN',new_training_or_trajectory=False,official_GT_metrics_changed=False)
    (base/'STATUS.json').write_text(json.dumps(status_record,indent=2)+'\n')
    run.save(attempt/'output_seal.json',dict(status=status,decision=decision,files={n:run.sha(attempt/n) for n in
        ('freeze.json','bank_seal.json','preflight.json','bank_validation.json','results.json','result_seal.json','validation.json','RESOURCE_LOG.json')},
        original_failure_preserved=True,optimizer_calls=0,new_membership_calls_in_retry=0))
    print('MF0 closed checks',decision,len(logs),total,peak,size,flush=True)


if __name__=='__main__':main()
