"""Independent PRI0 complete inventory, 64KiB hash and claim reconstruction."""
import hashlib
import json
import os
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'docs/maintenance/2026-10-15/public-release-identity-01'


def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))


def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as stream:
        for body in iter(lambda:stream.read(65536),b''):h.update(body)
    return h.hexdigest()


def validate():
    f=read(BASE/'freeze.json');a=read(BASE/'identity_audit.json');m=read(BASE/'PUBLIC_METADATA_OBSERVATIONS.json')
    assert sha(BASE/'identity_audit.json')==read(BASE/'audit_seal.json')['sha256']
    for p,row in f['files'].items():assert sha(p)==row['sha256'] and Path(p).stat().st_size==row['bytes']
    names=sorted(entry.name for entry in os.scandir(ROOT/'weights') if entry.is_file())
    assert names==f['local_names']==sorted(r['name'] for r in m['files'])
    assert len(names)==len(a['files'])==a['complete_local_file_denominator']==3
    for name in names:
        actual=next(r for r in a['files'] if r['name']==name)
        published=next(r for r in m['files'] if r['name']==name)
        p=ROOT/'weights'/name
        assert sha(p)==actual['SHA256']==published['SHA256']
        assert len(published['SHA256'])==64 and int(published['SHA256'],16)>=0
        assert actual['local_bytes']==os.stat(p).st_size
        assert actual['public_blob']==published['blob_url']
        assert published['blob_url']=='https://huggingface.co/YuePanEdward/RAP/blob/main/'+name
        assert actual['match'] and not actual['remote_exact_size_compared']
    assert sum(r['local_bytes'] for r in a['files'])==a['total_local_bytes']
    for key in ('original_download_receipt_authenticated','strict_tensor_loading_proven_by_this_audit',
                'training_membership_authenticated','native_backward_repair_or_efficacy_established',
                'new_model_or_dataset_payload_acquired'):
        assert not a[key]
    assert a['deserialization_model_or_metric_calls']==0 and a['all_old_nine_markers_preserved']
    assert m['official_README_links_model_repository']=='https://huggingface.co/YuePanEdward/RAP'
    assert m['model_card_links_official_code']=='https://github.com/PRBonn/RAP'
    assert m['public_RegX_viewer_preview_labels_seen_during_documentation_lookup']
    result=dict(passed=True,frozen_identities=len(f['files']),local_files=3,
        total_local_bytes=a['total_local_bytes'],independent_local_hashes_match_public_receipt=True,
        independent_remote_binary_retrieval_claim=False,training_membership_still_unknown=True,
        original_native_failures_unrepaired=True,decision=a['decision'])
    with (BASE/'validation.json').open('x',encoding='utf-8') as out:
        json.dump(result,out,indent=2,allow_nan=False);out.write('\n')
    print(json.dumps(result),flush=True)
