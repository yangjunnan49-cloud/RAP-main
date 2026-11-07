"""Owner-authorized two-object arXiv transport, no retries or other links."""
import ctypes
import hashlib
import http.client
import json
import os
import ssl
import sys
import time
import traceback
import uuid
from pathlib import Path
from urllib.parse import urljoin, urlsplit

ROOT = Path(__file__).resolve().parent
OUT = Path(sys.argv[1])
START = time.monotonic()
ROWS = []
TOTAL = 0
PEAK_CAP = 268435456
TOTAL_CAP = 8650752
DEADLINE = 90.0


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().lower()


def write(name, value):
    path = OUT / name
    temp = OUT / (name + '.tmp-' + uuid.uuid4().hex)
    with temp.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
    os.rename(temp, path)


def remaining():
    left = DEADLINE - (time.monotonic() - START)
    if left <= 0:
        raise TimeoutError('worker_deadline')
    return left


def peak():
    class PMC(ctypes.Structure):
        _fields_ = [('cb', ctypes.c_ulong), ('PageFaultCount', ctypes.c_ulong)] + [
            (name, ctypes.c_size_t) for name in (
                'PeakWorkingSetSize', 'WorkingSetSize', 'QuotaPeakPagedPoolUsage',
                'QuotaPagedPoolUsage', 'QuotaPeakNonPagedPoolUsage',
                'QuotaNonPagedPoolUsage', 'PagefileUsage', 'PeakPagefileUsage')]
    record = PMC()
    record.cb = ctypes.sizeof(record)
    ctypes.windll.kernel32.GetCurrentProcess.restype = ctypes.c_void_p
    ctypes.windll.psapi.GetProcessMemoryInfo.argtypes = [
        ctypes.c_void_p, ctypes.POINTER(PMC), ctypes.c_ulong]
    if not ctypes.windll.psapi.GetProcessMemoryInfo(
            ctypes.windll.kernel32.GetCurrentProcess(), ctypes.byref(record), record.cb):
        raise OSError('GetProcessMemoryInfo')
    return int(record.PeakWorkingSetSize)


def lease(sequence):
    token = uuid.uuid4().hex
    name = f'lease-{sequence:02d}-{token}'
    write(name + '.request.json', dict(nonce=token, sequence=sequence))
    began = time.monotonic()
    reply = OUT / (name + '.response.json')
    while not reply.exists():
        remaining()
        if time.monotonic() - began > 2:
            raise TimeoutError('fresh_host_lease_missing')
        time.sleep(.02)
    record = json.loads(reply.read_text(encoding='utf-8'))
    assert record['nonce'] == token and record['sequence'] == sequence
    assert record['headroom_bytes'] >= 12884901888
    assert record['query_seconds'] <= 2 and time.monotonic() - began <= 2
    assert peak() <= PEAK_CAP


def checked_url(url, role):
    parsed = urlsplit(url)
    paths = {'abstract': {'/abs/2310.16542'},
             'paper': {'/pdf/2310.16542.pdf', '/pdf/2310.16542'}}[role]
    if (parsed.scheme != 'https' or parsed.hostname != 'arxiv.org'
            or parsed.port not in (None, 443) or parsed.username is not None
            or parsed.password is not None or parsed.query or parsed.fragment
            or parsed.path not in paths):
        raise PermissionError('URL_outside_exact_authorized_object')
    return parsed


ok = False
error = None
admitted = []
try:
    freeze = json.loads((ROOT / 'SOURCE_FREEZE.json').read_text(encoding='utf-8'))
    for name, digest in freeze['files'].items():
        assert sha(ROOT / name) == digest
    assert sha(Path(sys.executable)) == freeze['python_sha256']
    plan = json.loads((ROOT / 'REQUEST_PLAN.json').read_text(encoding='utf-8'))
    assert plan['max_total_requests_including_redirects'] == 4
    assert plan['max_application_delivered_body_bytes_all_responses'] == TOTAL_CAP
    assert plan['worker_wall_seconds'] == DEADLINE
    assert plan['worker_peak_working_set_bytes'] == PEAK_CAP
    for role, obj in zip(('abstract', 'paper'), plan['objects']):
        current = obj['url']
        object_bytes = 0
        while True:
            if len(ROWS) >= 4:
                raise ValueError('total_request_cap')
            parsed = checked_url(current, role)
            remaining()
            index = len(ROWS)
            lease(index)
            request_headers = {
                'User-Agent': 'RAP-source-audit/1.0',
                'Accept': ','.join(obj['accepted_mime']),
                'Accept-Encoding': 'identity', 'Connection': 'close'}
            row = dict(index=index, role=role, url=current, method='GET',
                       request_headers=request_headers, body_bytes=0, EOF=False)
            ROWS.append(row)
            write(f'{index:02d}.request.json', row.copy())
            conn = http.client.HTTPSConnection(
                parsed.hostname, port=443, timeout=min(10., remaining()),
                context=ssl.create_default_context())
            response = None
            redirect_to = None
            try:
                conn.request('GET', parsed.path, headers=request_headers)
                response = conn.getresponse()
                row.update(status=response.status, reason=response.reason,
                           response_headers=response.getheaders())
                write(f'{index:02d}.headers.json', dict(
                    status=response.status, reason=response.reason,
                    headers=response.getheaders()))
                encoding = (response.getheader('Content-Encoding') or 'identity').strip().lower()
                if encoding not in ('', 'identity'):
                    raise ValueError('nonidentity_content_encoding')
                mime = (response.getheader('Content-Type') or '').split(';', 1)[0].strip().lower()
                redirect = response.status in (301, 302, 303, 307, 308)
                if redirect:
                    if mime not in ('', 'text/html', 'text/plain', 'application/xhtml+xml'):
                        raise ValueError('unexpected_redirect_mime')
                    location = response.getheader('Location')
                    if not location:
                        raise ValueError('redirect_without_location')
                    redirect_to = urljoin(current, location)
                    checked_url(redirect_to, role)
                    row['redirect_to'] = redirect_to
                elif response.status != 200 or mime not in obj['accepted_mime']:
                    raise ValueError('final_status_or_MIME_not_admitted')
                declared = response.getheader('Content-Length')
                allowance = min(TOTAL_CAP - TOTAL,
                                obj['delivered_body_cap_bytes'] - object_bytes)
                if declared is not None:
                    if not declared.isdecimal() or int(declared) > allowance:
                        raise ValueError('declared_body_exceeds_object_or_total_cap')
                body = OUT / f'{index:02d}.body'
                row['body_file'] = body.name
                with body.open('xb') as stream:
                    while True:
                        remaining()
                        if response.length == 0:
                            row['EOF'] = True
                            break
                        allowance = min(TOTAL_CAP - TOTAL,
                                        obj['delivered_body_cap_bytes'] - object_bytes)
                        if allowance <= 0:
                            raise ValueError('cap_without_confirmed_EOF')
                        if conn.sock is not None:
                            conn.sock.settimeout(min(10., remaining()))
                        try:
                            block = response.read(min(8192, allowance))
                        except http.client.IncompleteRead as failure:
                            block = failure.partial
                            assert len(block) <= allowance
                            stream.write(block)
                            TOTAL += len(block)
                            object_bytes += len(block)
                            row['body_bytes'] += len(block)
                            raise
                        if not block:
                            row['EOF'] = True
                            break
                        stream.write(block)
                        TOTAL += len(block)
                        object_bytes += len(block)
                        row['body_bytes'] += len(block)
                        if peak() > PEAK_CAP:
                            raise MemoryError('native_peak_cap')
                row['body_sha256'] = sha(body)
                if declared is not None and row['body_bytes'] != int(declared):
                    raise ValueError('declared_length_not_complete')
                if not redirect:
                    assert row['EOF']
                    if role == 'paper' and body.read_bytes()[:5] != b'%PDF-':
                        raise ValueError('PDF_signature_missing')
                    if role == 'abstract':
                        body.read_text(encoding='utf-8')
                    admitted.append(dict(role=role, url=current, body_file=body.name,
                                         bytes=row['body_bytes'], sha256=row['body_sha256']))
            finally:
                if response is not None:
                    response.close()
                conn.close()
                if 'body_file' in row and (OUT / row['body_file']).exists():
                    row['body_sha256'] = sha(OUT / row['body_file'])
                write(f'{index:02d}.receipt.json', row)
            if redirect_to is None:
                break
            current = redirect_to
    assert len(admitted) == 2
    assert sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file()) < 16777216
    ok = True
    write('RESULTS.json', dict(passed=True, objects=admitted, requests=len(ROWS),
        cumulative_delivered_body_bytes=TOTAL, retries=0, other_links_followed=0,
        credentials_or_cookies_sent=False, application_bytes_not_wire_or_TLS_bytes=True))
except BaseException as caught:
    error = repr(caught)
    write('FAILURE.json', dict(error=error, traceback=traceback.format_exc(),
        attempted_requests=len(ROWS), cumulative_delivered_body_bytes=TOTAL,
        complete_objects=admitted, retry_allowed=False))
    raise
finally:
    write('WORKER_EXIT.json', dict(success=ok, error=error,
        elapsed_seconds=time.monotonic() - START, peak_working_set_bytes=peak(),
        cumulative_delivered_body_bytes=TOTAL, requests=len(ROWS), all_request_rows=ROWS))
