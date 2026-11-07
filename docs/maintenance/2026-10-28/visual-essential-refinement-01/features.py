"""All 273 measured images; source-allowlisted, reference-free SIFT cache."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import baseline_lib as lib

OUT = lib.ROOT / 'features'
try:
    frozen = lib.verify_freeze('prediction')
    lib.verify_seal(lib.ROOT / 'controls')
    assert lib.load(lib.ROOT / 'controls/RESULT.json')['passed']
    inputs = lib.load(lib.ROOT / 'PREDICTION_INPUTS.json')
    method = lib.load(lib.ROOT / 'METHOD.json')
    cv2, np = lib.runtime()
    for item in inputs['runtime_files']:
        assert lib.sha(item['path']) == item['sha256']
    lib.read_gate([r['path'] for r in inputs['images']], OUT)
    sift = cv2.SIFT_create(**method['sift'])
    entries = []
    for row in inputs['images']:
        path = Path(row['path'])
        data = path.read_bytes()
        assert len(data) == row['bytes'] and lib.hashlib.sha256(data).hexdigest() == row['sha256']
        image = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_UNCHANGED)
        assert image is not None and image.dtype == np.uint8 and image.shape == (row['height'], row['width'])
        points, descriptors = sift.detectAndCompute(image, None)
        descriptors = np.empty((0, 128), dtype=np.float32) if descriptors is None else descriptors
        xy = np.asarray([p.pt for p in points], dtype=np.float64).reshape(-1, 2)
        kp = np.asarray([[*p.pt, p.size, p.angle, p.response, p.octave, p.class_id] for p in points], dtype=np.float64).reshape(-1, 7)
        assert descriptors.shape == (len(points), 128) and descriptors.dtype == np.float32 and np.isfinite(descriptors).all() and np.isfinite(kp).all()
        name = row['sequence'] + '_' + row['frame'] + '.npz'
        with (OUT / name).open('xb') as handle:
            np.savez(handle, xy=xy, keypoints=kp, descriptors=descriptors)
        entries.append({'sequence': row['sequence'], 'frame': row['frame'], 'cache': name,
                        'keypoints': len(points), 'image_sha256': row['sha256']})
        if len(entries) % 50 == 0:
            print('features %d/273' % len(entries), flush=True)
    assert len(entries) == 273
    lib.save(OUT / 'INDEX.json', entries)
    lib.complete(OUT, {'images': 273, 'total_keypoints': sum(e['keypoints'] for e in entries),
         'source_freeze_sha256': frozen, 'reference_or_label_payload_reads': 0,
         'cv2_version': cv2.__version__, 'numpy_version': np.__version__, 'threads': cv2.getNumThreads(), 'OpenCL': cv2.ocl.useOpenCL()})
    print('features complete 273/273', flush=True)
except BaseException as exc:
    lib.failure(OUT, exc)
    raise
