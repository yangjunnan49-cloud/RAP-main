"""RBA0 static source identity and existing scalar reconciliation, no torch."""
import time
START=time.monotonic()
import ast
import json
from pathlib import Path
import resource
import signal
import sys
import traceback
import demo_source_roles as ds

s=ds.s
ROOT=s.ROOT
BASE=ROOT/'docs/maintenance/2026-10-15/release-backend-attribution-01'
SUP=BASE/'supervision'
PRI=ROOT/'docs/maintenance/2026-10-15/public-release-identity-01/identity-attempt-02'
DAY=ROOT/'docs/maintenance/2026-10-13'
SCOPES=dict(NBR='native-backward-reproducibility-02',NMR='native-math-reproducibility-01',
 FPC='native-precision-control-01',DTC='native-double-tail-control-01')
read,sha=s.read,s.sha


def size():return sum(q.stat().st_size for q in BASE.rglob('*') if q.is_file())


def save(name,value):
    body=(json.dumps(value,indent=2,allow_nan=False)+'\n').encode();assert size()+len(body)<8*2**20
    with (BASE/name).open('xb') as out:out.write(body)


def oldfiles():
    paths=[]
    for key,name in SCOPES.items():
        folder=DAY/name
        names=['freeze.json','REPORT.md','PROTOCOL.md','STATUS.json','validation.json','DELIVERY_SEAL.json']
        if key in ('NBR','NMR'):names.append('results.json')
        seal={r['path']:r for r in read(folder/'DELIVERY_SEAL.json')['files']}
        for n in names:
            q=folder/n
            if n!='DELIVERY_SEAL.json':
                assert sha(q)==seal[n]['sha256'] and q.stat().st_size==seal[n]['bytes']
            paths.append(q)
    return paths


def freeze():
    paths=oldfiles()+[ROOT/'rectified_point_flow/flow_model/layer.py',
        ROOT/'config/model/flow_model/point_cloud_dit_12.yaml',ROOT/'weights/rap_model_12.ckpt',
        Path(__file__),Path(__file__).with_name('validate_release_backend_attribution.py'),
        Path(__file__).with_name('demo_source_roles.py'),Path(__file__).with_name('physical_source_role_feasibility.py'),
        Path(__file__).with_name('invoke_mgr_supervised_wsl.ps1')]
    paths += [BASE/n for n in ('OWNER_SCOPE.md','PROTOCOL.md','PUBLIC_SOURCE_OBSERVATION.json')]
    paths += [PRI/n for n in ('PUBLIC_METADATA_OBSERVATIONS.json','identity_audit.json','validation.json','DELIVERY_SEAL.json')]
    paths += [ROOT/'docs/maintenance'/n for n in ds.MARKERS]
    paths += [ROOT/'docs/maintenance/2026-10-15/demo-source-role-01/INCOMPLETE']
    snap=BASE/'source_snapshot'
    for q in paths:
        if q.suffix in ('.py','.ps1','.yaml'):
            target=snap/q.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True)
            with target.open('xb') as out:out.write(q.read_bytes())
    save('freeze.json',dict(files={str(q):dict(bytes=q.stat().st_size,sha256=sha(q)) for q in paths},
        repositories=s.repositories(),scopes=SCOPES,only_selected_old_files_verified=True))
    save('INCOMPLETE',dict(scope='RBA0',pending='static attribution and independent validation'))
    print('RBA0 frozen',len(paths),'identities',flush=True)


def verify():
    f=read(BASE/'freeze.json')
    for n,r in f['files'].items():assert sha(Path(n))==r['sha256'] and Path(n).stat().st_size==r['bytes']
    assert s.repositories()==f['repositories'];oldfiles();return f


def counts(rows):
    for r in rows:
        assert isinstance(r['corroborated'],bool)
        assert r['corroborated']==(r['error']<=r['bound'])
        assert abs(abs(r['central_difference']-r['gradient_dot'])-r['error'])<=1e-12*max(1,r['error'])
    return dict(total=len(rows),corroborated=sum(r['corroborated'] for r in rows),conjunction=all(r['corroborated'] for r in rows))


def reconstruct():
    layer=ROOT/'rectified_point_flow/flow_model/layer.py';weight=ROOT/'weights/rap_model_12.ckpt'
    code=ast.parse(layer.read_text());fn=next(n for n in code.body if isinstance(n,ast.FunctionDef) and n.name=='_flash_attn_varlen')
    imports=[n for n in ast.walk(code) if isinstance(n,(ast.Import,ast.ImportFrom))]
    assert not any('flash_attn' in ast.unparse(n) for n in imports)
    calls=[n for n in ast.walk(fn) if isinstance(n,ast.Call)]
    sdpa=[n for n in calls if ast.unparse(n.func)=='torch.nn.functional.scaled_dot_product_attention']
    assert len(sdpa)==1
    assert not any(isinstance(n,ast.Name) and isinstance(n.ctx,ast.Load) and n.id=='softcap' for n in ast.walk(fn))
    identities=[]
    for key,name in SCOPES.items():
        f=read(DAY/name/'freeze.json')
        for q in (layer,weight):assert f['files'][str(q)]==sha(q)
        identities.append(dict(scope=key,layer_SHA256=f['files'][str(layer)],weight_SHA256=f['files'][str(weight)]))
    pri=read(PRI/'identity_audit.json');assert next(r for r in pri['files'] if r['name']==weight.name)['SHA256']==sha(weight)
    nbr=read(DAY/SCOPES['NBR']/'results.json');pairs=[]
    for row in nbr['pairs']:
        details=row['details'];g=details['gradients.npz']
        pairs.append(dict(left=row['left'],right=row['right'],output_different=details['output.npz']['output']['different'],
            upstream_different=details['output.npz']['upstream']['different'],
            gradient_different=sum(v['different'] for v in g.values()),gradient_max=max(v['max_abs'] for v in g.values())))
    fpc=read(DAY/SCOPES['FPC']/'validation.json');dtc=read(DAY/SCOPES['DTC']/'validation.json')
    groups={condition:[r for r in fpc['directional_checks'] if r['condition']==condition] for condition in ('S','D')}
    assert all(len(rows)==12 for rows in groups.values())
    nmr={}
    for row in fpc['directional_checks']:
        r=row['original_NMR'];key=(r['arm'],r['group'],r['step'])
        if key in nmr:assert r==nmr[key]
        nmr[key]=r
    assert len(nmr)==12 and len(dtc['directional_checks'])==12
    summary=dict(NMR=counts(list(nmr.values())),FPC_S=counts(groups['S']),FPC_D=counts(groups['D']),DTC=counts(dtc['directional_checks']))
    assert summary['NMR']==summary['FPC_S']==summary['FPC_D']==dict(total=12,corroborated=8,conjunction=False)
    assert summary['DTC']==dict(total=12,corroborated=12,conjunction=True)
    nmr_results=read(DAY/SCOPES['NMR']/'results.json');assert nmr_results['all_instrumented_pairs_byte_equal']
    assert not nbr['all_instrumented_pairs_byte_equal']
    environment=read(DAY/SCOPES['NBR']/'freeze.json')['packages']
    config=(ROOT/'config/model/flow_model/point_cloud_dit_12.yaml').read_text()
    return dict(decision='PUBLIC_WEIGHT_IDENTITY_DOES_NOT_AUTHENTICATE_UPSTREAM_ATTENTION_RUNTIME_OR_GRADIENT_EQUIVALENCE',
        historical_identity_links=identities,local_layer_SHA256=sha(layer),weight_SHA256=sha(weight),
        local_attention_backend='PyTorch SDPA replacement',external_flash_attn_runtime_tested=False,
        helper_softcap_argument_unused=True,config_softcap_lines=[line for line in config.splitlines() if 'softcap:' in line],
        unused_softcap_proven_historical_cause=False,NBR_pairs=pairs,NMR_all_instrumented_pairs_exact=True,
        direction_summary=summary,NMR_direction_records_source='FPC0 sealed embedded original_NMR copies, deduplicated exactly',
        historical_packages=environment,unique_numerical_cause_identified=False,
        new_native_or_shadow_model_FD_fit_pose_or_metric_calls=0,new_external_issue_sent=False,
        upstream_current_runtime_reproduced=False,changed_shadow_repairs_native=False)


def audit():
    verify();result=reconstruct();save('attribution.json',result)
    save('audit_seal.json',dict(sha256=sha(BASE/'attribution.json'),bytes=(BASE/'attribution.json').stat().st_size))
    verify();print(json.dumps(dict(decision=result['decision'],summary=result['direction_summary'])),flush=True)


def usage():return dict(wall_seconds=time.monotonic()-START,
    peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
    peak_GPU_allocated_bytes=0,peak_GPU_reserved_bytes=0,artifact_bytes=size(),new_scientific_payload_calls=0)


def run(stage):
    spent=sum(read(q)['wall_seconds'] for q in SUP.glob('*/exit.json'));assert spent<300
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('RBA0 aggregate cap')))
    signal.alarm(max(1,int(300-spent)));ok,error=False,None
    try:
        if stage=='freeze':freeze()
        elif stage=='audit':audit()
        elif stage=='validate':
            import validate_release_backend_attribution as v
            v.validate()
        else:raise ValueError(stage)
        u=usage();assert u['peak_RSS_bytes']<=128*2**20 and u['artifact_bytes']<8*2**20
        if (SUP/'host_latest.json').exists():assert read(SUP/'host_latest.json')['headroom_bytes']>=4*2**30
        ok=True
    except BaseException as ex:
        error=repr(ex);traceback.print_exc();save('FAILURE_'+stage+'.json',dict(error=error,**usage()))
    finally:
        signal.alarm(0);save('supervision/'+stage+'/child_exit.json',dict(success=ok,error=error,full_resource_capture=True,**usage()))
    if not ok:sys.exit(1)


if __name__=='__main__':run(sys.argv[1])
