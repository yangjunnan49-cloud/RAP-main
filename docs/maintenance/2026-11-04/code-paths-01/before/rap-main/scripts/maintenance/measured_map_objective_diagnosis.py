"""Post-outcome MMR0 cost-landscape checks, with no optimizer execution."""
import argparse
import json
import resource
import time
from pathlib import Path
import measured_map_exploration_attempt02 as run
import numpy as np
from scipy.spatial.transform import Rotation

OUT = run.ROOT_BASE/'objective-diagnosis-01'


def interpolate(poses, direction, alpha):
    result = poses.copy()
    for node, delta in enumerate(direction, start=1):
        result[node] = run.alg.retract(poses[node], alpha*delta)
    return result


def main():
    run.verify()
    assert run.read(run.BASE/'bank_validation.json')['passed']
    assert run.read(run.BASE/'validation.json')['passed']
    files = [Path(__file__), run.ROOT_BASE/'OBJECTIVE_DIAGNOSIS_SCOPE.md',
             run.SLAM/'scripts/measured_map_reoptimization.py', run.BASE/'freeze.json',
             run.BASE/'bank_seal.json', run.BASE/'bank_validation.json',
             run.BASE/'results.json', run.BASE/'validation.json']
    files += list((run.BASE/'bank').iterdir())
    OUT.mkdir()
    run.save(OUT/'freeze.json', dict(utc=run.utc(), post_outcome=True, optimizer_calls=0,
             files={str(p): run.sha(p) for p in files}))
    rows = {}
    for seq, boundary in run.WINDOWS:
        key = f'{seq}-{boundary}'
        z = np.load(run.BASE/f'bank/{key}.npz', allow_pickle=False)
        points = [z[f'points_{i}'][::2] for i in range(8)]
        normal = [z[f'normals_{i}'][::2] for i in range(8)]
        valid = [z[f'valid_{i}'][::2] for i in range(8)]
        gt = run.gt(seq)[z['frames']]
        reference = np.array([run.alg.proper(t) for t in np.linalg.inv(gt[0])@gt])
        reference[0] = np.eye(4)
        outputs = {arm: z[arm] for arm in ('O', 'F', 'R')}
        outputs['reference'] = reference
        matches_o = run.alg.associations(points, normal, valid, z['O'])
        matches_r = run.alg.associations(points, normal, valid, z['R'])
        costs_o = {arm: run.alg.cost(points, normal, poses, matches_o) for arm, poses in outputs.items()}
        costs_r = {arm: run.alg.cost(points, normal, poses, matches_r) for arm, poses in outputs.items()}
        direction = []
        for current, target in zip(z['R'][1:], reference[1:]):
            rotation = Rotation.from_matrix(current[:3, :3].T@target[:3, :3]).as_rotvec()
            translation = current[:3, :3].T@(target[:3, 3]-current[:3, 3])
            direction.append(np.concatenate([rotation, translation]))
        direction = np.array(direction)
        h, g = run.alg.system(points, normal, z['R'], matches_r)
        components = g.reshape(-1, 6)*direction
        slope = float(components.sum())
        eps = 1e-6
        fd = (run.alg.cost(points, normal, interpolate(z['R'], direction, eps), matches_r)-
              run.alg.cost(points, normal, interpolate(z['R'], direction, -eps), matches_r))/(2*eps)
        assert abs(fd-slope) < 1e-7
        curve = []
        for alpha in (0., .1, .25, .5, 1.):
            current = interpolate(z['R'], direction, alpha)
            row = dict(alpha=alpha, fixed_final_r_cost=run.alg.cost(points, normal, current, matches_r))
            try:
                refreshed = run.alg.associations(points, normal, valid, current)
                row.update(rematched_cost=run.alg.cost(points, normal, current, refreshed),
                           rematched_counts=[len(m[2]) for m in refreshed], valid_rematching=True)
            except ValueError as error:
                row.update(valid_rematching=False, rejection=str(error))
            curve.append(row)
        diagonal = np.maximum(np.diag(h), 1e-8)
        eig = np.linalg.eigvalsh(h/np.sqrt(diagonal[:, None]*diagonal[None, :]))
        rows[key] = dict(fixed_initial_costs=costs_o, fixed_final_r_costs=costs_r,
                         final_r_to_reference_cost_slope=slope, slope_fd=float(fd),
                         slope_rotation=float(components[:, :3].sum()),
                         slope_translation=float(components[:, 3:].sum()),
                         interpolation=curve, normalized_hessian_eigenvalues=eig.tolist(),
                         normalized_hessian_rank_at_1e_minus6=int(np.sum(eig > 1e-6)),
                         initial_counts=[len(m[2]) for m in matches_o], final_r_counts=[len(m[2]) for m in matches_r])
        print(key, 'fixed initial costs', costs_o, 'R->reference slope', slope,
              'rotation', rows[key]['slope_rotation'], 'translation', rows[key]['slope_translation'], flush=True)
    run.save(OUT/'results.json', dict(utc=run.utc(), post_outcome=True, optimizer_calls=0, rows=rows))
    for p, digest in run.read(OUT/'freeze.json')['files'].items():
        assert run.sha(p) == digest
    run.save(OUT/'output_seal.json', dict(results_sha256=run.sha(OUT/'results.json'),
             freeze_sha256=run.sha(OUT/'freeze.json'), all_input_hashes_unchanged=True))


if __name__ == '__main__':
    start = time.perf_counter()
    try:
        main()
    finally:
        wall = time.perf_counter()-start
        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
        run.save(OUT/'RESOURCE_LOG.json', dict(wall_s=wall, peak_rss_bytes=rss))
        prior = run.read(run.ROOT_BASE/'RESOURCE_LOG.json')+run.read(run.BASE/'RESOURCE_LOG.json')
        artifacts = sum(p.stat().st_size for p in run.ROOT_BASE.rglob('*') if p.is_file())
        assert wall+sum(r['wall_s'] for r in prior) <= 1800 and rss <= 2*2**30 and artifacts <= 512*2**20
