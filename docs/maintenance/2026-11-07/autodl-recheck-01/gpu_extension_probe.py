"""One four-point CPU/GPU native-extension fixture for migration revalidation."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time

root = Path(__file__).resolve().parent
assert not (root / "GPU_EXTENSION_PROBE.json").exists()
started = time.monotonic()
import torch
from pytorch3d import _C
from pytorch3d.ops import ball_query, knn_points, sample_farthest_points
torch.set_num_threads(1)
points = torch.tensor([[[0., 0., 0.], [1., 0., 0.], [0., 2., 0.], [0., 0., 3.]]])
gpu = points.cuda()
cpu_fps = sample_farthest_points(points, K=3, random_start_point=False)
gpu_fps = sample_farthest_points(gpu, K=3, random_start_point=False)
assert torch.equal(cpu_fps[1], gpu_fps[1].cpu())
assert torch.equal(cpu_fps[0], gpu_fps[0].cpu())
cpu_ball = ball_query(points, points, K=4, radius=2.5, return_nn=True)
gpu_ball = ball_query(gpu, gpu, K=4, radius=2.5, return_nn=True)
assert torch.equal(cpu_ball.idx, gpu_ball.idx.cpu())
assert torch.allclose(cpu_ball.dists, gpu_ball.dists.cpu())
assert torch.allclose(cpu_ball.knn, gpu_ball.knn.cpu())
knn = knn_points(gpu, gpu, K=1)
assert torch.equal(knn.idx.cpu().flatten(), torch.arange(4)) and torch.count_nonzero(knn.dists) == 0
torch.cuda.synchronize()
pins = json.loads((root / "PINS.json").read_bytes())
sha = hashlib.sha256(Path(_C.__file__).read_bytes()).hexdigest()
assert sha == pins["native_extension_sha256"]
result = dict(observed_utc=datetime.now(timezone.utc).isoformat(), passed=True,
    scope="FOUR_POINT_NATIVE_CPU_GPU_ABI_ONLY", torch=torch.__version__, cuda=torch.version.cuda,
    capability=list(torch.cuda.get_device_capability()), native_extension_sha256=sha,
    points=4, operations=["sample_farthest_points", "ball_query", "knn_points"],
    model_instances=0, dataset_reads=0, checkpoint_loads=0, training_calls=0,
    wall_seconds=time.monotonic() - started)
with (root / "GPU_EXTENSION_PROBE.json").open("x") as stream:
    json.dump(result, stream, indent=2)
print(json.dumps(result))
