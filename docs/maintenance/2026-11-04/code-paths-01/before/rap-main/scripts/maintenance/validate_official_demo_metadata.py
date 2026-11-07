"""Independent MDA0 metadata transport/body-cap and complete local linkage."""
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit
import physical_source_role_feasibility as s

ROOT=s.ROOT
BASE=ROOT/'docs/maintenance/2026-10-15/official-demo-metadata-01'


def read(q):return json.loads(Path(q).read_text())


def sha(q):
    h=hashlib.sha256()
    with Path(q).open('rb') as stream:
        for b in iter(lambda:stream.read(65536),b''):h.update(b)
    return h.hexdigest()


def validate():
    f=read(BASE/'freeze.json');c=read(BASE/'catalog.json');a=read(BASE/'identity_links.json')
    for n,r in f['files'].items():assert sha(n)==r['sha256'] and Path(n).stat().st_size==r['bytes']
    receipts=[read(q) for q in sorted((BASE/'transfers').glob('*.json'))]
    assert len(receipts)<=40 and [r['index'] for r in receipts]==list(range(len(receipts)))
    total=0
    for r in receipts:
        q=BASE/r['body_path'];assert sha(q)==r['SHA256'] and q.stat().st_size==r['acquired_body_bytes']
        assert r['acquired_body_bytes']<=524288;total+=r['acquired_body_bytes']
        assert total<=4194304
        for url in (r['requested_url'],r['final_url']):
            if url is not None:assert urlsplit(url).scheme=='https' and urlsplit(url).netloc=='huggingface.co'
        assert not any(term in r['requested_url'] for term in ('regx_multiview_samples','.ply','.pcd','.ckpt','.pth','.bin'))
        if r['admitted']:assert r['complete'] and r['status']==200 and r['error'] is None
    assert {q.name for q in (BASE/'payload').iterdir()}=={Path(r['body_path']).name for r in receipts}
    reconstructed=[]
    for index in c['pages']:
        r=receipts[index]
        if r['admitted']:reconstructed.extend(read(BASE/r['body_path']))
    assert reconstructed==c['entries']
    local=read(ROOT/'docs/maintenance/2026-10-15/demo-source-role-01/source-attempt-02/headers_and_roles.json')['files']
    index={}
    for e in reconstructed:
        lfs=e.get('lfs') or {};key=(lfs.get('oid') or lfs.get('sha256'),e.get('size'))
        index.setdefault(key,[]).append(e)
    expected=[]
    for r in local:
        for e in index.get((r['sha256'],r['bytes']),[]):
            expected.append((r['path'],e['path'],r['bytes'],r['sha256']))
    actual=[(r['local_path'],r['remote_path'],r['bytes'],r['SHA256']) for r in a['matches']]
    assert sorted(expected)==sorted(actual) and len(local)==a['local_denominator']==156
    assert a['matched_local_files']==len({r[0] for r in actual})
    assert a['matched_scene_parents']==sorted({str(Path(r[1]).parent) for r in actual})
    assert a['catalog_complete']==c['complete'] and a['network_body_bytes']==total
    assert not a['canonical_sample_manifests_acquired'] and not a['point_or_weight_payload_acquired']
    assert not a['independent_confirmation_admitted'] and a['numeric_coordinate_reference_pose_metric_or_model_calls']==0
    assert s.repositories()==f['repositories']
    result=dict(passed=True,frozen_identities=len(f['files']),requests=len(receipts),network_body_bytes=total,
        admitted_requests=sum(r['admitted'] for r in receipts),catalog_complete=c['complete'],
        catalog_entries=len(c['entries']),local_files=156,matched_local_files=a['matched_local_files'],
        matched_scene_parents=a['matched_scene_parents'],no_point_or_weight_payload=True,
        complete_catalog_is_required_for_global_absence_claim=True)
    with (BASE/'validation.json').open('x',encoding='utf-8') as out:json.dump(result,out,indent=2);out.write('\n')
    print(json.dumps(result),flush=True)
