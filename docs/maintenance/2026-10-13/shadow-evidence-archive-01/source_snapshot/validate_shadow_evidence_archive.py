"""LCP0 independent uint8 decoder and complete file-byte reconstruction."""
import base64,collections,hashlib,zlib
import numpy as np
import shadow_evidence_archive as r
def validate():
    r.verify();s=r.read(r.BASE/'packed_seal.json');folder=r.BASE/'packed'
    assert s['freeze_sha256']==r.sha(r.BASE/'freeze.json') and s['files']=={str(q.relative_to(folder)):r.sha(q) for q in sorted(folder.rglob('*')) if q.is_file()}
    m=r.read(folder/'manifest.json');objects=m['objects'];assert m['all_base_payloads_included'] and m['source_scientific_comparison_INCOMPLETE']
    cache=collections.OrderedDict();cache_bytes=0;seen=set()
    def decode(key,stack=()):
        nonlocal cache_bytes
        if key in cache:cache.move_to_end(key);return cache[key]
        assert key not in stack and key in objects
        row=objects[key];q=r.BASE/row['encoded_path'];assert r.sha(q)==row['encoded_sha256'];packed=q.read_bytes()
        raw=packed if row['representation']=='raw' else zlib.decompress(packed)
        if row['representation']=='XOR_byte_chunks_zlib6':
            base=decode(row['base_raw_sha256'],stack+(key,));assert len(base)==len(raw)
            raw=np.bitwise_xor(np.frombuffer(raw,dtype=np.uint8),np.frombuffer(base,dtype=np.uint8)).tobytes()
        else:assert row['representation'] in ('zlib6','raw') and row['base_raw_sha256'] is None
        assert len(raw)==row['raw_bytes'] and r.digest(raw)==key==row['raw_sha256'];seen.add(key)
        cache[key]=raw;cache_bytes+=len(raw)
        while cache_bytes>128*2**20 and len(cache)>1:
            _,value=cache.popitem(last=False);cache_bytes-=len(value)
        return raw
    expected={x['path']:x for x in r.source_rows()};actual={x['path']:x for x in m['records']};assert len(actual)==len(m['records'])==576 and actual.keys()==expected.keys();checks=[];total=0
    for n,row in enumerate(m['records']):
        if row['kind']=='full_file_object':data=decode(row['raw_object'])
        else:
            assert row['kind']=='exact_ZIP_template';segments=[]
            for chunk in row['chunks']:
                if chunk['kind']=='literal':segment=base64.b64decode(chunk['bytes_base64'],validate=True)
                else:
                    assert chunk['kind']=='ZIP_member';raw=decode(chunk['raw_object'])
                    if chunk['method']==0:segment=raw
                    else:
                        assert chunk['method']==8;c=zlib.compressobj(level=6,wbits=-zlib.MAX_WBITS);segment=c.compress(raw)+c.flush()
                    assert len(segment)==chunk['original_payload_bytes'] and r.digest(segment)==chunk['original_payload_sha256']
                segments.append(segment)
            data=b''.join(segments)
        original=r.OLD/row['path'];assert data==original.read_bytes() and r.digest(data)==expected[row['path']]['sha256']==row['original_sha256'] and len(data)==row['original_bytes']==expected[row['path']]['bytes']
        total+=len(data);checks.append(dict(path=row['path'],original_file_byteexact=True,reconstructed_sha256=r.digest(data),bytes=len(data)));r.cap()
        if (n+1)%40==0:print('LCP0 independently reconstructed',n+1,'original files',flush=True)
    assert seen==set(objects) and total==m['source_available_bytes']
    encoded=sum(x['encoded_bytes'] for x in objects.values());metadata=(folder/'manifest.json').stat().st_size;packed_bytes=sum(q.stat().st_size for q in folder.rglob('*') if q.is_file())
    assert packed_bytes==encoded+metadata and packed_bytes<2*2**30
    kinds=collections.Counter(x['representation'] for x in objects.values());r.verify()
    r.save(r.BASE/'validation.json',dict(passed=True,decision='ALL_AVAILABLE_EVIDENCE_ORIGINAL_FILE_BYTES_RECONSTRUCT_EXACTLY',source_original_files=576,source_original_bytes=total,unique_raw_objects=len(objects),objects_by_representation=dict(kinds),encoded_object_bytes=encoded,manifest_bytes=metadata,self_contained_packed_evidence_bytes=packed_bytes,packed_to_source_ratio=packed_bytes/total,independent_uint8_decoder=True,all_original_files_byteexact=True,all_base_objects_embedded=True,all_manifest_objects_reached=True,records=checks,missing_P14_cases_not_synthesized=True,complete_future_bank_budget_not_proven=True,old_HFIT_scientific_INCOMPLETE=True,neural_gradient_GT_calls=0))
    print('LCP0 all576 files byteexact; self-contained available evidence',packed_bytes,'bytes; source',total,flush=True)
