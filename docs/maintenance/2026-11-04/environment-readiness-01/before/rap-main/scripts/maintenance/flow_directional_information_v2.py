"""FDI1 amendment 01: restore original F2 non-confuser cohort identities."""
import time
import numpy as np
import flow_directional_information as h
import flow_directional_response as f

LABELS={'00':f.MAIN/'docs/maintenance/2026-09-14/hl-v2/data-expansion-01/discovery_evaluator.json','08':f.MAIN/'docs/maintenance/2026-09-14/support-control-01/data/confirmation_evaluator.json'}
def verify_amendment():
    a=f.read(h.B/'amendment_freeze.json'); assert a['original_freeze_sha256']==f.sha(h.B/'freeze.json') and a['original_bank_seal_sha256']==f.sha(h.B/'bank_seal.json')
    for p,digest in a['files'].items(): assert f.sha(p)==digest,p
def cohorts():
    data={}
    for s,p in LABELS.items():
        labels=f.read(p); data[s]={(r['source_i'],r['source_j']):r['stratum'] for r in labels}
        assert set(data[s])=={(r['i'],r['j']) for r in h.selection() if r['seq']==s}
        assert {name:sum(v==name for v in data[s].values()) for name in ['confuser','ambiguous_positive','low_overlap','ordinary']}=={name:25 for name in ['confuser','ambiguous_positive','low_overlap','ordinary']}
    return data
def evaluate():
    h.verify(); verify_amendment(); B=h.B; seal=f.read(B/'bank_seal.json'); assert seal['files']=={p.name:f.sha(p) for p in (B/'bank').iterdir()}; start=f.now(); t=time.monotonic(); h.state('EVALUATING_V2'); membership=cohorts(); gt={s:h.gt(s) for s in ['00','08']}; rows=[]
    for r in h.selection():
        G=np.linalg.inv(gt[r['seq']][r['i']])@gt[r['seq']][r['j']]; stratum=membership[r['seq']][(r['i'],r['j'])]
        with np.load(B/'bank'/f"{r['key']}.npz",allow_pickle=False) as a:
            e=f.log(np.linalg.inv(a['full'][-1])@G)/f.D; scores={c:h.score(e,a[k]) for c,k in dict(J='C_total',I='C_control',G='C_geometry',T='C_time').items()}; scores['S']=1/6 if float(e@e)>=1e-12 else None
            rows.append(dict(r,stratum=stratum,positive=stratum!='confuser',native_available=any(h.strict(T,G) for T in a['native_T']),N0_strict=h.strict(a['N0_T'],G),e_normalized=e.tolist(),scores=scores))
    summary,gates,decision=h.aggregate(rows); f.save(B/'results-v2.json',dict(gt_read_started_utc=start,completed_utc=f.now(),bank_seal_sha256=f.sha(B/'bank_seal.json'),amendment_freeze_sha256=f.sha(B/'amendment_freeze.json'),rows=rows,summary=summary,gates=gates,decision=decision,wall_s=time.monotonic()-t)); h.state('EVALUATED_V2',decision=decision); print(decision,summary['08_hard'],flush=True)
if __name__=='__main__': evaluate()
