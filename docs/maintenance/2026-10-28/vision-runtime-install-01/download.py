import hashlib,http.client,json,ssl,time,zipfile
from pathlib import Path,PurePosixPath
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parent;START=time.monotonic()
plan=json.loads((ROOT/'REQUEST_PLAN.json').read_text(encoding='utf-8-sig'));freeze=json.loads((ROOT/'SOURCE_FREEZE.json').read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for n,h in freeze['files'].items():assert sha(ROOT/n)==h.lower(),n
assert sha(Path(plan['metadata_findings_path']))==plan['metadata_findings_sha256']
u=urlsplit(plan['url']);assert u.scheme=='https' and u.hostname=='files.pythonhosted.org' and not(u.query or u.fragment or u.username or u.password);assert u.path.endswith('/'+plan['filename'])
dest=ROOT/plan['filename'];assert not dest.exists();total=0;digest=hashlib.sha256();ok=False;error=None
try:
    conn=http.client.HTTPSConnection(u.hostname,timeout=15,context=ssl.create_default_context());conn.request('GET',u.path,headers={'User-Agent':'RAP-runtime-admission/1.0','Accept':'application/octet-stream','Accept-Encoding':'identity','Connection':'close'});r=conn.getresponse()
    assert r.status==200 and r.getheader('Content-Encoding','identity')=='identity';assert r.getheader('Content-Length')==str(plan['bytes']);assert r.getheader('Content-Type','').split(';')[0] in ('application/octet-stream','application/zip')
    with dest.open('xb') as f:
        while total<plan['bytes']:
            left=120-(time.monotonic()-START);assert left>0
            if conn.sock is not None:conn.sock.settimeout(min(15,left))
            block=r.read(min(1024**2,plan['bytes']-total));assert block
            f.write(block);digest.update(block);total+=len(block)
    assert r.length==0 and total==plan['bytes'] and digest.hexdigest()==plan['sha256'];r.close();conn.close()
    with zipfile.ZipFile(dest) as z:
        items=z.infolist();assert len(items)<=3000;assert sum(x.file_size for x in items)<=plan['wheel_uncompressed_bytes_cap'];names=set()
        for item in items:
            p=PurePosixPath(item.filename);assert not p.is_absolute() and '..' not in p.parts and '\\' not in item.filename and ':' not in item.filename;assert item.filename not in names;names.add(item.filename);assert (item.external_attr>>16)&0o170000!=0o120000 and not item.flag_bits&1
    ok=True
except BaseException as e:error=repr(e);raise
finally:
    (ROOT/'DOWNLOAD_RESULT.json').write_text(json.dumps({'passed':ok,'error':error,'requests':1,'redirects':0,'bytes':total,'sha256':digest.hexdigest(),'expected_sha256':plan['sha256'],'elapsed_seconds':time.monotonic()-START,'wheel_safety_checked':ok},indent=2)+'\n',encoding='utf-8')
