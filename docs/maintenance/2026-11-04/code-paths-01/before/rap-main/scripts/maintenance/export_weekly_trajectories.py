"""Portable B/G pose exports with roundtrip and source manifest; no GT alignment."""
import time
START=time.monotonic()
import sys,signal,resource,traceback,zipfile
from pathlib import Path
import numpy as np
import e0_local_map_six as x
r=x.r
BASE=r.MAIN/'docs/maintenance/2026-10-20/weekly-system-handoff-01'
def used():
    total=0.
    for d in (BASE/'supervision').glob('*'):
        if not d.is_dir():continue
        vals=[r.read(d/n)['wall_seconds'] for n in ('child_exit.json','exit.json') if (d/n).exists()];total+=max(vals,default=0.)
    return total
def run():
    left=300-used();assert left>1;signal.signal(signal.SIGALRM,lambda a,b:(_ for _ in ()).throw(TimeoutError('original delivery cap')));signal.alarm(max(1,int(left)))
    ok=False;err=None
    try:
        x.verify();result=r.read(x.BASE/'results.json');assert result['independent_validation_passed']
        for folder,seal,bank in ((x.BASE,'bank_seal.json','bank'),(x.OLD,'anchor_corrected_seal.json','anchor_corrected_bank')):
            for p,h in r.read(folder/seal)['files'].items():assert r.sha(folder/bank/p)==h
        r.save(BASE/'EXPORT_FREEZE.json',dict(utc=r.now(),files={str(p):r.sha(p) for p in (Path(__file__),BASE/'EXPORT_SCOPE.md',x.BASE/'results.json',x.BASE/'bank_seal.json',x.OLD/'anchor_corrected_seal.json')},original_delivery_seconds_remaining=left))
        import validate_scan_level_graph as v
        dest=BASE/'trajectory_package';dest.mkdir();source={};maximum=0.;count=0
        for s in x.SEQS:
            d=dest/s;d.mkdir();manifest=r.read(x.src(s)/'source_frames.json');ids=manifest['source_frame_ids'];assert ids==list(range(len(ids)))
            gp=(x.BASE/f'bank/{s}/G.npy') if s in x.NEW else (x.OLD/f'anchor_corrected_bank/{s}/G.npy');bp=x.src(s)/'optimized_poses.txt';cal=r.DATA/f'sequences/{s}/calib.txt';tr=v.calibration(s);ti=np.linalg.inv(tr)
            source[s]=dict(source_manifest_sha256=r.sha(x.src(s)/'source_frames.json'),B_source_sha256=r.sha(bp),G_source_sha256=r.sha(gp),calibration_sha256=r.sha(cal),frames=len(ids))
            for a,t in [('B',r.poses(bp)),('G',np.load(gp))]:
                assert len(t)==len(ids) and np.isfinite(t).all()
                for frame,arr in [('lidar',t),('camera',tr@t@ti)]:
                    p=d/f'{a}_{frame}.txt';assert not p.exists();np.savetxt(p,arr[:,:3,:].reshape(-1,12),fmt='%.17g')
                    load=np.loadtxt(p).reshape(-1,3,4);assert load.shape==arr[:,:3,:].shape;error=float(np.max(abs(load-arr[:,:3,:])));maximum=max(maximum,error);assert error<=1e-8;count+=1
                    if frame=='camera':
                        full=np.tile(np.eye(4),(len(load),1,1));full[:,:3,:]=load;error=float(np.max(abs(ti@full@tr-t)));maximum=max(maximum,error);assert error<=1e-8
            r.save(d/'source_frames.json',dict(source_frame_ids=ids,timestamps=manifest.get('timestamps'),source_manifest_sha256=source[s]['source_manifest_sha256']))
        r.save(dest/'METRICS.json',result)
        (dest/'README.md').write_text('''# Experimental fixed-E0 system trajectories — October20

All six exposed development sequences, complete source-frame order. B is the existing E0/RAP graph. G is the isolated corrected-anchor native local-map bundle, using exactly the same fixed E0 odometry. G is a single global mode, not a GT-selected mixture. Every file contains one unaligned rigid pose per source frame, the top3x4 matrix as12 row-major numbers. Source IDs/timestamps are in each directory. LiDAR files are LiDAR world poses; camera files are Tr @ T_lidar @ inv(Tr), with the original KITTI calibration. No GT alignment or reference coordinate file is included.

New six-sequence mean target passes: G ATE0.648336m versus archived complete KISS-SLAM0.699689m, G ter0.446952% versus0.478614%. Additional individual protection fails07 ter and10 rer;06/10 ATE is >5% worse than KISS. G is delivered experimentally; production/default B is unchanged. Original strict00/05 tests remain FAILED. METRICS includes every sequence and gate, not only averages.

These trajectories reuse cached E0. They do not supply a new full raw-system runtime benchmark, RAP-specific gain, independent scenes, physical-reference authentication or training-exclusion evidence. The latest complete raw-system benchmark remainsOctober11. 09 is retained. Use poses for independent inspection with those limits. No original data, prediction or installed package was modified.

SOURCE_BINDINGS and FILE_SHA256 bind the source identities and exported bytes; EXPORT_CHECKS in the parent dossier records full serialization/inverse-coordinate roundtrip. The ZIP and directory contain the same files. This is a local artifact, not a published release.
''',encoding='utf-8')
        r.save(dest/'SOURCE_BINDINGS.json',dict(utc=r.now(),sources=source,GT_alignment=False,new_predictions=0,new_solver_calls=0))
        r.save(dest/'FILE_SHA256.json',dict(files={str(p.relative_to(dest)):r.sha(p) for p in sorted(dest.rglob('*')) if p.is_file()}))
        zp=BASE/'experimental_fixed_E0_BG_20261020.zip'
        with zipfile.ZipFile(zp,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            for p in sorted(dest.rglob('*')):
                if p.is_file():z.write(p,arcname=str(p.relative_to(dest)))
        with zipfile.ZipFile(zp) as z:
            assert z.testzip() is None
            for p in sorted(dest.rglob('*')):
                if p.is_file():assert z.read(str(p.relative_to(dest)))==p.read_bytes()
        r.save(BASE/'EXPORT_CHECKS.json',dict(utc=r.now(),passed=True,pose_files=count,total_frames=sum(p['frames'] for p in source.values()),maximum_roundtrip_error=maximum,
            zip_sha256=r.sha(zp),zip_bytes=zp.stat().st_size,zip_member_bytes_verified=True,GT_alignment=False,new_predictions=0,new_solver_calls=0))
        assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024<=2*2**30;assert sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file())<=64*2**20
        print('Portable BG trajectories exported',count,'files, max roundtrip',maximum,'ZIP',zp.stat().st_size,flush=True);ok=True
    except BaseException as e:err=repr(e);traceback.print_exc();r.save(BASE/'FAILURE_export_final.json',dict(utc=r.now(),error=err))
    finally:
        signal.alarm(0);r.save(BASE/'supervision/export_final/child_exit.json',dict(utc=r.now(),success=ok,error=err,wall_seconds=time.monotonic()-START,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,GPU_calls=0))
    if not ok:sys.exit(1)
if __name__=='__main__':assert sys.argv[1]=='export_final';run()
