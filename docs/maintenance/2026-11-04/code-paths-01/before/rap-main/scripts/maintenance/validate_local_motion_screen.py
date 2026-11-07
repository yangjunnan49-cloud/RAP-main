"""Independent GT-free reconstruction and final GT/decision validation."""
import hashlib,resource,sys,time
from pathlib import Path
import numpy as np
from scipy.linalg import polar
import local_motion_common as c
from validate_local_motion_feasibility_v2 import horn,normalize,decode,icp,causal
from validate_local_motion_source_binding import reconstruct
B=c.SCREEN
ARMS=('R3','R2','G2','G3','KISS')

def load_poses(path,n):
    a=np.array([[float(x) for x in line.split()] for line in Path(path).read_text().splitlines() if line.strip()])
    assert a.shape==(n,12) and np.isfinite(a).all();p=np.tile(np.eye(4),(n,1,1));p[:,:3]=a.reshape(n,3,4);return p
def error(truth,pred):
    e=np.linalg.solve(truth,pred);q,_=polar(e[:3,:3]);assert np.linalg.det(q)>0
    sine=np.linalg.norm([q[2,1]-q[1,2],q[0,2]-q[2,0],q[1,0]-q[0,1]])/2
    cosine=(np.trace(q)-1)/2
    return dict(translation_m=float(np.sqrt(e[:3,3]@e[:3,3])),rotation_deg=float(np.arctan2(sine,cosine)*180/np.pi))
def aggregate(rows):
    assert len(rows)==58;primary={};gates={};safety={};groups={s:[r for r in rows if r['seq']==s] for s in c.SEQS}
    assert [len(groups[s]) for s in c.SEQS]==[22,13,5,5,7,6]
    for a in ('KISS','G2','G3','R2'):
        gain=[r['errors'][a]['translation_m']-r['errors']['R3']['translation_m'] for r in rows]
        relative=[g/max(r['errors'][a]['translation_m'],1e-6) for g,r in zip(gain,rows)]
        count=sum(g>0 for g in gain);median=float(np.median(gain));frac=count/58;rel=float(np.median(relative))
        passed=bool(median>=(.005 if a=='R2' else .01) and frac>=.60 and (a=='R2' or rel>=.10))
        primary[a]=dict(median_paired_gain_m=median,median_paired_relative_gain=rel,positive_count=count,positive_fraction=frac,gate=passed);gates[a]=passed
    per_seq={};pooled={}
    for s,rr in groups.items():
        safety[s]={};aa={}
        for a in ARMS:
            aa[a]={}
            for k in ('translation_m','rotation_deg'):
                values=[r['errors'][a][k] for r in rr];aa[a][k]=dict(mean=float(np.mean(values)),median=float(np.median(values)),p90=float(np.percentile(values,90)))
        per_seq[s]=dict(n=len(rr),arms=aa)
        for a in ('KISS','G2','G3'):
            td=float(np.mean([r['errors']['R3']['translation_m']-r['errors'][a]['translation_m'] for r in rr]))
            rd=float(np.median([r['errors']['R3']['rotation_deg']-r['errors'][a]['rotation_deg'] for r in rr]))
            safety[s][a]=dict(mean_translation_regression_m=td,median_paired_rotation_regression_deg=rd,gate=bool(td<=.01 and rd<=.05))
    for a in ARMS:
        pooled[a]={}
        for k in ('translation_m','rotation_deg'):
            v=[r['errors'][a][k] for r in rows];pooled[a][k]=dict(mean=float(np.mean(v)),median=float(np.median(v)),p90=float(np.percentile(v,90)))
    macro={a:{k:float(np.mean([per_seq[s]['arms'][a][k]['mean'] for s in c.SEQS])) for k in ('translation_m','rotation_deg')} for a in ARMS}
    gates['coverage']=True;gates['sequence_safety']=all(safety[s][a]['gate'] for s in c.SEQS for a in ('KISS','G2','G3'))
    return dict(primary=primary,gates=gates,sequence_safety=safety,per_sequence=per_seq,pooled=pooled,equal_sequence_mean=macro,
        decision='MATERIAL_CAUSAL_LOCAL_MOTION_SIGNAL' if all(gates.values()) else 'NO_CAUSAL_LOCAL_MOTION_SIGNAL')
def compare(a,b,tol=1e-7):
    if isinstance(a,dict):
        assert set(a)==set(b)
        return max([compare(a[k],b[k],tol) for k in a] or [0.])
    if isinstance(a,(str,bool)):assert a==b;return 0.
    delta=abs(a-b);assert delta<=tol,(a,b,delta);return delta
def census(f):
    expected=[];ex=[]
    for s,n in c.SEQS.items():
        m=c.read(c.source(s)/'source_frames.json');ts=np.loadtxt(c.DATA/'sequences'/s/'times.txt')
        assert m['source_frame_ids']==list(range(n)) and len(ts)==n and np.array_equal(ts,np.array(m['timestamps'])) and np.all(np.diff(ts)>0)
        for t in range(0,n,200):
            if t==0:ex.append(dict(seq=s,t=0,reason='two past scans unavailable'));continue
            ids=[t-1,t,t-2];paths=[str(c.DATA/'sequences'/s/'velodyne'/f'{i:06d}.bin') for i in ids]
            assert paths==[m['scan_files'][i] for i in ids]
            seed=int.from_bytes(hashlib.sha256(f'LMF1|{s}|{t}'.encode()).digest()[:4],'big')
            expected.append(dict(seq=s,t=t,ids=ids,paths=paths,times=ts[ids].tolist(),seed=seed));assert causal(ids,ts[ids],t)
    assert f['census']['rows']==expected and f['census']['exclusions']==ex
    return expected
def bank():
    import torch
    from dataset_process.extract_sample_features import FeatureExtractor
    t=time.monotonic();f=c.check_freeze(B);seal=c.check_seal(B);saved=c.read(B/'bank.json');expected=census(f)
    assert not saved['gt_files_read'] and len(saved['rows'])==58
    od={s:load_poses(c.source(s)/'odom_poses.txt',n) for s,n in c.SEQS.items()}
    model=FeatureExtractor(model_config=dict(num_points_per_patch=512,is_aligned_to_global_z=True,des_r=5.),des_r=5.,
        is_aligned_to_global_z=True,checkpoint_path=None,device='cuda').model
    weights=torch.load(c.MAIN/'weights/mini_spinnet_t.pth',map_location='cpu',weights_only=True)
    desc={k[5:]:v for k,v in weights.items() if k.startswith('Desc.')};assert len(desc)==58
    model.load_state_dict(desc,strict=True);model.eval();torch.cuda.reset_peak_memory_stats();maxdelta=0.;replays=0
    for ix,(row,r) in enumerate(zip(saved['rows'],expected)):
        assert {k:row[k] for k in r}==r
        with np.load(B/'bank'/f"{r['seq']}_{r['t']:06d}.npz",allow_pickle=False) as z:
            pp=np.split(z['points'],3);assert z['points'].shape==(3000,3) and z['features'].shape==(3000,32)
            assert all(np.isfinite(z[k]).all() for k in z.files)
            for k,path in enumerate(r['paths']):
                p=reconstruct(path);assert np.array_equal(p,pp[k])
                x=torch.tensor(p,device='cuda').unsqueeze(0)
                with c.rng(r['seed']),torch.no_grad():feat=model(pts=x,kpts=x.clone(),des_r=5.,is_aligned_to_global_z=True)['desc'].squeeze(0).cpu().numpy()
                assert np.any(feat) and np.array_equal(feat,z['features'][1000*k:1000*(k+1)])
            with c.rng(r['seed']):noise=torch.randn((3000,3),device='cuda').cpu().numpy()
            assert np.array_equal(noise,z['noise'])
            for arm,num in [('R3_',3),('R2_',2)]:
                cond,scale,centers,counts=normalize(pp[:num]);assert np.array_equal(cond,z[arm+'cond']) and np.array_equal(counts,z[arm+'counts'])
                assert abs(scale-float(z[arm+'scale']))<1e-12 and abs(centers-z[arm+'centers']).max()<1e-12
                assert z[arm+'end_point_trajectory'].shape==z[arm+'trajectory'].shape==(5,num*1000,3)
                parts=decode(z,arm);rel=np.linalg.solve(parts[0],parts[1]);d=max(float(abs(parts-z[arm+'parts']).max()),float(abs(rel-z[arm+'pose']).max()))
                maxdelta=max(maxdelta,d);assert d<1e-8
            two,tr2=icp(pp[0],pp[1]);support,trs=icp(pp[0],pp[2]);localmap=np.concatenate([pp[0],pp[2]@support[:3,:3].T+support[:3,3]])
            three,tr3=icp(localmap,pp[1],two)
            for a,T,tr in [('G2',two,tr2),('G3',three,tr3),('support',support,trs)]:
                d=float(abs(T-z[a+'_pose']).max());maxdelta=max(maxdelta,d);assert d<1e-8
                assert np.asarray(tr).shape==np.asarray(row['icp_trace'][a]).shape and abs(np.asarray(tr)-np.asarray(row['icp_trace'][a])).max()<1e-8
            native=np.linalg.solve(od[r['seq']][r['t']-1],od[r['seq']][r['t']]);d=float(abs(native-z['KISS_pose']).max());maxdelta=max(maxdelta,d);assert d<1e-8
            for a in ARMS:
                R=z[a+'_pose'][:3,:3];tol=1e-5 if a=='KISS' else 1e-8
                assert abs(R.T@R-np.eye(3)).max()<tol and abs(np.linalg.det(R)-1)<tol
            if r['t']==200:
                with np.load(c.PREFLIGHT/'attempt-02/bank'/f"local_{r['seq']}.npz",allow_pickle=False) as old:
                    d=max(float(np.max(abs(z[k]-old[k]))) for k in old.files)
                assert d==row['engineering_replay_max_delta'] and d<=1e-5;replays+=1
        if ix%10==9:print('independent GT-free windows',ix+1,'of58',flush=True)
    assert replays==6;c.check_freeze(B);c.check_seal(B);wall=time.monotonic()-t
    rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/2**20;gpu=torch.cuda.max_memory_allocated()/2**30
    assert saved['wall_s']+wall<1800 and max(saved['peak_rss_gib'],rss)<4 and max(saved['peak_allocated_gib'],gpu)<12
    c.save(B/'bank_validation.json',dict(utc=c.now(),passed=True,windows=58,raw_scans=174,points=174000,feature_values=5568000,
        raw_feature_noise_max_delta=0.,max_independent_pose_control_delta=maxdelta,engineering_replays=6,gt_files_read=False,
        wall_s=wall,peak_rss_gib=rss,peak_allocated_gib=gpu))
    c.save(B/'bank_validation_seal.json',dict(utc=c.now(),validation_sha256=c.sha(B/'bank_validation.json'),bank_seal_sha256=c.sha(B/'bank_seal.json')))
    c.status(B,'BANK_VALIDATED');print('complete GT-free bank independently validated',maxdelta,flush=True)
def final():
    t=time.monotonic();f=c.check_freeze(B);seal=c.check_seal(B);results=c.read(B/'results.json');vs=c.read(B/'bank_validation_seal.json')
    assert c.read(B/'bank_validation.json')['passed'] and c.sha(B/'bank_validation.json')==vs['validation_sha256']
    assert results['bank_seal_sha256']==c.sha(B/'bank_seal.json') and results['bank_validation_seal_sha256']==c.sha(B/'bank_validation_seal.json')
    assert f['utc']<c.read(B/'bank.json')['started_utc']<seal['utc']<vs['utc']<results['gt_read_started_utc']
    expected=census(f);gt={};maximum=0.;rows=[]
    for s,n in c.SEQS.items():
        cam=load_poses(c.DATA/'poses'/f'{s}.txt',n);tr=np.eye(4)
        lines=(c.DATA/'sequences'/s/'calib.txt').read_text().splitlines();line=next(x for x in lines if x.startswith('Tr:'))
        tr[:3]=np.array([float(x) for x in line.split(':',1)[1].split()]).reshape(3,4);gt[s]=np.linalg.solve(tr,cam@tr)
    for r,observed in zip(expected,results['rows']):
        assert observed['seq']==r['seq'] and observed['t']==r['t'];truth=np.linalg.solve(gt[r['seq']][r['t']-1],gt[r['seq']][r['t']])
        assert abs(truth-np.array(observed['T_GT'])).max()<1e-8
        with np.load(B/'bank'/f"{r['seq']}_{r['t']:06d}.npz",allow_pickle=False) as z:ee={a:error(truth,z[a+'_pose']) for a in ARMS}
        maximum=max(maximum,compare(ee,observed['errors']));rows.append(dict(seq=r['seq'],t=r['t'],errors=ee))
    assert len(results['rows'])==len(rows)==58
    summary=aggregate(rows);maximum=max(maximum,compare(summary,results['summary']))
    c.check_freeze(B);c.check_seal(B);wall=time.monotonic()-t
    stages=[c.read(B/p) for p in ['bank.json','bank_validation.json','results.json']];total=sum(x['wall_s'] for x in stages)+wall
    rss=max([resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/2**20]+[x['peak_rss_gib'] for x in stages]);size=sum(p.stat().st_size for p in B.rglob('*') if p.is_file())
    assert total<1800 and rss<4 and size<250000000
    c.save(B/'validation.json',dict(utc=c.now(),passed=True,decision=summary['decision'],windows=58,max_error_aggregate_delta=maximum,
        bank_validation_sha256=c.sha(B/'bank_validation.json'),results_sha256=c.sha(B/'results.json'),wall_s=wall,total_successful_wall_s=total,
        peak_rss_gib=rss,artifact_bytes_before_report=size,checks=['frozen identities/census/complete bank/pre-GT validation seals',
        '174 independent raw/feature/noise arrays and all Horn/control/KISS poses','independent calibrated GT direction and polar/atan2 errors',
        'every row/aggregate/sign/material/context/sequence safety decision','stage ordering/resources/final identity']))
    c.status(B,'VALIDATED',decision=summary['decision']);print('LMF1 final independent validation passed',summary['decision'],maximum,flush=True)
if __name__=='__main__':
    try:{'bank':bank,'final':final}[sys.argv[1]]()
    except Exception as ex:c.status(B,'STOPPED',error=repr(ex));raise
