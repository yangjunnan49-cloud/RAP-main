"""Synthetic equation audit for a proposed direction, not a RAP implementation."""
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation

ROOT = Path('/mnt/e/githouse/RAP-main')
OUT = ROOT / 'docs/maintenance/2026-09-15/breakthrough-direction-01'


def transform(p, t):
    return p @ t[:3, :3].T + t[:3, 3]


def pose(rng):
    t = np.eye(4)
    t[:3, :3] = Rotation.random(random_state=rng).as_matrix()
    t[:3, 3] = rng.normal(size=3) * 5
    return t


def fit(x, y):
    xc, yc = x.mean(0), y.mean(0)
    u, _, vt = np.linalg.svd((x-xc).T @ (y-yc))
    correction = np.diag([1, 1, np.linalg.det(vt.T @ u.T)])
    r = vt.T @ correction @ u.T
    t = np.eye(4)
    t[:3, :3] = r
    t[:3, 3] = yc - r @ xc
    return t


def recover(parts, locals_, outputs, scale, center):
    q = np.concatenate([(transform(p, l)-center)/scale for p, l in zip(parts, locals_)])
    qpose = fit(q, np.concatenate(outputs))
    physical = qpose.copy()
    physical[:3, 3] = scale*qpose[:3, 3] - qpose[:3, :3] @ center
    return physical


def main():
    target = OUT / 'geometry_check.json'
    assert not target.exists()
    rng = np.random.default_rng(20260915)
    maxima = dict(pose=0., local_relation=0., permutation=0., common_gauge=0., singleton=0.)
    for _ in range(100):
        groups = []
        gauge = pose(rng)
        scale = float(rng.uniform(20, 180))
        for group in range(2):
            parts = [rng.normal(size=(n, 3))*10 for n in [83, 47, 61]]
            ls = [np.eye(4), pose(rng), pose(rng)]
            g = pose(rng)
            center = rng.normal(size=3)*3
            # Evaluator-created ideal endpoints; synthetic truth never enters real generation.
            yy = [transform(transform(p, l), g)/scale for p, l in zip(parts, ls)]
            actual = recover(parts, ls, yy, scale, center)
            maxima['pose'] = max(maxima['pose'], float(np.max(np.abs(actual-g))))
            reindex = [2, 0, 1]
            perm = recover([parts[k] for k in reindex], [ls[k] for k in reindex], [yy[k] for k in reindex], scale, center)
            maxima['permutation'] = max(maxima['permutation'], float(np.max(np.abs(actual-perm))))
            one = recover(parts[:1], ls[:1], yy[:1], scale, center)
            maxima['singleton'] = max(maxima['singleton'], float(np.max(np.abs(one-g))))
            for a in range(3):
                for b in range(3):
                    expected = np.linalg.solve(ls[a], ls[b])
                    obtained = np.linalg.solve(actual@ls[a], actual@ls[b])
                    maxima['local_relation'] = max(maxima['local_relation'], float(np.max(np.abs(expected-obtained))))
            yg = [transform(y*scale, gauge)/scale for y in yy]
            changed = recover(parts, ls, yg, scale, center)
            groups.append((actual, changed))
        rel = np.linalg.solve(groups[0][0], groups[1][0])
        rel_g = np.linalg.solve(groups[0][1], groups[1][1])
        maxima['common_gauge'] = max(maxima['common_gauge'], float(np.max(np.abs(rel-rel_g))))
    assert max(maxima.values()) < 1e-10
    sources = [Path(__file__), ROOT/'rectified_point_flow/sampler.py', ROOT/'rectified_point_flow/procrustes.py', ROOT/'rectified_point_flow/modeling.py', ROOT/'rectified_point_flow/flow_model/layer.py', Path('/mnt/e/githouse/RAP-SLAM/rap_slam/rap_backend.py')]
    with target.open('x') as f:
        json.dump(dict(passed=True, trials=100, max_absolute_matrix_deltas=maxima,
            scope='Synthetic exact-motion equation audit only; no model inference, accuracy or memory claim.',
            tested=['scale and per-scan centering reconstruction', 'nontrivial rotations and translations', 'unequal point counts', 'scan permutation', 'common gauge invariance', 'singleton reduction', 'within-group relative poses'],
            untested=['noisy local motion', 'dynamics and scan distortion', 'conditioning shift', 'actual sampling hook', 'final endpoint versus projected state', 'GPU resources', 'real registration outcomes'],
            source_hashes={str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}), f, indent=2)
    print(json.dumps(maxima))


if __name__ == '__main__':
    main()
