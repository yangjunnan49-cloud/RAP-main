"""Cross-platform basename repair, leaving the failed frozen runtime intact."""
import ast,hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parent
old=root/'runtime';new=root/'runtime02'
assert not new.exists();new.mkdir()
before=(old/'worker.py').read_text()
assert before.count('from pathlib import Path')==1
assert before.count("Path(row['path']).name")==1
after=before.replace('from pathlib import Path','from pathlib import Path, PureWindowsPath').replace("Path(row['path']).name","PureWindowsPath(row['path']).name")
def normalized(source):
    tree=ast.parse(source)
    for n in ast.walk(tree):
        if isinstance(n,ast.ImportFrom) and n.module=='pathlib':n.names=[x for x in n.names if x.name!='PureWindowsPath']
        if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='PureWindowsPath':n.func.id='Path'
    return ast.dump(tree,include_attributes=False)
assert normalized(before)==normalized(after)
with (new/'worker.py').open('x') as f:f.write(after)
for p in old.iterdir():
    if p.name=='worker.py':continue
    b=p.read_bytes()
    if p.name=='host.ps1':
        assert b.count(b'output-visualization-01/runtime')==1
        b=b.replace(b'output-visualization-01/runtime',b'output-visualization-01/runtime02')
    with (new/p.name).open('xb') as f:f.write(b)
assert (new/'origin.json').read_bytes()==(old/'origin.json').read_bytes()
run=root/'run02';run.mkdir()
freeze=json.loads((root/'run01/SOURCE_FREEZE.json').read_text())
freeze['files']={p.name:hashlib.sha256(p.read_bytes()).hexdigest().upper() for p in new.iterdir()}
with (run/'SOURCE_FREEZE.json').open('x') as f:json.dump(freeze,f,indent=2)
with (root/'REPAIR_AST_CHECK.json').open('x') as f:json.dump(dict(passed=True,
    changed_only_pathlib_import_and_bound_basename=True,other_worker_AST_identical=True,
    same_original_origin=True,original_runtime_and_failure_preserved=True),f,indent=2)
print(json.dumps(dict(prepared=True,numeric_AST_unchanged=True,same_origin=True)))
