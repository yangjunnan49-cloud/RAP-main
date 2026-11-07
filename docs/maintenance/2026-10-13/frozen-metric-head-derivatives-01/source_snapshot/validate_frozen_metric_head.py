"""FHR0 independent Horn/FSUM/right-tangent/SciPy-exp/active-column checks."""
import math,numpy as np
from scipy.linalg import expm
import frozen_metric_head_derivatives as r
import validate_native_backward as e
def hat(v):
    t=v[:3];x,y,z=v[3:];return np.array([[0.,-z,y,t[0]],[z,0.,-x,t[1]],[-y,x,0.,t[2]],[0.,0.,0.,0.]])
def validate():
    r.verify();s=r.read(r.BASE/'trace_seal.json');folder=r.BASE/'traces';assert s['freeze_sha256']==r.sha(r.BASE/'freeze.json') and s['files']=={str(q.relative_to(folder)):r.sha(q) for q in sorted(folder.rglob('*')) if q.is_file()}
    ex=r.read(folder/'execution.json');assert ex['CPU_head_forwards']==246 and ex['CPU_head_backwards']==12 and len(ex['FD_trials'])==216 and ex['native_model_loads']==ex['native_backwards']==ex['optimizer_calls']==ex['retained_updates']==ex['GT_pose_errors']==0 and not ex['teacher_or_truth_loaded']
    f=r.read(r.BASE/'freeze.json');D=np.array(f['metric_scale']);directions=r.load(folder/'directions.npz');cots=r.load(folder/'cotangents.npz');obs=r.load(r.PRIOR/'features/observations.npz');pool=r.load(r.PRIOR/'pooled_features.npz');rows=[];fdchecks=[];maxbase=maxpool=maxgrad=maxexp=0.
    for noise in f['noise_names']:
        inputs=r.load(r.PRIOR/f'features/{noise}_J_joint/inputs.npz');velocity=r.load(r.PRIOR/f'features/{noise}_J_joint/hook.npz')['velocity'];endpoint=inputs['x'].astype(float)-velocity.astype(float);poses=[]
        for k in range(3):
            R,t=e.horn(obs['cond'][k*1000:(k+1)*1000].astype(float),endpoint[k*1000:(k+1)*1000]);P=np.eye(4);P[:3,:3]=R;P[:3,3]=float(obs['scale'])*t-R@obs['centers'][k].astype(float);poses.append(P)
        T=np.array([np.linalg.solve(poses[0],poses[k]) for k in (1,2)]);stored=r.load(folder/f'{noise}_base.npz');delta=float(np.max(abs(T-stored['relative'])));assert delta<=1e-10;maxbase=max(maxbase,delta);T=stored['relative']
        for arm in f['feature_arms']:
            dest=folder/f'{noise}_{arm}';h=np.load(dest/'inputs.npy',allow_pickle=False);p=pool[f'{noise}_{arm}'];assert np.array_equal(h,np.array([np.concatenate([p[0],p[k],[1.]]) for k in (1,2)]))
            source=r.load(r.PRIOR/f'features/{noise}_{"J_joint" if arm in ("D_pointwise","J_joint") else "I_separated"}/helper1.npz')['D_pointwise' if arm=='D_pointwise' else 'prefix']
            independent=np.array([[math.fsum(float(x) for x in source[k*1000:(k+1)*1000,j])/1000 for j in range(512)] for k in range(3)]);delta=float(np.max(abs(independent-p)));assert delta<=1e-10;maxpool=max(maxpool,delta)
            a=r.load(dest/'probe1.npz');b=r.load(dest/'probe2.npz');assert all(a[k].dtype==b[k].dtype and a[k].shape==b[k].shape and a[k].tobytes()==b[k].tobytes() for k in a) and a['pose'].tobytes()==T.tobytes() and np.count_nonzero(a['parameters'])==0
            tangents=np.array([[T[i]@hat(np.eye(6)[j]*D) for j in range(6)] for i in range(2)]);alpha=np.einsum('iab,ijab->ij',cots[noise],tangents);analytic=alpha.T@h;delta=float(np.max(abs(analytic-a['gradient'])));bound=max(1e-10,1e-10*float(np.max(abs(analytic))));assert delta<=bound;maxgrad=max(maxgrad,delta)
            columns=int(np.count_nonzero(np.any(h!=0,axis=0)))*6;sv=np.linalg.svd(h,compute_uv=False);rank=int(np.count_nonzero(sv>1e-12*sv.max()));assert columns==6150 and rank==2
            for trial in [x for x in ex['FD_trials'] if x['noise']==noise and x['arm']==arm]:
                vector=directions[f'direction_{trial["direction"]}'];expected=np.array([T[i]@expm(hat((h@(trial['sign']*trial['step']*vector).T)[i]*D)) for i in range(2)]);actual=np.load(r.BASE/trial['path'],allow_pickle=False);delta=float(np.max(abs(expected-actual)));assert delta<=1e-10;maxexp=max(maxexp,delta)
                assert np.max(abs(actual[:,:3,:3].transpose(0,2,1)@actual[:,:3,:3]-np.eye(3)))<=1e-10 and np.max(abs(np.linalg.det(actual[:,:3,:3])-1))<=1e-10 and np.array_equal(actual[:,3,:],np.array([[0.,0.,0.,1.]]*2))
            for j in range(9):
                vector=directions[f'direction_{j}'];reference=float(np.sum(analytic*vector))
                for step in f['FD_steps']:
                    def q(sign):return np.load(dest/f'direction_{j}_{step:g}_{sign:+d}.npy',allow_pickle=False)
                    fd=float(np.sum(cots[noise]*(q(1)-q(-1)))/(2*step));error=abs(fd-reference);bound=max(1e-6,1e-5*abs(reference));assert error<=bound;fdchecks.append(dict(noise=noise,arm=arm,direction=j,step=step,analytic=reference,FD=fd,error=error,bound=bound))
            convention=r.load(dest/'convention.npz');assert np.array_equal(convention['swapped'],convention['pose'][::-1]) and np.max(abs(convention['framed']-convention['G']@convention['pose']))<=1e-12
            rows.append(dict(noise=noise,arm=arm,nominal_parameters=6150,nonzero_output_Jacobian_columns=columns,feature_row_rank=rank,pose_output_Jacobian_rank=6*rank,repeat_byteexact=True,all_parameter_gradients_independently_verified=True,right_body_units_and_convention_pass=True));r.cap()
    assert len(rows)==6 and len(fdchecks)==108
    r.verify();r.save(r.BASE/'validation.json',dict(passed=True,decision='FROZEN_METRIC_SE3_HEAD_DERIVATIVES_AND_ACTIVE_COLUMNS_VALID',records=rows,FD_checks=fdchecks,independent_Horn_base_max_delta=maxbase,independent_FSUM_pool_max_delta=maxpool,full_parameter_gradient_max_delta=maxgrad,independent_SciPy_exponential_max_delta=maxexp,nominal_and_nonzero_output_Jacobian_columns_equal_6150=True,local_pose_output_Jacobian_rank_equal_12=True,not_full_native_capacity_or_dataset_rank=True,not_strong_geometry_baseline=True,CPU_head_backwards=12,native_backwards=0,retained_updates=0,GT_metrics=0,physical_system_or_novelty_claim=False))
    print('FHR0 independent head derivatives/6150 active columns/12 output rank pass',flush=True)
