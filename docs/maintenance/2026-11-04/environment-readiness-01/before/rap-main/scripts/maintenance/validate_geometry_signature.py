"""GSG0 independent direct distances/full candidates/Horn/fixture metrics."""
import math,numpy as np
import geometry_signature_control as r
import validate_native_backward as e
def load(q):
    with np.load(q,allow_pickle=False) as z:return {k:z[k].copy() for k in z.files}
def check_seal(folder,name):
    s=r.read(r.BASE/name);assert s['freeze_sha256']==r.sha(r.BASE/'freeze.json') and s['files']=={str(q.relative_to(folder)):r.sha(q) for q in sorted(folder.rglob('*')) if q.is_file()}
def independent_signature(p):return np.sort(np.sqrt(np.sum((p[:,None,:]-p[None,:,:])**2,axis=2)),axis=1)
def brute(source,target,target_points,saved):
    count=len(source);maxdelta=0.;ambiguity=0;firstmax=0.;candidate_count=0
    for start in range(0,count,8):
        distances=np.sqrt(np.sum((source[start:start+8,None,:]-target[None,:,:])**2,axis=2));expected=np.sort(distances,axis=1)[:,:2];delta=float(np.max(abs(saved['distance'][start:start+len(expected)]-expected)));assert delta<=1e-10*max(1.,float(expected.max()));maxdelta=max(maxdelta,delta)
        for j,d in enumerate(distances):
            index=start+j;chosen=saved['index'][index];assert np.max(abs(d[chosen]-expected[j]))<=1e-10*max(1.,float(expected[j].max()));ids=np.flatnonzero(d<=d.min()+r.EPS);actual=saved['candidate_indices'][saved['candidate_offsets'][index]:saved['candidate_offsets'][index+1]];assert np.array_equal(ids,actual) and saved['chosen'][index]==ids[0]
            coords=target_points[ids];ambiguity+=int(not np.array_equal(coords,np.broadcast_to(coords[0],coords.shape)));candidate_count+=len(ids);firstmax=max(firstmax,float(d.min()))
        r.cap()
    valid=ambiguity==0 and firstmax<=r.EPS;return dict(valid=bool(valid),ambiguity=ambiguity,candidate_count=candidate_count,firstmax=firstmax,maxdelta=maxdelta)
def validate():
    r.verify();check_seal(r.BASE/'preflight','preflight_seal.json');check_seal(r.BASE/'predictions','prediction_seal.json');fixtures=[]
    for row in r.read(r.BASE/'preflight/execution.json')['fixtures']:
        z=load(r.BASE/'preflight'/(row['name']+'.npz'));a=independent_signature(z['source']);b=independent_signature(z['target']);assert np.max(abs(a-z['source_signature']))<=1e-10 and np.max(abs(b-z['target_signature']))<=1e-10;support=brute(z['source_signature'],z['target_signature'],z['target'],z);assert support['valid']==row['expected_full_support']
        if support['valid']:
            R,t=e.horn(z['source'],z['target'][z['chosen']]);T=np.eye(4);T[:3,:3]=R;T[:3,3]=t;assert np.max(abs(T-z['pose']))<=1e-10 and np.max(abs(T-z['known_fixture_transform']))<=1e-10
        fixtures.append(dict(name=row['name'],passed=True,expected_full_support=row['expected_full_support']))
    folder=r.BASE/'predictions';points=np.load(folder/'points.npy',allow_pickle=False)
    with np.load(r.INPUT,allow_pickle=False) as z:assert np.array_equal(points,z['points'])
    sig=[];sigmax=0.
    for k in range(3):
        actual=np.load(folder/f'signature_part{k}.npy',allow_pickle=False);expected=independent_signature(points[k*1000:(k+1)*1000]);delta=float(np.max(abs(actual-expected)));assert delta<=1e-10;sigmax=max(sigmax,delta);sig.append(actual)
    ex=r.read(folder/'execution.json');assert not ex['descriptors_truth_target_or_CDG_matches_loaded'] and ex['signature_NN_queries']==4000;supportrows=[];nmax=0.
    for part in (1,2):
        for name,left,right in [('forward',part,0),('reverse',0,part)]:
            saved=load(folder/f'part{part}_{name}.npz');result=brute(sig[left],sig[right],points[right*1000:(right+1)*1000],saved);original=next(x[name] for x in ex['records'] if x['part']==part);assert result['valid']==original['full_coordinate_support'] and result['ambiguity']==original['different_coordinate_candidate_ambiguity'] and result['candidate_count']==original['candidate_count'];nmax=max(nmax,result['maxdelta']);supportrows.append(dict(part=part,direction=name,**result))
    allsupport=all(x['valid'] for x in supportrows);assert allsupport==ex['all_support'];metrics=[];hornmax=0.;poses=load(folder/'poses.npz')
    if allsupport:
        # Only complete coordinate-only prediction seal admits new original-fixture errors.
        with np.load(r.INPUT,allow_pickle=False) as z:truth=z['truth'].copy()
        for part in (1,2):
            fn=load(folder/f'part{part}_forward.npz')['chosen'];rv=load(folder/f'part{part}_reverse.npz')['chosen'];a=points[part*1000:(part+1)*1000];assert np.array_equal(a[rv[fn]],a);R,t=e.horn(a,points[:1000][fn]);T=poses[f'part{part}'];delta=max(float(np.max(abs(R-T[:3,:3]))),float(np.max(abs(t-T[:3,3]))));assert delta<=1e-10;hornmax=max(hornmax,delta);Rd=truth[part,:3,:3].T@T[:3,:3];skew=np.array([Rd[2,1]-Rd[1,2],Rd[0,2]-Rd[2,0],Rd[1,0]-Rd[0,1]]);angle=math.degrees(math.atan2(np.linalg.norm(skew),np.trace(Rd)-1));translation=float(np.linalg.norm(T[:3,3]-truth[part,:3,3]));residual=float(np.max(abs(a@T[:3,:3].T+T[:3,3]-points[:1000][fn])));assert np.max(abs(T[:3,:3].T@T[:3,:3]-np.eye(3)))<=1e-10 and abs(np.linalg.det(T[:3,:3])-1)<=1e-10;metrics.append(dict(part=part,t_m=translation,R_deg=angle,all1000_point_fit_max_residual_m=residual,control_gate=translation<=.005 and angle<=.05))
    ceiling=allsupport and all(x['control_gate'] for x in metrics);decision='CONGRUENT_SYNTHETIC_GEOMETRY_CEILING_RECOVERED_NO_LEARNING_CONTEXT_EFFICACY_IDENTIFIABLE' if ceiling else 'COORDINATE_GEOMETRY_CONTROL_SUPPORT_OR_POSE_GATE_UNRESOLVED'
    r.verify();r.save(r.BASE/'results.json',dict(decision=decision,control_conjunction=ceiling,metrics=metrics,support=supportrows,one_exposed_exactly_congruent_scene=True,no_descriptor_or_RAP_inputs=True,not_real_physical_or_system_baseline=True,stop_fixture_as_RAP_context_efficacy_test=ceiling))
    r.save(r.BASE/'validation.json',dict(passed=True,decision=decision,fixtures=fixtures,independent_3000000_point_distances=True,independent_4000000_signature_vector_distances=True,signature_scalar_component_comparisons=4000000000,all4000_full_candidate_queries_verified=True,independent_signature_max_delta=sigmax,nearest_distance_max_delta=nmax,independent_Horn_max_delta=hornmax,control_conjunction=ceiling,prediction_seal_precedes_new_truth_errors=True,CDG0_failed_support_not_repaired=True,head_fitting=0))
    print('GSG0 independently validated',decision,flush=True)
