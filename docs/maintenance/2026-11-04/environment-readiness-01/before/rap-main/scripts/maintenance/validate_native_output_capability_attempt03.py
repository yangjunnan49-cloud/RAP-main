"""Hash-bound independent centroid-precision correction; unchanged NOC0 bank."""
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
_old="centers=np.array([p.mean(0) for p in np.split(z['points'],3)])"
assert _code.count(_old)==1
_code=_code.replace(_old,"centers=np.array([p.astype(np.float64).mean(0) for p in np.split(z['points'],3)])")
_old="r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)"
assert _code.count(_old)==1
_code=_code.replace(_old,_old+"\nVALIDATION=r.BASE/'validation-attempt-02'")
for _name in ('validation.json','validation_seal.json','FAILURE_validation.json'):
    _code=_code.replace("r.BASE/'"+_name+"'","VALIDATION/'"+_name+"'")
_addition='''
def validation_freeze():
    r.check(); VALIDATION.mkdir()
    prior=r.BASE/'RESOURCE_LOG_before_validation.json'
    prior.write_bytes((r.BASE/'RESOURCE_LOG.json').read_bytes())
    files=[Path(__file__),_source,_source.with_name('validate_native_output_capability_attempt02.py'),
        _root/'AMENDMENT_02.md',r.BASE/'freeze.json',r.BASE/'bank_seal.json',r.BASE/'bank.json',prior]
    c.save(VALIDATION/'freeze.json',dict(files={str(p):c.sha(p) for p in files},
        centroid_cast_to_float64=True,scientific_bank_unchanged=True,optimizer_updates=0))
'''
_code=_code.replace("if __name__=='__main__':",_addition+"\nif __name__=='__main__':")
_code=_code.replace('try: run()','try: validation_freeze(); run()')
exec(compile(_code,str(_source)+'[centroid-precision-only]', 'exec'),globals())
