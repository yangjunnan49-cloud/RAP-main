"""Complete all273 stereo depth maps and all200 unchanged hypothesis supports."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
import measurement as m
out=Path(sys.argv[1]);right=read(METHOD['right_manifest']);binding=read(METHOD['crossvisit_binding'])
lefts={}
for row in right['rows']:
    left_path=str(Path(METHOD['left_image_root'])/row['left_image_identity']['relative_path'])
    lefts[(row['sequence'],row['frame'])]=left_path
allowed=[METHOD['right_manifest'],METHOD['crossvisit_binding']]+[r['path'] for r in right['rows']]+list(lefts.values())+[h['path'] for h in binding['hypotheses']]
gate(allowed,out);lease(out,True)
assert len(right['rows'])==273 and len(binding['pairs'])==200
cal={}
for c in right['calibration']:
    p=np.array(c['P0']).reshape(3,4)
    cal[c['sequence']]=(p[0,0],p[1,1],p[0,2],p[1,2],c['baseline_m'])
mapsdir=out/'maps';mapsdir.mkdir();maps={};map_index=[];algo=m.engine()
for row in right['rows']:
    lease(out)
    left_path=Path(lefts[(row['sequence'],row['frame'])]);rp=Path(row['path'])
    assert sha(left_path)==row['left_image_identity']['sha256'] and sha(rp)==row['sha256']
    left=cv2.imdecode(np.frombuffer(left_path.read_bytes(),np.uint8),cv2.IMREAD_GRAYSCALE)
    right_image=cv2.imdecode(np.frombuffer(rp.read_bytes(),np.uint8),cv2.IMREAD_GRAYSCALE)
    assert left.shape==right_image.shape==(row['height'],row['width'])
    dl=algo.compute(left,right_image)
    lease(out)
    dr=np.ascontiguousarray(np.fliplr(algo.compute(np.ascontiguousarray(np.fliplr(right_image)),np.ascontiguousarray(np.fliplr(left)))))
    dest=mapsdir/f'{row["sequence"]}_{row["frame"]:06d}.npz'
    np.savez_compressed(dest,left=dl,right=dr)
    maps[(row['sequence'],row['frame'])]=dest
    map_index.append(dict(sequence=row['sequence'],frame=row['frame'],path=str(dest),sha256=sha(dest),left_sha256=row['left_image_identity']['sha256'],right_sha256=row['sha256']))
    if len(map_index)%50==0:print(f'depth maps {len(map_index)}/273',flush=True)
hyp={h['key']:h for h in binding['hypotheses']};rows=[];pairdir=out/'pairs';pairdir.mkdir()
for pair in binding['pairs']:
    lease(out)
    e=hyp[pair['key']];assert sha(e['path'])==e['sha256']
    with np.load(e['path'],allow_pickle=False) as z:source=z['source_xy'];target=z['target_xy']
    with np.load(maps[(pair['sequence'],int(pair['source_i']))],allow_pickle=False) as z:a=m.sample(z['left'],z['right'],source,cal[pair['sequence']])
    with np.load(maps[(pair['sequence'],int(pair['source_j']))],allow_pickle=False) as z:b=m.sample(z['left'],z['right'],target,cal[pair['sequence']])
    joint=a[0]&b[0];count=int(joint.sum());covs=[m.min_covariance(q[joint]) for q in (source,target)]
    eligible=count>=METHOD['minimum_joint_matches'] and min(covs)>=METHOD['minimum_image_covariance_eigenvalue_px2']
    dest=pairdir/(pair['key']+'.npz')
    np.savez_compressed(dest,source_xy=source,target_xy=target,source_valid=a[0],target_valid=b[0],joint=joint,source_detail=a[1],target_detail=b[1],source_xyz=a[2],target_xyz=b[2])
    rows.append(dict(**pair,SIFT_hypotheses=len(source),source_valid=int(a[0].sum()),target_valid=int(b[0].sum()),joint_valid=count,covariance_minimum_eigenvalues=covs,eligible=bool(eligible),path=str(dest),sha256=sha(dest),physical_identity='UNVERIFIED'))
save(out/'MAP_INDEX.json',map_index);save(out/'ROWS.json',rows)
complete(out,complete_scans=273,complete_pairs=200,depth_calls=546,new_features=0,new_poses=0,total_joint_valid_matches=sum(r['joint_valid'] for r in rows),eligible_pairs=sum(r['eligible'] for r in rows),candidate_scores=0,reference_pose_reads=0)
