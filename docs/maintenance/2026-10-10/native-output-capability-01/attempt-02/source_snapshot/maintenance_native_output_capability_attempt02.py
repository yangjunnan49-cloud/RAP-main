"""Hash-bound NOC0 retry: fixed numerical loss scale, separate outputs."""
from pathlib import Path
import json
import hashlib

_source=Path(__file__).with_name('native_output_capability.py')
_root=_source.parents[2]/'docs/maintenance/2026-10-10/native-output-capability-01'
_freeze=json.loads((_root/'freeze.json').read_text())
assert hashlib.sha256(_source.read_bytes()).hexdigest()==_freeze['files'][str(_source)]
_code=_source.read_text()
_old="BASE=c.MAIN/'docs/maintenance/2026-10-10/native-output-capability-01'"
assert _code.count(_old)==1
_code=_code.replace(_old,_old.replace('BASE=','ROOT=')+"\nBASE=ROOT/'attempt-02'")
_code=_code.replace("BASE.rglob('*') if p.is_file()","ROOT.rglob('*') if p.is_file()")
_code=_code.replace("validate_native_output_capability.py","validate_native_output_capability_attempt02.py")
_old="loss=(v-(noise-y)).square().mean();loss.backward();groups=inspect_grad(params)"
assert _code.count(_old)==1
_code=_code.replace(_old,"loss=(v-(noise-y)).square().mean();(loss*1024).backward()\n        for p in params.values(): p.grad.div_(1024)\n        groups=inspect_grad(params)")
_old="files=c.frozen_sources()+[HELPER"
assert _code.count(_old)==1
_code=_code.replace(_old,"files=c.frozen_sources()+[_source,_source.with_name('validate_native_output_capability.py'),ROOT/'freeze.json',ROOT/'FAILURE_run.json',ROOT/'RESOURCE_LOG.json',ROOT/'AMENDMENT_01.md',ROOT/'gradient-diagnosis-01/freeze.json',ROOT/'gradient-diagnosis-01/results.json',ROOT/'gradient-diagnosis-01/output_seal.json',_source.with_name('diagnose_native_gradient.py'),HELPER")
exec(compile(_code,str(_source)+'[attempt02-fixed-loss-scale]', 'exec'),globals())
