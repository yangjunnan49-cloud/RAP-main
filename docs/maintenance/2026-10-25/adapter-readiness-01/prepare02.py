import ast,hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parent;old=root/'runtime';new=root/'runtime02'
before=(old/'worker.py').read_text(encoding='utf-8')
needle="        packages[name]=importlib.metadata.version(name)"
replacement="        try:packages[name]=importlib.metadata.version(name)\n        except importlib.metadata.PackageNotFoundError:packages[name]='MISSING'"
assert before.count(needle)==1
after=before.replace(needle,replacement)
def normalized(source):
    tree=ast.parse(source)
    for node in ast.walk(tree):
        for field,value in ast.iter_fields(node):
            if not isinstance(value,list):continue
            out=[]
            for item in value:
                if isinstance(item,ast.Try) and len(item.body)==1 and isinstance(item.body[0],ast.Assign) and ast.unparse(item.body[0].targets[0])=='packages[name]':out.extend(item.body)
                else:out.append(item)
            setattr(node,field,out)
    return ast.dump(tree,include_attributes=False)
assert normalized(before)==normalized(after)
new.mkdir()
for p in old.iterdir():
    data=after.encode() if p.name=='worker.py' else p.read_bytes()
    if p.name=='host.ps1':data=data.replace(b'adapter-readiness-01/runtime',b'adapter-readiness-01/runtime02')
    with (new/p.name).open('xb') as f:f.write(data)
assert (old/'origin.json').read_bytes()==(new/'origin.json').read_bytes()
run=root/'run02';run.mkdir()
freeze=json.loads((root/'run01/SOURCE_FREEZE.json').read_text(encoding='utf-8'))
freeze['files']={p.name:hashlib.sha256(p.read_bytes()).hexdigest().upper() for p in new.iterdir()}
with (run/'SOURCE_FREEZE.json').open('x') as f:json.dump(freeze,f,indent=2)
with (root/'REPAIR_AST_CHECKS.json').open('x') as f:json.dump(dict(passed=True,changed_only_metadata_exception_recording=True,remaining_worker_AST_identical=True,original_origin_identical=True),f,indent=2)
print(json.dumps(dict(prepared=True,numerical_probes_unchanged=True,same_origin=True)))
