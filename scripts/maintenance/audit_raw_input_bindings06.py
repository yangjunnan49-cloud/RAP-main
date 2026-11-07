"""All36 post-seal binding audit without GT or new prediction."""
import time
START=time.monotonic()
import sys,resource,signal,traceback,hashlib
from collections import Counter
from pathlib import Path
import numpy as np
import raw_input_system06 as d
r=d.r;BASE=d.BASE;SUP=d.SUP
def graph(path):
    vertices=[];edges=[];fixed=[]
    for line in path.read_text().splitlines():
        tokens=line.split()
        if not tokens:continue
        if tokens[0]=='VERTEX_SE3:QUAT':vertices.append(int(tokens[1]))
        elif tokens[0]=='EDGE_SE3:QUAT':edges.append(tuple(sorted((int(tokens[1]),int(tokens[2])))))
        elif tokens[0]=='FIX':fixed.append(int(tokens[1]))
        elif tokens[0].startswith('#'):continue
        else:raise ValueError(('Unknown graph record',tokens[0]))
    return vertices,Counter(edges),set(fixed)
def run():
    left=d.CAP-d.used();assert left>1;signal.signal(signal.SIGALRM,lambda a,b:(_ for _ in ()).throw(TimeoutError('original R0 cap')));signal.alarm(max(1,int(left)))
    ok=False;err=None
    try:
        d.verify();seal=d.read(BASE/'bank_seal06.json');assert seal['cells']==36
        for p,h in seal['files'].items():assert d.sha(BASE/'bank06'/p)==h,p
        d.save(BASE/'BINDING_AUDIT_FREEZE.json',dict(utc=d.now(),files={str(p):d.sha(p) for p in (Path(__file__),BASE/'BINDING_AUDIT_SCOPE.md',BASE/'bank_seal06.json')},remaining_original_seconds=left,GT_numeric_read=False))
        f=d.read(BASE/'freeze.json');rows={};total_frames=0;maximum=0.
        for cell in f['schedule']:
            key=cell['key'];s=cell['sequence'];m=cell['mode'];p=BASE/'bank06'/key;binding=d.read(p/'source_binding.json');n=f['counts'][s];t=np.load(p/'poses.npy');assert t.shape==(n,4,4)
            assert binding['source_frame_ids']==list(range(n));total_frames+=n;resets=binding['reset_anchors'];assert resets and resets[-1]==n-1 and resets==sorted(resets);events=len(resets)
            expected_intervals={str(mid):list(range(0 if mid==0 else resets[mid-1]+1,resets[mid]+1)) for mid in range(events)}
            assert binding['map_consumed_frames']=={mid:ids for mid,ids in expected_intervals.items() if ids}
            assert binding['inherited_voxel_conservative_prefixes']==[[0,i] for i in resets]
            expected_chain=hashlib.sha256()
            for i in range(n):expected_chain.update(f"{i} {f['raw_files'][str(r.raw(s,i))]}\n".encode())
            assert expected_chain.hexdigest()==binding['consumed_ordered_hash_chain']
            verts,edges,fixed=graph(p/'map_graph.g2o');assert verts==list(range(events+1)) and fixed=={0}
            expected=Counter((i,i+1) for i in range(events));accepted=[q for q in binding['loop_attempts'] if q['accepted']]
            for q in accepted:
                assert 0<=q['source']<events and 0<=q['target']<events;expected[tuple(sorted((q['source'],q['target'])))]+=1
            assert edges==expected and len(binding['loop_attempts'])==events
            anchor_ids=[0]+resets[:-1];empty_maps=[int(mid) for mid,ids in expected_intervals.items() if not ids];reconstruction=None;source_max=None;preservation=None
            if m=='G':
                anchors=d.read(p/'anchors.json');assert anchors['anchor_frames']==anchor_ids and not empty_maps
                o=np.load(p/'odometry.npy');old=r.proper(r.poses(d.old.src(s)/'odom_poses.txt'));source_max=float(np.max(abs(o-old)));assert source_max<=1e-5
                initial=np.load(p/'before_fine.npy');coarse=np.asarray(anchors['coarse_poses']);reconstruction=0.
                for mid,ids in expected_intervals.items():
                    a=anchor_ids[int(mid)];c=coarse[int(mid)];relative=np.tile(np.eye(4),(len(ids),1,1));relative[:,:3,:3]=o[a,:3,:3].T@o[ids,:3,:3];relative[:,:3,3]=(o[ids,:3,3]-o[a,:3,3])@o[a,:3,:3]
                    reconstruction=max(reconstruction,float(np.max(abs(c@relative-initial[ids]))))
                preservation=float(np.max(abs(t[anchor_ids]-coarse)));assert max(reconstruction,preservation)<=1e-8;maximum=max(maximum,reconstruction,preservation)
            else:
                dv,de,df=graph(p/'trajectory.g2o');assert dv==list(range(n)) and de==Counter((i,i+1) for i in range(n-1));assert df==({0}|{i-1 for i in resets})
            rows[key]=dict(frames=n,finalized_maps=events,direct_member_maps=len(binding['map_consumed_frames']),empty_direct_maps=empty_maps,coarse_vertices=len(verts),coarse_factors=sum(edges.values()),
                accepted_closures=len(accepted),map_source_anchors=anchor_ids,terminal_graph_only_variable=dict(id=events,source_frame=n-1,direct_frames=[]),frontend_reference_max=source_max,
                independent_body_reconstruction_max=reconstruction,anchor_preservation_max=preservation)
            d.cap()
        d.save(BASE/'binding_audit.json',dict(utc=d.now(),passed=True,cells=36,source_frame_occurrences=total_frames,maximum_rigid_reconstruction=maximum,rows=rows,
            GT_numeric_read=False,new_predictions=0,new_solver_calls=0,rounded_graph_pose_values_used=False,per_return_voxel_lineage_authenticated=False))
        print('All36 source/graph contracts pass',total_frames,maximum,flush=True);ok=True
    except BaseException as e:err=repr(e);traceback.print_exc();d.save(BASE/'FAILURE_binding_audit.json',dict(utc=d.now(),error=err))
    finally:
        signal.alarm(0);d.save(SUP/'audit_bindings/child_exit.json',dict(utc=d.now(),success=ok,error=err,wall_seconds=time.monotonic()-START,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,GPU_calls=0))
    if not ok:sys.exit(1)
if __name__=='__main__':assert sys.argv[1]=='audit_bindings';run()
