"""MDA0 full metadata denominator and resource closure, no further network."""
import hashlib
import json
from pathlib import Path
import re
import official_demo_metadata as p

BASE=p.BASE


def text(name,body):
    with (BASE/name).open('x',encoding='utf-8') as out:out.write(body)


def main():
    f=p.verify();v=p.read(BASE/'validation.json');assert v['passed']
    for name in ('WINDOWS_BINDING.json','ENTRY02_BINDING.json'):
        for n,r in p.read(BASE/name)['files'].items():assert p.sha(Path(n))==r['sha256'] and Path(n).stat().st_size==r['bytes']
    c=p.read(BASE/'catalog_windows.json');a=p.read(BASE/'identity_links.json');receipts=p.transfers()
    assert c['complete'] and len(c['pages'])==5 and len(c['entries'])==4577
    assert len({e['path'] for e in c['entries']})==4577
    for i,index in enumerate(c['pages']):
        receipt=receipts[index];assert receipt['admitted']
        links=re.findall(r'<([^>]+)>;\s*rel="?next"?',receipt['headers'].get('link',''))
        if i+1<len(c['pages']):assert links==[receipts[c['pages'][i+1]]['requested_url']]
        else:assert not links
    clouds=[e for e in c['entries'] if Path(e['path']).suffix in ('.ply','.pcd') and e['type']=='file']
    lfs=[e for e in clouds if e.get('lfs')];plain=[e for e in clouds if not e.get('lfs')]
    local=p.read(p.DSR/'headers_and_roles.json')['files'];sizes={r['bytes'] for r in local}
    assert len(clouds)==3243 and len(lfs)==3215 and len(plain)==28
    assert not any(e['size'] in sizes for e in plain)
    assert a['matched_local_files']==0 and len(local)==156
    assert all(len(e['lfs']['oid'])==64 and e['lfs']['size']==e['size'] for e in lfs)
    documents=[];known={e['path']:e for e in c['entries']}
    for row in a['acquired_metadata']:
        assert row['path'] in ('README.md','datasets.csv','ATTRIBUTION.md','LICENSE')
        r=receipts[row['transfer_index']];assert r['admitted']
        body=(BASE/r['body_path']).read_bytes();entry=known[row['path']]
        assert len(body)==entry['size']
        git=hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest()
        assert git==entry['oid']
        documents.append(dict(path=row['path'],bytes=len(body),Git_blob_SHA1=git,SHA256=r['SHA256']))
    coverage=dict(pinned_revision=p.REV,catalog_pages=5,catalog_entries=4577,all_paths_unique=True,
        point_files=3243,LFS_SHA256_point_files=3215,plain_Git_point_files=28,
        plain_point_files_with_any_local_size=0,local_files=156,exact_byte_matches=0,
        documents=documents,scene_metadata_or_reference_pose_files_acquired=0,
        inferred_same_geometry_or_physical_scene=False,all_history_or_training_exclusion_authenticated=False,
        decision='PINNED_REGX_HAS_NO_BYTE_IDENTICAL_EXISTING_LOCAL_DEMO_POINT_FILES')
    p.save('CATALOG_COVERAGE.json',coverage)
    attempts=[]
    for stage in ('freeze','catalog','windows','windows02','validate'):
        d=p.SUP/stage;e=p.read(d/'exit.json');child=p.read(d/'child_exit.json');launch=p.read(d/'launch.json')
        host=[json.loads(line) for line in (d/'host_memory.jsonl').read_text().splitlines()]
        assert len(host)==e['host_memory_observations'] and host
        assert launch['headroom_before_bytes']>=12*2**30 and min(r['headroom_bytes'] for r in host)>=4*2**30
        assert e['exit_code']==(1 if stage=='windows' else 0) and child['success']==(stage!='windows')
        assert child['full_resource_capture'] and child['peak_RSS_bytes']<=128*2**20
        attempts.append(dict(stage=stage,exit_code=e['exit_code'],Windows_seconds=e['wall_seconds'],
            Linux_child_seconds=child['wall_seconds'],Linux_RSS_bytes=child['peak_RSS_bytes'],host_observations=len(host)))
    windows=sum(r['Windows_seconds'] for r in attempts);linux=sum(r['Linux_child_seconds'] for r in attempts)
    assert windows<=900 and p.size()<16*2**20
    w=p.read(BASE/'windows_execution.json');assert w['native_exit_code']==0 and w['error'] is None
    assert w['final_child_OS_peak_complete'] and w['native_child_cap_pass'] and w['running_query_gaps']==0
    assert len(w['final_queries'])==2 and all(r['success'] for r in w['running_queries']+w['final_queries'])
    assert w['final_queries'][0]['peak_working_set']==w['final_queries'][1]['peak_working_set']==166621184
    assert w['observer_full_lifetime_peak']=='UNKNOWN'
    resource=dict(attempts=attempts,attempt_count=5,successes=4,retained_prestart_failures=1,
        retained_transport_failure_requests=1,total_Windows_seconds=windows,total_Linux_child_seconds=linux,
        maximum_Linux_RSS_bytes=max(r['Linux_RSS_bytes'] for r in attempts),GPU_bytes=0,
        nested_Windows_child_peak_bytes=166621184,nested_Windows_interval_enclosed_not_added_twice=True,
        Windows_observer_full_lifetime_peak='UNKNOWN',ordinary_preparation_closure_RSS='UNKNOWN',
        time_includes_startup_imports=True,all_expected_exit_receipts_present=True,logging_retries=0,
        acquired_body_bytes=1273695,owner_body_cap_bytes=4194304,remaining_body_allowance_bytes=4194304-1273695,
        all_native_or_process_tree_cap_proven=False,old_WPC0_NMQ0_gaps_repaired=False)
    assert sum(r['acquired_body_bytes'] for r in receipts)==1273695
    p.save('RESOURCE_AUDIT.json',resource)
    p.save('CHECKS.json',dict(passed=True,independent_validator=v,coverage=coverage,
        selected_documents_Git_blob_identity_matches=True,owner_body_cap_pass=True,
        Linux_RSS_and_time_caps_pass=True,native_metadata_child_peak_cap_pass=True,
        observer_lifetime_unknown_not_promoted=True,all_ten_retained_markers_preserved=True,
        scientific_goal_or_new_efficacy_complete=False))
    p.save('FINAL_IDENTITY_CHECK.json',dict(frozen_identities=len(f['files']),all_match=True,
        entry_bindings_all_match=True,repositories=p.s.repositories()))
    status='VALIDATED_BOUNDED_OFFICIAL_METADATA_NO_LOCAL_DEMO_BYTE_LINK_STOP'
    p.save('STATUS.json',dict(status=status,scientific_goal_complete=False,source_reference_link_unresolved=True,
        observer_lifetime_peak='UNKNOWN',original_transport_and_prestart_failures_retained=True))
    text('REPORT.md',f'''# MDA0 Official Metadata And Existing Demo Byte Linkage

Status: {status}.22 frozen identities plus separately frozen prospective Windows
transport/entry bindings. Owner authorized at most4MiB official metadata only.
Acquired10request receipts:9complete admitted,1retained WSL network-unreachable
with0body bytes. Shared total1273695bytes<=4194304. No point/weight download,
canonical14.2MB JSON/7.35MB JSONL acquisition, install or external message.

Fixed author repository revisionc8deb301b32bb887acd48371ae93221251a056b5.
Five chained, independently reconciled API pages4577unique entries,4308files,
264scene metadata.yaml entries,3243point files.3215point files have published
LFS SHA256/size; none match any of156local demo identities.28plain Git point
files have no length matching any local file, so they also cannot be byte
identical. This closes the complete current-revision byte comparison, not all
historical releases or equivalence after reencoding/resampling. No geometric
comparison or source reconstruction was performed.

The4small author documents README/datasets.csv/ATTRIBUTION/LICENSE were acquired
and their exact Git-blob SHA1/lengths match the pinned catalog. No scene qualifies
for reference-metadata acquisition under the byte-link rule;0scene metadata/
reference pose files acquired. No same-name/nearby-scene substitution or pose
invention. Author reference construction/current-demo linkage/training exclusion
remain unresolved. Supplied-reference engineering could be scoped only after
an exact source mapping, not by transplanting RegX truth onto these demo files.

Official [repository tree](https://huggingface.co/datasets/YuePanEdward/regx-benchmark/tree/c8deb301b32bb887acd48371ae93221251a056b5)
and [author card](https://huggingface.co/datasets/YuePanEdward/regx-benchmark)
are the metadata authority, not a surveyed physical-truth certificate. Preview
labels already exposed remain disclosed. See original raw response receipts.

Original WSL catalog transport failure retained. First Windows bridge failed
before native start on guessed runtime path; source/binding/failure/exit remain.
Separate entry02 changes5string literals(path/stage/failure/exit/binding routes),
same HTTP/cap predicates, no budget reset or scientific replay.5enclosing CPU
attempts4success/1retained prestart failure,Windows{windows:.7f}s including startup/
imports,child{linux:.9f}s/RSS{resource['maximum_Linux_RSS_bytes']}bytes/GPU0.
One nested Windows metadata child native exit0,all OS query returns retained,
final peak166621184bytes<=512MiB. Its interval is enclosed,not added twice.
Observer full-lifetime peak UNKNOWN; not an all-native/process-tree memory claim.
Original900s/128MiB Linux/16MiB dossier and4MiB network-body caps pass within
their exact scopes. Ordinary setup/closure RSS UNKNOWN,historical gaps unchanged.

No new model/native/shadow/head backward/update/fit/solver/pose metric/trajectory,
no production/default/backbone/reference/manuscript/restart/commit/Git sync.
All10 retained markers and original repositories/stops/09 unknown remain.
Scientific goal unresolved. Next precise dependency is the original author demo
archive member manifest and reference construction/version, not a full RegX
download or filename-based truth repair. No automatic further acquisition.
''')
    dest=BASE/'source_snapshot/scripts/maintenance'/Path(__file__).name
    with dest.open('xb') as out:out.write(Path(__file__).read_bytes())
    text('BOOKKEEPING.md','Stdlib closure and scalar metadata/receipt reconstruction only.\nNo additional network or point/model/pose computation. Ordinary RSS UNKNOWN.\n')
    (BASE/'INCOMPLETE').unlink()
    files=[dict(path=str(q.relative_to(BASE)),bytes=q.stat().st_size,sha256=p.sha(q)) for q in sorted(BASE.rglob('*')) if q.is_file()]
    p.save('DELIVERY_SEAL.json',dict(status=status,files=files));assert p.size()<16*2**20
    print(json.dumps(dict(status=status,deliveries=len(files),Windows_seconds=windows,Linux_child_seconds=linux,
        RSS=resource['maximum_Linux_RSS_bytes'],whole_dossier_bytes=p.size())),flush=True)


if __name__=='__main__':main()
