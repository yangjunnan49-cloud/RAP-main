"""Diagnose original synthetic no-op failure without real data or gate changes."""
import os
for key in ('OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','OMP_NUM_THREADS'):
    os.environ[key] = '1'
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]/'scripts/maintenance'))
import cross_visit_map_pilot as run
import numpy as np


def diagnose():
    run.verify()
    rng = np.random.default_rng(202610092429)
    truth = np.repeat(np.eye(4)[None], 6, axis=0)
    for i in range(1,6):
        truth[i] = run.alg.retract(truth[i], np.r_[rng.normal(0,.04,3),rng.normal(0,1.,3)])
    world = []
    for axis in range(3):
        p = rng.uniform(-3,3,(100,3))
        p[:,axis] = axis-1.
        world.append(p)
    groups = [[(p-t[:3,3])@t[:3,:3] for t in truth] for p in world]
    stats = run.previous.prior.stats_from_groups(groups)
    rows = {}
    for arm in ('F','J'):
        pose, trace, correction = run.alg.optimize(stats, truth, arm, 3)
        rows[arm] = dict(max_delta=float(np.max(abs(pose-truth))), correction=correction, trace=trace,
                         initial_cost=run.alg.cost(stats,truth,truth,arm,3),
                         initial_h_eigenvalues=np.linalg.eigvalsh(run.alg.system(stats,truth,truth,arm,3)[0]).tolist(),
                         initial_gradient=run.alg.system(stats,truth,truth,arm,3)[1].tolist())
    run.save(run.BASE/'PREFLIGHT_DIAGNOSIS.json', rows)
    print('Synthetic no-op diagnosis', {a:r['max_delta'] for a,r in rows.items()}, flush=True)


if __name__ == '__main__':
    run.record_stage('preflight_diagnosis', diagnose)
