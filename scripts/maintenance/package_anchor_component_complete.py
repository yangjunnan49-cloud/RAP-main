"""Self-contained provenance ZIP supplement; no numeric replay."""
import time
START=time.monotonic()
import sys,resource,signal,traceback,json,hashlib,zipfile
from pathlib import Path
import finalize_weekly_supplement as f
r=f.r;BASE=f.BASE;CAP=f.CAP
def run():
    used=sum(max([r.read(d/n)['wall_seconds'] for n in ('child_exit.json','exit.json') if (d/n).exists()]+[0]) for d in (BASE/'supervision').glob('*') if d.is_dir())
    used+=r.read(BASE/'WINDOWS_DELIVERY_CHECKS.json')['wall_seconds'];left=300-used;assert left>1;signal.signal(signal.SIGALRM,lambda a,b:(_ for _ in ()).throw(TimeoutError('original delivery cap')));signal.alarm(max(1,int(left)))
    ok=False;err=None
    try:
        parent=r.read(CAP/'DELIVERY_SEAL.json')
        for p,h in parent['files'].items():assert r.sha(CAP/p)==h
        entries={str(p.relative_to(CAP)):p.read_bytes() for p in sorted(CAP.rglob('*')) if p.is_file()}
        original=r.MAIN/'scripts/maintenance/coarse_anchor_fine_control.py';proof=r.read(CAP/'FREEZE.json')['AST_equivalence'];assert r.sha(original)==proof['source_sha256']
        entries['reference_source/coarse_anchor_fine_control.py']=original.read_bytes()
        entries['PACKAGE_NOTE.md']=b'''# Complete component archive supplement

All parent-dossier files, including supervision receipts named by DELIVERY_SEAL, are included. The original frozen fine-function source is included for AST comparison; it is a reference snapshot, not a standalone executable. PACKAGE_SHA256 covers every other ZIP member. Dependencies remain the documented installed environment and are not redistributed. Original G results/gates and original source seals remain unchanged. This archive replaces no historical file.
'''
        entries['PACKAGE_SHA256.json']=json.dumps(dict(files={p:hashlib.sha256(b).hexdigest() for p,b in entries.items()}),indent=2).encode()
        zp=BASE/'anchor_fine_component_complete_20261020.zip'
        with zipfile.ZipFile(zp,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            for p,b in entries.items():z.writestr(p,b)
        with zipfile.ZipFile(zp) as z:
            assert z.testzip() is None and set(z.namelist())==set(entries)
            manifest=json.loads(z.read('PACKAGE_SHA256.json'))['files']
            for p,h in manifest.items():assert hashlib.sha256(z.read(p)).hexdigest()==h
            for p,h in parent['files'].items():assert hashlib.sha256(z.read(p)).hexdigest()==h
        r.save(BASE/'PACKAGE_CHECKS02.json',dict(utc=r.now(),passed=True,zip_sha256=r.sha(zp),zip_bytes=zp.stat().st_size,all_package_manifest_members_verified=len(manifest),
            all_parent_delivery_members_present_and_verified=len(parent['files']),original_source_snapshot_present=True,previous_ZIP_preserved=True,
            previous_ZIP_scope='Runnable component/cases included; parent supervision receipts retained outside first ZIP. Complete supplement now includes those receipts.',new_numeric_calls=0))
        assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024<=2*2**30;assert sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file())<=64*2**20
        print('Complete component archive verified',len(entries),'members',zp.stat().st_size,'bytes',flush=True);ok=True
    except BaseException as e:err=repr(e);traceback.print_exc()
    finally:
        signal.alarm(0);r.save(BASE/'supervision/package_complete/child_exit.json',dict(utc=r.now(),success=ok,error=err,wall_seconds=time.monotonic()-START,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,GPU_calls=0))
    if not ok:sys.exit(1)
if __name__=='__main__':assert sys.argv[1]=='package_complete';run()
