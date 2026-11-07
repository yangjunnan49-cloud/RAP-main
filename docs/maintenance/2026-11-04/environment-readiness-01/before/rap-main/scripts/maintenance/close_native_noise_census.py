"""NOC1 delivery/resource/repository closure; no additional inference."""
import importlib.util
from pathlib import Path
import local_motion_common as c
spec=importlib.util.spec_from_file_location('noc1_close',Path(__file__).with_name('native_noise_census.py'))
n=importlib.util.module_from_spec(spec);spec.loader.exec_module(n)


def run():
    f=n.check();n.check_noise();n.check_predictions();old_count=n.check_old_delivery()
    v=c.read(n.BASE/'validation.json');assert v['passed']
    seal=c.read(n.BASE/'validation_seal.json');assert c.sha(n.BASE/'validation.json')==seal['validation_sha256']
    assert c.sha(n.BASE/'results_seal.json')==seal['results_seal_sha256'] and c.sha(n.BASE/'freeze.json')==seal['freeze_sha256']
    rs=c.read(n.BASE/'results_seal.json');assert c.sha(n.BASE/'results.json')==rs['results_sha256']
    assert c.sha(n.BASE/'prediction_seal.json')==rs['prediction_seal_sha256']
    assert c.sha(n.BASE/'diagnosis_seal.json')==rs['diagnosis_seal_sha256']
    ds=c.read(n.BASE/'diagnosis_seal.json');assert c.sha(n.BASE/'diagnosis.json')==ds['manifest_sha256']
    for p,h in ds['files'].items(): assert c.sha(n.BASE/p)==h,p
    result=c.read(n.BASE/'results.json');s=result['summary'];assert not (n.BASE/'INCOMPLETE').exists()
    repos=n.noc.git_state();assert repos==f['repositories']
    rows=n.ledger();wall=sum(x['wall_seconds'] for x in rows);rss=max(x['peak_RSS_bytes'] for x in rows)
    failed=[x for x in rows if not x['success']]
    assert len(failed)==1 and failed[0]['stage']=='validation' and 'FileNotFoundError' in failed[0]['error']
    assert (n.BASE/'FAILURE_validation.json').is_file() and (n.BASE/'EXECUTION_RETRY_NOTE.md').is_file()
    gpu_a=max(x['peak_GPU_allocated_bytes'] for x in rows);gpu_r=max(x['peak_GPU_reserved_bytes'] for x in rows)
    assert wall<=900 and rss<=4*2**30 and max(gpu_a,gpu_r)<=3*2**30
    c.save(n.BASE/'RESOURCE_AUDIT.json',dict(stages=rows,combined_recorded_wall_seconds=wall,peak_RSS_bytes=rss,
        peak_GPU_allocated_bytes=gpu_a,peak_GPU_reserved_bytes=gpu_r,all_attempted_RSS_captured=True,
        all_failed_stages_counted=True,limits=f['limits'],recorded_caps_pass=True,
        exclusions=['module imports','WSL startup','design/docs','final identity/seal bookkeeping'],production_latency=False))
    c.save(n.BASE/'REPOSITORY_STATE.json',dict(repositories=repos,heads_branches_tracked_sets_preserved=True,
        reused_sibling_helper_unchanged=True,no_commit_or_sync=True,no_production_default_backbone_source_or_manuscript_edit=True))
    c.save(n.BASE/'CHECKS.json',dict(freeze_entries=len(f['files']),NOC0_delivery_entries_unchanged=old_count,
        NOC0_original_failure_and_all_banks_preserved=True,original_model_config_and_checkpoint_identities_match=True,
        checkpoint_sha256=c.sha(c.MAIN/'weights/rap_model_12.ckpt'),strict_weights_only_RAP344_keys=True,
        descriptor_checkpoint_not_loaded=True,all_existing_fitted_parameters_frozen=True,optimizer_updates=0,
        exact_old_reference_native_replays=8,new_noise_draws=16,reference_draws_excluded=2,nearby_windows_executed=0,
        preserved_execution_order_failures=len(failed),same_frozen_validator_retry=True,implementation_repairs=0,
        no_GT_or_teacher_state_in_native_inference=True,independent_validation=v))
    native_table=[];diag_table=[];ref_table=[];reason=[]
    for cell in s['cells']:
        B,A=cell['B'],cell['A'];label=f"{cell['fixture']} part{cell['part']}"
        native_table.append(f"| {label} | {B['t']['mean']:.6f} / {A['t']['mean']:.6f} | {B['R']['mean']:.6f} / {A['R']['mean']:.6f} | {B['t']['q90']:.6f} / {A['t']['q90']:.6f} | {B['R']['q90']:.6f} / {A['R']['q90']:.6f} | {cell['joint_nonworse']}/16 | {cell['A_absolute_pass']}/16 | {cell['passed']} |")
        da,db=cell['secondary']['A'],cell['secondary']['B']
        diag_table.append(f"| {label} | {db['teacher_mean_MSE']['mean']:.9g} / {da['teacher_mean_MSE']['mean']:.9g} | {db['teacher_native_final_t_gap']['mean']:.6f} / {da['teacher_native_final_t_gap']['mean']:.6f} | {da['teacher_loss_native_t_spearman']} | {da['rigidity_native_t_spearman']} |")
        failed=[k for k,val in cell['tests'].items() if not val]
        if failed: reason.append(f"- {label}: failed {'/'.join(failed)}; median paired t/R gain {cell['paired_t_gain']['median']:.6f}m/{cell['paired_R_gain']['median']:.6f}deg.")
        for ref in cell['references']:
            if ref['arm']=='A': ref_table.append(f"| {label} {ref['name']} | {ref['errors']['t_m']:.6f} | {ref['errors']['R_deg']:.6f} | {100*ref['t_fresh_empirical_percentile']:.2f}% | {100*ref['R_fresh_empirical_percentile']:.2f}% |")
    status='VALIDATED_ZERO_UPDATE_NOISE_CENSUS_COMPLETE_WITH_EXECUTION_RETRY'
    c.status(n.BASE,'complete',status=status,decision=s['decision'],primary_conjunction=s['primary_conjunction'],
        optimizer_updates=0,nearby_windows_executed=0,native_inferences=72,teacher_conditions=72,
        no_independent_generalization_or_system_claim=True)
    report=f'''# NOC1: native noise robustness census

{status}; decision **{s['decision']}**. Owner said "探索并且执行下一轮" after NOC0. New fixed16-draw census and separate oracle teacher diagnosis completed, zero optimizer calls. Primary conjunction: **{s['primary_conjunction']}**. This is conditional evidence on the same two exposed tasks, not new-scene transfer or system performance.

## Fresh-noise result

B is frozen native RAP with initialized zero-B adapters; A is the unchanged NOC0 final400-update native adapter for each fixture. All16 fresh CUDA noises are predeclared BIG-ENDIAN SHA256-derived seeds and paired identically across B/A and fixtures. Original training noise850873755 and old unseen20261011 are separately repeated and excluded from aggregates. No best-noise/arm selector or pose ensemble. Quantiles use linear interpolation; t metres, R degrees; joint signs require both t and R nonworse within a draw.

| Fixture/part | Mean t B/A | Mean R B/A | q90 t B/A | q90 R B/A | Joint nonworse A | A absolute .05m/.2deg pass | Full cell gate |
| --- | --- | --- | --- | --- | --- | --- | --- |
{chr(10).join(native_table)}

The prospective cell gate requires mean t gain>=10%, paired median t gain>=5mm, mean R harm<=.01deg with nonnegative paired median R gain, joint nonworse>=12/16, q90 t harm<=5% and q90 R harm<=.02deg. All four cells must pass. This is an engineering screening criterion, not a retroactive NOC0 or historical gate amendment, calibrated safety bound or population test.

{chr(10).join(reason) if reason else 'All four prospective cells passed; this supports designing nearby-window evaluation only.'}

All four mean t and R errors improve and all q90 guards pass. Only real part2 passes its complete cell gate. The joint t/R nonworse counts9/11/5/12 show why these partial average gains do not establish consistent per-draw improvement. Synthetic part1 mean t gain9.736% narrowly misses10%; real part1 mean t gain6.447% and paired median4.142mm miss their thresholds. Do not describe this as universal adaptation failure or a tail regression.

## Was the original training noise representative?

Empirical percentile is the fraction of16 fresh errors <=the old reference error, lower is better. These ranks do not treat the old draw as a fresh independent test or quantify a physical confidence interval.

| Fitted A reference | t(m) | R(deg) | t fresh percentile | R fresh percentile |
| --- | --- | --- | --- | --- |
{chr(10).join(ref_table)}

Both old reference noises reproduce NOC0 native raw states/endpoints/velocities byte-exactly for all B/A/fixture combinations (eight reference inferences). Their unusual or typical ranks are diagnostics; no unique memorization/noise cause, reference correctness, checkpoint exposure or physical truth is inferred.

## Training state versus actual inference

Teacher-state diagnosis follows the complete prediction seal, uses old target-derived coordinates only in this labelled oracle scope, and is not a new performance candidate. It runs five tau values at each fixed weight/noise without gradients. Loss is normalized pointwise velocity MSE over all three parts, therefore shared by the two part rows within each fixture. The t gap is actual native fifth-step error minus teacher tau.2 error; the correlation columns describe fitted A on16 fresh draws, not independent efficacy or a selector.

| Fixture/part | Teacher mean MSE B/A | Native-minus-teacher final t gap B/A(m) | A teacher loss/native t Spearman | A rigidity/native t Spearman |
| --- | --- | --- | --- | --- |
{chr(10).join(diag_table)}

Synthetic A teacher MSE rises from1.16112e-5 to2.59428e-5 while both native mean pose errors improve; real A MSE falls from1.23504e-4 to2.88228e-5 without a full motion conjunction. Teacher velocity MSE is therefore not a sufficient proxy for this motion screen. A mean final native-minus-teacher t gaps are+4.942/+1.703/-4.554/+16.710mm; these small and mixed-sign gaps do not establish actual-state distribution shift as the dominant explanation. Teacher-state errors themselves remain substantial. A distinct pose-aligned, noise-varying fitting design is a hypothesis motivated by these mismatches, not a diagnosed causal cure.

All full per-draw errors, one/five-step outputs, teacher tau metrics, per-arm losses, min/max/std/median/q90, paired changes, joint signs, reference ranks and120-dependent-pair pose-dispersion summaries are retained in results.json. Rigidity is target-free raw endpoint distance to its own per-part best rigid condition fit, averaged over five steps in metric units; it does not calibrate pose errors. Correlation is descriptive; no causal, residual-to-accuracy or confidence claim. No pose mean/ensemble candidate was produced. The old simple direct controls are byte-bound contextual outputs: unequal architecture/init/capacity and synthetic copied descriptors prevent RAP-superiority conclusions.

## Validation and resources

All72 native traces independently reconstruct using Horn geometry versus evaluator SVD, first/fifth-step poses, every raw clean equation and rigid feedback recurrence, teacher clean algebra, all pose/MSE/rigidity metrics and aggregate fields. The statistics aggregation code is shared but run on independently reconstructed Horn records; the full gate is independently duplicated.18 noise draws independently regenerate exactly, eight first/last fresh full native inferences and40 teacher forward calls reproduce byte-exactly. Max pose delta {v['max_pose_delta']:.3g}, metric {v['max_metric_delta']:.3g}, recurrence {v['max_recurrence_delta']:.3g}, rigidity {v['max_rigidity_delta']:.3g}, teacher algebra {v['max_teacher_algebra_delta']:.3g}, aggregate {v['max_aggregate_delta']:.3g}. No full repeated72-inference census, optimizer replay, raw preprocessing or descriptor inference.

One validation attempt was started before the still-running evaluation completed its results seal. It stopped with FileNotFoundError before numerical checks. FAILURE_validation.json, its resource entry and EXECUTION_RETRY_NOTE.md are preserved. The same frozen validator passed after evaluation completed; no implementation, weights, noise, scientific outputs, gate or cap changed. This is an execution-order retry, not an implementation repair or a failed scientific candidate.

{len(rows)} recorded stages total {wall:.6f}s, peak allocated/reserved GPU {gpu_a/2**20:.2f}/{gpu_r/2**20:.2f}MiB, peak RSS {rss/2**30:.6f}GiB.900s/3GiB GPU/4GiB RSS/512MiB whole-dossier caps pass, all attempted RSS recorded. Imports/WSL startup/design/docs/final identity/seal bookkeeping excluded, not production latency. Artifact bytes are finalized in DELIVERY_SEAL.

## Decision boundary and preservation

{s['decision']}. Do not turn partial average improvements, teacher losses or lower noise dispersion into a system/physical/independent-generalization claim. Frozen checkpoint training/site membership, real reference/physical time/calibration and all previous uncertainties remain. NOC0 all103 delivery identities, its original failure/retry/validator/provenance notes and source/parameter arrays match.138 source/input freeze entries; all original model/config/checkpoint identities retained. Both HEADs/branches/two and nine tracked dirty sets preserved, sibling helper unchanged. No new training, window, acquisition/install, production/default/backbone-source/manuscript edit, official metric replacement, full trajectory, commit or Git sync. Prior map/RLP2 stops and originality exploration relaxation persist; no original mechanism.
'''
    (n.BASE/'REPORT.md').write_text(report)
    if s['primary_conjunction']:
        plan='''# Next decision after NOC1

The fixed fresh-noise engineering conjunction passed on two exposed tasks, zero updates. This supports the next DESIGN_ONLY scope: a predeclared nearby-window evaluation with no updates, identical measured input/control bindings, frozen native versus saved adapter versus unchanged strong geometry, no teacher states or target inputs at inference. Nearby scan/site overlap and old checkpoint membership must remain explicit. Freeze windows, noise and resources before execution; all selected windows remain regardless of outcome. This is a transfer question, not more fitting or a full trajectory. No nearby inference, new bank or protocol freeze executed by this plan. No system/generalization/original mechanism claim follows from the current census.
'''
    else:
        plan='''# Next decision after NOC1

The predeclared fresh-noise conjunction failed. Preserve all partial improvements and adverse cells rather than call the entire adapter useless or universally unlearnable. Stop more draws/seeds/steps/rates/checkpoints/window selection on this exact census and stop automatic expansion of the NOC0 single-fixed-noise velocity-MSE fit into nearby scenes or full trajectories. No extra fitting follows from this result.

Next DESIGN_ONLY: prioritize a metric/gauge-invariant relative-pose fitting objective with predeclared noise variation, then measure its relation to the actual native sampler. Synthetic teacher MSE worsens while pose averages improve, and real teacher MSE improves without consistent motion improvement; those observations justify checking objective alignment. The final teacher/native t gaps are only+4.942/+1.703/-4.554/+16.710mm on average, so this census does not establish a large state-distribution gap as the primary bottleneck. Do not simply prescribe more Euler steps, teacher calls or state matching as a cure.

Fresh-noise coverage would be an explicit distinct training objective, not hidden rescue or an old gate amendment. Keep a tiny known-transform task first, a verified simple affine clean-point capacity control and frozen native. Freeze objective, noise schedule, capacity controls, outputs, safety gates and a new resource ceiling before any new updates. Establish selected gradients/numerical feasibility in an isolated path; production sampler's detached returns cannot be treated as a differentiable rollout. Reference-derived states never become inference observations. Only a prospective fresh-noise motion conjunction would justify a real-window stage. Failure would stop that exact new construction; unresolved physical observations require independent evidence. No new objective/training wrapper/optimizer/protocol is implemented or frozen here.

If a later distinct fitting protocol establishes fresh-noise motion fitting, only then design a no-update nearby-window comparison against the strong unchanged geometry frontend. Old RLP2/exact shared-plane stops and all source/seal/physical-reference/site caveats remain. Conventional native adaptation is credited; no original-method or system claim.
'''
    (n.BASE/'NEXT_ROUND_PLAN.md').write_text(plan)
    (n.BASE/'HANDOFF.md').write_text(f'''# NOC1 handoff

{status}; {s['decision']}. Read REPORT/PROTOCOL/OWNER_SCOPE/NEXT_ROUND_PLAN/STATUS/CHECKS/RESOURCE_AUDIT/REPOSITORY_STATE/DELIVERY_SEAL/EXECUTION_RETRY_NOTE;138-entry freeze/source_snapshot/noise_seal/predictions/prediction_seal/separate diagnosis/seal/results/seal/validation/seal.16 fresh paired draws plus two excluded old references;72 native traces and72 teacher conditions,0 optimizers/nearby windows. Four mean t/R improvements, only real part2 passes full cell gate; joint signs9/11/5/12. One premature validation FileNotFoundError retained; same frozen validator passes after evaluation, no implementation repair. Old NOC0 all103 identities and both repo states preserved. Next plan is design only, prioritize pose-objective alignment with declared noise variation, not a claimed state-shift cure or automatic learning. No full census replay/calibrated safety/physical accuracy/system/originality claim.
''')
    bytes_=sum(p.stat().st_size for p in n.BASE.rglob('*') if p.is_file());assert bytes_<=512*2**20
    entries=[dict(path=str(p.relative_to(n.BASE)),sha256=c.sha(p),bytes=p.stat().st_size)
        for p in sorted(n.BASE.rglob('*')) if p.is_file() and p.name!='DELIVERY_SEAL.json']
    c.save(n.BASE/'DELIVERY_SEAL.json',dict(status=status,decision=s['decision'],files=entries,artifact_bytes_before_seal=bytes_,
        recorded_wall_seconds=wall,all_caps_pass=True))
    print('NOC1 CLOSED',s['decision'],'sealed',len(entries),'bytes',bytes_,'wall',wall,flush=True)


if __name__=='__main__': run()
