import collections,hashlib,json,os,stat,sys,time,zipfile
from pathlib import Path,PurePosixPath

ROOT=Path(__file__).resolve().parent
START=time.monotonic()
def check():
    if time.monotonic()-START>=175:raise TimeoutError('worker deadline reserve')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,obj):
    with (ROOT/name).open('x',encoding='utf-8') as f:json.dump(obj,f,indent=2,ensure_ascii=True)

try:
    freeze=json.loads((ROOT/'SOURCE_FREEZE.json').read_text(encoding='utf-8-sig'))
    for name,h in freeze['files'].items():assert sha(ROOT/name)==h.lower(),name
    binding=json.loads((ROOT/'INPUT_BINDING.json').read_text(encoding='utf-8-sig'))
    request=Path(binding['request_path']);assert sha(request)==binding['request_sha256']
    req=json.loads(request.read_text(encoding='utf-8-sig'));wanted=[r['archive_member'] for r in req['members']]
    assert len(wanted)==273 and len(set(wanted))==273
    archive=Path(binding['archive_path']);before=archive.stat()
    assert before.st_size==binding['archive_bytes'] and before.st_size<=26*1024**3
    h=hashlib.sha256();read_bytes=0
    with archive.open('rb') as f:
        while True:
            check();block=f.read(1024**2)
            if not block:break
            h.update(block);read_bytes+=len(block)
    assert read_bytes==before.st_size
    complete_hash=h.hexdigest();names=collections.Counter();counts=collections.Counter();selected=[];metadata=[];listing=hashlib.sha256();bad_paths=[]
    with zipfile.ZipFile(archive,'r') as z:
        entries=z.infolist();assert len(entries)<=150000
        for item in entries:
            check();name=item.filename;names[name]+=1
            path=PurePosixPath(name)
            if path.is_absolute() or '..' in path.parts or '\\' in name or ':' in name:bad_paths.append(name)
            parts=path.parts
            if len(parts)>=5 and parts[:2]==('dataset','sequences') and parts[3] in ('image_0','image_1','image_2','image_3'):counts[parts[2]+'/'+parts[3]]+=int(not item.is_dir())
            record={'name':name,'bytes':item.file_size,'compressed_bytes':item.compress_size,'CRC32':f'{item.CRC:08x}','compression':item.compress_type,'flags':item.flag_bits,'header_offset':item.header_offset}
            listing.update(json.dumps(record,sort_keys=True,separators=(',',':')).encode('utf-8')+b'\n')
            if name in wanted:
                assert not item.flag_bits&1 and item.compress_type in (zipfile.ZIP_STORED,zipfile.ZIP_DEFLATED)
                assert 33<=item.file_size<=2*1024**2
                selected.append(record)
            if not item.is_dir() and (path.name in ('calib.txt','times.txt') or path.suffix.lower() in ('.md','.pdf') or 'readme' in path.name.lower()):metadata.append(record)
        missing=sorted(set(wanted)-set(names));duplicates=sorted(n for n,c in names.items() if c>1)
        assert not bad_paths and not missing and not duplicates
        assert len(selected)==273 and sum(x['bytes'] for x in selected)<=512*1024**2
    after=archive.stat();assert (before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns)
    save('MEMBERS.json',{'required':selected,'metadata_candidates_not_read':metadata,'camera_counts':dict(sorted(counts.items()))})
    save('RESULTS.json',{'passed':True,'archive_path':str(archive),'archive_bytes':read_bytes,'archive_sha256':complete_hash,'archive_mtime_ns':before.st_mtime_ns,'archive_stat_unchanged':True,'index_entries':len(entries),'ordered_index_sha256':listing.hexdigest(),'required_members':len(selected),'missing_required':missing,'duplicate_names':duplicates,'unsafe_names':bad_paths,'required_declared_bytes':sum(x['bytes'] for x in selected),'camera_counts':dict(sorted(counts.items())),'metadata_candidates_count':len(metadata),'image_decompression_or_decode':False,'CRC_verified':False,'dimensions_known':False,'numeric_reference_or_calibration_read':False,'elapsed_seconds':time.monotonic()-START})
    print(json.dumps({'passed':True,'required_members':len(selected),'archive_bytes':read_bytes,'elapsed_seconds':time.monotonic()-START}))
except BaseException as e:
    save('FAILURE.json',{'error':repr(e),'elapsed_seconds':time.monotonic()-START});raise
