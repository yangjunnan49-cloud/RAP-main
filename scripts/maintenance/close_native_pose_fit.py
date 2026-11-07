"""NOC2 final delivery; no further fit or inference."""
from pathlib import Path
import local_motion_common as c
import native_pose_fit as r


def run():
    f=r.check();counts=r.old_deliveries();r.noise_check();r.check_seal(r.BASE/'bank/control')
    control=c.read(r.BASE/'bank/control/fit.json');fixtures=[];validations=[]
    if control['passed']:
        validation=c.read(r.BASE/'validation_synthetic.json');assert validation['passed'];fixtures.append('synthetic')
        if validation['primary_conjunction']: fixtures.append('real')
        for fixture in fixtures:
            v=c.read(r.BASE/f'validation_{fixture}.json');assert v['passed'];validations.append(v)
            vs=c.read(r.BASE/f'validation_{fixture}_seal.json');assert c.sha(r.BASE/f'validation_{fixture}.json')==vs['validation_sha256']
            assert c.sha(r.BASE/f'results_{fixture}_seal.json')==vs['results_seal_sha256']
            rs=c.read(r.BASE/f'results_{fixture}_seal.json');assert c.sha(r.BASE/f'results_{fixture}.json')==rs['results_sha256']
            assert c.sha(r.BASE/'bank'/f'{fixture}_predictions/seal.json')==rs['prediction_seal_sha256']
            r.check_seal(r.BASE/'bank'/f'{fixture}_predictions')
            for arm in ('V','P'): r.check_seal(r.BASE/'bank'/f'{fixture}_{arm}')
        decision=c.read(r.BASE/f'results_{fixtures[-1]}.json')['summary']['decision'];status='VALIDATED_POSE_OBJECTIVE_FIT_COMPLETE'
    else:
        v=c.read(r.BASE/'validation_control.json');assert v['passed'] and not v['control']['passed']
        vs=c.read(r.BASE/'validation_control_seal.json');assert c.sha(r.BASE/'validation_control.json')==vs['validation_sha256']
        assert not (r.BASE/'bank/synthetic_P').exists();validations.append(v)
        status='VALIDATED_PREREQUISITE_STOP';decision='AFFINE_POSE_OBJECTIVE_CONTROL_DID_NOT_FIT'
    repos=r.n.noc.git_state();assert repos==f['repositories']
    rows=r.ledger();assert all(x['success'] for x in rows)
    wall=sum(x['wall_seconds'] for x in rows);rss=max(x['peak_RSS_bytes'] for x in rows)
    ga=max(x['peak_GPU_allocated_bytes'] for x in rows);gr=max(x['peak_GPU_reserved_bytes'] for x in rows)
    assert wall<=1800 and rss<=4*2**30 and max(ga,gr)<=3*2**30
    updates=400+800*len(fixtures);inferences=72*len(fixtures)
    c.save(r.BASE/'RESOURCE_AUDIT.json',dict(stages=rows,combined_recorded_wall_seconds=wall,peak_RSS_bytes=rss,
        peak_GPU_allocated_bytes=ga,peak_GPU_reserved_bytes=gr,all_attempted_RSS_captured=True,all_failed_stages_counted=True,
        limits=f['limits'],all_recorded_caps_pass=True,exclusions=['module imports','WSL startup','design/docs','final identity/seal bookkeeping'],production_latency=False))
    c.save(r.BASE/'REPOSITORY_STATE.json',dict(repositories=repos,heads_branches_tracked_sets_preserved=True,
        sibling_helper_unchanged=True,no_production_default_backbone_source_manuscript_edit=True,no_commit_or_sync=True))
    c.save(r.BASE/'CHECKS.json',dict(freeze_entries=len(f['files']),NOC0_NOC1_delivery_entries_unchanged=counts,
        model_config_checkpoint_identities_unchanged=True,checkpoint_sha256=c.sha(c.MAIN/'weights/rap_model_12.ckpt'),
        trainable_params_per_native_arm=443904,control_params=36,updates=updates,real_windows=int('real' in fixtures),
        nearby_windows=0,native_prediction_inferences=inferences,no_target_teacher_cache_at_inference=True,
        no_full_optimizer_or_census_replay=True,validations=validations))
    table=[];reasons=[];loss_rows=[]
    for fixture in fixtures:
        result=c.read(r.BASE/f'results_{fixture}.json')
        for cell in result['summary']['cells']:
            B,V,P=[cell['arms'][a] for a in ('B','V','P')]
            table.append(f"| {fixture} part{cell['part']} | {B['t']['mean']:.6f}/{V['t']['mean']:.6f}/{P['t']['mean']:.6f} | {B['R']['mean']:.6f}/{V['R']['mean']:.6f}/{P['R']['mean']:.6f} | {cell['comparisons']['B']['joint_nonworse']}/16 / {cell['comparisons']['V']['joint_nonworse']}/16 | {cell['absolute_pass']['P']}/16 | {cell['passed']} |")
            for comp in ('B','V'):
                failed=[k for k,value in cell['comparisons'][comp]['tests'].items() if not value]
                reasons.append(f"- {fixture} part{cell['part']} P vs {comp}: {'failed '+','.join(failed) if failed else 'all comparative checks pass'}; median paired t gain {cell['comparisons'][comp]['paired_t_gain']['median']:.6f}m.")
            if cell['absolute_pass']['P']<12: reasons.append(f"- {fixture} part{cell['part']} P absolute .05m/.2deg capability count below12/16.")
        for arm in ('B','V','P'):
            for role in ('fit','eval'):
                records=[x for x in result['records'] if x['arm']==arm and x['role']==role]
                loss_rows.append(f"| {fixture} {arm} {role} | {sum(x['first_endpoint_pose_loss'] for x in records)/len(records):.9g} | {sum(x['velocity_MSE'] for x in records)/len(records):.9g} |")
    report=f'''# NOC2: fresh-noise relative-pose objective pilot

{status}; decision **{decision}**. Owner said "请按照你下一轮判断推进". This is a distinct objective comparison, not more NOC1 draws or an old stop/gate amendment. Freeze{len(f['files'])} sources/inputs before payload. Same exposed known-transform copied-descriptor task; real reference fixture executed: {int('real' in fixtures)}. {updates} optimizer updates: control400 plus V/P400 each per admitted fixture. No nearby window or trajectory.

## Objective and result

B is frozen initialized native RAP. V/P reset to the exact same NOC0 initialized443904-parameter adapters/output MLP. Both use pure-noise tau1, the same eight predeclared noise arrays cycling400 updates, AdamW1e-4/weight_decay1e-4/clip1. V velocity MSE uses established1024 backward scaling/unscale; P metric relative-pose+target-free nonrigidity loss uses double proper SVD and no scaling. Both receive identical normalized observations. P gradient is through its first raw endpoint only; performance is measured with unchanged production five-step sampling, no detached-rollout gradient claim. First-ten-block cache is target-free and exact full forward. No target/teacher/cache at inference, output selector or ensemble.

The36-parameter affine control learns on normalized measured coordinates with pose loss, identity initialization and no reference initialization. Final control errors: {control['errors']}; fixed .005m/.05deg gate: {control['passed']}. Analytic affine target representation is an oracle mathematical capacity check only. Unequal architecture/capacity prevents native-versus-control efficacy conclusions.

Mean fifth-step t(m)/R(deg) on16 new evaluation noises, separate from eight fit noises:

| Fixture/part | Mean t B/V/P | Mean R B/V/P | P joint nonworse vs B / V | P absolute pass | Full cell |
| --- | --- | --- | --- | --- | --- |
{chr(10).join(table) if table else '| Native stages not admitted | - | - | - | - | - |'}

All selected cells require P absolute .05m/.2deg>=12/16, mean t gain>=10%, median paired t gain>=5mm, rotation mean harm<=.01deg/nonnegative median gain, joint t/R nonworse>=12/16, q90 t harm<=5%/R harm<=.02deg versus both B and V. This asks for incremental pose-objective usefulness under shared new noise coverage. No population test/calibrated safety/scene generalization. V and P differ objective and its explicit .001 shape term; objective alignment versus noise-coverage effects cannot be separately attributed relative to the older different-state NOC0 fit.

{chr(10).join(reasons) if reasons else 'Native comparisons were not admitted, or all listed comparative checks passed; use the full-cell and status fields.'}

## First endpoint losses, not five-step efficacy

| Fixture/arm/noise scope | Mean pose objective | Mean velocity MSE |
| --- | --- | --- |
{chr(10).join(loss_rows) if loss_rows else '| Not admitted | - | - |'}

The saved first/fifth-step per-draw poses/errors and train/evaluation contrast remain in results files. Fitting a tau1 endpoint does not prove fitting intermediate tau states or the final sampler. A failure of the fifth-step conjunction cannot identify a unique state-shift/GT/calibration/capacity cause. A lower first-endpoint objective alone is not promotion evidence.

## Audit, resources and preservation

Objective exact target, known affine representation, common output gauge and three double output-directional finite differences checked before training and repeated independently. Independent Horn geometry versus evaluator SVD reconstructs every saved first/fifth-step pose, error, clean equation, rigid feedback recurrence and metric objective; aggregate code is shared on independent records, while complete pairwise gates are separately duplicated. Selected final native and cache/full forwards and initial gradients replay; full details in validation files. No full400-update AdamW replay, complete repeated census/raw preprocessing/descriptor inference. Scientific prediction banks seal before deriving their new native evaluation errors. All attempted stage RSS/GPU recorded, no failure or implementation repair.

{len(rows)} stages, combined recorded{wall:.6f}s, peak GPU allocated/reserved{ga/2**20:.2f}/{gr/2**20:.2f}MiB, RSS{rss/2**30:.6f}GiB.1800s/3GiB GPU/4GiB RSS/512MiB caps pass; imports/WSL startup/design/docs/final identity/seal bookkeeping excluded, not production latency. Final artifact account in DELIVERY_SEAL.

NOC0 all103 and NOC1 all188 delivery identities, original model/config/checkpoint, sibling helper, both HEADs/branches/two and nine tracked dirty sets unchanged. No acquisition/install, production/default/backbone source/manuscript edit, official GT replacement, new scene/trajectory, commit/Git sync. Old RLP2/map stops, real calibration/timing/reference/checkpoint/site uncertainty persist. Conventional geometry/adaptation credited, no original mechanism or physical/system/generalization claim.
'''
    (r.BASE/'REPORT.md').write_text(report)
    if not control['passed']:
        next_plan='The affine fixed-budget control failed its prerequisite. Stop dependent native/real fits. Next design only: inspect the declared objective/control optimization evidence; analytic representability does not prove fixed-step convergence. No rates/steps/control reinitialization rescue in NOC2, and no native learnability conclusion.'
    elif len(fixtures)==1:
        next_plan='The synthetic native five-step fresh-noise conjunction failed; no real fitting was admitted. Stop this exact pure-noise first-endpoint objective/noise schedule/update count. Compare saved first-step versus five-step errors to judge whether endpoint fitting survives native feedback. Do not promote low pose training loss or prescribe extra sampling steps as a cure. Any subsequent training-state/rollout redesign needs a distinct prospective protocol and numerical/resource feasibility; not implemented/frozen here.'
    else:
        passed=c.read(r.BASE/'results_real.json')['summary']['primary_conjunction']
        next_plan=('Both bounded stages pass. Next DESIGN_ONLY: no-update nearby-window comparison with unchanged strong geometry and frozen native, preserving exposure/capacity/reference limits.' if passed else 'Synthetic admission passed but real development conjunction failed. Stop this exact construction; no nearby/trajectory expansion. Investigate verified physical observations or a distinct measured motion objective without claiming a unique cause.')
    (r.BASE/'NEXT_ROUND_PLAN.md').write_text('# Next decision after NOC2\n\n'+next_plan+'\n')
    (r.BASE/'HANDOFF.md').write_text(f'# NOC2 handoff\n\n{status}; {decision}. Read REPORT/PROTOCOL/OWNER_SCOPE/NEXT_ROUND_PLAN/STATUS/CHECKS/RESOURCE_AUDIT/REPOSITORY_STATE/DELIVERY_SEAL and freeze/source_snapshot/noise/preflight/control/native banks/results/validation seals. Updates{updates}; conditional real windows{int("real" in fixtures)}. No extra rescue follows. Old NOC0/NOC1 identities and both repositories retained; physical/system/originality claims unestablished.\n')
    (r.BASE/'INCOMPLETE').unlink()
    c.status(r.BASE,'complete',status=status,decision=decision,updates=updates,real_windows=int('real' in fixtures),nearby_windows=0)
    size=sum(p.stat().st_size for p in r.BASE.rglob('*') if p.is_file());assert size<=512*2**20
    entries=[dict(path=str(p.relative_to(r.BASE)),sha256=c.sha(p),bytes=p.stat().st_size) for p in sorted(r.BASE.rglob('*')) if p.is_file() and p.name!='DELIVERY_SEAL.json']
    c.save(r.BASE/'DELIVERY_SEAL.json',dict(status=status,decision=decision,files=entries,artifact_bytes_before_seal=size,all_caps_pass=True,recorded_wall_seconds=wall))
    print('NOC2 CLOSED',status,decision,'entries',len(entries),'wall',wall,'bytes',size,flush=True)


if __name__=='__main__': run()
