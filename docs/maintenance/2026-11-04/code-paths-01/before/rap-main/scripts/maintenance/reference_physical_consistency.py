"""RPC0 fixed-return/source/reference diagnostic, zero pose-fitting calls."""
import hashlib
import importlib.metadata
import json
import resource
import signal
import sys
import time
import traceback
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation
import scan_level_graph_feasibility as c

MAIN=c.MAIN; DATA=c.DATA; SLAM=c.SLAM
BASE=MAIN/'docs/maintenance/2026-10-12/reference-physical-consistency-01'
MGR=MAIN/'docs/maintenance/2026-10-12/measured-gicp-registration-01'
TID=MAIN/'docs/maintenance/2026-10-05/temporal-identity-audit-01'
SUP=BASE/'supervision'; BANK=BASE/'bank'; OUT=BASE/'evaluation'
CASES={'00':(2429,3373),'09':(0,1574)}
ARMS=('G','G_transport','N','RI','W','J','K')
read,save,sha,now=c.read,c.save,c.sha,c.now

def raw(s,i): return DATA/'sequences'/s/'velodyne'/f'{i:06d}.bin'
def offsets(s,i): return [i+d for d in (-1,0,1) if 0<=i+d<c.SEQS[s]]
def needed(): return {s:sorted(set(offsets(s,i)+offsets(s,j))) for s,(i,j) in CASES.items()}
def pair_rows(): return [dict(seq=s,a=a,b=b,anchor_i=i,anchor_j=j) for s,(i,j) in CASES.items() for a in offsets(s,i) for b in offsets(s,j)]
def local_rows():
    return [dict(seq=s,a=i,b=b,side=side,offset=b-i,causal=b<i) for s,ij in CASES.items() for side,i in enumerate(ij) for b in offsets(s,i) if b!=i]
def seed(s,i): return int.from_bytes(hashlib.sha256(f'RPC0|{s}|{i}'.encode()).digest()[:8],'big')
def choose(s,i,rows):
    finite=np.isfinite(rows).all(1); radius=np.linalg.norm(rows[:,:3].astype(float),axis=1)
    code=np.full(len(rows),3,dtype=np.uint8); code[~finite]=0; code[finite&(radius<1.5)]=1; code[finite&(radius>80)]=2
    eligible=np.flatnonzero(finite&(radius>=1.5)&(radius<=80)); assert len(eligible)>=4096
    ids=np.sort(np.random.Generator(np.random.PCG64(seed(s,i))).choice(eligible,4096,replace=False)); code[ids]=4
    p=rows[ids,:3].astype(float); angle=np.arctan2(p[:,1],p[:,0]); quadrant=np.minimum(np.floor((angle+np.pi)/(np.pi/2)).astype(int),3)
    quadrant=np.maximum(quadrant,0); band=(np.linalg.norm(p,axis=1)>=20).astype(int); high=(p[:,2]>=-1).astype(int)
    return ids,code,(quadrant*4+band*2+high).astype(np.uint8)
def corrected(p):
    from rap_slam.real_dataset import kitti_vertical_correction
    return kitti_vertical_correction(p,.205)
def inventory():
    result={}
    for s in CASES:
        root=DATA/'sequences'/s
        names=('oxts','timestamps.txt','velodyne/timestamps.txt','velodyne/timestamps_start.txt','velodyne/timestamps_end.txt',
            'calib_velo_to_cam.txt','calib_imu_to_velo.txt','calib_cam_to_cam.txt','tracklet_labels.xml','labels','archive_receipt.json')
        result[s]=dict(directory_entries=sorted(p.name for p in root.iterdir()),
            evidence_paths=[dict(path=str(root/x),exists=(root/x).exists()) for x in names])
    return result
def calibration(s):
    line=next(v for v in (DATA/'sequences'/s/'calib.txt').read_text().splitlines() if v.startswith('Tr:'))
    tr=np.eye(4); tr[:3]=np.asarray(line.split(':',1)[1].split(),float).reshape(3,4); return tr
def sensor_reference(s): return np.linalg.inv(calibration(s))@c.load(DATA/'poses'/f'{s}.txt')@calibration(s)
def transfer(o,a,b,i,j,t): return np.linalg.inv(o[a])@o[i]@t@np.linalg.inv(o[j])@o[b]
def nearest(q,p):
    dist,indices=cKDTree(p).query(q,k=2,workers=1); out=indices[:,0].copy(); distances=dist[:,0].copy()
    for k in np.flatnonzero(dist[:,0]==dist[:,1]):
        ids=np.asarray(cKDTree(p).query_ball_point(q[k],np.nextafter(dist[k,1],np.inf)),int)
        squared=np.sum((p[ids]-q[k])**2,axis=1); keep=np.lexsort((ids,squared))[0]; out[k]=ids[keep]; distances[k]=np.sqrt(squared[keep])
    return distances,out
def summarize(d,labels):
    strata=[]
    for k in range(16):
        values=d[labels==k]; n=len(values)
        strata.append(dict(label=k,count=n,eligible=n>=64,within1=int(np.count_nonzero(values<1)),outside1=int(np.count_nonzero(values>=1)),
            within2_5=int(np.count_nonzero(values<=2.5)),outside2_5=int(np.count_nonzero(values>2.5)),
            mean=None if not n else float(values.mean())))
    return dict(n=len(d),mean=float(d.mean()),median=float(np.median(d)),q90=float(np.quantile(d,.9)),
        overlap1=float(np.mean(d<1)),overlap2_5=float(np.mean(d<=2.5)),censored_mse=float(np.mean(np.minimum(d,2.5)**2)),strata=strata)
def preserve():
    original=read(MGR/'freeze.json')['files']; files=dict(original)
    for p,h in original.items(): assert sha(p)==h,p
    for row in read(MGR/'DELIVERY_SEAL.json')['files']:
        p=MGR/row['path']; assert sha(p)==row['sha256']; files[str(p)]=row['sha256']
    files[str(MGR/'DELIVERY_SEAL.json')]=sha(MGR/'DELIVERY_SEAL.json')
    return files
def verify():
    f=read(BASE/'freeze.json')
    for p,h in f['files'].items(): assert sha(p)==h,p
    assert f['packages']=={p:importlib.metadata.version(p) for p in ('numpy','scipy','gtsam')}
    assert f['repositories']==c.repositories()
    assert f['local_evidence_inventory']==inventory()
def freeze():
    files=preserve(); paths=[BASE/n for n in ('PROTOCOL.md','OWNER_SCOPE.md','SOURCE_NOTES.md')]
    paths += [Path(__file__),Path(__file__).with_name('validate_reference_physical.py'),Path(__file__).with_name('invoke_mgr_supervised_wsl.ps1'),
        SLAM/'rap_slam/real_dataset.py',SLAM/'rap_slam/odometry.py',SLAM/'scripts/run_pipeline.py']
    paths += [TID/n for n in ('REPORT.md','freeze.json','bank_seal.json','results.json','validation.json')]
    for s,ids in needed().items(): paths += [raw(s,i) for i in ids]
    for s in CASES:
        paths += [DATA/'sequences'/s/n for n in ('calib.txt','times.txt')]
        paths += [DATA/'poses'/f'{s}.txt']+[c.src(s)/n for n in ('source_frames.json','summary.json','odom_poses.txt')]
    for p in paths: files[str(p)]=sha(p)
    snapshot=BASE/'source_snapshot'; snapshot.mkdir()
    for p in paths:
        if p.suffix in ('.py','.ps1'):
            name=('slam_'+p.parent.name+'_'+p.name if SLAM in p.parents else 'main_'+p.name)
            (snapshot/name).write_bytes(p.read_bytes())
    save(BASE/'freeze.json',dict(utc=now(),files=files,packages={p:importlib.metadata.version(p) for p in ('numpy','scipy','gtsam')},
        repositories=c.repositories(),cases=CASES,needed=needed(),pairs=pair_rows(),local_pairs=local_rows(),local_evidence_inventory=inventory(),
        previous_MGR_delivery_entries=344,cap_seconds=900,cap_RSS_bytes=2*2**30,cap_artifact_bytes=256*2**20))
    (BASE/'INCOMPLETE').write_text('RPC0 corpus, fixed-pose evaluation and independent diagnosis pending.\n')
    print('RPC0 frozen',len(files),'identities;11 raw scans,15 revisit/7 adjacent pairs',flush=True)
def preflight():
    verify(); rng=np.random.default_rng(20261012); records=[]
    for k in range(8):
        def pose():
            t=np.eye(4); t[:3,:3]=Rotation.from_rotvec(rng.normal(size=3)*.3).as_matrix(); t[:3,3]=rng.normal(size=3); return t
        tr,vi,vj,oa,ob,h=pose(),pose(),pose(),pose(),pose(),pose()
        ci,cj=tr@vi@np.linalg.inv(tr),tr@vj@np.linalg.inv(tr); derived=np.linalg.inv(tr)@np.linalg.inv(ci)@cj@tr
        known=np.linalg.inv(vi)@vj; error=float(np.max(abs(known-derived))); assert error<=1e-8
        o=np.asarray([oa,vi,vj,ob]); tij=np.linalg.inv(vi)@vj; converted=transfer(o,0,3,1,2,tij)
        assert np.max(abs(converted-np.linalg.inv(oa)@ob))<=1e-8
        assert np.max(abs(transfer(h@o,0,3,1,2,tij)-converted))<=1e-8
        p=rng.uniform(-20,20,(128,3)); corr=corrected(p); displacement=np.linalg.norm(corr-p,axis=1)
        bound=2*np.linalg.norm(p,axis=1)*np.sin(np.deg2rad(.205)/2); assert np.max(displacement-bound)<=1e-10
        records.append(dict(tr=tr.tolist(),vi=vi.tolist(),vj=vj.tolist(),ci=ci.tolist(),cj=cj.tolist(),derived=derived.tolist(),
            odom=o.tolist(),gauge=h.tolist(),transfer=converted.tolist(),points=p.tolist(),corrected=corr.tolist(),displacement=displacement.tolist(),bound=bound.tolist()))
    save(BASE/'preflight.json',dict(utc=now(),cases=records)); print('coordinate/transfer/correction-bound fixtures pass',flush=True)
def seal(folder,name): save(BASE/name,dict(utc=now(),freeze_sha256=sha(BASE/'freeze.json'),files={str(p.relative_to(folder)):sha(p) for p in sorted(folder.rglob('*')) if p.is_file()}))
def check_seal(folder,name):
    value=read(BASE/name); assert value['freeze_sha256']==sha(BASE/'freeze.json')
    assert value['files']=={str(p.relative_to(folder)):sha(p) for p in sorted(folder.rglob('*')) if p.is_file()}
def bank():
    verify(); assert read(BASE/'preflight_validation.json')['passed']; BANK.mkdir(); census=[]; bindings={}; started=now()
    for s,ids in needed().items():
        (BANK/s).mkdir(); frames=read(c.src(s)/'source_frames.json'); ts=np.loadtxt(DATA/'sequences'/s/'times.txt')
        actual=sorted(int(p.stem) for p in raw(s,0).parent.glob('*.bin')); assert actual==list(range(c.SEQS[s]))==frames['source_frame_ids']
        assert frames['scan_files']==[str(raw(s,i)) for i in actual] and np.array_equal(ts,frames['timestamps']) and np.all(np.diff(ts)>0)
        counts=[sum(bool(line.strip()) for line in p.read_text().splitlines()) for p in (DATA/'poses'/f'{s}.txt',c.src(s)/'odom_poses.txt')]
        assert counts[0]==counts[1]==len(ts)==c.SEQS[s]
        cfg=read(c.src(s)/'summary.json')['config']; assert cfg['deskew'] is False and cfg['apply_kitti_205'] is True
        bindings[s]=dict(n=len(ts),filename_path_ID_time_equal=True,min_dt=float(np.diff(ts).min()),max_dt=float(np.diff(ts).max()),median_dt=float(np.median(np.diff(ts))),
            deskew=False,apply_kitti_205=True,point_time_observed=False)
        for i in ids:
            body=raw(s,i).read_bytes(); assert len(body)%16==0; full=np.frombuffer(body,dtype='<f4').reshape(-1,4)
            selected,code,strata=choose(s,i,full); p=full[selected,:3].astype(float); corrected_p=corrected(p)
            displacement=np.linalg.norm(corrected_p-p,axis=1); bound=2*np.linalg.norm(p,axis=1)*np.sin(np.deg2rad(.205)/2)
            assert np.max(displacement-bound)<=1e-10
            np.savez(BANK/s/f'{i:06d}.npz',source_ids=selected,reason_code=code,selected_records=full[selected],raw=p,corrected=corrected_p,
                strata=strata,displacement=displacement,bound=bound)
            counts=np.bincount(code,minlength=5); assert counts.sum()==len(full) and counts[4]==4096
            census.append(dict(seq=s,frame=i,path=str(raw(s,i)),sha256=sha(raw(s,i)),raw_records=len(full),seed=seed(s,i),reason_counts=counts.tolist(),
                selected_strata_counts=np.bincount(strata,minlength=16).tolist(),intensity_min=float(full[selected,3].min()),intensity_max=float(full[selected,3].max()),
                max_intrinsic_displacement=float(displacement.max()),max_intrinsic_bound=float(bound.max())))
        cap(); print('raw source-ID corpus',s,len(ids),flush=True)
    excluded=[dict(seq=s,endpoint=v,offset=d,reason='outside available frames') for s,ij in CASES.items() for v in ij for d in (-1,0,1) if not 0<=v+d<c.SEQS[s]]
    save(BANK/'census.json',dict(scans=census,bindings=bindings,exclusions=excluded,pairs=pair_rows(),local_pairs=local_rows(),evidence_inventory=inventory(),
        reason_labels=['nonfinite','near_range','far_range','cap_excluded','selected']))
    save(BANK/'execution.json',dict(started_utc=started,utc=now())); seal(BANK,'bank_seal.json'); print('physical-return corpus sealed before new numerical reference geometry',flush=True)
def angles(a,b): return float(np.degrees(Rotation.from_matrix(a[:3,:3].T@b[:3,:3]).magnitude()))
def evaluate():
    verify(); check_seal(BANK,'bank_seal.json'); OUT.mkdir(); started=now(); rows=[]; local=[]; axis=[]; maxbound=0.; math={}
    for s,(i,j) in CASES.items():
        (OUT/s).mkdir(); tr=calibration(s); camera=c.load(DATA/'poses'/f'{s}.txt'); v=sensor_reference(s); odom=c.load(c.src(s)/'odom_poses.txt')
        g0=np.linalg.inv(v[i])@v[j]; alternative=np.linalg.inv(tr)@np.linalg.inv(camera[i])@camera[j]@tr
        assert np.max(abs(g0-alternative))<=1e-8
        math[s]=dict(relative_conjugation_max=float(np.max(abs(g0-alternative))),absolute_roundtrip_max=float(np.max(abs(tr@v@np.linalg.inv(tr)-camera))),
            calib_orthogonality=float(np.max(abs(tr[:3,:3].T@tr[:3,:3]-np.eye(3)))),reference_rotation_defect=float(np.max(abs(v[:,:3,:3].transpose(0,2,1)@v[:,:3,:3]-np.eye(3)))))
        pred=read(MGR/f'bank/{s}_000.json'); fixed={a:np.asarray(pred['predictions'][a]) for a in ('N','RI','W','J','K')}
        e=g0[:3,3]-fixed['N'][:3,3]; velo0=v[i,:3,:3]@e; cam0=camera[i,:3,:3]@tr[:3,:3]@e
        axis.append(dict(seq=s,anchor=[i,j],elapsed_seconds=float(np.loadtxt(DATA/'sequences'/s/'times.txt')[j]-np.loadtxt(DATA/'sequences'/s/'times.txt')[i]),
            reference_pose=g0.tolist(),translation_norm=float(np.linalg.norm(e)),reference_minus_N_in_i_lidar=e.tolist(),in_lidar0_world=velo0.tolist(),in_camera0_world=cam0.tolist(),
            i_lidar_component_fractions=(abs(e)/np.linalg.norm(e)).tolist(),lidar0_component_fractions=(abs(velo0)/np.linalg.norm(velo0)).tolist(),
            axis_is_not_independent_gravity=True))
        for pair in [r for r in pair_rows() if r['seq']==s]:
            a,b=pair['a'],pair['b']; z1=np.load(BANK/s/f'{a:06d}.npz'); z2=np.load(BANK/s/f'{b:06d}.npz')
            poses={name:transfer(odom,a,b,i,j,t) for name,t in fixed.items()}; poses['G']=np.linalg.inv(v[a])@v[b]; poses['G_transport']=transfer(odom,a,b,i,j,g0)
            row=dict(pair,transforms={name:poses[name].tolist() for name in ARMS},representations={}); arrays={}; cached={}
            for rep in ('raw','corrected'):
                p,q=z1[rep],z2[rep]; row['representations'][rep]={}
                for name in ARMS:
                    t=poses[name]; key=(rep,t.tobytes()); qq=q@t[:3,:3].T+t[:3,3]; label=f'{rep}_{name}'
                    if key in cached:
                        source,forward,reverse,ip,iq=cached[key]; alias=source
                    else:
                        forward,ip=nearest(qq,p); reverse,iq=nearest(p,qq); cached[key]=(label,forward,reverse,ip,iq); alias=None
                    arrays[label+'_forward']=forward; arrays[label+'_reverse']=reverse; arrays[label+'_ip']=ip; arrays[label+'_iq']=iq
                    f=summarize(forward,z2['strata']); rr=summarize(reverse,z1['strata']); combined=np.r_[forward,reverse]
                    row['representations'][rep][name]=dict(forward=f,reverse=rr,symmetric_mean=float(combined.mean()),symmetric_median=float(np.median(combined)),symmetric_q90=float(np.quantile(combined,.9)),
                        symmetric_overlap1=float(np.mean(combined<1)),alias=alias)
                    if rep=='corrected':
                        oldf=arrays[f'raw_{name}_forward']; oldr=arrays[f'raw_{name}_reverse']; opnorm=np.linalg.norm(t[:3,:3],2)
                        bf=opnorm*z2['displacement']+z1['displacement'].max(); br=z1['displacement']+opnorm*z2['displacement'].max()
                        excess=max(float(np.max(abs(forward-oldf)-bf)),float(np.max(abs(reverse-oldr)-br))); assert excess<=1e-8; maxbound=max(maxbound,excess)
            np.savez(OUT/s/f'{a:06d}_{b:06d}.npz',**arrays); rows.append(row)
        for pair in [r for r in local_rows() if r['seq']==s]:
            a,b=pair['a'],pair['b']; g=np.linalg.inv(v[a])@v[b]; k=np.linalg.inv(odom[a])@odom[b]
            za=np.load(BANK/s/f'{a:06d}.npz'); zb=np.load(BANK/s/f'{b:06d}.npz'); row=dict(pair,GT=g.tolist(),odom=k.tolist(),
                disagreement_t=float(np.linalg.norm(g[:3,3]-k[:3,3])),disagreement_R=angles(g,k),representations={})
            stamps=np.loadtxt(DATA/'sequences'/s/'times.txt'); row['dt']=float(stamps[b]-stamps[a]); arrays={}
            for rep in ('raw','corrected'):
                row['representations'][rep]={}
                for name,t in [('GT',g),('odom',k)]:
                    p=za[rep]; qq=zb[rep]@t[:3,:3].T+t[:3,3]; df,ip=nearest(qq,p); dr,iq=nearest(p,qq)
                    for key,value in [('forward',df),('reverse',dr),('ip',ip),('iq',iq)]: arrays[f'{rep}_{name}_{key}']=value
                    rotation=float(Rotation.from_matrix(t[:3,:3]).magnitude())
                    row['representations'][rep][name]=dict(mean=float(np.r_[df,dr].mean()),overlap1=float(np.mean(np.r_[df,dr]<1)),
                        pose_implied_frame_displacement_envelope=float(np.linalg.norm(t[:3,3])+160*np.sin(rotation/2)))
            np.savez(OUT/s/f'local_{a:06d}_{b:06d}.npz',**arrays); local.append(row)
        cap(); print('fixed-pose geometry complete',s,flush=True)
    summary=classify(rows,local)
    value=dict(utc=now(),reference_read_started_utc=started,bank_seal_sha256=sha(BASE/'bank_seal.json'),math=math,rows=rows,local_rows=local,
        axes=axis,max_intrinsic_NN_bound_excess=maxbound,summary=summary,optimizer_calls=0,new_reference_or_system_metrics=False)
    save(BASE/'results.json',value); seal(OUT,'evaluation_seal.json'); print(summary,flush=True)
def classify(rows,local):
    localflag={s:dict(t_median=float(np.median([v['disagreement_t'] for v in local if v['seq']==s])),
        R_median=float(np.median([v['disagreement_R'] for v in local if v['seq']==s]))) for s in CASES}
    for v in localflag.values(): v['agrees']=v['t_median']<=.2 and v['R_median']<=1
    summaries={}
    for s in CASES:
        summaries[s]={}
        for rep in ('raw','corrected'):
            selected=[r for r in rows if r['seq']==s]; gaps=[]; stratum_gaps=[]
            for row in selected:
                g,w=row['representations'][rep]['G'],row['representations'][rep]['W']; gaps.append(g['symmetric_mean']-w['symmetric_mean'])
                for direction in ('forward','reverse'):
                    for left,right in zip(g[direction]['strata'],w[direction]['strata']):
                        assert left['count']==right['count']
                        if left['eligible']: stratum_gaps.append(left['mean']-right['mean'])
            summaries[s][rep]=dict(pairs=len(selected),median_reference_minus_geometry_distance=float(np.median(gaps)),pairs_gap_ge_half=sum(x>=.5 for x in gaps),
                eligible_return_strata=len(stratum_gaps),strata_gap_ge_half=sum(x>=.5 for x in stratum_gaps),
                reference_median_overlap=float(np.median([r['representations'][rep]['G']['symmetric_overlap1'] for r in selected])),
                W_median_overlap=float(np.median([r['representations'][rep]['W']['symmetric_overlap1'] for r in selected])))
    flags={rep:(v['median_reference_minus_geometry_distance']>=.5 and v['pairs_gap_ge_half']>=5 and v['strata_gap_ge_half']>.5*v['eligible_return_strata']) for rep,v in summaries['09'].items()}
    complete=all(v['agrees'] for v in localflag.values()) and all(flags.values())
    decision='AVAILABLE_BINDINGS_VALID_BROAD_09_CONFLICT_PHYSICAL_CAUSE_UNRESOLVED' if complete else 'BOUNDED_REFERENCE_PHYSICAL_CENSUS_COMPLETE_WITH_UNRESOLVED_PATTERN'
    return dict(local_agreement=localflag,cross_visit=summaries,broad09_flags=flags,decision=decision,independent_physical_cause_certified=False)
def usage(): return dict(wall_seconds=time.monotonic()-START,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
    artifact_bytes=sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file()),optimizer_neural_graph_calls=0)
def cap():
    u=usage(); assert u['peak_RSS_bytes']<=2*2**30 and u['artifact_bytes']<=256*2**20
    if (SUP/'host_latest.json').exists(): assert read(SUP/'host_latest.json')['headroom_bytes']>=4*2**30
def run(stage):
    global START
    START=time.monotonic(); used=sum(read(p)['wall_seconds'] for p in SUP.glob('*/child_exit.json')); assert used<900
    signal.signal(signal.SIGALRM,lambda a,b:(_ for _ in ()).throw(TimeoutError('RPC0 remaining combined payload cap'))); signal.alarm(max(1,int(900-used)))
    success=False; error=None
    try:
        cap()
        if stage.startswith('validate'):
            import validate_reference_physical as v
            {'validate_preflight':v.preflight,'validate':v.validate}[stage]()
        else: {'freeze':freeze,'preflight':preflight,'bank':bank,'evaluate':evaluate}[stage]()
        cap(); success=True
    except BaseException as ex:
        error=repr(ex); traceback.print_exc(); save(BASE/f'FAILURE_{stage}.json',dict(utc=now(),error=error,**usage()))
    finally:
        signal.alarm(0); save(SUP/stage/'child_exit.json',dict(utc=now(),success=success,error=error,full_resource_capture=True,**usage()))
    if not success: sys.exit(1)
if __name__=='__main__':
    sys.modules['reference_physical_consistency']=sys.modules[__name__]; run(sys.argv[1])
