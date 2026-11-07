import hashlib,json,shutil,zipfile
from pathlib import Path,PurePosixPath
ROOT=Path(__file__).resolve().parent
freeze=json.loads((ROOT/'SOURCE_FREEZE.json').read_text(encoding='utf-8-sig'))
for name,h in freeze['files'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==h.lower()
plan=json.loads((ROOT/'REQUEST_PLAN.json').read_text(encoding='utf-8-sig'));source=Path(plan['local_wheel']);before=source.stat();assert before.st_size==plan['bytes'];assert hashlib.sha256(source.read_bytes()).hexdigest()==plan['sha256']
with zipfile.ZipFile(source) as z:
    entries=z.infolist();assert len(entries)<=3000 and sum(e.file_size for e in entries)<=512*1024**2;seen=set()
    for e in entries:
        p=PurePosixPath(e.filename);assert not p.is_absolute() and '..' not in p.parts and '\\' not in e.filename and ':' not in e.filename and e.filename not in seen;seen.add(e.filename);assert (e.external_attr>>16)&0o170000!=0o120000 and not e.flag_bits&1
    assert z.testzip() is None
assert (source.stat().st_size,source.stat().st_mtime_ns)==(before.st_size,before.st_mtime_ns)
target=ROOT/plan['filename'];assert not target.exists();shutil.copyfile(source,target);assert hashlib.sha256(target.read_bytes()).hexdigest()==plan['sha256']
(ROOT/'LOCAL_WHEEL_RESULT.json').write_text(json.dumps({'passed':True,'source':str(source),'bytes':before.st_size,'sha256':plan['sha256'],'ZIP_safety_CRC_pass':True,'source_stat_unchanged':True,'network_requests':0,'old_failed_scopes_changed':False},indent=2)+'\n',encoding='utf-8')
