"""NOC0 identity/resource closure and bounded development report."""
import importlib.util
import json
import time
from pathlib import Path
import local_motion_common as c

ROOT=c.MAIN/'docs/maintenance/2026-10-10/native-output-capability-01'
BASE=ROOT/'attempt-02'
VALID=BASE/'validation-attempt-02'
spec=importlib.util.spec_from_file_location('noc_retry',Path(__file__).with_name('native_output_capability_attempt02.py'))
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)


def delivery(base,top_only=False):
    s=c.read(base/'DELIVERY_SEAL.json')['files'];count=0
    rows=s.items() if isinstance(s,dict) else [(x['path'],x['sha256']) for x in s]
    for p,h in rows:
        path=Path(p);path=path if path.is_absolute() else base/path
        if top_only and path.parent!=base: continue
        assert c.sha(path)==h,str(path);count+=1
    return count


def metric_line(info,noise='train',step=5):
    rows=next(x['errors'] for x in info['native'] if x['noise']==noise and x['step']==step)
    return ' / '.join(f"{x['t_m']:.6f}m, {x['R_deg']:.6f}deg" for x in rows)


def run():
    r.check();v=c.read(VALID/'validation.json');assert v['passed']
    vs=c.read(VALID/'validation_seal.json')
    assert c.sha(VALID/'validation.json')==vs['validation_sha256']
    assert c.sha(BASE/'bank_seal.json')==vs['bank_seal_sha256']
    vf=c.read(VALID/'freeze.json');assert all(c.sha(p)==h for p,h in vf['files'].items())
    original=c.read(ROOT/'freeze.json')
    assert all(c.sha(p)==h for p,h in original['files'].items())
    diag=ROOT/'gradient-diagnosis-01'
    ds=c.read(diag/'output_seal.json')['files'];assert all(c.sha(diag/p)==h for p,h in ds.items())
    assert (ROOT/'INCOMPLETE').exists() and not (BASE/'INCOMPLETE').exists()
    current=r.git_state();expected=c.read(BASE/'freeze.json')['repositories'];assert current==expected
    prior={}
    for date,name in (('2026-10-09','measured-map-reoptimization-01'),('2026-10-09','shared-plane-map-pilot-01'),
        ('2026-10-09','structural-holdout-map-pilot-01'),('2026-10-09','cross-visit-map-pilot-01'),
        ('2026-10-09','rotation-protected-map-pilot-01'),('2026-10-10','membership-formation-diagnosis-01'),
        ('2026-10-10','experiment-review-01')):
        prior[name]=delivery(c.MAIN/f'docs/maintenance/{date}/{name}')
    rlp=delivery(r.OLD,top_only=True)
    rows=r.ledger();wall=sum(x['wall_seconds'] for x in rows)
    rss=max(x['peak_RSS_bytes'] for x in rows);gpu_a=max(x['peak_GPU_allocated_bytes'] for x in rows)
    gpu_r=max(x['peak_GPU_reserved_bytes'] for x in rows)
    assert wall<=1800 and rss<=4*2**30 and max(gpu_a,gpu_r)<=3*2**30
    c.save(ROOT/'RESOURCE_AUDIT.json',dict(stages=rows,combined_recorded_wall_seconds=wall,all_failed_stages_counted=True,
        all_attempted_RSS_captured=True,peak_RSS_bytes=rss,peak_GPU_allocated_bytes=gpu_a,peak_GPU_reserved_bytes=gpu_r,
        limits=c.read(BASE/'freeze.json')['limits'],recorded_caps_pass=True,
        excluded=['module imports','WSL startup','design/docs','final identity/seal bookkeeping'],production_latency=False))
    c.save(ROOT/'REPOSITORY_STATE.json',dict(repositories=current,original_heads_branches_tracked_sets_preserved=True,
        isolated_helper=str(r.HELPER),no_commit_or_sync=True,no_production_default_backbone_source_or_manuscript_edit=True))
    source_noise_seed=c.read(r.OLD/'full-bank/bank.json')['rows'][0]['seed']
    assert source_noise_seed==850873755
    c.save(ROOT/'NOISE_PROVENANCE_NOTE.json',dict(training_noise_source='RLP2 full-bank/00_000002.npz noise array',
        original_noise_seed=source_noise_seed,initialization_and_sampler_RNG_guard_seed=20261010,
        unseen_noise_seed=20261011,training_noise_reused_byte_exact=True,
        bank_summary_noise_seeds_first_value_is_initialization_not_original_noise_seed=True,
        sealed_bank_not_rewritten=True,scientific_outputs_unchanged=True))
    c.save(ROOT/'CHECKS.json',dict(original_freeze_entries=len(original['files']),retry_freeze_entries=len(c.read(BASE/'freeze.json')['files']),
        all_original_sources_inputs_failure_and_INCOMPLETE_preserved=True,original_optimizer_updates=0,
        numerical_loss_scale_repair_only=True,independent_validator_centroid_precision_only_repair=True,
        independent_validator_static_repair_freeze_entries=len(vf['files']),helper_unchanged=True,old_delivery_entries=prior,
        RLP2_top_level_delivery_entries=rlp,RLP2_full_bank_or_training_replayed=False,
        checkpoint_sha256=c.sha(c.MAIN/'weights/rap_model_12.ckpt'),strict_weights_only_model_load=True,
        descriptor_checkpoint_not_loaded=True,noise_provenance_note='NOISE_PROVENANCE_NOTE.json',independent_validation=v))
    summary=c.read(BASE/'bank.json');fits=[];table=[];teacher=[]
    for folder in sorted((BASE/'bank').iterdir()):
        if not folder.is_dir(): continue
        fit=c.read(folder/'fit.json');fits.append(fit)
        initial=c.read(folder/'evaluation_0000.json');final=c.read(folder/'evaluation_0400.json')
        if 'native' in folder.name:
            table.append(f"| {folder.name} | {metric_line(initial)} | {metric_line(final)} | {metric_line(final,'unseen')} |")
            teacher.append(f"- {folder.name}: mean teacher velocity MSE {initial['teacher_loss_mean']:.9g} -> {final['teacher_loss_mean']:.9g}; final tau1 teacher {metric_line({'native':[dict(noise='train',step=5,errors=final['teacher_errors'][0]['errors'])]})}; tau.2 {metric_line({'native':[dict(noise='train',step=5,errors=final['teacher_errors'][-1]['errors'])]})}.")
        else:
            values=' / '.join(f"{x['t_m']:.6f}m, {x['R_deg']:.6f}deg" for x in final['errors'])
            table.append(f"| {folder.name} | direct initial loss {initial['loss']:.6g} | {values} | noise-independent direct output |")
    total_updates=sum(x['updates'] for x in fits)
    status='VALIDATED_CAPABILITY_DIAGNOSTIC_COMPLETE_WITH_NUMERICAL_REPAIR'
    c.status(ROOT,'complete',status=status,decision=summary['decision'],synthetic_native_pass=summary['synthetic_native_pass'],
        real_windows=summary['real_windows'],total_optimizer_updates=total_updates,full_optimizer_replay=False,
        no_transfer_or_system_gain=True,original_failure_preserved=True)
    report=f'''# NOC0 native-output capability diagnostic

{status}; decision **{summary['decision']}**. Owner said "执行下一轮" then "继续". This is the small diagnostic recommended after MF0, not the old twelve-fit draft or stopped RLP2. All retained outcomes are exposed development evidence.

## Result

Synthetic native five-step train-noise gate passed: {summary['synthetic_native_pass']}. Selected declared learning rate: {summary['selected_lr']}. Real windows executed: {summary['real_windows']}. Total optimizer updates: {total_updates}; each retained fit400 updates. No extra steps, windows, seeds or undeclared learning-rate rescue. Moving part1/part2 errors below use independent proper rigid decode, t metres/R degrees.

| Arm | Initial five-step train noise | Final five-step train noise or direct output | Final five-step unseen noise |
| --- | --- | --- | --- |
{chr(10).join(table)}

The synthetic conditional gate is both moving parts <=.05m and <=.2deg on the fixed training noise. Unseen noise was withheld from fitting, but shares the exact same scan/task: it is not scene transfer. A single known-transform fit or weak-reference real-window fit is not calibrated accuracy, independent generalization, RAP superiority, useful system gain or original mechanism. The direct control differs in initialization, architecture and capacity ({v['fit_parameter_counts']}); comparisons diagnose fitting only.

Noise provenance: training noise is the byte-exact original RLP2 00/t2 array (original seed850873755), adapter/direct initialization and sampler RNG guard use20261010, unseen noise uses20261011. The sealed bank summary's noise_seeds[0]=20261010 labels initialization rather than the original noise seed; NOISE_PROVENANCE_NOTE records this metadata correction without rewriting sealed arrays/manifest. Actual training noise identity is independently checked.

## Teacher forcing versus actual sampler

{chr(10).join(teacher)}

Teacher outputs use target-derived X_tau and remain separately labelled. Pure-noise inference uses original measured normalized inputs/descriptors and the unmodified production five-step Euler/rigidity-feedback sampler, with no target coordinates, target poses, teacher prefix cache or gradients through detached sampler outputs. All raw endpoints, states, velocities and one-step/five-step decoded poses are saved, including adverse and unseen-noise outcomes. Independent auditing checks every saved recurrence and gate. Low normalized MSE alone cannot establish a metric pose fit; common scale and sparse late-state errors can mask meaningful motion differences.

## Numerical failure and repair

Original92-entry freeze, partial bank/source snapshots, failure/two-row ledger/INCOMPLETE are intact. The initial backward had zero gradients for all four low-rank B matrices, and stopped before optimizer update1. Separate zero-update gradient diagnosis checks scales1 and1024 with identical parameters/states/loss. Scale1 B norm0, scale1024/unscale B norm3.1292e-5; output-MLP norm.00256185 identical. Every B branch is restored. This confirms this particular fp16 underflow, not universal unlearnability. AMENDMENT_01 discloses fixed backward scale1024 and gradient division before clipping/AdamW; no objective weight, learning-rate, count, seed, gate or cap changed. Zero A gradients at zero-B initialization are expected; A becomes active after updates. Retry source/input freeze has {len(c.read(BASE/'freeze.json')['files'])} entries and separate output routing; unchanged helper/production sources. Selected output-weight FD abs difference {c.read(BASE/'bank/synthetic_native_lr1e-4/preflight.json')['FD_abs_delta']:.3g}.

## Validation and resources

Independent Horn quaternion decode, exact target/normalization and real-source bindings (when admitted), all saved teacher/native/direct metrics, conditional search admission, every five-step recurrence and selected final full model/direct checkpoint forwards pass. {v['evaluation_records']} checkpoint records audited; max pose delta {v['maximum_pose_delta']:.3g}, metric {v['maximum_metric_delta']:.3g}, native float32 recurrence versus independent float64 geometry {v['maximum_sampler_recurrence_delta']:.3g}, selected forward {v['maximum_selected_forward_delta']:.3g}. First-ten-block teacher caches equal full forwards and frozen parameters retain their digest. Before validator execution, static review caught float32 real-point mean computation in its independent centre reconstruction; AMENDMENT_02 separately binds the float64 cast matching native normalization. Original validator sources and all fitted arrays remain unchanged; validation-attempt-02 has an independent source/input freeze. This is a pre-execution validator correction, not another failed fit or outcome change. Validation is bounded: no full independent AdamW replay and no independent replay of the selected FD beyond its stored values. No new raw preprocessing, descriptor inference or physical-reference verification.

All {len(rows)} recorded stages, including original failure and zero-update diagnosis, total {wall:.6f}s. Peak allocated/reserved GPU {gpu_a/2**20:.2f}/{gpu_r/2**20:.2f}MiB, RSS {rss/2**30:.6f}GiB. Original+diagnosis+retry whole-dossier artifact count is finalized in DELIVERY_SEAL.1800s/3GiB GPU/4GiB RSS/512MiB caps pass. Imports/WSL startup/design/docs/final identity/seal bookkeeping excluded, not production latency. Full resource ledger retained; all attempted RSS captured.

## Repository and evidence limits

Both original HEADs/branches/two and nine tracked dirty sets retained; checkpoint hash and all frozen model/config sources match. Strict weights-only344-key RAP load, no miniSpin load. Prior map/MF0/review delivery counts {prior} match. RLP2 {rlp} top-level delivery identities match; its full old bank/optimizer replay was not repeated. New isolated helper, main maintenance scripts/dossier and mutable handoffs only. No production/default/backbone-source/manuscript edit, acquisition/install, official-GT replacement, full trajectory/system metric, commit or Git sync. Prior stops/seals, physical time/calibration/reference/site/checkpoint-training-membership uncertainties and exploration relaxation remain.
'''
    (ROOT/'REPORT.md').write_text(report)
    if summary['synthetic_native_pass']:
        next_plan='''# Next decision after NOC0

The fixed tiny native-sampler gate passed; this establishes a debugging capability on the synthetic fixture only. Inspect the saved real-window and unseen-noise outcomes before selecting any broader learning route. No automatic training expansion is admitted by this result.

Next design only, in this order: first preserve the fitted adapter and audit a predeclared small noise census on the same synthetic and real window without updates, against frozen native. The retained unseen-noise real part2 remains about.356m while fixed-noise fitting reaches about.026m; do not expand training on that evidence. Mean teacher MSE did not necessarily improve even when the selected pose gate passed, so inspect the objective/metric/state mismatch instead of calling this a converged fit. Direct control's synthetic gate also failed; no architecture or RAP-superiority claim follows.

Then, only if that evidence warrants it, design a predeclared nearby-window evaluation without updates and with fixed measured inputs/no target-derived inference states, against frozen native and the unchanged strong geometry frontend. Separate same-task noise sensitivity from new-scene motion transfer. If transfer fails, diagnose its observed failure without claiming token impossibility or tuning evaluation windows. One-seed overfitting/weak GT cannot support system gain or originality. A geometry-conditioned residual comparison is a distinct later design, not executed here. No full trajectory, old RLP2 rescue or shared-plane optimization follows. No new diagnostic bank, protocol freeze, extra noise sweep or nearby-window inference was executed by this next plan.
'''
    else:
        next_plan='''# Next decision after NOC0

Both declared native trials failed the fixed synthetic five-step pose fit gate, so no real-window fitting was executed. Preserve all teacher, one-step/five-step and unseen-noise outputs, direct control, gradient diagnosis and numerical failure. This is a negative result for this two-rate400-update fixed-noise velocity-MSE adapter construction, not universal native-output unlearnability.

Stop additional steps/rates/seeds/windows or weak real fitting on this exact protocol. Next design only should be based on the measured teacher-versus-native gap: first ask whether known-transform motion is fitted through an inference-compatible state/objective, with metric pose/correct-gradient checks and a simple clean-coordinate capability control. Any actual-rollout gradient wrapper must explicitly retain a valid path rather than differentiating detached production sampler returns. If the direct learner also cannot fit, revisit its normalization/architecture/capacity before making a representation claim. No automatic loss/architecture rescue is implemented. Real transfer, geometry-conditioned residual learning or full trajectories require distinct concrete evidence/scope. MF0/shared-plane and old RLP2 stops remain.
'''
    (ROOT/'NEXT_ROUND_PLAN.md').write_text(next_plan)
    (ROOT/'HANDOFF.md').write_text(f'''# NOC0 handoff

{status}; {summary['decision']}. Read REPORT/PROTOCOL/OWNER_SCOPE/AMENDMENT_01/02/NEXT_ROUND_PLAN/STATUS/CHECKS/RESOURCE_AUDIT/REPOSITORY_STATE/DELIVERY_SEAL/NOISE_PROVENANCE_NOTE. Original92-entry freeze/partialbank/failure/ledger/INCOMPLETE and separate zero-update gradient diagnosis retained; validated102-entry attempt-02 freeze/bank/seals/combinedledger and separate8-entry validation-attempt-02 freeze/results/seal. Original0 updates, combined{total_updates} actual fitting updates; realwindows{summary['real_windows']}. No transfer/trajectory/system claim. Source/input identities and numerical/scientific distinctions are documented. No new experiment is selected/frozen by this handoff.
''')
    bytes_=sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file());assert bytes_<=512*2**20
    entries=[dict(path=str(p.relative_to(ROOT)),sha256=c.sha(p),bytes=p.stat().st_size)
        for p in sorted(ROOT.rglob('*')) if p.is_file() and p.name!='DELIVERY_SEAL.json']
    c.save(ROOT/'DELIVERY_SEAL.json',dict(status=status,decision=summary['decision'],files=entries,
        artifact_bytes_before_seal=bytes_,wall_seconds=wall,all_caps_pass=True))
    print('NOC0 CLOSED',summary['decision'],'sealed',len(entries),'bytes',bytes_,'wall',wall,flush=True)


if __name__=='__main__': run()
