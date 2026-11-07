"""C0 independent Decimal scalar audit. Does not import builder implementation."""
import decimal
import hashlib
import json
import math
import pathlib
import resource
import signal
import struct
import time
import traceback

ROOT=pathlib.Path(__file__).resolve().parents[2]
BASE=ROOT/'docs/maintenance/2026-10-16/regx-interface-contract-01'
START=time.monotonic();decimal.getcontext().prec=50;D=decimal.Decimal
EPS=D(2)**-52
def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        while b:=f.read(65536):h.update(b)
    return h.hexdigest()
def write(name,obj):
    with (BASE/name).open('x',encoding='utf-8') as f:json.dump(obj,f,indent=2);f.write('\n')
def world_points(path):
    with path.open('rb') as f:
        n=None;header_bytes=0
        while True:
            b=f.readline(1024);header_bytes+=len(b)
            assert b and header_bytes<16384
            if b.startswith(b'element vertex '):n=int(b.split()[-1])
            if b.rstrip()==b'end_header':break
        body=f.read()
    assert n and len(body)==n*24
    # Independent explicit per-point byte offsets, not builder's iter_unpack list.
    return [tuple(D.from_float(struct.unpack_from('<d',body,24*i+8*j)[0]) for j in range(3)) for i in range(n)]
def run():
    previous=sum(json.loads(p.read_text())['wall_seconds'] for p in BASE.glob('*/exit.json'))
    assert previous<900;signal.alarm(max(1,int(900-previous)))
    for r in json.loads((BASE/'SOURCE_FREEZE.json').read_text()):
        p=pathlib.Path(r['Linux_path']);assert p.stat().st_size==r['bytes'] and digest(p)==r['SHA256']
    seal=json.loads((BASE/'INPUT_SEAL.json').read_text());actual={}
    for p in (BASE/'inputs').rglob('*'):
        if p.is_file():actual[str(p.relative_to(BASE/'inputs'))]=dict(bytes=p.stat().st_size,SHA256=digest(p))
    assert actual==seal['files'] and sum(r['bytes'] for r in actual.values())==seal['all_public_bytes']
    assert digest(BASE/'private/REFERENCE.json')==json.loads((BASE/'PRIVATE_REFERENCE_SEAL.json').read_text())['SHA256']
    refs=json.loads((BASE/'private/REFERENCE.json').read_text())
    index=json.loads((BASE/'inputs/INDEX.json').read_text());assert set(index)=={'version','cases'}
    assert index['cases']==['case-000/manifest.json','case-001/manifest.json']
    expected_access=['INDEX.json'];count_points=0;count_coords=0;max_forward=D(0);max_roundtrip=D(0);details=[]
    b1=ROOT/'docs/maintenance/2026-10-16/regx-reference-package-01'
    source_admit=json.loads((b1/'transfer-01/ADMITTED.json').read_text())
    jsonl=b1/'transfer-01'/next(r['body_file'] for r in source_admit['files'] if r['path']=='regx_multiview_samples_v2.jsonl')
    with jsonl.open() as f:
        original={i:json.loads(line,parse_float=str,parse_int=str) for i,line in enumerate(f,1) if i in (913,914)}
    worlds={}
    assert len(refs['cases'])==2
    for ci,case in enumerate(refs['cases']):
        assert case['case']==f'case-{ci:03d}' and case['original_JSONL_line']==913+ci
        record=original[913+ci];assert record['scene']=='OutdoorScan/paris_02'
        rel=index['cases'][ci];expected_access.append(rel)
        m=json.loads((BASE/'inputs'/rel).read_text())
        assert set(m)=={'version','format','view_count','views'} and m['version']==1 and m['format']=='xyz-f64le-v1'
        assert m['view_count']==len(case['views'])==len(record['inputs'])==ci+2
        for vi,(view,ref,orig) in enumerate(zip(m['views'],case['views'],record['inputs'])):
            assert set(view)=={'id','file','points','bytes','SHA256'}
            assert view['id']==ref['id']==f'v{vi:02d}' and view['file']==f'v{vi:02d}.xyz64'
            assert ref['source_name']==orig['point_cloud_file']
            source=ROOT/ref['source_file'];assert digest(source)==ref['source_SHA256']
            if str(source) not in worlds:worlds[str(source)]=world_points(source)
            w=worlds[str(source)];assert len(w)==view['points']
            t=[[D(x) for x in row] for row in ref['world_to_view_decimal']]
            q=[[D(x) for x in row] for row in ref['view_to_world_decimal']]
            assert t==[[D(x) for x in row] for row in orig['transformation_matrix']]
            assert t[3]==q[3]==[0,0,0,1]
            for a,b in ((t,q),(q,t)):
                for i in range(4):
                    for j in range(4):assert abs(sum(a[i][k]*b[k][j] for k in range(4))-(1 if i==j else 0))<=D('1e-40')
            data_path=BASE/'inputs'/case['case']/view['file'];data=data_path.read_bytes()
            expected_access.append(str(data_path.relative_to(BASE/'inputs')))
            assert len(data)==view['bytes']==24*len(w) and digest(data_path)==view['SHA256']
            for pi,p in enumerate(w):
                x=[D.from_float(struct.unpack_from('<d',data,24*pi+8*j)[0]) for j in range(3)]
                bounds=[]
                for j in range(3):
                    terms=[t[j][k]*p[k] for k in range(3)]
                    expected=terms[0]+terms[1]+terms[2]+t[j][3]
                    bound=128*EPS*(1+sum(abs(z) for z in terms)+abs(t[j][3]))
                    ratio=abs(x[j]-expected)/bound;assert ratio<=1
                    max_forward=max(max_forward,ratio);bounds.append(bound);count_coords+=1
                for j in range(3):
                    reconstructed=q[j][0]*x[0]+q[j][1]*x[1]+q[j][2]*x[2]+q[j][3]
                    bound=sum(abs(q[j][k])*bounds[k] for k in range(3))+256*EPS*(1+abs(p[j]))
                    ratio=abs(reconstructed-p[j])/bound;assert ratio<=1
                    max_roundtrip=max(max_roundtrip,ratio)
                count_points+=1
            details.append(dict(case=case['case'],view=view['id'],points=len(w)))
    consumer=json.loads((BASE/'CONSUMER.json').read_text())
    assert consumer['requested_public_files']==expected_access
    assert not consumer['reference_files_requested'] and not consumer['OS_sandbox']
    assert not any('private' in p or 'REFERENCE' in p for p in expected_access)
    assert sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file())<16*1024*1024
    assert previous+time.monotonic()-START<900
    assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024<=536870912
    write('VALIDATION.json',dict(status='VALIDATED_CUSTOM_INPUT_REFERENCE_CONTRACT_ALL_POINTS',
        all_points=count_points,forward_coordinate_comparisons=count_coords,inverse_coordinate_comparisons=count_coords,
        max_forward_error_budget_ratio=str(max_forward),max_inverse_error_budget_ratio=str(max_roundtrip),
        details=details,public_files=len(actual),consumer_read_paths=expected_access,
        all_selected_cases=True,no_builder_math_import=True,no_registration_pose_metric=True,
        physical_world_truth_authenticated=False,canonical_batch_reproduced=False,OS_access_isolation=False))
    print(json.dumps(dict(points=count_points,coordinate_checks_each=count_coords,independent=True)))
error=None
try:run()
except BaseException:error=traceback.format_exc();print(error,flush=True)
finally:
    write('validation_child_exit.json',dict(success=error is None,error=error,child_seconds=time.monotonic()-START,
        maxrss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,GPU=0,registration_model_solver=0))
if error:raise SystemExit(1)
