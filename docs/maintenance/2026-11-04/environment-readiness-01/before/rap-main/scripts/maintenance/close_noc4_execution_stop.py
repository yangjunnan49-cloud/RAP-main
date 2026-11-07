"""Seal an audited, scientifically incomplete execution stop; no model calls."""
from pathlib import Path
import native_conditioned_comparison as r
c=r.c


def run():
    f=r.check();counts=r.old_deliveries();r.noise_check()
    v=c.read(r.BASE/'validation_execution_stop.json');assert v['passed']
    vs=c.read(r.BASE/'validation_execution_stop_seal.json')
    assert c.sha(r.BASE/'validation_execution_stop.json')==vs['validation_sha256']
    assert c.sha(r.BASE/'freeze.json')==vs['freeze_sha256']
    assert c.sha(r.BASE/'noise_seal.json')==vs['noise_seal_sha256']
    repos=r.n.noc.git_state();assert repos==f['repositories']
    supplements=[Path(__file__),Path(__file__).with_name('audit_noc4_execution_stop.py'),
        Path(__file__).with_name('diagnose_noc4_execution.py'),Path(__file__).with_name('diagnose_noc4_execution_sync.py'),
        r.BASE/'EXECUTION_NOTE.md',r.BASE/'EXECUTION_STOP_SCOPE.md']
    snap=r.BASE/'execution_source_snapshot';snap.mkdir()
    for p in supplements:
        if p.suffix=='.py': (snap/p.name).write_bytes(p.read_bytes())
    c.save(r.BASE/'execution_scope_seal.json',dict(files={str(p):c.sha(p) for p in supplements},
        scientific_freeze_sha256=c.sha(r.BASE/'freeze.json'),no_scientific_source_or_setting_change=True))
    ledger=r.ledger();observations=c.read(r.BASE/'EXTERNAL_EXECUTION_OBSERVATIONS.json')
    progress={}
    for name in ('execution_diagnosis_progress.jsonl','execution_diagnosis_sync.jsonl'):
        lines=[__import__('json').loads(x) for x in (r.BASE/name).read_text().splitlines()]
        progress[name]=dict(markers=len(lines),last=lines[-1],partial_process_peak_only=True)
    rss=max([x['peak_RSS_bytes'] for x in ledger]+[x['last']['RSS_peak_bytes'] for x in progress.values()]+[v['RSS_peak_bytes']])
    ga=max([x['peak_GPU_allocated_bytes'] for x in ledger]+[x['last']['GPU_allocated_peak_bytes'] for x in progress.values()])
    gr=max([x['peak_GPU_reserved_bytes'] for x in ledger]+[x['last']['GPU_reserved_peak_bytes'] for x in progress.values()])
    size=sum(p.stat().st_size for p in r.BASE.rglob('*') if p.is_file())
    assert size<512*2**20 and rss<4*2**30 and max(ga,gr)<3*2**30
    c.save(r.BASE/'RESOURCE_AUDIT.json',dict(original_stage_ledger=ledger,external_observations=observations,
        partial_diagnostic_progress=progress,recorded_stage_wall_seconds=sum(x['wall_seconds'] for x in ledger),
        available_CPU_audit_wall_seconds=v['wall_seconds'],max_observed_RSS_bytes=rss,
        max_observed_GPU_allocated_bytes=ga,max_observed_GPU_reserved_bytes=gr,limits=f['limits'],
        all_attempted_RSS_captured=False,all_attempted_GPU_peaks_captured=False,
        whole_attempt_wall_accounting_complete=False,all_attempt_caps_verified=False,
        observed_peaks_below_limits=True,artifact_bytes_at_audit=size,artifact_limit_pass=True,
        missing='background lifetime/exit marker and complete resource peaks for external exits/selected diagnostics',
        production_latency=False,old_budget_not_amended=True))
    c.save(r.BASE/'REPOSITORY_STATE.json',dict(repositories=repos,heads_branches_tracked_sets_preserved=True,
        sibling_helpers_unchanged=True,model_config_checkpoint_identities_unchanged=True,no_commit_or_sync=True))
    c.save(r.BASE/'CHECKS.json',dict(freeze_entries=len(f['files']),old_delivery_entries_unchanged=counts,
        validation_available_artifacts=v,scientific_neural_gates_complete=False,
        optimizer_probe_calls=0,neural_backward_calls=0,fit_updates=0,prediction_traces=0,
        real_windows=0,nearby_windows=0,resource_all_attempt_caps_verified=False))
    status='AUDITED_EXECUTION_STOP_BEFORE_NATIVE_NUMERICAL_GATE'
    decision='NO_NATIVE_FIT_RESULT_EXTERNAL_PROCESS_EXIT'
    report=f'''# NOC4: execution stop before native numerical gates

**{status}**; decision **{decision}**. Scientific native comparison remains incomplete. The owner asked to continue NOC3's positive control signal. A distinct synthetic V/P protocol and170-entry source/input freeze were prepared, but repeated external WSL exits prevented either native numerical probe. No backward call, actual optimizer probe, fitted update or complete native sampling trace occurred. This is not a learnability result.

## Available progress

The same exposed NOC0/NOC2 synthetic3x1000-point copied-descriptor fixture is byte-exact. The exact-target/gauge/three output-directional finite-difference mathematics passed and repeated in a CPU-only audit.24 newly declared fit8/eval16 noise arrays were generated and sealed before model loading; they were not used in gradient updates or native evaluation. Both arms' planned400-update fits and all72 native predictions remain unexecuted. No real/nearby/trajectory stage exists.

Independent Horn exact-target objective:{v['independent_Horn_exact_target_cost']:.9g}; identity objective delta versus torch proper-SVD:{v['independent_Horn_identity_cost_delta']:.9g}. All170 original frozen bindings and old delivery103/188/53/5/37 entries match. GPU noise arrays were checked for seal/shape/dtype/finiteness, without generator replay. Native numerical/fitting/performance gates were not independently validated because no such outputs exist.

## Preserved execution failures

The launcher initially omitted the prescribed one-thread runtime. Prepare and a prematurely submitted dependent preflight stopped at the thread check before numerical payload or checkpoint load. Their failures remain. Same-source retries set OMP/MKL/OPENBLAS thread counts to1, preserving all frozen scientific settings.

The corrected preparation passed. A subsequent foreground preflight exited externally without a Python failure record. An empty preflight directory was retained as preflight-external-exit. A hidden process with persistent logs likewise left an empty new preflight directory and no complete exit marker. A later call correctly refused that existing directory; its FileExistsError resource row is retained. Its error-record write also refused to overwrite the existing original FAILURE_preflight.json. No failed source or output was overwritten.

Read-only diagnostics confirm at least two strict344-key weights-only RAP loads, a complete ten-block prefix in one trace, and both tail transformer blocks returning in the module-hook trace before entry into the first final-MLP layer. Another synchronized trace stopped earlier during model loading. A standalone IEEE float32 matrix operation and the same frozen first MLP layer on a random input both succeed. Variable exit locations and absent Python exceptions prevent a unique driver/kernel/model/data/process-lifecycle diagnosis. Partial trace markers are not proof that every asynchronous GPU operation completed. No numerical workaround, precision change, parameter replacement or scientific rescue was applied.

## Resources and next boundary

Original ledger:{len(ledger)} rows, measured after-import wall{sum(x['wall_seconds'] for x in ledger):.6f}s; CPU stop audit{v['wall_seconds']:.6f}s. Maximum observed RSS{rss}bytes, GPU allocated/reserved{ga}/{gr}bytes, current artifacts{size}bytes. Observed peaks and artifacts lie below the prospective4GiB RSS/3GiB GPU/512MiB bounds. **Whole all-attempt wall/RSS/GPU caps cannot be certified**: an external background lifetime and several full-process peaks are missing. Original1800s/3GiB/4GiB/512MiB scope is not amended. Details/known external durations are retained in RESOURCE_AUDIT/EXTERNAL_EXECUTION_OBSERVATIONS/progress logs. Missing resource values are not zero and do not establish a limit breach. These are not production latencies.

Stop further native execution in this round. Preserve this scientifically incomplete attempt and its protocol/settings/inputs. Next DESIGN_ONLY: resolve or externally verify the execution environment, then specify a separate attempt with persistent per-process failure/exit/resource capture and fresh output routing before any new numerical probe. Do not tune rates, backward scales, update count, noise seeds, initialization or outcome gates to compensate for these exits. NOC3's positive float64 rigid-control result remains unchanged; it neither proves nor disproves native feasibility here.

Both original HEADs/branches/two and nine tracked dirty sets, model/config/checkpoint and sibling helpers remain. Only isolated main maintenance/docs/mutable handoffs changed. No acquisition/install, production/default/backbone-source/manuscript edit, officialGT replacement, real/nearby/trajectory, commit/Git sync. Old stops/seals/physical/reference/time/site/checkpoint uncertainty remain. Conventional geometry/adaptation; no original, physical, generalization or system gain.
'''
    (r.BASE/'REPORT.md').write_text(report)
    (r.BASE/'NEXT_ROUND_PLAN.md').write_text('# Next boundary after NOC4 execution stop\n\nResolve/verify the external execution environment first. Design a separate output-routed attempt with complete persistent process exit/resource capture before any new probe. No numerical tuning or dependent fit/native evaluation is admitted by this stop closure; scientific gates are unexecuted, not failed learnability evidence. NOC3 control signal and all old stops/seals remain.\n')
    (r.BASE/'HANDOFF.md').write_text(f'# NOC4 execution stop\n\n{status}; {decision}. Scientific experiment incomplete. Read REPORT/PROTOCOL/OWNER_SCOPE/EXECUTION_NOTE/EXECUTION_STOP_SCOPE/NEXT_ROUND_PLAN/STATUS/CHECKS/RESOURCE_AUDIT/REPOSITORY_STATE/DELIVERY_SEAL. Original170-entry freeze/24-noise seal/math and separate CPU available-artifact validation; external failure/diagnostic logs retained.0 neural backward/optimizer/fit/native prediction calls completed; no real/nearby/trajectory. All-attempt resource gaps prevent cap certification. No silent retry/tuning; old controls/negative results unchanged.\n')
    (r.BASE/'INCOMPLETE').write_text('Scientific native numerical/fitting/evaluation gates unexecuted. Attempt stopped and available artifacts audited; delivery seal does not certify scientific completion.\n')
    c.status(r.BASE,'execution_stopped',status=status,decision=decision,scientific_complete=False,
        available_artifact_audit_passed=True,fit_updates=0,optimizer_probe_calls=0,
        neural_backward_calls=0,prediction_traces=0,all_attempt_caps_verified=False)
    entries=[dict(path=str(p.relative_to(r.BASE)),sha256=c.sha(p),bytes=p.stat().st_size)
        for p in sorted(r.BASE.rglob('*')) if p.is_file() and p.name!='DELIVERY_SEAL.json']
    c.save(r.BASE/'DELIVERY_SEAL.json',dict(status=status,decision=decision,scientific_complete=False,
        available_artifact_audit_passed=True,all_attempt_caps_verified=False,files=entries,
        artifact_bytes_before_seal=sum(x['bytes'] for x in entries)))
    print('NOC4 execution stop sealed',len(entries),'entries; scientific comparison INCOMPLETE',flush=True)


if __name__=='__main__': run()
