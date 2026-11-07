"""C0 custom interface, not canonical batch or an efficacy experiment."""
import decimal
import fractions
import hashlib
import json
import math
import pathlib
import resource
import signal
import struct
import sys
import time
import traceback

ROOT = pathlib.Path(__file__).resolve().parents[2]
BASE = ROOT / 'docs/maintenance/2026-10-16/regx-interface-contract-01'
B1 = ROOT / 'docs/maintenance/2026-10-16/regx-reference-package-01'
B2 = ROOT / 'docs/maintenance/2026-10-16/regx-reference-code-01'
START = time.monotonic()
def _deadline(signum, frame):
    raise TimeoutError('C0 combined execution deadline')
signal.signal(signal.SIGALRM, _deadline)
D = decimal.Decimal
decimal.getcontext().prec = 50

def sha(p):
    h = hashlib.sha256()
    with pathlib.Path(p).open('rb') as f:
        while b := f.read(65536): h.update(b)
    return h.hexdigest()

def save(path, value, raw=False):
    data = value if raw else (json.dumps(value, indent=2, ensure_ascii=False)+'\n').encode()
    current = sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file())
    assert current+len(data)+32768 <= 16*1024*1024, 'controlled dossier reservation'
    path = pathlib.Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as f: f.write(data)

def mm(a, b):
    return [[sum(a[i][k]*b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]

def inverse(a):
    z = type(a[0][0])(0); one = type(a[0][0])(1)
    rows = [list(a[i])+[one if i==j else z for j in range(4)] for i in range(4)]
    for k in range(4):
        pivot = max(range(k, 4), key=lambda i: abs(rows[i][k]))
        assert rows[pivot][k] != z, 'singular transform'
        rows[k], rows[pivot] = rows[pivot], rows[k]
        scale = rows[k][k]; rows[k] = [x/scale for x in rows[k]]
        for i in range(4):
            if i != k:
                scale = rows[i][k]; rows[i] = [x-scale*y for x,y in zip(rows[i],rows[k])]
    return [row[4:] for row in rows]

def apply(a, p):
    return [sum(a[i][j]*p[j] for j in range(3))+a[i][3] for i in range(3)]

def residual_identity(a):
    return max(abs(a[i][j]-(1 if i==j else 0)) for i in range(4) for j in range(4))

def valid_manifest(m):
    assert set(m)=={'version','format','view_count','views'}
    assert m['version']==1 and m['format']=='xyz-f64le-v1'
    assert type(m['view_count']) is int and len(m['views'])==m['view_count'] in (2,3)
    for i,v in enumerate(m['views']):
        assert set(v)=={'id','file','points','bytes','SHA256'}
        assert v['id']==f'v{i:02d}' and v['file']==f'v{i:02d}.xyz64'
        assert type(v['points']) is int and 0<v['points']<1000000
        assert v['bytes']==v['points']*24
        assert len(v['SHA256'])==64 and all(c in '0123456789abcdef' for c in v['SHA256'])

def synthetic():
    F=fractions.Fraction
    arrays=[[[0,-1,0,3],[1,0,0,-2],[0,0,1,1],[0,0,0,1]],
            [[-1,0,0,-1],[0,1,0,4],[0,0,-1,2],[0,0,0,1]],
            [[1,0,0,2],[0,0,-1,1],[0,1,0,-3],[0,0,0,1]]]
    t=[[[F(x) for x in row] for row in a] for a in arrays]
    q=[inverse(a) for a in t]
    points=[[F(x) for x in p] for p in ((0,0,0),(2,0,0),(0,3,0),(0,0,5))]
    checks=[]
    for i in range(3):
        assert residual_identity(mm(q[i],t[i]))==0 and residual_identity(mm(t[i],q[i]))==0
        for p in points:
            x=apply(t[i],p); assert apply(q[i],x)==p
            row=[sum((p+[F(1)])[k]*t[i][j][k] for k in range(4)) for j in range(3)]
            assert row==x
        checks.append(f'view{i}:exact inverse/roundtrip/row-column')
    g=[[F(x) for x in row] for row in [[0,0,1,7],[0,1,0,-5],[-1,0,0,2],[0,0,0,1]]]
    left=[mm(g,a) for a in q]; right=[mm(a,g) for a in q]
    for i in range(3):
        for j in range(3): assert mm(inverse(left[i]),left[j])==mm(inverse(q[i]),q[j])
    assert any(mm(inverse(right[i]),right[j])!=mm(inverse(q[i]),q[j]) for i,j in ((0,1),(1,2),(0,2)))
    assert any(apply(t[0],apply(t[0],p))!=p for p in points)  # wrong inverse
    assert any([sum((p+[F(1)])[k]*t[0][k][j] for k in range(4)) for j in range(3)]!=apply(t[0],p) for p in points)
    assert any(apply(q[1],apply(t[0],p))!=p for p in points)
    perm=[2,0,1]
    for i in perm:
        for p in points: assert apply(q[i],apply(t[i],p))==p
    good={'version':1,'format':'xyz-f64le-v1','view_count':2,
          'views':[dict(id=f'v{i:02d}',file=f'v{i:02d}.xyz64',points=4,bytes=96,SHA256='0'*64) for i in range(2)]}
    valid_manifest(good)
    negatives=[]
    for label, mutate in [('reference_key',lambda m:m.update(reference='T')),
                           ('private_path',lambda m:m['views'][0].update(file='../private/REFERENCE.json')),
                           ('unknown_view_key',lambda m:m['views'][0].update(transform=[])),
                           ('wrong_size',lambda m:m['views'][0].update(bytes=95)),
                           ('wrong_view_order',lambda m:m['views'].reverse())]:
        bad=json.loads(json.dumps(good));mutate(bad)
        try: valid_manifest(bad)
        except AssertionError: negatives.append(label)
        else: raise AssertionError('negative admitted:'+label)
    result=dict(status='EXACT_SYNTHETIC_CONTRACT_PASS',positive_checks=checks,
                exact_relative_left_gauge=True,permutation_invariant_when_paired=True,
                rejected_semantic_negatives=['wrong_inverse','wrong_row_form','right_gauge','wrong_view_reference_order'],
                rejected_schema_negatives=negatives,actual_data_read=False)
    save(BASE/'SYNTHETIC.json',result)
    save(BASE/'SYNTHETIC_SEAL.json',{'SHA256':sha(BASE/'SYNTHETIC.json')})

def source_records():
    freeze=json.loads((BASE/'SOURCE_FREEZE.json').read_text())+json.loads((BASE/'SUPPLEMENTAL_SOURCE_FREEZE.json').read_text())
    for r in freeze:
        p=pathlib.Path(r['Linux_path']);assert p.stat().st_size==r['bytes'] and sha(p)==r['SHA256']
    seal=json.loads((BASE/'SYNTHETIC_SEAL.json').read_text())
    assert sha(BASE/'SYNTHETIC.json')==seal['SHA256']
    assert json.loads((BASE/'SYNTHETIC.json').read_text())['status']=='EXACT_SYNTHETIC_CONTRACT_PASS'
    plan=json.loads((B1/'PACKAGE_PLAN.json').read_text())
    admitted=json.loads((B1/'transfer-01/ADMITTED.json').read_text())
    paths={r['path']:B1/'transfer-01'/r['body_file'] for r in admitted['files']}
    records=[]
    with paths['regx_multiview_samples_v2.jsonl'].open() as f:
        for n,line in enumerate(f,1):
            obj=json.loads(line,parse_float=str,parse_int=str)
            if obj['scene']==plan['scene']: records.append((n,obj))
    assert [n for n,_ in records]==[913,914]
    assert [len(o['inputs']) for _,o in records]==[2,3]
    return paths,records

def read_world(path):
    with path.open('rb') as f:
        header=[]
        while True:
            s=f.readline(1024).decode('ascii').strip();header.append(s)
            assert len(header)<20
            if s=='end_header':break
        assert header[:3]==['ply','format binary_little_endian 1.0','comment Created by Open3D']
        assert header[4:]==['property double x','property double y','property double z','end_header']
        n=int(header[3].split()[-1]);data=f.read()
    assert len(data)==n*24
    points=list(struct.iter_unpack('<ddd',data));assert all(math.isfinite(v) for p in points for v in p)
    return points

def check_transform(tokens):
    t=[[D(x) for x in row] for row in tokens]
    assert len(t)==4 and all(len(r)==4 for r in t)
    assert all(x.is_finite() for row in t for x in row)
    assert t[3]==[D(0),D(0),D(0),D(1)]
    ortho=max(abs(sum(t[k][i]*t[k][j] for k in range(3))-(1 if i==j else 0)) for i in range(3) for j in range(3))
    det=t[0][0]*(t[1][1]*t[2][2]-t[1][2]*t[2][1])-t[0][1]*(t[1][0]*t[2][2]-t[1][2]*t[2][0])+t[0][2]*(t[1][0]*t[2][1]-t[1][1]*t[2][0])
    assert ortho<=D('1e-10') and abs(det-1)<=D('1e-10')
    q=inverse(t)
    residual=max(residual_identity(mm(t,q)),residual_identity(mm(q,t)))
    assert residual<=D('1e-40')
    return t,q,dict(orthogonality=str(ortho),determinant_minus_one=str(det-1),inverse_residual=str(residual))

def build():
    paths,records=source_records();worlds={}
    private=[];index=[];counts=[]
    for case,(line,obj) in enumerate(records):
        caseid=f'case-{case:03d}';views=[];refs=[]
        for i,v in enumerate(obj['inputs']):
            name=v['point_cloud_file'];source=paths['OutdoorScan/paris_02/'+name]
            if name not in worlds:worlds[name]=read_world(source)
            world=worlds[name];td,qd,checks=check_transform(v['transformation_matrix'])
            tf=[[float(x) for x in row] for row in td]
            data=bytearray()
            for p in world:
                x=apply(tf,p);assert all(math.isfinite(z) for z in x)
                data.extend(struct.pack('<ddd',*x))
            target=BASE/'inputs'/caseid/f'v{i:02d}.xyz64';save(target,bytes(data),raw=True)
            views.append(dict(id=f'v{i:02d}',file=target.name,points=len(world),bytes=len(data),SHA256=sha(target)))
            refs.append(dict(id=f'v{i:02d}',source_file=str(source.relative_to(ROOT)),source_SHA256=sha(source),
                source_name=name,world_to_view_decimal=[[str(x) for x in row] for row in td],
                view_to_world_decimal=[[str(x) for x in row] for row in qd],legal_checks=checks))
        manifest=dict(version=1,format='xyz-f64le-v1',view_count=len(views),views=views)
        valid_manifest(manifest);save(BASE/'inputs'/caseid/'manifest.json',manifest)
        private.append(dict(case=caseid,original_JSONL_line=line,views=refs))
        index.append(f'{caseid}/manifest.json');counts.append(sum(v['points'] for v in views))
    save(BASE/'inputs/INDEX.json',{'version':1,'cases':index})
    files={str(p.relative_to(BASE/'inputs')):dict(bytes=p.stat().st_size,SHA256=sha(p)) for p in sorted((BASE/'inputs').rglob('*')) if p.is_file()}
    save(BASE/'INPUT_SEAL.json',{'files':files,'all_public_bytes':sum(r['bytes'] for r in files.values())})
    save(BASE/'private/REFERENCE.json',{'role':'constructor/evaluator only; not an OS access-control boundary','cases':private})
    save(BASE/'PRIVATE_REFERENCE_SEAL.json',{'SHA256':sha(BASE/'private/REFERENCE.json')})
    save(BASE/'BUILD.json',dict(status='ALL_SELECTED_INPUTS_CONSTRUCTED_AND_SEALED',case_view_counts=[2,3],
        case_point_counts=counts,source_world_files=3,no_sampling=True,no_normalization=True,
        physical_alignment_authenticated=False,canonical_batch_reproduced=False,registration_metrics=False))

def consume(public_root):
    public_root=pathlib.Path(public_root).resolve();access=[]
    def read(relative):
        p=public_root/relative
        assert not p.is_symlink() and p.resolve().is_relative_to(public_root)
        assert all(not (public_root/part).is_symlink() for part in pathlib.Path(relative).parents if str(part)!='.')
        access.append(relative);return p.read_bytes()
    index=json.loads(read('INDEX.json'));assert set(index)=={'version','cases'} and index['version']==1
    assert index['cases']==['case-000/manifest.json','case-001/manifest.json']
    counts=[]
    for rel in index['cases']:
        m=json.loads(read(rel));valid_manifest(m);n=0
        for v in m['views']:
            data=read(str(pathlib.PurePosixPath(rel).parent/v['file']))
            assert len(data)==v['bytes'] and hashlib.sha256(data).hexdigest()==v['SHA256']
            assert all(math.isfinite(x) for p in struct.iter_unpack('<ddd',data) for x in p)
            n+=v['points']
        counts.append(n)
    save(BASE/'CONSUMER.json',dict(status='PUBLIC_SCHEMA_READER_PASS',requested_public_files=access,
        case_point_counts=counts,model=False,OS_sandbox=False,reference_files_requested=False))

def main():
    stage=sys.argv[1];assert stage in ('synthetic','build','consume')
    previous=sum(json.loads(p.read_text())['wall_seconds'] for p in BASE.glob('*/exit.json'))+json.loads((BASE/'PRESTART_ACCOUNTING.json').read_text())['enclosing_seconds']
    remaining=900-previous
    assert remaining>0
    signal.alarm(max(1,int(remaining)))
    error=None
    try:
        if stage=='synthetic':synthetic()
        elif stage=='build':build()
        else:
            assert len(sys.argv)==3
            consume(sys.argv[2])
        assert previous+time.monotonic()-START<900
        assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024<=536870912
        print(json.dumps(dict(stage=stage,success=True,no_model_solver=True)))
    except BaseException:
        error=traceback.format_exc();print(error,flush=True)
    finally:
        save(BASE/f'{stage}_child_exit.json',dict(success=error is None,error=error,child_seconds=time.monotonic()-START,
             maxrss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,GPU=0,registration_model_solver=0))
    if error:raise SystemExit(1)

if __name__=='__main__':main()
