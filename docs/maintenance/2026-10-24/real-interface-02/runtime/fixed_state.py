"""Fixed hash-bound raw storage reader; no pickle/global/model constructors."""
import hashlib,zipfile
from pathlib import Path,PurePosixPath
from tensor_candidate import decode,tensor_hash
def path(value):return Path('/mnt/'+value[0].lower()+'/'+value[3:].replace('\\','/'))
def sha_file(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest().upper()
def decode_archive(weight,inventory,archive,torch,descriptor_only=False):
    p=path(weight['path']);assert p.stat().st_size==weight['bytes'] and sha_file(p)==weight['sha256']
    records=inventory['state']
    records=records if not descriptor_only else {k[5:]:v for k,v in records.items() if k.startswith('Desc.')}
    decoded={};hashes={};byteorder=None
    with zipfile.ZipFile(p) as z:
        members=z.infolist();names=[m.filename for m in members];assert len(names)==len(set(names))
        pkl=[m for m in members if PurePosixPath(m.filename).name=='data.pkl'];assert len(pkl)==1
        prefix=pkl[0].filename.rsplit('/',1)[0]
        order=prefix+'/byteorder'
        if order in names:byteorder=z.read(order).decode();assert byteorder=='little'
        elif not descriptor_only:raise ValueError('RAP_explicit_byteorder_required')
        elif torch.serialization.get_default_load_endianness() not in (None,torch.serialization.LoadEndianness.LITTLE):raise ValueError('legacy_byteorder_default')
        expected_members={r['name']:r for r in archive['entries']}
        for key,meta in records.items():
            member=prefix+'/data/'+meta['storage'];record=expected_members[member]
            assert record['bytes']<=64*2**20 and z.getinfo(member).file_size==record['bytes']
            raw=z.read(member);decoded[key]=decode(raw,meta,record['sha256'],torch);hashes[key]=record['sha256']
    return decoded,hashes,dict(byteorder_marker=byteorder,legacy_default_little=descriptor_only and byteorder is None,ignored_non_Desc_tensors=inventory['state_tensors']-len(decoded) if descriptor_only else 0)
def verify_model(model,expected_hashes,torch):
    actual=model.state_dict();assert set(actual)==set(expected_hashes)
    rows=[]
    for key,a in actual.items():
        got=tensor_hash(a);assert got==expected_hashes[key],key
        assert not a.is_floating_point() or torch.isfinite(a).all(),key
        rows.append(dict(key=key,sha256=got,exact_archive_bytes=True,finite=True))
    return rows
