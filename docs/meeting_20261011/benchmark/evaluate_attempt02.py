from pathlib import Path
import json,hashlib
import repeat_systems as r
import evaluate_repeats as v
base=Path(__file__).resolve().parent
p=base/'evaluation_routing_freeze.json'
f=json.loads(p.read_text());assert f['sha256']==hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
r.BASE=base/'attempt02';v.BASE=r.BASE
v.main()
