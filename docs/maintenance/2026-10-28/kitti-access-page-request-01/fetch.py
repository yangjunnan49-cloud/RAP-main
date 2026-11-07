"""Single authorized main-HTML transport; no automatic redirects or retries."""
import ctypes, hashlib, http.client, json, os, ssl, sys, time, traceback, uuid
from pathlib import Path
from urllib.parse import urljoin, urlsplit
ROOT=Path(__file__).resolve().parent
OUT=Path(sys.argv[1]);START=time.monotonic();TOTAL=0;ROWS=[]
CAP=262144;DEADLINE=60.;URL='https://www.cvlibs.net/datasets/kitti/user_login.php'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def write(name,v):
    payload=json.dumps(v,indent=2,allow_nan=False)
    with (OUT/name).open('x',encoding='utf-8') as f:f.write(payload)
def remaining():
    left=DEADLINE-(time.monotonic()-START)
    if left<=0:raise TimeoutError('worker_deadline')
    return left
def peak():
    class PMC(ctypes.Structure):
        _fields_=[('cb',ctypes.c_ulong),('PageFaultCount',ctypes.c_ulong)]+[(n,ctypes.c_size_t) for n in (
            'PeakWorkingSetSize','WorkingSetSize','QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage',
            'QuotaPeakNonPagedPoolUsage','QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage')]
    p=PMC();p.cb=ctypes.sizeof(p)
    ctypes.windll.kernel32.GetCurrentProcess.restype=ctypes.c_void_p
    ctypes.windll.psapi.GetProcessMemoryInfo.argtypes=[ctypes.c_void_p,ctypes.POINTER(PMC),ctypes.c_ulong]
    if not ctypes.windll.psapi.GetProcessMemoryInfo(ctypes.windll.kernel32.GetCurrentProcess(),ctypes.byref(p),p.cb):
        raise OSError('GetProcessMemoryInfo failed')
    return int(p.PeakWorkingSetSize)
def lease(sequence):
    token=uuid.uuid4().hex;name=f'lease-{sequence:02d}-{token}'
    write(name+'.request.json',dict(nonce=token,sequence=sequence))
    began=time.monotonic();reply=OUT/(name+'.response.json')
    while not reply.exists():
        remaining()
        if time.monotonic()-began>2:raise TimeoutError('fresh_host_lease_missing')
        time.sleep(.02)
    r=json.loads(reply.read_text(encoding='utf-8'))
    assert r['nonce']==token and r['sequence']==sequence
    assert r['headroom_bytes']>=12884901888 and r['query_seconds']<=2
    assert time.monotonic()-began<=2
    assert peak()<=134217728
def checked_url(url):
    p=urlsplit(url)
    if p.scheme!='https' or p.hostname not in ('www.cvlibs.net','cvlibs.net') or p.port not in (None,443) or p.username is not None or p.password is not None or p.query or p.fragment or p.path != '/datasets/kitti/user_login.php':
        raise PermissionError('redirect_outside_authorized_origin')
    return p
ok=False;error=None;current=URL
try:
    freeze=json.loads((ROOT/'SOURCE_FREEZE.json').read_text(encoding='utf-8'))
    for n,h in freeze['files'].items():assert sha(ROOT/n)==h
    proposal=Path(freeze['proposal_path']);assert sha(proposal)==freeze['proposal_sha256']
    plan=json.loads(proposal.read_text(encoding='utf-8'))
    assert plan['object']['url']==URL and plan['max_requests']==4 and plan['cumulative_delivered_body_cap_bytes']==CAP
    for index in range(4):
        parsed=checked_url(current);remaining();lease(index)
        path=parsed.path or '/'
        if parsed.query:path+='?'+parsed.query
        headers={'User-Agent':'RAP-source-audit/1.0','Accept':'text/html,application/xhtml+xml;q=0.9',
            'Accept-Encoding':'identity','Connection':'close'}
        row=dict(index=index,url=current,method='GET',request_headers=headers,body_bytes=0,EOF=False)
        ROWS.append(row);write(f'{index:02d}.request.json',row.copy())
        conn=http.client.HTTPSConnection(parsed.hostname,port=443,timeout=min(10.,remaining()),context=ssl.create_default_context())
        response=None
        try:
            conn.request('GET',path,headers=headers)
            response=conn.getresponse()
            row.update(status=response.status,reason=response.reason,response_headers=response.getheaders())
            write(f'{index:02d}.headers.json',dict(status=response.status,reason=response.reason,headers=response.getheaders()))
            encoding=(response.getheader('Content-Encoding') or 'identity').strip().lower()
            if encoding not in ('','identity'):raise ValueError('nonidentity_content_encoding')
            mime=(response.getheader('Content-Type') or '').split(';',1)[0].strip().lower()
            is_redirect=response.status in (301,302,303,307,308)
            if mime not in ('text/html','application/xhtml+xml') and not (is_redirect and mime in ('','text/plain')):
                raise ValueError('non_HTML_response_rejected_without_body_read')
            declared=response.getheader('Content-Length')
            if declared is not None:
                if not declared.isdecimal():raise ValueError('invalid_content_length')
                if int(declared)>CAP-TOTAL:raise ValueError('declared_body_exceeds_remaining_cap')
            body=OUT/f'{index:02d}.body';row['body_file']=body.name
            with body.open('xb') as f:
                while True:
                    remaining()
                    if response.length==0:
                        row['EOF']=True;break
                    allowance=CAP-TOTAL
                    if allowance<=0:raise ValueError('body_cap_without_confirmed_EOF')
                    if conn.sock is not None:conn.sock.settimeout(min(10.,remaining()))
                    try:
                        block=response.read(min(8192,allowance))
                    except http.client.IncompleteRead as failure:
                        block=failure.partial
                        if len(block)>allowance:raise AssertionError('partial body exceeds authorized read')
                        f.write(block);TOTAL+=len(block);row['body_bytes']+=len(block)
                        raise
                    if not block:
                        row['EOF']=True;break
                    f.write(block);TOTAL+=len(block);row['body_bytes']+=len(block)
                    if peak()>134217728:raise MemoryError('native_peak_over_cap')
            row['body_sha256']=sha(body)
            if declared is not None and row['body_bytes']!=int(declared):raise ValueError('incomplete_declared_body')
            if is_redirect:
                location=response.getheader('Location')
                if not location:raise ValueError('redirect_without_location')
                destination=urljoin(current,location);checked_url(destination)
                row['redirect_to']=destination
                if index==3:raise ValueError('request_cap_before_redirect_target')
                current=destination
            else:
                if response.status!=200:raise ValueError('non200_final_status')
                assert row['EOF'];ok=True;break
        finally:
            if response is not None:response.close()
            conn.close()
            if 'body_file' in row and (OUT/row['body_file']).exists():row['body_sha256']=sha(OUT/row['body_file'])
            write(f'{index:02d}.receipt.json',row)
    if not ok:raise ValueError('no_complete_final_page')
    write('RESULTS.json',dict(passed=True,initial_URL=URL,final_URL=current,requests=len(ROWS),
        cumulative_delivered_body_bytes=TOTAL,body_cap_bytes=CAP,final_body=ROWS[-1]['body_file'],
        final_body_sha256=ROWS[-1]['body_sha256'],EOF=True,identity_encoding=True,
        redirects_followed=len(ROWS)-1,hyperlinks_followed=0,retries=0,
        linked_PDF_archive_raw_pose_weight_script_requests=0,credentials_or_cookies_sent=False))
except BaseException as caught:
    error=repr(caught)
    write('FAILURE.json',dict(error=error,traceback=traceback.format_exc(),
        attempted_requests=len(ROWS),cumulative_delivered_body_bytes=TOTAL))
    raise
finally:
    write('WORKER_EXIT.json',dict(success=ok,error=error,elapsed_seconds=time.monotonic()-START,
        peak_working_set_bytes=peak(),cumulative_delivered_body_bytes=TOTAL,requests=len(ROWS),
        all_request_rows=ROWS,whole_scope_not_retried=True))
