"""Read only recorded metadata/owned NPY bytes; stdlib, no raw/GT/native imports."""
import ast, hashlib, json, resource, struct, time
from pathlib import Path
from capture_codec import read_verified
from bindings import OUT, save, sha, read
start=time.monotonic();bank=OUT/'frontend'
seal=read(bank/'SEAL.json')
for name,expected in seal['files'].items():assert sha(bank/name)==expected
body=(bank/'poses.npy').read_bytes();assert body[:6]==b'\x93NUMPY' and body[6:8]==b'\x01\x00'
size=struct.unpack('<H',body[8:10])[0];header=ast.literal_eval(body[10:10+size].decode())
assert header['descr']=='<f8' and not header['fortran_order'] and header['shape']==(1101,4,4)
payload=body[10+size:];assert len(payload)==1101*128
packets=read(bank/'packets.json');events=0;checked=0;last=None;cloud=None
for binding,event in read_verified(OUT/'supervision/native1/events.jsonl'):
    events+=1;last=event
    if event['boundary']=='packet':
        i=event['frame'];assert i==checked
        assert event['components']['points']['sha256']==packets[i]['map_sha256']
        assert event['components']['frontend']['sha256']==hashlib.sha256(payload[i*128:(i+1)*128]).hexdigest()
        checked+=1
    if event['boundary']=='voxel0._point_cloud' and event['phase']=='after':cloud=event
expected_bytes=cloud['components']['value']['shape'][0]*3*8
assert expected_bytes>16*2**20
assert not(OUT/'supervision/native2').exists()
save(OUT/'PARTIAL_AUDIT.json',dict(passed=True,verified_event_chain_rows=events,verified_packet_prefix=checked,
    last_event=last,last_query_cloud=cloud,projected_detector_f64_bytes=expected_bytes,original_array_cap=16*2**20,
    frontend_bank_hashes_unchanged=True,native2_started=False,comparative_scientific_result='INCOMPLETE',
    raw_reads=0,GT_reads=0,native_imports=0,elapsed=time.monotonic()-start,
    max_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024))
print(json.dumps(dict(events=events,packet_prefix=checked,expected_detector_bytes=expected_bytes)))
