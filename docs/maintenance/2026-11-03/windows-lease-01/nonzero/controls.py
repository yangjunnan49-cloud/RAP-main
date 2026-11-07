"""Pure-stdlib synthetic child for the immutable external lease contract."""
import datetime,json,os,sys,time,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parent;out=Path(sys.argv[1])
case=json.loads((ROOT/'CASE.json').read_text())['case']
def save(p,v):
    with p.open('x') as f:json.dump(v,f)
def lease(serial=1):
    nonce=uuid.uuid4().hex;request=out/f'{serial:06d}_{nonce}_request.json'
    temporary=request.with_suffix('.tmp');save(temporary,dict(serial=serial,nonce=nonce));os.replace(temporary,request)
    response=out/f'{serial:06d}_{nonce}_response.json';start=time.monotonic()
    while not response.exists():
        if time.monotonic()-start>3:raise RuntimeError('synthetic response absent')
        time.sleep(.005)
    grant=json.loads(response.read_text());assert grant['nonce']==nonce and grant['serial']==serial
    assert grant['headroom_bytes']>=12*1024**3 and grant['query_seconds']<=2 and grant['passed']
    return grant
if case=='without_lease':save(out/'RESULT.json',dict(passed=True))
elif case=='future_serial':lease(2)
else:
    lease()
    if case=='nonzero':raise SystemExit(7)
    elif case=='blocking':time.sleep(30)
    elif case=='no_result':pass
    else:save(out/'RESULT.json',dict(passed=True))
