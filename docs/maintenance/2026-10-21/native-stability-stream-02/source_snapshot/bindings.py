"""Source-only original-binding verification; never opens dataset pose/GT files."""
import hashlib, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent
OUT = ROOT.parents[1] / 'outputs/native_stability_stream_20261021'
BANK = ROOT.parents[1] / 'outputs/native_stability_control_20261021/frontend'
S1 = Path('/mnt/e/githouse/RAP-main/docs/maintenance/2026-10-20/raw-input-contract-01')
P0 = Path('/mnt/e/githouse/RAP-main/docs/maintenance/2026-10-21/runtime-overlap-01')


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as source:
        for block in iter(lambda: source.read(2**20), b''):
            h.update(block)
    return h.hexdigest()


def save(path, value):
    with path.open('x') as target:
        json.dump(value, target, separators=(',', ':'), allow_nan=False)


def freeze_originals():
    original = {}
    manifests = [S1 / name for name in ('freeze.json','VARIANT02_FREEZE.json','VARIANT03_FREEZE.json',
        'S1_EXECUTION_FREEZE.json','GUARD05_FREEZE.json','GUARD06_FREEZE.json')]
    manifests += [P0 / 'EXECUTION_FREEZE.json', P0 / 'EXECUTION02_FREEZE.json']
    for manifest in manifests:
        for name, expected in read(manifest)['files'].items():
            p = Path(name)
            if p.suffix in {'.py','.so'} or (p.suffix == '.json' and 'config' in p.name):
                if name in original:
                    assert original[name] == expected.lower(), 'conflicting original binding:' + name
                original[name] = expected.lower()
    original.update({str(p): sha(p) for p in manifests})
    for p in [S1/'config_G.json', S1/'original_prepared_reference.json', S1/'legacy_f32_correction.py']:
        if str(p) not in original:
            original[str(p)] = sha(p)
    for name, expected in original.items():
        assert sha(name) == expected, 'original_source_mismatch:' + name
    save(OUT / 'INPUT_BINDINGS.json', dict(files=original, raw_or_GT_opened=False,
         original_manifests={str(p):sha(p) for p in manifests}))


def verify_originals():
    for name, expected in read(OUT/'INPUT_BINDINGS.json')['files'].items():
        assert sha(name) == expected, 'original_source_mismatch:' + name


def core():
    sys.path.insert(0, '/mnt/e/githouse/RAP-main/scripts/maintenance')
    import overlap_core02
    return overlap_core02
