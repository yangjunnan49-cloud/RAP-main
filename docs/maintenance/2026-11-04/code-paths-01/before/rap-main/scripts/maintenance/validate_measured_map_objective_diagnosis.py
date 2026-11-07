"""Independent world-plane cost arithmetic for the post-outcome diagnostic."""
import resource
import time
import measured_map_objective_diagnosis as diag
import numpy as np
from scipy.spatial.transform import Rotation

run = diag.run


def world_cost(points, normals, poses, matches):
    total = 0.
    for a, b, ia, ib in matches:
        target = (poses[a, :3, :3]@points[a][ia].T).T+poses[a, :3, 3]
        source = (poses[b, :3, :3]@points[b][ib].T).T+poses[b, :3, 3]
        n = (poses[a, :3, :3]@normals[a][ia].T).T
        r = np.sum(n*(source-target), axis=1)
        total += float(np.mean(.04*(np.sqrt(1+25*r*r)-1)))
    return total


def main():
    run.verify()
    freeze = run.read(diag.OUT/'freeze.json')
    for path, digest in freeze['files'].items():
        assert run.sha(path) == digest
    seal = run.read(diag.OUT/'output_seal.json')
    assert seal['results_sha256'] == run.sha(diag.OUT/'results.json')
    result = run.read(diag.OUT/'results.json')
    max_delta = 0.
    count = 0
    for seq, boundary in run.WINDOWS:
        key = f'{seq}-{boundary}'
        row = result['rows'][key]
        z = np.load(run.BASE/f'bank/{key}.npz', allow_pickle=False)
        points = [z[f'points_{i}'][::2] for i in range(8)]
        normal = [z[f'normals_{i}'][::2] for i in range(8)]
        valid = [z[f'valid_{i}'][::2] for i in range(8)]
        gt = run.gt(seq)[z['frames']]
        reference = np.stack([np.linalg.solve(gt[0], pose) for pose in gt])
        for t in reference:
            u, _, vh = np.linalg.svd(t[:3, :3])
            t[:3, :3] = u@np.diag([1., 1., np.linalg.det(u@vh)])@vh
        reference[0] = np.eye(4)
        outputs = dict(O=z['O'], F=z['F'], R=z['R'], reference=reference)
        for name, arm in (('fixed_initial_costs', 'O'), ('fixed_final_r_costs', 'R')):
            matches = run.alg.associations(points, normal, valid, z[arm])
            for pose_arm, poses in outputs.items():
                actual = world_cost(points, normal, poses, matches)
                max_delta = max(max_delta, abs(actual-row[name][pose_arm]))
                count += 1
        matches = run.alg.associations(points, normal, valid, z['R'])
        for curve in row['interpolation']:
            alpha = curve['alpha']
            poses = z['R'].copy()
            for i in range(1, 8):
                current, target = poses[i], reference[i]
                tangent_rotation = Rotation.from_matrix(current[:3, :3].T@target[:3, :3]).as_rotvec()
                poses[i, :3, :3] = current[:3, :3]@Rotation.from_rotvec(alpha*tangent_rotation).as_matrix()
                poses[i, :3, 3] = (1-alpha)*z['R'][i, :3, 3]+alpha*target[:3, 3]
            max_delta = max(max_delta, abs(world_cost(points, normal, poses, matches)-curve['fixed_final_r_cost']))
            count += 1
        assert row['normalized_hessian_rank_at_1e_minus6'] == 42
        assert abs(row['slope_rotation']+row['slope_translation']-row['final_r_to_reference_cost_slope']) < 1e-12
    assert max_delta < 1e-9
    run.save(diag.OUT/'validation.json', dict(passed=True, independent_world_cost_max_delta=max_delta,
             cost_records_checked=count, optimizer_calls=0, post_outcome=True))
    print('MMR0 post-outcome world cost validation passed', max_delta, count, flush=True)


if __name__ == '__main__':
    start = time.perf_counter()
    try:
        main()
    finally:
        wall = time.perf_counter()-start
        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
        run.save(diag.OUT/'VALIDATION_RESOURCE_LOG.json', dict(wall_s=wall, peak_rss_bytes=rss))
        prior = run.read(run.ROOT_BASE/'RESOURCE_LOG.json')+run.read(run.BASE/'RESOURCE_LOG.json')
        extra = run.read(diag.OUT/'RESOURCE_LOG.json')['wall_s']
        assert sum(r['wall_s'] for r in prior)+extra+wall <= 1800 and rss <= 2*2**30
