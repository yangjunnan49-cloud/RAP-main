"""MF0 independent explicit census, row overlap, costs and directional checks."""
import os
for name in ('OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','OMP_NUM_THREADS'):
    os.environ[name]='1'
import argparse
import hashlib
import numpy as np
import membership_formation_diagnosis as run


def compare(a,b,tol=1e-8):
    if isinstance(a,dict):
        assert set(a)==set(b),(set(a),set(b))
        return max([compare(a[k],b[k],tol) for k in a] or [0.])
    if a is None or isinstance(a,(str,bool)):
        assert a==b,(a,b);return 0.
    delta=float(np.max(np.abs(np.asarray(a)-np.asarray(b)))) if np.asarray(a).size else 0.
    assert delta<tol,(a,b,delta)
    return delta


def reconstruct(points,poses,seq,endpoints):
    # Dictionary formation, then explicit centered world-point covariance.
    cells={}
    for i,(p,t) in enumerate(zip(points,poses)):
        world=p@t[:3,:3].T+t[:3,3]
        for row,key in enumerate(np.floor(world/2.).astype(np.int64)):
            cells.setdefault(tuple(key),{}).setdefault(i,[]).append(row)
    keys=sorted(cells);n=len(points);kcount=len(keys)
    raw=np.zeros((kcount,n),np.int64);effective=raw.copy()
    reason=np.ones(kcount,np.int8);bits=np.zeros(kcount,np.uint8)
    eig=np.full((kcount,3),np.nan);offset=np.full(kcount,np.nan)
    candidate_ids=[np.empty(len(p),np.int64) for p in points]
    labels=[np.full(len(p),-1,np.int64) for p in points]
    counts=[];means=[];seconds=[];accepted=[]
    for c,key in enumerate(keys):
        groups=cells[key]
        active={i:np.array(ids,np.int64) for i,ids in groups.items() if len(ids)>=6}
        for i,ids in groups.items():
            raw[c,i]=len(ids);candidate_ids[i][ids]=c
        for i,ids in active.items():effective[c,i]=len(ids)
        if len(active)<3 or effective[c].sum()<40:continue
        worlds=[points[i][ids]@poses[i,:3,:3].T+poses[i,:3,3] for i,ids in active.items()]
        center=np.mean([q.mean(0) for q in worlds],axis=0)
        covariance=np.mean([(q-center).T@(q-center)/len(q) for q in worlds],axis=0)
        values,vectors=np.linalg.eigh(covariance);eig[c]=values
        offset[c]=max(abs(float(vectors[:,0]@(q.mean(0)-center))) for q in worlds)
        tests=(values[0]/max(values.sum(),1e-15)<.025,values[1]>.005,values[0]<=.015,offset[c]<=.20)
        bits[c]=sum(2**i for i,passed in enumerate(tests) if not passed)
        if not all(tests):reason[c]=2;continue
        if not (effective[c,:8].sum()>0 and effective[c,8:].sum()>0):reason[c]=3;continue
        reason[c]=0;patch=len(accepted);accepted.append(c)
        mu=np.zeros((n,3));second=np.zeros((n,3,3))
        for i,ids in active.items():
            q=points[i][ids];mu[i]=q.mean(0);second[i]=q.T@q/len(q);labels[i][ids]=patch
        counts.append(effective[c].copy());means.append(mu);seconds.append(second)
    accepted=np.array(accepted,np.int64)
    patch_keys=np.array(keys,np.int64).reshape(-1,3)[accepted]
    numbers=np.array([int(hashlib.sha256((f'CV1|{seq}|{endpoints[0]}|{endpoints[1]}|2|'+','.join(str(int(x)) for x in key)).encode()).hexdigest()[:8],16) for key in patch_keys],np.uint32)
    expected=dict(candidate_keys=np.array(keys,np.int64).reshape(-1,3),candidate_raw_counts=raw,candidate_effective_counts=effective,
        candidate_reason=reason,candidate_plane_fail_bits=bits,candidate_eigenvalues=eig,candidate_offset_max_m=offset,
        accepted_candidate_ids=accepted,keys=patch_keys,counts=np.array(counts,np.int64).reshape(-1,n),
        means=np.array(means).reshape(-1,n,3),seconds=np.array(seconds).reshape(-1,n,3,3),hash_integers=numbers,holdout=numbers%4==0)
    for i,p in enumerate(points):
        expected[f'candidate_id_{i}']=candidate_ids[i];expected[f'label_{i}']=labels[i]
        why=reason[candidate_ids[i]].copy();why[(why==0)&(labels[i]<0)]=4;expected[f'point_reason_{i}']=why
    return expected


def reference(seq,frames):
    cam=np.repeat(np.eye(4)[None],len(frames),axis=0)
    cam[:,:3]=np.loadtxt(run.DATA/f'poses/{seq}.txt').reshape(-1,3,4)[frames]
    text=(run.DATA/f'sequences/{seq}/calib.txt').read_text()
    row=next(x for x in text.splitlines() if x.startswith('Tr:'))
    tr=np.eye(4);tr[:3]=np.fromstring(row.split(':')[1],sep=' ').reshape(3,4)
    absolute=np.stack([np.linalg.solve(tr,x@tr) for x in cam])
    relative=np.stack([np.linalg.solve(absolute[0],x) for x in absolute])
    for x in relative:
        u,_,vt=np.linalg.svd(x[:3,:3]);x[:3,:3]=u@np.diag([1.,1.,np.linalg.det(u@vt)])@vt
    relative[0]=np.eye(4)
    return relative


def bank():
    run.verify()
    for name,digest in run.read(run.BASE/'bank_seal.json')['files'].items():assert run.sha(run.BASE/'bank'/name)==digest
    summary=run.read(run.BASE/'bank/summary.json')
    numeric=0.;reference_delta=0.;candidate_total=0;row_total=0
    for seq in run.SEQUENCES:
        with np.load(run.BASE/f'bank/{seq}-inputs.npz',allow_pickle=False) as z, np.load(run.CV2/f'bank/{seq}.npz',allow_pickle=False) as old:
            points=[z[f'points_{i}'] for i in range(16)]
            assert all(np.array_equal(z[k],old[k]) for k in ('B','F','T','frames','nodes'))
            for i,p in enumerate(points):
                assert np.array_equal(p,old[f'points_{i}'])
                assert np.array_equal(z[f'row_id_{i}'],np.arange(len(p)))
                row_total+=len(p)
            independent=reference(seq,z['frames']);reference_delta=max(reference_delta,float(np.max(abs(independent-z['G']))))
            formations={}
            for name in ('B','G'):
                expected=reconstruct(points,z[name],seq,summary[seq]['endpoints']);formations[name]=expected
                candidate_total+=len(expected['candidate_keys'])
                with np.load(run.BASE/f'bank/{seq}-{name}.npz',allow_pickle=False) as saved:
                    assert set(saved.files)==set(expected)
                    for k,a in expected.items():
                        b=saved[k];assert a.shape==b.shape,k
                        if k in ('candidate_eigenvalues','candidate_offset_max_m'):
                            assert np.array_equal(np.isnan(a),np.isnan(b));good=np.isfinite(a)
                            if good.any():numeric=max(numeric,float(np.max(abs(a[good]-b[good]))))
                        elif np.issubdtype(a.dtype,np.floating):
                            if a.size:numeric=max(numeric,float(np.max(abs(a-b))))
                        else:assert np.array_equal(a,b),(seq,name,k)
                    reason=expected['candidate_reason']
                    census=dict(candidate_voxels=len(reason),full_eligible_planes=int(np.sum((reason==0)|(reason==3))),accepted_cross_patches=len(expected['keys']),
                        rejected_support=int(np.sum(reason==1)),rejected_plane=int(np.sum(reason==2)),rejected_single_visit=int(np.sum(reason==3)))
                    compare(census,summary[seq]['memberships'][name]['census'])
                    for part,mask in (('train',~expected['holdout']),('holdout',expected['holdout'])):
                        coverage=expected['counts'][mask].sum(0)
                        record=dict(patches=int(mask.sum()),per_scan_points=coverage.tolist(),per_visit_points=[int(coverage[:8].sum()),int(coverage[8:].sum())],
                            per_visit_scans=[int(np.sum(coverage[:8]>0)),int(np.sum(coverage[8:]>0))])
                        compare(record,summary[seq]['memberships'][name][part])
            b,g=formations['B'],formations['G']; nb,ng=len(b['keys']),len(g['keys'])
            flat=[];scan_counts=[];shared=[]
            for i,p in enumerate(points):
                lb,lg=b[f'label_{i}'],g[f'label_{i}'];both=(lb>=0)&(lg>=0);union=(lb>=0)|(lg>=0)
                flat.extend((lb[both]*ng+lg[both]).tolist());shared.append(both)
                assert np.array_equal(both,z[f'intersection_{i}'])
                scan_counts.append(dict(total=len(p),B=int(np.sum(lb>=0)),G=int(np.sum(lg>=0)),intersection=int(both.sum()),
                    B_only=int(np.sum((lb>=0)&(lg<0))),G_only=int(np.sum((lg>=0)&(lb<0))),union=int(union.sum())))
            overlap=np.bincount(np.array(flat,np.int64),minlength=nb*ng).reshape(nb,ng)
            assert np.array_equal(overlap,z['overlap_counts']);edges=overlap>0
            cov=dict(per_scan=scan_counts,intersection_points=sum(x['intersection'] for x in scan_counts),union_points=sum(x['union'] for x in scan_counts),
                jaccard=(sum(x['intersection'] for x in scan_counts)/sum(x['union'] for x in scan_counts) if sum(x['union'] for x in scan_counts) else None),
                B_split_patches=int(np.sum(edges.sum(1)>1)),G_merge_patches=int(np.sum(edges.sum(0)>1)),B_patches_with_no_shared_rows=int(np.sum(edges.sum(1)==0)),
                G_patches_with_no_shared_rows=int(np.sum(edges.sum(0)==0)),same_key_pairs=len({tuple(k) for k in b['keys']}&{tuple(k) for k in g['keys']}))
            compare(cov,summary[seq]['coverage'])
            for name,formation in formations.items():
                count=[];mu=[];second=[];kept=[]
                for k in range(len(formation['keys'])):
                    scans=[p[(formation[f'label_{i}']==k)&shared[i]] for i,p in enumerate(points)]
                    if not sum(map(len,scans)):continue
                    kept.append(k);count.append([len(q) for q in scans])
                    mu.append([q.mean(0) if len(q) else np.zeros(3) for q in scans])
                    second.append([q.T@q/len(q) if len(q) else np.zeros((3,3)) for q in scans])
                assert np.array_equal(z[f'intersection_{name}_original_patch_ids'],kept)
                for field,a in [('counts',np.array(count).reshape(-1,16)),('means',np.array(mu).reshape(-1,16,3)),('seconds',np.array(second).reshape(-1,16,3,3)),('keys',formation['keys'][kept])]:
                    target=z[f'intersection_{name}_{field}'];assert a.shape==target.shape
                    if a.size:numeric=max(numeric,float(np.max(abs(a-target))))
            print('MF0 independent entire census',seq,nb,ng,flush=True)
    assert numeric<1e-8 and reference_delta<1e-10 and row_total==288000
    run.save(run.BASE/'bank_validation.json',dict(passed=True,all_candidate_census_reconstructed=True,candidate_records=candidate_total,
        retained_points=row_total,all_row_membership_rejection_checked=True,independent_moment_eigenvalue_offset_max_delta=numeric,
        independent_reference_pose_max_delta=reference_delta,complete_overlap_and_intersection_checked=True,
        raw_preprocessing_replayed=False,optimizer_calls=0,physical_surface_identity_verified=False))


def direct(points,labels,poses,kcount,shared=None):
    values=[];normals=[];centers=[];world_groups=[]
    for k in range(kcount):
        groups=[];indices=[]
        for i,p in enumerate(points):
            mask=labels[i]==k
            if shared is not None:mask&=shared[i]
            q=p[mask]
            if len(q):groups.append(q@poses[i,:3,:3].T+poses[i,:3,3]);indices.append(i)
        if not groups:continue
        center=np.mean([q.mean(0) for q in groups],axis=0)
        covariance=np.mean([(q-center).T@(q-center)/len(q) for q in groups],axis=0)
        eig,vector=np.linalg.eigh(covariance)
        values.append(max(float(eig[0]),0.));normals.append(vector[:,0]);centers.append(center);world_groups.append((indices,groups))
    return np.array(values),normals,centers,world_groups


def record_cost(values,mask):
    if not np.any(mask):return None
    v=values[mask]
    return dict(cost=float(50*v.mean()),rms_m=float(np.sqrt(v.mean())),per_patch_variance_m2=v.tolist(),patches=len(v))


def evaluate():
    run.verify(); result=run.read(run.BASE/'results.json');summary=run.read(run.BASE/'bank/summary.json')
    assert result['bank_seal_sha256']==run.sha(run.BASE/'bank_seal.json')
    assert run.sha(run.BASE/'results.json')==run.read(run.BASE/'result_seal.json')['files']['results.json']
    cost_delta=gradient_delta=fd_delta=0.;cost_records=0
    for seq in run.SEQUENCES:
        with np.load(run.BASE/f'bank/{seq}-inputs.npz',allow_pickle=False) as z:
            points=[z[f'points_{i}'] for i in range(16)];shared=[z[f'intersection_{i}'] for i in range(16)]
            for name in ('B','G'):
                with np.load(run.BASE/f'bank/{seq}-{name}.npz',allow_pickle=False) as m:
                    labels=[m[f'label_{i}'] for i in range(16)];kcount=len(m['keys']);saved=result['rows'][seq][name]
                    for pose in ('B','G','F','T'):
                        values=direct(points,labels,z[pose],kcount)[0]
                        for part,mask in [('train',~m['holdout']),('holdout',m['holdout']),('all',np.ones(kcount,bool))]:
                            cost_delta=max(cost_delta,compare(record_cost(values,mask),saved['costs'][part][pose]));cost_records+=1
                    for pose in ('B','G'):
                        values=direct(points,labels,z[pose],kcount,shared)[0]
                        cost_delta=max(cost_delta,compare(record_cost(values,np.ones(len(values),bool)),saved['intersection_costs'][pose]));cost_records+=1
                    values,normals,centers,groups=direct(points,labels,z['B'],kcount)
                    train=~m['holdout'];gradient_world=np.zeros(3)
                    if train.any():
                        for k,((ids,world),normal,center) in enumerate(zip(groups,normals,centers)):
                            if not train[k]:continue
                            for i,q in zip(ids,world):
                                if i>=8:gradient_world+=normal*float(np.mean((q-center)@normal))/(train.sum()*len(ids)*.10**2)
                        gradient=z['B'][-1,:3,:3].T@gradient_world
                        gradient_delta=max(gradient_delta,float(np.max(abs(gradient-saved['B_translation_gradient_body']))))
                        d=z['G'][-1,:3,3]-z['B'][-1,:3,3];length=np.linalg.norm(d)
                        if length>1e-12:
                            direction=d/length;analytic=float(gradient_world@direction)
                            plus,minus=z['B'].copy(),z['B'].copy();plus[8:,:3,3]+=direction*1e-5;minus[8:,:3,3]-=direction*1e-5
                            cp=record_cost(direct(points,labels,plus,kcount)[0],train)['cost']
                            cm=record_cost(direct(points,labels,minus,kcount)[0],train)['cost']
                            fd_delta=max(fd_delta,abs((cp-cm)/2e-5-analytic))
                            assert abs(analytic-saved['B_cost_slope_towards_G_per_m'])<1e-8
                    delta=saved['costs']['train']['G']['cost']-saved['costs']['train']['B']['cost'] if train.any() else None
                    preference='MISSING' if delta is None else ('B' if delta>1e-10 else 'G' if delta< -1e-10 else 'TIE')
                    assert preference==saved['train_preference']
                    ti,hi=summary[seq]['memberships'][name]['train'],summary[seq]['memberships'][name]['holdout']
                    supported=ti['patches']>=10 and min(ti['per_visit_scans'])>=3 and min(ti['per_visit_points'])>=100 and hi['patches']>=5
                    assert bool(supported)==saved['supported']
                if name=='B':
                    old=run.read(run.CV2/'objective-diagnosis-01/results.json')['rows'][seq]
                    for part in ('train','holdout'):
                        assert abs(saved['costs'][part]['B']['rms_m']-old['Oshape__native_placement'][part+'_rms_m'])<1e-8
                        assert abs(saved['costs'][part]['G']['rms_m']-old['reference_shape__full_reference_placement'][part+'_rms_m'])<1e-8
            a,b=result['rows'][seq]['B'],result['rows'][seq]['G']
            expected='INSUFFICIENT_SUPPORT' if not(a['supported'] and b['supported']) else 'OPPOSING_FORMATION_PREFERENCES' if a['train_preference']=='B' and b['train_preference']=='G' else 'PERSISTENT_B_PREFERENCE' if a['train_preference']==b['train_preference']=='B' else 'OTHER_OR_MIXED'
            assert expected==result['rows'][seq]['formation_pattern']
            print('MF0 independent costs checked',seq,flush=True)
    assert cost_delta<1e-8 and gradient_delta<1e-8 and fd_delta<1e-5
    run.save(run.BASE/'validation.json',dict(passed=True,explicit_cost_records=cost_records,explicit_point_cost_max_delta=cost_delta,
        independent_translation_gradient_max_delta=gradient_delta,directional_fd_max_delta=fd_delta,
        all_preferences_and_patterns_checked=True,old_CV2_diagnostic_reproduced=True,optimizer_calls=0,
        calibrated_accuracy_or_physical_causality=False))
    (run.BASE/'INCOMPLETE').unlink()


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=('bank','evaluate'))
    stage=parser.parse_args().stage;run.record('validate_'+stage,globals()[stage])
