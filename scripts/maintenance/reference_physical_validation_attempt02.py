"""RPC0 independently frozen validator-only attempt; original results immutable."""
import signal
import sys
import time
import traceback
from pathlib import Path
import reference_physical_consistency as r
import validate_reference_physical as v

def freeze02():
    original=r.read(r.BASE/'freeze.json'); old=r.BASE/'source_snapshot/main_validate_reference_physical.py'
    validator=Path(v.__file__).resolve(); assert original['files'][str(validator)]==r.sha(old)
    for p,h in original['files'].items():
        if p!=str(validator): assert r.sha(p)==h,p
    assert original['repositories']==r.c.repositories()
    snapshot=r.BASE/'validation_attempt02_sources'; snapshot.mkdir()
    sources=[validator,Path(__file__).resolve()]
    for p in sources: (snapshot/p.name).write_bytes(p.read_bytes())
    files=sources+[old,r.BASE/'AMENDMENT_01.md',r.BASE/'freeze.json',r.BASE/'results.json',r.BASE/'bank_seal.json',r.BASE/'evaluation_seal.json',
        r.BASE/'FAILURE_validate.json',r.SUP/'validate/child_exit.json',r.SUP/'validate/exit.json']+list(snapshot.iterdir())
    r.save(r.BASE/'VALIDATION_AMENDMENT_FREEZE02.json',dict(utc=r.now(),files={str(p):r.sha(p) for p in files},
        original_validator_path=str(validator),original_validator_sha256=original['files'][str(validator)],original_validator_snapshot=str(old),
        repaired_validator_sha256=r.sha(validator),replaced_scientific_inputs=0,tolerance_changed=False))
    print('validator-only amendment frozen; original outputs unchanged',flush=True)

def main(stage):
    r.START=time.monotonic(); used=sum(r.read(p)['wall_seconds'] for p in r.SUP.glob('*/child_exit.json')); assert used<900
    signal.signal(signal.SIGALRM,lambda a,b:(_ for _ in ()).throw(TimeoutError('RPC0 combined payload cap'))); signal.alarm(max(1,int(900-used)))
    success=False; error=None
    try:
        r.cap()
        if stage=='freeze02': freeze02()
        elif stage=='validate_preflight02': v.validate_rotation_contract()
        elif stage=='validate02': v.validate()
        else: raise ValueError(stage)
        r.cap(); success=True
    except BaseException as ex:
        error=repr(ex); traceback.print_exc(); r.save(r.BASE/f'FAILURE_{stage}.json',dict(utc=r.now(),error=error,**r.usage()))
    finally:
        signal.alarm(0); r.save(r.SUP/stage/'child_exit.json',dict(utc=r.now(),success=success,error=error,full_resource_capture=True,**r.usage()))
    if not success: sys.exit(1)
if __name__=='__main__': main(sys.argv[1])
