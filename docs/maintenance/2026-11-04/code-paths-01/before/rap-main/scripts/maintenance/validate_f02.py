"""Bounded GPU geometry regression; writes a new, exclusive evidence file."""
import json
import sys
from pathlib import Path
import numpy as np
import torch

sys.path[:0] = ['/mnt/e/githouse/RAP-SLAM', '/mnt/e/githouse/RAP-main']
from rap_slam.rap_precision import ieee_matmul
from rectified_point_flow.procrustes import fit_transformations, rigidify_prediction_with_procrustes

def geometry(r):
    r = r.double()
    return {'orthogonality': (r.T @ r - torch.eye(3, device=r.device)).abs().max().item(),
            'det_error': abs(torch.linalg.det(r).item() - 1)}

def main():
    torch.manual_seed(42)
    device = 'cuda'
    x = torch.randn(2048, 3, device=device)
    a = .37
    r = torch.tensor([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]], device=device, dtype=torch.float64)
    t = torch.tensor([.2, -.3, .1], device=device, dtype=torch.float64)
    y = (x.double() @ r.T + t).float()
    counts = torch.tensor([[1024, 1024]], device=device)
    cu = torch.tensor([0, 2048], device=device, dtype=torch.int32)
    rows = []
    original = torch.get_float32_matmul_precision()
    try:
        for policy in ['highest', 'high', 'medium']:
            torch.set_float32_matmul_precision(policy)
            with ieee_matmul():
                assert torch.get_float32_matmul_precision() == 'highest'
                with torch.autocast('cuda', dtype=torch.float16):
                    rotations, translations = fit_transformations(x, y, counts, cu)
                    rigid = rigidify_prediction_with_procrustes(y, x, counts, cu)
                for i in range(2):
                    row = {'incoming_policy': policy, 'part': i, **geometry(rotations[0, i])}
                    row['rotation_max_error'] = (rotations[0, i].double() - r).abs().max().item()
                    row['translation_max_error'] = (translations[0, i].double() - t).abs().max().item()
                    row['rigidify_max_error'] = (rigid - y).abs().max().item()
                    assert max(row[k] for k in ['orthogonality', 'det_error', 'rotation_max_error', 'translation_max_error', 'rigidify_max_error']) < 1e-5, row
                    rows.append(row)
            assert torch.get_float32_matmul_precision() == policy
            try:
                with ieee_matmul():
                    with ieee_matmul():
                        raise RuntimeError('restoration probe')
            except RuntimeError:
                pass
            assert torch.get_float32_matmul_precision() == policy
    finally:
        torch.set_float32_matmul_precision(original)
    result = {'torch': torch.__version__, 'gpu': torch.cuda.get_device_name(), 'rows': rows,
              'restoration_and_nested_exception': 'passed', 'status': 'passed'}
    output = Path(sys.argv[1])
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x') as f:
        json.dump(result, f, indent=2)
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
