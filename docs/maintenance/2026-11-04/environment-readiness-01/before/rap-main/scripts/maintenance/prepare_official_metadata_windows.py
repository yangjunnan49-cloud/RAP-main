"""Bind prospective native transport sources after retained WSL network failure."""
from pathlib import Path
import official_demo_metadata as p

assert p.read(p.BASE/'transfers/000.json')['acquired_body_bytes']==0
assert not p.read(p.BASE/'catalog.json')['complete']
paths=[p.BASE/'WINDOWS_TRANSPORT_AMENDMENT.md',Path(__file__),
    p.ROOT/'scripts/maintenance/official_demo_metadata_windows.ps1',
    p.ROOT/'scripts/maintenance/official_demo_metadata_windows_control.ps1',
    p.ROOT/'scripts/maintenance/official_demo_metadata_windows_bridge.py',
    p.ROOT/'scripts/maintenance/native_memory_probe.ps1']
p.save('WINDOWS_BINDING.json',dict(files={str(q):dict(bytes=q.stat().st_size,sha256=p.sha(q)) for q in paths},
    original_network_failure_preserved=True,validator_catalog_route_literal_changes=1))
for q in paths:
    if q.suffix in ('.py','.ps1'):
        target=p.BASE/'source_snapshot'/q.relative_to(p.ROOT);target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('xb') as out:out.write(q.read_bytes())
print('MDA0 Windows transport sources bound',len(paths),flush=True)
