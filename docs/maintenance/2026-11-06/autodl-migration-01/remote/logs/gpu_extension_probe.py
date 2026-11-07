"""Four-point target native ABI fixture; no project, model, data, or training."""
import hashlib
import json
from pathlib import Path
import time
import torch
from pytorch3d import _C
from pytorch3d.ops import ball_query, knn_points, sample_farthest_points

root = Path("/root/autodl-tmp/rap-migration-20261106")
output = root / "GPU_EXTENSION_PROBE.json"
assert not output.exists() and torch.cuda.is_available()
start = time.monotonic()
points = torch.tensor([[[0., 0., 0.], [1., 0., 0.], [0., 2., 0.], [0., 0., 3.]]])
cpu_fps, cpu_index = sample_farthest_points(points, K=2, random_start_point=False)
cpu_ball = ball_query(points, points, K=2, radius=2.1, return_nn=True)
device_points = points.cuda()
gpu_fps, gpu_index = sample_farthest_points(device_points, K=2, random_start_point=False)
gpu_ball = ball_query(device_points, device_points, K=2, radius=2.1, return_nn=True)
gpu_knn = knn_points(device_points, device_points, K=1)
assert torch.equal(cpu_index, gpu_index.cpu()) and torch.equal(cpu_fps, gpu_fps.cpu())
assert torch.equal(cpu_ball.idx, gpu_ball.idx.cpu())
assert torch.isfinite(gpu_ball.dists).all() and torch.equal(gpu_knn.dists, torch.zeros_like(gpu_knn.dists))
torch.cuda.synchronize()
native = Path(_C.__file__)
value = dict(passed=True, scope="FOUR_POINT_NATIVE_CPU_GPU_ABI_ONLY", torch=torch.__version__,
    cuda=torch.version.cuda, capability=list(torch.cuda.get_device_capability(0)),
    native_extension_path=str(native), native_extension_sha256=hashlib.sha256(native.read_bytes()).hexdigest(),
    points=4, operations=["sample_farthest_points", "ball_query", "knn_points"],
    model_instances=0, dataset_reads=0, checkpoint_loads=0, training_calls=0, wall_seconds=time.monotonic()-start)
output.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
print(json.dumps(value))
