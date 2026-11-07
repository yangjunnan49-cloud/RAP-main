"""LCP0 prospective exact-alias implementation amendment, old source preserved."""
import ast,inspect,signal,sys,time,traceback
from pathlib import Path
import shadow_evidence_archive as r
ORIGINAL_VERIFY=r.verify
def verify():
    ORIGINAL_VERIFY();b=r.read(r.BASE/'EXECUTION_BINDING.json');assert b['original_freeze_sha256']==r.sha(r.BASE/'freeze.json')
    for q,h in b['files'].items():assert r.sha(q)==h,q
def install_exact_alias():
    tree=ast.parse(inspect.getsource(r.pack));matches=0
    for node in ast.walk(tree):
        if isinstance(node,ast.FunctionDef) and node.name=='put':
            assert ast.dump(node.body[1],include_attributes=False)==ast.dump(ast.parse('if key in objects:return key').body[0],include_attributes=False)
            node.body.insert(2,ast.parse('if base is not None and base == raw:return put(raw)').body[0]);matches+=1
    assert matches==1;ast.fix_missing_locations(tree);exec(compile(tree,'<LCP0 sealed exact-alias branch>','exec'),r.__dict__)
def bind():
    ORIGINAL_VERIFY();assert not (r.BASE/'compatibility.json').exists() and not (r.BASE/'packed').exists()
    paths=[Path(__file__),r.BASE/'AMENDMENT_01.md'];files={str(q):r.sha(q) for q in paths}
    (r.BASE/'source_snapshot/shadow_evidence_archive_execution.py').write_bytes(Path(__file__).read_bytes())
    r.save(r.BASE/'EXECUTION_BINDING.json',dict(original_freeze_sha256=r.sha(r.BASE/'freeze.json'),files=files,old_source_preserved=True,static_review_before_any_serialization_or_encoding=True,change='exact target/base equality aliases even when content first encountered',no_failed_payload=True,no_gate_cap_or_scientific_change=True))
    print('LCP0 prospective exact-alias branch bound before any serialization/packing',flush=True)
def run(stage):
    r.START=time.monotonic();used=sum(r.read(q)['wall_seconds'] for q in r.SUP.glob('*/child_exit.json'));assert used<1800
    signal.signal(signal.SIGALRM,lambda a,b:(_ for _ in ()).throw(TimeoutError('LCP0 aggregate attempted-child time cap')));signal.alarm(max(1,int(1800-used)));ok=False;error=None
    try:
        if stage=='bind':bind()
        else:
            verify();install_exact_alias();r.verify=verify
            if stage=='compatibility':r.compatibility()
            elif stage=='pack':r.pack()
            elif stage=='validate':
                import validate_shadow_evidence_archive as v;v.validate()
            else:raise ValueError(stage)
        r.cap();ok=True
    except BaseException as ex:error=repr(ex);traceback.print_exc();r.save(r.BASE/f'FAILURE_{stage}.json',dict(error=error,**r.usage()))
    finally:signal.alarm(0);r.save(r.SUP/stage/'child_exit.json',dict(success=ok,error=error,full_resource_capture=True,**r.usage()))
    if not ok:sys.exit(1)
if __name__=='__main__':run(sys.argv[1])
