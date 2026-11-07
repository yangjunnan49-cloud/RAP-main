"""Cooperative lease and declared reads for this new CPU-only source scope."""
import codecs, datetime, hashlib, json, os, sys, time, uuid, zipfile, io
from pathlib import Path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import winapi
METHOD = json.loads((ROOT / 'METHOD.json').read_text(encoding='utf-8-sig'))
sys.path.insert(0, METHOD['cv2_path'])
import numpy as np
import numpy.linalg, numpy.ma, numpy.random, numpy.lib.format
import cv2
cv2.setNumThreads(1)
cv2.ocl.setUseOpenCL(False)
for encoding in ('ascii', 'utf-8', 'latin-1', 'cp437'): codecs.lookup(encoding)
START = time.monotonic()
SERIAL = 0
LAST = 0.0
READS = set()

def read(path): return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def stamp(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(path, value):
    with Path(path).open('x', encoding='utf-8') as f:
        json.dump(value, f, indent=2, allow_nan=False)
def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1048576), b''): h.update(block)
    return h.hexdigest()
def gate(paths, out):
    allowed = {os.path.normcase(str(Path(p).resolve())) for p in paths}
    out = Path(out).resolve()
    def audit(event, args):
        if event.startswith(('socket.', 'subprocess.', 'os.system', 'os.exec', 'os.spawn')):
            raise PermissionError('SRA1 network/subprocess denied')
        if event != 'open' or isinstance(args[0], int): return
        p = Path(os.fsdecode(args[0])).resolve()
        mode, flags = args[1:3]
        writing = any(c in mode for c in 'wax+') if isinstance(mode, str) else bool(flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
        if writing:
            if not p.is_relative_to(out): raise PermissionError('SRA1 write outside output')
        elif os.path.normcase(str(p)) not in allowed and not p.is_relative_to(out):
            raise PermissionError('SRA1 undeclared read: ' + str(p))
        else: READS.add(str(p))
    sys.addaudithook(audit)
def lease(out, force=False):
    global SERIAL, LAST
    if not force and time.monotonic() - LAST < .25: return
    SERIAL += 1
    nonce = uuid.uuid4().hex
    temporary = Path(out) / 'REQUEST_CURRENT.tmp'
    save(temporary, dict(serial=SERIAL, nonce=nonce, utc=stamp()))
    os.replace(temporary, Path(out) / 'REQUEST_CURRENT.json')
    response = Path(out) / f'{SERIAL:06d}_{nonce}_response.json'
    start = time.monotonic()
    while not response.exists():
        if time.monotonic() - start > 2: raise RuntimeError('external nonce timeout')
        time.sleep(.01)
    grant = read(response)
    assert grant['serial'] == SERIAL and grant['nonce'] == nonce and grant['passed']
    assert grant['headroom_bytes'] >= METHOD['headroom_bytes'] and grant['query_seconds'] <= 2
    assert (datetime.datetime.now(datetime.timezone.utc) - datetime.datetime.fromisoformat(grant['utc'])).total_seconds() < 2
    LAST = time.monotonic()
def complete(out, **extra):
    save(Path(out) / 'RESULT.json', dict(passed=True, utc=stamp(), elapsed_seconds=time.monotonic()-START, child_lifetime_peak_bytes=winapi.peak(), read_paths=sorted(READS), **extra))
