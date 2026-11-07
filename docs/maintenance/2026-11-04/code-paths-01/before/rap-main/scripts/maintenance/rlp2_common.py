"""RLP2 isolated bookkeeping using existing sealed identity utilities."""
import rlp1_common as _r
import local_motion_common as c
from pathlib import Path

B = c.MAIN/'docs/maintenance/2026-10-08/motion-supervised-readout-01'
DESIGN = c.MAIN/'docs/maintenance/2026-10-08/readout-task-redesign-01'
OLD = c.MAIN/'docs/maintenance/2026-10-08/readout-pilot-01'
ENG = OLD/'engineering-preflight/attempt-03'
STOP = OLD/'prerequisite-stop-audit'
NUM = B/'numerical-preflight'
FULL = B/'full-bank'
LAB = B/'pose-targets'
FIT = B/'fits'
PRED = B/'predictions'
DIAG = B/'diagnostics'
EVAL = B/'evaluation'
HELPER = c.SLAM/'scripts/motion_supervised_readout.py'
SEEDS = (20261007,20261008,20261009)
_r.B = B
_r.HELPER = HELPER
rows,stem,runtime = _r.rows,_r.stem,_r.runtime
check,seal,check_seal,validated = _r.check,_r.seal,_r.check_seal,_r.validated
usage,cap,finish,fail,pass_validation = _r.usage,_r.cap,_r.finish,_r.fail,_r.pass_validation

def freeze(base,selected,script,validator,**kw):
    extra=kw.pop('extra_files',[])
    extra += [Path(__file__),DESIGN/'PLAN.md',DESIGN/'DELIVERY_SEAL.json',
              Path(__file__).with_name('rlp2_independent.py'),
              Path(__file__).with_name('rlp1_validation_math.py')]
    _r.freeze(base,selected,script,validator,extra_files=extra,**kw)

def order(seed):
    import hashlib
    return sorted([x for x in rows() if x['role']=='fit'],
        key=lambda x:hashlib.sha256(f"RLP1-order|{seed}|{x['seq']}|{x['t']}".encode()).hexdigest())
