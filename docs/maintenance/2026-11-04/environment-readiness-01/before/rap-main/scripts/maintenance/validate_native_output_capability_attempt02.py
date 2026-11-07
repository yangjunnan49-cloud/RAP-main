"""Hash-bound NOC0 validator routed to the numerically repaired retry."""
from pathlib import Path
import json
import hashlib
_source=Path(__file__).with_name('validate_native_output_capability.py')
_root=_source.parents[2]/'docs/maintenance/2026-10-10/native-output-capability-01'
_freeze=json.loads((_root/'freeze.json').read_text())
assert hashlib.sha256(_source.read_bytes()).hexdigest()==_freeze['files'][str(_source)]
_code=_source.read_text()
assert _code.count("with_name('native_output_capability.py')")==1
_code=_code.replace("with_name('native_output_capability.py')","with_name('native_output_capability_attempt02.py')")
exec(compile(_code,str(_source)+'[attempt02-routing]', 'exec'),globals())
