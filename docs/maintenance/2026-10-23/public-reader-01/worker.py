"""Synthetic adversarial controls then new candidate's public-only demonstration."""
import ast,copy,hashlib,json,math,os,stat,struct,sys,time
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
import public_reader as reader
CASE=sys.argv[1];OUT=ROOT/CASE;OUT.mkdir(exist_ok=False);START=time.monotonic()
REPO=ROOT.parents[3];PUBLIC=REPO/'docs/maintenance/2026-10-16/regx-interface-contract-01/inputs'
denied=[PUBLIC.parent/'private',REPO/'docs/maintenance/2026-10-16/regx-reference-package-01/transfer-01',REPO/'docs/maintenance/2026-10-16/regx-reference-code-01/transfer-01',REPO/'weights']
reference_attempts=[0]
def audit(event,args):
    if event=='socket.connect':raise PermissionError('PR1 network forbidden')
    if event=='open' and args and isinstance(args[0],(str,bytes)):
        p=Path(os.fsdecode(args[0])).absolute()
        if any(p==r or r in p.parents for r in denied):reference_attempts[0]+=1;raise PermissionError('PR1 private/reference/weights forbidden')
sys.addaudithook(audit)
def write(name,value):
    with (OUT/name).open('x') as f:json.dump(value,f,indent=2)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def enc(x):return json.dumps(x).encode()
ok=False;error=None
try:
    freeze=json.loads((ROOT/'SOURCE_FREEZE.json').read_text())
    for name,expected in freeze['files'].items():assert sha((ROOT/name).read_bytes()).upper()==expected
    source=REPO/'scripts/maintenance/regx_interface_contract_execution02.py'
    assert sha(source.read_bytes()).upper()==freeze['original_validation_source_sha256']
    if CASE=='synthetic':
        nodes=[n for n in ast.walk(ast.parse(source.read_bytes())) if isinstance(n,ast.FunctionDef) and n.name=='valid_manifest'];assert len(nodes)==1
        ns={};exec(compile(ast.Module(body=nodes,type_ignores=[]),str(source),'exec'),ns)
        original=ns['valid_manifest']
        points=((0.,0.,0.),(1.,2.,3.),(4.,-2.,1.),(3.,2.,-1.))
        payload=b''.join(struct.pack('<ddd',*p) for p in points)
        files={'INDEX.json':enc(dict(version=1,cases=reader.CASE_PATHS))}
        for case,n in enumerate((2,3)):
            views=[]
            for i in range(n):
                filename=f'v{i:02d}.xyz64';files[f'case-{case:03d}/'+filename]=payload
                views.append(dict(id=f'v{i:02d}',file=filename,points=4,bytes=len(payload),SHA256=sha(payload)))
            m=dict(version=1,format='xyz-f64le-v1',view_count=n,views=views)
            original(m);reader.manifest(m);files[f'case-{case:03d}/manifest.json']=enc(m)
        def fixture(label,data,catalog_mutate=None):
            path=OUT/'fixtures'/label;path.mkdir(parents=True,exist_ok=False)
            for rel,raw in data.items():
                target=path/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
            catalog={rel:dict(bytes=len(raw),sha256=sha(raw)) for rel,raw in data.items()}
            if catalog_mutate:catalog_mutate(catalog)
            return reader.load(path,catalog)
        result,receipt=fixture('valid',files)
        assert receipt['point_occurrences']==20 and receipt['case_point_counts']==[8,12] and len(receipt['public_access'])==8
        assert all(v.xyz==points for c in result for v in c.views)
        assert set(vars(result[0]))=={'case_id','views'} and set(vars(result[0].views[0]))=={'view_id','xyz'}
        controls=[dict(case='valid_two_and_three_view_exact_rows',passed=True),dict(case='original_AST_positive_contract',passed=True),dict(case='inference_API_fields_only',passed=True)]
        def mutate_manifest(label,fn):
            data=dict(files);m=json.loads(data['case-000/manifest.json']);fn(m);data['case-000/manifest.json']=enc(m);return label,data,None
        negatives=[mutate_manifest('unknown_reference',lambda m:m.update(reference=[])),mutate_manifest('view_transform',lambda m:m['views'][0].update(transform=[])),mutate_manifest('private_path',lambda m:m['views'][0].update(file='../private/REFERENCE.json')),mutate_manifest('absolute_path',lambda m:m['views'][0].update(file='C:/private/REFERENCE.json')),mutate_manifest('version_bool',lambda m:m.update(version=True)),mutate_manifest('wrong_version',lambda m:m.update(version=2)),mutate_manifest('view_count_bool',lambda m:m.update(view_count=True)),mutate_manifest('points_bool',lambda m:m['views'][0].update(points=True)),mutate_manifest('bytes_bool',lambda m:m['views'][0].update(bytes=True)),mutate_manifest('wrong_order',lambda m:m['views'].reverse()),mutate_manifest('duplicate_view_id',lambda m:m['views'][1].update(id='v00')),mutate_manifest('wrong_hash',lambda m:m['views'][0].update(SHA256='0'*64)),mutate_manifest('invalid_hash',lambda m:m['views'][0].update(SHA256='x'*64)),mutate_manifest('negative_count',lambda m:m['views'][0].update(points=-1)),mutate_manifest('huge_count',lambda m:m['views'][0].update(points=1000000)),mutate_manifest('wrong_size',lambda m:m['views'][0].update(bytes=95)),mutate_manifest('views_wrong_type',lambda m:m.update(views=None))]
        for label,raw in [('duplicate_json_key',b'{"version":1,"version":1,"cases":["case-000/manifest.json","case-001/manifest.json"]}'),('json_nan',b'{"version":NaN,"cases":[]}'),('invalid_utf8',b'\xff'),('index_private_field',enc(dict(version=1,cases=reader.CASE_PATHS,reference='private'))),('index_wrong_order',enc(dict(version=1,cases=list(reversed(reader.CASE_PATHS))))),('index_version_bool',enc(dict(version=True,cases=reader.CASE_PATHS)))]:
            data=dict(files);data['INDEX.json']=raw;negatives.append((label,data,None))
        for label,raw in [('truncated_xyz',payload[:-1]),('extra_xyz_record',payload+payload[:24]),('byte_tamper',b'\x01'+payload[1:])]:
            data=dict(files);data['case-000/v00.xyz64']=raw;negatives.append((label,data,None))
        for label,value in [('nan_xyz',math.nan),('infinite_xyz',math.inf)]:
            raw=struct.pack('<d',value)+payload[8:];data=dict(files);data['case-000/v00.xyz64']=raw
            m=json.loads(data['case-000/manifest.json']);m['views'][0]['SHA256']=sha(raw);data['case-000/manifest.json']=enc(m);negatives.append((label,data,None))
        negatives.extend([('catalog_private_path',dict(files),lambda c:c.update({'../private/REFERENCE.json':dict(bytes=1,sha256='0'*64)})),('catalog_missing',dict(files),lambda c:c.pop('INDEX.json')),('catalog_wrong_hash',dict(files),lambda c:c['case-000/v00.xyz64'].update(sha256='0'*64)),('catalog_wrong_size',dict(files),lambda c:c['case-000/v00.xyz64'].update(bytes=97))])
        for label,data,mutator in negatives:
            try:fixture(label,data,mutator)
            except (ValueError,TypeError,KeyError,struct.error):pass
            else:raise AssertionError('Invalid public input admitted:'+label)
            controls.append(dict(case='reject_'+label,passed=True))
        for label,st in [('Windows_reparse',SimpleNamespace(st_mode=stat.S_IFREG,st_file_attributes=0x400)),('POSIX_symlink',SimpleNamespace(st_mode=stat.S_IFLNK,st_file_attributes=0))]:
            try:reader.ordinary(st)
            except ValueError:pass
            else:raise AssertionError('Reparse metadata accepted')
            controls.append(dict(case='reject_'+label,passed=True,simulated_stat_only=True))
        old=json.loads(files['case-000/manifest.json']);old['version']=True;original(old)
        try:reader.manifest(old)
        except ValueError:pass
        else:raise AssertionError('Bool version accepted')
        controls.append(dict(case='strict_version_type_vs_original_equality',passed=True,original_accepts_bool_version=True,pinned_hash_still_required_in_original_real_case=True))
        assert reference_attempts[0]==0 and not any(k in sys.modules for k in ('numpy','torch'))
        write('RESULTS.json',dict(passed=True,count=len(controls),controls=controls,real_point_reads=0,private_attempts=0,original_C0_stages_invoked=0,simulated_reparse_not_OS_proof=True))
    elif CASE=='public':
        cases,receipt=reader.load(PUBLIC,json.loads((ROOT/'PINNED_INPUTS.json').read_text()))
        assert receipt['point_occurrences']==56557 and receipt['case_point_counts']==[22622,33935]
        assert len(cases)==2 and [len(c.views) for c in cases]==[2,3] and len(receipt['public_access'])==8
        assert not any(k in sys.modules for k in ('numpy','torch')) and reference_attempts[0]==0
        write('RESULTS.json',dict(passed=True,receipt=receipt,finite_coordinate_occurrences=56557*3,private_attempts=0,model_calls=0,weights_reads=0,original_C0_stages_invoked=0,physical_efficacy_claim=False,installed=False))
    else:raise ValueError('unknown_stage')
    ok=True
except BaseException as caught:
    error=repr(caught)
    import traceback
    write('FAILURE.json',dict(error=error,traceback=traceback.format_exc()));raise
finally:write('worker_exit.json',dict(success=ok,error=error,elapsed_seconds=time.monotonic()-START,private_attempts=reference_attempts[0],python_version=sys.version))
