"""Close the validated RAD1 retry without modifying frozen evidence."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
import numpy as np

MAIN=Path(__file__).resolve().parents[2]
ROOT=MAIN/'docs/maintenance/2026-10-07/raw-association-decoder-01'
BASE=ROOT/'attempt-02'
def read(p):return json.loads(p.read_text())
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for block in iter(lambda:f.read(1<<20),b''):h.update(block)
    return h.hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
assert read(BASE/'validation.json')['passed']
assert sha(BASE/'validation.json')==read(BASE/'validation_seal.json')['sha256']
assert ROOT.joinpath('INCOMPLETE').is_file() and not BASE.joinpath('INCOMPLETE').exists()
for folder in (ROOT,BASE):
    for p,h in read(folder/'freeze.json')['files'].items():assert sha(p)==h,p
    bank=read(folder/'bank.json');assert sha(folder/'bank.json')==read(folder/'bank_seal.json')['bank_sha256']
    for row in bank['rows']:assert sha(row['file'])==row['sha256']
assert not list(BASE.glob('FAILURE*'))
summary=read(BASE/'summary.json');assert summary['decision']=='NO_RAW_ASSOCIATION_DECODER_SIGNAL'
bank=read(BASE/'bank.json');fallback=np.zeros(4,int);selected=np.zeros(4,int)
for row in bank['rows']:
    with np.load(row['file'],allow_pickle=False) as z:
        fallback+=z['fallback'].sum(1)
        selected+=z['fallback'][np.arange(4),z['selected']]
diag=read(BASE/'DESCRIPTIVE_DIAGNOSTIC.json')
diag.update(fallback_generations=dict(zip(['R','P','D','Z'],fallback.tolist())),
    selected_fallbacks=dict(zip(['R','P','D','Z'],selected.tolist())),fallback_generation_denominator=800,selected_denominator=200)
save(BASE/'DESCRIPTIVE_DIAGNOSTIC.json',diag)
utc=datetime.now(timezone.utc).isoformat()
status=dict(stage='RAD1',status='VALIDATED_NEGATIVE',attempt=2,decision=summary['decision'],utc=utc,
    owner_authorized_execution=True,identities=1501,pairs=200,synthetic_npz=101,bank_npz=200,
    independent_synthetic_passed=True,independent_bank_passed=True,independent_evaluation_passed=True,
    hard08_selected_recovery=0,hard08_oracle_recovery=0,gt_read=True,new_inference=False,training=False,
    graph_or_trajectory=False,originality_established=False,original_attempt_status='INCOMPLETE',
    original_bank_preserved=True,repair='../AMENDMENT_01.md',all_scientific_gates_unchanged=True,
    official_metrics_unchanged=True,next_stage=dict(status='PLANNED_READ_ONLY_NOT_STARTED',plan='../NEXT_ROUND_PLAN.md',online71_licensed=False))
save(BASE/'STATUS.json',status)
rootstatus=dict(status,valid_result_location='attempt-02',identities_original=1497,
    original_incomplete_marker_preserved=True,original_failure='FAILURE_validation_bank.json',
    repair='AMENDMENT_01.md',original_gt_read=False)
rootstatus['next_stage']=dict(status='PLANNED_READ_ONLY_NOT_STARTED',plan='NEXT_ROUND_PLAN.md',online71_licensed=False)
save(ROOT/'STATUS.json',rootstatus)
handoff='''# RAD1 final handoff — validated negative retry

Owner authorized planning, protocol/handoff and execution on2026-10-07.
Read REPORT.md, NEXT_ROUND_PLAN.md, STATUS.json and AMENDMENT_01.md here;
then attempt-02/PROTOCOL.md, freeze.json, bank_seal.json,
bank_validation.json/bank_validation_seal.json, summary.json,
validation.json/validation_seal.json and DESCRIPTIVE_DIAGNOSTIC.json.

Valid result is attempt-02:1501 identities froze before101 synthetic files
and the complete200-pair bank; all3200 solves/source inputs/geometry reproduce
independently. GT-free validation sealed before GT, and final independent
evaluation passed. Decision NO_RAW_ASSOCIATION_DECODER_SIGNAL.
Selected strict N/R/P on00=49/50/50 and08=30/30/31 out of75 positives.
R recovers0/41 hard08; every R/P/D/Z arm also has zero oracle hard recoveries.
00 incorrect accepts N/R=1/3. Raw lacks the required unique/material/safe
gain. Official labels/ter/rer/ATE remain unchanged. No system or originality
gain follows. Fixed final-raw decoder route stops before online71/graph/
trajectory, without parameter, step, density, solver, selector or cohort rescue.

Original attempt remains INCOMPLETE, with unchanged1497-identity freeze,
all200 NPZs, original three sources and FAILURE_validation_bank.json.
Noncollinear points had rank1 cross-covariance and a nonunique rotation.
Separate retry adds objective eigengap rejection, reruns all200 before GT,
and preserves scientific gates. Root INCOMPLETE refers to that original;
attempt-02 INCOMPLETE was removed only after final validation. Root status
points to the valid retry. Do not treat the original bank as validated.

No active process or unfinished authorized experimental stage remains.
The next distinct measurement-source/statistical-model audit is PLANNED ONLY
in NEXT_ROUND_PLAN.md; no new mechanism/protocol/bank selected or running.
Do not automatically restart stopped routes or rerun sealed outputs.
An additional proposal needs genuinely distinct information/objective,
matched physical controls, prior-art review and its own stage boundary.
Unknown checkpoint training membership and09 physical discrepancy persist.

Frozen algorithms: RAP-SLAM/scripts/measurement_association.py(original)
and measurement_association_v2.py(retry). Corresponding RAD1 maintenance
drivers/validators live in RAP-main/scripts/maintenance. Existing WSL
Ubuntu-24.04 /root/miniconda3/envs/rap-inference/bin/python runs -B with
OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=MKL_NUM_THREADS=1. No package install,
new neural inference, training, production/default/model/manuscript change,
commit or Git sync. All old banks and negative stops remain immutable.

Original HEADs remain RAP-main4055d929c594b0033aafc6eed339c910369eef55
on codex/meeting-20260930; RAP-SLAM6d3f2d22cedfe1f807deb11fd8796b9f5bf17cd6
on codex/e0-f1-20260926. Existing dirty work is preserved. Delivery records
and resource audit distinguish failed original effort from successful retry.
'''
(ROOT/'HANDOFF.md').write_text(handoff)
(BASE/'HANDOFF.md').write_text('# RAD1 attempt-02 final handoff\n\nRead ../HANDOFF.md, ../REPORT.md, ../AMENDMENT_01.md and ../NEXT_ROUND_PLAN.md.\nThis attempt is VALIDATED_NEGATIVE with complete independent GT-free and\nGT evaluation seals. No active work remains; online71/graph/trajectory is not\nlicensed by this result. Original attempt stays INCOMPLETE and preserved.\nSee STATUS.json and frozen PROTOCOL.md for the exact boundary.\n')
stages=[read(BASE/'synthetic_seal.json'),read(BASE/'synthetic_validation.json'),bank,
    read(BASE/'bank_validation.json'),dict(wall_s=summary['evaluation_wall_s'],peak_rss_bytes=summary['peak_rss_bytes']),read(BASE/'validation.json')]
audit=dict(utc=utc,successful_attempt_stage_wall_s=sum(s['wall_s'] for s in stages),
    successful_attempt_peak_rss_bytes=max(s['peak_rss_bytes'] for s in stages),new_npz_bytes=read(BASE/'bank_seal.json')['npz_bytes'],
    original_npz_bytes=read(ROOT/'bank_seal.json')['npz_bytes'],
    total_retained_bytes_excluding_resource_audit=sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file() and p.name!='RESOURCE_AUDIT.json'),
    artifact_cap_bytes=300*2**20,stage_caps_passed=True,new_neural_inference=False,gpu_work=False,
    original_failed_bank_validation_full_wall_unrecorded=True,source_hashing_diagnosis_documentation_excluded_from_stage_wall=True,
    both_original_and_repaired_frozen_identities_and_complete_banks_rehashed=True,
    original_summary_absent=not (ROOT/'summary.json').exists(),original_incomplete_preserved=True)
assert audit['total_retained_bytes_excluding_resource_audit']+10000<300*2**20
save(ROOT/'RESOURCE_AUDIT.json',audit)
print(json.dumps(dict(fallback=diag,audit=audit),indent=2))
