"""Close DSR0 static roles with all attempts and retained assertion failure."""
import json
from pathlib import Path
import demo_source_roles_attempt02 as p

ROOT,BASE=p.ROOT,p.BASE
OLD=BASE.parent


def save(name,value):
    with (BASE/name).open('x',encoding='utf-8') as out:json.dump(value,out,indent=2);out.write('\n')


def text(name,body):
    with (BASE/name).open('x',encoding='utf-8') as out:out.write(body)


def main():
    f=p.verify();v=p.read(BASE/'validation.json');assert v['passed']
    b=p.read(BASE/'VARIANT_BINDING.json');assert b['exact_tuple_assertion_changes']==1
    for r in b['files']:
        assert p.sha(Path(r['original']))==r['original_SHA256'] and p.sha(Path(r['variant']))==r['variant_SHA256']
    assert p.sha(Path(b['assembler']))==b['assembler_SHA256']
    old=p.read(BASE/'ORIGINAL_AVAILABLE_SEAL.json')['files']
    for n,r in old.items():assert p.sha(OLD/n)==r['sha256'] and (OLD/n).stat().st_size==r['bytes']
    attempts=[]
    for sup in (OLD/'supervision',BASE/'supervision'):
        for d in sorted(sup.iterdir()):
            if not d.is_dir():continue
            e=p.read(d/'exit.json');c=p.read(d/'child_exit.json');l=p.read(d/'launch.json')
            host=[json.loads(line) for line in (d/'host_memory.jsonl').read_text().splitlines()]
            assert len(host)==e['host_memory_observations'] and host
            assert l['headroom_before_bytes']>=12*2**30 and min(r['headroom_bytes'] for r in host)>=4*2**30
            assert c['full_resource_capture'] and c['peak_RSS_bytes']<=128*2**20
            assert c['peak_GPU_allocated_bytes']==c['peak_GPU_reserved_bytes']==0
            fail=d==OLD/'supervision/audit'
            assert e['exit_code']==(1 if fail else 0) and c['success']==(not fail)
            attempts.append(dict(path=str(d),exit_code=e['exit_code'],Windows_seconds=e['wall_seconds'],
                Linux_child_seconds=c['wall_seconds'],Linux_RSS_bytes=c['peak_RSS_bytes'],host_observations=len(host)))
    assert len(attempts)==5
    windows=sum(r['Windows_seconds'] for r in attempts);linux=sum(r['Linux_child_seconds'] for r in attempts)
    assert windows<=300 and p.size()<8*2**20
    resource=dict(attempts=attempts,attempt_count=5,successes=4,retained_assertion_failure=1,
        total_Windows_seconds=windows,total_Linux_child_seconds=linux,
        maximum_Linux_RSS_bytes=max(r['Linux_RSS_bytes'] for r in attempts),GPU_bytes=0,
        time_includes_startup_imports=True,ordinary_preparation_and_closure_RSS='UNKNOWN',
        whole_original_and_attempt02_dossier_cap_bytes=8*2**20,logging_retries=0,
        expected_new_child_and_Windows_exit_receipts=5,all_expected_exit_receipts_present=True,
        old_gaps_unchanged=True)
    save('RESOURCE_AUDIT.json',resource)
    save('CHECKS.json',dict(passed=True,independent_validator=v,whole_namespace_reconciled=True,
        all_nine_prior_markers_and_original_DSR0_marker_preserved=True,
        original_failure_source_and_partial_evidence_preserved=True,all_attempts_counted=True,
        no_coordinate_pose_model_metric_acquisition_or_production_calls=True))
    save('FINAL_IDENTITY_CHECK.json',dict(frozen_identities=len(f['files']),all_match=True,
        original_available_files=len(old),all_match_original=True,repositories=p.s.repositories()))
    status='VALIDATED_EXISTING_DEMO_SOURCE_AND_DEFAULT_REFERENCE_ROLE_AUDIT_COMPLETE'
    save('STATUS.json',dict(status=status,scientific_goal_complete=False,
        efficacy_or_independent_confirmation_admitted=False,original_assertion_failure_retained=True))
    text('REPORT.md',f'''# DSR0 Demo Source And Default Reference Roles

Status: {status}.

Complete existing namespace:27 directories/156 point-cloud files,151PLY+5PCD,
478400579bytes.214 frozen identities; all bytes and bounded format headers
independently verified without decoding coordinates. No external reference
sidecar exists within this exact root. This is not a global absence or a claim
that PCD VIEWPOINT authenticates cross-scan truth. See headers_and_roles.json.

Default demo source selects direct lowercase .ply only:26 directories contain
PLY; lidar_scan_oxford contains5PCD only and is not admitted by that enumerator.
No automatic conversion or scene selection was performed.

Seven complete static function citations establish the default path:
demo process_point_clouds calls save_processed_sample with3positional arguments,
without its optional source pose-copy directory; demo constructs val.txt and
trainer.test uses the val dataset. The folder loader assigns input sampled pcs
to pointclouds_gt. Its non-training transform uses identity rotations, derives
centering/scaling/translation references from those coordinates, and evaluator
consumes the resulting arrays. --eval_on controls table printing, not admission
of an external reference. No new runtime metric was executed.

If supplied clouds are already aligned, these references describe their supplied
alignment; if not, this path does not independently establish the correct pose.
This audit does not establish either physical state of the demo clouds or a
loader bug. PLY/PCD headers and scene names do not authenticate author/RegX byte
linkage, measurement frames, training exclusion or physical reference quality.
Do not report these default metrics as external-truth registration accuracy.

Original source assertion omitted parentheses emitted by ast.unparse. Its
181-identity freeze/source/INCOMPLETE/audit failure/full receipts remain.
Original30available files bound; separate variant changes1tuple-text assertion
plus routes/evidence binding/aggregate accounting only. Five enclosing CPU
attempts4success/1retained failure; Windows{windows:.7f}s including imports/startup,
Linux-child{linux:.9f}s/RSS{resource['maximum_Linux_RSS_bytes']}bytes/GPU0.
All original/new attempts share300s/128MiB/8MiB caps; setup/closure RSS UNKNOWN.
All9 prior markers plus original DSR0 marker stay. No model/pose/GT/new cohort,
no old family/fit/archive retry, source/default/reference change or acquisition.
Scientific goal unresolved. See NEXT_DESIGN.md for an explicit non-run contract.
''')
    text('NEXT_DESIGN.md','''# Next Distinct Design, Not An Execution Authorization

## Evidence Before Any Different Measured Test

Use a complete, author-identified measured scene/sample manifest, per-file SHA256,
input coordinate convention and externally supplied input-to-world references,
with reference construction/quality documented. Establish whether current demo
bytes match that manifest; names alone do not. Retain all exposed labels and
unknown checkpoint training membership. RegX documentation alone supplies no
local per-file linkage. Public card preview was already exposed. Acquiring a
manifest/pose archive/point data still requires explicit owner authorization.

Minimum request: existing exact byte manifests and input-to-world transforms for
the27 already-local demo scenes, their source/archive version and provenance,
and measurement/reference construction. Request documentation first, no new
17GB dataset. A supplied reference permits reference-relative engineering,
not automatically independent physical confirmation or pretraining exclusion.

## Candidate Scientific Question

No new RAP-specific observable is justified by this role audit. Before any
candidate, write the extra measured information and falsifiable mechanism that
the exact retired matching-head/context/residual families did not already test.
Do not rename local inference residual/rigidity/confidence as new information.
The default supplied-coordinate target must not be silently reused as truth for
unposed inputs. Method selection must not use reference poses/overlap labels.

## Required Common-Input Controls

For any later multi-view proposal, freeze the full scene/sample population,
all raw point IDs and preprocessing, input transforms, random seeds, initial
poses and information visibility. Include strong raw-geometry pairwise+global
and direct-stat controls, a model-free solver, and relevant shared/separated
native controls. Graph edges/reference overlap labels are evaluator-only unless
the experiment explicitly supplies them to every method. Align one global
SE3 gauge only; do not independently align each part or fit scale to hide error.

Count preprocessing/descriptor/cache/native inference/solver/failure/fallback
and complete evaluation work, not cached head latency. If a learner is proposed,
measure actually active capacity and provide fixed-checkpoint complete fit and
evaluation predictions; no padded parameter matching. Changed numerical
functions need their own derivative/activity gates but are not efficacy.
Fix scene-level safety, metric units/normalization, all-edge success and failure
handling prospectively. No point/window replication as independent scenes.

This is DESIGN_ONLY. No crop/noise expansion of the retired congruent fixture,
old native/base/head/radius rescue, new benchmark run or download is authorized
by this document. Preserve original benchmark2026-10-11 attempt03 and09 unknown.
''')
    snap=BASE/'source_snapshot/scripts/maintenance'
    for src in (Path(__file__),Path(b['assembler'])):
        with (snap/src.name).open('xb') as out:out.write(src.read_bytes())
    text('BOOKKEEPING.md','Closure uses stdlib reconciliation and exclusive evidence writes; no coordinate/model execution.\nOrdinary preparation/closure RSS UNKNOWN; historical gaps unchanged.\n')
    (BASE/'INCOMPLETE').unlink()
    files=[dict(path=str(q.relative_to(BASE)),bytes=q.stat().st_size,sha256=p.sha(q)) for q in sorted(BASE.rglob('*')) if q.is_file()]
    save('DELIVERY_SEAL.json',dict(status=status,files=files));assert p.size()<8*2**20
    print(json.dumps(dict(status=status,deliveries=len(files),frozen_identities=len(f['files']),
        Windows_seconds=windows,Linux_child_seconds=linux,RSS=resource['maximum_Linux_RSS_bytes'],whole_dossier_bytes=p.size())),flush=True)


if __name__=='__main__':main()
