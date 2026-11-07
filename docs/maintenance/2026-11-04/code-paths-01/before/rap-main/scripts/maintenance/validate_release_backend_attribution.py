"""Independent RBA0 static/scalar grouping with no model or array imports."""
import ast
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import physical_source_role_feasibility as s

ROOT=s.ROOT
BASE=ROOT/'docs/maintenance/2026-10-15/release-backend-attribution-01'
DAY=ROOT/'docs/maintenance/2026-10-13'


def read(q):return json.loads(Path(q).read_text())


def sha(q):
    h=hashlib.sha256()
    with Path(q).open('rb') as inp:
        for b in iter(lambda:inp.read(65536),b''):h.update(b)
    return h.hexdigest()


def validate():
    f=read(BASE/'freeze.json');a=read(BASE/'attribution.json')
    assert sha(BASE/'attribution.json')==read(BASE/'audit_seal.json')['sha256']
    for n,r in f['files'].items():assert sha(n)==r['sha256'] and Path(n).stat().st_size==r['bytes']
    layer=ROOT/'rectified_point_flow/flow_model/layer.py'
    fn=next(n for n in ast.walk(ast.parse(layer.read_text())) if isinstance(n,ast.FunctionDef) and n.name=='_flash_attn_varlen')
    sdpa=[n for n in ast.walk(fn) if isinstance(n,ast.Attribute) and n.attr=='scaled_dot_product_attention']
    assert len(sdpa)==1 and sha(layer)==a['local_layer_SHA256']
    assert a['weight_SHA256']=='0c5b9f20ee4dfe2345c3cd47dd0632a3d807a3da69c7653900a755cd06564200'
    for row in a['historical_identity_links']:
        old=read(DAY/f['scopes'][row['scope']]/'freeze.json')['files']
        assert old[str(layer)]==row['layer_SHA256']==a['local_layer_SHA256']
        assert old[str(ROOT/'weights/rap_model_12.ckpt')]==row['weight_SHA256']==a['weight_SHA256']
    nbr=read(DAY/f['scopes']['NBR']/'results.json')
    assert len(nbr['pairs'])==len(a['NBR_pairs'])==8
    for old,new in zip(nbr['pairs'],a['NBR_pairs']):
        assert (old['left'],old['right'])==(new['left'],new['right'])
        assert new['output_different']==old['details']['output.npz']['output']['different']==0
        assert new['upstream_different']==old['details']['output.npz']['upstream']['different']==0
        gradient=old['details']['gradients.npz']
        assert sum(r['different'] for r in gradient.values())==new['gradient_different']
        assert max(r['max_abs'] for r in gradient.values())==new['gradient_max']
    fpc=read(DAY/f['scopes']['FPC']/'validation.json');dtc=read(DAY/f['scopes']['DTC']/'validation.json')
    groups=defaultdict(list);nmr={}
    for r in fpc['directional_checks']:
        groups['FPC_'+r['condition']].append(r)
        n=r['original_NMR'];key=json.dumps([n['arm'],n['group'],n['step']])
        if key in nmr:assert nmr[key]==n
        nmr[key]=n
    groups['NMR']=list(nmr.values());groups['DTC']=dtc['directional_checks']
    assert set(groups)==set(a['direction_summary'])
    for key,rows in groups.items():
        flags=[]
        for r in rows:
            difference=abs(r['central_difference']-r['gradient_dot'])
            assert abs(difference-r['error'])<1e-10
            assert (difference<=r['bound'])==r['corroborated']
            flags.append(difference<=r['bound'])
        assert a['direction_summary'][key]==dict(total=len(flags),corroborated=flags.count(True),conjunction=all(flags))
    obs=read(BASE/'PUBLIC_SOURCE_OBSERVATION.json')
    assert obs['observed_external_flash_attn_import'] and obs['observed_external_varlen_call_sites']==2
    assert not obs['raw_bytes_hashed_or_remote_code_installed'] and not obs['immutable_upstream_commit_authenticated']
    for key in ('external_flash_attn_runtime_tested','unused_softcap_proven_historical_cause',
        'unique_numerical_cause_identified','new_external_issue_sent','upstream_current_runtime_reproduced','changed_shadow_repairs_native'):assert not a[key]
    assert a['new_native_or_shadow_model_FD_fit_pose_or_metric_calls']==0
    assert s.repositories()==f['repositories']
    result=dict(passed=True,frozen_identities=len(f['files']),historical_scopes=4,pair_records=8,
        distinct_direction_rows=48,selected_old_evidence_not_full_binary_revalidation=True,
        local_SDPA_not_upstream_FlashAttention=True,decision=a['decision'])
    with (BASE/'validation.json').open('x',encoding='utf-8') as out:json.dump(result,out,indent=2);out.write('\n')
    print(json.dumps(result),flush=True)
