"""LPC0 independent stdlib NPY parser and byte decoder, no NumPy/torch."""
import ast, hashlib, struct, zipfile, zlib
import shadow_prefix_storage_codec as r
def parse_member(q):
    with zipfile.ZipFile(q) as z: member=z.read('prefix.npy')
    assert member[:6] == b'\x93NUMPY'; version=tuple(member[6:8])
    if version == (1,0): hlen=struct.unpack('<H',member[8:10])[0]; start=10
    elif version in ((2,0),(3,0)): hlen=struct.unpack('<I',member[8:12])[0]; start=12
    else: raise AssertionError(version)
    layout=ast.literal_eval(member[start:start+hlen].decode('utf-8' if version==(3,0) else 'latin1'))
    assert layout == {'descr':'<f4','fortran_order':False,'shape':(3000,512)}
    header, raw=member[:start+hlen],member[start+hlen:]; assert len(raw)==6144000
    return header,raw,member
def reconstruct(row, base):
    if row['representation']=='source_base_alias': return base
    assert row['representation']=='uint32_XOR_zlib6'
    q=r.BASE/row['encoded_path']; assert r.sha(q)==row['encoded_sha256']
    packed=q.read_bytes(); stream=zlib.decompressobj(); delta=stream.decompress(packed)+stream.flush()
    assert stream.eof and not stream.unused_data and len(delta)==len(base) and r.digest(delta)==row['raw_delta_sha256']
    # Independent byte interpretation: arbitrary precision byte chunks, no uint32 array view.
    out=[]
    for offset in range(0,len(base),65536):
        b=base[offset:offset+65536]; d=delta[offset:offset+65536]
        out.append((int.from_bytes(b,'little')^int.from_bytes(d,'little')).to_bytes(len(b),'little'))
    return b''.join(out)
def validate():
    r.verify(); r.check_seal(r.BASE/'encoded','encoded_seal.json'); m=r.read(r.BASE/'encoded/manifest.json')
    rows=m['records']; assert len(rows)==100
    expected={(q.parent.name,i) for q in (r.OLD/'predictions').glob('*/step_0.npz') if q.parent.name.split('_')[0] in ('V','P') for i in range(5)}
    actual={(x['arm']+'_'+x['noise'],x['step']) for x in rows}; assert actual==expected and len(actual)==100
    checks=[]; total=baseline=raw_total=aliases=0
    for row in rows:
        q=r.Path(row['source_path']); qb=r.Path(row['base_path'])
        assert r.sha(q)==row['source_sha256'] and r.sha(qb)==row['base_sha256']
        h,raw,member=parse_member(q); bh,base,bm=parse_member(qb)
        assert r.digest(member)==row['source_member_sha256'] and r.digest(bm)==row['base_member_sha256']
        assert row['dtype']=='<f4' and row['shape']==[3000,512] and row['byte_order']=='little' and row['order']=='C'
        assert r.digest(base)==row['base_raw_sha256'] and r.digest(raw)==row['source_raw_sha256']
        decoded=reconstruct(row,base); assert decoded==raw and r.digest(h+decoded)==row['source_member_sha256']
        if row['representation']=='source_base_alias': aliases+=1
        elif row['step']==0: raise AssertionError('initial shared state/prefix must bind exactly')
        total+=row['encoded_bytes']; baseline+=row['baseline_member_compressed_bytes']; raw_total+=len(raw)
        checks.append(dict(arm=row['arm'],noise=row['noise'],step=row['step'],byteexact=True,reconstructed_raw_sha256=r.digest(decoded),reconstructed_NPY_sha256=r.digest(h+decoded)))
        r.cap()
    fixtures=[]
    for row in m['fixtures']:
        target=(r.BASE/row['target_path']).read_bytes(); base=(r.BASE/row['base_path']).read_bytes()
        assert r.digest(target)==row['target_sha256'] and r.digest(base)==row['base_sha256']
        assert reconstruct(row,base)==target; fixtures.append(dict(name=row['name'],byteexact=True))
    assert aliases>=20 and len(fixtures)==4
    r.verify(); r.save(r.BASE/'validation.json',dict(passed=True,decision='AVAILABLE_PREFIX_BIT_IDENTITY_AND_LOSSLESS_REPRESENTATION_VALID',complete_source_matrices=100,source_aliases=aliases,encoded_deltas=100-aliases,independent_byte_decoder=True,independent_NPY_parser=True,all_array_and_NPY_member_bytes_exact=True,records=checks,fixtures=fixtures,raw_source_bytes=raw_total,baseline_compressed_prefix_member_bytes=baseline,encoded_delta_bytes=total,delta_to_old_member_ratio=total/baseline,source_base_bytes_not_counted_as_new_output=True,missing_P14_cases_not_synthesized=True,complete_future_bank_fit_not_proven=True,old_HFIT_comparison_INCOMPLETE=True,neural_GT_calls=0))
    print('LPC0 independent reconstruction passes',len(checks),'prefixes; bytes',total,'baseline',baseline,'aliases',aliases,flush=True)
