"""Bind a validator-only D1 repair to the original immutable sealed bank."""
from __future__ import annotations
import hashlib,json,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'docs/maintenance/2026-10-06/shared-identity-engineering-01'
ATTEMPT=BASE/'attempt-02'


def sha(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1<<20),b''): digest.update(chunk)
    return digest.hexdigest()


def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def main():
    assert not (ATTEMPT/'freeze.json').exists()
    original=read(BASE/'freeze.json');seal=read(BASE/'bank_seal.json')
    source_seal=read(BASE/'source_binding_seal.json')
    assert original['stage']==seal['stage']=='D1'
    assert seal['freeze_sha256']==sha(BASE/'freeze.json')
    assert seal['bank_sha256']==sha(BASE/'bank.json')
    assert len(seal['files'])==96
    for name,digest in original['files'].items(): assert sha(name)==digest,name
    for name,digest in seal['files'].items(): assert sha(BASE/name)==digest,name
    assert source_seal['validation_sha256']==sha(BASE/'source_binding_validation.json')
    assert read(BASE/'source_binding_validation.json')['passed'] is True
    names=[Path(__file__),Path(__file__).with_name('validate_shared_identity_engineering_v2.py'),
           Path(__file__).with_name('validate_shared_identity_engineering.py'),
           ATTEMPT/'PROTOCOL.md',BASE/'AMENDMENT_01.md',BASE/'FAILURE_01.json',
           BASE/'freeze.json',BASE/'bank.json',BASE/'bank_seal.json',
           BASE/'source_binding_validation.json',BASE/'source_binding_seal.json',
           Path(sys.executable)]
    ATTEMPT.mkdir(parents=True,exist_ok=True)
    (ATTEMPT/'freeze.json').write_text(json.dumps(dict(
        stage='D1_VALIDATOR_REPAIR_02',created_utc=datetime.now(timezone.utc).isoformat(),
        repair_scope='Exclude root-only wall_seconds metadata from repeat key-set comparison',
        original_freeze_sha256=sha(BASE/'freeze.json'),
        original_bank_seal_sha256=sha(BASE/'bank_seal.json'),
        files={str(path):sha(path) for path in names},
        samples_controls_thresholds_outputs_changed=False,model_rerun=False,
        gt_read=False),indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print('D1 validator attempt-02 frozen',len(names),'identities')


if __name__=='__main__': main()
