"""APL0 independent stdlib tree/stat/byte/reservation reconciliation."""
import json,os
from pathlib import Path
import artifact_payload_ledger as r
def independent_files(root):
    rows=[]
    for directory,dirs,files in os.walk(root):
        for name in sorted(files):
            q=Path(directory)/name;rows.append(dict(path=str(q.relative_to(root)),bytes=os.stat(q).st_size,sha256=r.sha(q)))
    return rows
def validate():
    r.verify();m=r.read(r.BASE/'measurements.json');expected={'exact_success':(7,7,True),'short_write':(8,3,True),'duplicate_refusal':(8,4,True),'budget_refusal':(4,4,True),'path_refusal':(0,0,True),'two_retained_failures':(18,9,True),'untracked_external_negative':(4,16,False)};checks=[]
    assert {x['name'] for x in m['fixtures']}==set(expected)
    for row in m['fixtures']:
        files=independent_files(r.BASE/'fixtures'/row['name']);actual=sum(x['bytes'] for x in files);reserved=sum(x['reservation'] for x in row['events']);R,A,U=expected[row['name']];assert actual==row['actual_bytes']==A and reserved==row['reserved']==R and (reserved>=actual)==row['payload_upper_bound']==U
        running=0
        for event in row['events']:running+=event['reservation'];assert event['reserved_after']==running and running<=row['cap']
        checks.append(dict(name=row['name'],passed=True,reserved=reserved,actual_bytes=actual,all_files=files,upper_bound_applies=U))
    observed=independent_files(r.SOURCE);f=r.read(r.BASE/'freeze.json');source={str(Path(x['path']).relative_to(r.SOURCE)):x for x in f['source_corpus']};assert len(observed)==len(source)
    for x in observed:assert x['path'] in source and x['bytes']==source[x['path']]['bytes'] and x['sha256']==source[x['path']]['sha256']
    total=sum(x['bytes'] for x in observed);assert total==m['source_corpus_bytes']
    for run in m['repetitions']:assert run['complete_filesystem_census_bytes']==run['known_length_sum_bytes']==total and run['complete_filesystem_census_seconds']>0 and run['known_length_sum_seconds']>0
    assert len(m['repetitions'])==3 and m['external_untracked_counterexample_detected'] and m['payload_only_not_whole_dossier_cap_proof']
    r.verify();r.save(r.BASE/'validation.json',dict(passed=True,decision='EXCLUSIVE_PAYLOAD_UPPER_BOUND_VALID_EXTERNAL_WRITES_REQUIRE_SEPARATE_RECONCILIATION',fixtures=checks,independent_source_files=len(observed),independent_source_bytes=total,all_source_hashes_and_lengths_match=True,filesystem_and_metadata_sums_exact=True,external_untracked_negative_detected=True,whole_new_dossier_cap_safety_not_proven=True,archive_retry_or_codec_or_model_GT_calls=0,performance_scope='observer sums only; not end-to-end archive speedup'))
    print('APL0 independent reservation/tree/hash reconciliation passes',len(observed),'source files',flush=True)
