"""Metadata, source and input freeze only. No image/reference numeric decode."""
import ast
import datetime as dt
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[3]
DAY = ROOT.parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(name, value):
    with (ROOT / name).open('x', encoding='utf-8') as handle:
        json.dump(value, handle, indent=2, ensure_ascii=True, allow_nan=False)
        handle.write('\n')


def require_sealed(dossier, name):
    seal = json.loads((dossier / 'DELIVERY_SEAL.json').read_text(encoding='utf-8-sig'))
    entry = next(e for e in seal['files'] if e['path'] == name)
    p = dossier / name
    assert p.stat().st_size == entry['bytes'] and digest(p) == entry['sha256']


assert not (ROOT / 'SOURCE_FREEZE.json').exists(), 'No re-freeze'
assert (dt.datetime.now(dt.timezone.utc) - dt.datetime(2026, 10, 28, 6, 48, 18, tzinfo=dt.timezone.utc)).total_seconds() < 1800
for dossier, name in [('camera-frustum-support-01', 'INPUT_BINDING.json'),
        ('camera-frustum-support-01', 'STRATUM_READOUT.json'),
        ('image-packet-verification-01', 'IMAGE_MANIFEST.json'),
        ('vision-runtime-local-01', 'API_RESULT.json')]:
    require_sealed(DAY / dossier, name)
old = REPO / 'AGENTS.md'
with (ROOT / 'AGENTS.before.md').open('xb') as handle:
    handle.write(old.read_bytes())
bind = json.loads((DAY / 'camera-frustum-support-01/INPUT_BINDING.json').read_text())
cohort_path = Path(bind['cohort_path'])
assert digest(cohort_path) == bind['cohort_sha256']
cohort = json.loads(cohort_path.read_text())
image_path = DAY / 'image-packet-verification-01/IMAGE_MANIFEST.json'
assert digest(image_path) == bind['image_manifest_sha256']
images = json.loads(image_path.read_text())
assert len(cohort['pairs']) == 200 and len(images['rows']) == 273
assert len({r['key'] for r in cohort['pairs']}) == 200
image_rows = []
for row in images['rows']:
    p = image_path.parent / row['relative_path']
    assert p.stat().st_size == row['bytes'] and digest(p) == row['sha256']
    image_rows.append({**{k: row[k] for k in ('sequence', 'bytes', 'sha256', 'width', 'height')},
                       'frame': Path(row['member']).stem, 'path': str(p)})
actual = {(r['sequence'], r['frame']) for r in image_rows}
needed = {(r['sequence'], r[field].zfill(6)) for r in cohort['pairs'] for field in ('source_i', 'source_j')}
assert actual == needed and len(actual) == 273
calibrations = []
for seq in ('00', '08'):
    p = image_path.parent / 'metadata' / seq / 'calib.txt'
    association = next(a for a in images['associations'] if a['sequence'] == seq)
    assert digest(p) == association['archive_calib_sha256']
    calibrations.append({'sequence': seq, 'path': str(p), 'bytes': p.stat().st_size, 'sha256': digest(p)})
runtime = DAY / 'vision-runtime-local-01'
api = json.loads((runtime / 'API_RESULT.json').read_text())
assert api['passed'] and api['cv2_version'] == '5.0.0' and api['numpy_version'] == '2.3.5'
runtime_files = []
for name in ('cv2/cv2.pyd', 'cv2/__init__.py', 'cv2/config.py', 'cv2/config-3.py',
             'opencv_python_headless-5.0.0.93.dist-info/METADATA'):
    p = runtime / 'site-packages' / name
    runtime_files.append({'path': str(p), 'bytes': p.stat().st_size, 'sha256': digest(p)})
write('PREDICTION_INPUTS.json', {'pairs': cohort['pairs'], 'images': image_rows,
      'calibrations': calibrations, 'runtime': str(runtime / 'site-packages'),
      'runtime_files': runtime_files, 'cohort_identity_sha256': digest(cohort_path),
      'original_manifest_sha256': digest(image_path),
      'reference_or_label_paths': [], 'selection': 'All 200 ordered pairs; all 273 required images'})
labels = [REPO / 'docs/maintenance/2026-09-14/hl-v2/data-expansion-01/discovery_evaluator.json',
          REPO / 'docs/maintenance/2026-09-14/support-control-01/data/confirmation_evaluator.json']
prior_labels = json.loads((DAY / 'camera-frustum-support-01/STRATUM_READOUT.json').read_text())['source_labels_bound']
label_bindings = []
for p in labels:
    expected = next(e['sha256'] for e in prior_labels if Path(e['path']).resolve() == p.resolve())
    assert digest(p) == expected
    label_bindings.append({'path': str(p), 'bytes': p.stat().st_size, 'sha256': expected})
write('EVALUATION_INPUTS.json', {'poses': bind['poses'], 'labels': label_bindings,
      'pose_payload_decoded_during_preparation': False,
      'reference_hashes_role': 'Prior sealed CF1 hashes; verify again only after prediction seal'})
write('METHOD.json', {'sift': {'nfeatures': 2048, 'nOctaveLayers': 3,
      'contrastThreshold': 0.04, 'edgeThreshold': 10, 'sigma': 1.6},
      'ratio': 0.75, 'minimum_matches': 8, 'prob': 0.999, 'threshold_px': 1.0,
      'maxIters': 2000, 'rotation_validity_tolerance': 1e-6,
      'reference_validity_tolerance': 1e-5, 'reference_translation_epsilon_m': 1e-9,
      'rotation_bins_deg': [5, 10], 'direction_bins_deg': [15, 30],
      'scope_origin_utc': '2026-10-28T06:48:18+00:00', 'whole_scope_seconds': 5400,
      'closure_reserve_seconds': 180, 'dossier_bytes': 1073741824,
      'stage_seconds': {'controls': 60, 'features': 300, 'predict': 300, 'evaluate': 120, 'audit': 180},
      'child_peak_bytes': 1073741824, 'headroom_bytes': 12884901888, 'query_seconds': 2})
entries = []
roles = {'METHOD.json': 'shared', 'baseline_lib.py': 'shared', 'PROTOCOL.md': 'shared',
         'PREDICTION_INPUTS.json': 'prediction', 'EVALUATION_INPUTS.json': 'evaluation',
         'controls.py': 'controls', 'features.py': 'prediction', 'predict.py': 'prediction',
         'evaluate.py': 'evaluation', 'audit.py': 'audit', 'host.ps1': 'host', 'prepare.py': 'preparation'}
for name, role in roles.items():
    p = ROOT / name
    if p.suffix == '.py':
        ast.parse(p.read_text(encoding='utf-8'), filename=name)
    entries.append({'path': name, 'bytes': p.stat().st_size, 'sha256': digest(p), 'role': role})
write('SOURCE_FREEZE.json', {'utc': dt.datetime.now(dt.timezone.utc).isoformat(),
      'files': entries, 'image_payload_decodes': 0, 'pose_payload_decodes': 0,
      'actual_matching_or_solver_calls': 0, 'all_sources_parse': True})
write('PREPARATION_RESULT.json', {'passed': True, 'image_files_hashed': 273,
      'pairs': 200, 'runtime_files_hashed': len(runtime_files),
      'source_freeze_sha256': digest(ROOT / 'SOURCE_FREEZE.json'),
      'old_AGENTS_bytes': old.stat().st_size, 'old_AGENTS_sha256': digest(old),
      'image_or_pose_numeric_decode': False, 'new_training': False})
print('VB1 metadata/source freeze complete; no image/reference numeric decode')
