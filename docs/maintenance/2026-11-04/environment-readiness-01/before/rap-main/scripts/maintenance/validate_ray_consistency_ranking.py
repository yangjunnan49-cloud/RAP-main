"""Independent RVC0 evidence/class/rank/metric validator; no primary import."""
import functools,hashlib,json,sys
from pathlib import Path
import numpy as np
from scipy.spatial.distance import cdist
from scipy.spatial.transform import Rotation
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'docs/maintenance/2026-10-16/ray-consistency-ranking-01';F2=ROOT/'docs/maintenance/2026-09-27/f2-structured-dev-01';G1=ROOT/'docs/maintenance/2026-09-28/fullscan-global-baseline-01'
sys.path.insert(0,str(ROOT.parent/'RAP-SLAM'));from rap_slam.real_dataset import kitti_vertical_correction
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    d=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):d.update(b)
    return d.hexdigest()
freeze=read(BASE/'freeze.json');seal=read(BASE/'SCORE_SEAL.json')
for name,row in freeze['files'].items():assert sha(name)==row['sha256'] and Path(name).stat().st_size==row['bytes']
assert sha(BASE/'candidates.json')==freeze['candidates_sha256'] and sha(BASE/'scores.json')==seal['score_sha256'] and sha(BASE/'selections.json')==seal['selection_sha256']
assert read(BASE/'supervision/bank/exit.json')['utc_end']<read(BASE/'supervision/evaluate/launch.json')['utc_start']
@functools.lru_cache(maxsize=8)
def cloud(s,i):
    path=ROOT.parent/f'Datasets/data_odometry_velodyne/dataset/sequences/{s}/velodyne/{i:06d}.bin'
    xyz=np.fromfile(path,dtype='<f4').reshape(-1,4)[:,:3];xyz=xyz[np.linalg.norm(xyz,axis=1)>=1.5]
    # Deliberately shared frozen preprocessing, independent scoring/lookup below.
    p=kitti_vertical_correction(xyz).astype(float);r=np.sqrt(np.einsum('ij,ij->i',p,p));u=p/r[:,None]
    seed=int.from_bytes(hashlib.sha256(f'RVC0|{s}|{i}'.encode()).digest()[:8],'big');rows=np.sort(np.random.default_rng(seed).choice(len(p),2000,replace=False)).astype(np.int32)
    return p,r,u,rows
candidates=read(BASE/'candidates.json');evidence=read(BASE/'scores.json');stored_selection=read(BASE/'selections.json');computed={};count=0;brute=0;cone_members=0;nn_max=0.;score_max=0.;classes_total=0
threshold=(2*np.sin(np.pi*.15/360))**2
for index,(row,entry) in enumerate(zip(candidates,evidence)):
    s=row['sequence'];pair=row['pair'];assert entry['pair']==pair and sha(BASE/entry['evidence'])==entry['evidence_sha256']
    a=cloud(s,row['i']);b=cloud(s,row['j']);assert len(a[0])==row['target_points'] and len(b[0])==row['source_points']
    with np.load(BASE/entry['evidence'],allow_pickle=False) as z:
        for family in ('A','G'):
            t=np.asarray(row[family]);summaries=[]
            for side,(target,source,transform) in enumerate(((a,b,t),(b,a,np.linalg.inv(t)))):
                prefix=f'{family}_{side}_';ptr=z[prefix+'indptr'];ids=z[prefix+'cone_rows'];rows=z[prefix+'query_rows'];nn=z[prefix+'NN'];oldclasses=z[prefix+'classes']
                assert np.array_equal(rows,source[3]) and len(ptr)==2001 and ptr[0]==0 and ptr[-1]==len(ids) and np.all(np.diff(ptr)>=0)
                q=source[0][rows]@transform[:3,:3].T+transform[:3,3];r=np.sqrt(np.einsum('ij,ij->i',q,q));unit=np.zeros_like(q);valid=r>1e-12;unit[valid]=q[valid]/r[valid,None]
                owner=np.repeat(np.arange(2000),np.diff(ptr));delta=target[2][ids]-unit[owner]
                assert np.all(np.einsum('ij,ij->i',delta,delta)<=threshold+1e-12);cone_members+=len(ids)
                classification=np.empty(2000,dtype=np.int8)
                for k in range(2000):
                    neighbours=ids[ptr[k]:ptr[k+1]]
                    if not len(neighbours):classification[k]=4;continue
                    depths=target[1][neighbours];near=(depths>=r[k]-1)&(depths<=r[k]+1)
                    classification[k]=0 if np.any(near) else 1 if np.all(depths>r[k]+1) else 2 if np.all(depths<r[k]-1) else 3
                assert np.array_equal(classification,oldclasses);classes_total+=2000
                # Full angular and Cartesian completeness on fixed first8queries.
                angular=cdist(unit[:8],target[2],metric='sqeuclidean');cart=cdist(q[:8],target[0]);nearest=cart.min(1)
                for k in range(8):
                    expected=np.flatnonzero(angular[k]<=threshold) if valid[k] else np.array([],dtype=int)
                    assert np.array_equal(expected,ids[ptr[k]:ptr[k+1]])
                nn_error=float(np.max(abs(nearest-nn[:8])));assert nn_error<1e-8;nn_max=max(nn_max,nn_error);brute+=8
                summary=dict(agreement=int(np.count_nonzero(classification==0)),front=int(np.count_nonzero(classification==1)),occluded=int(np.count_nonzero(classification==2)),mixed=int(np.count_nonzero(classification==3)),unknown=int(np.count_nonzero(classification==4)),queries=2000,NN_1m=int(np.count_nonzero(nn<=1)),NN_trim_mean=float(np.partition(nn,199)[:200].mean()),NN_full_mean=float(sum(nn)/2000))
                for k,v in summary.items():assert abs(v-entry['families'][family]['directions'][side][k])<1e-8
                summaries.append(summary)
            eligible=min(d['agreement'] for d in summaries)>=100
            scores={'V':(eligible,min(d['agreement']/max(1,d['agreement']+d['front']) for d in summaries)),
              'R':(eligible,min(d['agreement']/2000 for d in summaries)),'O':(True,min(d['NN_1m']/2000 for d in summaries)),
              'D':(True,-max(d['NN_trim_mean'] for d in summaries)),'F':(True,-max(d['NN_full_mean'] for d in summaries))}
            computed[(s,pair,family)]=scores
            for name,(admit,value) in scores.items():
                old=entry['families'][family]['scores'][name];assert old['eligible']==admit;err=abs(value-old['score']);score_max=max(score_max,err);assert err<1e-8
            count+=1
    if (index+1)%25==0:print('RVC0 independent evidence',index+1,'/200',flush=True)
rankings={}
for s,budget in (('00',29),('08',32)):
    rankings[s]={}
    for family in ('A','G'):
        rankings[s][family]={}
        for policy in ('V','R','O','D','F'):
            values=[(pair,sc[policy][1]) for (seq,pair,fam),sc in computed.items() if seq==s and fam==family and sc[policy][0]]
            ordered=sorted(values,key=lambda p:(-p[1],hashlib.sha256(f'RVC0|rank|{s}|{p[0]}'.encode()).hexdigest()))
            names=[p for p,v in ordered];assert names==stored_selection[s][family][policy]['ranking']
            rankings[s][family][policy]=names[:budget];assert names[:budget]==stored_selection[s][family][policy]['selected']
results=read(BASE/'results.json');lookup={};metric_errors=[];global_available={}
gtpaths={'00':ROOT/'docs/maintenance/2026-09-14/hl-v2/data-expansion-01/00/evaluator_gt.npy','08':ROOT/'docs/maintenance/2026-09-14/support-control-01/data/08/evaluator_gt.npy'}
for s in ('00','08'):
    gt=np.load(gtpaths[s],allow_pickle=False);old=read(F2/s/'evaluator_only_decisions.json');rr=read(F2/s/'records.json')
    rows=[r for r in candidates if r['sequence']==s]
    for row,original in zip(rows,old):
        chosen=sorted([r for r in rr if r['arm']=='A' and r['pair']==row['pair'] and r['valid']],key=lambda r:(r['rigidity_rmse_m'],r['generation']))[0]
        assert chosen['generation']==row['A_generation'] and chosen['T']==row['A']
        reference=np.linalg.solve(gt[row['i']],gt[row['j']])
        for family in ('A','G'):
            delta=np.linalg.solve(reference,np.asarray(row[family]));te=float(np.linalg.norm(delta[:3,3]));re=float(np.degrees(Rotation.from_matrix(delta[:3,:3]).magnitude()));correct=te<=1 and re<=5
            metric=next(m for m in results['metrics'] if m['sequence']==s and m['pair']==row['pair'] and m['family']==family)
            errors=(abs(te-metric['RTE_m']),abs(re-metric['RRE_deg']));assert errors[0]<1e-8 and errors[1]<1e-3 and correct==metric['strict'];metric_errors.append(errors)
            lookup[(s,row['pair'],family)]=(correct,original['stratum']=='confuser')
        assert lookup[(s,row['pair'],'A')][0]==original['methods']['A']['strict']
    for family in ('A','G'):
        global_available[s+'_'+family]=sum(lookup[(s,r['pair'],family)][0] for r in rows if next(o for o in old if o['source_i']==r['i'] and o['source_j']==r['j'])['stratum']!='confuser')
    recalculated={}
    for family in ('A','G'):
        recalculated[family]={}
        for policy,names in rankings[s][family].items():
            selected=[lookup[(s,p,family)] for p in names];vals=dict(accepted=len(selected),correct=sum(a for a,b in selected),incorrect=sum(not a for a,b in selected),confusers=sum(b for a,b in selected))
            for k,v in vals.items():assert results['sequences'][s]['arms'][family][policy][k]==v
            recalculated[family][policy]=vals
    base=results['sequences'][s]['baseline'];v=recalculated['A']['V'];other=max(recalculated['A'][p]['correct'] for p in ('R','O','D','F'));g=recalculated['G']['V']
    gates=dict(coverage_filled=v['accepted']==(29 if s=='00' else 32),correct_gain=v['correct']>=base['correct']+5,incorrect_nonincrease=v['incorrect']<=base['incorrect'],zero_confusers=v['confusers']==0,radial_increment=v['correct']>=other+3,RAP_increment=v['correct']>=g['correct']+5)
    assert gates==results['gates'][s]
assert results['admitted']==all(all(g.values()) for g in results['gates'].values())
output=dict(passed=True,poses=count,point_classifications=classes_total,cone_memberships_checked=cone_members,full_lookup_completeness_queries=brute,all_queries_completeness_claim=False,NN_subset_max_error=nn_max,score_max_error=score_max,metric_rows=len(metric_errors),RTE_max_error=max(a for a,b in metric_errors),RRE_max_error_deg=max(b for a,b in metric_errors),stored_selections_and_gates_match=True,complete_source_candidate_availability=global_available,raw_preprocessing_shared_frozen_function=True,model_solver_replays=0)
with (BASE/'validation.json').open('x') as f:json.dump(output,f,indent=2)
print(json.dumps(output),flush=True)
