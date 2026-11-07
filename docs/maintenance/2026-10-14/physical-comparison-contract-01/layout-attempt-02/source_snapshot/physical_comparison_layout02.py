"""PCC0 separately frozen AST-exact archive-layout repair; original preserved."""
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
OLD=ROOT/'docs/maintenance/2026-10-14/physical-comparison-contract-01'
BASE=OLD/'layout-attempt-02'
SUP=BASE/'supervision'
read,sha=s.read,s.sha

def size():return sum(p.stat().st_size for p in OLD.rglob('*') if p.is_file())

def save(p,v):
    body=(json.dumps(v,indent=2,allow_nan=False)+'\n').encode()
    assert size()+len(body)<32*2**20
    with Path(p).open('xb') as stream:stream.write(body)

def derive(path):
    tree=ast.parse(path.read_text())
    class LayoutOnly(ast.NodeTransformer):
        def __init__(self):self.layouts=0;self.routes=0
        def visit_List(self,node):
            if all(isinstance(x,ast.Constant) for x in node.elts) and [x.value for x in node.elts]==[3000,512]:
                self.layouts+=1
                return ast.copy_location(ast.List(elts=[ast.Constant(x) for x in (3,1000,512)],ctx=ast.Load()),node)
            return self.generic_visit(node)
        def visit_Constant(self,node):
            if node.value=='docs/maintenance/2026-10-14/physical-comparison-contract-01':
                self.routes+=1
                return ast.copy_location(ast.Constant(str(BASE.relative_to(ROOT))),node)
            return node
    transform=LayoutOnly();changed=transform.visit(tree)
    assert transform.layouts==2 and transform.routes==1,(str(path),transform.layouts,transform.routes)
    ast.fix_missing_locations(changed)
    return ast.unparse(changed)+'\n',dict(token_shape_lists=2,output_route=1,no_other_AST_change=True)

def bind():
    assert (OLD/'INCOMPLETE').exists() and not read(OLD/'supervision/audit/child_exit.json')['success']
    assert not (OLD/'contract_audit.json').exists()
    files=dict(read(OLD/'freeze.json')['files'])
    for p,h in files.items():assert sha(p)==h,p
    available=[]
    for p in sorted(OLD.rglob('*')):
        if p.is_file() and BASE not in p.parents:
            available.append(dict(path=str(p.relative_to(OLD)),sha256=sha(p),bytes=p.stat().st_size))
    save(OLD/'ORIGINAL_AVAILABLE_SEAL.json',dict(status='SOURCE_LAYOUT_ASSERTION_STOP_NO_NUMERIC_REPLAY',
        entries=len(available),files=available,original_INCOMPLETE_retained=True))
    files[str(OLD/'ORIGINAL_AVAILABLE_SEAL.json')]=sha(OLD/'ORIGINAL_AVAILABLE_SEAL.json')
    paths=[Path(__file__),BASE/'PROTOCOL.md',
           ROOT.parent/'RAP-SLAM/scripts/joint_token_extraction.py']
    snapshots=BASE/'source_snapshot';snapshots.mkdir()
    variants={}
    for name in ('physical_comparison_contract.py','validate_physical_comparison_contract.py'):
        source=Path(__file__).with_name(name)
        text,changes=derive(source)
        target=snapshots/('layout02_'+name)
        with target.open('x',encoding='utf-8') as out:out.write(text)
        files[str(target)]=sha(target)
        variants[name]=dict(path=str(target),original_path=str(source),original_sha256=sha(source),
                            derived_sha256=sha(target),changes=changes)
    for p in paths:files[str(p)]=sha(p)
    with (snapshots/Path(__file__).name).open('xb') as out:out.write(Path(__file__).read_bytes())
    f=read(OLD/'freeze.json')
    save(BASE/'freeze.json',dict(files=files,repositories=f['repositories'],rows=f['rows'],
        caps=f['caps'],following_candidate=f['following_candidate'],variants=variants,
        original_failure_retained=True,aggregate_budget_includes_original_attempt=True))
    save(BASE/'INCOMPLETE',dict(scope='PCC0_LAYOUT02',pending='audit/independent validation'))
    print('PCC0 layout02 bound',len(files),'identities; exact2+1 AST changes/source',flush=True)

def check():
    f=read(BASE/'freeze.json')
    for p,h in f['files'].items():assert sha(p)==h,p
    for row in read(OLD/'ORIGINAL_AVAILABLE_SEAL.json')['files']:
        assert sha(OLD/row['path'])==row['sha256']
    assert s.repositories()==f['repositories']
    return f

def execute(name,function):
    f=check();v=f['variants'][name]
    text,changes=derive(Path(v['original_path']))
    assert text==Path(v['path']).read_text() and changes==v['changes']
    namespace=dict(__name__='pcc0_layout02_bound_source',__file__=v['original_path'])
    exec(compile(text,v['path'],'exec'),namespace)
    namespace[function]()
    check()

def usage():return dict(wall_seconds=time.monotonic()-START,
    peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
    peak_GPU_allocated_bytes=0,peak_GPU_reserved_bytes=0,artifact_bytes=size(),
    model_calls=0,optimizer_calls=0,numeric_array_values_read=False)

def run(stage):
    receipts=list((OLD/'supervision').glob('*/exit.json'))+list(SUP.glob('*/exit.json'))
    spent=sum(read(p)['wall_seconds'] for p in receipts);assert spent<900
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('PCC0 combined original/layout02 cap')))
    signal.alarm(max(1,int(900-spent)));ok,error=False,None
    try:
        if stage=='bind':bind()
        elif stage=='audit':execute('physical_comparison_contract.py','audit')
        elif stage=='validate':execute('validate_physical_comparison_contract.py','validate')
        else:raise ValueError(stage)
        u=usage();assert u['peak_RSS_bytes']<=512*2**20 and u['artifact_bytes']<32*2**20
        if (SUP/'host_latest.json').exists():assert read(SUP/'host_latest.json')['headroom_bytes']>=4*2**30
        ok=True
    except BaseException as ex:
        error=repr(ex);traceback.print_exc();save(BASE/f'FAILURE_{stage}.json',dict(error=error,**usage()))
    finally:
        signal.alarm(0);save(SUP/stage/'child_exit.json',dict(success=ok,error=error,full_resource_capture=True,**usage()))
    if not ok:sys.exit(1)

if __name__=='__main__':run(sys.argv[1])
