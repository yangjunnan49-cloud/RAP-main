"""Post-execution documentary closure; no scientific payload replay."""
import datetime as dt
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DAY = ROOT.parent


def load(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))


def save(p, obj):
    with p.open('x', encoding='utf-8') as f:
        json.dump(obj, f, indent=2)
        f.write('\n')


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def text(p, value):
    with p.open('x', encoding='utf-8', newline='\n') as f:
        f.write(value)


def verify(root, name):
    seal = load(root / name)
    for e in seal['files']:
        p = root / e['path']
        assert p.stat().st_size == e['bytes'] and sha(p) == e['sha256'], str(p)
    return len(seal['files'])


vb = DAY / 'visual-baseline-execution-01'
cd = DAY / 'visual-control-diagnostic-01'
er = DAY / 'visual-essential-refinement-01'
for root in (vb, cd, er):
    verify(root, 'SOURCE_FREEZE.json')
for name in ('RUNTIME02_FREEZE.json', 'RUNTIME03_FREEZE.json', 'AUDIT_IOFIX_FREEZE.json'):
    verify(er, name)
for stage in ('controls', 'features', 'runtime02/probe', 'runtime03/probe', 'runtime03/predict', 'runtime03/evaluate', 'runtime03/audit'):
    verify(er / stage, 'SEAL.json')
    assert load(er / stage / 'HOST_EXIT.json')['passed']
assert not list((er / 'predict').glob('*.npz'))
assert len(list((er / 'runtime02/predict').glob('*.npz'))) == 7
for item in load(er / 'RUNTIME03_PARTIAL_INDEX.json')['entries']:
    assert sha(Path(item['path'])) == item['sha256']
    assert sha(er / 'runtime03/predict' / item['record']['evidence']) == item['sha256']
stages = ['controls', 'features', 'predict', 'runtime02/probe', 'runtime02/predict', 'runtime03/probe', 'runtime03/predict', 'runtime03/evaluate', 'runtime03/audit']
receipts = [{'stage': n, **load(er/n/'HOST_EXIT.json')} for n in stages]
assert all(r['no_live_owned_process'] for r in receipts)
prediction_seconds = sum(r['elapsed_seconds'] for r in receipts if r['stage'] in ('predict', 'runtime02/probe', 'runtime02/predict', 'runtime03/probe', 'runtime03/predict'))
assert prediction_seconds < 300
now = dt.datetime.now(dt.timezone.utc)
origin = dt.datetime(2026,10,28,7,1,26,tzinfo=dt.timezone.utc)
inclusive = (now-origin).total_seconds()
assert inclusive < 5400
size = sum(p.stat().st_size for p in er.rglob('*') if p.is_file())
assert size < 1073741824
resources = {'utc': now.isoformat(), 'scope_origin_utc': origin.isoformat(), 'inclusive_seconds': inclusive,
    'whole_scope_cap_seconds': 5400, 'cap_pass': True, 'all_child_receipts': receipts,
    'sum_child_host_wall_seconds_including_failures': sum(r['elapsed_seconds'] for r in receipts),
    'prediction_all_attempts_and_cold_controls_seconds': prediction_seconds, 'prediction_cap_seconds': 300,
    'successful_children_max_lifetime_peak_bytes': max(r['child_lifetime_peak_bytes'] or 0 for r in receipts),
    'failed_child_self_peaks': 'UNKNOWN; retain host-polled peaks, do not infer exact lifetime peaks',
    'dossier_bytes_before_documentary_closure': size, 'dossier_cap_bytes': 1073741824,
    'all_owned_children_reaped': True, 'no_other_process_or_WSL_state_claim': True}
save(er/'RESOURCE_AUDIT.json', resources)
final = load(er/'runtime03/evaluate/SUMMARY.json')['groups'][0]
raw = load(er/'runtime03/evaluate/INITIAL_SUMMARY.json')['groups'][0]
audit = load(er/'runtime03/audit/RESULT.json')
refit = load(er/'runtime03/audit/REFIT_TRACE_AUDIT.json')
text(er/'REPORT.md', f'''# ER1 complete ordinary camera baseline: limited coverage, no refit gain claim

All 273 original images and all 200 existing ordered pairs are complete. The final result is 30 pose outputs and 170 explicit no-evidence records. All 30 outputs are from sequence00's original75 positives; sequence08 has zero outputs on all100 pairs, and all50 confusers have no output. These are output-availability observations for this fixed estimator, not calibrated rejection/correctness labels or proof of image-only impossibility.

| Complete-cohort quantity | Initial raw RANSAC | Robust refit |
|---|---:|---:|
| Pose outputs /200 | 30 | 30 |
| Rotation mean, degrees (30 outputs) | {raw['rotation_error_mean_deg']:.9f} | {final['rotation_error_mean_deg']:.9f} |
| Rotation median, degrees (30 outputs) | {raw['rotation_error_median_deg']:.9f} | {final['rotation_error_median_deg']:.9f} |
| Direction mean, degrees (30 outputs) | {raw['direction_error_mean_deg']:.9f} | {final['direction_error_mean_deg']:.9f} |
| Direction median, degrees (30 outputs) | {raw['direction_error_median_deg']:.9f} | {final['direction_error_median_deg']:.9f} |
| Rotation<=5 and direction<=15, all200 denominator | 23/200 | 23/200 |
| Rotation<=10 and direction<=30, all200 denominator | 24/200 | 24/200 |

Refit improved the two medians slightly but worsened both means and increased neither complete-cohort joint bin. This does not establish an overall or material improvement. Keep all170 missing outputs and the full00/08, positive/confuser and eight25-pair strata. Full rows and15 summary groups per estimator are under runtime03/evaluate. Reference direction is defined on all200; reported mean/median errors have denominator30, not200. Frozen bins are descriptive, not safety/efficacy gates.

## Implementation and controls

Original VB1 raw-RANSAC outlier control remains FAILED (0.113146318316918-degree rotation versus strict0.1 gate; direction0.499837669953744 versus0.5). CD1's fixed analytic0.2-degree candidate still meets both1-pixel line-distance bounds on96 exact correspondences; this refutes an angular certificate from the consensus tolerance alone, not native solver correctness. ER1 is a distinct five-parameter robust Sampson-refit implementation with all parameters and code frozen before real images. The identical outlier fixture/seed/gates now gives5.944964418571343e-14-degree rotation and zero printed direction error; all23 controls pass. Initial raw values/failure remain visible in its controls and measured-data comparator.

The first actual prediction launch failed before the pair loop on a standard ASCII codec lazy import. The first narrow cold P0/NPZ probe passed; the next prediction reached seven complete no-evidence files then failed on NumPy.ma lazy loading. Both original children/sources/receipts are preserved. The final correction preloads standard modules before the same exact read allowlist, passes a complete cold synthetic computation path, preserves seven exact NPZ files, reconstructs two insufficient-match and five insufficient-essential-support JSON records from their frozen early-return semantics, and computes only193 missing pairs. A metadata-preparation assumption that all seven were insufficient-match records failed before freeze; the earlier source/plan are retained and the actual ZIP/header/mask branches were checked explicitly. No image/algorithm/threshold/seed changes or partial accuracy readout occurred. A prospective audit-only read-set correction accounts for five feature caches no longer needed by the skipped completed pairs; all273 caches remain sealed and audited.

## Separation and independent evidence

All200 initial/final predictions were sealed at2026-10-28 07:14:04.8454464 UTC. The independent reference-read begin record is07:16:11.579718 UTC. Prediction's strict Python audit hook permits only needed feature caches, two archive P0 files and seven previously completed evidence files; reference/label values are excluded. This is reviewed Python-level enforcement, not an OS security claim. Inputs retain their exposed cohort and supplied-reference roles.

The audit passed all273 cache identities/shapes,200 ordered predictions/masks/pose semantics, {audit['independent_clear_nearest_ratio_checks']} independent clear descriptor nearest/ratio checks. {audit['numerically_ambiguous_checks_retained']} sampled decisions are numerically ambiguous and explicitly retained, not counted as independently clear. All200 relative transforms were independently recomputed with Decimal60 Gaussian elimination: maximum element difference {audit['max_reference_element_difference']:.17g}; rotation/direction metric differences {audit['max_rotation_metric_difference_deg']:.17g}/{audit['max_direction_metric_difference_deg']:.17g} degrees. All15 final and15 raw summaries retain complete denominators. The saved refit audit covers {refit['finite_manifold_trace_steps']} manifold trace steps and {refit['independent_line_search_costs_verified']} independently recomputed line-search costs; maximum scaled cost difference {refit['largest_scaled_cost_difference']:.17g}. No prediction/feature replay was used for audit.

## Resources and limits

Prediction failures+cold controls+final continuation total {prediction_seconds:.9f}/300 seconds. All scientific-stage host walls including failures sum {resources['sum_child_host_wall_seconds_including_failures']:.9f} seconds; these are child accounts, not summed overlapping inclusive scopes. Maximum successful-child OS lifetime peak is {resources['successful_children_max_lifetime_peak_bytes']} bytes. Failed children lack final self-peak; their host-polled peaks remain. ER1 inclusive time at this closure is {inclusive:.6f}/5400 seconds, new dossier {size}/1073741824 bytes before small closure records. Every owned child exited/reaped; fresh12GiB/2s guards and original stage caps passed. RESOURCE_AUDIT.json contains exact receipts. No old cap is replenished.

This is measured-image camera rotation and signed unit translation direction only. No metric translation scale/full metric6DoF, corrected-LiDAR equivalence, physical truth, independent source/cohort authentication, RAP increment, new RAP training or manuscript readiness is established. Old SR1 four-noise-cell failure, HFIT0 INCOMPLETE/2GiB stop, old native/joint/equivalence/source failures and all caps remain. Research UNRESOLVED; manuscript PAUSED. No installations, network, WSL start, existing-environment/default/production/Git writes, outreach, scheduler or goal-status action. Next useful review is a complete saved-output categorical join to historical missing-proposal categories, not parameter/seed/subset rescue.
''')
save(er/'STATUS.json', {'state': 'COMPLETE_273_IMAGES_200_INITIAL_AND_FINAL_PREDICTIONS_EVALUATED_AND_AUDITED',
    'pose_outputs': 30, 'no_evidence': 170, 'sequence00_outputs': 30, 'sequence08_outputs': 0,
    'joint_5_15_all200': 23, 'joint_10_30_all200': 24, 'overall_refit_gain_established': False,
    'metric_translation_scale': False, 'new_RAP_training': False, 'research': 'UNRESOLVED', 'manuscript': 'PAUSED',
    'original_VB1_fail_unchanged': True, 'all_children_reaped': True})
text(er/'CURRENT_HANDOFF.md', '''# Complete measured-image ordinary camera baseline

Read REPORT.md, STATUS.json, RESOURCE_AUDIT.json, DELIVERY_SEAL.json and runtime03/evaluate plus runtime03/audit. All273 feature caches/200 initial-and-final predictions are complete and prediction-sealed before reference evaluation.30/200 poses, all00;08=0/100.23/200 in the frozen5/15-degree bin,24/200 in10/30. Refit worsens both means and does not add bin successes. No overall gain, metric translation, RAP increment or physical/generalization claim. All old failures/caps remain; research UNRESOLVED/manuscript PAUSED.

Do not rerun original failed VB1, old download/install hosts or ER1 one-launch stages. Cold-import failures, seven-row byte-preserving continuation, metadata assertion and read-set audit correction are explicit additive receipts, not erased attempts. All children reaped. No pending numerical worker. Current owner continuation/account availability is managed separately in project-continuation-02; this finite stage is complete and does not automatically resume at reset.
''')
verify(cd/'controls', 'SEAL.json')
cdseal = load(cd/'controls/SEAL.json')
cdend = dt.datetime.fromisoformat(cdseal['sealed_utc'])
cdorigin = dt.datetime(2026,10,28,6,58,25,tzinfo=dt.timezone.utc)
text(cd/'REPORT_ADDITIVE.md', f'''# CD1 closed primary output, later documentary additive

The sole synthetic worker passed13 controls, exited0 and was reaped; its primary files were host-sealed at{cdseal['sealed_utc']}. Primary inclusive origin-to-seal time was{(cdend-cdorigin).total_seconds():.7f}/900 seconds. The fixed analytic candidate's0.2-degree rotation error has maximum forward/reverse line distances0.8896101915873307/0.8639366247991574 pixels on all96 clean correspondences, demonstrating that1-pixel consensus alone is not a0.1-degree rotation certificate. No failed native pose estimator was replayed. No measured images/reference/model/training input; no real-image admission. VB1 remains failed.

This report is written later at{now.isoformat()}, outside the earlier primary controls/SEAL.json, under the separately dated documentary closure. It is not backdated into that primary seal or charged as a new scientific payload. The inherited launcher console 'VB1 controls PASS' identifies this directory's CD1 controls only, not a reversal of original VB1. No automatic stage or quota-reset resume.
''')
save(cd/'CLOSE_CHECKS_ADDITIVE.json', {'primary_seal_verified': True, 'primary_inclusive_seconds': (cdend-cdorigin).total_seconds(),
    'primary_cap_seconds': 900, 'primary_cap_pass': (cdend-cdorigin).total_seconds() < 900,
    'later_report_utc': now.isoformat(), 'VB1_remains_failed': True})
for root in (vb, cd, er):
    assert not (root/'DELIVERY_SEAL.json').exists()
    files = [{'path': p.relative_to(root).as_posix(), 'bytes': p.stat().st_size, 'sha256': sha(p)}
             for p in sorted(root.rglob('*')) if p.is_file()]
    save(root/'DELIVERY_SEAL.json', {'sealed_utc': dt.datetime.now(dt.timezone.utc).isoformat(), 'files': files,
         'role': 'Final documentary delivery; dated source freezes and primary output seals remain distinct'})
    count = verify(root, 'DELIVERY_SEAL.json')
    print(root.name, 'sealed entries', count)
save(ROOT/'CLOSED_SCOPES.json', {'utc': now.isoformat(), 'scopes': [
    {'id': 'VB1', 'state': 'CLOSED_CONTROL_FAIL', 'delivery_seal_sha256': sha(vb/'DELIVERY_SEAL.json')},
    {'id': 'CD1', 'state': 'COMPLETE_SYNTHETIC_DIAGNOSTIC', 'delivery_seal_sha256': sha(cd/'DELIVERY_SEAL.json')},
    {'id': 'ER1', 'state': 'COMPLETE_LIMITED_CAMERA_5DOF_BASELINE', 'delivery_seal_sha256': sha(er/'DELIVERY_SEAL.json')}],
    'research': 'UNRESOLVED', 'manuscript': 'PAUSED', 'no_pending_owned_numeric_child': True})
