"""Independent stdlib delivery hashes, source identity and freeze receipts."""
import ast,datetime as dt,hashlib,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent;DAY=ROOT.parent;REPO=ROOT.parents[3];START=time.monotonic()
NAMES=('feature-candidate-01','checkpoint-binding-01','checkpoint-archive-01','checkpoint-structure-01','tensor-transfer-01','public-reader-01','singleton-layout-01','inference-semantics-01')
def write(name,value):
    with (ROOT/name).open('x',encoding='utf-8') as f:json.dump(value,f,indent=2)
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest().upper()
ok=False;error=None
try:
    old=json.loads((DAY/'continuation-01/PAYLOAD_MANIFEST.json').read_text())
    for row in old:
        p=Path(row['path']);assert p.stat().st_size==row['bytes'] and sha(p)==row['sha256']
    costs=json.loads((DAY/'continuation-02/PRIOR_CLOSED_COSTS.json').read_text())
    for name,row in costs.items():assert sha(DAY/name/'COSTS_FINAL.json')==row['sha256']
    code=json.loads((DAY/'real-interface-01/CODE_BINDINGS.json').read_text())
    for row in code:assert sha(Path(row['path']))==row['sha256']
    public=json.loads((DAY/'real-interface-01/INPUT_BINDINGS.json').read_text())
    for row in public['public_files']+public['weights']:
        p=Path(row['path']);assert p.stat().st_size==row['bytes'] and sha(p)==row['sha256']
    agents=(REPO/'AGENTS.md').read_bytes();assert agents.endswith((DAY/'continuation-02/AGENTS.before_additive_pointer.md').read_bytes())
    freezes=[];receipts=[];manifest=[];jsons=0;python=0
    for name in NAMES:
        folder=DAY/name;cost=json.loads((folder/'COSTS_FINAL.json').read_text());assert cost['elapsed_seconds']<cost['cap_seconds']
        receipts.append(dict(scope=name,cost_receipt=cost,scientific_success_not_inferred_from_budget=True))
        if (folder/'run01/SOURCE_FREEZE.json').exists():
            freeze=json.loads((folder/'run01/SOURCE_FREEZE.json').read_text())
            for leaf,expected in freeze['files'].items():assert sha(folder/'runtime'/leaf)==expected
            if 'protocol_sha256' in freeze:assert sha(folder/'PROTOCOL.md')==freeze['protocol_sha256']
            if 'binding_files' in freeze:
                for leaf,expected in freeze['binding_files'].items():assert sha(folder/leaf)==expected
            freezes.append(dict(scope=name,active_runtime_files=len(freeze['files']),matches=True))
        elif (folder/'SOURCE_FREEZE.json').exists():
            freeze=json.loads((folder/'SOURCE_FREEZE.json').read_text());bound=freeze.get('files',freeze)
            for leaf,expected in bound.items():assert sha(folder/leaf)==expected
            freezes.append(dict(scope=name,root_frozen_files=len(bound),matches=True))
        if (folder/'METADATA_SOURCE_FREEZE.json').exists():
            for leaf,expected in json.loads((folder/'METADATA_SOURCE_FREEZE.json').read_text()).items():assert sha(folder/leaf)==expected
        for p in sorted(folder.rglob('*')):
            if not p.is_file():continue
            before=p.stat();digest=sha(p);after=p.stat();assert (before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns)
            manifest.append(dict(path=str(p.relative_to(REPO)).replace('\\','/'),bytes=before.st_size,sha256=digest))
            if 'fixtures' not in p.parts and p.suffix=='.json':json.loads(p.read_text(encoding='utf-8-sig'));jsons+=1
            if p.suffix=='.py':ast.parse(p.read_bytes());python+=1
    # Exact conclusion/counter checks, separate from receipt time gates.
    fc=json.loads((DAY/'feature-candidate-01/run01/numeric/RESULTS.json').read_text());assert fc['control_count']==23
    assert sum(r.get('original_secondary_error',False) for r in fc['controls'])==3
    cb=json.loads((DAY/'checkpoint-binding-01/run01/authenticate/worker_exit.json').read_text());assert not cb['success'] and cb['counters']['backend_constructor_attempts']==0
    tt=json.loads((DAY/'tensor-transfer-01/run01/transfer/worker_exit.json').read_text());assert not tt['success'] and tt['counters']['forward_attempts']==0 and tt['counters']['loaded_state_tensors']==344
    pr=json.loads((DAY/'public-reader-01/public/RESULTS.json').read_text());assert pr['receipt']['point_occurrences']==56557 and pr['model_calls']==0
    is1=json.loads((DAY/'inference-semantics-01/run01/synthetic/RESULTS.json').read_text());assert is1['count']==43 and is1['actual_neural_model_calls']==0
    write('SEALED_NEW_PAYLOAD.json',manifest)
    write('CHECKS.json',dict(passed=True,utc=dt.datetime.now(dt.timezone.utc).isoformat(),old_payload_entries=len(old),old_closed_costs_unchanged=len(costs),current_source_files=len(code),weights_unchanged=len(public['weights']),public_files_unchanged=len(public['public_files']),new_manifest_entries=len(manifest),new_manifest_bytes=sum(r['bytes'] for r in manifest),JSON_receipts_parsed=jsons,Python_files_AST_parsed=python,active_freezes=freezes,closed_scope_costs=receipts,AGENTS_old_suffix_preserved=True,FC1_secondary_error_count=3,CB1_and_TT1_failures_preserved=True,all_eight_new_time_budgets_pass=True,real_RAP_inference_calls=0,physical_efficacy_admitted=False,numeric_imports=False))
    assert not any(k in sys.modules for k in ('torch','numpy'))
    ok=True
except BaseException as caught:
    error=repr(caught)
    import traceback
    write('FAILURE.json',dict(error=error,traceback=traceback.format_exc()));raise
finally:write('worker_exit.json',dict(success=ok,error=error,elapsed_seconds=time.monotonic()-START))
