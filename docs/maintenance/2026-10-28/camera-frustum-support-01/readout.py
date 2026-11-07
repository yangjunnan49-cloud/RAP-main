import collections,hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[3]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
seal=json.loads((ROOT/'PRIMARY_SEAL.json').read_text(encoding='utf-8-sig'))
for e in seal['files']:
    p=ROOT/e['path'];assert p.stat().st_size==e['bytes'] and sha(p)==e['sha256']
prior=json.loads((REPO/'docs/maintenance/2026-09-27/f2-structured-dev-01/freeze.json').read_text());labels={};bindings=[]
for rel in ['docs/maintenance/2026-09-14/hl-v2/data-expansion-01/discovery_evaluator.json','docs/maintenance/2026-09-14/support-control-01/data/confirmation_evaluator.json']:
    p=REPO/rel;digest=sha(p);assert prior['parents']['/mnt/e/'+p.as_posix()[3:]]==digest
    data=json.loads(p.read_text(encoding='utf-8'),parse_int=str,parse_float=str);assert len(data)==100
    for r in data:
        key=f"{r['sequence']}_{r['source_i']}_{r['source_j']}";assert key not in labels;labels[key]=r['stratum']
    bindings.append({'path':str(p),'sha256':digest})
rows=json.loads((ROOT/'ROWS.json').read_text());assert len(rows)==400 and len(labels)==200;groups={}
for r in rows:groups.setdefault((r['sequence'],labels[r['key']]),[]).append(r)
out=[]
for (seq,stratum),g in sorted(groups.items()):
    pairs={}
    for r in g:pairs.setdefault(r['key'],[]).append(r)
    assert len(g)==50 and len(pairs)==25 and all(len(v)==2 for v in pairs.values())
    out.append({'sequence':seq,'stratum':stratum,'pairs':25,'directions':50,'center_domain_occurrences':sum(r['center_domain_joint'] for r in g),'edge_upper_occurrences':sum(r['half_pixel_edge_upper'] for r in g),'zero_upper_directions':sum(r['half_pixel_edge_upper']==0 for r in g),'zero_upper_both_pairs':sum(all(r['half_pixel_edge_upper']==0 for r in v) for v in pairs.values()),'unconditional_upper_fraction_median':statistics.median(r['fraction_of_source_upper'] for r in g)})
positive=[]
for seq in ['00','08']:
    cells=[c for c in out if c['sequence']==seq and c['stratum']!='confuser'];assert len(cells)==3 and sum(c['pairs'] for c in cells)==75
    positive.append({'sequence':seq,'original_positive_pairs':75,'zero_upper_both_pairs':sum(c['zero_upper_both_pairs'] for c in cells),'zero_upper_directions':sum(c['zero_upper_directions'] for c in cells)})
result={'primary_seal_verified':True,'source_labels_bound':bindings,'complete_pairs':200,'cells':out,'original_positive_aggregates':positive,'no_raw_image_pose_geometry_replay':True,'role':'Complete saved-output descriptive join, no model or efficacy gate'}
(ROOT/'STRATUM_READOUT.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
