"""Exact runtime path/stage routing variant after prestart FileNotFoundError."""
import ast
from pathlib import Path
import official_demo_metadata as p

assert p.read(p.BASE/'supervision/windows/exit.json')['exit_code']==1
assert p.read(p.BASE/'FAILURE_windows.json')['new_scientific_payload_calls']==0
source=p.ROOT/'scripts/maintenance/official_demo_metadata_windows_bridge.py'
tree=ast.parse(source.read_text())
replacements={
 '/mnt/c/Program Files/PowerShell/7/pwsh.exe':'/mnt/c/Users/AAA/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/powershell/pwsh.exe',
 'windows':'windows02','FAILURE_windows.json':'FAILURE_windows02.json',
 'supervision/windows/child_exit.json':'supervision/windows02/child_exit.json',
 'WINDOWS_BINDING.json':'ENTRY02_BINDING.json'}
counts={k:0 for k in replacements}
for node in ast.walk(tree):
    if isinstance(node,ast.Constant) and isinstance(node.value,str) and node.value in replacements:
        old=node.value;node.value=replacements[old];counts[old]+=1
assert all(v==1 for v in counts.values())
ast.fix_missing_locations(tree)
target=source.with_name('official_demo_metadata_windows_entry02.py')
with target.open('x',encoding='utf-8') as out:out.write(ast.unparse(tree)+'\n')
amendment=p.BASE/'ENTRY02_AMENDMENT.md'
with amendment.open('x',encoding='utf-8') as out:
    out.write('# MDA0 Exact Windows Entry Path Amendment\n\nOriginal Linux bridge failed before native start/HTTP on guessed pwsh path.\nOriginal source/binding/failure/receipts retained. Actual current Windows shell\npath was observed through Get-Process. New variant changes exactly5string\nliterals: executable path, stage, failure receipt, child exit route and binding\nroute. No HTTP/scientific/hash/byte-cap predicate changes or budget reset.\nSame original900s/all attempts/4MiB shared bodies; no payload replay or install.\n')
files=dict(p.read(p.BASE/'WINDOWS_BINDING.json')['files'])
for q in (target,amendment,Path(__file__)):
    files[str(q)]=dict(bytes=q.stat().st_size,sha256=p.sha(q))
p.save('ENTRY02_BINDING.json',dict(files=files,exact_string_literal_changes=counts))
for q in (target,Path(__file__)):
    dest=p.BASE/'source_snapshot'/q.relative_to(p.ROOT)
    with dest.open('xb') as out:out.write(q.read_bytes())
print('MDA0 exact5literal entry variant bound',flush=True)
