"""RVC0 fixed stored-hypothesis ranking, new measured radial-order evidence."""
import functools,hashlib,json,resource,subprocess,sys,time
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation
ROOT=Path(__file__).resolve().parents[2];DATE=ROOT/'docs/maintenance/2026-10-16';BASE=DATE/'ray-consistency-ranking-01'
F2=ROOT/'docs/maintenance/2026-09-27/f2-structured-dev-01';G1=ROOT/'docs/maintenance/2026-09-28/fullscan-global-baseline-01'
RAW=ROOT.parent/'Datasets/data_odometry_velodyne/dataset/sequences';SLAM=ROOT.parent/'RAP-SLAM'
GT={'00':ROOT/'docs/maintenance/2026-09-14/hl-v2/data-expansion-01/00/evaluator_gt.npy','08':ROOT/'docs/maintenance/2026-09-14/support-control-01/data/08/evaluator_gt.npy'}
ANGLE=np.deg2rad(.15);CHORD=2*np.sin(ANGLE/2);K={'00':29,'08':32};POLICIES=('V','R','O','D','F')
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    d=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):d.update(b)
    return d.hexdigest()
def artifacts():return sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file())
def save(name,obj):
    out=(json.dumps(obj,indent=2,allow_nan=False)+'\n').encode();assert artifacts()+len(out)<240*2**20
    p=BASE/name;p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as f:f.write(out)
def npz(name,arrays):
    assert artifacts()+sum(a.nbytes for a in arrays.values())+65536<240*2**20
    p=BASE/name;p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as f:np.savez(f,**arrays)
def repositories():
    out={}
    for label,p in (('main',ROOT),('slam',SLAM)):
        def git(*a):return subprocess.check_output(['git','--no-optional-locks','-c',f'safe.directory={p}','-C',str(p),*a],text=True).strip()
        out[label]=dict(head=git('rev-parse','HEAD'),branch=git('branch','--show-current'),tracked_status=git('status','--short','--untracked-files=no').splitlines())
    return out
def proper(t):
    assert t.shape==(4,4) and np.isfinite(t).all() and np.max(abs(t[3]-[0,0,0,1]))<1e-8
    assert np.max(abs(t[:3,:3].T@t[:3,:3]-np.eye(3)))<1e-4 and abs(np.linalg.det(t[:3,:3])-1)<1e-4
    return t
def raw(s,i):return RAW/s/'velodyne'/f'{i:06d}.bin'
def row_seed(s,i):return int.from_bytes(hashlib.sha256(f'RVC0|{s}|{i}'.encode()).digest()[:8],'big')
def tie(s,pair):return hashlib.sha256(f'RVC0|rank|{s}|{pair}'.encode()).hexdigest()
def candidates():
    g=read(G1/'bank.json');out=[]
    assert sha(G1/'bank.json')==read(G1/'bank_seal.json')['sha256'] and len(g)==200
    for s in ('00','08'):
        rr=read(F2/s/'records.json');pairs=list(dict.fromkeys(r['pair'] for r in rr if r['arm']=='N'));assert len(pairs)==100
        for pair in pairs:
            aa=[r for r in rr if r['pair']==pair and r['arm']=='A' and r['valid']]
            assert [r['generation'] for r in aa]==[0,1,2,3]
            chosen=min(aa,key=lambda r:r['rigidity_rmse_m']);gg=next(r for r in g if r['sequence']==s and r['pair']==pair)
            assert gg['status']=='valid';_,i,j=pair.split('_');i=int(i);j=int(j)
            for t in (chosen['T'],gg['T']):proper(np.asarray(t))
            out.append(dict(sequence=s,pair=pair,i=i,j=j,A_generation=chosen['generation'],A=chosen['T'],G=gg['T'],target_points=gg['target_points'],source_points=gg['source_points']))
    return out
def freeze():
    rows=candidates();old=read(G1/'freeze.json')['files'];paths=[]
    for s in ('00','08'):
        paths.extend([F2/s/'records.json',F2/s/'evaluator_only_decisions.json',GT[s]])
    paths.extend(sorted({raw(r['sequence'],r[k]) for r in rows for k in ('i','j')}))
    for p in paths:assert str(p) in old and sha(p)==old[str(p)],str(p)
    paths += [BASE/'OWNER_SCOPE.md',BASE/'PROTOCOL.md',DATE/'strategy-revision-01/STRATEGY_CN.md',DATE/'strategy-revision-01/PRIMARY_SOURCES.md',
      Path(__file__),Path(__file__).with_name('run_ray_consistency_ranking.py'),Path(__file__).with_name('validate_ray_consistency_ranking.py'),Path(__file__).with_name('invoke_mgr_supervised_wsl.ps1'),
      G1/'freeze.json',G1/'bank.json',G1/'bank_seal.json',F2/'REPORT.md',F2/'freeze.json',F2/'artifact_hashes.json',
      ROOT/'scripts/maintenance/fullscan_global_baseline.py',SLAM/'rap_slam/real_dataset.py',SLAM/'rap_slam/trajectory_protocol.py',SLAM/'rap_slam/measurement.py',
      ROOT/'docs/maintenance/2026-09-15/rejection-diagnostic-01/REPORT.md',G1/'REPORT.md',ROOT/'docs/maintenance/2026-10-15/nonlocal-joint-comparison-01/REPORT.md',
      ROOT/'docs/maintenance/2026-10-15/continuation-handoff-08/DELIVERY_SEAL.json']
    markers=read(ROOT/'docs/maintenance/2026-10-15/continuation-handoff-06/IDENTITY_CHECKS.json')['retained_markers'];paths += list(map(Path,markers))
    files={str(p):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(set(paths))}
    for p in paths:
        if p.suffix in ('.py','.ps1'):
            q=BASE/'source_snapshot'/p.relative_to(ROOT.parent);q.parent.mkdir(parents=True,exist_ok=True)
            if not q.exists():
                with q.open('xb') as f:f.write(p.read_bytes())
    save('candidates.json',rows);repos=repositories()
    assert repos==read(ROOT/'docs/maintenance/2026-10-15/nonlocal-joint-comparison-01/freeze.json')['repositories']
    save('freeze.json',dict(files=files,candidates_sha256=sha(BASE/'candidates.json'),repositories=repos,retained_markers=markers,raw_scans=len({str(raw(r['sequence'],r[k])) for r in rows for k in ('i','j')}),
      NumPy=np.__version__,cap_seconds=1200,cap_RSS_bytes=2*2**30,cap_artifacts_bytes=256*2**20))
    save('INCOMPLETE',dict(pending='synthetic controls, all radial scores and fixed selections, postseal metrics and independent verification'))
    print('RVC0 frozen',len(files),'identities,200pairs/400poses',flush=True)
def verify():
    f=read(BASE/'freeze.json')
    for name,r in f['files'].items():assert Path(name).stat().st_size==r['bytes'] and sha(name)==r['sha256'],name
    assert sha(BASE/'candidates.json')==f['candidates_sha256'] and repositories()==f['repositories']

@functools.lru_cache(maxsize=8)
def scan(s,i):
    sys.path.insert(0,str(SLAM));from rap_slam.real_dataset import kitti_vertical_correction
    p=np.fromfile(raw(s,i),dtype=np.float32).reshape(-1,4)[:,:3];assert np.isfinite(p).all()
    p=p[np.linalg.norm(p,axis=1)>=1.5];p=kitti_vertical_correction(p).astype(np.float32).astype(float)
    assert len(p)>=2000 and np.isfinite(p).all();ranges=np.linalg.norm(p,axis=1);unit=p/ranges[:,None]
    rows=np.sort(np.random.default_rng(row_seed(s,i)).choice(len(p),2000,replace=False)).astype(np.int32)
    return dict(points=p,ranges=ranges,unit=unit,angular=cKDTree(unit),xyz=cKDTree(p),rows=rows)

def direction(target,query,nn=True):
    radius=np.linalg.norm(query,axis=1);valid=radius>1e-12;unit=np.zeros_like(query);unit[valid]=query[valid]/radius[valid,None]
    cones=target['angular'].query_ball_point(unit,CHORD,return_sorted=True)
    for i in np.flatnonzero(~valid):cones[i]=[]
    offsets=np.r_[0,np.cumsum([len(c) for c in cones])].astype(np.int32)
    ids=np.concatenate([np.asarray(c,dtype=np.int32) for c in cones]);classes=np.full(len(query),4,dtype=np.int8)
    for k,cone in enumerate(cones):
        if not cone:continue
        r=target['ranges'][cone];v=radius[k]
        if np.any(abs(r-v)<=1.):classes[k]=0
        elif np.min(r)>v+1.:classes[k]=1
        elif np.max(r)<v-1.:classes[k]=2
        else:classes[k]=3
    dist=target['xyz'].query(query)[0] if nn else np.zeros(len(query))
    assert np.isfinite(dist).all()
    summary=dict(agreement=int(np.count_nonzero(classes==0)),front=int(np.count_nonzero(classes==1)),occluded=int(np.count_nonzero(classes==2)),mixed=int(np.count_nonzero(classes==3)),unknown=int(np.count_nonzero(classes==4)),queries=len(query),NN_1m=int(np.count_nonzero(dist<=1)),NN_trim_mean=float(np.sort(dist)[:max(1,len(query)//10)].mean()),NN_full_mean=float(dist.mean()))
    return summary,dict(indptr=offsets,cone_rows=ids,classes=classes,NN=dist)
def scores(dirs):
    eligible=all(d['agreement']>=100 for d in dirs)
    return dict(V=dict(eligible=eligible,score=min(d['agreement']/max(1,d['agreement']+d['front']) for d in dirs)),
      R=dict(eligible=eligible,score=min(d['agreement']/d['queries'] for d in dirs)),
      O=dict(eligible=True,score=min(d['NN_1m']/d['queries'] for d in dirs)),
      D=dict(eligible=True,score=-max(d['NN_trim_mean'] for d in dirs)),F=dict(eligible=True,score=-max(d['NN_full_mean'] for d in dirs)))
def synthetic():
    verify();theta=np.linspace(-.2,.2,256);p=np.c_[10*np.cos(theta),10*np.sin(theta),np.zeros(256)]
    def target(p):r=np.linalg.norm(p,axis=1);return dict(ranges=r,angular=cKDTree(p/r[:,None]),xyz=cKDTree(p))
    t=target(p);cases={};checks={}
    for name,q,expected in [('same',p,0),('front',p*.5,1),('behind',p*1.5,2),('unknown',p@Rotation.from_rotvec([0,0,np.pi/2]).as_matrix().T,4)]:
        d,e=direction(t,q);assert np.all(e['classes']==expected),(name,np.unique(e['classes'],return_counts=True));cases[name]=dict(summary=d,classes=e['classes'].tolist())
    boundary=target(np.tile([10.,0,0],(256,1)));d,e=direction(boundary,np.tile([9.,0,0],(256,1)));assert np.all(e['classes']==0);cases['boundary']=dict(summary=d,classes=e['classes'].tolist())
    mixed=target(np.r_[p,p*2]);d,e=direction(mixed,p*1.5);assert np.all(e['classes']==3);cases['mixed']=dict(summary=d,classes=e['classes'].tolist())
    r=Rotation.from_rotvec([.19,-.23,.13]).as_matrix();d1,e1=direction(t,p);d2,e2=direction(target(p@r.T),p@r.T)
    assert np.array_equal(e1['classes'],e2['classes']);checks['common_basis_rotation']=True
    z=np.eye(4);z[:3,:3]=r;z[:3,3]=[1.,-.5,.2];q=(p-z[:3,3])@r
    back=q@z[:3,:3].T+z[:3,3];assert np.max(abs(back-p))<1e-12
    checks['direction_inverse_max_error']=float(np.max(abs(back-p)));save('synthetic.json',dict(passed=True,cases=cases,checks=checks))
    print('RVC0 synthetic range/direction controls pass',flush=True)
def bank():
    verify();assert read(BASE/'synthetic.json')['passed'];rows=read(BASE/'candidates.json');outputs=[];start=time.monotonic()
    for ix,row in enumerate(rows):
        s,i,j=row['sequence'],row['i'],row['j'];a,b=scan(s,i),scan(s,j);assert len(a['points'])==row['target_points'] and len(b['points'])==row['source_points']
        arrays={};entry=dict(sequence=s,pair=row['pair'],i=i,j=j,A_generation=row['A_generation'],families={})
        for family in ('A','G'):
            t=np.asarray(row[family]);dirs=[]
            for k,(target,source,transform) in enumerate(((a,b,t),(b,a,np.linalg.inv(t)))):
                q=source['points'][source['rows']]@transform[:3,:3].T+transform[:3,3];d,e=direction(target,q);dirs.append(d)
                for key,val in e.items():arrays[f'{family}_{k}_{key}']=val
                arrays[f'{family}_{k}_query_rows']=source['rows']
            entry['families'][family]=dict(directions=dirs,scores=scores(dirs))
        name=f'evidence/{s}_{i}_{j}.npz';npz(name,arrays);entry.update(evidence=name,evidence_sha256=sha(BASE/name));outputs.append(entry)
        assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024<=2*2**30
        if (ix+1)%25==0:print('RVC0 evidence',ix+1,'/200',round(time.monotonic()-start,2),'s',flush=True)
    save('scores.json',outputs);selections={}
    for s in ('00','08'):
        selections[s]={}
        for family in ('A','G'):
            selections[s][family]={}
            for policy in POLICIES:
                ordered=sorted([r for r in outputs if r['sequence']==s and r['families'][family]['scores'][policy]['eligible']],key=lambda r:(-r['families'][family]['scores'][policy]['score'],tie(s,r['pair'])))
                selections[s][family][policy]=dict(eligible=len(ordered),budget=K[s],ranking=[r['pair'] for r in ordered],selected=[r['pair'] for r in ordered[:K[s]]])
    save('selections.json',selections);save('SCORE_SEAL.json',dict(score_sha256=sha(BASE/'scores.json'),selection_sha256=sha(BASE/'selections.json'),poses=400,pairs=200,evidence_files=200,references_numerically_read=False))
    print('RVC0 all scores/selections sealed before labels',flush=True)

def evaluate():
    verify();seal=read(BASE/'SCORE_SEAL.json');assert sha(BASE/'scores.json')==seal['score_sha256'] and sha(BASE/'selections.json')==seal['selection_sha256']
    sys.path.insert(0,str(SLAM));from rap_slam.measurement import transform_label
    selection=read(BASE/'selections.json');stats={};metricrows=[];byseq={};sources=read(BASE/'candidates.json')
    for s in ('00','08'):
        gt=np.load(GT[s],allow_pickle=False);old=read(F2/s/'evaluator_only_decisions.json');rows=[r for r in sources if r['sequence']==s];lookup={};baseline=dict(correct=0,incorrect=0,accepted=0,confusers=0)
        for row,original in zip(rows,old):
            assert row['i']==original['source_i'] and row['j']==original['source_j'] and row['A_generation']==original['methods']['A']['generation']
            truth=np.linalg.inv(gt[row['i']])@gt[row['j']];lookup[row['pair']]={}
            for family in ('A','G'):
                t=np.asarray(row[family]);label=transform_label(t,truth);rte=label['gt_translation_error_m'];rre=label['gt_rotation_error_deg'];strict=rte<=1 and rre<=5
                m=dict(sequence=s,pair=row['pair'],family=family,stratum=original['stratum'],RTE_m=rte,RRE_deg=rre,strict=bool(strict));lookup[row['pair']][family]=m;metricrows.append(m)
                if family=='A':
                    previous=original['methods']['A'];assert strict==previous['strict'] and abs(rte-previous['RTE_m'])<1e-4 and abs(rre-previous['RRE_deg'])<1e-3
            previous=original['methods']['A']
            if previous['accepted']:
                baseline['accepted']+=1;baseline['correct']+=previous['strict'];baseline['incorrect']+=not previous['strict'];baseline['confusers']+=original['stratum']=='confuser'
        expected=(24,22,2) if s=='00' else (27,17,10);assert (baseline['accepted'],baseline['correct'],baseline['incorrect'])==expected
        assert {k:sum(r['stratum']==k for r in old) for k in {r['stratum'] for r in old}}==dict(ordinary=25,low_overlap=25,ambiguous_positive=25,confuser=25)
        stats[s]=dict(baseline=baseline,arms={})
        for family in ('A','G'):
            stats[s]['arms'][family]={}
            for policy,chosen in selection[s][family].items():
                admitted=[lookup[p][family] for p in chosen['selected']]
                stats[s]['arms'][family][policy]=dict(accepted=len(admitted),correct=sum(r['strict'] for r in admitted),incorrect=sum(not r['strict'] for r in admitted),confusers=sum(r['stratum']=='confuser' for r in admitted),eligible=chosen['eligible'],selection=chosen['selected'])
        v=stats[s]['arms']['A']['V'];others=[stats[s]['arms']['A'][p]['correct'] for p in ('R','O','D','F')];g=stats[s]['arms']['G']['V']
        byseq[s]=dict(coverage_filled=v['accepted']==K[s],correct_gain=v['correct']>=baseline['correct']+5,incorrect_nonincrease=v['incorrect']<=baseline['incorrect'],zero_confusers=v['confusers']==0,radial_increment=v['correct']>=max(others)+3,RAP_increment=v['correct']>=g['correct']+5)
    passed=all(all(v.values()) for v in byseq.values());save('results.json',dict(scope='exposed batch ranking evidence only',sequences=stats,gates=byseq,admitted=passed,metrics=metricrows,score_seal_sha256=sha(BASE/'SCORE_SEAL.json'),online_or_system_gain=False))
    print(json.dumps(dict(sequences={s:dict(baseline=v['baseline'],arms={f:{p:{k:r[k] for k in ('accepted','correct','incorrect','confusers')} for p,r in arms.items()} for f,arms in v['arms'].items()}) for s,v in stats.items()},gates=byseq,admitted=passed)),flush=True)

if __name__=='__main__':{'freeze':freeze,'synthetic':synthetic,'bank':bank,'evaluate':evaluate}[sys.argv[1]]()
