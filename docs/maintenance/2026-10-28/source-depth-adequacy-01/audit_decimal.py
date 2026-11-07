"""Saved source identity and independent Decimal affine/projection audit."""
import codecs
from decimal import Decimal,localcontext
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import baseline_lib as lib

OUT=lib.ROOT/'audit'
try:
    for item in lib.load(lib.ROOT/'AUDIT_FREEZE.json')['files']:
        assert lib.sha(lib.ROOT/item['path'])==item['sha256']
    lib.verify_seal(lib.ROOT/'features')
    binding=lib.load(lib.ROOT/'INPUT_BINDING.json');rows=lib.load(lib.ROOT/'features/ROWS.json')
    _,np=lib.runtime()
    import numpy.ma
    for codec in ('ascii','cp437','utf-8','latin-1'):codecs.lookup(codec)
    fixtures=[(np.zeros((4,3)),0),(np.array([[0.,0.,0.],[1.,0.,0.],[2.,0.,0.]]),1),
        (np.array([[0.,0.,0.],[1.,0.,0.],[0.,1.,0.]]),2),(np.array([[0.,0.,0.],[1.,0.,0.],[0.,1.,0.],[0.,0.,1.]]),3)]
    assert all(int(np.linalg.matrix_rank(a-a.mean(axis=0)))==rank for a,rank in fixtures)
    paths=[e['path'] for e in binding['raw']+binding['calibrations']]+[str(lib.ROOT/'features'/(p['key']+'.npz')) for p in binding['pairs']]
    lib.read_gate(paths,OUT)
    calibrations={}
    for e in binding['calibrations']:
        assert lib.sha(e['path'])==e['sha256'];values={}
        for line in Path(e['path']).read_text(encoding='ascii').splitlines():
            key,value=line.split(':',1);values[key]=[Decimal.from_float(float(v)) for v in value.split()]
        calibrations[e['sequence']]=values
    raw={(e['sequence'],e['frame']):e for e in binding['raw']};point_checks=0;scalar_checks=0;max_delta=0.;projection_checks=0
    with localcontext() as context:
        context.prec=60
        for row in rows:
            with np.load(lib.ROOT/'features'/(row['key']+'.npz'),allow_pickle=False) as z:
                selected=z['unique_match_indices'];ids=z['assigned_raw_indices'][selected];points=z['unique_camera_xyz'];source_xy=z['source_xy'][selected];squared=z['squared_pixel_distance'][selected]
            assert len(ids)==len(set(map(int,ids)))==row['unique_associated_points']==len(points)
            if not len(ids):continue
            item=raw[(row['sequence'],row['source_i'].zfill(6))];payload=Path(item['path']).read_bytes()
            assert lib.hashlib.sha256(payload).hexdigest()==item['sha256'];table=np.frombuffer(payload,dtype='<f4').reshape(-1,4)
            c=calibrations[row['sequence']];tr=[c['Tr'][i*4:(i+1)*4] for i in range(3)];p0=[c['P0'][i*4:i*4+3] for i in range(3)]
            for raw_id,actual,query,stored_distance in zip(ids,points,source_xy,squared):
                xyz=[Decimal.from_float(float(v)) for v in table[int(raw_id),:3]]+[Decimal(1)]
                exact=[sum(a*b for a,b in zip(line,xyz)) for line in tr]
                for n in range(3):
                    delta=abs(exact[n]-Decimal.from_float(float(actual[n])))
                    guard=Decimal.from_float(512*np.finfo(float).eps)*(sum(abs(a*b) for a,b in zip(tr[n],xyz))+1)
                    assert delta<=guard;max_delta=max(max_delta,float(delta));scalar_checks+=1
                assert exact[2]>0
                image=[sum(a*b for a,b in zip(line,exact)) for line in p0]
                uv=[image[0]/image[2],image[1]/image[2]]
                distance=sum((u-Decimal.from_float(float(q)))**2 for u,q in zip(uv,query))
                assert distance<=Decimal('4.00000001') and abs(distance-Decimal.from_float(float(stored_distance)))<Decimal('0.00000001')
                point_checks+=1;projection_checks+=1
    lib.complete(OUT,{'complete_pairs':200,'unique_raw_point_identity_checks':point_checks,'Decimal60_affine_scalar_checks':scalar_checks,
        'Decimal60_radius_projection_checks':projection_checks,'max_affine_absolute_difference':max_delta,
        'rank_fixtures':4,'rank_fixture_timing':'Added in audit after primary association, prospective rank-control requirement omitted; deviation retained',
        'pose_solver_calls':0,'reference_pose_reads':0})
    print('SD1 independent source identity/Decimal audit PASS')
except BaseException as e:
    lib.failure(OUT,e)
    raise
