"""Frozen VB1 geometry and I/O helpers, independent of RAP/SLAM production."""
import ctypes
import datetime as dt
import hashlib
import json
import math
import os
import sys
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
START = time.monotonic()
READS = set()


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda: handle.read(1024 ** 2), b''):
            h.update(block)
    return h.hexdigest()


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def save(path, obj):
    with Path(path).open('x', encoding='utf-8') as handle:
        json.dump(obj, handle, indent=2, allow_nan=False, ensure_ascii=True)
        handle.write('\n')


def stamp():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def verify_freeze(role):
    freeze = load(ROOT / 'SOURCE_FREEZE.json')
    roles = {'shared', role}
    if role in ('evaluation', 'audit'):
        roles.add('prediction')
    if role == 'audit':
        roles.add('evaluation')
    for item in freeze['files']:
        if item['role'] in roles:
            p = ROOT / item['path']
            assert p.stat().st_size == item['bytes'] and sha(p) == item['sha256'], str(p)
    return sha(ROOT / 'SOURCE_FREEZE.json')


def runtime():
    target = ROOT.parent / 'vision-runtime-local-01/site-packages'
    sys.path.insert(0, str(target))
    import cv2
    import numpy as np
    import numpy.lib._npyio_impl
    import numpy.linalg
    assert Path(cv2.__file__).resolve().is_relative_to(target.resolve())
    assert cv2.__version__ == '5.0.0' and np.__version__ == '2.3.5'
    cv2.setNumThreads(1)
    cv2.ocl.setUseOpenCL(False)
    assert cv2.getNumThreads() == 1 and not cv2.ocl.useOpenCL() and 'torch' not in sys.modules
    return cv2, np


def read_gate(paths, output):
    allowed = {os.path.normcase(str(Path(p).resolve())) for p in paths}
    out = Path(output).resolve()

    def audit(event, args):
        if event.startswith(('socket.', 'subprocess.', 'os.system', 'os.exec', 'os.spawn')):
            raise PermissionError('VB1 excludes network/process execution: ' + event)
        if event != 'open' or isinstance(args[0], int):
            return
        p = Path(os.fsdecode(args[0])).resolve()
        mode, flags = args[1:3]
        writing = any(c in mode for c in 'wax+') if isinstance(mode, str) else bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
        if writing:
            if not p.is_relative_to(out):
                raise PermissionError('VB1 output outside stage: ' + str(p))
        else:
            normalized = os.path.normcase(str(p))
            if normalized not in allowed:
                raise PermissionError('VB1 read not on exact allowlist: ' + str(p))
            READS.add(normalized)

    sys.addaudithook(audit)


def peak_bytes():
    class Counters(ctypes.Structure):
        _fields_ = [('cb', ctypes.c_ulong), ('PageFaultCount', ctypes.c_ulong)] + [
            (n, ctypes.c_size_t) for n in ('PeakWorkingSetSize', 'WorkingSetSize',
            'QuotaPeakPagedPoolUsage', 'QuotaPagedPoolUsage', 'QuotaPeakNonPagedPoolUsage',
            'QuotaNonPagedPoolUsage', 'PagefileUsage', 'PeakPagefileUsage')]
    counters = Counters()
    counters.cb = ctypes.sizeof(counters)
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.GetCurrentProcess.restype = ctypes.c_void_p
    psapi = ctypes.WinDLL('psapi', use_last_error=True)
    psapi.GetProcessMemoryInfo.argtypes = [ctypes.c_void_p, ctypes.POINTER(Counters), ctypes.c_ulong]
    assert psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(), ctypes.byref(counters), counters.cb)
    return int(counters.PeakWorkingSetSize)


def complete(output, extra):
    save(output / 'RESULT.json', {'passed': True, 'completed_utc': stamp(),
         'elapsed_seconds': time.monotonic() - START, 'child_lifetime_peak_bytes': peak_bytes(),
         'audited_read_paths': sorted(READS), 'torch_imported': 'torch' in sys.modules, **extra})


def failure(output, exc):
    path = output / 'FAILURE.json'
    if not path.exists():
        save(path, {'error': repr(exc), 'utc': stamp(), 'elapsed_seconds': time.monotonic() - START})


def seed(key):
    return int(hashlib.sha256(('VB1:' + key).encode('ascii')).hexdigest()[:8], 16) % 2147483647


def camera(np, path):
    rows = {}
    for line in Path(path).read_text(encoding='ascii').splitlines():
        key, text = line.split(':', 1)
        rows[key] = [float(x) for x in text.split()]
    p = np.asarray(rows['P0'], dtype=np.float64).reshape(3, 4)
    k = np.ascontiguousarray(p[:, :3])
    assert np.isfinite(p).all() and np.array_equal(p[:, 3], np.zeros(3))
    assert np.array_equal(k[2], [0., 0., 1.]) and k[0, 0] > 0 and k[1, 1] > 0 and np.linalg.det(k) > 0
    return k


def mutual_matches(cv2, np, a, b, ratio):
    if len(a) < 2 or len(b) < 2:
        return np.empty((0, 2), dtype=np.int32)
    matcher = cv2.BFMatcher(cv2.NORM_L2, crossCheck=False)

    def good(first, second):
        accepted = {}
        for group in matcher.knnMatch(first, second, k=2):
            if len(group) == 2 and all(math.isfinite(m.distance) for m in group):
                m, n = group
                if m.distance < ratio * n.distance:
                    accepted[m.queryIdx] = m.trainIdx
        return accepted

    forward, backward = good(a, b), good(b, a)
    result = sorted((i, j) for i, j in forward.items() if backward.get(j) == i)
    return np.asarray(result, dtype=np.int32).reshape(-1, 2)


def estimate(cv2, np, first, second, k, settings, key):
    n = len(first)
    out = {'status': 'NO_EVIDENCE_INSUFFICIENT_MATCHES', 'matches': n,
           'essential_inliers': 0, 'cheirality_inliers': 0, 'candidate_counts': [],
           'seed': seed(key), 'R_i_to_j': None, 'unit_t_i_to_j': None}
    arrays = {'E': np.empty((0, 3), dtype=np.float64),
              'essential_mask': np.zeros(n, dtype=np.uint8), 'cheirality_mask': np.zeros(n, dtype=np.uint8)}
    if n < settings['minimum_matches']:
        return out, arrays
    if not np.isfinite(first).all() or not np.isfinite(second).all():
        out['status'] = 'NO_EVIDENCE_NONFINITE_MATCHES'
        return out, arrays
    if any(np.linalg.matrix_rank(p - p.mean(axis=0)) < 2 for p in (first, second)):
        out['status'] = 'NO_EVIDENCE_DEGENERATE_COORDINATES'
        return out, arrays
    cv2.setRNGSeed(out['seed'])
    try:
        essential, mask = cv2.findEssentialMat(first, second, cameraMatrix=k, method=cv2.RANSAC,
            prob=settings['prob'], threshold=settings['threshold_px'], maxIters=settings['maxIters'])
        if essential is None or mask is None:
            out['status'] = 'NO_EVIDENCE_NO_ESSENTIAL'
            return out, arrays
        essential = np.asarray(essential, dtype=np.float64)
        if essential.ndim != 2 or essential.shape[1] != 3 or essential.shape[0] % 3 or not 3 <= essential.shape[0] <= 30 or not np.isfinite(essential).all():
            out['status'] = 'NO_EVIDENCE_INVALID_ESSENTIAL'
            return out, arrays
        em = np.asarray(mask, dtype=np.uint8).reshape(-1)
        assert len(em) == n
        em = (em != 0).astype(np.uint8)
        arrays.update(E=essential, essential_mask=em)
        out['essential_inliers'] = int(em.sum())
        if out['essential_inliers'] < settings['minimum_matches']:
            out['status'] = 'NO_EVIDENCE_ESSENTIAL_SUPPORT'
            return out, arrays
        best = None
        for index in range(essential.shape[0] // 3):
            count, rotation, translation, cm = cv2.recoverPose(essential[index * 3:index * 3 + 3],
                first, second, cameraMatrix=k, mask=em.reshape(-1, 1).copy())
            cm = (np.asarray(cm).reshape(-1) != 0).astype(np.uint8)
            assert len(cm) == n and int(cm.sum()) == int(count) and np.all(cm <= em)
            out['candidate_counts'].append(int(count))
            if best is None or count > best[0]:
                best = (int(count), rotation, translation.reshape(3), cm, index)
        count, rotation, translation, cm, index = best
        out.update(cheirality_inliers=count, selected_essential_index=index)
        arrays['cheirality_mask'] = cm
        tol = settings['rotation_validity_tolerance']
        norm = float(np.linalg.norm(translation))
        if not np.isfinite(rotation).all() or not np.isfinite(translation).all() or norm <= 0 or np.linalg.norm(rotation.T @ rotation - np.eye(3), ord=np.inf) > tol or abs(np.linalg.det(rotation) - 1) > tol:
            out['status'] = 'NO_EVIDENCE_INVALID_POSE'
        elif count < settings['minimum_matches']:
            out['status'] = 'NO_EVIDENCE_CHEIRALITY_SUPPORT'
        else:
            out.update(status='POSE', R_i_to_j=rotation.tolist(), unit_t_i_to_j=(translation / norm).tolist())
        return out, arrays
    except cv2.error as exc:
        out.update(status='NO_EVIDENCE_SOLVER_ERROR', solver_error=str(exc)[:800])
        return out, arrays


def angles(np, rotation, translation, reference, epsilon):
    delta = rotation @ reference[:3, :3].T
    sine = np.linalg.norm([delta[2, 1] - delta[1, 2], delta[0, 2] - delta[2, 0], delta[1, 0] - delta[0, 1]]) / 2
    cosine = (float(np.trace(delta)) - 1) / 2
    r = math.degrees(math.atan2(float(sine), cosine))
    norm = float(np.linalg.norm(reference[:3, 3]))
    t = None if norm <= epsilon else math.degrees(math.acos(float(np.clip(np.dot(translation, reference[:3, 3]) / norm, -1, 1))))
    return r, t


def seal_directory(directory, filename='SEAL.json'):
    entries = []
    for p in sorted(directory.rglob('*')):
        if p.is_file() and p.name != filename:
            entries.append({'path': p.relative_to(directory).as_posix(), 'bytes': p.stat().st_size, 'sha256': sha(p)})
    save(directory / filename, {'sealed_utc': stamp(), 'files': entries})


def verify_seal(directory):
    obj = load(directory / 'SEAL.json')
    for item in obj['files']:
        p = directory / item['path']
        assert p.resolve().is_relative_to(directory.resolve())
        assert p.stat().st_size == item['bytes'] and sha(p) == item['sha256'], str(p)
    return obj
