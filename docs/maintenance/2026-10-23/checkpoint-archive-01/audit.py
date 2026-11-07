"""ZIP/pickle opcode metadata only: no unpickling, torch or global execution."""
import collections, hashlib, io, json, pickletools, sys, time, zipfile
from pathlib import Path, PurePosixPath
ROOT=Path(__file__).resolve().parent;START=time.monotonic()
LIMIT=8*2**20
def write(name,value):
    with (ROOT/name).open('x',encoding='utf-8') as f:json.dump(value,f,indent=2)
def scan(raw):
    if len(raw)>LIMIT:raise ValueError('metadata_size_cap')
    ops=list(pickletools.genops(raw))
    if not ops or ops[-1][0].name!='STOP' or ops[-1][2]+1!=len(raw):raise ValueError('missing_STOP_or_trailing_bytes')
    names=collections.Counter(o.name for o,_,_ in ops)
    globals_=collections.Counter(str(a) for o,a,_ in ops if o.name=='GLOBAL')
    strings=[a for o,a,_ in ops if o.name in ('BINUNICODE','SHORT_BINUNICODE','UNICODE','STRING') and isinstance(a,str)]
    keys=[s for s in strings if s.startswith(('flow_model.','Desc.','feature_extractor.'))]
    return dict(opcodes=dict(names),opcode_count=len(ops),globals=dict(globals_),STACK_GLOBAL_count=names['STACK_GLOBAL'],
        tensor_key_strings=keys,tensor_key_string_count=len(keys),state_dict_literal_count=strings.count('state_dict'),
        persistent_reference_opcodes=names['BINPERSID']+names['PERSID'],
        no_pickle_execution=True,complete_tensor_semantics_validated=False)
def sha_file(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest().upper()
ok=False;error=None
try:
    controls=[]
    for name,raw,want in [('none',b'\x80\x02N.',{}),('symbolic_os_system',b'\x80\x02cos\nsystem\nX\x05\x00\x00\x00hello\x85R.',{'os system':1}),('symbolic_BUILD',b'\x80\x02cnever_imported_module\nNeverConstruct\n)R}b.',{'never_imported_module NeverConstruct':1})]:
        got=scan(raw);assert got['globals']==want
        assert 'never_imported_module' not in sys.modules
        controls.append(dict(case=name,passed=True,descriptive_only=True))
    for name,raw in [('truncated',b'\x80\x02X\xff'),('missing_stop',b'\x80\x02N'),('trailing_bytes',b'\x80\x02N.hidden'),('oversized',b'N'*(LIMIT+1))]:
        try:scan(raw)
        except (ValueError,IndexError):pass
        else:raise AssertionError('Malformed control accepted:'+name)
        controls.append(dict(case=name,passed=True,rejected=True))
    write('CONTROLS.json',dict(passed=True,count=len(controls),controls=controls))
    reports=[]
    for row in json.loads((ROOT/'WEIGHT_BINDINGS.json').read_text()):
        p=Path(row['path']);assert p.stat().st_size==row['bytes'] and p.stat().st_size<=512*2**20 and sha_file(p)==row['sha256']
        entries=[];total=0
        with zipfile.ZipFile(p) as z:
            members=z.infolist();assert 0<len(members)<=4096
            names=[m.filename for m in members];assert len(names)==len(set(names))
            for m in members:
                q=PurePosixPath(m.filename)
                assert not q.is_absolute() and '..' not in q.parts and '\\' not in m.filename and not m.flag_bits&1
                total+=m.file_size
            assert total<=512*2**20
            metadata=[m for m in members if PurePosixPath(m.filename).name=='data.pkl'];assert len(metadata)==1 and metadata[0].file_size<=LIMIT
            for m in members:
                h=hashlib.sha256();size=0
                with z.open(m) as f:
                    for b in iter(lambda:f.read(1024*1024),b''):h.update(b);size+=len(b)
                assert size==m.file_size
                entries.append(dict(name=m.filename,bytes=size,compressed_bytes=m.compress_size,CRC32=f'{m.CRC:08X}',sha256=h.hexdigest().upper()))
            result=scan(z.read(metadata[0]))
            storage=[m for m in members if '/data/' in m.filename and PurePosixPath(m.filename).name.isdecimal()]
            reports.append(dict(checkpoint=p.name,checkpoint_sha256=row['sha256'],archive_entries=len(members),uncompressed_bytes=total,metadata_bytes=metadata[0].file_size,storage_entries=len(storage),storage_bytes=sum(m.file_size for m in storage),pickle=result,entries=entries))
        assert time.monotonic()-START<120
    assert not any(n in sys.modules for n in ('torch','numpy','omegaconf'))
    write('RESULTS.json',dict(passed=True,archives=reports,controls=len(controls),numeric_imports=False,unpickling=False,model_constructors=0,point_reads=0,reference_reads=0,claim='Nonexecuting archive/opcode metadata only'))
    ok=True
except BaseException as caught:
    error=repr(caught)
    import traceback
    write('FAILURE.json',dict(error=error,traceback=traceback.format_exc()));raise
finally:
    write('worker_exit.json',dict(success=ok,error=error,elapsed_seconds=time.monotonic()-START,python_version=sys.version))
