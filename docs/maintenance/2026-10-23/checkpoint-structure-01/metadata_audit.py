"""Nonexecuting metadata inventory for the two fixed checkpoint archives."""
import hashlib,json,sys,time,zipfile
from pathlib import Path,PurePosixPath
ROOT=Path(__file__).resolve().parent;START=time.monotonic()
sys.path.insert(0,str(ROOT))
from symbolic_pickle import parse,mapping,tensor_metadata,Node,Symbol
def write(name,value):
    with (ROOT/name).open('x') as f:json.dump(value,f,indent=2)
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest().upper()
ok=False;error=None
try:
    controls=[]
    x=parse(b'\x80\x02]q\x00K\x03ah\x00\x86.');assert x[0] is x[1] and x[0]==[3]
    controls.append(dict(case='memo_and_list_identity',passed=True))
    x=parse(b'\x80\x02}X\x01\x00\x00\x00aK\x03s.');assert x=={'a':3};controls.append(dict(case='dict_values',passed=True))
    x=parse(b'\x80\x02cos\nsystem\nX\x05\x00\x00\x00hello\x85R}b.');assert isinstance(x,Node) and x.call.name=='os system' and x.args==('hello',) and x.state=={}
    controls.append(dict(case='GLOBAL_REDUCE_BUILD_remain_symbols',passed=True))
    storage=Node('persistent',args=('storage',Symbol('torch FloatStorage'),'0','cpu',6))
    tensor=Node('REDUCE',Symbol('torch._utils _rebuild_tensor_v2'),(storage,0,(2,3),(3,1),False,Node('REDUCE',Symbol('collections OrderedDict'),())))
    meta=tensor_metadata(tensor,{'0':24});assert meta['shape']==[2,3] and meta['elements']==6
    controls.append(dict(case='synthetic_tensor_storage_metadata',passed=True))
    for name,raw in [('missing_memo',b'\x80\x02h\x01.'),('trailing',b'\x80\x02N.extra'),('extra_stack',b'\x80\x02NN.'),('duplicate_key',b'\x80\x02}X\x01\x00\x00\x00aK\x01sX\x01\x00\x00\x00aK\x02s.'),('unsupported_extension',b'\x80\x02\x82\x01.'),('truncated',b'\x80\x02X\xff')]:
        try:parse(raw)
        except ValueError:pass
        else:raise AssertionError('Malformed metadata accepted:'+name)
        controls.append(dict(case='reject_'+name,passed=True))
    for name,sizes in [('wrong_bytes',{'0':20}),('missing_storage',{})]:
        try:tensor_metadata(tensor,sizes)
        except ValueError:pass
        else:raise AssertionError('Corrupt storage admitted:'+name)
        controls.append(dict(case='reject_'+name,passed=True))
    write('CONTROLS.json',dict(passed=True,count=len(controls),controls=controls))
    reports=[]
    for row in json.loads((ROOT/'WEIGHT_BINDINGS.json').read_text()):
        p=Path(row['path']);assert p.stat().st_size==row['bytes'] and sha(p)==row['sha256']
        with zipfile.ZipFile(p) as z:
            members=z.infolist();assert len(members)<=4096 and len({m.filename for m in members})==len(members)
            pkl=[m for m in members if PurePosixPath(m.filename).name=='data.pkl'];assert len(pkl)==1 and pkl[0].file_size<=8*2**20
            prefix=pkl[0].filename.rsplit('/',1)[0]
            sizes={m.filename[len(prefix+'/data/'):]:m.file_size for m in members if m.filename.startswith(prefix+'/data/')}
            root=mapping(parse(z.read(pkl[0])))
            states=mapping(root['state_dict']) if 'state_dict' in root else root
            rows={key:tensor_metadata(value,sizes) for key,value in states.items()}
            assert all(isinstance(k,str) for k in rows)
            reports.append(dict(checkpoint=p.name,checkpoint_sha256=row['sha256'],top_keys=sorted(root),state_tensors=len(rows),state_elements=sum(r['elements'] for r in rows.values()),state=rows,unpickling=False,values_decoded=False))
        assert time.monotonic()-START<120
    assert not any(k in sys.modules for k in ('torch','numpy','omegaconf'))
    write('STATE_METADATA.json',dict(passed=True,archives=reports,controls=len(controls),class_execution=False,tensor_values_decoded=False))
    ok=True
except BaseException as caught:
    error=repr(caught)
    import traceback
    write('METADATA_FAILURE.json',dict(error=error,traceback=traceback.format_exc()));raise
finally:write('metadata_exit.json',dict(success=ok,error=error,elapsed_seconds=time.monotonic()-START))
