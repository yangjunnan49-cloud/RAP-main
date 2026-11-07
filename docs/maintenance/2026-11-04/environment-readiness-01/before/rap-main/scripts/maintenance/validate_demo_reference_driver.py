"""Resource enclosure for the separately bound DRD0 validator syntax variant."""
import time
START=time.monotonic()
import ast,json,resource,runpy
from pathlib import Path
source=Path(__file__).with_name('validate_demo_reference_documents_attempt02.py')
base=Path(__file__).resolve().parents[2]/'docs/maintenance/2026-10-15/demo-reference-documentation-01'
ok=False;error=None
try:
    ast.parse(source.read_text())
    runpy.run_path(str(source),run_name='__main__')
    ok=True
except BaseException as ex:
    error=repr(ex);raise
finally:
    result=dict(success=ok,error=error,seconds=time.monotonic()-START,
        peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
        syntax_checked_before_execution=True,original_prestart_peak_RSS='UNKNOWN_NOT_RETROSPECTIVELY_REPAIRED')
    with (base/'driver_resource.json').open('x') as f:json.dump(result,f,indent=2)
