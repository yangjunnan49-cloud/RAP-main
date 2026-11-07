"""FCE0 CPU source/input/context isolation and feature census; no model/GT."""
import ast,numpy as np
import frozen_context_extraction as r
def load(q):
    with np.load(q,allow_pickle=False) as z:return {k:z[k].copy() for k in z.files}
def validate():
    r.verify();folder=r.BASE/'features';s=r.read(r.BASE/'feature_seal.json');assert s['freeze_sha256']==r.sha(r.BASE/'freeze.json') and s['files']=={str(q.relative_to(folder)):r.sha(q) for q in sorted(folder.rglob('*')) if q.is_file()}
    ex=r.read(folder/'execution.json');assert ex['prefix_helper_calls']==12 and ex['full_FP32_flow_forwards']==4 and ex['native_backwards']==ex['head_backwards']==ex['retained_updates']==ex['source_sampler_calls']==0 and not ex['truth_target_arrays_loaded']
    observations=load(folder/'observations.npz');assert set(observations)=={'points','features','cond','scale','centers','counts'}
    source_bank=r.ROOT/'docs/maintenance/2026-10-10/native-conditioned-comparison-01/attempt-02/bank'
    with np.load(source_bank/'synthetic_fixture.npz',allow_pickle=False) as z:assert all(np.array_equal(z[k],v) for k,v in observations.items())
    model_tree=ast.parse((r.ROOT/'rectified_point_flow/flow_model/point_cloud_dit.py').read_text());layer_tree=ast.parse((r.ROOT/'rectified_point_flow/flow_model/layer.py').read_text());assert any(isinstance(n,ast.For) and isinstance(n.iter,ast.Call) and isinstance(n.iter.func,ast.Name) and n.iter.func.id=='enumerate' for n in ast.walk(model_tree))
    cls=next(n for n in layer_tree.body if isinstance(n,ast.ClassDef) and n.name=='DiTLayer');forward=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='forward');attention=[n for n in ast.walk(forward) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in ('_part_attention','_global_attention')]
    assert [(n.func.attr,ast.unparse(n.args[1])) for n in attention]==[('_part_attention','cu_seqlens_part'),('_global_attention','cu_seqlens_batch')]
    rows=[];pools={}
    for noise in ('fit_00','eval_00'):
        references={}
        for layout in ('J_joint','I_separated'):
            q=folder/f'{noise}_{layout}';inputs=load(q/'inputs.npz');a=load(q/'helper1.npz');b=load(q/'helper2.npz');hook=load(q/'hook.npz');changed=load(q/'perturbed.npz');xin=load(q/'perturbed_input.npz')['x']
            assert a.keys()==b.keys()==changed.keys()=={'D_pointwise','prefix'} and hook.keys()=={'D_pointwise','prefix','velocity'}
            assert all(np.array_equal(a[k],b[k]) and np.array_equal(a[k],hook[k]) for k in a)
            assert all(v.dtype==np.float32 and np.isfinite(v).all() for z in (a,b,hook,changed,inputs) for v in z.values() if v.dtype.kind=='f')
            assert np.array_equal(inputs['cu_seqlens_part'],[0,1000,2000,3000]) and np.array_equal(inputs['cu_seqlens_batch'],[0,3000] if layout=='J_joint' else [0,1000,2000,3000])
            assert np.array_equal(inputs['timesteps'],np.ones(1 if layout=='J_joint' else 3,dtype=np.float32))
            with np.load(source_bank/f'noise/{noise}.npz',allow_pickle=False) as z:assert np.array_equal(inputs['x'],z['noise'])
            assert np.array_equal(inputs['cond_coord'],observations['cond']) and np.array_equal(inputs['local_features'],observations['features'])
            assert inputs['anchor_indices'].dtype==np.bool_ and np.array_equal(inputs['anchor_indices'],np.arange(3000)<1000)
            assert np.array_equal(inputs['scales'],np.full(1 if layout=='J_joint' else 3,float(observations['scale']),dtype=np.float32))
            assert np.array_equal(xin[:1000],inputs['x'][:1000]) and np.array_equal(xin[1000:],inputs['x'][1000:]+np.array([.125,-.0625,.03125],np.float32))
            assert np.array_equal(changed['D_pointwise'][:1000],a['D_pointwise'][:1000])
            diff=changed['prefix'][:1000].astype(float)-a['prefix'][:1000].astype(float);changed_count=int(np.count_nonzero(diff));delta=float(np.max(abs(diff)))
            if layout=='I_separated':assert changed_count==0
            else:
                assert changed_count>0
                with np.load(r.SOURCE/f'bank/{noise}_helper1/step_0.npz',allow_pickle=False) as z:assert np.array_equal(z['prefix'],a['prefix']) and np.array_equal(z['prefix_input'],inputs['x'])
            references[layout]=a
            rows.append(dict(noise=noise,layout=layout,repeat_and_full_hook_byteexact=True,part0_pointwise_unchanged=True,part0_changed_prefix_entries=changed_count,part0_max_prefix_delta=delta,separated_isolation_pass=changed_count==0 if layout=='I_separated' else None))
            for arm,v in [('D_pointwise',a['D_pointwise']),('J_joint' if layout=='J_joint' else 'I_separated',a['prefix'])]:
                pooled=np.array([v[k*1000:(k+1)*1000].astype(float).mean(axis=0) for k in range(3)])
                if arm=='D_pointwise' and f'{noise}_{arm}' in pools:assert np.array_equal(pools[f'{noise}_{arm}'],pooled)
                else:pools[f'{noise}_{arm}']=pooled
            r.cap()
        assert np.array_equal(references['J_joint']['D_pointwise'],references['I_separated']['D_pointwise'])
    assert len(rows)==4 and len(pools)==6
    np.savez(r.BASE/'pooled_features.npz',**pools)
    r.verify();r.save(r.BASE/'validation.json',dict(passed=True,decision='FROZEN_FEATURE_EXTRACTION_AND_CONTEXT_ISOLATION_BINDINGS_VALID',records=rows,SAR0_initial_joint_prefix_byteexact=True,joint_prefix_context_dependence_observed=True,separated_part0_causal_input_isolation_byteexact=True,pointwise_features_same_in_all_layouts=True,pooled_features_shape=[3,512],pooled_feature_role='fixed float64 means; no head or capacity claim yet',no_GT_pose_metric_or_training=True,source_sampler_calls=0,original_native_FP16_equivalence=False,not_physical_or_system_headroom=True))
    print('FCE0 complete frozen extraction/context isolation passes',flush=True)
