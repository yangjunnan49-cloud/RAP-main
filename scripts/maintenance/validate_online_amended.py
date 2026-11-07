"""Verify the serialization amendment then invoke the frozen validator."""
import sys,json,hashlib,runpy
from pathlib import Path
B=Path('/mnt/e/githouse/RAP-main/docs/maintenance/2026-10-05/online-geotransformer-01')
freeze=json.loads((B/'amendment_freeze.json').read_text())
for p,h in freeze['files'].items(): assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h,p
assert hashlib.sha256((B/'freeze.json').read_bytes()).hexdigest()==freeze['original_freeze_sha256']
target=Path(__file__).with_name('validate_online_inputs_v2.py' if sys.argv[1]=='inputs' else 'validate_online_geotransformer.py')
runpy.run_path(str(target),run_name='__main__')
