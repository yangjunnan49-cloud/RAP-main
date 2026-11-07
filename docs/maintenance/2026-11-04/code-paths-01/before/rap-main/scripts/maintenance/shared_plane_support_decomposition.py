"""Post-hoc count-only separation of cap and half-split effects."""
import resource
import time
from pathlib import Path
import shared_plane_representation_diagnosis as diag
import numpy as np

run = diag.run
OUT = run.BASE/'support-decomposition-01'


def main():
    run.verify()
    prior_freeze = run.read(diag.OUT/'freeze.json')
    for p, digest in prior_freeze['files'].items():
        assert run.sha(p) == digest
    files = [Path(__file__), run.BASE/'SUPPORT_DECOMPOSITION_SCOPE.md', Path(diag.__file__),
             diag.OUT/'results.json', diag.OUT/'output_seal.json', run.old.SLAM/'scripts/shared_plane_map.py']
    files += [run.old.BASE/f'bank/{s}-{b}.npz' for s, b in run.old.WINDOWS]
    OUT.mkdir()
    run.save(OUT/'freeze.json', dict(utc=run.utc(), post_outcome=True, optimizer_calls=0,
             files={str(p): run.sha(p) for p in files}))
    previous = run.read(diag.OUT/'results.json')['rows']
    rows = {}
    max_delta = 0.
    points_checked = 0
    for seq, boundary in run.old.WINDOWS:
        key = f'{seq}-{boundary}'
        z = np.load(run.old.BASE/f'bank/{key}.npz', allow_pickle=False)
        retained = [z[f'points_{i}'] for i in range(8)]
        for i, frame in enumerate(z['frames']):
            p, _ = diag.full_representatives(seq, int(frame))
            mapping = {tuple(k): j for j, k in enumerate(np.floor(p/.5).astype(np.int64))}
            index = np.array([mapping[tuple(k)] for k in np.floor(retained[i]/.5).astype(np.int64)])
            max_delta = max(max_delta, float(np.max(abs(retained[i]-p[index]))))
            points_checked += len(retained[i])
        rows[key] = {}
        for scale in run.SCALES:
            prior = previous[key]['scenarios'][str(int(scale))]
            middle = diag.census(retained, z['O'], scale)
            rows[key][str(int(scale))] = dict(old_even_training=prior['old_thin'],
                                            all_retained_points=middle,
                                            full_voxel_superset=prior['full_voxel_superset'])
        print('SMP1 support decomposition', key,
              {s: {name: [info['features'], info['representation_valid']] for name, info in values.items()}
               for s, values in rows[key].items()}, flush=True)
    assert max_delta < 1e-10 and points_checked == 190332
    run.save(OUT/'results.json', dict(utc=run.utc(), rows=rows, retained_superset_points_checked=points_checked,
             superset_max_coordinate_delta=max_delta, post_outcome=True, optimizer_calls=0, pose_errors_computed=False))
    for p, digest in run.read(OUT/'freeze.json')['files'].items():
        assert run.sha(p) == digest
    run.save(OUT/'output_seal.json', dict(results_sha256=run.sha(OUT/'results.json'),
             freeze_sha256=run.sha(OUT/'freeze.json'), all_input_hashes_match=True))


if __name__ == '__main__':
    start = time.perf_counter()
    try:
        main()
    finally:
        wall = time.perf_counter()-start
        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
        run.save(OUT/'RESOURCE_LOG.json', dict(wall_s=wall, peak_rss_bytes=rss))
        prior = run.read(run.BASE/'RESOURCE_LOG.json')
        extra = run.read(diag.OUT/'RESOURCE_LOG.json')['wall_s']
        artifacts = sum(p.stat().st_size for p in run.BASE.rglob('*') if p.is_file())
        assert wall+extra+sum(x['wall_s'] for x in prior) <= 1800 and rss <= 2*2**30 and artifacts <= 512*2**20
