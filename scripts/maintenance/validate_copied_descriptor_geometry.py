"""CDG0 full brute-force descriptors/Horn/known-fixture metric audit, no model."""
import math,numpy as np
import copied_descriptor_geometry_control as r
import validate_native_backward as e
def load(q):
    with np.load(q,allow_pickle=False) as z:return {k:z[k].copy() for k in z.files}
def validate():
    r.verify();folder=r.BASE/'predictions';s=r.read(r.BASE/'prediction_seal.json');assert s['freeze_sha256']==r.sha(r.BASE/'freeze.json') and s['files']=={str(q.relative_to(folder)):r.sha(q) for q in sorted(folder.rglob('*')) if q.is_file()};ex=r.read(folder/'execution.json');assert ex['descriptor_queries']==4000 and ex['complete_pairs']==2 and not ex['truth_target_loaded'] and not ex['HFIT_partial_predictions_used']
    obs=load(folder/'observations.npz');points=obs['points'];features=obs['features'];rows=[];maxNN=0.;queries=0;directed_distances=0
    with np.load(r.INPUT,allow_pickle=False) as z:assert np.array_equal(z['points'],points) and np.array_equal(z['features'],features)
    for part in (1,2):
        for direction,left,right in [('part_to_anchor',part,0),('anchor_to_part',0,part)]:
            source=features[left*1000:(left+1)*1000].astype(float);target=features[right*1000:(right+1)*1000].astype(float);saved=load(folder/f'part{part}_{direction}.npz');nearest=[]
            for start in range(0,1000,32):
                dist=np.sum((source[start:start+32,None,:]-target[None,:,:])**2,axis=2);rank=np.argsort(dist,axis=1,kind='stable')[:,:2];expected=np.sqrt(np.take_along_axis(dist,rank,axis=1));actual=saved['distance'][start:start+len(rank)];delta=float(np.max(abs(actual-expected)));assert delta<=1e-10*max(1.,float(expected.max()));maxNN=max(maxNN,delta)
                for i,choice in enumerate(saved['index'][start:start+len(rank)]):
                    actual_dist=np.sqrt(dist[i,choice]);assert np.max(abs(actual_dist-expected[i]))<=1e-10*max(1.,float(expected[i].max()))
                    if expected[i,1]>expected[i,0]:assert choice[0]==rank[i,0]
                nearest.extend(rank[:,0]);queries+=len(rank);directed_distances+=len(rank)*1000;r.cap()
            record=next(x for x in ex['records'] if x['part']==part and x['direction']==direction);assert record['nearest_ties']==int(np.count_nonzero(saved['distance'][:,0]==saved['distance'][:,1])) and record['unique_first_indices']==len(np.unique(saved['index'][:,0]));rows.append(dict(part=part,direction=direction,all1000_bruteforce_queries_verified=True,index_identity_matches=int(np.count_nonzero(saved['index'][:,0]==np.arange(1000))),max_first_descriptor_distance=record['max_first_descriptor_distance']))
    assert queries==4000 and directed_distances==4000000
    # Fixture truth is read only after complete geometric prediction seal verified.
    metrics=[];poses=load(folder/'poses.npz');maxHorn=0.
    if ex['all_support']:
        with np.load(r.INPUT,allow_pickle=False) as z:truth=z['truth'].copy()
        for part in (1,2):
            index=load(folder/f'part{part}_part_to_anchor.npz')['index'][:,0];rot,shift=e.horn(points[part*1000:(part+1)*1000].astype(float),points[:1000][index].astype(float));pose=poses[f'part{part}'];delta=max(float(np.max(abs(rot-pose[:3,:3]))),float(np.max(abs(shift-pose[:3,3]))));assert delta<=1e-10;maxHorn=max(maxHorn,delta)
            assert np.max(abs(pose[:3,:3].T@pose[:3,:3]-np.eye(3)))<=1e-10 and abs(np.linalg.det(pose[:3,:3])-1)<=1e-10
            Rdelta=truth[part,:3,:3].T@pose[:3,:3];skew=np.array([Rdelta[2,1]-Rdelta[1,2],Rdelta[0,2]-Rdelta[2,0],Rdelta[1,0]-Rdelta[0,1]]);angle=math.degrees(math.atan2(np.linalg.norm(skew),np.trace(Rdelta)-1));translation=float(np.linalg.norm(pose[:3,3]-truth[part,:3,3]));fit_residual=float(np.max(abs(points[part*1000:(part+1)*1000]@pose[:3,:3].T+pose[:3,3]-points[:1000][index])));gate=translation<=.005 and angle<=.05
            metrics.append(dict(part=part,t_m=translation,R_deg=angle,all_point_registration_max_residual_m=fit_residual,control_5mm_05deg_pass=gate))
    ceiling=ex['all_support'] and all(x['control_5mm_05deg_pass'] for x in metrics)
    decision='COPIED_DESCRIPTOR_FIXTURE_GEOMETRY_CEILING_RECOVERED_WITHOUT_LEARNING' if ceiling else 'COPIED_DESCRIPTOR_CONTROL_UNRESOLVED_SUPPORT_OR_POSE_GATE'
    r.verify();r.save(r.BASE/'results.json',dict(decision=decision,complete_two_part_control=ceiling,ambiguity_and_support=ex['support'],metrics=metrics,independent_scenes=1,copied_descriptor_exposed_fixture=True,real_physical_or_system_baseline=False,head_fitting_or_native_updates=0,stop_copied_fixture_as_RAP_context_efficacy_test=ceiling))
    r.save(r.BASE/'validation.json',dict(passed=True,decision=decision,full_bruteforce_queries=queries,directed_descriptor_distances=directed_distances,nearest_distance_max_delta=maxNN,independent_Horn_max_delta=maxHorn,all_4000_NN_queries_verified=True,records=rows,predictions_sealed_before_new_fixture_truth_errors=True,control_conjunction=ceiling,no_partial_HFIT_GTevaluation=True))
    print('CDG0 independent complete control',decision,flush=True)
