"""Freeze validated data-only roles and plot fixed-label examples."""
import hashlib,json
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path('/mnt/e/githouse/RAP-main')
OUT=ROOT/'docs/maintenance/2026-09-14/hl-v2/data-expansion-01'
STRATA=['confuser','ambiguous_positive','low_overlap','ordinary']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):
    with p.open('x') as f:json.dump(v,f,indent=2,allow_nan=False)
fig,axes=plt.subplots(2,4,figsize=(18,9));counts=[]
for row,(role,seq) in enumerate([('discovery','00'),('confirmation','02')]):
    folder=OUT/seq;validation=json.loads((folder/'validation.json').read_text());assert validation['passed']
    adequate=json.loads((folder/'adequacy.json').read_text());assert adequate['adequate'] and adequate['headroom']
    labels=json.loads((folder/'selected_evaluator.json').read_text())
    groups=[[r for r in labels if r['stratum']==s] for s in STRATA]
    # Interleaving only changes execution order, never selected membership.
    ordered=[groups[k][i] for i in range(25) for k in range(4)]
    save(OUT/f'{role}_evaluator.json',ordered)
    save(OUT/f'{role}_inputs.json',[{k:r[k] for k in ['sequence','source_i','source_j','support_i','support_j']} for r in ordered])
    counts.append(adequate);geom=np.load(folder/'label_geometry.npz');gt=np.load(folder/'evaluator_gt.npy')
    for col,group in enumerate(groups):
        r=group[0];i,j=r['source_i'],r['source_j'];p=geom[str(i)];q=geom[str(j)];T=np.linalg.inv(gt[i])@gt[j];q=q@T[:3,:3].T+T[:3,3]
        ax=axes[row,col];ax.scatter(p[:,0],p[:,1],s=.3,alpha=.5);ax.scatter(q[:,0],q[:,1],s=.3,alpha=.5)
        ax.set_aspect('equal');ax.set_title(f"{seq} {STRATA[col]}\n({i},{j}), overlap={r['GT_overlap']:.3f}");ax.set_xlabel('x (m)');ax.set_ylabel('y (m)')
fig.suptitle('HL-V2 fixed sample examples: GT-aligned XY; proxy labels, no membership filtering')
fig.tight_layout();fig.savefig(OUT/'sample_examples.png',dpi=140);plt.close(fig)
save(OUT/'cohort_freeze.json',dict(protocol='HL-V2',frozen_utc=datetime.now(timezone.utc).isoformat(),roles={'discovery':['00'],'confirmation':['02']},
    hypotheses_generated_before_freeze=0,counts=counts,hashes={p.name:sha(p) for p in OUT.glob('*_inputs.json')},
    evaluator_hashes={p.name:sha(p) for p in OUT.glob('*_evaluator.json')},
    source_hashes={str(p):sha(p) for p in [Path('/mnt/e/githouse/RAP-SLAM/scripts/hl2_data_bridge.py'),Path('/mnt/e/githouse/RAP-SLAM/scripts/validate_hl_v2_data.py')]},
    protocol_sha256=sha(OUT/'PROTOCOL.md'),preflight_order='First ten round-robin stratum samples:3confuser,3ambiguous,2low,2ordinary'))
print('Frozen 100 discovery + 100 confirmation pairs; each role25 per stratum')
