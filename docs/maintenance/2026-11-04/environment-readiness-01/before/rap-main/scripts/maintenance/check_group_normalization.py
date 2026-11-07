"""Check the proposed coordinate conversion against the actual read-only normalizer."""
import ast
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation

root = Path('/mnt/e/githouse/RAP-main')
source = Path('/mnt/e/githouse/RAP-SLAM/rap_slam/rap_backend.py')
target = root / 'docs/maintenance/2026-09-15/breakthrough-direction-01/normalization_check.json'
assert not target.exists()
tree = ast.parse(source.read_text())
cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'RAPBackend')
method = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == '_normalize_parts')
method.decorator_list = []
env = {'np': np}
exec(compile(ast.Module(body=[method], type_ignores=[]), str(source), 'exec'), env)
rng = np.random.default_rng(913)
max_roundtrip = 0.
max_transport = 0.
for trial in range(100):
    parts = [rng.normal(size=(n, 3))*20 + rng.normal(size=3)*30 for n in [200, 100, 100, 200, 100, 100]]
    cond, scale, offsets, counts, anchor = env['_normalize_parts'](parts)
    cursor = 0
    assert sum(counts) == len(cond) and anchor == 0
    for p, count, offset in zip(parts, counts, offsets):
        recovered = cond[cursor:cursor+count].astype(float)*scale + offset
        max_roundtrip = max(max_roundtrip, float(np.max(np.abs(p-recovered))))
        r = Rotation.random(random_state=rng).as_matrix()
        t, center = rng.normal(size=(2, 3))
        a = (p@r.T+t-center)/scale
        b = (recovered@r.T+t-center)/scale
        max_transport = max(max_transport, float(np.max(np.abs(a-b))))
        cursor += count
assert max_roundtrip < 2e-5 and max_transport < 1e-6
with target.open('x') as f:
    json.dump(dict(passed=True, trials=100, six_parts_per_trial=True,
        actual_normalizer_extracted_by_ast=True,
        max_point_roundtrip_error_m=max_roundtrip,
        max_normalized_local_transport_error=max_transport,
        source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        scope='CPU coordinate conversion only; no RAP inference or GPU result'), f, indent=2)
print(max_roundtrip, max_transport)
