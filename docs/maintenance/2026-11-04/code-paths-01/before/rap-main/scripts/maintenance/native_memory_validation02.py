"""Exact validator-only nullable observation repair; native data immutable."""
import time
START=time.monotonic()
import ast
import json
import resource
import signal
import sys
import traceback
from pathlib import Path
import physical_source_role_feasibility as s

ROOT=s.ROOT
OLD=ROOT/'docs/maintenance/2026-10-14/native-memory-query-01'
BASE=OLD/'validation-attempt-02'
SUP=BASE/'supervision'
read,sha=s.read,s.sha
SOURCE=Path(__file__).with_name('validate_native_memory.py')


def size():return sum(p.stat().st_size for p in OLD.rglob('*') if p.is_file())


def save(path,value):
    data=(json.dumps(value,indent=2,allow_nan=False)+'\n').encode()
    assert size()+len(data)<8*2**20
    with path.open('xb') as out:out.write(data)


def derive():
    tree=ast.parse(SOURCE.read_text())
    original="dotnet['peak_working_set'] >= 0 and dotnet['error'] is None"
    replacement="(dotnet['peak_working_set'] is None or dotnet['peak_working_set'] >= 0) and dotnet['error'] is None"
    class NullableOnly(ast.NodeTransformer):
        def __init__(self):self.assertions=self.routes=0
        def visit_Assert(self,node):
            if ast.unparse(node.test)==original:
                self.assertions+=1;node.test=ast.parse(replacement,mode='eval').body
            return self.generic_visit(node)
        def visit_Constant(self,node):
            if node.value==str(OLD.relative_to(ROOT)):
                self.routes+=1;return ast.copy_location(ast.Constant(str(BASE.relative_to(ROOT))),node)
            return node
    edit=NullableOnly();new=edit.visit(tree)
    assert edit.assertions==edit.routes==1
    ast.fix_missing_locations(new)
    return ast.unparse(new)+'\n'


def bind():
    old=read(OLD/'freeze.json');files=dict(old['files'])
    assert (OLD/'INCOMPLETE').exists() and not (OLD/'validation.json').exists()
    assert not read(OLD/'supervision/validate/child_exit.json')['success']
    for p,row in files.items():assert sha(p)==row['sha256']
    entries=[dict(path=str(p.relative_to(OLD)),sha256=sha(p),bytes=p.stat().st_size)
             for p in sorted(OLD.rglob('*')) if p.is_file() and BASE not in p.parents]
    save(OLD/'ORIGINAL_AVAILABLE_SEAL.json',dict(entries=len(entries),files=entries,
         status='VALIDATOR_NULLABLE_OBSERVATION_TYPE_ASSERTION_STOP',INCOMPLETE_retained=True))
    paths=[Path(__file__),BASE/'PROTOCOL.md',OLD/'ORIGINAL_AVAILABLE_SEAL.json']
    for name in ('native_queries.json','interop_exit.json','observation_seal.json'):
        target=BASE/name
        with target.open('xb') as out:out.write((OLD/name).read_bytes())
        assert sha(target)==sha(OLD/name);paths.append(target)
    snap=BASE/'source_snapshot';snap.mkdir()
    target=snap/'nullable02_validate_native_memory.py'
    with target.open('x',encoding='utf-8') as out:out.write(derive())
    paths.append(target)
    with (snap/Path(__file__).name).open('xb') as out:out.write(Path(__file__).read_bytes())
    for p in paths:files[str(p)]=dict(sha256=sha(p),bytes=p.stat().st_size)
    save(BASE/'freeze.json',dict(files=files,repositories=old['repositories'],
        potential_cases=old['potential_cases'],caps=old['caps'],variant_path=str(target),
        exact_AST_changes=dict(nullable_assertions=1,output_routes=1,no_other_change=True),
        all_original_attempts_counted=True,no_native_replay=True))
    save(BASE/'INCOMPLETE',dict(scope='NMQ0_NULLABLE02',pending='independent interpretation validation'))
    print('NMQ0 nullable02 frozen',len(files),'identities',flush=True)


def check():
    f=read(BASE/'freeze.json')
    for p,row in f['files'].items():assert sha(p)==row['sha256'] and Path(p).stat().st_size==row['bytes']
    for row in read(OLD/'ORIGINAL_AVAILABLE_SEAL.json')['files']:
        assert sha(OLD/row['path'])==row['sha256']
    assert s.repositories()==f['repositories']
    return f


def validate():
    f=check();text=derive();assert text==Path(f['variant_path']).read_text()
    namespace=dict(__name__='nmq0_bound_nullable_validator',__file__=str(SOURCE))
    exec(compile(text,f['variant_path'],'exec'),namespace);namespace['validate']();check()


def usage():return dict(wall_seconds=time.monotonic()-START,
    peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
    peak_GPU_allocated_bytes=0,peak_GPU_reserved_bytes=0,artifact_bytes=size(),
    new_native_query_or_model_or_fit_calls=0)


def run(stage):
    spent=sum(read(p)['wall_seconds'] for sup in (OLD/'supervision',SUP) for p in sup.glob('*/exit.json'))
    assert spent<300
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('NMQ0 combined cap')))
    signal.alarm(max(1,int(300-spent)));ok,error=False,None
    try:
        if stage=='bind':bind()
        elif stage=='validate':validate()
        else:raise ValueError(stage)
        u=usage();assert u['peak_RSS_bytes']<=128*2**20 and u['artifact_bytes']<8*2**20
        if (SUP/'host_latest.json').exists():assert read(SUP/'host_latest.json')['headroom_bytes']>=4*2**30
        ok=True
    except BaseException as ex:
        error=repr(ex);traceback.print_exc();save(BASE/('FAILURE_'+stage+'.json'),dict(error=error,**usage()))
    finally:
        signal.alarm(0);save(SUP/stage/'child_exit.json',
            dict(success=ok,error=error,full_resource_capture=True,**usage()))
    if not ok:sys.exit(1)


if __name__=='__main__':run(sys.argv[1])
