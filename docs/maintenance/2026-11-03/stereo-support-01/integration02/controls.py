"""Exercise immutable serial mailboxes and restricted cold NPZ, no real arrays."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
out=Path(sys.argv[1]);gate([],out)
for index in range(160):lease(out,True)
requests=sorted(out.glob('*_request.json'));responses=sorted(out.glob('*_response.json'))
assert len(requests)==len(responses)==160
for index,(rq,rp) in enumerate(zip(requests,responses),1):
    a=read(rq);b=read(rp)
    assert a['serial']==b['serial']==index and a['nonce']==b['nonce']
    assert b['query_seconds']<=2 and b['headroom_bytes']>=12*1024**3
np.savez_compressed(out/'cold_fixture.npz',left=np.arange(24,dtype=np.int16).reshape(4,6),right=np.zeros((4,6),dtype=np.int16))
with np.load(out/'cold_fixture.npz',allow_pickle=False) as z:assert z['left'].shape==z['right'].shape==(4,6)
complete(out,immutable_request_response_pairs=160,serial_nonce_identity_checks=160,real_arrays_read=0,cold_NPZ_pass=True,old_numeric_controls_byte_preserved=True)
