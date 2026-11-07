"""Local fixture check. Requires an existing NumPy environment; installs nothing."""
from pathlib import Path
import hashlib
import numpy as np
from legacy_f32_correction import legacy_f32_correction
base=Path(__file__).resolve().parent
p=np.load(base/'synthetic_points.npy',allow_pickle=False)
expected=np.load(base/'expected_original_f32.npy',allow_pickle=False)
actual=legacy_f32_correction(p)
assert actual.dtype==np.float32 and actual.shape==expected.shape
assert hashlib.sha256(actual.tobytes(order='C')).digest()==hashlib.sha256(expected.tobytes(order='C')).digest()
print('PASS',np.__version__,actual.shape,'exact original float32 bytes')
