"""Matched fresh POSS inference arms; never rewrites historical edges."""
import hashlib
import json
import sys
from pathlib import Path
import numpy as np
import torch

sys.path[:0] = ['/mnt/e/githouse/RAP-SLAM', '/mnt/e/githouse/RAP-main']
from rap_slam.rap_backend import RAPBackend

def geom(r):
    return dict(orthogonality=float(np.max(np.abs(r.T @ r - np.eye(3)))),
                det_error=float(abs(np.linalg.det(r) - 1)))

def main():
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=False)
    root = Path('/mnt/e/githouse/RAP-SLAM')
    source = root / 'output_prods/poss/accepted_loops.json'
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    edges = json.loads(source.read_text())
    scans = {}
    identities = []
    for frame in sorted({3850 + e[k] for e in edges for k in ['i', 'j']}):
        path = root / f'data/poss/dataset/sequences/00/velodyne/{frame:06d}.bin'
        scans[frame] = np.fromfile(path, dtype=np.float32).reshape(-1, 4)[:, :3]
        identities.append(dict(frame=frame, path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    backend = RAPBackend()
    rows = []
    for edge in edges:
        ids = [3850 + edge[k] for k in ['i', 'j']]
        for arm in ['fresh_tf32_legacy', 'ieee_repaired']:
            torch.manual_seed(42)
            np.random.seed(42)
            torch.set_float32_matmul_precision('high')
            if arm == 'ieee_repaired':
                transform, diag = backend.register(*(scans[i] for i in ids))
            else:
                transform, diag = RAPBackend.register.__wrapped__(backend, *(scans[i] for i in ids))
            assert torch.get_float32_matmul_precision() == 'high'
            g = geom(transform[:3, :3])
            if arm == 'ieee_repaired':
                assert max(g.values()) < 1e-5, g
            row = dict(arm=arm, source_frame_ids=ids, seed=42, T_rel=transform.tolist(),
                       diagnostics=diag, **g)
            rows.append(row)
            print(json.dumps({k: row[k] for k in ['arm', 'source_frame_ids', 'orthogonality', 'det_error']}), flush=True)
    torch.manual_seed(42)
    parts, diag = backend.register_multi([scans[i] for i in sorted(scans)[:3]])
    multi = [geom(p[:3, :3]) for p in parts]
    assert all(max(g.values()) < 1e-5 for g in multi)
    assert hashlib.sha256(source.read_bytes()).hexdigest() == source_hash
    result = dict(parent_run_id='legacy-poss_off', historical_rng_binding='unknown',
                  protocol='Fresh matched seed 42 per pair, default RAPBackend configuration; raw POSS LiDAR scans. Numerical validation only, no GT score claim.',
                  source_edges_sha256=source_hash, inputs=identities, rows=rows,
                  multi_geometry=multi, multi_source_frame_ids=sorted(scans)[:3],
                  backend_sha256=hashlib.sha256((root/'rap_slam/rap_backend.py').read_bytes()).hexdigest(),
                  precision_sha256=hashlib.sha256((root/'rap_slam/rap_precision.py').read_bytes()).hexdigest(),
                  torch=torch.__version__, status='passed')
    (out/'results.json').write_text(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
