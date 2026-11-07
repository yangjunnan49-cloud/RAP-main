"""Post-outcome raw/support census, no optimization or reference errors."""
import resource
import time
from pathlib import Path
import shared_plane_map_pilot as run
import numpy as np

OUT = run.BASE/'representation-diagnosis-01'


def full_representatives(seq, frame):
    raw = np.fromfile(run.old.rawpath(seq, frame), dtype='<f4').reshape(-1, 4)[:, :3].astype(float)
    radius = np.linalg.norm(raw, axis=1)
    cloud = raw[(radius >= 1.5) & (radius <= 80.)]
    angle = np.deg2rad(.205)
    x, y, z = cloud.T
    rho = np.hypot(x, y)
    good = rho > 1e-6
    corrected = cloud.copy()
    corrected[good, 0] = x[good]*np.cos(angle)-x[good]*z[good]/rho[good]*np.sin(angle)
    corrected[good, 1] = y[good]*np.cos(angle)-y[good]*z[good]/rho[good]*np.sin(angle)
    corrected[good, 2] = z[good]*np.cos(angle)+rho[good]*np.sin(angle)
    _, index = np.unique(np.floor(corrected/.5).astype(np.int64), axis=0, return_index=True)
    return corrected[index], dict(raw_points=len(raw), range_points=len(cloud), voxel_representatives=len(index))


def census(points, initial, scale):
    stats, info = run.alg.features(points, initial, scale)
    if info['features']:
        vectors = run.alg.fit_planes(stats, initial)[1][:, :, 0]
        info['normal_scatter_eigenvalues'] = np.linalg.eigvalsh(vectors.T@vectors/len(vectors)).tolist()
    else:
        info['normal_scatter_eigenvalues'] = None
    return info


def main():
    run.verify()
    assert run.read(run.BASE/'validation.json')['passed']
    files = [Path(__file__), run.BASE/'REPRESENTATION_DIAGNOSIS_SCOPE.md',
             run.old.SLAM/'scripts/shared_plane_map.py', run.BASE/'results.json',
             run.BASE/'validation.json', run.BASE/'bank_seal.json']
    files += list((run.BASE/'bank').iterdir())
    files += [run.old.rawpath(s, f) for s, boundary in run.old.WINDOWS for f in run.old.frames(s, boundary)]
    OUT.mkdir()
    run.save(OUT/'freeze.json', dict(utc=run.utc(), post_outcome=True, optimizer_calls=0,
             files={str(p): run.sha(p) for p in files}))
    original_raw_freeze = run.read(run.old.ROOT_BASE/'freeze.json')['files']
    for p in files:
        if p.suffix == '.bin':
            assert run.sha(p) == original_raw_freeze[str(p)]
    rows = {}
    maximum = 0.
    for seq, boundary in run.old.WINDOWS:
        key = f'{seq}-{boundary}'
        z = np.load(run.old.BASE/f'bank/{key}.npz', allow_pickle=False)
        full, counts = [], []
        thin = [z[f'points_{i}'][::2] for i in range(8)]
        for i, frame in enumerate(z['frames']):
            p, info = full_representatives(seq, int(frame))
            index = {tuple(k): j for j, k in enumerate(np.floor(p/.5).astype(np.int64))}
            selected = np.array([index[tuple(k)] for k in np.floor(thin[i]/.5).astype(np.int64)])
            maximum = max(maximum, float(np.max(abs(p[selected]-thin[i]))))
            full.append(p)
            counts.append(info)
        rows[key] = dict(point_counts=counts, old_training_points=[len(p) for p in thin],
                         scenarios={str(int(scale)): dict(old_thin=census(thin, z['O'], scale),
                                                         full_voxel_superset=census(full, z['O'], scale)) for scale in run.SCALES})
        print('SMP1 representation census', key,
              {scale: {scenario: [info['features'], info['representation_valid'], min(info['per_scan_training_points'])]
                       for scenario, info in values.items()} for scale, values in rows[key]['scenarios'].items()}, flush=True)
    assert maximum < 1e-10
    run.save(OUT/'results.json', dict(utc=run.utc(), rows=rows, superset_coordinate_max_delta=maximum,
             post_outcome=True, optimizer_calls=0, new_pose_error_computation=False))
    for path, digest in run.read(OUT/'freeze.json')['files'].items():
        assert run.sha(path) == digest
    run.save(OUT/'output_seal.json', dict(results_sha256=run.sha(OUT/'results.json'),
             source_freeze_sha256=run.sha(OUT/'freeze.json'), all_input_hashes_match=True))


if __name__ == '__main__':
    start = time.perf_counter()
    try:
        main()
    finally:
        wall = time.perf_counter()-start
        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
        run.save(OUT/'RESOURCE_LOG.json', dict(wall_s=wall, peak_rss_bytes=rss))
        rows = run.read(run.BASE/'RESOURCE_LOG.json')
        artifacts = sum(p.stat().st_size for p in run.BASE.rglob('*') if p.is_file())
        assert wall+sum(r['wall_s'] for r in rows) <= 1800 and rss <= 2*2**30 and artifacts <= 512*2**20
