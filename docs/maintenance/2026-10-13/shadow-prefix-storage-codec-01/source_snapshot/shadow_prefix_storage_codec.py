"""LPC0 immutable-artifact lossless encoding prerequisite; no neural imports."""
import hashlib, json, resource, signal, subprocess, sys, time, traceback, zlib
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
OLD = ROOT / 'docs/maintenance/2026-10-13/shadow-conditioned-fit-pilot-01'
BASE = ROOT / 'docs/maintenance/2026-10-13/shadow-prefix-storage-codec-01'
SUP = BASE / 'supervision'
START = None

def read(q): return json.loads(Path(q).read_text(encoding='utf-8-sig'))
def digest(b): return hashlib.sha256(b).hexdigest()
def sha(q):
    h = hashlib.sha256()
    with Path(q).open('rb') as f:
        for block in iter(lambda: f.read(1048576), b''): h.update(block)
    return h.hexdigest()
def save(q, value):
    with Path(q).open('x', encoding='utf-8') as f:
        json.dump(value, f, indent=2, allow_nan=False); f.write('\n')
def repositories():
    out = {}
    for name, q in [('main', ROOT), ('slam', ROOT.parent / 'RAP-SLAM')]:
        def git(*args): return subprocess.check_output(['git', '--no-optional-locks', '-C', str(q), *args], text=True).strip()
        out[name] = dict(head=git('rev-parse', 'HEAD'), branch=git('branch', '--show-current'), tracked_status=git('status', '--short', '--untracked-files=no').splitlines())
    return out
def seal(folder, target):
    files = {str(q.relative_to(folder)): sha(q) for q in sorted(folder.rglob('*')) if q.is_file()}
    save(BASE / target, dict(files=files, entries=len(files), freeze_sha256=sha(BASE / 'freeze.json')))
def check_seal(folder, target):
    s = read(BASE / target); assert s['freeze_sha256'] == sha(BASE / 'freeze.json')
    assert s['files'] == {str(q.relative_to(folder)): sha(q) for q in sorted(folder.rglob('*')) if q.is_file()}
def freeze():
    prior = read(OLD / 'freeze.json'); files = dict(prior['files'])
    for folder, name, count in [(OLD, 'AVAILABLE_DELIVERY_SEAL.json', 576), (ROOT / 'docs/maintenance/2026-10-13/continuation-handoff-02', 'DELIVERY_SEAL.json', 10), (ROOT / 'docs/maintenance/2026-10-13/shadow-storage-capacity-review-01', 'DELIVERY_SEAL.json', 5)]:
        s = read(folder / name); assert len(s['files']) == count
        for row in s['files']:
            q = (folder / row['path'].replace(chr(92), '/')).resolve(); assert folder.resolve() in q.parents
            assert sha(q) == row['sha256']; files[str(q)] = row['sha256']
        files[str(folder / name)] = sha(folder / name)
    sources = [BASE / 'PROTOCOL.md', BASE / 'OWNER_SCOPE.md', Path(__file__), Path(__file__).with_name('validate_shadow_prefix_codec.py'), Path(__file__).with_name('invoke_mgr_supervised_wsl.ps1')]
    snap = BASE / 'source_snapshot'; snap.mkdir()
    for q in sources:
        files[str(q)] = sha(q)
        if q.suffix in ('.py', '.ps1'): (snap / q.name).write_bytes(q.read_bytes())
    for q, h in files.items(): assert sha(q) == h, q
    assert repositories() == prior['repositories']
    assert (OLD / 'INCOMPLETE').exists() and not (OLD / 'prediction_seal.json').exists()
    save(BASE / 'freeze.json', dict(files=files, repositories=prior['repositories'], source_available_entries=576, cap_seconds=600, cap_RSS_bytes=2*2**30, cap_GPU_bytes=0, cap_artifact_bytes=512*2**20, source_cases=dict(U=17, V=17, P=3), student_prefixes=100, neural_or_GT_execution=False))
    (BASE / 'INCOMPLETE').write_text('LPC0 lossless artifact encoding and independent reconstruction pending.\n', encoding='utf-8')
    print('LPC0 frozen', len(files), 'identities', flush=True)
def verify():
    f = read(BASE / 'freeze.json')
    for q, h in f['files'].items(): assert sha(q) == h, q
    assert repositories() == f['repositories']
    assert (OLD / 'INCOMPLETE').exists() and not (OLD / 'prediction_seal.json').exists()
def encode():
    verify()
    import numpy as np
    import zipfile
    folder = BASE / 'encoded'; folder.mkdir(); rows = []; fixture_rows = []
    def encode_raw(target, base, name):
        assert len(target) == len(base) and len(target) % 4 == 0
        a = np.frombuffer(target, dtype='<u4'); b = np.frombuffer(base, dtype='<u4')
        delta = np.bitwise_xor(a, b).tobytes()
        if target == base: return dict(representation='source_base_alias', encoded_path=None, encoded_bytes=0, raw_delta_sha256=digest(delta))
        packed = zlib.compress(delta, level=6)
        q = folder / (name + '.xor.zlib')
        with q.open('xb') as out: out.write(packed)
        return dict(representation='uint32_XOR_zlib6', encoded_path=str(q.relative_to(BASE)), encoded_bytes=len(packed), encoded_sha256=sha(q), raw_delta_sha256=digest(delta))
    # Adversarial bit patterns, including signed zero, subnormals and NaN payloads.
    words = np.array([0, 0x80000000, 1, 0x80000001, 0x7f800000, 0xff800000, 0x7fc00001, 0x7f800001, 0x3f800000, 0xffffffff], dtype='<u4')
    for i in range(4):
        target = (words if i == 0 else np.roll(words, i)).tobytes(); base = words.tobytes()
        q = folder / f'fixture_{i}.target.raw'; q.write_bytes(target)
        qb = folder / f'fixture_{i}.base.raw'; qb.write_bytes(base)
        fixture_rows.append(dict(name=f'fixture_{i}', target_path=str(q.relative_to(BASE)), base_path=str(qb.relative_to(BASE)), target_sha256=digest(target), base_sha256=digest(base), **encode_raw(target, base, f'fixture_{i}')))
    for case in sorted((OLD / 'predictions').iterdir()):
        if not case.is_dir() or case.name.split('_')[0] not in ('V', 'P'): continue
        arm, noise = case.name.split('_', 1)
        for step in range(5):
            q = case / f'step_{step}.npz'; qb = OLD / 'predictions' / ('U_' + noise) / q.name
            with np.load(q, allow_pickle=False) as z: a = z['prefix'].copy()
            with np.load(qb, allow_pickle=False) as z: b = z['prefix'].copy()
            assert a.shape == b.shape == (3000, 512) and a.dtype == b.dtype == np.dtype('<f4') and a.flags.c_contiguous and b.flags.c_contiguous
            assert np.isfinite(a).all() and np.isfinite(b).all()
            raw, br = a.tobytes(), b.tobytes()
            with zipfile.ZipFile(q) as z: member = z.read('prefix.npy'); compressed = z.getinfo('prefix.npy').compress_size
            with zipfile.ZipFile(qb) as z: bm = z.read('prefix.npy')
            rows.append(dict(arm=arm, noise=noise, step=step, source_path=str(q), source_sha256=sha(q), base_path=str(qb), base_sha256=sha(qb), source_member_sha256=digest(member), base_member_sha256=digest(bm), source_raw_sha256=digest(raw), base_raw_sha256=digest(br), dtype='<f4', byte_order='little', order='C', shape=[3000,512], raw_bytes=len(raw), baseline_member_compressed_bytes=compressed, **encode_raw(raw, br, f'{case.name}_step_{step}')))
            cap()
        print('LPC0 encoded', case.name, flush=True)
    assert len(rows) == 100
    save(folder / 'manifest.json', dict(records=rows, fixtures=fixture_rows, complete_available_student_prefixes=100, old_partial_cases_not_scientifically_admitted=True, no_missing_cases_generated=True, no_model_reference_metrics=True))
    seal(folder, 'encoded_seal.json'); verify()
def usage():
    return dict(wall_seconds=time.monotonic()-START, peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024, peak_GPU_allocated_bytes=0, peak_GPU_reserved_bytes=0, artifact_bytes=sum(q.stat().st_size for q in BASE.rglob('*') if q.is_file()), imports_included=True, optimizer_calls=0, neural_calls=0)
def cap():
    f = read(BASE / 'freeze.json') if (BASE / 'freeze.json').exists() else dict(cap_RSS_bytes=2*2**30, cap_artifact_bytes=512*2**20)
    z = usage(); assert z['peak_RSS_bytes'] <= f['cap_RSS_bytes'] and z['artifact_bytes'] <= f['cap_artifact_bytes'], z
    if (SUP / 'host_latest.json').exists(): assert read(SUP / 'host_latest.json')['headroom_bytes'] >= 4*2**30
def run(stage):
    global START
    START = time.monotonic(); used = sum(read(q)['wall_seconds'] for q in SUP.glob('*/child_exit.json')); assert used < 600
    signal.signal(signal.SIGALRM, lambda a,b: (_ for _ in ()).throw(TimeoutError('LPC0 aggregate scientific-child time cap'))); signal.alarm(max(1,int(600-used)))
    ok=False; error=None
    try:
        if stage == 'freeze': freeze()
        elif stage == 'encode': encode()
        elif stage == 'validate':
            import validate_shadow_prefix_codec as v; v.validate()
        else: raise ValueError(stage)
        cap(); ok=True
    except BaseException as ex:
        error=repr(ex); traceback.print_exc(); save(BASE / f'FAILURE_{stage}.json', dict(error=error, **usage()))
    finally:
        signal.alarm(0); save(SUP / stage / 'child_exit.json', dict(success=ok, error=error, full_resource_capture=True, **usage()))
    if not ok: sys.exit(1)
if __name__ == '__main__': sys.modules['shadow_prefix_storage_codec'] = sys.modules[__name__]; run(sys.argv[1])
