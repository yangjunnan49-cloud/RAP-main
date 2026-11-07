"""Metadata-only next-design binding; no raw coordinates, evaluator poses or optimizer."""
import os
for name in ('OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'OMP_NUM_THREADS'):
    os.environ[name] = '1'
import json
import time
from pathlib import Path
import structural_holdout_map_pilot as run

BASE = run.BASE/'revisit-design-audit-01'


def main():
    start = time.perf_counter()
    seq = '00'
    source = run.old.source(seq)
    files = [Path(__file__), run.BASE/'NEXT_DESIGN_SCOPE.md']
    files += [source/name for name in ('accepted_loops.json', 'keyframes.json', 'source_frames.json', 'odom_poses.txt')]
    files += [run.old.SLAM/'rap_slam/pose_graph.py', run.old.SLAM/'scripts/shared_plane_map.py']
    BASE.mkdir()
    run.save(BASE/'freeze.json', dict(utc=run.utc(), files={str(p): run.sha(p) for p in files},
             selection_rule='Sequence00, original accepted-loop array index0; no GT or quality ranking',
             historical_gt_fields_in_container=True, previously_exposed_development=True))
    # Only these fields are projected into the design; the container has historical GT fields.
    source_rows = run.read(source/'accepted_loops.json')
    selected = {k: source_rows[0][k] for k in ('i', 'j', 'T_rel', 'measurement_id')}
    keys, frames = run.read(source/'keyframes.json'), run.read(source/'source_frames.json')
    groups = [[int(k) for k in keys if int(k) <= endpoint][-8:] for endpoint in (selected['i'], selected['j'])]
    assert all(len(g) == 8 and g[-1] == endpoint for g, endpoint in zip(groups, (selected['i'], selected['j'])))
    assert not set(groups[0]).intersection(groups[1])
    binding = []
    for visit, group in enumerate(groups):
        for node in group:
            raw = int(frames[node])
            path = run.old.rawpath(seq, raw)
            binding.append(dict(visit=visit, node=node, raw_frame=raw, path=str(path), bytes=path.stat().st_size, sha256=run.sha(path)))
    run.save(BASE/'results.json', dict(utc=run.utc(), sequence=seq, original_accepted_index=0,
             selected=selected, visit_keyframe_nodes=groups, raw_bindings=binding,
             raw_coordinate_payload_parsed=False, numeric_gt_pose_file_parsed=False,
             historical_gt_fields_used_in_selector=False,
             historical_gt_metadata_exposure_disclosed_in_scope=True,
             new_plane_construction=False, optimizer_calls=0, measurement_physical_correctness_unknown=True,
             shared_patch_support_unknown=True, whole_sequence_execution=False))
    for path, digest in run.read(BASE/'freeze.json')['files'].items():
        assert run.sha(path) == digest
    run.save(BASE/'output_seal.json', dict(utc=run.utc(), files={p.name: run.sha(p) for p in BASE.iterdir()}))
    elapsed = time.perf_counter()-start
    logs = run.read(run.BASE/'RESOURCE_LOG.json')
    import resource
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
    logs.append(dict(stage='next_design_metadata_audit', utc=run.utc(), wall_s=elapsed, peak_rss_bytes=rss, passed=True))
    (run.BASE/'RESOURCE_LOG.json').write_text(json.dumps(logs, indent=2)+'\n')
    assert sum(r['wall_s'] for r in logs) <= 1800 and rss <= 2*2**30
    print('Revisit design metadata', selected['i'], selected['j'], groups, flush=True)


if __name__ == '__main__':
    main()
