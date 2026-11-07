"""Read-only engineering diagnosis after D0's pre-label gate assertion."""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
import d0_flow_trajectory as d0
from d0_flow_trajectory import g0,g1,v0,F2

g=v0.gate_backend()
for seq in ('00','08'):
    records=g0.read(F2/seq/'records.json')
    gates=g0.read(F2/seq/'gates.json')
    max_pose=max_overlap=max_dist=0.0
    worst=None
    for ix,pair in enumerate(g0.order(seq)):
        rec=[r for r in records if r['pair']==pair and r['arm']=='N']
        chosen=min(rec,key=lambda r:(r['rigidity_rmse_m'],r['generation']))
        folder=F2/seq/pair
        with np.load(folder/'inputs.npz',allow_pickle=False) as a:
            cond,counts,centers,scale=(a[x] for x in ('cond','counts','centers','scale'))
        with np.load(folder/f'N{chosen["generation"]}.npz',allow_pickle=False) as a:
            raw=a['end_point_trajectory'][-1]
        reconstructed=d0.decode_one(cond,raw,counts,centers,float(scale))
        saved=np.asarray(chosen['T'])
        tp,sp=g1.pair_scans(seq,pair)
        t=g.preprocess(g1.load_scan(tp))[0]
        s=g.preprocess(g1.load_scan(sp))[0]
        x=g._alignment_metrics(t,s,reconstructed,thresh=1.)
        y=g._alignment_metrics(t,s,saved,thresh=1.)
        old=gates[pair]['N'][str(chosen['generation'])]
        pd=float(np.max(np.abs(reconstructed-saved)))
        od=abs(x[0]-old['overlap_ratio'])
        md=abs(x[1]-old['mean_dist'])
        if md>max_dist:
            worst=(ix,pair,pd,od,md,x,y,(old['overlap_ratio'],old['mean_dist']))
        max_pose=max(max_pose,pd)
        max_overlap=max(max_overlap,od)
        max_dist=max(max_dist,md)
    print(seq,'max pose',max_pose,'max overlap',max_overlap,'max mean distance',max_dist,'worst',worst,flush=True)
