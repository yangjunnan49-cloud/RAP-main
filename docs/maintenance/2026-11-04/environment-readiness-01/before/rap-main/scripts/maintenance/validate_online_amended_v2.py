"""Verify both engineering amendments, then run unchanged-threshold validation."""
import json,hashlib,runpy
from pathlib import Path
B=Path('/mnt/e/githouse/RAP-main/docs/maintenance/2026-10-05/online-geotransformer-01')
for name in ['amendment_freeze.json','amendment_02_freeze.json']:
    freeze=json.loads((B/name).read_text())
    for p,h in freeze['files'].items(): assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h,p
    assert hashlib.sha256((B/'freeze.json').read_bytes()).hexdigest()==freeze['original_freeze_sha256']
runpy.run_path(str(Path(__file__).with_name('validate_online_geotransformer_v2.py')),run_name='__main__')
