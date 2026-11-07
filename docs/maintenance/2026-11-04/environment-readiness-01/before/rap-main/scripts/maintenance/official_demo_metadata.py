"""MDA0 bounded official metadata only; never fetches cloud/model payloads."""
import time
START=time.monotonic()
import hashlib
import json
from pathlib import Path
import resource
import signal
import sys
import traceback
import urllib.error
import urllib.parse
import urllib.request
import demo_source_roles as ds

s=ds.s;ROOT=s.ROOT
BASE=ROOT/'docs/maintenance/2026-10-15/official-demo-metadata-01'
SUP=BASE/'supervision'
DSR=ROOT/'docs/maintenance/2026-10-15/demo-source-role-01/source-attempt-02'
REV='c8deb301b32bb887acd48371ae93221251a056b5'
API='https://huggingface.co/api/datasets/YuePanEdward/regx-benchmark/tree/'+REV
RESOLVE='https://huggingface.co/datasets/YuePanEdward/regx-benchmark/resolve/'+REV+'/'
CAP=4194304
read,sha=s.read,s.sha


def size():return sum(q.stat().st_size for q in BASE.rglob('*') if q.is_file())


def save(name,value):
    body=(json.dumps(value,indent=2,allow_nan=False)+'\n').encode();assert size()+len(body)<16*2**20
    with (BASE/name).open('xb') as out:out.write(body)


def transfers():return [read(q) for q in sorted((BASE/'transfers').glob('*.json'))]


def valid(url):
    u=urllib.parse.urlsplit(url)
    assert u.scheme=='https' and u.netloc=='huggingface.co' and not u.fragment
    if url.startswith(API):return
    if url.startswith(RESOLVE):
        name=urllib.parse.unquote(u.path).split('/resolve/'+REV+'/',1)[1]
        assert name in ('README.md','datasets.csv','ATTRIBUTION.md','LICENSE') or name.endswith('/metadata.yaml')
        return
    assert u.path.startswith('/api/resolve-cache/datasets/YuePanEdward/regx-benchmark/'+REV+'/')
    name=urllib.parse.unquote(u.path).split('/'+REV+'/',1)[1]
    assert name in ('README.md','datasets.csv','ATTRIBUTION.md','LICENSE') or name.endswith('/metadata.yaml')


class Redirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        valid(newurl)
        return super().redirect_request(req,fp,code,msg,headers,newurl)


def fetch(url,kind):
    valid(url);old=transfers();assert len(old)<40
    remaining=CAP-sum(r['acquired_body_bytes'] for r in old);assert remaining>0
    limit=min(524288,remaining);index=len(old);body=b'';error=None;complete=False;headers={};status=None;final=None
    request=urllib.request.Request(url,headers={'Accept-Encoding':'identity','User-Agent':'RAP-local-metadata-identity-audit/1.0'})
    try:
        opener=urllib.request.build_opener(Redirect())
        try:response=opener.open(request,timeout=20)
        except urllib.error.HTTPError as ex:response=ex
        with response:
            final=response.geturl();valid(final);status=response.status
            headers={k.lower():v for k,v in response.headers.items()}
            encoding=headers.get('content-encoding','identity');assert encoding in ('identity','')
            length=int(headers['content-length']) if 'content-length' in headers else None
            if length is not None and length>limit:raise ValueError('declared body exceeds reserved per-request/remaining cap')
            while len(body)<limit:
                n=min(65536,limit-len(body));part=response.read(n);body+=part
                if len(part)<n:complete=True;break
            if len(body)==limit:complete=(length==limit)
            if length is not None:assert len(body)==length
            assert complete,'body prefix retained, completeness not established'
            assert status==200,'non200 body retained'
    except Exception as ex:error=repr(ex)
    target=BASE/'payload'/f'{index:03d}.body'
    with target.open('xb') as out:out.write(body)
    receipt=dict(index=index,requested_url=url,final_url=final,kind=kind,status=status,
        headers=headers,acquired_body_bytes=len(body),body_path=str(target.relative_to(BASE)),
        SHA256=hashlib.sha256(body).hexdigest(),complete=complete,admitted=(error is None),error=error)
    save('transfers/'+f'{index:03d}.json',receipt)
    assert sum(r['acquired_body_bytes'] for r in transfers())<=CAP
    return receipt,body


def freeze():
    paths=[BASE/n for n in ('OWNER_AUTHORIZATION.md','PROTOCOL.md')]
    paths += [DSR/n for n in ('freeze.json','headers_and_roles.json','validation.json','DELIVERY_SEAL.json')]
    paths += [ROOT/'docs/maintenance/2026-10-15/public-release-identity-01/identity-attempt-02/PUBLIC_METADATA_OBSERVATIONS.json']
    paths += [Path(__file__),Path(__file__).with_name('validate_official_demo_metadata.py'),
        Path(__file__).with_name('demo_source_roles.py'),Path(__file__).with_name('physical_source_role_feasibility.py'),
        Path(__file__).with_name('invoke_mgr_supervised_wsl.ps1')]
    paths += [ROOT/'docs/maintenance'/n for n in ds.MARKERS]
    paths += [ROOT/'docs/maintenance/2026-10-15/demo-source-role-01/INCOMPLETE']
    for n in ('payload','transfers','source_snapshot'): (BASE/n).mkdir()
    for q in paths:
        if q.suffix in ('.py','.ps1'):
            target=BASE/'source_snapshot'/q.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True)
            with target.open('xb') as out:out.write(q.read_bytes())
    save('freeze.json',dict(files={str(q):dict(bytes=q.stat().st_size,sha256=sha(q)) for q in paths},
        repositories=s.repositories(),revision=REV,network_body_cap_bytes=CAP))
    save('INCOMPLETE',dict(scope='MDA0',pending='bounded acquisition and identity comparison'))
    print('MDA0 frozen',len(paths),'identities',flush=True)


def verify():
    f=read(BASE/'freeze.json')
    for n,r in f['files'].items():assert sha(Path(n))==r['sha256'] and Path(n).stat().st_size==r['bytes']
    assert s.repositories()==f['repositories'];return f


def catalog():
    verify();url=API+'?recursive=true&expand=false&limit=1000';entries=[];pages=[];complete=False
    for _ in range(12):
        r,body=fetch(url,'catalog');pages.append(r['index'])
        if not r['admitted']:break
        page=json.loads(body);assert isinstance(page,list);entries.extend(page)
        link=r['headers'].get('link','');next_urls=[]
        for part in link.split(','):
            if 'rel="next"' in part or 'rel=next' in part:next_urls.append(part.split('<',1)[1].split('>',1)[0])
        assert len(next_urls)<=1
        if not next_urls:complete=True;break
        url=next_urls[0];assert url.startswith(API)
    save('catalog.json',dict(revision=REV,complete=complete,pages=pages,entries=entries))
    verify();print(json.dumps(dict(catalog_complete=complete,entries=len(entries),pages=len(pages),network_bytes=sum(r['acquired_body_bytes'] for r in transfers()))),flush=True)


def match():
    verify();c=read(BASE/'catalog.json');local=read(DSR/'headers_and_roles.json')['files'];matches=[]
    for row in local:
        for e in c['entries']:
            lfs=e.get('lfs') or {};digest=lfs.get('oid') or lfs.get('sha256')
            if digest==row['sha256'] and e.get('size')==row['bytes']:
                matches.append(dict(local_path=row['path'],remote_path=e['path'],bytes=row['bytes'],SHA256=digest,
                    scene=str(Path(e['path']).parent)))
    scenes=sorted({r['scene'] for r in matches});selected=[]
    known={e['path']:e for e in c['entries'] if e['type']=='file'}
    for name in ('README.md','datasets.csv','ATTRIBUTION.md','LICENSE'):
        if name in known and known[name]['size']<=131072:selected.append(name)
    for scene in scenes:
        name=scene+'/metadata.yaml'
        if name in known and known[name]['size']<=131072:selected.append(name)
    acquired=[]
    for name in selected:
        if len(transfers())>=40 or sum(t['acquired_body_bytes'] for t in transfers())>=CAP:break
        r,_=fetch(RESOLVE+urllib.parse.quote(name,safe='/'),'scene_reference' if name.endswith('/metadata.yaml') else 'documentation')
        acquired.append(dict(path=name,transfer_index=r['index'],admitted=r['admitted']))
        if sum(t['acquired_body_bytes'] for t in transfers())>=CAP:break
    result=dict(revision=REV,catalog_complete=c['complete'],local_denominator=len(local),matches=matches,
        matched_local_files=len({r['local_path'] for r in matches}),matched_scene_parents=scenes,
        selected_metadata=selected,acquired_metadata=acquired,network_body_bytes=sum(r['acquired_body_bytes'] for r in transfers()),
        acquisition_body_cap_bytes=CAP,canonical_sample_manifests_acquired=False,point_or_weight_payload_acquired=False,
        numeric_coordinate_reference_pose_metric_or_model_calls=0,independent_confirmation_admitted=False,
        source_link_scope='exact file bytes only; reference construction/training membership remain separate')
    save('identity_links.json',result);verify();print(json.dumps({k:result[k] for k in ('catalog_complete','local_denominator','matched_local_files','matched_scene_parents','network_body_bytes')}),flush=True)


def usage():return dict(wall_seconds=time.monotonic()-START,
    peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
    peak_GPU_allocated_bytes=0,peak_GPU_reserved_bytes=0,artifact_bytes=size(),
    acquired_network_body_bytes=sum(r['acquired_body_bytes'] for r in transfers()),new_scientific_payload_calls=0)


def run(stage):
    spent=sum(read(q)['wall_seconds'] for q in SUP.glob('*/exit.json'));assert spent<900
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('MDA0 aggregate cap')))
    signal.alarm(max(1,int(900-spent)));ok,error=False,None
    try:
        if stage=='freeze':freeze()
        elif stage=='catalog':catalog()
        elif stage=='match':match()
        elif stage=='validate':
            import validate_official_demo_metadata as v
            v.validate()
        else:raise ValueError(stage)
        u=usage();assert u['peak_RSS_bytes']<=128*2**20 and u['artifact_bytes']<16*2**20 and u['acquired_network_body_bytes']<=CAP
        if (SUP/'host_latest.json').exists():assert read(SUP/'host_latest.json')['headroom_bytes']>=4*2**30
        ok=True
    except BaseException as ex:
        error=repr(ex);traceback.print_exc();save('FAILURE_'+stage+'.json',dict(error=error,**usage()))
    finally:
        signal.alarm(0);save('supervision/'+stage+'/child_exit.json',dict(success=ok,error=error,full_resource_capture=True,**usage()))
    if not ok:sys.exit(1)


if __name__=='__main__':run(sys.argv[1])
