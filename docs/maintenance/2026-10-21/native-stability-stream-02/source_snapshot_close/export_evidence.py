"""Post-hoc evidence extraction/formatting only, standard library, no solver/raw/GT."""
import ast, hashlib, json, math, resource, struct, time, zipfile
from pathlib import Path
from capture_codec import read_verified
ROOT=Path(__file__).resolve().parent;OUT=ROOT.parents[1]/'outputs/native_stability_stream_20261021'
start=time.monotonic();seal=json.loads((OUT/'PAIRED_SEAL.json').read_text())


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name,value):
    with (OUT/name).open('x') as f:json.dump(value,f,indent=2,allow_nan=False)


for name,expected in seal['files'].items():assert sha(OUT/'supervision'/name).upper()==expected.upper()
left=read_verified(OUT/'supervision/native1/events.jsonl.gz');right=read_verified(OUT/'supervision/native2/events.jsonl.gz')
previous=None;prior=0;first=None
for l,r in zip(left,right):
    assert l[0]==r[0]
    if l[1]!=r[1]:
        first=(l[1],r[1]);break
    previous=l[1];prior+=1
assert first is not None and previous['boundary']=='ICP' and previous['phase']=='before'
assert first[0]['boundary']==first[1]['boundary']=='ICP' and first[0]['phase']==first[1]['phase']=='after'
changed=[name for name in first[0]['components'] if first[0]['components'][name]!=first[1]['components'][name]]
save('FIRST_ICP_EVIDENCE.json',dict(equal_prior_events=prior,first_index=first[0]['index'],frame=first[0]['frame'],
    exact_recorded_before_event=previous,changed_output_components=changed,
    left_output=first[0],right_output=first[1],hidden_state='UNKNOWN',causal_mechanism='UNKNOWN',
    before_hashes_are_recording_assertions_not_independent_authenticity=True))
names=[];roundtrip=0
for stage in ('native1','native2'):
    body=(OUT/'supervision'/stage/'coarse_poses.npy').read_bytes()
    assert body[:8]==b'\x93NUMPY\x01\x00'
    size=struct.unpack('<H',body[8:10])[0];meta=ast.literal_eval(body[10:10+size].decode())
    assert meta['descr']=='<f8' and meta['shape']==(1101,4,4) and not meta['fortran_order']
    data=body[10+size:];assert len(data)==1101*128
    rows=[]
    for index in range(1101):
        raw=data[index*128:(index+1)*128];values=struct.unpack('<16d',raw)
        assert all(math.isfinite(x) for x in values) and values[12:]==(0.,0.,0.,1.)
        line=' '.join(format(x,'.17g') for x in values[:12])
        assert struct.pack('<12d',*[float(x) for x in line.split()])==raw[:96]
        roundtrip+=1;rows.append(line)
    name='coarse_G06_'+stage+'.txt';(OUT/name).write_text('\n'.join(rows)+'\n');names.append(name)
readme='N2 diagnostic only: two fixed-frontend serial native COARSE G06 trajectories,1101poses each. Unaligned LiDAR3x4; noGT/finegraph/RAP/all-six efficacy/P0qualification. Original N1 remains incomplete. See REPORT_CN.md and RESULTS.json.\n'
archive=OUT/'coarse_G06_native_pair.zip'
with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
    for name in names:z.write(OUT/name,name)
    z.writestr('README.txt',readme)
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    for name in names:assert hashlib.sha256(z.read(name)).hexdigest()==sha(OUT/name)
save('EXPORT_CHECKS.json',dict(passed=True,trajectories=2,poses=roundtrip,members=3,
    all_3x4_float64_bit_roundtrips_exact=True,archive_sha256=sha(archive),source_pair_seal_sha256=sha(OUT/'PAIRED_SEAL.json'),
    helper_sha256=sha(Path(__file__)),elapsed=time.monotonic()-start,
    max_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,raw_reads=0,GT_reads=0,new_predictions=0))
print(json.dumps(dict(equal_prior_events=prior,first_frame=first[0]['frame'],changed=changed,poses_exported=roundtrip)))
