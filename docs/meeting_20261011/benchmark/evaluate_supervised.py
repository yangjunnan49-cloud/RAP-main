from pathlib import Path
import hashlib,json,runpy,sys
base=Path(__file__).resolve().parent
f=json.loads((base/'evaluation_supervision_freeze.json').read_text())
for p,h in f.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h,p
receipt=base/'attempt03/evaluation.resource.json'
sys.argv=[str(base/'attempt03/child_capture.py'),str(receipt),str(base/'evaluate_attempt03.py')]
runpy.run_path(sys.argv[0],run_name='__main__')
