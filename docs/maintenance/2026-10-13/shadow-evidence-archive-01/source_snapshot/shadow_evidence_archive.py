"""LCP0 lossless available-evidence ZIP serialization/packing, no neural imports."""
import base64,hashlib,json,resource,signal,struct,sys,time,traceback,zipfile,zlib
from pathlib import Path
import shadow_prefix_storage_codec as p
ROOT=p.ROOT; OLD=p.OLD; PRIOR=p.BASE
BASE=ROOT/'docs/maintenance/2026-10-13/shadow-evidence-archive-01'; SUP=BASE/'supervision'; START=None
read,sha,save,digest=p.read,p.sha,p.save,p.digest
def source_rows():
    s=read(OLD/'AVAILABLE_DELIVERY_SEAL.json');assert len(s['files'])==576;return s['files']
def freeze():
    f=read(PRIOR/'freeze.json');assert read(PRIOR/'validation.json')['passed'];files=dict(f['files']);delivery=read(PRIOR/'DELIVERY_SEAL.json');assert delivery['entries']==127
    for x in delivery['files']:
        q=(PRIOR/x['path'].replace(chr(92),'/')).resolve();assert PRIOR.resolve() in q.parents and sha(q)==x['sha256'];files[str(q)]=x['sha256']
    paths=[PRIOR/'DELIVERY_SEAL.json',Path(__file__),Path(__file__).with_name('validate_shadow_evidence_archive.py'),Path(__file__).with_name('invoke_mgr_supervised_wsl.ps1'),BASE/'OWNER_SCOPE.md',BASE/'PROTOCOL.md']
    snap=BASE/'source_snapshot';snap.mkdir()
    for q in paths:
        files[str(q)]=sha(q)
        if q.suffix in ('.py','.ps1'):(snap/q.name).write_bytes(q.read_bytes())
    for q,h in files.items():assert sha(q)==h,q
    assert p.repositories()==f['repositories']
    save(BASE/'freeze.json',dict(files=files,repositories=f['repositories'],source_available_entries=576,source_available_bytes=sum(x['bytes'] for x in source_rows()),cap_seconds=1800,cap_RSS_bytes=2*2**30,cap_GPU_bytes=0,cap_artifact_bytes=2*2**30,NPZ_files=440,no_neural_or_GT=True))
    (BASE/'INCOMPLETE').write_text('LCP0 archive serialization/packing/independent original-file reconstruction pending.\n')
    print('LCP0 frozen',len(files),'identities',flush=True)
def verify():
    f=read(BASE/'freeze.json')
    for q,h in f['files'].items():assert sha(q)==h,q
    assert p.repositories()==f['repositories'] and (OLD/'INCOMPLETE').exists() and not (OLD/'prediction_seal.json').exists()
def deflate(raw):
    c=zlib.compressobj(6,zlib.DEFLATED,-15);return c.compress(raw)+c.flush()
def zip_members(q):
    file=q.read_bytes();rows=[]
    with zipfile.ZipFile(q) as z:
        assert not z.testzip()
        for m in sorted(z.infolist(),key=lambda x:x.header_offset):
            offset=m.header_offset;assert file[offset:offset+4]==b'PK\x03\x04'
            nl,el=struct.unpack_from('<HH',file,offset+26);start=offset+30+nl+el;end=start+m.compress_size
            raw=z.read(m.filename);payload=file[start:end];assert len(raw)==m.file_size and m.compress_type in (0,8)
            rows.append(dict(name=m.filename,start=start,end=end,method=m.compress_type,raw=raw,payload=payload))
    return file,rows
def compatibility():
    verify();rows=[];members=0;methods={0:0,8:0}
    for x in source_rows():
        if not x['path'].endswith('.npz'):continue
        q=OLD/x['path'];file,ms=zip_members(q);assert digest(file)==x['sha256']
        for m in ms:
            rebuilt=m['raw'] if m['method']==0 else deflate(m['raw'])
            assert rebuilt==m['payload'],(x['path'],m['name'],'original ZIP deflate payload mismatch')
            members+=1;methods[m['method']]+=1
        rows.append(dict(path=x['path'],members=len(ms),original_compressed_payloads_byteexact=True));cap()
    assert len(rows)==440
    save(BASE/'compatibility.json',dict(passed=True,NPZ_files=440,members=members,method_counts=methods,records=rows,original_level6_raw_deflate_serialization_byteexact=True,no_parameter_search=True,models_GT_calls=0))
    verify();print('LCP0 full ZIP serialization compatibility',len(rows),'files',members,'members',flush=True)
def xor_bytes(a,b):
    assert len(a)==len(b);out=[]
    for o in range(0,len(a),65536):
        x=a[o:o+65536];y=b[o:o+65536];out.append((int.from_bytes(x,'little')^int.from_bytes(y,'little')).to_bytes(len(x),'little'))
    return b''.join(out)
def pack():
    verify();assert read(BASE/'compatibility.json')['passed'];folder=BASE/'packed';folder.mkdir();blobdir=folder/'blobs';blobdir.mkdir();objects={};records=[]
    def put(raw,base=None):
        key=digest(raw)
        if key in objects:return key
        mode='zlib6';data=raw;basekey=None
        if base is not None and len(base)==len(raw):
            basekey=put(base);assert basekey!=key;data=xor_bytes(raw,base);mode='XOR_byte_chunks_zlib6'
        packed=zlib.compress(data,6)
        if basekey is None and len(packed)>=len(data):packed=data;mode='raw'
        q=blobdir/(key+'.blob');q.write_bytes(packed)
        objects[key]=dict(raw_sha256=key,raw_bytes=len(raw),representation=mode,base_raw_sha256=basekey,encoded_path=str(q.relative_to(BASE)),encoded_bytes=len(packed),encoded_sha256=sha(q))
        return key
    def delta_base(path,member):
        parts=Path(path).parts
        if parts[0]=='predictions' and parts[-1].startswith('step_') and member=='prefix.npy' and parts[1].split('_')[0] in ('V','P'):
            base=OLD/'predictions'/('U_'+parts[1].split('_',1)[1])/parts[-1]
        elif parts[0]=='fits' and parts[-1]=='after.npz':base=OLD/Path(path).with_name('before.npz')
        else:return None
        with zipfile.ZipFile(base) as z:return z.read(member)
    for n,x in enumerate(source_rows()):
        q=OLD/x['path'];assert sha(q)==x['sha256'];rec=dict(path=x['path'],original_sha256=x['sha256'],original_bytes=x['bytes'])
        if q.suffix=='.npz':
            file,ms=zip_members(q);chunks=[];pos=0
            for m in ms:
                payload=m['raw'] if m['method']==0 else deflate(m['raw']);assert payload==m['payload']
                chunks.append(dict(kind='literal',bytes_base64=base64.b64encode(file[pos:m['start']]).decode()))
                chunks.append(dict(kind='ZIP_member',method=m['method'],original_payload_sha256=digest(m['payload']),original_payload_bytes=len(m['payload']),raw_object=put(m['raw'],delta_base(x['path'],m['name'])),member=m['name']))
                pos=m['end']
            chunks.append(dict(kind='literal',bytes_base64=base64.b64encode(file[pos:]).decode()));rec.update(kind='exact_ZIP_template',chunks=chunks)
        else:rec.update(kind='full_file_object',raw_object=put(q.read_bytes()))
        records.append(rec);cap()
        if (n+1)%40==0:print('LCP0 packed',n+1,'source files; objects',len(objects),flush=True)
    assert len(records)==576
    save(folder/'manifest.json',dict(format='LCP0_available_evidence_exact_original_file_bytes_v1',records=records,objects=objects,source_available_seal_sha256=sha(OLD/'AVAILABLE_DELIVERY_SEAL.json'),source_available_files=576,source_available_bytes=sum(x['bytes'] for x in source_rows()),source_scientific_comparison_INCOMPLETE=True,all_base_payloads_included=True,missing_cases_generated=False))
    save(BASE/'packed_seal.json',dict(files={str(q.relative_to(folder)):sha(q) for q in sorted(folder.rglob('*')) if q.is_file()},freeze_sha256=sha(BASE/'freeze.json')))
    verify();print('LCP0 pack complete',len(objects),'unique payload objects',flush=True)
def usage():return dict(wall_seconds=time.monotonic()-START,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,peak_GPU_allocated_bytes=0,peak_GPU_reserved_bytes=0,artifact_bytes=sum(q.stat().st_size for q in BASE.rglob('*') if q.is_file()),imports_included=True,optimizer_calls=0,neural_calls=0)
def cap():
    u=usage();assert u['peak_RSS_bytes']<=2*2**30 and u['artifact_bytes']<=2*2**30,u
    if (SUP/'host_latest.json').exists():assert read(SUP/'host_latest.json')['headroom_bytes']>=4*2**30
def run(stage):
    global START
    START=time.monotonic();used=sum(read(q)['wall_seconds'] for q in SUP.glob('*/child_exit.json'));assert used<1800
    signal.signal(signal.SIGALRM,lambda a,b:(_ for _ in ()).throw(TimeoutError('LCP0 aggregate attempted-child time cap')));signal.alarm(max(1,int(1800-used)));ok=False;error=None
    try:
        if stage=='freeze':freeze()
        elif stage=='compatibility':compatibility()
        elif stage=='pack':pack()
        elif stage=='validate':
            import validate_shadow_evidence_archive as v;v.validate()
        else:raise ValueError(stage)
        cap();ok=True
    except BaseException as ex:error=repr(ex);traceback.print_exc();save(BASE/f'FAILURE_{stage}.json',dict(error=error,**usage()))
    finally:signal.alarm(0);save(SUP/stage/'child_exit.json',dict(success=ok,error=error,full_resource_capture=True,**usage()))
    if not ok:sys.exit(1)
if __name__=='__main__':sys.modules['shadow_evidence_archive']=sys.modules[__name__];run(sys.argv[1])
