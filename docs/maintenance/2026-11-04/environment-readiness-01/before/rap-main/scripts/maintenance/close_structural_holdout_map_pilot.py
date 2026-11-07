"""Delivery bookkeeping for validated SMP2; no geometry, GT or optimizer computation."""
import json
import subprocess
from pathlib import Path
import structural_holdout_map_pilot as run


def main():
    frozen = run.verify()
    assert run.read(run.BASE/'bank_validation.json')['passed'] and run.read(run.BASE/'validation.json')['passed']
    assert not (run.BASE/'INCOMPLETE').exists()
    old_smp = run.check_delivery(run.prior.BASE)
    old_mmr = run.check_delivery(run.old.ROOT_BASE)
    audit_root = run.BASE/'revisit-design-audit-01'
    audit_retry = audit_root/'attempt-02'
    checks = []
    for root in (run.BASE, audit_root, audit_retry):
        f = run.read(root/'freeze.json')
        for path, digest in f['files'].items():
            actual = run.sha(path)
            assert actual == digest, path
            checks.append(dict(freeze=str(root/'freeze.json'), path=path, sha256=digest, matches=True))
    seals = []
    for root, filename in ((run.BASE, 'bank_seal.json'), (audit_retry, 'output_seal.json')):
        f = run.read(root/filename)
        for name, digest in f['files'].items():
            path = root/'bank'/name if filename == 'bank_seal.json' else root/name
            assert run.sha(path) == digest
            seals.append(dict(path=str(path), sha256=digest, matches=True))
    audit = run.read(audit_retry/'results.json')
    assert run.read(audit_retry/'validation.json')['passed']
    for row in audit['raw_bindings']:
        assert run.sha(row['path']) == row['sha256']
    old_checks = run.read(run.prior.BASE/'CHECKS.json')
    model = []
    for row in old_checks['model_source_checks']:
        path = run.old.MAIN/row['path']
        assert run.sha(path) == row['sha256']
        model.append(dict(path=row['path'], sha256=row['sha256'], matches=True))
    checkpoint = run.sha(run.old.MAIN/'weights/rap_model_12.ckpt')
    assert checkpoint == old_checks['opaque_checkpoint_sha256']
    repositories = []
    previous = run.read(run.prior.BASE/'REPOSITORY_STATE.json')['repositories']
    for root, expected in zip((run.old.MAIN, run.old.SLAM), previous):
        def git(*args):
            return subprocess.check_output(['git', '-C', str(root), *args], text=True).rstrip('\n')
        state = dict(root=expected['root'], HEAD=git('rev-parse', 'HEAD'), branch=git('branch', '--show-current'),
                     tracked_dirty=git('status', '--porcelain', '--untracked-files=no').splitlines())
        assert state == expected, state
        repositories.append(state)
    result, summary = run.read(run.BASE/'results.json'), run.read(run.BASE/'bank/summary.json')
    logs = run.read(run.BASE/'RESOURCE_LOG.json')
    total = sum(row['wall_s'] for row in logs)
    core = sum(row['wall_s'] for row in logs if not row['stage'].startswith('next_design'))
    peak = max(row['peak_rss_bytes'] for row in logs if row['peak_rss_bytes'] is not None)
    decision = 'NO_MATERIAL_SUPPORT_PRESERVING_LOCAL_GAIN'
    lines = []
    for window, row in result['rows'].items():
        s, p, o = summary[window], row['P'], row['O']
        ratio = s['geometry']['P']['holdout']['scan_balanced_patch_rms_m']/s['geometry']['O']['holdout']['scan_balanced_patch_rms_m']
        lines.append(f"| {window} | {s['train']['patches']}/{s['holdout']['patches']} | {min(s['train']['per_scan_points'])}/{min(s['holdout']['per_scan_points'])} | {o['aligned_position_ate_m']:.6f}->{p['aligned_position_ate_m']:.6f} | {100*p['aligned_ate_gain']:+.3f}% | {100*p['translation_gain']:+.3f}% | {p['rotation_regression_deg']:+.6f} | {ratio:.6f} |")
    report = f'''# SMP2: complete clusters recover support, not a material local gain

Status **VALIDATED_EXPLORATORY_COMPLETE**; decision **{decision}**.
Owner said "不错，继续推进下一轮方案" after the support-preserving next plan.
The one2m complete-patch experiment is executed and closed. It meets all support,
pose validity and safety conditions but misses the prospective5%mean aligned-ATE
gain. No full trajectory, useful system gain or original method is established.

## Results

The same190332retained points in the four MMR0windows participate in unchanged
eligible-plane construction. Full106/132/52/51patches now retain their complete
cross-scan support. One fixed BIG-ENDIAN SHA256 whole-patch split produces the
training/holdout sets below. No alternate hashes, scales, windows or thresholds.
P uses only training patches plus the frozen.10m/.15deg motion regularizer;
24updates. O is the unchanged properly projected E0 input. All4records support
optimization and all4candidate poses are valid.

| Window | Train/test patches | Min train/test points per scan | Local aligned ATE O->P(m) | ATE gain | tRMSE gain | Mean R change(deg) | Holdout RMS P/O |
|---|---:|---:|---:|---:|---:|---:|---:|
{chr(10).join(lines)}

Positive gains are improvements. Three of four ATEs improve; mean fractional
gain **{100*result['gates']['mean_fractional_ate_gain']:.6f}%**, below the fixed5%line.
ATE/tRMSE5%regression guards and rotation.02deg guards all pass. Ratio of mean
holdout patch RMS **{result['gates']['mean_holdout_rms_ratio']:.9f}**, a0.700766%decrease,
passes1.01. The conjunction still fails. The06localATE regresses0.706%; do not
omit it or present the other three as a selected cohort. P maximum corrections
are.015509/.009617/.012464/.005185m and.014030/.007857/.007426/.006252deg.

## What we learned

Whole-patch retention directly removes the support failure found in SMP1.
This is an engineering result, not proof of useful poses. Support repair alone
does not produce material improvement under this local geometry/regularizer.
These data do not identify whether the remaining limit is strong prior, biased
geometry/membership, or redundant single-visit information. No prior-strength,
point-count or membership sweep was performed; no universal BA/geometry stop.

Held-out patch planes are refitted at the reporting pose to measure consistency.
Those complete patches do not enter pose optimization, backtracking or stopping.
Eligibility was nevertheless selected at O with all observed geometry; neighboring
surfaces are correlated and normal spectra differ between splits. This is
structural geometric checking, not independent statistical/physical validation.
The official reference convention and known short-segment caveat are retained.
Full rank/residual reduction cannot resolve physical correspondence, dynamics,
calibration, missing point times, checkpoint/site exposure or09discrepancy.

## Verification and resources

34source/input entries froze before synthetic preflight. Subset compact versus
explicit H/g checks are5.3291e-15/8.8818e-16; unchanged SMP1 solver preflight is
hash-bound. All4prediction records seal before any new numeric reference parsing.
Every retained eligible moment and whole-patch hash/membership/coverage is checked;
moment delta0, explicit geometry2.8953e-13, geometry+prior cost3.2258e-13,
selected training FD2.8005e-10. Independent pose-error reconstruction delta
5.6843e-14 and fractional-gain delta7.1276e-14; complete conjunction reproduced.
Bounded discovery verification, not full optimizer replay or an independent
census of every rejected feature. No scientific implementation failure/repair.

Six core stages **{core:.6f}s**; observed successful-process peak RSS
**{peak}bytes**. Separate next-design audit plus its failure/retry brings recorded
accounting to **{total:.6f}s**. Combined wall1800s/artifact512MiB pass. Successful
observed RSS is below2GiB; failed metadata process did not capture peak RSS, so
combined attempted-process RSS compliance is not fully verified. Original failed
metadata tool wall2.6586884s includes startup/imports; other timings exclude
imports/WSL startup/design/docs/bookkeeping. These are not production latency.

The separate next-design audit originally misread source_frames.json's outer
record as a list (KeyError2378). Original8entryfreeze/source/failure/INCOMPLETE
are retained; attempt-02 repairs only source_frame_ids lookup and validates all
16bindings. No scientific bank, gates, selection or optimizer was changed.

## Next concrete question

The proposed next pilot uses original00accepted record0,2429->3373, two eight-frame
visits with bound raw identities. Compare saved RAP relative alignment, rigid
shared-map refinement and joint internal-pose refinement on identical cross-visit
structures. This introduces actual revisit observations; the completed local
windows did not. It is a design recommendation following a failed material-gain
test, not a conditionally admitted successful method. See NEXT_ROUND_PLAN.md.
No new two-visit coordinates, planes, optimization or reference errors exist yet.

The accepted-loop source contains historical GT fields and was displayed this
turn; prescribed first-record selection does not rank on them. Previously exposed
development remains explicit. Established [BALM](https://arxiv.org/abs/2209.08854)
is eligible under the owner's originality relaxation; no new mechanism claim.

Both original HEADs/branches and2/9tracked dirty sets are preserved. SMP1's
{old_smp}delivery identities and MMR0's{old_mmr}remain unchanged;8model/config hashes
and opaque checkpoint digest match. No checkpoint deserialization, training,
RAP inference, GPU, full trajectory, official metric/GT replacement, acquisition,
production/default/backbone/manuscript edit, commit or Git sync.
'''
    (run.BASE/'REPORT.md').write_text(report, encoding='utf-8')
    status = dict(task='structural-holdout-map-pilot-01', status='VALIDATED_EXPLORATORY_COMPLETE', decision=decision,
                  owner_continuation='不错，继续推进下一轮方案', freeze_entries=len(frozen['files']),
                  research_finding='WHOLE_PATCH_RETENTION_RESTORES_SUPPORT_WITHOUT_MATERIAL_LOCAL_GAIN',
                  supported_windows=4, valid_predictions=4, full_features=[106,132,52,51],
                  train_features=[86,100,40,37], holdout_features=[20,32,12,14], gates=result['gates'],
                  scientific_failures_or_repairs=0, separate_metadata_schema_repair=True,
                  next_revisit_design=dict(status='DESIGN_ONLY', sequence='00', i=2429, j=3373, raw_bindings=16,
                                           coordinate_payload_parsed=False, optimizer_executed=False),
                  full_optimizer_replay=False, full_sequence_metrics=False, checkpoint_deserialized=False,
                  new_model_training_or_RAP_inference=False, old_scientific_outcomes_reclassified=False,
                  original_breakthrough_or_independent_generalization_established=False)
    run.save(run.BASE/'STATUS.json', status)
    run.save(run.BASE/'CHECKS.json', dict(all_match=True, frozen_entry_checks=len(checks), frozen_checks=checks,
             sealed_checks=seals, prior_SMP1_delivery_entries_unchanged=old_smp, prior_MMR0_delivery_entries_unchanged=old_mmr,
             model_source_checks=model, opaque_checkpoint_sha256=checkpoint, checkpoint_deserialized=False,
             new_scientific_INCOMPLETE_absent=True, original_metadata_INCOMPLETE_preserved=(audit_root/'INCOMPLETE').exists()))
    run.save(run.BASE/'REPOSITORY_STATE.json', dict(repositories=repositories, heads_branches_tracked_sets_preserved=True,
             new_algorithm_source=False, reused_frozen_algorithm='RAP-SLAM/scripts/shared_plane_map.py', no_commit_or_sync=True))
    handoff = '''# SMP2 handoff

Read REPORT.md,PROTOCOL.md,NEXT_ROUND_PLAN.md,STATUS.json,freeze/preflight/bank/
bank_seal/bank_validation/results/validation,RESOURCE_AUDIT,CHECKS,REPOSITORY_STATE
and DELIVERY_SEAL. VALIDATED_EXPLORATORY_COMPLETE, no material local gain.
Four complete-cluster2m representations supported; one fixed whole-patch hash;
four valid regularized poses,3/4ATE improvements,mean1.138%<5%. All safety and
structural-holdout checks pass; do not reclassify the conjunction as successful.
Stop extra local steps/hash/prior/window/density rescue of this exact candidate.

Distinct next design: original00accepted array index0,2429->3373, eight keyframes
per visit; raw identities bound, no new coordinate/plane/optimizer/GT-error bank.
Compare saved RAP center, rigid submap geometry refinement and joint internal
poses with two within-visit motion chains. New solver implementation/preflight
is needed; no fabricated temporal-gap edge. See concrete NEXT_ROUND_PLAN.
Historical GT metadata in source was displayed; no ranking on it, exposed data.

Read NEXT_DESIGN_SCOPE and revisit-design-audit-01 original freeze/FAILURE/
AMENDMENT/INCOMPLETE plus attempt-02 freeze/results/validation/seal. Metadata-only
schema repair, scientific SMP2 unchanged. Original failure wall included, failed
process RSS unavailable; do not claim complete attempted RSS verification.
Old source/bank/seal/official metric/GT/09/checkpoint/site/exposure boundaries
remain. Both HEADs/branches and2/9dirty sets retained. Owner originality/rigor
relaxation admits established geometry, not an originality or independent claim.
No model/GPU/training/RAP/system trajectory/acquisition/production edits/Git sync.
'''
    (run.BASE/'HANDOFF.md').write_text(handoff, encoding='utf-8')
    audit_data = dict(recorded_stages=len(logs), scientific_core_stage_wall_s=core, total_accounted_wall_s=total,
                      observed_successful_peak_rss_bytes=peak, gpu_used=False,
                      wall_cap_s=1800, rss_cap_bytes=2*2**30, artifact_cap_bytes=512*2**20,
                      wall_cap_pass=total<=1800, observed_successful_rss_cap_pass=peak<=2*2**30,
                      failed_metadata_peak_rss_unavailable=True, all_attempted_rss_cap_fully_verified=False,
                      failure_wall_included=True, full_runtime_or_production_latency=False,
                      excluded='Imports/WSL startup except original failed metadata external wall; design/docs/bookkeeping')
    audit_data['dossier_bytes_before_closure_seal'] = sum(p.stat().st_size for p in run.BASE.rglob('*') if p.is_file())
    audit_data['artifact_cap_pass'] = audit_data['dossier_bytes_before_closure_seal'] < 512*2**20
    run.save(run.BASE/'RESOURCE_AUDIT.json', audit_data)
    header = f'''Latest owner/exploratory boundary (2026-10-09, continued): owner said
"不错，继续推进下一轮方案". SMP2 structural-holdout-map-pilot-01 is
VALIDATED_EXPLORATORY_COMPLETE;decision NO_MATERIAL_SUPPORT_PRESERVING_LOCAL_GAIN.
Read REPORT,PROTOCOL,NEXT_ROUND_PLAN,HANDOFF,STATUS,RESOURCE_AUDIT,CHECKS,
REPOSITORY_STATE,DELIVERY_SEAL and34entryfreeze/source_snapshot/preflight/bank/
validation; separate NEXT_DESIGN_SCOPE/revisit-design-audit-01 original failure/
AMENDMENT/INCOMPLETE plus attempt-02freeze/results/validation/seal.

Exact MMR0four eight-scan windows/190332retainedpoints/Oinitials;one2m complete
shared-patch representation,unchanged eligible criteria and fixedwhole-patch
SHA256first4BIG-ENDIAN modulo4holdout. Full106/132/52/51patches;train86/100/40/37,
test20/32/12/14. All4support/posesvalid. P unchanged.10m/.15deg engineeringmotion
regularizer/24updates,no G. Allbankseal/explicitpointvalidation precede newGTerrors.
ATE gains+.872/+2.601/+1.784/-.706%,mean1.137760%<5%;3/4positive/all5%ATE/tRMSE
and.02degR safety pass;meanholdoutRMSratio.992992337passes. Conjunction fails.
Complete-cluster support repaired,insufficient material localpose gain;no prior/
split/scale/window/density/step rescue. Not universalgeometry/BA impossibility.

Subsetsynthetic H/g5.3291e-15/8.8818e-16;realmome nts exact,explicitgeometry
2.8953e-13,geometry+prior3.2258e-13,selectedtrainFD2.8005e-10;independentmetrics
5.6843e-14,gain7.1276e-14/fullconjunctionchecked. Bounded discovery verification,
no fulloptimizer/rejectedfeaturecensus replay or scientificimplementationrepair.

Next concrete distinctdesignonly:00 original acceptedloopindex0,2429->3373,
A2378/2384/2391/2398/2405/2413/2423/2429;
B3318/3324/3331/3338/3345/3352/3361/3373.16rawbindingshashed/checked,no new
coordinatepayload/planes/optimizer/GTerrors. Compare savedRAPcenter,rigidmap
refinement andjointinternalposes with14within-visit edges,no inventedgapedge.
Not admission fromfailedSMP2,no actualrevisit/systemexperiment. Originalaccepted
JSON includeshistoricalGTmetadata displayedthisturn;selectorusesprescribedarray
index/whitelist only,exposeddevelopment. Need truecrossvisitfeatureidentity/support,
internaldistortion/priorbalance/bias/localminima/physicalaccuracy stillunresolved.

SeparatemetadataauditKeyError2378 onouterframe-record lookup;original8entryfreeze/
source/failure/INCOMPLETE preserved. Attempt-02 correctssource_frame_ids only,
samecandidate/bindings,independentlychecked. ScientificSMP2 unchanged. Recorded
6corestages{core:.6f}s;8accountedstagesinclmetadatafailure/retry{total:.6f}s,
successfulobservedpeakRSS{peak}bytes;wall1800s/artifacts512MiBpass. Failedmetadata
RSSunmeasured,do notclaimwholeattemptedRSScapverified;successfulRSS<2GiB.
Timers excludeimports/WSLstartup/design/docs exceptfailedexternalwallincludesstartup.

BothoriginalHEADs/branches/2/9trackeddirtysets retained;SMP1{old_smp}/MMR0{old_mmr}delivery
identities,8model/configandopaquecheckpoint unchanged. ReusefrozenRAP-SLAMhelper;
newmainmaintenancescripts/docs+mutablehandoffs only. No model/checkpointload,
training/RAPinference/GPU/fulltrajectory/officialGTmetricreplacement/acquisition/
install/production/default/backbone/manuscriptedit/commit/Gitsync. Alloldstops/
seals and09/checkpoint/site/exposureunknowns persist. Originality/rigorrelaxation
persists;BALMcredited,no independentgain/originalbreakthrough claim.

'''.replace('realmome nts', 'realmoments')
    agents = run.old.MAIN/'AGENTS.md'
    existing = agents.read_text(encoding='utf-8-sig')
    title, body = existing.split('\n', 1)
    agents.write_text(title+'\n\n'+header+body.lstrip('\n'), encoding='utf-8')
    phase = run.old.MAIN/'docs/maintenance/2026-10-09/PHASE_RECORD.md'
    with phase.open('a', encoding='utf-8') as stream:
        stream.write('\n## SMP2 support-preserving structural-holdout continuation\n\n'+header)
    # Mutable AGENTS/PHASE are outside this immutable dossier seal.
    entries = [dict(path=str(p.relative_to(run.BASE)), sha256=run.sha(p), bytes=p.stat().st_size)
               for p in sorted(run.BASE.rglob('*')) if p.is_file()]
    run.save(run.BASE/'DELIVERY_SEAL.json', dict(status='VALIDATED_EXPLORATORY_COMPLETE', decision=decision,
             scientific_failure=False, separate_metadata_failure_preserved=True, files=entries,
             mutable_AGENTS_PHASE_outside_seal=True, tracked_heads_work_preserved=True))
    assert run.check_delivery(run.BASE) == len(entries)
    assert run.check_delivery(run.prior.BASE) == old_smp and run.check_delivery(run.old.ROOT_BASE) == old_mmr
    final_bytes = sum(p.stat().st_size for p in run.BASE.rglob('*') if p.is_file())
    assert final_bytes <= 512*2**20
    print('SMP2 delivered', len(entries), 'dossier files', total, 'accounted seconds', final_bytes, 'bytes', flush=True)


if __name__ == '__main__':
    main()
