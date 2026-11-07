"""Bind correction to original F2 evaluator identities; no matrix regeneration."""
from pathlib import Path
import flow_directional_information as h
import flow_directional_response as f
import flow_directional_information_v2 as v

if __name__=='__main__':
    h.verify(); original=f.read(f.OLD/'freeze.json'); paths=[h.B/'AMENDMENT_01.md',h.B/'FAILURE_01.json',Path(__file__),Path(v.__file__),Path(__file__).with_name('validate_flow_directional_information_v2.py'),f.OLD/'PROTOCOL.md',f.OLD/'freeze.json']
    for s,p in v.LABELS.items():
        paths.extend([p,p.parent/s/'evaluator_gt.npy'])
        for q in [p,p.parent/s/'evaluator_gt.npy']: assert f.sha(q)==original['parents'][str(q)]
    f.save(h.B/'amendment_freeze.json',dict(utc=f.now(),original_freeze_sha256=f.sha(h.B/'freeze.json'),original_bank_seal_sha256=f.sha(h.B/'bank_seal.json'),files={str(p):f.sha(p) for p in paths},scope='original non-confuser identity binding; unchanged 200 bank files and every gate'))
    print('amendment identities frozen',len(paths),flush=True)
