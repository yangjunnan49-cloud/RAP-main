"""Validator-only MF0 retry with unchanged membership banks and cost evaluator."""
import argparse
import shutil
from pathlib import Path
import membership_formation_diagnosis as original

ROOT_BASE = original.BASE
BASE = ROOT_BASE/'attempt-02'
original.BASE = BASE
MAIN,SLAM,CV2,DATA,SEQUENCES = original.MAIN,original.SLAM,original.CV2,original.DATA,original.SEQUENCES
read,save,sha,utc,verify,record = original.read,original.save,original.sha,original.utc,original.verify,original.record


def freeze():
    old=read(ROOT_BASE/'freeze.json')
    assert (ROOT_BASE/'FAILURE_validate_bank.json').exists() and (ROOT_BASE/'INCOMPLETE').exists()
    for name,digest in old['files'].items():assert sha(name)==digest,name
    for name,digest in read(ROOT_BASE/'bank_seal.json')['files'].items():assert sha(ROOT_BASE/'bank'/name)==digest
    bank=BASE/'bank';bank.mkdir()
    for p in (ROOT_BASE/'bank').iterdir():shutil.copyfile(p,bank/p.name)
    shutil.copyfile(ROOT_BASE/'bank_seal.json',BASE/'bank_seal.json')
    shutil.copyfile(ROOT_BASE/'preflight.json',BASE/'preflight.json')
    sources=[Path(__file__),Path(__file__).with_name('validate_membership_formation_attempt02.py'),ROOT_BASE/'AMENDMENT_01.md']
    snapshot=BASE/'source_snapshot';snapshot.mkdir()
    files=list(old['files'])+[str(ROOT_BASE/p) for p in ('freeze.json','bank_seal.json','preflight.json','FAILURE_validate_bank.json','RESOURCE_LOG.json','INCOMPLETE')]
    files += [str(p) for p in (ROOT_BASE/'bank').iterdir()]+[str(p) for p in bank.iterdir()]
    files += [str(BASE/'bank_seal.json'),str(BASE/'preflight.json')]
    for i,p in enumerate(sources):
        q=snapshot/f'{i:02d}-{p.name}';shutil.copyfile(p,q);files += [str(p),str(q)]
    save(BASE/'freeze.json',dict(utc=utc(),files={p:sha(p) for p in dict.fromkeys(files)},packages=old['packages'],bindings=old['bindings'],
        amendment='VALIDATOR_LIST_OF_DICTIONARIES_ONLY',original_membership_bank_reused_byte_exact=True,
        new_membership_calls=0,optimizer_calls=0,scientific_settings_unchanged=True))
    (BASE/'INCOMPLETE').write_text('Attempt-02 requires complete census and cost validation\n')
    print('MF0 validator-only attempt frozen',len(set(files)),flush=True)


def evaluate():
    original.evaluate()


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=('freeze','evaluate'))
    stage=parser.parse_args().stage
    if stage=='freeze':
        BASE.mkdir()
        shutil.copyfile(ROOT_BASE/'RESOURCE_LOG.json',BASE/'RESOURCE_LOG.json')
    record('amendment_freeze' if stage=='freeze' else stage,globals()[stage])
