"""Prepare English delivery documents from independently sealed RLP2 results."""
import json
from pathlib import Path
import local_motion_common as c
import rlp2_common as r


def write(name, value):
    (r.B / name).write_text(value.rstrip() + '\n', encoding='utf-8')


def js(name, value):
    write(name, json.dumps(value, indent=2, allow_nan=False))


def pair(values):
    return f'{values[0]:.6f} / {values[1]:.6f}'


def run():
    result = c.read(r.EVAL / 'bank/results.json')
    evaluation = c.read(r.EVAL / 'validation.json')
    closure = c.read(r.B / 'CLOSURE_CHECKS.json')
    repository = c.read(r.B / 'REPOSITORY_STATE.json')
    assert evaluation['passed'] and closure['passed'] and repository['heads_branches_match']
    assert repository['tracked_dirty_counts_match']
    summary = result['summary']
    decision = summary['decision']
    limit = getattr(r, 'COMBINED_LIMIT', 3600)
    failure_count = sum(not x['passed'] for x in c.read(r.B / 'RESOURCE_LOG.json'))
    amendment_text = (f'Owner separately approved at most45 additional process minutes before any GT model-error '
        f'outcome was inspected. Combined ceiling is now6300s (105min); all scientific settings and other caps '
        f'remain unchanged. Original budget stops retained: {failure_count}. The isolated hash-bound '
        f'resource-amendment-01 launcher changes only combined cap enforcement; original scientific sources '
        f'and all partial compute/failure snapshots remain. Original60min is not claimed as passed.'
        if limit == 6300 else 'Original3600s combined ceiling was retained.')
    status = ('VALIDATED_LOCAL_PASS' if decision == 'PASS_USEFUL_LOCAL_MOTION' else
              'VALIDATED_REPRESENTATION_ONLY' if decision == 'REPRESENTATION_ONLY_NO_USEFUL_LOCAL_GAIN' else
              'VALIDATED_INCONCLUSIVE' if decision == 'COVERAGE_INCONCLUSIVE' else 'VALIDATED_NEGATIVE')
    fits = [(seed, arm, c.read(r.FIT / f'{seed}_{arm}/validation.json'))
            for seed in r.SEEDS for arm in ('D', 'I', 'J')]
    assert all(v['passed'] and v['optimizer_updates'] == 1000 and v['initial_final_optimizer_exact']
               for _, _, v in fits)
    primary = c.read(r.PRED / 'validation.json')
    diagnostic = c.read(r.DIAG / 'validation.json')
    numerical = c.read(r.NUM / 'validation.json')
    full = c.read(r.FULL / 'validation.json')
    targets = c.read(r.LAB / 'validation.json')
    js('STATUS.json', dict(utc=c.now(), stage='RLP2', status=status, decision=decision,
        owner_authorized=True, all_15_scientific_stages_independently_validated=True,
        feature_windows=204, pose_target_windows=204, fit_windows=144, development_windows=12,
        exposed_evaluation_windows=48, completed_fits=9, validated_fits=9,
        completed_training_updates=9000, independent_replay_updates=9000,
        primary_predictions=432, valid_primary_predictions=primary['valid'],
        permutation_predictions=144, valid_permutation_predictions=diagnostic['valid'],
        evaluator_records=708, GT_model_errors_computed=True, gates=summary['gates'],
        trajectory_run=False, system_scope_separately_required=True, backbone_frozen=True,
        scientific_rescue=False, RLP2_numeric_implementation_failures=0,
        original_budget_stop_count=failure_count, combined_time_limit_s=limit,
        resource_extension_owner_approved=limit == 6300, physical_GT_verified=False,
        independent_generalization_claim=False, original_method_claim=False))
    root_marker = r.B / 'INCOMPLETE'
    assert root_marker.parent == r.B
    root_marker.unlink()
    if decision == 'PASS_USEFUL_LOCAL_MOTION':
        interpretation = ('The fixed local conjunction passes. This supports a separately scoped complete-sequence '
            'motion-factor intervention, not a system or original-method claim. No trajectory was included in this pilot.')
        next_text = ('Prepare a prospective full-sequence cost/coverage/boundary/invalid-policy protocol using existing '
            'results only, then obtain the separately required system scope before any trajectory generation. '
            'Keep original retrieval, keyframes, loops, admissions and graph noise fixed; require coupled official '
            'ter/rer/ATE improvement and sequence safety. No present system experiment is frozen or executed.')
    elif decision == 'REPRESENTATION_ONLY_NO_USEFUL_LOCAL_GAIN':
        interpretation = ('J passes both equally trained representation comparisons but fails the useful-motion '
            'conjunction against geometry/KISS. This is representation evidence on exposed weak GT only; no trajectory follows.')
        next_text = ('Stop promotion of this fixed construction to trajectories. Preserve the complete negative usefulness '
            'result and all fits. No tuning, best-seed selection, new decoder, radius, sampling or cohort rescue is authorized.')
    elif decision == 'COVERAGE_INCONCLUSIVE':
        interpretation = ('Complete prediction coverage fails; invalid outcomes remain in the denominator. '
            'Accuracy conclusions and trajectory promotion are inconclusive under the declared prerequisite.')
        next_text = ('Preserve all invalid records and independently validated coverage decision. Do not skip invalids '
            'or supply native/identity fallback. No scientific rescue or trajectory follows.')
    else:
        interpretation = ('J fails the required conjunction of coupled comparisons against I and D. Stop investment in '
            'this exact frozen-token, fixed-budget motion-supervised readout construction. This does not prove '
            'universal token unlearnability. No trajectory or automatic rescue follows.')
        next_text = ('Stop this exact head/soft-solve/loss/frozen-token construction under the present project budget. '
            'No epoch, seed, temperature, loss, density, correspondence threshold, window or cohort rescue follows. '
            'Any future experiment needs a distinct measurable mechanism and a new reviewable scope. '
            'No new experimental arm is selected or frozen by this delivery.')
    comparisons = '| Control | Windows | J median t(m) / R(deg) | Control median | Paired control-minus-J gain | Positive fractions t / R | Full gate |\n'
    comparisons += '|---|---:|---:|---:|---:|---:|---|\n'
    if summary['gates']['coverage']:
        for arm in ('I', 'D', 'G3', 'KISS'):
            x = summary['comparisons'][arm]
            comparisons += (f"| {arm} | {x['windows']} | {pair(x['J_median'])} | {pair(x['control_median'])} | "
                f"{pair(x['paired_median_gain'])} | {pair(x['positive_fraction'])} | {x['passed']} |\n")
        safety = '| Comparison | Sequence | J-minus-control mean t(m) / R(deg) | Safety pass |\n|---|---|---:|---|\n'
        for arm in ('I', 'D', 'G3', 'KISS'):
            for seq, x in summary['comparisons'][arm]['sequence_safety'].items():
                safety += f"| J vs {arm} | {seq} | {pair(x['mean_regression'])} | {x['passed']} |\n"
        medians = '; '.join(f"{arm}: {pair(summary['cohort_medians'][arm])}" for arm in ('D', 'I', 'J'))
        diagnostic_text = json.dumps(summary['permutation'], indent=2)
        diagnostic_text += '\nIdentity median t(m) / R(deg): ' + pair(summary['identity_median'])
    else:
        comparisons += '| Coverage incomplete | 48 | Inconclusive | Inconclusive | Inconclusive | Inconclusive | False |\n'
        safety = 'Accuracy and sequence gates are not promoted without complete primary coverage.\n'
        medians = 'Not promoted because coverage fails.'
        diagnostic_text = 'All outcomes remain saved; no coverage-conditioned rescue.'
    fit_table = '| Seed | Arm | Updates | Initial/final/optimizer exact | Max loss delta | Max gradient norm delta |\n|---|---|---:|---|---:|---:|\n'
    for seed, arm, v in fits:
        fit_table += (f"| {seed} | {arm} | 1000 | {v['initial_final_optimizer_exact']} | "
            f"{v['max_loss_delta']:.3e} | {v['max_gradient_norm_delta']:.3e} |\n")
    report = f'''# RLP2 complete motion-supervised readout pilot

Status: {status}. Decision: {decision}.
Owner authorized the complete immediate pilot with "执行你的建议" and then "请继续".
All204 feature/pose-target windows, nine fixed1000-update fits,432 primary and144
permutation predictions,708 error records and15 scientific stage validations are complete.
Primary coverage {primary['valid']}/432; permutation coverage {diagnostic['valid']}/144.
No RLP2 numerical implementation failure/repair or scientific setting change occurred.
{amendment_text}

{interpretation}

## Actual experimental scope

Original count-selected windows:144 fit00-05,12 development06,48 historically exposed
evaluation07-10;612 unique raw frame paths.06 was retained in the source/target banks
but used for no optimizer step, tuning or selection. Three fixed seeds20261007/08/09
and the same initial state across D/I/J per seed. Exactly9000 promoted optimizer
updates plus9000 separate independent replay updates, not18 fitted candidates.
Each per-window error is the median of all three seed errors before cohort comparison.
No favorable window/seed/epoch selection.

D uses32 descriptors+480 zero padding; I uses full-flow separated-context512-D tokens;
J uses joint-context512-D tokens. Identical9 common channels and521->128SiLU->64
unit embeddings.75072 nominal parameters; D13632effective, I/J identical active capacity.
Frozen RAP/miniSpin extraction uses original1000 points/scan, scanorder[t-1,t,t-2],
big-endian original LMF1 noise seed, last nominalt=.2, five native flow calls.
Both I and J were extracted for every window (2040 flow calls total).

Pose-only R/t weak supervision from update1 for all three pairs; no point-positive
count floor, overlap/dustbin branch or hard-match inference decoder. Float32 IEEE
dual-softmax-product weights normalize in float64 and solve proper SE3 on original
measured points. Same continuous solve at train and inference; Horn relative gap>1e-6,
no nonunique solve skip/fallback. AdamW lr1e-3,wd1e-4,batch1,clip1,1000updates;
fixed cyclic hash order and loss scales. Exact encoding saves float32 embeddings,
FULL raw-W SHA256, marginals/mass/spectrum/gap and pose. Validators regenerate all
weights byte-exactly on pinned operators, then use independent double Horn.

## Local results

All48 exposed-window cohort medians, t(m) / R(deg): {medians}

{comparisons}
Gains are paired medians, not differences of cohort medians. J vs each I/D requires
both paired gains>=.005m/.01deg, both J medians<=90%control, positive fractions>=.60
for each, and every sequence mean regression<=.005m/.02deg. G3 requires paired
gains.005m/.01deg+sequence safety. KISS uses36 identical07/09/10 endpoints, paired
gains.002m/.005deg, both J medians<=90%control+sequence safety. Dense-map KISS has
different input/context/cost; same-point G3 is separately included.

{safety}
Full per-seed/per-window errors and sequence mean/median arrays are in
{r.EVAL.relative_to(r.B)}/bank/results.json. Official GT files and historical system metrics stay
unchanged; new angular targets use the declared proper-rotation projection only.

## Fixed diagnostics

Within each scan, J token rows roll137 while coordinates/common rows remain fixed.
All144 diagnostic outputs were generated after primary validation and before GT
error evaluation. This changes the input distribution and alone proves no causal
mechanism or physical point identity. Identity is evaluator-only, not a fallback.

```text
{diagnostic_text}
```

## Independent evidence

Numerical:6 solver/rejection fixtures,18 initialized00/05 head checks,selected
finite-difference gradient delta{numerical['maximum_fd_gradient_delta']:.3e}, Horn
delta{numerical['maximum_horn_delta']:.3e}; no optimizer in this prerequisite.
Full bank:612 scans/612000 points/19584000 descriptor values and original noise exact;
native group/time/RNG bindings,48 same-point G3 and36 KISS endpoints independently
checked. Max pose/control delta{full['maximum_pose_delta']:.3e}; no native flow rerun
in that validator.204 weak pose targets maxdelta{targets['maximum_target_delta']:.3e}.

{fit_table}
Prediction weight hashes all exact. Independent primary/diagnostic Horn pose maxima
{primary['max_pose_delta']:.3e}/{diagnostic['max_pose_delta']:.3e}; final708 GT/error/
aggregate/gate records maxerror delta{evaluation['maximum_error_delta']:.3e}.
Independent fitting implements its own head/loss/solve and replays every step,
not just checkpoint arithmetic. CLOSURE_CHECKS.json rechecks every stage freeze,
complete bank/seal/validation, old RLP1/DS0/design delivery files, original TR0 and
isolated helper/staging binding. Historical AGENTS/PHASE snapshots are mutable
handoffs and excluded from old delivery comparisons. REPOSITORY_STATE.json checks
original HEADs/branches and tracked dirty counts. No prior failure/bank was removed.

## Resources

RESOURCE_TABLE_PLACEHOLDER

Counters are sums of recorded monotonic process stages, including freezes, validation,
all9000 independent replay updates and closure/delivery hashing. They are not the
enclosing session wall time. Routine implementation/documentation, idle intervals
and WSL launching are separate; UTC stamps include a long gap and are not the cap
clock. {amendment_text} No precision/density reduction or scientific rescue.

## Limits and next boundary

Exposed engineering pilot, not an independent generalization result. Published RAP
training includes Oxford and excludes KITTI08-10, but local checkpoint binding/site
membership remains unknown; historical02/M3/E0/08 exposure persists. Short-segment
weak GT/09 discrepancy is not resolved or physically verified. I is a possible
one-part OOD ablation with unequal attention work; D effective capacity is smaller.
No calibrated confidence, exact physical correspondence, system metric gain or
originality established by this soft matching/SVD/pose-supervised construction.
All old scientific stops/banks and owner's original breakthrough requirement remain.

{next_text}
No production/default/backbone/manuscript edits, acquisition/install, commit or Git
synchronization. Training authorization was used only for these isolated small heads.
'''
    write('REPORT.md', report)
    write('NEXT_ROUND_PLAN.md', '# RLP2 next boundary\n\nDecision: ' + decision + '\n\n' + next_text +
        '\n\nThe immediate authorized pilot is complete. Earlier R3/LMF1/RAD1/D1/PFG1/LC0/RLP1 '
        'stops remain. Physical GT,09 discrepancy,checkpoint/site/exposure and originality '
        'questions remain unresolved. Preserve all scientific seals and original dirty work.')
    write('HANDOFF.md', f'''# RLP2 handoff

{status}; {decision}. The complete owner-authorized immediate pilot has closed.
Read REPORT.md, PROTOCOL.md, OWNER_AUTHORIZATION.md, STATUS.json, RESOURCE_AUDIT.json,
CLOSURE_CHECKS.json, REPOSITORY_STATE.json and DELIVERY_SEAL.json; then evaluation/
bank/results.json and all15 scientific freeze/bank/validation seals. Original head
implementation is the isolated RAP-SLAM/scripts/motion_supervised_readout.py,
identical to source_staging. Do not edit frozen sources or rerun candidates.

204 feature/target windows;144 fit00-05,12 unused development06,48 exposed07-10.
All nine fixed1000-update fits and nine full independent replays validated.
432 primary ({primary['valid']}valid),144 permutation ({diagnostic['valid']}valid),708
metric records complete. All weight hashes exact. No numerical failure/repair.
{amendment_text}

{interpretation}

{next_text}
No trajectory/default/backbone/manuscript/acquisition/install/commit/Git sync.
Both original HEADs/branches/tracked dirty counts preserved. RLP1 failed attempt
markers and old mutable snapshot seals remain historical. Original breakthrough,
physical GT/09 discrepancy,checkpoint/site/exposure and originality unresolved.
''')
    # Hash large unchanged scientific payloads once; final small metadata changes
    # below are explicitly rehashed after the timed stage counter is appended.
    files = {str(p): c.sha(p) for p in sorted(r.B.rglob('*')) if p.is_file()}
    r.finish('delivery_preparation_and_hashing')
    log = c.read(r.B / 'RESOURCE_LOG.json')
    total = sum(x['wall_s'] for x in log)
    training = [x for x in log if x['stage'] in {f'fit_{s}_{a}' for s in r.SEEDS for a in ('D', 'I', 'J')}]
    gpu, rss = max(x['gpu_gib'] for x in log), max(x['rss_gib'] for x in log)
    artifact = max(x['artifact_bytes'] for x in log)
    assert total <= limit and gpu <= 3 and rss <= 4 and artifact <= 4 * 2**30
    assert len(training) == 9 and max(x['wall_s'] for x in training) <= 300
    extraction = next(x['wall_s'] for x in log if x['stage'] == 'full_bank')
    assert extraction <= 1200
    js('RESOURCE_AUDIT.json', dict(utc=c.now(), passed=True, combined_process_s=total,
        combined_limit_s=limit, original_combined_limit_s=3600,
        original_combined_cap_passed=total <= 3600,
        owner_approved_additional_limit_s=limit-3600,
        original_budget_stop_count=failure_count,
        extraction_s=extraction, extraction_limit_s=1200,
        maximum_fit_s=max(x['wall_s'] for x in training), each_fit_limit_s=300,
        peak_GPU_GiB=gpu, GPU_limit_GiB=3, peak_RSS_GiB=rss, RSS_limit_GiB=4,
        artifact_bytes_at_final_timed_checkpoint=artifact, artifact_limit_bytes=4 * 2**30,
        training_updates=9000, independent_replay_updates=9000,
        failed_stages=sum(not x['passed'] for x in log), stage_count=len(log),
        cap_clock='Sum of monotonic recorded processes; not enclosing session elapsed',
        routine_implementation_documentation_idle_WSL_launch_excluded=True,
        UTC_gap_not_used_as_compute_clock=True, log=log))
    resource_text = (f'Recorded process sum {total:.3f}s /{limit}s; full extraction {extraction:.3f}s /1200s; '
        f'max fit {max(x["wall_s"] for x in training):.3f}s /300s.\n'
        f'Peak GPU {gpu:.3f}GiB /3GiB; RSS {rss:.3f}GiB /4GiB; artifacts at final timed '
        f'checkpoint {artifact / 2**30:.3f}GiB /4GiB. Amended caps pass; original budget stops {failure_count}.')
    write('REPORT.md', report.replace('RESOURCE_TABLE_PLACEHOLDER', resource_text))
    for name in ('RESOURCE_LOG.json', 'RESOURCE_AUDIT.json', 'REPORT.md'):
        files[str(r.B / name)] = c.sha(r.B / name)
    for path in (c.MAIN / 'AGENTS.md', c.MAIN / 'docs/maintenance/2026-10-08/PHASE_RECORD.md'):
        files[str(path)] = c.sha(path)
    seal = dict(utc=c.now(), status=status, decision=decision, files=files,
        note='AGENTS.md/PHASE_RECORD.md are historical mutable handoff snapshots; scientific stage seals are separate. '
             'All15 scientific stages are complete; old RLP1 failed stages remain unchanged.')
    js('DELIVERY_SEAL.json', seal)
    final_bytes = sum(p.stat().st_size for p in r.B.rglob('*') if p.is_file())
    assert final_bytes <= 4 * 2**30
    print('RLP2 delivery sealed', status, decision, total, final_bytes, flush=True)


if __name__ == '__main__':
    run()
