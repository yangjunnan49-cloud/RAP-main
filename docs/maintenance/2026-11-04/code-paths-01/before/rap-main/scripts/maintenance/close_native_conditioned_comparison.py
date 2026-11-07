"""Close only independently validated NOC4 work and preserve historical identities."""
import native_conditioned_comparison as r
c=r.c


def close():
    f=r.check();counts=r.old_deliveries();r.noise_check();r.check_seal(r.BASE/'preflight')
    preflight=c.read(r.BASE/'preflight/probes.json');pv=c.read(r.BASE/'validation_preflight.json');assert pv['passed']
    pvs=c.read(r.BASE/'validation_preflight_seal.json');assert c.sha(r.BASE/'validation_preflight.json')==pvs['validation_sha256']
    assert c.sha(r.BASE/'preflight/seal.json')==pvs['preflight_seal_sha256']
    fitted=preflight['passed'];table=[];first=[];reasons=[]
    if fitted:
        validation=c.read(r.BASE/'validation_synthetic.json');assert validation['passed']
        vs=c.read(r.BASE/'validation_synthetic_seal.json');assert c.sha(r.BASE/'validation_synthetic.json')==vs['validation_sha256']
        assert c.sha(r.BASE/'results_synthetic_seal.json')==vs['results_seal_sha256']
        result=c.read(r.BASE/'results_synthetic.json');rs=c.read(r.BASE/'results_synthetic_seal.json')
        assert c.sha(r.BASE/'results_synthetic.json')==rs['results_sha256']
        r.check_seal(r.BASE/'bank/synthetic_predictions')
        status='VALIDATED_NATIVE_COMPARISON_COMPLETE';decision=result['summary']['decision']
        for cell in result['summary']['cells']:
            table.append(f"| {cell['part']} | "+' | '.join(f"{cell['arms'][a]['t']['mean']:.6f} / {cell['arms'][a]['R']['mean']:.6f}" for a in ('B','V','P'))+
                f" | {cell['comparisons']['B']['joint_nonworse']} / {cell['comparisons']['V']['joint_nonworse']} | {cell['absolute_pass']['P']} | {cell['passed']} |")
            for comp in ('B','V'):
                failures=[k for k,v in cell['comparisons'][comp]['tests'].items() if not v]
                reasons.append(f"- Part{cell['part']} P versus{comp}: failed {', '.join(failures) if failures else 'none'}.")
        for arm in ('B','V','P'):
            for role in ('fit','eval'):
                a=[x for x in result['records'] if x['arm']==arm and x['role']==role]
                first.append(f"| {arm} {role} | {sum(x['first_endpoint_pose_loss'] for x in a)/len(a):.9g} | {sum(x['velocity_MSE'] for x in a)/len(a):.9g} |")
        next_plan=('Synthetic conjunction passes. Next DESIGN_ONLY: specify a single existing real development fixture comparison with physical/reference caveats; no such fit or protocol follows automatically.'
            if result['summary']['primary_conjunction'] else
            'Stop this exact pure-tau1 first-endpoint construction, including its rate/steps/scales/noises/gates. Next DESIGN_ONLY: compare saved first-versus-fifth-step results and fit-versus-held-out draws to determine whether a distinct training-state or rollout proposal is justified. Neither lower endpoint loss nor this negative gate identifies a unique cause. No extra fit, real/nearby/trajectory expansion, or production promotion.')
    else:
        assert not (r.BASE/'bank/synthetic_V').exists() and not (r.BASE/'bank/synthetic_P').exists()
        validation=pv;status='VALIDATED_NATIVE_NUMERICAL_PREREQUISITE_STOP';decision='NATIVE_PARAMETER_STEP_PREFLIGHT_DID_NOT_PASS'
        next_plan='Stop this declared native optimizer/backward-scale construction. Next DESIGN_ONLY: inspect retained gradient/FD/actual-step evidence and identify the specific failed numerical gates before designing a distinct numerical policy. No factor/rate/step rescue or fitted/native/real expansion follows.'
    repos=r.n.noc.git_state();assert repos==f['repositories'];rows=r.ledger();assert all(x['success'] for x in rows)
    wall=sum(x['wall_seconds'] for x in rows);rss=max(x['peak_RSS_bytes'] for x in rows)
    ga=max(x['peak_GPU_allocated_bytes'] for x in rows);gr=max(x['peak_GPU_reserved_bytes'] for x in rows)
    assert wall<=1800 and rss<=4*2**30 and max(ga,gr)<=3*2**30
    c.save(r.BASE/'RESOURCE_AUDIT.json',dict(stages=rows,combined_recorded_wall_seconds=wall,peak_RSS_bytes=rss,
        peak_GPU_allocated_bytes=ga,peak_GPU_reserved_bytes=gr,all_attempted_RSS_captured=True,all_failed_stages_counted=True,
        limits=f['limits'],caps_pass=True,exclusions=['module imports','WSL startup','design/docs','final identity/seal bookkeeping'],production_latency=False))
    c.save(r.BASE/'REPOSITORY_STATE.json',dict(repositories=repos,heads_branches_tracked_sets_preserved=True,sibling_helpers_unchanged=True,no_commit_or_sync=True))
    c.save(r.BASE/'CHECKS.json',dict(freeze_entries=len(f['files']),old_delivery_entries_unchanged=counts,
        preflight_optimizer_calls=2,validation_probe_optimizer_calls=2,retained_probe_updates=0,fit_updates=800 if fitted else 0,
        parameters_per_arm=443904,native_prediction_traces=72 if fitted else 0,real_windows=0,nearby_windows=0,
        no_target_cache_at_inference=True,model_config_checkpoint_identities_unchanged=True,validation_preflight=pv,validation=validation))
    probes=[]
    for row in preflight['records']:
        probes.append(f"| {row['arm']} | {row['loss_before']:.9g} → {row['loss_after']:.9g} | {row['gradient_norm']:.9g} | {row['clip1_counterfactual']:.9g} | {row['parameter_changes']['max_abs']:.9g} | {row['passed']} |")
    report=f'''# NOC4: same-capacity native objective comparison

{status}; decision **{decision}**. Owner asked to continue the prior positive signal. NOC3 established fixed-anchor float64 rigid-control feasibility. This new round checks neural numerical feasibility and, only after an independently audited prerequisite, synthetic fresh-noise native sampling. No old stop or scientific result was rewritten.

## Numerical prerequisite

Same original443904 trainables/initialization in V/P. Fixed AdamW1e-4, betas(.9,.999), eps1e-8, no weight decay/clipping; backward multipliers V1024/P1/1024 are divided out before stepping. Relative-pose P objective, metric units and double proper SVD are unchanged. The first-ten-block cache is observation/noise-only and equals full forward. Two actual one-step optimizer probes and two validation probe steps have zero retained updates, with parameters restored byte-exactly and optimizer state discarded before training. Do not describe these as zero optimizer calls.

| Arm | Probe loss before → after | Raw gradient norm | Clip1 counterfactual multiplier | Max actual parameter change | Full preflight |
| --- | --- | --- | --- | --- | --- |
{chr(10).join(probes)}

All individual gradients/parameters/optimizer states are retained in preflight, including zero/nonzero counts, output-weight FD, B/MLP activation and actual parameter changes. A is expected inactive at B0. Independent full-forward probe replay is byte-exact; NumPy first-Adam-step maximum difference{pv['NumPy_first_Adam_step_max_delta']:.9g}; independent Horn objective maximum difference{pv['independent_Horn_objective_max_delta']:.9g}. This bounded numerical result does not establish convergence or a unique cause of NOC2's affine failure.

## Final five-step fresh-noise result

Fit updates:{800 if fitted else 0}. Both arms reset from original initialized arrays, use identical eight pure-noise tau1 inputs and400 fixed updates. Final400 only; no checkpoint/draw/arm selector.72 B/V/P traces across8 fit and16 held-out draws seal before deriving new native performance errors. Unchanged actual five-step sampler receives observations/noise only; it has no target/cache. No real window follows.

Mean fifth-step t(m)/R(deg) on16 held-out draws:

| Moving part | B mean t / R | V mean t / R | P mean t / R | P joint nonworse vs B / V (of16) | P absolute passes (of16) | Full cell |
| --- | --- | --- | --- | --- | --- | --- |
{chr(10).join(table) if table else '| Not admitted | - | - | - | - | - | - |'}

All cells require P absolute .05m/.2deg>=12/16 and the complete mean/median/joint/tail comparative conjunction against BOTH B and V. Full details remain in results/protocol; gates are fixed prospectively. Partial gains or low loss cannot replace the conjunction.

{chr(10).join(reasons)}

First-endpoint objective and velocity MSE, descriptive only:

| Arm / noise scope | Mean pose objective | Mean velocity MSE |
| --- | --- | --- |
{chr(10).join(first) if first else '| Not admitted | - | - |'}

Training differentiates only the first tau1 raw endpoint, not a five-step rollout. Lower first-endpoint loss does not guarantee intermediate-state/final-sampler behavior. This exposed same-scan copied-descriptor synthetic task is reference-supervised development, not physical accuracy, unseen-scene generalization, system improvement or a new original mechanism. No unique gauge/precision/clipping/state-distribution/capacity explanation follows from these comparisons.

## Validation, resources and preservation

Independent preflight full gradient/probe state replay and NumPy first-step formula; all mathematical checks repeated. {'All72 Horn traces/first-final poses/metrics/objectives/recurrences independently reconstructed; all24 noise replays and six selected native five-step replays byte-exact, four cache/full checks; complete comparative and absolute gates duplicated. Aggregate code is shared on independently reconstructed records. No full400-update optimizer/raw-preprocessing/descriptor or full72 native inference replay.' if fitted else 'No training/native prediction gate was executed after the prerequisite stop.'}

{len(rows)} successful execution/audit stages,{wall:.6f}s combined recorded wall, peak GPU allocated/reserved{ga}/{gr}bytes, RSS{rss}bytes.1800s/3GiB GPU/4GiB RSS/512MiB caps pass; all attempted RSS captured. Imports/WSL startup/design/docs/final identity/seal bookkeeping excluded, not production latency. Final whole-dossier size in DELIVERY_SEAL.

NOC0/NOC1/NOC2 original/corrected/NOC3 delivery103/188/53/5/37 entries unchanged. Original model/config/checkpoint/sibling helpers, both HEADs/branches/two and nine tracked dirty sets retained. Only isolated main maintenance/docs/mutable handoffs. No acquisition/install, production/default/backbone-source/manuscript edits, officialGT replacement, real/nearby/trajectory, commit/Git sync. All prior physical/reference/time/site/checkpoint unknowns and stops/seals persist. Conventional adaptation and geometry credited.
'''
    (r.BASE/'REPORT.md').write_text(report)
    (r.BASE/'NEXT_ROUND_PLAN.md').write_text('# Next decision after NOC4\n\n'+next_plan+'\n')
    (r.BASE/'HANDOFF.md').write_text(f'# NOC4 handoff\n\n{status}; {decision}. Read REPORT/PROTOCOL/OWNER_SCOPE/NEXT_ROUND_PLAN/STATUS/CHECKS/RESOURCE_AUDIT/REPOSITORY_STATE/DELIVERY_SEAL and freeze/source_snapshot/noise/preflight/replay/validation/banks/results/seals. Two original and two validation probe optimizer calls, zero retained probe updates; fit updates{800 if fitted else 0}. No real/nearby/trajectory expansion. Old identities/stops/unknowns retained.\n')
    c.status(r.BASE,'complete',status=status,decision=decision,fit_updates=800 if fitted else 0,probe_calls=4,retained_probe_updates=0,real_windows=0)
    (r.BASE/'INCOMPLETE').unlink()
    size=sum(p.stat().st_size for p in r.BASE.rglob('*') if p.is_file());assert size<512*2**20
    entries=[dict(path=str(p.relative_to(r.BASE)),sha256=c.sha(p),bytes=p.stat().st_size)
        for p in sorted(r.BASE.rglob('*')) if p.is_file() and p.name!='DELIVERY_SEAL.json']
    c.save(r.BASE/'DELIVERY_SEAL.json',dict(status=status,decision=decision,files=entries,
        artifact_bytes_before_seal=size,recorded_wall_seconds=wall,caps_pass=True))
    print('NOC4 CLOSED',status,decision,'delivery entries',len(entries),'wall',wall,'bytes',size,flush=True)


if __name__=='__main__': close()
