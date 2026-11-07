"""DSR0 exact AST-unparse tuple assertion variant; preserve original failure."""
import ast
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OLD=ROOT/'docs/maintenance/2026-10-15/demo-source-role-01'
NEW=OLD/'source-attempt-02'


def sha(q):return hashlib.sha256(q.read_bytes()).hexdigest()


def save(q,value):
    with q.open('x',encoding='utf-8') as out:json.dump(value,out,indent=2);out.write('\n')


def main():
    assert not NEW.exists()
    assert json.loads((OLD/'supervision/audit/exit.json').read_text())['exit_code']==1
    original={str(q.relative_to(OLD)):dict(sha256=sha(q),bytes=q.stat().st_size)
        for q in OLD.rglob('*') if q.is_file()}
    NEW.mkdir();save(NEW/'ORIGINAL_AVAILABLE_SEAL.json',dict(files=original))
    for name in ('OWNER_SCOPE.md','PROTOCOL.md'):
        with (NEW/name).open('xb') as out:out.write((OLD/name).read_bytes())
    with (NEW/'AMENDMENT.md').open('x',encoding='utf-8') as out:
        out.write('# DSR0 Tuple-Unparse Assertion Amendment\n\nOriginal source assertion omitted the tuple parentheses emitted by ast.unparse.\nOriginal181-identity freeze/source/audit failure/full receipts stay unchanged.\nSeparate variant changes exactly1 tuple-text assertion plus output/import routes,\nevidence binding and aggregate accounting. No scientific predicate or numeric\ninput changes. All original/new attempts share300s/128MiB/8MiB caps;8MiB covers\nboth directories. No point numeric/model/pose/GT evaluation or acquisition.\n')
    variants=[]
    for name in ('demo_source_roles.py','validate_demo_source_roles.py'):
        src=ROOT/'scripts/maintenance'/name;tree=ast.parse(src.read_text());route=fix=0
        for node in ast.walk(tree):
            if isinstance(node,ast.Constant) and node.value=='docs/maintenance/2026-10-15/demo-source-role-01':
                node.value+='/source-attempt-02';route+=1
            if isinstance(node,ast.Constant) and node.value=='pts_gt, gt_trans = center_pcd(pts_gt)':
                node.value='(pts_gt, gt_trans) = center_pcd(pts_gt)';fix+=1
        assert route==1 and fix==(1 if name=='demo_source_roles.py' else 0)
        if name=='demo_source_roles.py':
            for fn in tree.body:
                if isinstance(fn,ast.FunctionDef) and fn.name=='size':
                    fn.body=ast.parse("return sum(q.stat().st_size for q in BASE.parent.rglob('*') if q.is_file())").body
                if isinstance(fn,ast.FunctionDef) and fn.name=='run':
                    fn.body[0]=ast.parse("spent=sum(read(q)['wall_seconds'] for folder in (BASE.parent/'supervision',SUP) for q in folder.glob('*/exit.json'));assert spent<300").body[0]
                if isinstance(fn,ast.FunctionDef) and fn.name=='freeze':
                    idx=next(i for i,n in enumerate(fn.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='inv' for t in n.targets))
                    fn.body[idx:idx]=ast.parse("paths += [BASE/n for n in ('AMENDMENT.md','ORIGINAL_AVAILABLE_SEAL.json','VARIANT_BINDING.json')]\nfor rel,row in read(BASE/'ORIGINAL_AVAILABLE_SEAL.json')['files'].items():\n q=BASE.parent/rel\n assert sha(q)==row['sha256'] and q.stat().st_size==row['bytes']\n paths.append(q)").body
        ast.fix_missing_locations(tree);rendered=ast.unparse(tree)+'\n'
        if name=='demo_source_roles.py':
            rendered=rendered.replace("with_name('validate_demo_source_roles.py')","with_name('validate_demo_source_roles_attempt02.py')")
            rendered=rendered.replace('import validate_demo_source_roles as v','import validate_demo_source_roles_attempt02 as v')
        target=src.with_name(src.stem+'_attempt02.py')
        with target.open('x',encoding='utf-8') as out:out.write(rendered)
        variants.append(dict(original=str(src),original_SHA256=sha(src),variant=str(target),variant_SHA256=sha(target)))
    save(NEW/'VARIANT_BINDING.json',dict(files=variants,assembler=str(Path(__file__)),assembler_SHA256=sha(Path(__file__)),exact_tuple_assertion_changes=1))
    print(json.dumps(dict(original_available_files=len(original),variants=variants)),flush=True)


if __name__=='__main__':main()
