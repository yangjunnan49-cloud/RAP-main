"""Prospective fixed-G extension under the ORIGINAL cumulative LMB resource cap."""
import time
START=time.monotonic()
import os,sys,resource,signal,subprocess,traceback,hashlib
from pathlib import Path
import numpy as np
import e0_local_map_bundle as r
r.imports()
OLD=r.BASE
BASE=r.MAIN/'docs/maintenance/2026-10-20/e0-local-map-six-01'
SUP=BASE/'supervision'
SEQS=('00','05','06','07','09','10')
NEW=SEQS[2:]
ARCHIVE=r.MAIN/'docs/meeting_20261011/benchmark/attempt03/results.json'
def src(s):
    date='2026-09-26/e0-frontend-01' if s in ('00','05','06') else '2026-09-27/e0-heldout-01'
    return r.MAIN/f'docs/maintenance/{date}/full-{s}-A'
def used():
    total=r.used()
    for d in SUP.glob('*'):
        if d.is_dir():
            vals=[r.read(d/n)['wall_seconds'] for n in ('child_exit.json','exit.json') if (d/n).exists()]
            total+=max(vals,default=0.)
    return total
def cap():
    assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024<=4*2**30
    assert sum(p.stat().st_size for b in (OLD,BASE) for p in b.rglob('*') if p.is_file())<=128*2**20
    if (SUP/'host_latest.json').exists():assert r.read(SUP/'host_latest.json')['headroom_bytes']>=4*2**30
def oldcheck():
    r.verify_bank()
    for p,h in r.read(OLD/'anchor_corrected_seal.json')['files'].items():assert r.sha(OLD/'anchor_corrected_bank'/p)==h,p
    assert r.read(OLD/'coarse_anchor_control.json')['passed']
    for p,h in r.read(OLD/'FIX_CONTROL_FREEZE.json')['sources'].items():assert r.sha(p)==h,p
    assert r.read(OLD/'anchor_results.json')['independent_validation_passed']
    assert not r.read(OLD/'anchor_results.json')['original_strict_gate_against_B']['passed']
def verify():
    oldcheck()
    for p,h in r.read(BASE/'freeze.json')['files'].items():assert r.sha(p)==h,p
def freeze():
    oldcheck()
    paths=[Path(__file__),BASE/'OWNER_SCOPE.md',BASE/'PROTOCOL.md',Path(r.__file__).with_name('coarse_anchor_fine_control.py'),
        OLD/'freeze.json',OLD/'anchor_corrected_seal.json',OLD/'anchor_results.json',OLD/'FIX_CONTROL_FREEZE.json',ARCHIVE,
        Path(r.__file__).with_name('invoke_mgr_supervised_wsl.ps1'),Path(r.__file__).with_name('validate_scan_level_graph.py')]
    rawfiles={}
    for s in SEQS:
        paths += [src(s)/n for n in ('source_frames.json','odom_poses.txt','optimized_poses.txt')]
        paths += [r.DATA/f'poses/{s}.txt',r.DATA/f'sequences/{s}/calib.txt']
        if s not in NEW:continue
        priorpath=src(s).parent/'freeze.json'; paths.append(priorpath); prior=r.read(priorpath)['inputs']
        manifest=r.read(src(s)/'source_frames.json'); ids=manifest['source_frame_ids'];assert ids==list(range(len(ids)))
        for i in ids:
            p=r.raw(s,i);assert str(p)==manifest['scan_files'][i];h=r.sha(p);assert h==prior[str(p)];rawfiles[str(p)]=h
            if i%500==0:cap();print('freeze raw',s,i,flush=True)
    # Reuse the original installed binary/config identities, not a new configuration.
    for p,h in r.read(OLD/'freeze.json')['files'].items():assert r.sha(p)==h
    paths=list(dict.fromkeys(paths));snap=BASE/'source_snapshot';snap.mkdir()
    for i,p in enumerate(paths):
        if p.suffix in ('.py','.ps1','.md'):(snap/f'{i:03d}-{p.name}').write_bytes(p.read_bytes())
    r.save(BASE/'freeze.json',dict(utc=r.now(),files={str(p):r.sha(p) for p in paths},raw_files=rawfiles,
        original_LMB_charged_seconds=r.used(),original_cap_seconds=1800,combined_remaining_seconds=1800-used(),GT_numeric_read=False))
    (BASE/'INCOMPLETE').write_text('Pending remaining-four bank and full-six independent metrics.\n')
    print('Prospective G frozen',len(paths),len(rawfiles),'raw files',flush=True)
def bank():
    verify()
    from kiss_slam.slam import KissSLAM
    from rap_slam.real_dataset import kitti_vertical_correction
    from coarse_anchor_fine_control import fine
    dest=BASE/'bank';dest.mkdir();f=r.read(BASE/'freeze.json');summary={}
    for s in NEW:
        d=dest/s;d.mkdir();o=r.proper(r.poses(src(s)/'odom_poses.txt'));slam=KissSLAM(r.config());fixed=r.FixedOdometry(r.config().kiss_icp_config(),o);slam.odometry=fixed
        recorder=r.Recorder(slam.closer);slam.closer=recorder;membership={};consumed={};begin=time.monotonic()
        for i in range(len(o)):
            p=r.raw(s,i);body=p.read_bytes();h=hashlib.sha256(body).hexdigest();assert h==f['raw_files'][str(p)];consumed[str(p)]=h
            points=np.frombuffer(body,dtype=np.float32).reshape(-1,4)[:,:3].copy();ranges=np.linalg.norm(points,axis=1);points=points[(ranges>=1.5)&(ranges<=80.)]
            points=kitti_vertical_correction(points);mapid=slam.local_map_graph.last_id;membership.setdefault(str(mapid),[]).append(i);slam.process_scan(points,np.array([]))
            if i%250==0:cap();print('mapping',s,i,'maps',slam.local_map_graph.last_id,'loops',len(slam.closures),flush=True)
        slam.generate_new_node();slam.local_map_graph.erase_last_local_map();initial=np.asarray(slam.poses)
        anchors=[];coarse=[];maximum=0.
        for key,frames in membership.items():
            mid=int(key);a=0 if mid==0 else fixed.resets[mid-1];first=frames[0];p=initial[first]@np.linalg.solve(o[first],o[a]);anchors.append(a);coarse.append(p)
            for i in frames:maximum=max(maximum,float(np.max(abs(p@np.linalg.solve(o[a],o[i])-initial[i]))))
        assert maximum<=1e-8 and anchors==sorted(set(anchors)) and anchors[0]==0
        coarse=np.asarray(coarse);t=fine(o,initial,anchors,coarse);error=float(np.max(abs(t[anchors]-coarse)));assert error<=1e-8
        assert t.shape==initial.shape==o.shape and np.isfinite(t).all() and fixed.index==len(o)-1 and fixed.max_relative_error<=1e-9
        assert sorted(i for group in membership.values() for i in group)==list(range(len(o)))
        rot=t[:,:3,:3];assert np.max(abs(rot.transpose(0,2,1)@rot-np.eye(3)))<=1e-8 and np.max(abs(np.linalg.det(rot)-1))<=1e-8
        np.save(d/'G.npy',t);np.save(d/'before_fine.npy',initial)
        r.save(d/'source_binding.json',dict(source_frame_ids=list(range(len(o))),map_consumed_frames=membership,reset_anchors=fixed.resets,raw_sha256=consumed,
            inherited_voxel_conservative_source_prefixes=[[0,i] for i in fixed.resets],per_return_voxel_lineage=False,relative_pose_max=fixed.max_relative_error,
            odometry_alignment_calls=0,loop_attempts=recorder.rows,anchor_frames=anchors,coarse_poses=coarse.tolist(),anchor_preservation_max=error,coarse_reconstruction_max=maximum))
        slam.optimizer.write_graph(str(d/'local_map_graph.g2o'))
        summary[s]=dict(frames=len(o),local_maps=len(anchors),closures=len(slam.closures),loop_calls=len(recorder.rows),wall_seconds=time.monotonic()-begin,
            anchor_preservation_max=error,coarse_reconstruction_max=maximum,maximum_adapter_relative_error=fixed.max_relative_error)
        cap();print('mapping complete',s,summary[s],flush=True)
    r.save(dest/'execution.json',dict(utc=r.now(),rows=summary,GT_numeric_read=False))
    r.save(BASE/'bank_seal.json',dict(utc=r.now(),freeze_sha256=r.sha(BASE/'freeze.json'),reused00_05_seal_sha256=r.sha(OLD/'anchor_corrected_seal.json'),
        files={str(p.relative_to(dest)):r.sha(p) for p in dest.rglob('*') if p.is_file()}))
    print('Complete remaining-four G bank sealed before metrics',flush=True)
def gates(rows):
    means={a:{k:float(np.mean([rows[s][a][k] for s in SEQS])) for k in ('ate','ter','rer')} for a in ('B','G','KISS')}
    primary=dict(mean_ATE_better=means['G']['ate']<means['KISS']['ate'],mean_ter_nonworse=means['G']['ter']<=means['KISS']['ter']+1e-5)
    safety={f'{s}_{k}':rows[s]['G'][k]<=rows[s]['KISS'][k]+.01 for s in SEQS for k in ('ter','rer')}
    return dict(means=means,primary=primary,safety=safety,primary_passed=all(primary.values()),safety_passed=all(safety.values()),
        deployable=all(primary.values()) and all(safety.values()),ATE_gain5pct=means['G']['ate']<=.95*means['KISS']['ate'],
        ATE_harm_over5pct={s:rows[s]['G']['ate']>1.05*rows[s]['KISS']['ate'] for s in SEQS})
def evaluate():
    verify();seal=r.read(BASE/'bank_seal.json')
    assert seal['freeze_sha256']==r.sha(BASE/'freeze.json') and seal['reused00_05_seal_sha256']==r.sha(OLD/'anchor_corrected_seal.json')
    for p,h in seal['files'].items():assert r.sha(BASE/'bank'/p)==h
    from rap_slam.real_dataset import load_gt_poses,_read_calib_transform
    import eval_paper_metrics as epm
    import validate_scan_level_graph as v
    started=r.now();rows={};maximum=0.;count=0;f=r.read(BASE/'freeze.json');dest=BASE/'evaluation';dest.mkdir();archive=r.read(ARCHIVE)
    for s in SEQS:
        (dest/s).mkdir();tr=_read_calib_transform(str(r.DATA/f'sequences/{s}/calib.txt'));ti=np.linalg.inv(tr)
        gt=np.asarray(load_gt_poses(str(r.DATA/f'poses/{s}.txt'),str(r.DATA/f'sequences/{s}/calib.txt'),apply_calib=True));cg=v.load(r.DATA/f'poses/{s}.txt');ct=v.calibration(s);rows[s]={}
        binding=r.read((BASE/f'bank/{s}/source_binding.json') if s in NEW else (OLD/f'bank/{s}/source_binding.json'))
        assert binding['source_frame_ids']==list(range(len(gt)))
        frozen=f['raw_files'] if s in NEW else r.read(OLD/'freeze.json')['raw_files']
        assert binding['raw_sha256']=={str(r.raw(s,i)):frozen[str(r.raw(s,i))] for i in range(len(gt))}
        assert sorted(i for group in binding['map_consumed_frames'].values() for i in group)==list(range(len(gt)))
        for a in ('B','G'):
            t=r.poses(src(s)/'optimized_poses.txt') if a=='B' else np.load((BASE/f'bank/{s}/G.npy') if s in NEW else (OLD/f'anchor_corrected_bank/{s}/G.npy'))
            assert len(t)==len(gt);ids=list(range(len(t)));li=epm.evaluate_pair(list(gt),list(t),ids);ca=epm.evaluate_pair(list(tr@gt@ti),list(tr@t@ti),ids)
            x=dict(ate=li['ape_aligned_rmse'],ter=ca['kitti_ter_pct'],rer=ca['kitti_rer_deg100m'],segments=ca['kitti_segments'])
            seg=v.segments(cg,ct@t@np.linalg.inv(ct));count+=len(seg);assert len(seg)==len(ca['kitti_segment_records'])
            y=dict(ate=v.horn_rmse(np.linalg.inv(ct)@cg@ct,t),ter=float(np.mean([q['translation_fraction'] for q in seg])*100),rer=float(np.mean([q['rotation_rad_per_m'] for q in seg])*180/np.pi*100),segments=len(seg))
            for k in x:maximum=max(maximum,abs(x[k]-y[k]));assert abs(x[k]-y[k])<=1e-8
            for q,z in zip(seg,ca['kitti_segment_records']):
                for k in ('first','last','source_first','source_last','length_m'):assert q[k]==z[k]
                for k in ('translation_fraction','rotation_rad_per_m','speed_mps'):maximum=max(maximum,abs(q[k]-z[k]));assert abs(q[k]-z[k])<=2e-10
            rows[s][a]=x;r.save(dest/s/f'{a}_segments.json',ca['kitti_segment_records'])
        kr=[x for x in archive['rows'] if x['model']=='KISS-SLAM' and x['sequence']==s];assert len(kr)==3
        rows[s]['KISS']={k:float(np.mean([x[k] for x in kr])) for k in ('ate','ter','rer')}
    r.save(BASE/'results.json',dict(utc=r.now(),gt_read_started_utc=started,bank_sealed_before_GT=seal['utc']<started,rows=rows,gate=gates(rows),
        independent_validation_passed=True,independent_segments=count,maximum_metric_delta=maximum,nonlinear_optimizer_independent=False))
    print('Full-six validated',rows,'decision',gates(rows),flush=True)
def run(stage,native):
    left=1800-used();assert left>1;signal.signal(signal.SIGALRM,lambda a,b:(_ for _ in ()).throw(TimeoutError('original cumulative LMB cap')));signal.alarm(max(1,int(left)))
    ok=False;err=None;peak=0
    try:
        if stage in ('freeze','bank') and not native:
            env=os.environ.copy();env['CUDA_VISIBLE_DEVICES']='';env['OPEN3D_CPU_RENDERING']='true'
            p=subprocess.run([r.KISS,'-u','-B',__file__,stage,'--native'],env=env,timeout=left-1);receipt=r.read(SUP/stage/'native_exit.json');peak=receipt['peak_RSS_bytes'];assert p.returncode==0 and receipt['success']
        else:{'freeze':freeze,'bank':bank,'evaluate':evaluate}[stage]()
        cap();ok=True
    except BaseException as e:
        err=repr(e);traceback.print_exc();r.save(BASE/f'FAILURE_{stage}_{"native" if native else "wrapper"}.json',dict(utc=r.now(),error=err))
    finally:
        signal.alarm(0);r.save(SUP/stage/('native_exit.json' if native else 'child_exit.json'),dict(utc=r.now(),success=ok,error=err,wall_seconds=time.monotonic()-START,
            peak_RSS_bytes=max(peak,resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024),GPU_calls=0,original_cumulative_LMB_cap=True))
    if not ok:sys.exit(1)
if __name__=='__main__':run(sys.argv[1],'--native' in sys.argv)
