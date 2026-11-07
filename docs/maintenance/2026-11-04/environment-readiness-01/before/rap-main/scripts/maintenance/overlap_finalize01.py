from overlap_core01 import np,time,r,old,FINE,AD,module,cap,save,read
def finish(cell,s,m,key,n,dest,c,slam,recorder,membership,o,fixed,reset_events,begin,timing,chain):
    slam.generate_new_node();slam.local_map_graph.erase_last_local_map();initial=np.asarray(slam.poses);fine_begin=time.monotonic();frontend_delta=None;anchor_max=None;reconstruction=None
    if m=='G':
        reference=r.proper(r.poses(old.src(s)/'odom_poses.txt'));frontend_delta=float(np.max(abs(reference-o)))
        if frontend_delta>1e-5:np.save(dest/'failed_frontend.npy',o);np.save(dest/'failed_initial.npy',initial)
        assert frontend_delta<=1e-5,('E0 frontend correspondence failed',frontend_delta)
        anchors=[];coarse=[];reconstruction=0.
        for mid,frames in membership.items():
            a=0 if int(mid)==0 else fixed.resets[int(mid)-1];p=initial[frames[0]]@np.linalg.solve(o[frames[0]],o[a]);anchors.append(a);coarse.append(p)
            for i in frames:reconstruction=max(reconstruction,float(np.max(abs(p@np.linalg.solve(o[a],o[i])-initial[i]))))
        assert reconstruction<=1e-8 and anchors==sorted(set(anchors)) and anchors[0]==0
        coarse=np.asarray(coarse);fine_module=module('raw_anchor_fine',FINE/'anchor_fine.py');t=fine_module.fine(o,initial,anchors,coarse,c.pose_graph_optimizer);anchor_max=float(np.max(abs(t[anchors]-coarse)));assert anchor_max<=1e-8
        anchor_record=dict(anchor_frames=anchors,coarse_poses=coarse.tolist(),maximum_reconstruction=reconstruction,maximum_preservation=anchor_max)
        resets=fixed.resets;relative=fixed.max_relative_error;assert relative<=1e-9 and resets==reset_events
    else:
        t,pgo=slam.fine_grained_optimization();t=np.asarray(t);resets=reset_events;relative=None
    fine_seconds=time.monotonic()-fine_begin;serialization_begin=time.monotonic()
    if m=='G':
        np.save(dest/'odometry.npy',o);np.save(dest/'before_fine.npy',initial);save(dest/'anchors.json',anchor_record)
    else:pgo.write_graph(str(dest/'trajectory.g2o'))
    assert t.shape==(n,4,4) and np.isfinite(t).all();rot=t[:,:3,:3];assert np.max(abs(rot.transpose(0,2,1)@rot-np.eye(3)))<=1e-5 and np.max(abs(np.linalg.det(rot)-1))<=1e-5
    assert sorted(i for group in membership.values() for i in group)==list(range(n));np.save(dest/'poses.npy',t);np.save(dest/'frame_timing.npy',np.asarray(timing));slam.optimizer.write_graph(str(dest/'map_graph.g2o'))
    save(dest/'source_binding.json',dict(source_frame_ids=list(range(n)),map_consumed_frames=membership,reset_anchors=resets,consumed_ordered_hash_chain=chain.hexdigest(),per_return_voxel_lineage=False,
        inherited_voxel_conservative_prefixes=[[0,i] for i in resets] if resets is not None else None,loop_attempts=recorder.rows,frontend_reference_max=frontend_delta,adapter_relative_max=relative,
        anchor_preservation_max=anchor_max,coarse_reconstruction_max=reconstruction,GT_numeric_read=False))
    save(dest/'execution.json',dict(utc=now(),cell=cell,frames=n,local_maps=len(membership),closures=len(slam.closures),loop_calls=len(recorder.rows),raw_loop_and_finalize_seconds=time.monotonic()-begin,
        fine_seconds=fine_seconds,serialization_seconds=time.monotonic()-serialization_begin,private_evidence_outputs_identical=False,frame_timing_columns=['read_hash','preprocess','E0_frontend_separate_G_only','native_process_scan','frame_total'],new_raw_frontend=True,large_map_exports=False))
    cap();print('complete',key,'frontend_max',frontend_delta,'loops',len(slam.closures),flush=True)
