"""Preserve v2 result identity and pin independent log convention repair."""
from pathlib import Path
import flow_directional_information as h
import flow_directional_response as f
import flow_directional_information_v2 as v
if __name__=='__main__':
    h.verify(); v.verify_amendment(); files=[h.B/'AMENDMENT_02.md',h.B/'FAILURE_02.json',Path(__file__),Path(__file__).with_name('validate_flow_directional_information_v3.py'),Path(__file__).with_name('diagnose_fdi_log_convention.py')]
    f.save(h.B/'amendment_02_freeze.json',dict(utc=f.now(),results_v2_sha256=f.sha(h.B/'results-v2.json'),amendment_01_sha256=f.sha(h.B/'amendment_freeze.json'),files={str(p):f.sha(p) for p in files},scope='validator-only independent SO3 recovery for GT error logarithm'))
    print('second amendment frozen',flush=True)
