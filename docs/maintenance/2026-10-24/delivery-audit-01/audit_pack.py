"""Independent stdlib provenance/counter audit and local ZIP delivery."""
import ast,datetime as dt,hashlib,json,sys,time,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent;DAY=ROOT.parent;REPO=ROOT.parents[3];OLD=DAY.parent/'2026-10-23';START=time.monotonic()
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest().upper()
def write(name,value):
    with (ROOT/name).open('x') as f:json.dump(value,f,indent=2)
prior=json.loads((DAY/'continuation-01/PRIOR_CLOSED_SCOPES.json').read_text())
for row in prior['scopes']:assert sha(OLD/row['scope']/'COSTS_FINAL.json')==row['SHA256']
oldzip=json.loads((OLD/'handoff-02/ZIP_CHECKS.json').read_text());assert sha(OLD/'handoff-02/RAP_20261023_closed_scopes.zip')==oldzip['ZIP_sha256']
code=json.loads((DAY/'real-interface-02/CODE_BINDINGS.json').read_text())
for row in code:assert sha(Path(row['path']))==row['sha256']
weights=json.loads((DAY/'real-interface-02/WEIGHT_BINDINGS.json').read_text())
for row in weights:assert sha(Path(row['path']))==row['sha256']
public=REPO/'docs/maintenance/2026-10-16/regx-interface-contract-01/inputs'
for name,row in json.loads((DAY/'real-interface-02/PINNED_INPUTS.json').read_text()).items():assert (public/name).stat().st_size==row['bytes'] and sha(public/name)==row['sha256'].upper()
sources=set();costs=[];normal_json=0;ast_files=0;invalid_expected=[];freezes=[]
for name in ('tensor-transfer-02','backend-constructor-01','real-interface-02','output-contract-01'):
    folder=DAY/name;cost=json.loads((folder/'COSTS_FINAL.json').read_text());assert cost['elapsed_seconds']<cost['cap_seconds'];costs.append(dict(scope=name,sha256=sha(folder/'COSTS_FINAL.json'),receipt=cost))
    for run,runtime in [('run01','runtime'),('run02','runtime02')]:
        f=folder/run/'SOURCE_FREEZE.json'
        if not f.exists():continue
        freeze=json.loads(f.read_text())
        for leaf,expected in freeze['files'].items():assert sha(folder/runtime/leaf)==expected
        for leaf,expected in freeze.get('binding_files',{}).items():assert sha(folder/leaf)==expected
        freezes.append(dict(scope=name,run=run,frozen_files=len(freeze['files']),matches=True))
    for p in folder.rglob('*'):
        if not p.is_file():continue
        sources.add(p)
        if p.suffix=='.json':
            if name=='output-contract-01' and p.relative_to(folder).as_posix()=='run01/verify/RESULTS.json':
                try:json.loads(p.read_text())
                except json.JSONDecodeError:invalid_expected.append(str(p.relative_to(REPO)))
                else:raise AssertionError('Expected preserved failed/truncated JSON to be invalid')
            else:json.loads(p.read_text(encoding='utf-8-sig'));normal_json+=1
        if p.suffix=='.py':ast.parse(p.read_bytes());ast_files+=1
ri=DAY/'real-interface-02/run01/real';r=json.loads((ri/'RESULTS.json').read_text());assert r['passed']
assert r['counters']['RAP_calls_completed']==2 and r['counters']['descriptor_forward_completed']==5 and r['counters']['flow_forward_completed']==10 and r['counters']['ICP_calls_completed']==3 and r['counters']['private_reference_reads']==0 and r['counters']['point_occurrences_decoded']==56557
assert json.loads((ri/'CONSTRUCTOR_PARAMETERS.json').read_text())==json.loads((ri/'AFTER_OUTPUTS_PARAMETERS.json').read_text())
for case in r['cases']:
    s=json.loads((ri/case['RAP_seal']).read_text());assert sha(ri/s['file'])==s['sha256']
oc=DAY/'output-contract-01/run02/verify';v=json.loads((oc/'RESULTS.json').read_text());assert v['passed'] and v['normalization_coordinate_checks']==60000 and len(v['exports'])==5
for e in v['exports']:assert sha(oc/e['file'])==e['sha256']
assert len(invalid_expected)==1
assert (REPO/'AGENTS.md').read_bytes().endswith((ROOT/'AGENTS.before_result_pointer.md').read_bytes())
sources.update(p for p in (DAY/'continuation-01').iterdir() if p.is_file() and p.name not in ('CURRENT_ACCOUNT.json','ACCOUNT_STOP.json','OBSERVATION_STOP.json'))
sources.update((REPO/'AGENTS.md',DAY/'PHASE_RECORD.md'))
def package(filename,paths,kind):
    manifest=[]
    for p in sorted(paths):
        assert p.resolve().is_relative_to(REPO.resolve()) and not p.is_symlink()
        manifest.append(dict(path=p.relative_to(REPO).as_posix(),bytes=p.stat().st_size,sha256=sha(p)))
    assert sum(x['bytes'] for x in manifest)<16*2**20
    meta=dict(kind=kind,created_utc=dt.datetime.now(dt.timezone.utc).isoformat(),files=manifest,actual_quota_exhaustion_claim=False,physical_efficacy_claim=False)
    raw=json.dumps(meta,indent=2).encode();target=ROOT/filename
    with zipfile.ZipFile(target,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        z.writestr('_MANIFEST.json',raw)
        for row in manifest:z.write(REPO/row['path'],row['path'])
    with zipfile.ZipFile(target) as z:
        expected={'_MANIFEST.json',*(x['path'] for x in manifest)};assert len(z.namelist())==len(expected) and set(z.namelist())==expected
        assert z.read('_MANIFEST.json')==raw
        for row in manifest:
            h=hashlib.sha256();size=0
            with z.open(row['path']) as f:
                for b in iter(lambda:f.read(1024*1024),b''):h.update(b);size+=len(b)
            assert size==row['bytes'] and h.hexdigest().upper()==row['sha256']
    write(filename+'.manifest.json',meta)
    return dict(file=filename,members=len(manifest)+1,source_files=len(manifest),source_bytes=sum(x['bytes'] for x in manifest),ZIP_bytes=target.stat().st_size,sha256=sha(target),all_CRC_SHA_match=True)
full=package('RAP_public_functional_20261024.zip',sources,'PRE_BOUNDARY_CLOSED_FUNCTIONAL_EVIDENCE')
pose=package('RAP_5_common_frame_matrices_20261024.zip',{oc/e['file'] for e in v['exports']},'FIVE_ESTIMATED_ORIGINAL_VIEW_TO_COMMON_MATRICES_INPUT_UNITS_NOT_INDEPENDENTLY_AUTHENTICATED')
assert sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file())<8*2**20 and not any(k in sys.modules for k in ('numpy','torch'))
write('CHECKS.json',dict(passed=True,old_costs_unchanged=15,old_ZIP_unchanged=True,source_files_unchanged=len(code),weights_unchanged=2,public_files_unchanged=8,normal_JSON_parsed=normal_json,Python_AST_parsed=ast_files,preserved_invalid_JSON=invalid_expected,freezes=freezes,closed_costs=costs,RI2_counters=r['counters'],OC1_checks=60000,five_existing_matrix_exports=True,AGENTS_previous_suffix_preserved=True,packages=[full,pose],numeric_imports=False,physical_efficacy_admitted=False,elapsed_seconds=time.monotonic()-START))
print(json.dumps(dict(passed=True,packages=[full,pose],normal_JSON=normal_json,preserved_failed_JSON=1),indent=2))
