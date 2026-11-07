"""Cold standard-codec integration, with the unchanged exact read gate."""
import codecs
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import baseline_lib as lib
import refine_lib

OUT = lib.ROOT / 'runtime03/probe'
try:
    lib.verify_freeze('prediction')
    extra = lib.load(lib.ROOT / 'RUNTIME03_FREEZE.json')
    for item in extra['files']:
        assert lib.sha(lib.ROOT / item['path']) == item['sha256']
    cv2, np = lib.runtime()
    import numpy.ma
    for encoding in ('ascii', 'cp437', 'utf-8', 'latin-1'):
        codecs.lookup(encoding)
    cache = lib.ROOT / 'controls/synthetic_cache.npz'
    calibration = lib.ROOT / 'runtime02/synthetic_calib.txt'
    extra_method = lib.load(lib.ROOT / 'METHOD.json')
    lib.read_gate([cache, calibration], OUT)
    k = lib.camera(np, calibration)
    assert np.array_equal(k, [[700., 0., 620.], [0., 700., 180.], [0., 0., 1.]])
    with np.load(cache, allow_pickle=False) as data:
        xy, descriptors = data['xy'], data['descriptors']
        assert xy.shape == (120, 2) and descriptors.shape == (8, 128)
    with (OUT / 'roundtrip.npz').open('xb') as handle:
        np.savez(handle, xy=xy, descriptors=descriptors)
    da = np.eye(8, 128, dtype=np.float32) * 10
    assert len(lib.mutual_matches(cv2, np, da, da + np.float32(.001), .75)) == 8
    xyz = np.asarray([[x, y, z] for z in (8., 12., 18.) for y in (-1., 0., 1.) for x in (-2., -1., 0., 1., 2.)])
    angle = np.deg2rad(7.)
    rotation = np.array([[np.cos(angle), 0., np.sin(angle)], [0., 1., 0.], [-np.sin(angle), 0., np.cos(angle)]])
    translation = np.array([1.2, .15, .3])
    p1 = xyz @ k.T
    p2 = (xyz @ rotation.T + translation) @ k.T
    method = extra_method
    result, evidence = refine_lib.estimate(cv2, np, np.ascontiguousarray(p1[:, :2]/p1[:, 2:3]), np.ascontiguousarray(p2[:, :2]/p2[:, 2:3]), k, method, 'cold_full_path')
    reference = np.eye(4)
    reference[:3, :3], reference[:3, 3] = rotation, translation
    assert result['status'] == 'POSE'
    errors = lib.angles(np, np.asarray(result['R_i_to_j']), np.asarray(result['unit_t_i_to_j']), reference, 1e-9)
    assert errors[0] < .1 and errors[1] < .5
    denied = False
    try:
        (lib.ROOT / 'EVALUATION_INPUTS.json').read_bytes()
    except PermissionError:
        denied = True
    assert denied
    lib.complete(OUT, {'cold_codec_camera_NPZ_IO': 'PASS', 'reference_binding_denied': True,
        'actual_image_or_feature_reads': 0, 'supplied_reference_reads': 0,
        'synthetic_complete_pose_path': 'PASS', 'real_pose_calls': 0})
    print('Cold integration PASS; exact read gate retained')
except BaseException as exc:
    lib.failure(OUT, exc)
    raise
