"""Cold standard-codec integration, with the unchanged exact read gate."""
import codecs
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import baseline_lib as lib

OUT = lib.ROOT / 'runtime02/probe'
try:
    lib.verify_freeze('prediction')
    extra = lib.load(lib.ROOT / 'RUNTIME02_FREEZE.json')
    for item in extra['files']:
        assert lib.sha(lib.ROOT / item['path']) == item['sha256']
    cv2, np = lib.runtime()
    for encoding in ('ascii', 'cp437', 'utf-8', 'latin-1'):
        codecs.lookup(encoding)
    cache = lib.ROOT / 'controls/synthetic_cache.npz'
    calibration = lib.ROOT / 'runtime02/synthetic_calib.txt'
    lib.read_gate([cache, calibration], OUT)
    k = lib.camera(np, calibration)
    assert np.array_equal(k, [[700., 0., 620.], [0., 700., 180.], [0., 0., 1.]])
    with np.load(cache, allow_pickle=False) as data:
        xy, descriptors = data['xy'], data['descriptors']
        assert xy.shape == (120, 2) and descriptors.shape == (8, 128)
    with (OUT / 'roundtrip.npz').open('xb') as handle:
        np.savez(handle, xy=xy, descriptors=descriptors)
    denied = False
    try:
        (lib.ROOT / 'EVALUATION_INPUTS.json').read_bytes()
    except PermissionError:
        denied = True
    assert denied
    lib.complete(OUT, {'cold_codec_camera_NPZ_IO': 'PASS', 'reference_binding_denied': True,
        'actual_image_or_feature_reads': 0, 'supplied_reference_reads': 0,
        'RANSAC_recoverPose_or_refit_calls': 0})
    print('Cold integration PASS; exact read gate retained')
except BaseException as exc:
    lib.failure(OUT, exc)
    raise
