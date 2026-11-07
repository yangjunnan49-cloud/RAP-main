"""Complete200-pair source-depth adequacy; no new feature or pose solver."""
import codecs
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import baseline_lib as lib
import geometry

OUT=lib.ROOT/'features'
try:
    lib.verify_freeze('prediction')
    lib.verify_seal(lib.ROOT/'controls')
    binding=lib.load(lib.ROOT/'INPUT_BINDING.json')
    _,np=lib.runtime()
    import numpy.ma
    for codec in ('ascii','cp437','utf-8','latin-1'):
        codecs.lookup(codec)
    allowed=[e['path'] for e in binding['raw']+binding['calibrations']+binding['evidence']]
    lib.read_gate(allowed,OUT)
    cameras={}
    for e in binding['calibrations']:
        assert lib.sha(e['path'])==e['sha256']
        rows={}
        for line in Path(e['path']).read_text(encoding='ascii').splitlines():
            key,value=line.split(':',1);rows[key]=np.asarray([float(x) for x in value.split()])
        tr=np.eye(4);tr[:3]=rows['Tr'].reshape(3,4)
        assert np.max(np.abs(tr[:3,:3].T@tr[:3,:3]-np.eye(3)))<1e-5
        cameras[e['sequence']]=(tr,rows['P0'].reshape(3,4)[:,:3])
    raw={(e['sequence'],e['frame']):e for e in binding['raw']}
    evidence={e['key']:e for e in binding['evidence']}
    dims={(e['sequence'],e['frame']):(e['width'],e['height']) for e in binding['images']}
    output=[];dense_checks=0;raw_reads=0
    for pair in binding['pairs']:
        e=evidence[pair['key']]
        assert lib.sha(e['path'])==e['sha256']
        with np.load(e['path'],allow_pickle=False) as z:
            first,second=z['first'],z['second']
        n=len(first);assigned=np.full(n,-1,dtype=np.int64);distance=np.full(n,np.inf);unique=np.empty(0,dtype=np.int64)
        camera=np.empty((0,3));index=np.empty(0,dtype=np.int64);projected=0;raw_count=None;rank=0;singular=[]
        if n:
            source=raw[(pair['sequence'],pair['source_i'].zfill(6))]
            payload=Path(source['path']).read_bytes()
            assert len(payload)==source['bytes'] and lib.hashlib.sha256(payload).hexdigest()==source['sha256']
            scans=np.frombuffer(payload,dtype='<f4').reshape(-1,4);raw_count=len(scans);raw_reads+=1
            tr,k=cameras[pair['sequence']]
            uv,camera,index,grid=geometry.project(np,scans[:,:3].astype(np.float64),tr,k,*dims[(pair['sequence'],pair['source_i'].zfill(6))])
            projected=len(uv)
            assigned,distance,unique=geometry.associate(np,first,uv,camera,index,grid)
            selected=list(range(n)) if n<=8 else sorted({i*(n-1)//7 for i in range(8)})
            for q in selected:
                assert int(assigned[q])==geometry.dense(np,first[q],uv,camera,index)
                dense_checks+=1
        positions=assigned[unique]
        points=camera[positions] if len(unique) else np.empty((0,3))
        if len(points):
            centered=points-points.mean(axis=0)
            rank=int(np.linalg.matrix_rank(centered));singular=np.linalg.svd(centered,compute_uv=False).tolist()
        with (OUT/(pair['key']+'.npz')).open('xb') as f:
            np.savez(f,source_xy=first,target_xy=second,assigned_raw_indices=np.where(assigned>=0,index[np.maximum(assigned,0)] if len(index) else -1,-1),squared_pixel_distance=distance,
                unique_match_indices=unique,unique_camera_xyz=points,unique_target_xy=second[unique])
        output.append({**pair,'SIFT_matches':n,'source_scan_points':raw_count,'source_zbuffer_points':projected,
            'associated_matches':int(np.count_nonzero(assigned>=0)),'unique_associated_points':len(unique),
            'centered_rank':rank,'singular_values':singular,'at_least8_unique_depth_hypotheses':len(unique)>=8,
            'status':'ASSOCIATION_HYPOTHESES_ONLY' if len(unique) else ('NO_SIFT_MATCHES_NOT_QUERIED' if not n else 'NO_WITHIN_RADIUS_SOURCE_ASSOCIATION')})
    summaries=[]
    for name,data in [('all200',output),('00',[r for r in output if r['sequence']=='00']),('08',[r for r in output if r['sequence']=='08'])]:
        summaries.append({'group':name,'pairs':len(data),'pairs_any_hypothesis':sum(r['unique_associated_points']>0 for r in data),
            'pairs_at_least8':sum(r['at_least8_unique_depth_hypotheses'] for r in data),
            'pairs_at_least8_rank3':sum(r['at_least8_unique_depth_hypotheses'] and r['centered_rank']==3 for r in data),
            'pairs_at_least8_rank2':sum(r['at_least8_unique_depth_hypotheses'] and r['centered_rank']==2 for r in data)})
    lib.save(OUT/'ROWS.json',output);lib.save(OUT/'SUMMARY.json',{'groups':summaries,'role':'Source proximity hypotheses; no actual correspondence/pose accuracy or PnP admission'})
    lib.complete(OUT,{'complete_pairs':200,'independent_dense_query_checks':dense_checks,'raw_scan_occurrence_reads':raw_reads,'pose_solver_calls':0,'reference_pose_reads':0})
    print('SD1 complete200 pairs; no pose solver')
except BaseException as e:
    lib.failure(OUT,e)
    raise
