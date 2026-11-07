import hashlib,json,statistics
from collections import Counter
from pathlib import Path
root=Path(r"E:\githouse\RAP-main\docs\maintenance\2026-10-26\camera-support-upper-bound-01")
repo=root.parents[3]
seal=json.loads((root/"PRIMARY_SEAL.json").read_text(encoding="utf-8"))
for item in seal["files"]:
 p=root/item["path"];assert p.stat().st_size==item["bytes"] and hashlib.sha256(p.read_bytes()).hexdigest()==item["sha256"]
prior=json.loads((repo/"docs/maintenance/2026-09-27/f2-structured-dev-01/freeze.json").read_text(encoding="utf-8"))
paths=[repo/"docs/maintenance/2026-09-14/hl-v2/data-expansion-01/discovery_evaluator.json",repo/"docs/maintenance/2026-09-14/support-control-01/data/confirmation_evaluator.json"]
labels={};bindings=[]
for p in paths:
 old="/mnt/e/"+p.as_posix()[3:]
 digest=hashlib.sha256(p.read_bytes()).hexdigest()
 assert prior["parents"][old]==digest
 data=json.loads(p.read_text(encoding="utf-8"),parse_int=str,parse_float=str)
 assert len(data)==100
 for r in data:
  key=f'{r["sequence"]}_{r["source_i"]}_{r["source_j"]}'
  assert key not in labels
  labels[key]=r["stratum"]
 bindings.append(dict(path=str(p),sha256=digest,counts=dict(Counter(r["stratum"] for r in data))))
rows=json.loads((root/"ROWS.json").read_text(encoding="utf-8"))
groups={}
for row in rows:
 assert row["key"] in labels
 group=(row["sequence"],labels[row["key"]])
 groups.setdefault(group,[]).append(row)
out=[]
for (seq,stratum),g in sorted(groups.items()):
 by_pair={}
 for r in g:by_pair.setdefault(r["key"],[]).append(r)
 assert len(by_pair)==25 and len(g)==50 and all(len(v)==2 for v in by_pair.values())
 out.append(dict(sequence=seq,stratum=stratum,pairs=25,directions=50,
  zero_upper_directions=sum(r["numerical_upper_count"]==0 for r in g),
  zero_upper_both_directions_pairs=sum(all(r["numerical_upper_count"]==0 for r in v) for v in by_pair.values()),
  zero_upper_either_direction_pairs=sum(any(r["numerical_upper_count"]==0 for r in v) for v in by_pair.values()),
  fraction_median=statistics.median(r["fraction_of_source_occurrences"] for r in g)))
result=dict(primary_seal_verified=True,stratum_sources=bindings,all_pairs_retained=True,complete_pairs=len(labels),cells=out,readout_role="Supplementary exposed-cohort description only; no support-subset selection or efficacy gate")
with (root/"STRATUM_READOUT.json").open("x",encoding="utf-8") as f:json.dump(result,f,indent=2)
print(json.dumps(out,indent=2))