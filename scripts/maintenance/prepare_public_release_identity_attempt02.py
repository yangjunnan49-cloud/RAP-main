"""Preserve PRI0 prefreeze failure; generate a snapshot-layout-only variant."""
import ast
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OLD=ROOT/'docs/maintenance/2026-10-15/public-release-identity-01'
NEW=OLD/'identity-attempt-02'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def save(p,value):
    with p.open('x',encoding='utf-8') as out:json.dump(value,out,indent=2);out.write('\n')


def main():
    assert not NEW.exists()
    assert json.loads((OLD/'supervision/freeze/exit.json').read_text())['exit_code']==1
    original={str(p.relative_to(OLD)):dict(sha256=sha(p),bytes=p.stat().st_size)
              for p in OLD.rglob('*') if p.is_file()}
    NEW.mkdir()
    save(NEW/'ORIGINAL_AVAILABLE_SEAL.json',dict(files=original,original_freeze_incomplete=True))
    for name in ('OWNER_SCOPE.md','PROTOCOL.md','PUBLIC_METADATA_OBSERVATIONS.json'):
        with (NEW/name).open('xb') as out:out.write((OLD/name).read_bytes())
    amendment='''# PRI0 Snapshot Layout Amendment

Original prefreeze failed on a repeated audit_continuation_handoff05.py basename,
before freeze.json or comparison. All original source, partial snapshot and full
failure/exit receipts remain in place and are bound by ORIGINAL_AVAILABLE_SEAL.
This separate attempt deduplicates exact input paths and preserves repository-
relative paths in source_snapshot. Hash/comparison/claim predicates do not change.
Only output routing, original-evidence binding, snapshot layout and aggregate
attempt accounting change. Original and new attempts share300s/128MiB/8MiB caps;
the8MiB cap covers both directories. No model/dataset download or deserialization.
'''
    with (NEW/'AMENDMENT.md').open('x',encoding='utf-8') as out:out.write(amendment)
    variants=[]
    for name in ('public_release_identity.py','validate_public_release_identity.py'):
        source=ROOT/'scripts/maintenance'/name
        tree=ast.parse(source.read_text())
        base_changes=0
        for node in ast.walk(tree):
            if isinstance(node,ast.Constant) and node.value=='docs/maintenance/2026-10-15/public-release-identity-01':
                node.value+='/'+'identity-attempt-02';base_changes+=1
        assert base_changes==1
        if name=='public_release_identity.py':
            for node in tree.body:
                if isinstance(node,ast.FunctionDef) and node.name=='size':
                    node.body=ast.parse("return sum(p.stat().st_size for p in BASE.parent.rglob('*') if p.is_file())").body
                if isinstance(node,ast.FunctionDef) and node.name=='freeze':
                    old=ast.parse('for p in paths:\n if p.suffix in (".py",".ps1",".sh",".yaml"):\n  with (snap/p.name).open("xb") as out:out.write(p.read_bytes())').body[0]
                    found=[i for i,x in enumerate(node.body) if ast.dump(x)==ast.dump(old)]
                    assert len(found)==1
                    node.body[found[0]]=ast.parse('for p in dict.fromkeys(paths):\n if p.suffix in (".py",".ps1",".sh",".yaml"):\n  target=snap/p.relative_to(ROOT)\n  target.parent.mkdir(parents=True,exist_ok=True)\n  with target.open("xb") as out:out.write(p.read_bytes())').body[0]
                    idx=next(i for i,x in enumerate(node.body) if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='files' for t in x.targets))
                    extra=ast.parse("paths += [BASE/n for n in ('AMENDMENT.md','ORIGINAL_AVAILABLE_SEAL.json','VARIANT_BINDING.json')]\nfor rel,row in read(BASE/'ORIGINAL_AVAILABLE_SEAL.json')['files'].items():\n p=BASE.parent/rel\n assert sha(p)==row['sha256'] and p.stat().st_size==row['bytes']\n paths.append(p)").body
                    node.body[idx:idx]=extra
                if isinstance(node,ast.FunctionDef) and node.name=='run':
                    node.body[0]=ast.parse("spent=sum(read(p)['wall_seconds'] for folder in (BASE.parent/'supervision',SUP) for p in folder.glob('*/exit.json'));assert spent<300").body[0]
        ast.fix_missing_locations(tree)
        target=source.with_name(source.stem+'_attempt02.py')
        rendered=ast.unparse(tree)+'\n'
        if name.startswith('public_'):
            rendered=rendered.replace("with_name('validate_public_release_identity.py')","with_name('validate_public_release_identity_attempt02.py')")
            rendered=rendered.replace('import validate_public_release_identity as v','import validate_public_release_identity_attempt02 as v')
        with target.open('x',encoding='utf-8') as out:out.write(rendered)
        variants.append(dict(original=str(source),original_SHA256=sha(source),variant=str(target),variant_SHA256=sha(target)))
    save(NEW/'VARIANT_BINDING.json',dict(changes='output route; original binding; snapshot layout; aggregate accounting only',files=variants,assembler=str(Path(__file__)),assembler_SHA256=sha(Path(__file__))))
    print(json.dumps(dict(original_files=len(original),variants=variants)),flush=True)


if __name__=='__main__':main()
