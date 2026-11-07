"""Resume official acquisition after a release-host timeout; preserve originals."""
import hashlib,json,tarfile,urllib.request,time
from pathlib import Path

B=Path('/mnt/e/githouse/RAP-main/docs/maintenance/2026-10-05/geotransformer-feasibility-01')
rels=json.loads((B/'releases.json').read_text()); release=next(r for r in rels if any('kitti' in a['name'] for a in r['assets']))
asset=next(a for a in release['assets'] if 'kitti' in a['name']); commit=json.loads((B/'release_commit.json').read_text())['sha']
target=B/'official-source'
if not target.exists():
    target.mkdir()
    with tarfile.open(B/'source.tar.gz') as archive:
        for member in archive.getmembers():
            parts=Path(member.name).parts
            assert parts[0]=='GeoTransformer-'+commit and '..' not in parts
            if len(parts)==1: continue
            dest=target.joinpath(*parts[1:]); assert dest.resolve().is_relative_to(target.resolve())
            assert member.isfile() or member.isdir()
            if member.isdir(): dest.mkdir(parents=True,exist_ok=True)
            else:
                dest.parent.mkdir(parents=True,exist_ok=True)
                with dest.open('xb') as f: f.write(archive.extractfile(member).read())
print('official pinned source extracted',commit,flush=True)
record={'source_commit':commit,'release_tag':release['tag_name'],'checkpoint_name':asset['name'],'attempts':[]}
try:
    headers={'User-Agent':'RAP-thesis-feasibility','Accept':'application/octet-stream'}
    req=urllib.request.Request(asset['url']+'?download=1',headers=headers)
    with urllib.request.urlopen(req,timeout=30) as response:
        body=response.read(200000001)
    assert len(body)==asset['size'],('asset size differs',len(body),asset['size'])
    with (B/asset['name']).open('xb') as f: f.write(body)
    record['checkpoint_sha256']=hashlib.sha256(body).hexdigest()
    record['checkpoint_bytes']=len(body)
    record['status']='ACQUIRED'
    print('official KITTI checkpoint acquired',len(body),record['checkpoint_sha256'],flush=True)
except Exception as e:
    record['status']='CHECKPOINT_PENDING'; record['error']=repr(e)
    print('checkpoint pending',repr(e),flush=True)
finally:
    record['source_archive_sha256']=hashlib.sha256((B/'source.tar.gz').read_bytes()).hexdigest()
    with (B/'recovery_acquisition.json').open('x') as f: json.dump(record,f,indent=2)
