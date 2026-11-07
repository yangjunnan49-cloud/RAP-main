"""Read-only scoped command-argument census; no process changes."""
import json,os
from pathlib import Path
root=Path(__file__).resolve().parents[2]
base=root/'docs/maintenance/2026-10-15/continuation-handoff-07'
names={'validate_original_archive_inventory.py','validate_original_archive_inventory_attempt02.py',
 'validate_demo_reference_documents.py','validate_demo_reference_documents_attempt02.py','validate_demo_reference_driver.py'}
rows=0;args=0;unknown=[];matches=[]
for directory in Path('/proc').iterdir():
    if not directory.name.isdigit():continue
    rows+=1
    try:
        argv=(directory/'cmdline').read_bytes().split(b'\0');argv=[x.decode(errors='replace') for x in argv if x];args+=len(argv)
    except (OSError,PermissionError) as ex:unknown.append(dict(pid=int(directory.name),error=repr(ex)));continue
    if int(directory.name)==os.getpid():continue
    for name in names:
        if any(name in arg for arg in argv):matches.append(dict(pid=int(directory.name),identifier=name,argv=argv));break
result=dict(processes=rows,arguments=args,unreadable=unknown,scoped_matches=matches,
    unrelated_process_absence_claim=False,scope_only=True,ordinary_setup_RSS='UNKNOWN')
with (base/'LINUX_PROCESS_CENSUS.json').open('x') as f:json.dump(result,f,indent=2)
print(json.dumps(dict(processes=rows,arguments=args,unreadable=len(unknown),scoped_matches=len(matches))))
