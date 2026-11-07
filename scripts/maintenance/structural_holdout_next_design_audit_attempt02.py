"""Schema-only retry of the separate metadata audit; original source is immutable."""
import os
for name in ('OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'OMP_NUM_THREADS'):
    os.environ[name] = '1'
import json
import resource
import time
import traceback
from pathlib import Path
import structural_holdout_map_pilot as run

ROOT = run.BASE/'revisit-design-audit-01'
BASE = ROOT/'attempt-02'


def main():
    frozen = run.read(ROOT/'freeze.json')
    for path, digest in frozen['files'].items():
        assert run.sha(path) == digest
    source = run.old.source('00')
    files = list(map(Path, frozen['files']))+[Path(__file__), ROOT/'freeze.json', ROOT/'FAILURE.json', ROOT/'AMENDMENT_01.md']
    BASE.mkdir()
    run.save(BASE/'freeze.json', dict(utc=run.utc(), files={str(p): run.sha(p) for p in files},
             schema_only_repair=True, selection_unchanged=True, new_coordinate_or_numeric_gt_payload=False))
    rows = run.read(source/'accepted_loops.json')
    selected = {k: rows[0][k] for k in ('i', 'j', 'T_rel', 'measurement_id')}
    keys = run.read(source/'keyframes.json')
    frames = run.read(source/'source_frames.json')['source_frame_ids']
    groups = [[int(k) for k in keys if int(k) <= endpoint][-8:] for endpoint in (selected['i'], selected['j'])]
    assert all(len(g) == 8 and g[-1] == endpoint for g, endpoint in zip(groups, (selected['i'], selected['j'])))
    assert not set(groups[0]).intersection(groups[1])
    binding = []
    for visit, group in enumerate(groups):
        for node in group:
            raw = int(frames[node])
            path = run.old.rawpath('00', raw)
            binding.append(dict(visit=visit, node=node, raw_frame=raw, path=str(path), bytes=path.stat().st_size, sha256=run.sha(path)))
    run.save(BASE/'results.json', dict(utc=run.utc(), sequence='00', original_accepted_index=0,
             selected=selected, visit_keyframe_nodes=groups, raw_bindings=binding,
             raw_coordinate_payload_parsed=False, numeric_gt_pose_file_parsed=False,
             historical_gt_fields_used_in_selector=False, historical_gt_metadata_exposure_disclosed_in_scope=True,
             new_plane_construction=False, optimizer_calls=0, measurement_physical_correctness_unknown=True,
             shared_patch_support_unknown=True, whole_sequence_execution=False))
    # Recheck schema binding independently by keyframe positional lookup.
    endpoints = [selected['i'], selected['j']]
    for visit, endpoint in enumerate(endpoints):
        position = keys.index(endpoint)
        assert keys[position-7:position+1] == groups[visit]
        for entry in binding[8*visit:8*visit+8]:
            assert frames[entry['node']] == entry['raw_frame'] and run.sha(entry['path']) == entry['sha256']
    for path, digest in run.read(BASE/'freeze.json')['files'].items():
        assert run.sha(path) == digest
    run.save(BASE/'validation.json', dict(passed=True, frame_bindings=16, source_selection_index=0, numeric_accuracy_not_computed=True))
    run.save(BASE/'output_seal.json', dict(utc=run.utc(), files={p.name: run.sha(p) for p in BASE.iterdir()}))
    print('Revisit design metadata', selected['i'], selected['j'], groups, flush=True)


if __name__ == '__main__':
    start, failure = time.perf_counter(), None
    try:
        main()
    except Exception as error:
        failure = repr(error)
        if BASE.exists():
            run.save(BASE/'FAILURE.json', dict(error=failure, traceback=traceback.format_exc()))
        raise
    finally:
        logs = run.read(run.BASE/'RESOURCE_LOG.json')
        logs.append(dict(stage='next_design_metadata_audit_original_failed', utc=run.utc(), wall_s=2.6586884,
                         peak_rss_bytes=None, passed=False, wall_from_external_tool_includes_startup_imports=True))
        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
        logs.append(dict(stage='next_design_metadata_audit_attempt02', utc=run.utc(), wall_s=time.perf_counter()-start,
                         peak_rss_bytes=rss, passed=failure is None))
        (run.BASE/'RESOURCE_LOG.json').write_text(json.dumps(logs, indent=2)+'\n')
        assert sum(r['wall_s'] for r in logs) <= 1800 and rss <= 2*2**30
