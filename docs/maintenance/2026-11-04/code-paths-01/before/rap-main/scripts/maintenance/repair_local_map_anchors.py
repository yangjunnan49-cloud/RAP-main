"""Target-free real source-anchor contract repair; seal before metrics."""
import time
START=time.monotonic()
import os,sys,resource,signal,subprocess,traceback
from pathlib import Path
import numpy as np
import e0_local_map_bundle as r
r.imports()
BASE=r.BASE
def native():
    import coarse_anchor_fine_control as c
    assert r.read(BASE/'coarse_anchor_control.json')['passed']
    proof=r.read(BASE/'FIX_CONTROL_FREEZE.json'); assert proof['sources'][str(Path(c.__file__))]==r.sha(c.__file__)
    data=r.read(BASE/'fine_graph_diagnosis.json'); outdir=BASE/'anchor_corrected_bank'; outdir.mkdir(); rows={}
    for s in r.SEQS:
        d=outdir/s; d.mkdir(); o=r.proper(r.poses(r.src(s)/'odom_poses.txt')); initial=np.load(BASE/f'bank/{s}/before_fine.npy')
        entries=data['rows'][s]['coarse_anchors']; ids=[e['anchor_frame'] for e in entries]; poses=np.asarray([e['pose'] for e in entries])
        assert ids==sorted(set(ids)) and ids[0]==0
        t=c.fine(o,initial,ids,poses); error=float(np.max(abs(t[ids]-poses))); assert error<=1e-8
        assert t.shape==o.shape and np.isfinite(t).all(); rot=t[:,:3,:3]; assert np.max(abs(rot.transpose(0,2,1)@rot-np.eye(3)))<=1e-8
        np.save(d/'G.npy',t); r.save(d/'anchors.json',dict(source_frame_ids=list(range(len(o))),anchor_frames=ids,coarse_poses=poses.tolist(),anchor_preservation_max=error))
        rows[s]=dict(frames=len(o),anchors=len(ids),anchor_preservation_max=error)
    r.save(outdir/'execution.json',dict(utc=r.now(),rows=rows,GT_numeric_read=False))
    r.save(BASE/'anchor_corrected_seal.json',dict(utc=r.now(),original_bank_seal_sha256=r.sha(BASE/'bank_seal.json'),
        files={str(p.relative_to(outdir)):r.sha(p) for p in outdir.rglob('*') if p.is_file()}))
    print('Corrected coarse anchors preserved; both target-free trajectories sealed',rows,flush=True)
def run():
    left=1800-r.used(); assert left>0; signal.signal(signal.SIGALRM,lambda a,b:(_ for _ in ()).throw(TimeoutError('original LMB cap'))); signal.alarm(max(1,int(left)))
    ok=False; err=None; peak=0
    try:
        r.verify_bank(); paths=[Path(__file__),BASE/'ANCHOR_REPAIR_SCOPE.md',r.MAIN/'scripts/maintenance/coarse_anchor_fine_control.py']
        r.save(BASE/'ANCHOR_REPAIR_FREEZE.json',dict(utc=r.now(),sources={str(p):r.sha(p) for p in paths},original_bank_seal_sha256=r.sha(BASE/'bank_seal.json'),remaining_original_seconds=left))
        env=os.environ.copy(); env['CUDA_VISIBLE_DEVICES']=''; p=subprocess.run([r.KISS,'-u','-B',__file__,'--native'],env=env,timeout=left-1); assert p.returncode==0
        peak=r.read(BASE/'supervision/anchor_repair/native_exit.json')['peak_RSS_bytes']; r.cap(); ok=True
    except BaseException as e:
        err=repr(e);traceback.print_exc();r.save(BASE/'FAILURE_anchor_repair.json',dict(utc=r.now(),error=err))
    finally:
        signal.alarm(0);r.save(BASE/'supervision/anchor_repair/child_exit.json',dict(utc=r.now(),success=ok,error=err,wall_seconds=time.monotonic()-START,
            peak_RSS_bytes=max(peak,resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024),GPU_calls=0))
    if not ok:sys.exit(1)
if __name__=='__main__':
    if '--native' in sys.argv:
        try:native()
        finally:r.save(BASE/'supervision/anchor_repair/native_exit.json',dict(utc=r.now(),wall_seconds=time.monotonic()-START,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024))
    else:
        assert sys.argv[1]=='anchor_repair';run()
