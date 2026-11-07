import collections,hashlib,io,json,struct,time,zipfile,zlib
from decimal import Decimal
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parent;START=time.monotonic()
def check():
    if time.monotonic()-START>=175:raise TimeoutError('worker deadline reserve')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,obj):
    with (ROOT/name).open('x',encoding='utf-8') as f:json.dump(obj,f,indent=2,ensure_ascii=True)
def png(data):
    assert data[:8]==b'\x89PNG\r\n\x1a\n';pos=8;chunks=[];shape=None
    while pos<len(data):
        assert pos+12<=len(data);n=struct.unpack('>I',data[pos:pos+4])[0];tag=data[pos+4:pos+8];end=pos+12+n;assert end<=len(data)
        payload=data[pos+8:pos+8+n];crc=struct.unpack('>I',data[pos+8+n:end])[0];assert zlib.crc32(tag+payload)&0xffffffff==crc
        if not chunks:
            assert tag==b'IHDR' and n==13;w,h,depth,color,comp,filt,inter=struct.unpack('>IIBBBBB',payload);assert depth==8 and color==0 and comp==0 and filt==0 and inter in (0,1);assert 0<w<=4096 and 0<h<=2048 and w*h<=8388608;shape=(w,h)
        chunks.append(tag);pos=end
        if tag==b'IEND':assert n==0 and pos==len(data);break
    assert chunks[-1]==b'IEND' and b'IDAT' in chunks
    with Image.open(io.BytesIO(data)) as im:
        assert im.format=='PNG' and im.mode=='L' and im.size==shape;im.load()
    return shape,len(chunks)
def calibration(data):
    result={}
    for line in data.decode('ascii').splitlines():
        if not line.strip():continue
        key,values=line.split(':',1);assert key not in result;row=[Decimal(t) for t in values.split()];assert len(row)==12 and all(v.is_finite() for v in row);result[key]=row
    return result
def timestamps(data):
    rows=[Decimal(v.strip()) for v in data.decode('ascii').splitlines() if v.strip()];assert all(v.is_finite() for v in rows);return rows

try:
    freeze=json.loads((ROOT/'SOURCE_FREEZE.json').read_text(encoding='utf-8-sig'))
    for name,h in freeze['files'].items():assert sha(ROOT/name)==h.lower(),name
    bind=json.loads((ROOT/'INPUT_BINDING.json').read_text(encoding='utf-8-sig'));ad=Path(bind['admission_dir'])
    assert sha(ad/'RESULTS.json')==bind['admission_results_sha256'] and sha(ad/'MEMBERS.json')==bind['admission_members_sha256']
    result=json.loads((ad/'RESULTS.json').read_text());members=json.loads((ad/'MEMBERS.json').read_text());assert result['passed'] and len(members['required'])==273
    for entry in bind['local_metadata']:assert sha(Path(entry['path']))==entry['sha256']
    archive=Path(result['archive_path']);before=archive.stat();assert (before.st_size,before.st_mtime_ns)==(result['archive_bytes'],result['archive_mtime_ns'])
    rows=[];dimensions=collections.Counter();associations=[];total=0
    with zipfile.ZipFile(archive) as z:
        listing=hashlib.sha256()
        for item in z.infolist():
            check();record={'name':item.filename,'bytes':item.file_size,'compressed_bytes':item.compress_size,'CRC32':f'{item.CRC:08x}','compression':item.compress_type,'flags':item.flag_bits,'header_offset':item.header_offset};listing.update(json.dumps(record,sort_keys=True,separators=(',',':')).encode()+b'\n')
        assert listing.hexdigest()==result['ordered_index_sha256']
        for record in members['required']:
            check();info=z.getinfo(record['name']);assert info.file_size==record['bytes'] and f'{info.CRC:08x}'==record['CRC32'];data=z.read(info);assert len(data)==record['bytes'] and zlib.crc32(data)&0xffffffff==info.CRC
            (w,h),nchunks=png(data);seq=record['name'].split('/')[2];dimensions[(seq,w,h)]+=1
            output=ROOT/'images'/record['name'];assert output.resolve().is_relative_to(ROOT.resolve());output.parent.mkdir(parents=True,exist_ok=True)
            with output.open('xb') as f:f.write(data)
            total+=len(data);assert total<=512*1024**2
            rows.append({'member':record['name'],'relative_path':output.relative_to(ROOT).as_posix(),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'CRC32':record['CRC32'],'sequence':seq,'width':w,'height':h,'bit_depth':8,'mode':'L','PNG_chunks_verified':nchunks,'full_pixel_decode_pass':True})
        assert len(rows)==273
        for seq in ('00','08'):
            seq_records={x['kind']:x for x in bind['local_metadata'] if x['sequence']==seq}
            data={kind:z.read(f'dataset/sequences/{seq}/{kind}') for kind in ('calib.txt','times.txt')}
            target=ROOT/'metadata'/seq;target.mkdir(parents=True,exist_ok=False)
            for kind,content in data.items():assert len(content)<=1024**2;(target/kind).write_bytes(content)
            local_calib=Path(seq_records['calib.txt']['path']).read_bytes();local_times=Path(seq_records['times.txt']['path']).read_bytes()
            a=calibration(data['calib.txt']);b=calibration(local_calib);shared=sorted(a.keys()&b.keys());assert all(k in shared for k in ('P0','P1','P2','P3'));equal=all(a[k]==b[k] for k in shared);assert equal,'Projection calibration mismatch'
            t=timestamps(data['times.txt']);u=timestamps(local_times);assert t==u and len(t)==result['camera_counts'][seq+'/image_0'],'Timestamp association mismatch'
            ids=[int(Path(r['member']).stem) for r in rows if r['sequence']==seq];assert max(ids)<len(t)
            associations.append({'sequence':seq,'archive_calib_sha256':hashlib.sha256(data['calib.txt']).hexdigest(),'local_calib_sha256':seq_records['calib.txt']['sha256'],'projection_keys_compared_exact_Decimal':shared,'projection_entries_equal':equal,'archive_only_keys':sorted(a.keys()-b.keys()),'local_only_keys':sorted(b.keys()-a.keys()),'Tr_supplied_by_new_archive':'Tr' in a,'archive_times_sha256':hashlib.sha256(data['times.txt']).hexdigest(),'local_times_sha256':seq_records['times.txt']['sha256'],'timestamp_bytes_equal':data['times.txt']==local_times,'timestamp_rows_equal_exact_Decimal':True,'timestamp_rows':len(t),'selected_IDs_in_range':True})
    after=archive.stat();assert (before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns)
    save('IMAGE_MANIFEST.json',{'rows':rows,'complete_pairs':200,'required_members':273,'images_bytes':total,'associations':associations})
    save('RESULTS.json',{'passed':True,'complete_images':273,'images_bytes':total,'archive_sha256_from_IA1':result['archive_sha256'],'archive_stat_and_index_unchanged':True,'all_ZIP_CRC_PNG_chunks_full_pixel_decodes_pass':True,'dimensions':[{'sequence':s,'width':w,'height':h,'count':c} for (s,w,h),c in sorted(dimensions.items())],'associations':associations,'source_role':'Owner-provided archive and supplied-record consistency; no independent physical calibration or prior extraction certification','pose_reference_reads':0,'models_features_solvers':0,'elapsed_seconds':time.monotonic()-START})
    print(json.dumps({'passed':True,'complete_images':273,'images_bytes':total,'dimensions':list(dimensions.items()),'elapsed_seconds':time.monotonic()-START}))
except BaseException as e:
    save('FAILURE.json',{'error':repr(e),'elapsed_seconds':time.monotonic()-START});raise
