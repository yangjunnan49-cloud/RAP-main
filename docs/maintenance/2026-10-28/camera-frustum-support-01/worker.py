import hashlib,json,time
from decimal import Decimal,localcontext
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parent;START=time.monotonic()
def check():assert time.monotonic()-START<290,'Worker deadline'
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1024**2),b''):h.update(block)
    return h.hexdigest()
def save(n,o):
    with (ROOT/n).open('x',encoding='utf-8') as f:json.dump(o,f,indent=2,allow_nan=False)
def planes(k,w,h,margin):
    assert np.array_equal(k[2],[0.,0.,1.]);z=np.array([0.,0.,1.]);lo=-margin;hiX=w-1+margin;hiY=h-1+margin
    return np.column_stack((np.array([z,k[0]-lo*z,hiX*z-k[0],k[1]-lo*z,hiY*z-k[1]]),np.zeros(5)))
def evaluate(xyz,tr,q,k,source_shape,target_shape,margin):
    x=np.column_stack((xyz,np.ones(len(xyz))));a=planes(k,*source_shape,margin);b=planes(k,*target_shape,margin);ca=a@tr;cb=b@q@tr
    v=x@ca.T;u=x@cb.T;camera=x@tr.T;target=camera@q.T;vd=camera@a.T;ud=target@b.T
    eps=np.finfo(np.float64).eps*512;ga=eps*(np.abs(x)@(np.abs(a)@np.abs(tr)).T+1);gb=eps*(np.abs(x)@(np.abs(b)@np.abs(q)@np.abs(tr)).T+1)
    assert np.all(np.abs(v-vd)<=ga) and np.all(np.abs(u-ud)<=gb)
    nominal=(v[:,0]>0)&(u[:,0]>0)&np.all(v[:,1:]>=0,axis=1)&np.all(u[:,1:]>=0,axis=1)
    direct=(vd[:,0]>0)&(ud[:,0]>0)&np.all(vd[:,1:]>=0,axis=1)&np.all(ud[:,1:]>=0,axis=1)
    lower=np.all(v>ga,axis=1)&np.all(u>gb,axis=1);upper=np.all(v>=-ga,axis=1)&np.all(u>=-gb,axis=1);near=np.any(np.abs(v)<=ga,axis=1)|np.any(np.abs(u)<=gb,axis=1)
    assert not np.any((nominal!=direct)&~near);assert int(lower.sum())<=int(nominal.sum())<=int(upper.sum())
    return {'v':v,'u':u,'ca':ca,'cb':cb,'ga':ga,'gb':gb,'lower':int(lower.sum()),'upper':int(upper.sum()),'nominal':int(nominal.sum()),'near':int(near.sum()),'disagreements':int((nominal!=direct).sum()),'positive_depth':int(((camera[:,2]>0)&(target[:,2]>0)).sum())}

rows=[]
try:
    freeze=json.loads((ROOT/'SOURCE_FREEZE.json').read_text(encoding='utf-8-sig'))
    for n,h in freeze['files'].items():assert sha(ROOT/n)==h.lower()
    b=json.loads((ROOT/'INPUT_BINDING.json').read_text(encoding='utf-8-sig'))
    for p,h in [(b['cohort_path'],b['cohort_sha256']),(b['prior_depth_rows_path'],b['prior_depth_rows_sha256']),(b['image_manifest_path'],b['image_manifest_sha256']),(b['measured_image_results_path'],b['measured_image_results_sha256'])]:assert sha(Path(p))==h
    for item in b['raw']+b['calibrations']+b['poses']:
        assert Path(item['path']).stat().st_size==item['bytes'] and sha(Path(item['path']))==item['sha256'];check()
    identity=np.eye(4);k=np.eye(3);fixture=np.array([[1.,1.,1.],[-.25,1.,1.],[2.25,1.,1.],[3.,1.,1.],[1.,1.,-1.],[0.,0.,0.]])
    c=evaluate(fixture,identity,identity,k,(3,3),(3,3),0);o=evaluate(fixture,identity,identity,k,(3,3),(3,3),.5);tests=[c['nominal']==1,o['nominal']==3,c['nominal']<=o['nominal']]
    q=identity.copy();q[0,3]=2;point=np.array([[0.,1.,1.]])
    tests+=[evaluate(point,identity,q,k,(3,3),(3,3),0)['nominal']==1,evaluate(point,identity,np.linalg.inv(q),k,(3,3),(3,3),0)['nominal']==0];assert all(tests)
    save('CONTROL_RESULTS.json',{'passed':True,'controls':len(tests),'real_numeric_decodes_before_controls':False,'numpy_version':np.__version__})
    cohort=json.loads(Path(b['cohort_path']).read_text());images=json.loads(Path(b['image_manifest_path']).read_text());measured=json.loads(Path(b['measured_image_results_path']).read_text());assert measured['passed'] and len(images['rows'])==273
    assert all(a['projection_entries_equal'] and a['timestamp_bytes_equal'] for a in measured['associations'])
    dims={(r['sequence'],Path(r['member']).stem):(r['width'],r['height']) for r in images['rows']};rawmap={(r['sequence'],r['frame']):Path(r['path']) for r in b['raw']};prior={(r['key'],r['direction']):r for r in json.loads(Path(b['prior_depth_rows_path']).read_text())}
    calibrations={};poses={}
    for item in b['calibrations']:
        data={}
        for line in Path(item['path']).read_text().splitlines():
            key,value=line.split(':',1);data[key]=np.array([float(s) for s in value.split()])
        tr=np.eye(4);tr[:3]=data['Tr'].reshape(3,4);p0=data['P0'].reshape(3,4);assert np.array_equal(p0[:,3],np.zeros(3));calibrations[item['sequence']]=(tr,p0[:,:3])
    for item in b['poses']:
        data=np.loadtxt(item['path']);assert data.shape[1]==12 and np.isfinite(data).all();table=np.tile(np.eye(4),(len(data),1,1));table[:,:3]=data.reshape(-1,3,4);poses[item['sequence']]=table
    decimal_checks=0;max_delta=Decimal(0)
    for pair in cohort['pairs']:
        seq=pair['sequence'];tr,k=calibrations[seq]
        for a,c,direction in [('source_i','source_j','i_to_j'),('source_j','source_i','j_to_i')]:
            si=pair[a].zfill(6);ti=pair[c].zfill(6);q=np.linalg.solve(poses[seq][int(ti)],poses[seq][int(si)]);path=rawmap[(seq,si)];raw=np.fromfile(path,dtype='<f4').reshape(-1,4);xyz=raw[:,:3].astype(np.float64);assert np.isfinite(xyz).all()
            inner=evaluate(xyz,tr,q,k,dims[(seq,si)],dims[(seq,ti)],0);outer=evaluate(xyz,tr,q,k,dims[(seq,si)],dims[(seq,ti)],.5);old=prior[(pair['key'],direction)]
            assert len(xyz)==old['point_occurrences'] and outer['positive_depth']==old['joint_positive_route1'];assert inner['nominal']<=outer['upper']<=old['numerical_upper_count']
            indices=sorted({i*(len(xyz)-1)//3 for i in range(4)})
            with localcontext() as context:
                context.prec=60
                for index in indices:
                    point=[Decimal.from_float(float(v)) for v in xyz[index]]+[Decimal(1)]
                    for coeffs,values,guards in [(outer['ca'],outer['v'],outer['ga']),(outer['cb'],outer['u'],outer['gb'])]:
                        for n in range(5):
                            exact=sum((Decimal.from_float(float(z))*v for z,v in zip(coeffs[n],point)),Decimal(0));delta=abs(exact-Decimal.from_float(float(values[index,n])));assert delta<=Decimal.from_float(float(guards[index,n]));max_delta=max(max_delta,delta);decimal_checks+=1
            rows.append({'key':pair['key'],'sequence':seq,'direction':direction,'source_frame':si,'target_frame':ti,'point_occurrences':len(xyz),'positive_depth':outer['positive_depth'],'center_domain_joint':inner['nominal'],'half_pixel_edge_nominal':outer['nominal'],'half_pixel_edge_lower':outer['lower'],'half_pixel_edge_upper':outer['upper'],'near_plane_occurrences':outer['near'],'route_sign_disagreements':outer['disagreements'],'fraction_of_source_upper':outer['upper']/len(xyz),'source_dimensions':dims[(seq,si)],'target_dimensions':dims[(seq,ti)]});check()
    assert len(rows)==400 and len({(r['key'],r['direction']) for r in rows})==400
    summaries=[]
    for seq in ['00','08']:
        data=[r for r in rows if r['sequence']==seq];bykey={}
        for r in data:bykey.setdefault(r['key'],[]).append(r)
        summaries.append({'sequence':seq,'pairs':len(bykey),'directions':len(data),'point_occurrences':sum(r['point_occurrences'] for r in data),'center_domain_joint':sum(r['center_domain_joint'] for r in data),'half_pixel_edge_upper_occurrences':sum(r['half_pixel_edge_upper'] for r in data),'zero_upper_directions':sum(r['half_pixel_edge_upper']==0 for r in data),'both_zero_upper_pairs':sum(all(r['half_pixel_edge_upper']==0 for r in group) for group in bykey.values()),'upper_fraction_median':float(np.median([r['fraction_of_source_upper'] for r in data]))})
    save('ROWS.json',rows);save('RESULTS.json',{'passed':True,'complete_pairs':200,'directions':400,'point_occurrences':sum(r['point_occurrences'] for r in rows),'summaries':summaries,'Decimal_scalar_checks':decimal_checks,'max_Decimal_affine_delta':str(max_delta),'all_independent_route_checks_pass':True,'actual_image_pixel_or_correspondence_work':False,'pose_accuracy_or_candidate_selection':False,'elapsed_seconds':time.monotonic()-START});print(json.dumps({'passed':True,'directions':400,'summaries':summaries,'elapsed_seconds':time.monotonic()-START}))
except BaseException as e:
    save('FAILURE.json',{'error':repr(e),'completed_directions':len(rows),'elapsed_seconds':time.monotonic()-START});raise
