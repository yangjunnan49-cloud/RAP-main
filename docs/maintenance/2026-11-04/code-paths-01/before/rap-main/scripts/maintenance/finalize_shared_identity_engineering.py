"""Document-only final seal for the already validated D1 engineering study."""
from __future__ import annotations
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'docs/maintenance/2026-10-06/shared-identity-engineering-01'
ATTEMPT=BASE/'attempt-02'


def sha(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1<<20),b''):digest.update(chunk)
    return digest.hexdigest()


def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def save(path,value):
    assert not path.exists(),str(path)
    path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def main():
    original=read(BASE/'freeze.json');bank_seal=read(BASE/'bank_seal.json')
    source=read(BASE/'source_binding_validation.json');source_seal=read(BASE/'source_binding_seal.json')
    amended=read(ATTEMPT/'freeze.json');result=read(ATTEMPT/'validation.json')
    assert result['passed'] and result['decision']=='NO_FOUR_PAIR_FEEDBACK_RESPONSE'
    assert result['response_cases']==2 and result['required']==4
    assert result['dataset_gt_read'] is False and result['pose_accuracy_computed'] is False
    assert source['passed'] and source['dataset_gt_read'] is False
    assert bank_seal['freeze_sha256']==sha(BASE/'freeze.json')
    assert bank_seal['bank_sha256']==sha(BASE/'bank.json')
    assert len(bank_seal['files'])==96
    for name,digest in original['files'].items():assert sha(name)==digest,name
    for name,digest in bank_seal['files'].items():assert sha(BASE/name)==digest,name
    assert source_seal['validation_sha256']==sha(BASE/'source_binding_validation.json')
    assert source_seal['freeze_sha256']==sha(BASE/'freeze.json')
    assert source_seal['bank_seal_sha256']==sha(BASE/'bank_seal.json')
    assert amended['original_freeze_sha256']==sha(BASE/'freeze.json')
    assert amended['original_bank_seal_sha256']==sha(BASE/'bank_seal.json')
    for name,digest in amended['files'].items():assert sha(name)==digest,name
    assert result['freeze_sha256']==sha(BASE/'freeze.json')
    assert result['bank_seal_sha256']==sha(BASE/'bank_seal.json')
    assert result['amendment_freeze_sha256']==sha(ATTEMPT/'freeze.json')
    assert result['source_binding_sha256']==sha(BASE/'source_binding_validation.json')
    assert result['combined_wall_s']<=original['limits']['wall_s']
    assert result['peak_rss_bytes']<=original['limits']['rss_bytes']
    assert result['peak_allocated_bytes']<=original['limits']['gpu_bytes']
    assert (BASE/'INCOMPLETE').exists() and not (BASE/'validation.json').exists()
    now=datetime.now(timezone.utc).isoformat()
    save(ATTEMPT/'validation_seal.json',dict(stage='D1_VALIDATOR_REPAIR_02',utc=now,
        original_freeze_sha256=sha(BASE/'freeze.json'),bank_seal_sha256=sha(BASE/'bank_seal.json'),
        source_binding_seal_sha256=sha(BASE/'source_binding_seal.json'),
        amendment_freeze_sha256=sha(ATTEMPT/'freeze.json'),validation_sha256=sha(ATTEMPT/'validation.json'),
        bank_reused_without_inference=True,passed=True))
    status=dict(stage='D1',status='VALIDATED_NEGATIVE',decision=result['decision'],utc=now,
        frozen_identity_count=len(original['files']),sealed_npz_count=len(bank_seal['files']),
        source_binding_passed=True,numerical_validation_passed=True,
        response_cases=2,response_required=4,
        original_validator_failed='FAILURE_01.json',repair='AMENDMENT_01.md',
        repaired_validation='attempt-02/validation.json',
        original_bank_preserved=True,gt_read=False,pose_accuracy_computed=False,
        originality_established=False,
        next_stage=dict(status='PLANNED_READ_ONLY',plan='NEXT_ROUND_PLAN.md',D2_licensed=False),
        combined_wall_s=result['combined_wall_s'],peak_rss_bytes=result['peak_rss_bytes'],
        peak_allocated_bytes=result['peak_allocated_bytes'],
        original_head_rap='4055d929c594b0033aafc6eed339c910369eef55',
        original_head_slam='6d3f2d22cedfe1f807deb11fd8796b9f5bf17cd6')
    (BASE/'STATUS.json').write_text(json.dumps(status,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    assert sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file())<original['limits']['artifact_bytes']
    (BASE/'INCOMPLETE').unlink()
    listed=[BASE/name for name in ('REPORT.md','PROTOCOL.md','NEXT_ROUND_PLAN.md','HANDOFF.md','STATUS.json',
        'AMENDMENT_01.md','FAILURE_01.json','manifest.json','freeze.json','bank.json','bank_seal.json',
        'source_binding_validation.json','source_binding_seal.json')]
    listed += [ATTEMPT/name for name in ('PROTOCOL.md','freeze.json','validation.json','validation_seal.json')]
    save(BASE/'artifact_hashes.json',dict(stage='D1',kind='delivery_only_original_freeze_and_bank_seal_authoritative',utc=now,
        files=[dict(path=p.relative_to(BASE).as_posix(),sha256=sha(p),size=p.stat().st_size) for p in listed]))
    total=sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file())
    assert total<original['limits']['artifact_bytes']
    print(json.dumps(dict(status='VALIDATED_NEGATIVE',response_cases=2,required=4,
        sealed_files=len(bank_seal['files']),total_artifact_bytes=total,incomplete_marker=False)))


if __name__=='__main__':main()
