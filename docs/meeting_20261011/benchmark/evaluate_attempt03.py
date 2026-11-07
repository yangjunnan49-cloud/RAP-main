from pathlib import Path
import json,hashlib
import repeat_systems as r
import evaluate_repeats as v
base=Path(__file__).resolve().parent
f=json.loads((base/'evaluation03_routing_freeze.json').read_text());assert f['sha256']==hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
r.BASE=base/'attempt03';v.BASE=r.BASE
v.main()
