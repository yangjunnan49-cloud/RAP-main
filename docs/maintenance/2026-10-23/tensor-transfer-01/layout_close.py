"""Read sealed metadata only after TT1 stop; no tensor decoding or retry."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
m=json.loads((ROOT/'STATE_METADATA.json').read_text())
rows=[]
for key,meta in m['archives'][1]['state'].items():
    if not key.startswith('Desc.'):continue
    step=1;stride=[]
    for d in reversed(meta['shape']):stride.append(step);step*=d
    canonical=list(reversed(stride))
    if meta['stride']!=canonical:
        dims=[i for i,(a,b) in enumerate(zip(meta['stride'],canonical)) if a!=b]
        rows.append(dict(key=key,shape=meta['shape'],recorded_stride=meta['stride'],canonical_stride=canonical,
            differing_axes=dims,all_differences_singleton=all(meta['shape'][i]==1 for i in dims)))
result=dict(first_rejected_key=rows[0]['key'] if rows else None,canonical_stride_rejections=len(rows),rows=rows,
    numerical_retry=False,gate_widened=False,values_decoded=False,
    partial_RAP_counter=344,no_sealed_partial_per_tensor_result=True,
    limitation='Singleton-axis stride equivalence is metadata interpretation only; TT1 canonical-stride gate remains unchanged and failed')
with (ROOT/'LAYOUT_AFTER_STOP.json').open('x') as f:json.dump(result,f,indent=2)
print(json.dumps(result,indent=2))
