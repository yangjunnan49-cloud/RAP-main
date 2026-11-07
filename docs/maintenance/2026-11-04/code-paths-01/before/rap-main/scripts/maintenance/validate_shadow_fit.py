"""HFIT0 independent CPU update/loss/rigidity/metric census; no torch import."""
import math
import numpy as np
import shadow_conditioned_fit as r
import validate_native_backward as e

def parts(z,q):
    poses=[];shapes=[]
    for k in range(3):
        x=z['cond'][k*1000:(k+1)*1000].astype(float);y=q[k*1000:(k+1)*1000].astype(float);rot,shift=e.horn(x,y)
        pose=np.eye(4);pose[:3,:3]=rot;pose[:3,3]=float(z['scale'])*shift-rot@z['centers'][k].astype(float);poses.append(pose)
        shapes.append(float(np.mean((float(z['scale'])*(y-x@rot.T-shift))**2)))
    return np.array(poses),float(np.mean(shapes))
def terms(z,q):
    ps,shape=parts(z,q);translation=[];rotation=[]
    for k in (1,2):
        rel=np.linalg.solve(ps[0],ps[k]);translation.append(float(np.sum(((rel[:3,3]-z['truth'][k,:3,3])/.05)**2)));rotation.append(float(np.sum((z['truth'][k,:3,:3].T@rel[:3,:3]-np.eye(3))**2)/(2*math.radians(.2)**2)))
    return dict(translation=float(np.mean(translation)),rotation=float(np.mean(rotation)),shape=.001*shape/.05**2)
def pose_metrics(z,q):
    ps,_=parts(z,q);values=[]
    for k in (1,2):
        rel=np.linalg.solve(ps[0],ps[k]);delta=z['truth'][k,:3,:3].T@rel[:3,:3];skew=np.array([delta[2,1]-delta[1,2],delta[0,2]-delta[2,0],delta[1,0]-delta[0,1]])
        values.append(dict(part=k,t_m=float(np.linalg.norm(rel[:3,3]-z['truth'][k,:3,3])),R_deg=float(np.degrees(np.arctan2(np.linalg.norm(skew),np.trace(delta)-1)))))
    return values
def objective(z,noise,out,arm):
    assert np.array_equal(noise-out['velocity'],out['output'])
    if arm=='V':return dict(velocity=float(np.mean((out['velocity']-(noise-z['target'].astype(float)))**2)))
    return terms(z,out['output'])
def validate_fit():
    r.verify();r.r.check_seal(r.BASE/'preflight','preflight_seal.json');r.r.check_seal(r.BASE/'fits','fit_seal.json');ex=r.read(r.BASE/'fits/execution.json')
    assert ex['actual_retained_updates']==40 and ex['shadow_tail_forwards']==80 and ex['backwards']==40 and ex['prefix_calls']==1 and ex['optimizer_API_calls']==0 and ex['double_artifact_states_preserved'] and ex['original_live_values_dtypes_restored']
    z=e.load(r.r.r.OLD/'bank/synthetic_fixture.npz');noise=e.load(r.r.r.OLD/'bank/noise/fit_00.npz')['noise'].astype(float);initial={k:v.astype(float) for k,v in e.load(r.r.r.OLD/'preflight/P/initial.npz').items()};rows=[];local=[];maxcost=0.;upmax=0.;fdrows=[]
    directions=[];rng=np.random.default_rng(417)
    for k,col in ((1,0),(2,1),(0,2)):
        d=np.zeros((3000,3));d[k*1000:(k+1)*1000,col]=1.;directions.append(d)
    for _ in range(9):
        d=rng.normal(size=(3000,3));d/=np.linalg.norm(d);directions.append(d)
    for arm in ('V','P'):
        previous=initial
        for step in range(1,21):
            folder=r.BASE/f'fits/{arm}/step_{step:02d}';row=r.read(folder/'update.json');assert row==next(x for x in ex['records'] if (x['arm'],x['step'])==(arm,step))
            before=e.load(folder/'before.npz');grad=e.load(folder/'gradients.npz');after=e.load(folder/'after.npz');out=e.load(folder/'output_before.npz');post=e.load(folder/'output_after.npz')
            assert set(before)==set(grad)==set(after)==set(initial) and all(np.array_equal(before[k],v) for k,v in previous.items())
            assert all(v.dtype==np.float64 and np.isfinite(v).all() for values in (before,grad,after,out,post) for v in values.values())
            norm=math.sqrt(sum(float(np.sum(g*g)) for g in grad.values()));assert abs(norm-row['gradient_norm'])<=1e-12*max(1.,norm)
            radius=min(.001,.001*row['loss_before']/norm);assert abs(radius-row['radius'])<=1e-15;expected={k:v-row['radius']*grad[k]/row['gradient_norm'] for k,v in before.items()};assert all(np.array_equal(after[k],v) for k,v in expected.items())
            dot=sum(float(np.sum(grad[k]*(after[k]-v))) for k,v in before.items());length=math.sqrt(sum(float(np.sum((after[k]-v)**2)) for k,v in before.items()));assert dot==row['actual_dot'] and abs(length-row['actual_parameter_norm'])<=1e-15 and dot<0 and length<=row['radius']*(1+1e-10)
            preterms=objective(z,noise,out,arm);postterms=objective(z,noise,post,arm)
            for expected_terms,stored in ((preterms,row['terms_before']),(postterms,row['terms_after'])):
                assert set(expected_terms)==set(stored)
                for k,v in expected_terms.items():delta=abs(v-stored[k]);assert delta<=1e-7;maxcost=max(maxcost,delta)
            L=sum(preterms.values());La=sum(postterms.values());assert abs(L-row['loss_before'])<=1e-7 and abs(La-row['loss_after'])<=1e-7;pass_descent=La<=L+.5*dot;assert pass_descent==row['Armijo_pass']
            if arm=='V':
                delta=float(np.max(abs(-2*(out['velocity']-(noise-z['target'].astype(float)))/9000-out['upstream'])));assert delta<=1e-14;upmax=max(upmax,delta)
            else:
                for j,d in enumerate(directions):
                    fd=(e.objective(z,out['output']+1e-6*d)-e.objective(z,out['output']-1e-6*d))/2e-6;analytic=float(np.sum(out['upstream']*d));error=abs(fd-analytic);bound=max(1e-4,1e-5*abs(fd));assert error<=bound;fdrows.append(dict(step=step,direction=j,error=error,bound=bound))
            if step in (1,20):
                hooks=e.load(folder/'hooks.npz');assert len(hooks)==12
                for module in sorted({k.split('|')[0] for k in hooks}):
                    x=hooks[module+'|input'];go=hooks[module+'|scaled_gradient'];rank=hooks[module+'|rank'];A=before[module+'.A'];B=before[module+'.B'];factor=1024 if arm=='V' else 1/1024
                    rankdelta=float(np.max(abs(x@A.T-rank)));assert rankdelta<=max(1e-10,1e-10*float(np.max(abs(rank))))
                    for group,value in {'A':(go@B).T@x/factor,'B':go.T@rank/factor}.items():
                        actual=grad[module+'.'+group];delta=float(np.max(abs(value-actual)));bound=max(1e-10,1e-10*float(np.max(abs(actual))));assert delta<=bound;local.append(dict(arm=arm,step=step,module=module,group=group,delta=delta,bound=bound))
            rows.append(dict(arm=arm,step=step,loss_before=L,loss_after=La,actual_dot=dot,Armijo_pass=pass_descent,parameter_arrays_exact=True));previous=after;r.cap()
        final=e.load(r.BASE/f'fits/{arm}/parameters_20.npz');assert all(np.array_equal(final[k],v) for k,v in previous.items())
    assert len(local)==32 and len(rows)==40;conjunction=all(x['Armijo_pass'] for x in rows)
    r.verify();r.save(r.BASE/'fit_validation.json',dict(passed=True,fit_conjunction=conjunction,rows=rows,actual_retained_updates=40,optimizer_API_calls=0,independent_parameter_rule_replay=True,independent_neural_optimizer_replay=False,local_A_B_checks=local,P_output_directional_FD=fdrows,independent_loss_terms_max_delta=maxcost,V_upstream_max_delta=upmax,double_final_states_verified=True))
    print('HFIT0 independent40 update conjunction',conjunction,flush=True)
def distribution(values):
    x=np.asarray(values,float);return dict(mean=float(x.mean()),median=float(np.median(x)),q90=float(np.quantile(x,.9,method='linear')),std=float(x.std()),min=float(x.min()),max=float(x.max()))
def cell_gate(bt,br,at,ar,g):
    bt,br,at,ar=map(lambda x:np.asarray(x,float),(bt,br,at,ar));dt=bt-at;dr=br-ar;B=dict(t=distribution(bt),R=distribution(br));A=dict(t=distribution(at),R=distribution(ar));signs=int(np.sum((dt>=0)&(dr>=0)))
    tests=dict(mean_t=A['t']['mean']<=g['mean_t_ratio']*B['t']['mean'],median_t=float(np.median(dt))>=g['median_t_gain_m'],mean_R=A['R']['mean']<=B['R']['mean']+g['mean_R_slack_deg'],median_R=float(np.median(dr))>=g['median_R_gain_deg'],joint_signs=signs>=g['joint_nonworse_min'],q90_t=A['t']['q90']<=g['q90_t_ratio']*B['t']['q90'],q90_R=A['R']['q90']<=B['R']['q90']+g['q90_R_slack_deg'])
    return dict(B=B,A=A,paired_t_gain=distribution(dt),paired_R_gain=distribution(dr),joint_nonworse=signs,tests={k:bool(v) for k,v in tests.items()},passed=bool(all(tests.values())))
def evaluate():
    r.verify();r.r.check_seal(r.BASE/'predictions','prediction_seal.json');ex=r.read(r.BASE/'predictions/execution.json');assert ex['complete_source_sampler_traces']==51 and ex['shadow_tail_forwards']==ex['prefix_calls']==255 and ex['no_truth_target_arrays_loaded'] and ex['all_live_values_restored']
    z=e.load(r.r.r.OLD/'bank/synthetic_fixture.npz');condition=z['cond'].astype(float);records=[];maxrig=0.;maxstate=0.;buffer_outside=0;part_fits=0
    for row in ex['records']:
        folder=r.BASE/f"predictions/{row['arm']}_{row['noise']}";source=e.load(folder/'source_trajectory.npz');meta=r.read(folder/'trace.json');noise=e.load(r.r.r.OLD/f"bank/noise/{row['noise']}.npz")['noise'].astype(float);assert meta['taus']==[1-i*.2 for i in range(5)];previous=None;first=None
        for i,tau in enumerate(meta['taus']):
            v=e.load(folder/f'step_{i}.npz');assert np.array_equal(v['prefix_input'],v['state'].astype(np.float32)) and np.array_equal(v['timestep'],np.array([tau],np.float32))
            if i==0:assert np.array_equal(v['state'],noise);first=v
            else:delta=float(np.max(abs(v['state']-previous)));assert delta<=1e-10;maxstate=max(maxstate,delta)
            endpoint=v['state']-tau*v['velocity'];rigid=[]
            for k in range(3):
                x=condition[k*1000:(k+1)*1000];rot,shift=e.horn(x,endpoint[k*1000:(k+1)*1000]);rigid.append(x@rot.T+shift);part_fits+=1
            rigid=np.concatenate(rigid);delta=float(np.max(abs(rigid-v['rigid'])));assert delta<=1e-10;maxrig=max(maxrig,delta);previous=rigid*(1-tau+.2)+noise*(tau-.2)
            for name,expected in [('end_point_trajectory',endpoint),('trajectory',previous)]:
                actual=source[name][i];difference=abs(expected.astype(np.float32).astype(float)-actual.astype(float));outside=int(np.sum(difference>abs(np.spacing(actual).astype(float))));assert outside==0;buffer_outside+=outside
            r.cap()
        records.append(dict(row,first=pose_metrics(z,source['end_point_trajectory'][0].astype(float)),final=pose_metrics(z,source['end_point_trajectory'][-1].astype(float)),first_velocity_MSE=float(np.mean((first['velocity']-(noise-z['target'].astype(float)))**2)),first_buffer_pose_loss=e.objective(z,source['end_point_trajectory'][0].astype(float))))
    assert part_fits==765;gate=r.read(r.BASE/'freeze.json')['gate'];cells=[]
    for arm in ('V','P'):
        for part in (1,2):
            def values(a,key):return [next(x[key] for x in v['final'] if x['part']==part) for v in records if v['arm']==a and v['role']=='old_eval']
            cells.append(dict(arm=arm,part=part,**cell_gate(values('U','t_m'),values('U','R_deg'),values(arm,'t_m'),values(arm,'R_deg'),gate)))
    summary=dict(cells=cells,conditional_noise_conjunction=all(x['passed'] for x in cells),fit_diagnostics=[x for x in records if x['role']=='fit_diagnostic'],old_eval_noises=16,independent_scenes=1,not_fresh_noise=True)
    decision='BOUNDED_SHADOW_FIT_COMPLETE_WITH_CONDITIONAL_NOISE_SIGNAL' if summary['conditional_noise_conjunction'] else 'BOUNDED_SHADOW_FIT_COMPLETE_NO_SAFE_MATERIAL_NOISE_CONJUNCTION'
    r.verify();r.save(r.BASE/'results.json',dict(records=records,summary=summary,decision=decision,actual_retained_updates=40,original_native_equivalence=False,system_or_physical_gain_claim=False))
    r.save(r.BASE/'validation.json',dict(passed=True,fit_validation=r.read(r.BASE/'fit_validation.json'),complete_paired_traces=51,independent_Horn_part_fits=765,independent_rigid_max_delta=maxrig,independent_state_max_delta=maxstate,float32_buffer_outside_ULP=buffer_outside,all_prediction_bindings_and_counts=True,metrics_and_gates_independently_reconstructed=True,independent_complete_model=False,decision=decision,conditional_noise_conjunction=summary['conditional_noise_conjunction']))
    print('HFIT0 independent complete pilot',decision,flush=True)
def validate(stage):
    if stage=='validate_fit':validate_fit()
    elif stage=='evaluate':evaluate()
    else:raise ValueError(stage)
