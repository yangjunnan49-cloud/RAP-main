"""All 200 ordinary camera poses, sealed before any supplied-reference read."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import baseline_lib as lib
import refine_lib

extra = lib.load(lib.ROOT / 'RUNTIME02_FREEZE.json')
for item in extra['files']:
    assert lib.sha(lib.ROOT / item['path']) == item['sha256']

OUT = lib.ROOT / 'runtime02/predict'
try:
    frozen = lib.verify_freeze('prediction')
    lib.verify_seal(lib.ROOT / 'controls')
    lib.verify_seal(lib.ROOT / 'features')
    feature_seal_sha = lib.sha(lib.ROOT / 'features/SEAL.json')
    assert lib.load(lib.ROOT / 'features/RESULT.json')['passed']
    inputs = lib.load(lib.ROOT / 'PREDICTION_INPUTS.json')
    method = lib.load(lib.ROOT / 'METHOD.json')
    index = lib.load(lib.ROOT / 'features/INDEX.json')
    cv2, np = lib.runtime()
    import codecs
    for encoding in ('ascii', 'cp437', 'utf-8', 'latin-1'):
        codecs.lookup(encoding)
    cache = {(e['sequence'], e['frame']): lib.ROOT / 'features' / e['cache'] for e in index}
    allowed = list(cache.values()) + [e['path'] for e in inputs['calibrations']]
    lib.read_gate(allowed, OUT)
    cameras = {}
    for e in inputs['calibrations']:
        assert lib.sha(e['path']) == e['sha256']
        cameras[e['sequence']] = lib.camera(np, e['path'])
    predictions = []
    for pair in inputs['pairs']:
        a = cache[(pair['sequence'], pair['source_i'].zfill(6))]
        b = cache[(pair['sequence'], pair['source_j'].zfill(6))]
        with np.load(a, allow_pickle=False) as data:
            ax, ad = data['xy'], data['descriptors']
        with np.load(b, allow_pickle=False) as data:
            bx, bd = data['xy'], data['descriptors']
        indices = lib.mutual_matches(cv2, np, ad, bd, method['ratio'])
        first = np.ascontiguousarray(ax[indices[:, 0]])
        second = np.ascontiguousarray(bx[indices[:, 1]])
        result, arrays = refine_lib.estimate(cv2, np, first, second, cameras[pair['sequence']], method, pair['key'])
        with (OUT / (pair['key'] + '.npz')).open('xb') as handle:
            np.savez(handle, indices=indices, first=first, second=second, **arrays)
        predictions.append({**pair, **result, 'evidence': pair['key'] + '.npz'})
        if len(predictions) % 50 == 0:
            print('predictions %d/200' % len(predictions), flush=True)
    assert len(predictions) == 200
    lib.save(OUT / 'PREDICTIONS.json', predictions)
    lib.complete(OUT, {'pairs': 200, 'poses': sum(p['status'] == 'POSE' for p in predictions),
         'source_freeze_sha256': frozen, 'reference_or_label_payload_reads': 0,
         'feature_seal_sha256': feature_seal_sha,
         'threads': cv2.getNumThreads(), 'OpenCL': cv2.ocl.useOpenCL()})
    print('predictions complete 200/200', flush=True)
except BaseException as exc:
    lib.failure(OUT, exc)
    raise
