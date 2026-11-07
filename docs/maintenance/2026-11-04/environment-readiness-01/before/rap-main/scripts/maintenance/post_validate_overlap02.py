"""Resource-accounted immutable-bank JSON validation; original math unchanged."""
import time
START=time.monotonic()
import sys,json,resource,importlib,traceback
from pathlib import Path
import overlap_core02 as p
def inventory():return {str(x.relative_to(p.BASE)):x.stat().st_size for x in p.BASE.rglob('*') if x.is_file()}
def run(stage):
    assert stage in ('audit_bindings','assess');p.verify();assert p.read(p.BASE/'bank_seal02.json')['cells']==72
    if stage=='assess':
        assert p.read(p.BASE/'binding_audit.json')['passed'] and p.read(p.BASE/'POST_RESOURCES_audit_bindings.json')['passed']
    module=importlib.import_module('audit_overlap02' if stage=='audit_bindings' else 'assess_overlap03')
    oldcap=p.cap;oldsave=p.save;initial=inventory();base=sum(initial.values());assert base<=96*2**20,('validation baseline admission',base)
    target=p.SUP/stage;counter=0;writes={};peak_aux=0;ok=False;error=None
    bindings={str(x):p.sha(x) for x in [Path(__file__),Path(module.__file__),p.BASE/'POST_VALIDATION_RESOURCE_POLICY.md',p.BASE/'bank_seal02.json']}
    if stage=='assess':bindings[str(Path(importlib.import_module('overlap_metrics02').__file__))]=p.sha(Path(importlib.import_module('overlap_metrics02').__file__))
    oldsave(p.BASE/f'POST_RESOURCE_SOURCE_{stage}.json',dict(utc=p.now(),files=bindings,original_numerical_helpers_unchanged=True,GT_not_read_by_wrapper=True))
    # Include source-binding output in the immutable baseline.
    initial=inventory();base=sum(initial.values());assert base<=96*2**20
    def check():
        nonlocal peak_aux
        assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024<=4*2**30
        aux=sum(x.stat().st_size for x in target.rglob('*') if x.is_file());peak_aux=max(peak_aux,aux)
        assert counter<=128*2**20 and aux<=31*2**20
        assert base+counter+aux+2**20<=256*2**20
    def save(path,data):
        nonlocal counter
        path=Path(path);assert path.is_relative_to(p.BASE)
        size=len((json.dumps(data,indent=2,allow_nan=False)+'\n').encode('utf-8'));counter+=size;writes[str(path.relative_to(p.BASE))]=size;check();oldsave(path,data)
    p.cap=check;p.save=save
    metric=None;old_metric_cap=old_metric_save=None
    if stage=='assess':
        metric=importlib.import_module('overlap_metrics02');old_metric_cap=metric.cap;old_metric_save=metric.save;metric.cap=check;metric.save=save
    try:
        check();module.run();check();ok=True
    except BaseException as exc:error=repr(exc);traceback.print_exc()
    finally:
        p.cap=oldcap;p.save=oldsave
        if metric is not None:metric.cap=old_metric_cap;metric.save=old_metric_save
        end=inventory();actual=sum(end.values());memory=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024;aux=sum(x.stat().st_size for x in target.rglob('*') if x.is_file())
        resource_pass=actual<=256*2**20 and memory<=4*2**30 and actual<=base+counter+aux+2**20
        # Strict final inventory includes all observer changes; source SHA checked by original helpers.
        passed=ok and resource_pass
        oldsave(p.BASE/f'POST_RESOURCES_{stage}.json',dict(utc=p.now(),passed=passed,original_stage_passed=ok,error=error,full_inventory_before_bytes=base,full_inventory_after_bytes=actual,exact_serialized_JSON_bytes=counter,JSON_writes=writes,maximum_observed_live_stage_bytes=peak_aux,peak_RSS_bytes=memory,original_dossier_cap_bytes=256*2**20,original_Python_cap_bytes=4*2**30,numerical_checks_unchanged=True,cooperative_not_OS_isolation=True,wall_seconds=time.monotonic()-START))
        if not passed:raise SystemExit(1)
if __name__=='__main__':run(sys.argv[1])
