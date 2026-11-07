"""PRI0 stdlib delivery closure; never deserializes or acquires model payloads."""
import json
from pathlib import Path
import public_release_identity_attempt02 as p

ROOT,BASE=p.ROOT,p.BASE
OLD=BASE.parent


def save(name,value):
    with (BASE/name).open('x',encoding='utf-8') as out:
        json.dump(value,out,indent=2,allow_nan=False);out.write('\n')


def text(name,body):
    with (BASE/name).open('x',encoding='utf-8') as out:out.write(body)


def main():
    frozen=p.verify();v=p.read(BASE/'validation.json');assert v['passed']
    binding=p.read(BASE/'VARIANT_BINDING.json')
    for row in binding['files']:
        assert p.sha(Path(row['original']))==row['original_SHA256']
        assert p.sha(Path(row['variant']))==row['variant_SHA256']
    assert p.sha(Path(binding['assembler']))==binding['assembler_SHA256']
    original=p.read(BASE/'ORIGINAL_AVAILABLE_SEAL.json')['files']
    for name,row in original.items():
        q=OLD/name;assert p.sha(q)==row['sha256'] and q.stat().st_size==row['bytes']
    attempts=[]
    for sup in (OLD/'supervision',BASE/'supervision'):
        for d in sorted(sup.iterdir()):
            if not d.is_dir():continue
            end=p.read(d/'exit.json');child=p.read(d/'child_exit.json');launch=p.read(d/'launch.json')
            host=[json.loads(line) for line in (d/'host_memory.jsonl').read_text().splitlines()]
            assert len(host)==end['host_memory_observations'] and host
            assert launch['headroom_before_bytes']>=12*2**30
            assert min(r['headroom_bytes'] for r in host)>=4*2**30
            assert child['full_resource_capture'] and child['peak_RSS_bytes']<=128*2**20
            assert child['peak_GPU_allocated_bytes']==child['peak_GPU_reserved_bytes']==0
            assert child['success']==(end['exit_code']==0)
            expected_failure=d==OLD/'supervision/freeze'
            assert (end['exit_code']==1) if expected_failure else (end['exit_code']==0)
            attempts.append(dict(path=str(d),exit_code=end['exit_code'],Windows_seconds=end['wall_seconds'],
                Linux_child_seconds=child['wall_seconds'],Linux_RSS_bytes=child['peak_RSS_bytes'],
                host_observations=len(host),failure_retained=expected_failure))
    assert len(attempts)==4
    windows=sum(r['Windows_seconds'] for r in attempts)
    linux=sum(r['Linux_child_seconds'] for r in attempts)
    assert windows<=300 and p.size()<8*2**20
    resource=dict(attempts=attempts,attempt_count=4,successes=3,retained_prefreeze_failures=1,
        total_Windows_seconds=windows,total_Linux_child_seconds=linux,
        maximum_Linux_RSS_bytes=max(r['Linux_RSS_bytes'] for r in attempts),GPU_bytes=0,
        Windows_time_includes_startup_imports=True,ordinary_preparation_and_closure_RSS='UNKNOWN',
        whole_original_and_attempt02_dossier_cap_bytes=8*2**20,logging_retries=0,
        expected_new_child_and_Windows_exit_receipts=4,all_expected_exit_receipts_present=True,
        historical_resource_gaps_not_repaired=True)
    save('RESOURCE_AUDIT.json',resource)
    save('FINAL_IDENTITY_CHECK.json',dict(frozen_identities=len(frozen['files']),all_match=True,
        original_available_files=len(original),original_files_all_match=True,
        repositories=p.s.repositories(),all_nine_old_markers_preserved=True))
    save('CHECKS.json',dict(passed=True,independent_validator=v,
        frozen_source_predicates_unchanged_except_documented_layout_route_accounting=True,
        local_inventory_complete=True,all_attempts_counted=True,
        old_source_failure_partial_outputs_preserved=True,new_model_or_GT_or_pose_calls=0,
        remote_binary_retrieval=False,remote_rounded_size_not_exact_size_claim=True,
        training_membership_and_original_native_repair_not_established=True))
    status='VALIDATED_AUTHOR_LINKED_PUBLIC_WEIGHT_BYTE_IDENTITIES_COMPLETE'
    save('STATUS.json',dict(status=status,scientific_goal_complete=False,
        original_failure_retained=True,training_membership='UNKNOWN',native_backward='OLD_FAILURES_UNCHANGED'))
    text('REPORT.md',f'''# PRI0 Public Release Identity

Status: {status}.

All3 regular files in local weights/ match the SHA256 displayed on author-linked
hosted file metadata; local total686394961 bytes. Driver and independent64KiB
validator each checked all3 files, not a chosen subset. See identity_audit.json.

The official [README](https://raw.githubusercontent.com/PRBonn/RAP/main/README.md)
links the [author model card](https://huggingface.co/YuePanEdward/RAP), which links
back to official code. Metadata pages for
[10-layer](https://huggingface.co/YuePanEdward/RAP/blob/main/rap_model_10.ckpt),
[12-layer](https://huggingface.co/YuePanEdward/RAP/blob/main/rap_model_12.ckpt), and
[miniSpinNet](https://huggingface.co/YuePanEdward/RAP/blob/main/mini_spinnet_t.pth)
provide the comparison SHA values. Public metadata trust and crawl/cache limits
are explicit; no remote binary was downloaded or freshly hashed. Rounded public
display sizes were not compared as exact byte lengths.

This resolves hosted-file byte identity only. Original acquisition receipt,
training membership/site exclusion, exact raw source authentication, physical
truth, strict tensor loading and numerical efficacy remain separate. No torch,
model forward/backward/update/solver/fit/pose metric or new dataset acquisition.
The public extra10_ns checkpoint is absent and was not acquired or substituted.
Official current training-data curation TODO remains unresolved; removing an old
training-code TODO does not authenticate complete training implementation.

Original prefreeze snapshot basename collision/source/partial outputs/full
failure receipts remain bound in ORIGINAL_AVAILABLE_SEAL. Separate attempt02
changes only routing, snapshot path layout, evidence binding and combined
accounting, not hash/comparison predicates. Four enclosing attempts:3success,
1retained failure; Windows{windows:.7f}s including startup/imports,
Linux-child{linux:.9f}s; RSS{resource['maximum_Linux_RSS_bytes']}bytes/GPU0.
All share original300s/128MiB/8MiB caps. Ordinary preparation/closure RSS UNKNOWN.
All9 old markers, original repository HEADs/branches/two-nine tracked dirty sets,
retired families,09 unknown, official reference and old resource gaps persist.

RegX documentation was opened, including automatic viewer preview labels and
transform/overlap values. It is documentation exposure, not untouched independent
confirmation. No sample manifest/point payload was acquired or evaluated.
Next distinct work may examine provenance/task roles of existing local demo
files, not reopen old residual/head/fit/archive families or adopt toy supervisors.
''')
    snap=BASE/'source_snapshot/scripts/maintenance'
    for src in (Path(__file__),Path(binding['assembler'])):
        with (snap/src.name).open('xb') as out:out.write(src.read_bytes())
    text('BOOKKEEPING.md','Closure is stdlib read-only reconciliation plus new exclusive evidence writes.\nOrdinary setup/closure RSS is UNKNOWN; no model/GT/pose payload executes.\n')
    (BASE/'INCOMPLETE').unlink()
    files=[dict(path=str(q.relative_to(BASE)),bytes=q.stat().st_size,sha256=p.sha(q))
           for q in sorted(BASE.rglob('*')) if q.is_file()]
    save('DELIVERY_SEAL.json',dict(status=status,files=files))
    assert p.size()<8*2**20
    print(json.dumps(dict(status=status,deliveries=len(files),frozen_identities=len(frozen['files']),
        original_files=len(original),Windows_seconds=windows,Linux_child_seconds=linux,
        RSS=resource['maximum_Linux_RSS_bytes'],whole_dossier_bytes=p.size())),flush=True)


if __name__=='__main__':main()
