"""Independent ODA0 directory/range/local-byte validation; no coordinates/network."""
import time
START=time.monotonic()
import hashlib,json,resource,signal,struct,sys,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'docs/maintenance/2026-10-15/original-demo-archive-metadata-01'
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('180s validator cap')))
signal.alarm(180)
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def save(name,value):
    data=(json.dumps(value,indent=2,allow_nan=False)+'\n').encode()
    assert sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file())+len(data)<8*2**20
    with (BASE/name).open('xb') as f:f.write(data)
def run():
    for binding in ('freeze.json','local_bindings02.json'):
        for f in read(BASE/binding)['files']:
            p=Path(f['path'].replace('E:\\githouse\\RAP-main','/mnt/e/githouse/RAP-main').replace('\\','/'))
            assert p.stat().st_size==f['bytes'] and sha(p)==f['sha256'],str(p)
    receipts=[read(BASE/f'receipt-{i:02d}.json') for i in range(3)]
    for r in receipts:
        p=BASE/r['body_path'];assert p.stat().st_size==r['body_bytes'] and sha(p)==r['sha256']
        assert r['admitted'] and r['error'] is None
    assert receipts[0]['kind']=='HEAD' and receipts[0]['status']==200 and receipts[0]['body_bytes']==0
    length=int(receipts[0]['headers']['content-length']);version=receipts[0]['headers']['etag']
    end=(BASE/receipts[1]['body_path']).read_bytes()
    signature,disk,cd_disk,n_disk,n,size,offset,comment=struct.unpack('<4s4H2LH',end)
    assert signature==b'PK\x05\x06' and disk==cd_disk==comment==0 and n_disk==n and n!=65535
    assert offset+size+22==length
    for r,start,count in ((receipts[1],length-22,22),(receipts[2],offset,size)):
        assert r['status']==206 and r['headers']['etag']==version
        assert r['headers']['content-range']==f'bytes {start}-{start+count-1}/{length}'
        assert int(r['headers']['content-length'])==r['body_bytes']==count<=524288
    raw=(BASE/receipts[2]['body_path']).read_bytes();pos=0;rows=[];seen=set()
    for _ in range(n):
        start=pos
        fields=struct.unpack_from('<4s6H3L5H2L',raw,pos);pos+=46
        magic,made,needed,flags,method,mtime,mdate,crc,csize,usize,nl,xl,cl,diskno,iattr,eattr,local=fields
        assert magic==b'PK\x01\x02' and diskno==0 and local<offset
        name=raw[pos:pos+nl].decode('utf-8' if flags&2048 else 'ascii');pos+=nl
        extra=raw[pos:pos+xl];pos+=xl;comment_body=raw[pos:pos+cl];pos+=cl
        assert len(comment_body)==cl and pos<=len(raw) and name not in seen
        assert name and not name.startswith('/') and '..' not in name and '\\' not in name
        seen.add(name);ep=0;tags=[]
        while ep<len(extra):
            tag,sz=struct.unpack_from('<HH',extra,ep);ep+=4;body=extra[ep:ep+sz];ep+=sz
            assert len(body)==sz;tags.append(dict(id=tag,length=sz,hex=body.hex()))
        assert ep==len(extra)
        rows.append(dict(name=name,is_directory=name.endswith('/'),bytes=usize,compressed_bytes=csize,
            crc32=f'{crc:08x}',flags=flags,method=method,local_header_offset=local,central_start=start,
            central_end=pos,extra_fields=tags,comment_bytes=cl,external_attributes=eattr,dos_date=mdate,dos_time=mtime))
    assert pos==len(raw)
    observed=read(BASE/'inventory02.json');assert rows==observed['entries']
    local=read(ROOT/'docs/maintenance/2026-10-15/continuation-handoff-06/DEMO_MEMBER_REQUEST.json')
    files={r['name']:r for r in rows if not r['is_directory']};comparisons=[]
    assert zlib.crc32(b'123456789')==0xcbf43926 and zlib.crc32(b'')==0
    for member,saved in zip(local['members'],observed['local_members']):
        p=ROOT/'demo_example_data'/member['path'];h=hashlib.sha256();crc=0;count=0
        with p.open('rb') as f:
            for b in iter(lambda:f.read(65536),b''):h.update(b);crc=zlib.crc32(b,crc);count+=len(b)
        name='demo_example_data/'+member['path'];r=files[name]
        assert count==member['bytes'] and h.hexdigest()==member['SHA256']
        rebuilt=dict(local_path=member['path'],archive_path=name,bytes=count,sha256=h.hexdigest(),
            local_crc32=f'{crc:08x}',archive_crc32=r['crc32'],length_match=count==r['bytes'],crc32_match=f'{crc:08x}'==r['crc32'])
        assert rebuilt==saved;comparisons.append(rebuilt)
    assert len(comparisons)==len(local['members'])==156
    assert all(r['length_match'] and r['crc32_match'] for r in comparisons)
    assert len(files)==156 and len(rows)==184 and not observed['unmapped_archive_files']
    net=read(BASE/'network_result.json');assert net['new_body_bytes']==sum(r['body_bytes'] for r in receipts)==23099
    assert net['combined_old_new_body_bytes']==1273695+23099<=4194304
    save('validation.json',dict(passed=True,entries=len(rows),point_files=len(files),directories=len(rows)-len(files),
        independent_crc_length_matches=156,current_local_SHA256_matches=156,point_file_bytes=sum(r['bytes'] for r in comparisons),
        independent_range_and_version_predicates=True,new_network_requests=0,new_body_bytes=23099,
        combined_old_new_body_bytes=1296794,cryptographic_remote_member_identity_authenticated=False,
        physical_truth_or_reference_construction_authenticated=False,source_shapes_or_coordinates_decoded=False))
try:
    run();success=True;error=None
except BaseException as ex:
    success=False;error=repr(ex)
finally:
    rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
    save('validation_resource.json',dict(success=success,error=error,seconds=time.monotonic()-START,peak_RSS_bytes=rss,GPU_bytes=0))
    assert rss<=128*2**20,'128MiB local validator cap'
    if not success:raise RuntimeError(error)
