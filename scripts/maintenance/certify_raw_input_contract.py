"""All-frame byte certificate before new registration; shared R0 campaign cap."""
import time
START=time.monotonic()
import os,sys,resource,signal,subprocess,traceback,hashlib,importlib.util
from pathlib import Path
import numpy as np
import raw_system_integration03 as d
BASE=d.BASE.parent/'raw-input-contract-01';SUP=BASE/'supervision';R0=d.BASE
def used():
    total=d.used()
    for p in SUP.glob('*'):
        if p.is_dir():total+=max([d.read(p/n)['wall_seconds'] for n in ('child_exit.json','exit.json') if (p/n).exists()]+[0])
    return total
def cap():
    assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024<=4*2**30
    assert sum(p.stat().st_size for b in (R0,BASE) for p in b.rglob('*') if p.is_file())<=256*2**20
def native_reference():
    from rap_slam.real_dataset import kitti_vertical_correction
    f=d.read(R0/'freeze.json');rows={};total=0
    for s in d.SEQS:
        rows[s]=[]
        for i in range(f['counts'][s]):
            p=d.r.raw(s,i);body=p.read_bytes();assert hashlib.sha256(body).hexdigest()==f['raw_files'][str(p)];raw=np.frombuffer(body,np.float32).reshape(-1,4)[:,:3];assert np.isfinite(raw).all()
            raw=raw[np.linalg.norm(raw,axis=1)>=1.5].copy();prepared=kitti_vertical_correction(raw).astype(np.float32);assert prepared.dtype==np.float32
            rows[s].append(dict(points=len(prepared),prepared_sha256=hashlib.sha256(prepared.tobytes(order='C')).hexdigest()));total+=len(prepared)
            if i%500==0:cap();print('original float32 reference',s,i,flush=True)
    d.save(BASE/'original_prepared_reference.json',dict(utc=d.now(),numpy=np.__version__,rows=rows,prepared_point_occurrences=total,registration_calls=0,GT_numeric_read=False))
def native_candidate():
    spec=importlib.util.spec_from_file_location('legacy_f32',BASE/'legacy_f32_correction.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    f=d.read(R0/'freeze.json');reference=d.read(BASE/'original_prepared_reference.json');frames=0;points=0
    for s in d.SEQS:
        assert len(reference['rows'][s])==f['counts'][s]
        for i in range(f['counts'][s]):
            p=d.r.raw(s,i);body=p.read_bytes();assert hashlib.sha256(body).hexdigest()==f['raw_files'][str(p)];raw=np.frombuffer(body,np.float32).reshape(-1,4)[:,:3]
            prepared=m.legacy_f32_correction(raw[np.linalg.norm(raw,axis=1)>=1.5].copy());entry=reference['rows'][s][i]
            assert len(prepared)==entry['points'] and hashlib.sha256(prepared.tobytes(order='C')).hexdigest()==entry['prepared_sha256'],('prepared bytes differ',s,i)
            frames+=1;points+=len(prepared)
            if i%500==0:cap();print('explicit float32 certificate',s,i,flush=True)
    d.save(BASE/'INPUT_CERTIFICATE.json',dict(utc=d.now(),passed=True,complete_frames=frames,prepared_point_occurrences=points,prepared_coordinate_occurrences=3*points,
        numpy=np.__version__,reference_sha256=d.sha(BASE/'original_prepared_reference.json'),correction_source_sha256=d.sha(BASE/'legacy_f32_correction.py'),byte_hashes_all_equal=True,registration_calls=0,GT_numeric_read=False))
def run():
    left=7200-used();assert left>1;signal.signal(signal.SIGALRM,lambda a,b:(_ for _ in ()).throw(TimeoutError('shared R0/S1 campaign cap')));signal.alarm(max(1,int(left)))
    ok=False;err=None;peak=0
    try:
        d.verify();assert not (R0/'bank_seal03.json').exists()
        d.save(BASE/'SOURCE_PREFREEZE.json',dict(utc=d.now(),files={str(p):d.sha(p) for p in (Path(__file__),BASE/'OWNER_SCOPE.md',BASE/'PROTOCOL.md',BASE/'legacy_f32_correction.py',R0/'FRONTEND_DIAGNOSIS.json',R0/'freeze.json')},shared_charged_seconds=used(),shared_remaining_seconds=left,real_registration_before_certificate=0))
        env=os.environ.copy();env['CUDA_VISIBLE_DEVICES']='';env['PYTHONDONTWRITEBYTECODE']='1'
        for label,exe in [('reference','/root/miniconda3/envs/rap-inference/bin/python'),('candidate',d.r.KISS)]:
            p=subprocess.run([exe,'-u','-B',__file__,'--native',label],env=env,timeout=7200-used()-1);receipt=d.read(SUP/'certify_inputs'/f'{label}_exit.json');peak=max(peak,receipt['peak_RSS_bytes']);assert p.returncode==0 and receipt['success']
        cap();ok=True
    except BaseException as e:err=repr(e);traceback.print_exc();d.save(BASE/'FAILURE_input_certificate.json',dict(utc=d.now(),error=err))
    finally:
        signal.alarm(0);d.save(SUP/'certify_inputs/child_exit.json',dict(utc=d.now(),success=ok,error=err,wall_seconds=time.monotonic()-START,peak_RSS_bytes=max(peak,resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024),GPU_calls=0,shared_R0_cap=True))
    if not ok:sys.exit(1)
if __name__=='__main__':
    if '--native' in sys.argv:
        label=sys.argv[-1];ok=False
        try:{'reference':native_reference,'candidate':native_candidate}[label]();ok=True
        finally:d.save(SUP/f'certify_inputs/{label}_exit.json',dict(utc=d.now(),success=ok,wall_seconds=time.monotonic()-START,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,GPU_calls=0))
    else:assert sys.argv[1]=='certify_inputs';run()
