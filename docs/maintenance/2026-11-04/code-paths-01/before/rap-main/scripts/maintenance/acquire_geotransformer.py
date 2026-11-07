"""Acquire only official GeoTransformer metadata/source/KITTI weights, capped."""
import hashlib
import json
import tarfile
import urllib.request
from datetime import datetime,timezone
from pathlib import Path

BASE=Path('/mnt/e/githouse/RAP-main/docs/maintenance/2026-10-05/geotransformer-feasibility-01')
HEADERS={'User-Agent':'RAP-thesis-registration-feasibility','Accept':'application/vnd.github+json'}

def fetch(url,limit):
    req=urllib.request.Request(url,headers=HEADERS)
    with urllib.request.urlopen(req,timeout=60) as response:
        data=response.read(limit+1)
    assert len(data)<=limit,(url,len(data))
    return data

def save(p,data):
    with p.open('xb') as f: f.write(data)

def main():
    releases=fetch('https://api.github.com/repos/qinzheng93/GeoTransformer/releases',2000000)
    save(BASE/'releases.json',releases)
    release=next(r for r in json.loads(releases) if any('kitti' in a['name'].lower() for a in r['assets']))
    tag=release['tag_name']
    commit_data=fetch('https://api.github.com/repos/qinzheng93/GeoTransformer/commits/'+tag,2000000)
    save(BASE/'release_commit.json',commit_data)
    commit=json.loads(commit_data)['sha']
    asset=next(a for a in release['assets'] if 'kitti' in a['name'].lower())
    assert asset['size']<200000000
    for name,url,limit in [('source.tar.gz',f'https://codeload.github.com/qinzheng93/GeoTransformer/tar.gz/{commit}',50000000),
                           (asset['name'],asset['browser_download_url'],200000000)]:
        body=fetch(url,limit); save(BASE/name,body)
    target=BASE/'official-source'; target.mkdir()
    with tarfile.open(BASE/'source.tar.gz') as archive:
        prefix=archive.getmembers()[0].name.split('/')[0]
        for member in archive.getmembers():
            parts=Path(member.name).parts
            assert parts[0]==prefix and '..' not in parts
            if len(parts)==1: continue
            assert member.isdir() or member.isfile(),member.name
            dest=target.joinpath(*parts[1:])
            assert dest.resolve().is_relative_to(target.resolve())
            if member.isdir(): dest.mkdir(parents=True,exist_ok=True)
            else:
                dest.parent.mkdir(parents=True,exist_ok=True)
                save(dest,archive.extractfile(member).read())
    receipt=dict(utc=datetime.now(timezone.utc).isoformat(),repository='https://github.com/qinzheng93/GeoTransformer',
      release_tag=tag,source_commit=commit,asset_name=asset['name'],asset_url=asset['browser_download_url'],
      files={p.name:dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in BASE.iterdir() if p.is_file()})
    save(BASE/'acquisition.json',(json.dumps(receipt,indent=2)+'\n').encode())
    print(json.dumps({k:receipt[k] for k in ('release_tag','source_commit','asset_name')}),flush=True)

if __name__=='__main__': main()
