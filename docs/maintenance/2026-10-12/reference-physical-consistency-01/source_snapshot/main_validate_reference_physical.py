"""RPC0 independent raw corpus, matrix equations and brute-force NN audit."""
import hashlib
import importlib.metadata
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
from scipy.spatial.distance import cdist

MAIN=Path(__file__).resolve().parents[2]; SLAM=MAIN.parent/'RAP-SLAM'
DATA=MAIN.parent/'Datasets/data_odometry_velodyne/dataset'
BASE=MAIN/'docs/maintenance/2026-10-12/reference-physical-consistency-01'
MGR=MAIN/'docs/maintenance/2026-10-12/measured-gicp-registration-01'
CASES={'00':(2429,3373),'09':(0,1574)}; COUNTS={'00':4541,'09':1591}
ARMS=('G','G_transport','N','RI','W','J','K'); MAXIMA={}
def now(): return datetime.now(timezone.utc).isoformat()
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(p,obj):
    with Path(p).open('x',encoding='utf-8') as f: json.dump(obj,f,indent=2,allow_nan=False); f.write('\n')
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for block in iter(lambda:f.read(1048576),b''): h.update(block)
    return h.hexdigest()
def close(a,b,tol=1e-8,name='arithmetic'):
    a,b=np.asarray(a),np.asarray(b); assert a.shape==b.shape and np.isfinite(a).all() and np.isfinite(b).all()
    delta=float(np.max(np.abs(a-b))) if a.size else 0.; MAXIMA[name]=max(MAXIMA.get(name,0.),delta)
    assert delta<=tol,(name,delta,tol)
def source(s):
    date='2026-09-26/e0-frontend-01' if s=='00' else '2026-09-27/e0-heldout-01'
    return MAIN/'docs/maintenance'/date/f'full-{s}-A'
def raw(s,i): return DATA/'sequences'/s/'velodyne'/f'{i:06d}.bin'
def neighbors(s,i): return [n for n in range(i-1,i+2) if 0<=n<COUNTS[s]]
def pairs(): return [(s,a,b) for s,(i,j) in CASES.items() for a in neighbors(s,i) for b in neighbors(s,j)]
def locals_(): return [(s,i,b,side) for s,ij in CASES.items() for side,i in enumerate(ij) for b in neighbors(s,i) if i!=b]
def poses(p):
    lines=[line.split() for line in Path(p).read_text().splitlines() if line.strip()]; assert all(len(v)==12 for v in lines)
    out=np.broadcast_to(np.eye(4),(len(lines),4,4)).copy(); out[:,:3,:]=np.asarray(lines,float).reshape(-1,3,4); return out
def calib(s):
    rows=[line.split()[1:] for line in (DATA/'sequences'/s/'calib.txt').read_text().splitlines() if line.startswith('Tr:')]
    assert len(rows)==1; result=np.eye(4); result[:3,:]=np.asarray(rows[0],float).reshape(3,4); return result
def relative(a,b): return np.linalg.solve(a,b)
def transport(o,a,b,i,j,t): return np.linalg.solve(o[a],o[i]@t@np.linalg.solve(o[j],o[b]))
def corrected(p):
    axis=np.cross(p,np.array([0.,0.,1.])); lengths=np.linalg.norm(axis,axis=1); usable=lengths>1e-6
    result=p.copy(); axis=axis[usable]/lengths[usable,None]; theta=np.pi*.205/180; selected=p[usable]
    result[usable]=selected*np.cos(theta)+np.cross(axis,selected)*np.sin(theta)+axis*np.sum(axis*selected,axis=1)[:,None]*(1-np.cos(theta))
    return result
def rotation_angle(m):
    # Stable quaternion extraction independently of scipy.spatial.transform.
    trace=np.trace(m); pick=int(np.argmax([m[0,0],m[1,1],m[2,2],trace])); q=np.empty(4)
    if pick==3:
        q[:3]=[m[2,1]-m[1,2],m[0,2]-m[2,0],m[1,0]-m[0,1]]; q[3]=1+trace
    else:
        i=pick; j=(i+1)%3; k=(j+1)%3; q[i]=1-trace+2*m[i,i]; q[j]=m[j,i]+m[i,j]; q[k]=m[k,i]+m[i,k]; q[3]=m[k,j]-m[j,k]
    q/=np.linalg.norm(q); return float(2*np.arctan2(np.linalg.norm(q[:3]),abs(q[3])))
def inventory():
    paths=('oxts','timestamps.txt','velodyne/timestamps.txt','velodyne/timestamps_start.txt','velodyne/timestamps_end.txt',
        'calib_velo_to_cam.txt','calib_imu_to_velo.txt','calib_cam_to_cam.txt','tracklet_labels.xml','labels','archive_receipt.json')
    return {s:dict(directory_entries=sorted(p.name for p in (DATA/'sequences'/s).iterdir()),
        evidence_paths=[dict(path=str(DATA/'sequences'/s/n),exists=(DATA/'sequences'/s/n).exists()) for n in paths]) for s in CASES}
def repositories():
    result={}
    for name,p in [('main',MAIN),('slam',SLAM)]:
        def git(*args): return subprocess.check_output(['git','--no-optional-locks','-C',str(p),*args],text=True).strip()
        result[name]=dict(head=git('rev-parse','HEAD'),branch=git('branch','--show-current'),tracked_status=git('status','--short','--untracked-files=no').splitlines())
    return result
def verify():
    frozen=read(BASE/'freeze.json')
    for p,h in frozen['files'].items(): assert sha(p)==h,p
    assert frozen['packages']=={p:importlib.metadata.version(p) for p in ('numpy','scipy','gtsam')}
    assert frozen['repositories']==repositories() and frozen['local_evidence_inventory']==inventory()
    return frozen
def seal(folder,name):
    record=read(BASE/name); assert record['freeze_sha256']==sha(BASE/'freeze.json')
    assert record['files']=={str(p.relative_to(folder)):sha(p) for p in sorted(folder.rglob('*')) if p.is_file()}; return record
def preflight():
    verify(); fixtures=read(BASE/'preflight.json'); assert len(fixtures['cases'])==8
    for item in fixtures['cases']:
        m={k:np.asarray(item[k]) for k in ('tr','vi','vj','ci','cj','derived','odom','gauge','transfer')}; tr=m['tr']; o=m['odom']
        close(np.linalg.solve(tr,m['ci']@tr),m['vi'],name='synthetic_coordinate'); close(np.linalg.solve(tr,m['cj']@tr),m['vj'],name='synthetic_coordinate')
        direct=relative(m['vi'],m['vj']); close(np.linalg.solve(tr,np.linalg.solve(m['ci'],m['cj']@tr)),direct,name='synthetic_direction'); close(m['derived'],direct,name='synthetic_direction')
        converted=transport(o,0,3,1,2,direct); close(converted,relative(o[0],o[3]),name='synthetic_transfer'); close(converted,m['transfer'],name='synthetic_transfer')
        close(transport(m['gauge']@o,0,3,1,2,direct),converted,name='synthetic_gauge')
        p=np.asarray(item['points']); corr=corrected(p); delta=np.linalg.norm(corr-p,axis=1); bound=2*np.linalg.norm(p,axis=1)*np.sin(np.pi*.205/360)
        close(corr,item['corrected'],1e-10,'synthetic_correction'); close(delta,item['displacement'],1e-10,'synthetic_correction'); close(bound,item['bound'],1e-10,'synthetic_correction'); assert np.all(delta<=bound+1e-10)
    save(BASE/'preflight_validation.json',dict(utc=now(),passed=True,independent_cases=8,maxima=MAXIMA,independent_matrix_solve_and_Rodrigues=True,optimizer_neural_graph_calls=0))
    print('independent eight-fixture checks pass',flush=True)
def brute(query,target):
    distances=np.empty(len(query)); ids=np.empty(len(query),dtype=np.int64)
    for start in range(0,len(query),128):
        block=cdist(query[start:start+128],target,'euclidean'); indices=np.argmin(block,axis=1)
        ids[start:start+len(block)]=indices; distances[start:start+len(block)]=block[np.arange(len(block)),indices]
    return distances,ids
def stats(d,labels):
    groups=[]
    for label in range(16):
        values=d[np.flatnonzero(labels==label)]; n=len(values)
        groups.append(dict(label=label,count=n,eligible=n>=64,within1=int(sum(values<1)),outside1=int(sum(values>=1)),
            within2_5=int(sum(values<=2.5)),outside2_5=int(sum(values>2.5)),mean=float(np.sum(values)/n) if n else None))
    return dict(n=len(d),mean=float(np.sum(d)/len(d)),median=float(np.quantile(d,.5)),q90=float(np.quantile(d,.9)),
        overlap1=float(np.count_nonzero(d<1)/len(d)),overlap2_5=float(np.count_nonzero(d<=2.5)/len(d)),censored_mse=float(np.sum(np.minimum(d,2.5)**2)/len(d)),strata=groups)
def compare_stats(a,b):
    assert a['n']==b['n']
    for k in ('mean','median','q90','overlap1','overlap2_5','censored_mse'): close(a[k],b[k],1e-9,'distance_statistics')
    for left,right in zip(a['strata'],b['strata']):
        for k in ('label','count','eligible','within1','outside1','within2_5','outside2_5'): assert left[k]==right[k],(k,left,right)
        if left['mean'] is None: assert right['mean'] is None
        else: close(left['mean'],right['mean'],1e-9,'stratum_mean')
def classification(rows,local):
    agreement={}
    for s in CASES:
        t=float(np.quantile([r['disagreement_t'] for r in local if r['seq']==s],.5)); angle=float(np.quantile([r['disagreement_R'] for r in local if r['seq']==s],.5))
        agreement[s]=dict(t_median=t,R_median=angle,agrees=t<=.2 and angle<=1)
    cross={}
    for s in CASES:
        cross[s]={}; selected=[r for r in rows if r['seq']==s]
        for rep in ('raw','corrected'):
            pair_gaps=[]; group_gaps=[]
            for r in selected:
                g,w=[r['representations'][rep][name] for name in ('G','W')]; pair_gaps.append(g['symmetric_mean']-w['symmetric_mean'])
                for direction in ('forward','reverse'):
                    for left,right in zip(g[direction]['strata'],w[direction]['strata']):
                        if left['count']>=64: group_gaps.append(left['mean']-right['mean'])
            cross[s][rep]=dict(pairs=len(selected),median_reference_minus_geometry_distance=float(np.quantile(pair_gaps,.5)),pairs_gap_ge_half=int(np.count_nonzero(np.asarray(pair_gaps)>=.5)),
                eligible_return_strata=len(group_gaps),strata_gap_ge_half=int(np.count_nonzero(np.asarray(group_gaps)>=.5)),
                reference_median_overlap=float(np.quantile([r['representations'][rep]['G']['symmetric_overlap1'] for r in selected],.5)),
                W_median_overlap=float(np.quantile([r['representations'][rep]['W']['symmetric_overlap1'] for r in selected],.5)))
    flags={rep:(v['median_reference_minus_geometry_distance']>=.5 and v['pairs_gap_ge_half']>=5 and 2*v['strata_gap_ge_half']>v['eligible_return_strata']) for rep,v in cross['09'].items()}
    decision='AVAILABLE_BINDINGS_VALID_BROAD_09_CONFLICT_PHYSICAL_CAUSE_UNRESOLVED' if all(v['agrees'] for v in agreement.values()) and all(flags.values()) else 'BOUNDED_REFERENCE_PHYSICAL_CENSUS_COMPLETE_WITH_UNRESOLVED_PATTERN'
    return dict(local_agreement=agreement,cross_visit=cross,broad09_flags=flags,decision=decision,independent_physical_cause_certified=False)
def compare_structure(a,b):
    assert type(a)==type(b),(type(a),type(b))
    if isinstance(a,dict):
        assert a.keys()==b.keys()
        for k in a: compare_structure(a[k],b[k])
    elif isinstance(a,list):
        assert len(a)==len(b)
        for x,y in zip(a,b): compare_structure(x,y)
    elif isinstance(a,float): close(a,b,1e-8,'summary')
    else: assert a==b,(a,b)
def validate():
    started=now(); frozen=verify(); assert read(BASE/'preflight_validation.json')['passed']; bank=BASE/'bank'; out=BASE/'evaluation'
    bs=seal(bank,'bank_seal.json'); es=seal(out,'evaluation_seal.json'); results=read(BASE/'results.json'); census=read(bank/'census.json'); execution=read(bank/'execution.json')
    assert frozen['utc']<execution['started_utc']<=execution['utc']<bs['utc']<results['reference_read_started_utc']<results['utc']<es['utc']<started
    assert results['bank_seal_sha256']==sha(BASE/'bank_seal.json') and results['optimizer_calls']==0 and results['new_reference_or_system_metrics'] is False
    cloud={}; total_raw=0; assert len(census['scans'])==11
    for scan in census['scans']:
        s,i=scan['seq'],scan['frame']; assert i in sorted(set(neighbors(s,CASES[s][0])+neighbors(s,CASES[s][1])))
        file=raw(s,i); assert str(file)==scan['path'] and sha(file)==scan['sha256']; records=np.fromfile(file,dtype=np.dtype('<f4')).reshape(-1,4); total_raw+=len(records)
        radial=np.sqrt(np.sum(records[:,:3].astype(np.float64)**2,axis=1)); finite=np.isfinite(records).all(axis=1)
        codes=np.full(len(records),3,dtype=np.uint8); codes[~finite]=0; codes[finite&(radial<1.5)]=1; codes[finite&(radial>80)]=2
        candidates=np.flatnonzero(finite&(radial>=1.5)&(radial<=80)); seed=int(hashlib.sha256(f'RPC0|{s}|{i}'.encode()).hexdigest()[:16],16)
        selected=np.random.Generator(np.random.PCG64(seed)).choice(candidates,size=4096,replace=False); selected.sort(); codes[selected]=4; z=np.load(bank/s/f'{i:06d}.npz')
        assert np.array_equal(codes,z['reason_code']) and np.array_equal(selected,z['source_ids']) and np.array_equal(records[selected],z['selected_records'])
        p=records[selected,:3].astype(float); corr=corrected(p); close(p,z['raw'],0.,'raw_identity'); close(corr,z['corrected'],1e-10,'real_correction')
        angle=np.arctan2(p[:,1],p[:,0]); quad=np.clip(np.floor((angle+np.pi)*2/np.pi).astype(int),0,3); labels=(quad*4+2*(np.linalg.norm(p,axis=1)>=20)+(p[:,2]>=-1)).astype(np.uint8)
        assert np.array_equal(labels,z['strata']); delta=np.linalg.norm(corr-p,axis=1); bound=2*np.linalg.norm(p,axis=1)*np.sin(np.pi*.205/360)
        close(delta,z['displacement'],1e-10,'real_displacement'); close(bound,z['bound'],1e-10,'real_displacement'); assert np.all(delta<=bound+1e-10)
        assert scan['raw_records']==len(records) and scan['seed']==seed and scan['reason_counts']==np.bincount(codes,minlength=5).tolist() and scan['selected_strata_counts']==np.bincount(labels,minlength=16).tolist()
        close(scan['intensity_min'],records[selected,3].min(),0.,'raw_identity'); close(scan['intensity_max'],records[selected,3].max(),0.,'raw_identity')
        close(scan['max_intrinsic_displacement'],delta.max(),1e-10,'real_displacement'); close(scan['max_intrinsic_bound'],bound.max(),1e-10,'real_displacement')
        cloud[s,i]=dict(raw=p,corrected=corr,strata=labels,displacement=delta)
    assert len(cloud)==11 and census['evidence_inventory']==inventory()
    assert census['exclusions']==[dict(seq='09',endpoint=0,offset=-1,reason='outside available frames')]
    logical=0; unique=0; aliases=0; rebuilt_local=[]; rebuilt_cross=[]
    for s,(i,j) in CASES.items():
        frame=read(source(s)/'source_frames.json'); stamps=np.asarray([float(line) for line in (DATA/'sequences'/s/'times.txt').read_text().splitlines() if line.strip()]); files=sorted(raw(s,0).parent.glob('*.bin'))
        assert [int(p.stem) for p in files]==list(range(COUNTS[s]))==frame['source_frame_ids'] and [str(p) for p in files]==frame['scan_files'] and np.array_equal(stamps,np.asarray(frame['timestamps'])) and np.all(np.diff(stamps)>0)
        camera=poses(DATA/'poses'/f'{s}.txt'); odom=poses(source(s)/'odom_poses.txt'); tr=calib(s); assert len(camera)==len(odom)==len(stamps)==COUNTS[s]
        v=np.asarray([np.linalg.solve(tr,m@tr) for m in camera]); g0=relative(v[i],v[j]); config=read(source(s)/'summary.json')['config']; assert config['deskew'] is False and config['apply_kitti_205'] is True
        compare_structure(dict(n=len(stamps),filename_path_ID_time_equal=True,min_dt=float(np.diff(stamps).min()),max_dt=float(np.diff(stamps).max()),median_dt=float(np.median(np.diff(stamps))),deskew=False,apply_kitti_205=True,point_time_observed=False),census['bindings'][s])
        alternative=np.linalg.solve(tr,np.linalg.solve(camera[i],camera[j]@tr)); close(g0,alternative,1e-8,'relative_conjugation'); close(tr@v@np.linalg.solve(tr,np.eye(4)),camera,1e-8,'absolute_roundtrip')
        for k,value in dict(relative_conjugation_max=np.max(abs(g0-alternative)),absolute_roundtrip_max=np.max(abs(tr@v@np.linalg.solve(tr,np.eye(4))-camera)),calib_orthogonality=np.max(abs(tr[:3,:3].T@tr[:3,:3]-np.eye(3))),reference_rotation_defect=np.max(abs(v[:,:3,:3].transpose(0,2,1)@v[:,:3,:3]-np.eye(3)))).items(): close(value,results['math'][s][k],1e-8,'reported_defects')
        fixed={a:np.asarray(read(MGR/f'bank/{s}_000.json')['predictions'][a]) for a in ('N','RI','W','J','K')}; axis=next(a for a in results['axes'] if a['seq']==s)
        e=g0[:3,3]-fixed['N'][:3,3]; world=v[i,:3,:3]@e; cam=camera[i,:3,:3]@tr[:3,:3]@e; assert axis['anchor']==[i,j] and axis['axis_is_not_independent_gravity'] is True
        for k,value in dict(reference_pose=g0,translation_norm=np.linalg.norm(e),reference_minus_N_in_i_lidar=e,in_lidar0_world=world,in_camera0_world=cam,i_lidar_component_fractions=abs(e)/np.linalg.norm(e),lidar0_component_fractions=abs(world)/np.linalg.norm(world),elapsed_seconds=stamps[j]-stamps[i]).items(): close(value,axis[k],1e-8,'axis_vectors')
        for _,a,b in [p for p in pairs() if p[0]==s]:
            stored=next(r for r in results['rows'] if (r['seq'],r['a'],r['b'])==(s,a,b)); za,zb=cloud[s,a],cloud[s,b]; transforms={arm:transport(odom,a,b,i,j,t) for arm,t in fixed.items()}
            transforms['G']=relative(v[a],v[b]); transforms['G_transport']=transport(odom,a,b,i,j,g0); archive=np.load(out/s/f'{a:06d}_{b:06d}.npz'); rebuilt=dict(stored,representations={}); cached={}; original={}
            for rep in ('raw','corrected'):
                rebuilt['representations'][rep]={}
                for arm in ARMS:
                    close(transforms[arm],stored['transforms'][arm],1e-8,'real_transfer'); t=np.asarray(stored['transforms'][arm]); p=za[rep]; q=zb[rep]@t[:3,:3].T+t[:3,3]; label=f'{rep}_{arm}'; key=(rep,t.tobytes())
                    if key in cached: alias,df,dr,ip,iq=cached[key]; aliases+=1
                    else:
                        df,ip=brute(q,p); dr,iq=brute(p,q); unique+=len(df)+len(dr); cached[key]=(label,df,dr,ip,iq); alias=None
                    logical+=len(df)+len(dr)
                    for suffix,value in [('forward',df),('reverse',dr)]: close(value,archive[label+'_'+suffix],1e-8,'nearest_distances')
                    for suffix,ids in [('ip',ip),('iq',iq)]: assert np.array_equal(ids,archive[label+'_'+suffix]),('NN IDs',s,a,b,rep,arm,suffix)
                    f,rr=stats(df,zb['strata']),stats(dr,za['strata']); values=np.concatenate([df,dr]); rec=stored['representations'][rep][arm]; compare_stats(f,rec['forward']); compare_stats(rr,rec['reverse']); assert alias==rec['alias']
                    obj=dict(forward=f,reverse=rr,symmetric_mean=float(values.mean()),symmetric_median=float(np.quantile(values,.5)),symmetric_q90=float(np.quantile(values,.9)),symmetric_overlap1=float(np.count_nonzero(values<1)/len(values)),alias=alias)
                    for k in ('symmetric_mean','symmetric_median','symmetric_q90','symmetric_overlap1'): close(obj[k],rec[k],1e-8,'symmetric_statistics')
                    rebuilt['representations'][rep][arm]=obj
                    if rep=='raw': original[arm]=(df,dr)
                    else:
                        operator=np.linalg.norm(t[:3,:3],2); oldf,oldr=original[arm]; assert np.all(abs(df-oldf)<=operator*zb['displacement']+za['displacement'].max()+1e-8) and np.all(abs(dr-oldr)<=za['displacement']+operator*zb['displacement'].max()+1e-8)
            rebuilt_cross.append(rebuilt)
        for _,a,b,side in [p for p in locals_() if p[0]==s]:
            stored=next(r for r in results['local_rows'] if (r['seq'],r['a'],r['b'])==(s,a,b)); g=relative(v[a],v[b]); k=relative(odom[a],odom[b]); close(g,stored['GT'],1e-8,'local_transform'); close(k,stored['odom'],1e-8,'local_transform')
            assert stored['side']==side and stored['offset']==b-a and stored['causal']==(b<a); td=float(np.linalg.norm(g[:3,3]-k[:3,3])); rd=float(rotation_angle(g[:3,:3].T@k[:3,:3])*180/np.pi)
            close(td,stored['disagreement_t'],1e-8,'local_disagreement'); close(rd,stored['disagreement_R'],1e-8,'local_disagreement'); close(stamps[b]-stamps[a],stored['dt'],1e-10,'local_timing')
            rebuilt_local.append(dict(stored,disagreement_t=td,disagreement_R=rd)); archive=np.load(out/s/f'local_{a:06d}_{b:06d}.npz'); za,zb=cloud[s,a],cloud[s,b]
            for rep in ('raw','corrected'):
                for arm,independent in [('GT',g),('odom',k)]:
                    t=np.asarray(stored['GT'] if arm=='GT' else stored['odom']); p=za[rep]; q=zb[rep]@t[:3,:3].T+t[:3,3]; df,ip=brute(q,p); dr,iq=brute(p,q); logical+=len(df)+len(dr); unique+=len(df)+len(dr)
                    for suffix,val in [('forward',df),('reverse',dr)]: close(val,archive[f'{rep}_{arm}_{suffix}'],1e-8,'nearest_distances')
                    for suffix,val in [('ip',ip),('iq',iq)]: assert np.array_equal(val,archive[f'{rep}_{arm}_{suffix}']),('local NN IDs',s,a,b,rep,arm,suffix)
                    rec=stored['representations'][rep][arm]; values=np.concatenate([df,dr]); close(values.mean(),rec['mean'],1e-8,'local_statistics'); close(np.mean(values<1),rec['overlap1'],1e-8,'local_statistics')
                    envelope=np.linalg.norm(independent[:3,3])+160*np.sin(rotation_angle(independent[:3,:3])/2); close(envelope,rec['pose_implied_frame_displacement_envelope'],1e-8,'local_envelope')
        print('independent raw/calibration/brute geometry pass',s,flush=True)
    assert len(rebuilt_cross)==len(results['rows'])==15 and len(rebuilt_local)==len(results['local_rows'])==7 and len(results['axes'])==2
    independent=classification(rebuilt_cross,rebuilt_local); compare_structure(independent,results['summary']); verify()
    save(BASE/'validation.json',dict(utc=now(),passed=True,scans=11,raw_records=total_raw,retained_points=11*4096,cross_pairs=15,local_pairs=7,logical_directed_NN_records=logical,unique_brute_NN_records=unique,explicit_aliases=aliases,maxima=MAXIMA,summary=independent,
        scope='independent raw-ID census/Rodrigues/general-solve transforms/brute cdist distances/tie IDs/statistics/axes/classification; stored transforms used only after independent equation check; no optimizer or independent physical provenance',optimizer_neural_graph_calls=0,reference_truth_certified=False))
    print('all independent RPC0 checks pass;',independent['decision'],flush=True)
