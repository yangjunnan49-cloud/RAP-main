"""Standalone measured pilot figure; no model fitting or decision changes."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
ROOT=Path('/mnt/e/githouse/RAP-main/docs/maintenance/2026-09-14/hl-v2/pilot-01')
methods=['B1','B4','S4','R4','OR4'];colors=['#aeb8c1','#31688e','#21918c','#c18a36','#7c5b9c']
fig,axes=plt.subplots(1,2,figsize=(12,5))
for ax,role,seq in zip(axes,['discovery','confirmation'],['00','02']):
    m=json.loads((ROOT/role/'metrics.json').read_text());v=[m['overall'][s] for s in methods]
    bars=ax.bar(methods,[x['strict_positive_successes'] for x in v],color=colors,width=.62)
    for bar,x in zip(bars,v):ax.text(bar.get_x()+bar.get_width()/2,bar.get_height()+1,f"{x['strict_positive_successes']}/75",ha='center',fontsize=10)
    ax.set_ylim(0,80);ax.set_ylabel('Strict successes among75 positive pairs');ax.set_title(f"KITTI{seq} {role}\n{m['decision']}");ax.spines[['top','right']].set_visible(False);ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True)
fig.suptitle('HL-V2: one frozen K4 bank per role, unchanged1m/5deg success')
fig.text(.5,.01,'S4: raw support; R4: official rigidity; OR4: GT-only diagnostic upper bound. Development cohorts, not independent-domain evidence.',ha='center',fontsize=9)
fig.tight_layout(rect=[0,.05,1,.95]);fig.savefig(ROOT/'selection_results.png',dpi=160);plt.close(fig)
