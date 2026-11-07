"""RBA0 stdlib closure; no upstream issue or scientific execution."""
import json
from pathlib import Path
import release_backend_attribution as p

BASE=p.BASE


def save(name,value):
    with (BASE/name).open('x',encoding='utf-8') as out:json.dump(value,out,indent=2);out.write('\n')


def text(name,body):
    with (BASE/name).open('x',encoding='utf-8') as out:out.write(body)


def main():
    f=p.verify();v=p.read(BASE/'validation.json');assert v['passed']
    attempts=[]
    for stage in ('freeze','audit','validate'):
        d=p.SUP/stage;e=p.read(d/'exit.json');c=p.read(d/'child_exit.json');l=p.read(d/'launch.json')
        h=[json.loads(line) for line in (d/'host_memory.jsonl').read_text().splitlines()]
        assert len(h)==e['host_memory_observations'] and h
        assert l['headroom_before_bytes']>=12*2**30 and min(r['headroom_bytes'] for r in h)>=4*2**30
        assert e['exit_code']==0 and c['success'] and c['full_resource_capture']
        assert c['peak_RSS_bytes']<=128*2**20 and c['peak_GPU_allocated_bytes']==c['peak_GPU_reserved_bytes']==0
        attempts.append(dict(stage=stage,Windows_seconds=e['wall_seconds'],Linux_child_seconds=c['wall_seconds'],
            Linux_RSS_bytes=c['peak_RSS_bytes'],exit_code=0,host_observations=len(h)))
    windows=sum(r['Windows_seconds'] for r in attempts);linux=sum(r['Linux_child_seconds'] for r in attempts)
    assert windows<=300
    resource=dict(attempts=attempts,attempt_count=3,successes=3,failures=0,
        total_Windows_seconds=windows,total_Linux_child_seconds=linux,
        maximum_Linux_RSS_bytes=max(r['Linux_RSS_bytes'] for r in attempts),GPU_bytes=0,
        time_includes_startup_imports=True,ordinary_preparation_and_closure_RSS='UNKNOWN',
        logging_retries=0,all_expected_child_and_Windows_exit_receipts_present=True,old_gaps_unchanged=True)
    save('RESOURCE_AUDIT.json',resource)
    save('CHECKS.json',dict(passed=True,independent_validation=v,all_frozen_identities_match=True,
        old_native_gate_values_not_amended=True,all_ten_retained_markers_preserved=True,
        no_upstream_runtime_equivalence_bug_or_unique_cause_claim=True,no_new_model_arrays_or_external_message=True))
    save('FINAL_IDENTITY_CHECK.json',dict(frozen_identities=len(f['files']),all_match=True,repositories=p.s.repositories()))
    status='VALIDATED_LOCAL_SDPA_RELEASE_ATTRIBUTION_BOUNDARY_COMPLETE'
    save('STATUS.json',dict(status=status,scientific_goal_complete=False,old_native_failures_unrepaired=True,
        upstream_runtime_tested=False,external_issue_sent=False))
    text('REPORT.md',f'''# RBA0 Release And Backend Attribution

Status: {status}.51 frozen identities; four historical scopes,8pair records and
48distinct saved direction rows independently reconciled. See attribution.json
and MAINTAINER_REVIEW_BRIEF.md, a local artifact only, not sent externally.

All4old freezes bind the same exact local attention layer and hosted-matching
12-layer weight. Local source is PyTorch SDPA replacement, not the external
FlashAttention calls observed in author source metadata. Weight byte identity
does not establish runtime/source/gradient equivalence. Public mutable source
crawl label4months; no current immutable upstream runtime authentication.
Local unused softcap argument is documented, not a demonstrated nonzero-softcap
historical failure or unique cause. No upstream code installed or executed.

NBR02 forward/upstream exact in8pairs, P parameter gradient repeats differ.
NMR0 math repeats exact but8/12direction gates; FPC0 S/D each8/12. DTC0 shadow
12/12 is a changed fixed-prefix function, not native repair. Scalar counts only,
not new FD/arrays/model or full binary-bank revalidation. Finite precision FD
failures do not prove mathematical autograd error or identify a unique kernel.

Three CPU successes; Windows{windows:.7f}s including imports/startup,
Linux-child{linux:.9f}s/RSS{resource['maximum_Linux_RSS_bytes']}bytes/GPU0.
300s/128MiB/8MiB new scope caps pass; ordinary preparation/closure RSS UNKNOWN.
All10 retained markers, original repo states/old negative gates/09/reference/
historical gaps and exclusions remain. No new native/shadow backward/update,
fit/pose/GT, acquisition/install/source change or external communication.
Scientific goal unresolved; no release-wide bug or scientific gain inferred.
''')
    target=BASE/'source_snapshot/scripts/maintenance'/Path(__file__).name
    with target.open('xb') as out:out.write(Path(__file__).read_bytes())
    text('BOOKKEEPING.md','Stdlib closure only; ordinary preparation/closure RSS UNKNOWN.\nNo new model/array/GT/metric, installation, acquisition or external message.\n')
    (BASE/'INCOMPLETE').unlink()
    files=[dict(path=str(q.relative_to(BASE)),bytes=q.stat().st_size,sha256=p.sha(q)) for q in sorted(BASE.rglob('*')) if q.is_file()]
    save('DELIVERY_SEAL.json',dict(status=status,files=files));assert p.size()<8*2**20
    print(json.dumps(dict(status=status,deliveries=len(files),Windows_seconds=windows,Linux_child_seconds=linux,
        RSS=resource['maximum_Linux_RSS_bytes'],whole_dossier_bytes=p.size())),flush=True)


if __name__=='__main__':main()
