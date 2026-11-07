"""Independent scalar projection and Decimal reference metric audit."""
from decimal import Decimal,localcontext
import math
import os
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import baseline_lib as lib
import numpy as np

OUT=lib.ROOT/'audit'


def solve(left,right):
    a=[[*left[i],*right[i]] for i in range(4)]
    for col in range(4):
        pivot=max(range(col,4),key=lambda i:abs(a[i][col]));assert a[pivot][col]!=0
        a[col],a[pivot]=a[pivot],a[col];value=a[col][col];a[col]=[x/value for x in a[col]]
        for row in range(4):
            if row!=col:
                factor=a[row][col];a[row]=[x-factor*y for x,y in zip(a[row],a[col])]
    return [[float(v) for v in row[4:]] for row in a]


def metrics(rotation,translation,q):
    delta=[[sum(rotation[i][k]*q[j][k] for k in range(3)) for j in range(3)] for i in range(3)]
    sine=math.sqrt(sum(v*v for v in (delta[2][1]-delta[1][2],delta[0][2]-delta[2][0],delta[1][0]-delta[0][1])))/2
    cosine=(sum(delta[i][i] for i in range(3))-1)/2;r=math.degrees(math.atan2(sine,cosine))
    t=math.sqrt(sum((translation[i]-q[i][3])**2 for i in range(3)))
    pn=math.sqrt(sum(x*x for x in translation));rn=math.sqrt(sum(q[i][3]**2 for i in range(3)))
    d=None if min(pn,rn)<=1e-9 else math.degrees(math.acos(max(-1.,min(1.,sum(translation[i]*q[i][3] for i in range(3))/(pn*rn)))))
    return r,t,d


try:
    lib.verify_freeze('audit')
    for stage in ('controls','predict','evaluate'):lib.verify_seal(lib.ROOT/stage)
    inputs=lib.load(lib.ROOT/'PREDICTION_INPUTS.json');binding=lib.load(lib.ROOT/'EVALUATION_INPUTS.json')
    pred=lib.load(lib.ROOT/'predict/PREDICTIONS.json');rows=lib.load(lib.ROOT/'evaluate/ROWS.json')
    assert len(pred)==len(rows)==200 and [r['key'] for r in pred]==[r['key'] for r in rows]==[r['key'] for r in inputs['pairs']]
    normalize=lambda p:os.path.normcase(str(Path(p).resolve()))
    assert set(lib.load(lib.ROOT/'predict/RESULT.json')['audited_read_paths'])=={normalize(e['path']) for e in inputs['hypotheses']+inputs['calibrations']}
    begin=lib.load(lib.ROOT/'evaluate/REFERENCE_READ_BEGIN.json');sealed=lib.load(lib.ROOT/'predict/SEAL.json')
    assert begin['utc']>sealed['sealed_utc']>lib.load(lib.ROOT/'predict/RESULT.json')['completed_utc']
    assert begin['prediction_seal_sha256']==lib.sha(lib.ROOT/'predict/SEAL.json')
    cameras={e['sequence']:lib.camera(np,e['path']) for e in inputs['calibrations']}
    projection_checks=0;threshold_ambiguous=0;max_projection_delta=0.
    for record,item in zip(pred,inputs['hypotheses']):
        assert lib.sha(item['path'])==item['sha256']
        with np.load(item['path'],allow_pickle=False) as data:xyz=data['unique_camera_xyz'];xy=data['unique_target_xy']
        with np.load(lib.ROOT/'predict'/record['evidence'],allow_pickle=False) as data:
            native=data['native_mask'];verified=data['verified_mask'];projected=data['projected_xy'];depth=data['target_depth'];residual=data['residual_px'];rvec=data['rvec'];tvec=data['tvec']
        assert len(xyz)==record['input_hypotheses'] and native.shape==verified.shape==(len(xyz),)
        assert int(native.sum())==record['native_inliers'] and int(verified.sum())==record['verified_inliers'] and np.all(verified<=native)
        if record['status']!='POSE':
            assert record['R_i_to_j'] is None and record['t_i_to_j_m'] is None;continue
        rotation=record['R_i_to_j'];translation=record['t_i_to_j_m'];k=cameras[record['sequence']]
        rr=np.asarray(rotation);assert np.max(np.abs(rr.T@rr-np.eye(3)))<1e-6 and abs(np.linalg.det(rr)-1)<1e-6
        assert record['verified_inliers']>=8 and np.array_equal(tvec,np.asarray(translation))
        angle=math.sqrt(sum(float(v)**2 for v in rvec))
        if angle>1e-12:
            x,y,z=[float(v)/angle for v in rvec];c,s=math.cos(angle),math.sin(angle)
            scalar=np.asarray([[c+x*x*(1-c),x*y*(1-c)-z*s,x*z*(1-c)+y*s],
                [y*x*(1-c)+z*s,c+y*y*(1-c),y*z*(1-c)-x*s],[z*x*(1-c)-y*s,z*y*(1-c)+x*s,c+z*z*(1-c)]])
            assert np.max(np.abs(scalar-rr))<1e-10
        for n,(point,target) in enumerate(zip(xyz,xy)):
            camera=[math.fsum(rotation[i][j]*float(point[j]) for j in range(3))+translation[i] for i in range(3)]
            assert abs(camera[2]-depth[n])<1e-9*max(1.,abs(camera[2]))
            expected=False
            if camera[2]>0:
                image=[math.fsum(float(k[i,j])*camera[j] for j in range(3)) for i in range(3)]
                uv=[image[i]/image[2] for i in range(2)];error=math.hypot(uv[0]-float(target[0]),uv[1]-float(target[1]))
                difference=max(abs(uv[i]-projected[n,i]) for i in range(2));max_projection_delta=max(max_projection_delta,difference)
                assert difference<1e-7 and abs(error-residual[n])<1e-7
                expected=bool(native[n] and error<=2)
                if abs(error-2)<1e-8:threshold_ambiguous+=1
                else:assert bool(verified[n])==expected
            else:assert not verified[n]
            projection_checks+=1
    decimal={}
    for item in binding['poses']:
        assert lib.sha(item['path'])==item['sha256']
        decimal[item['sequence']]=[[Decimal(v) for v in line.split()] for line in Path(item['path']).read_text().splitlines()]
    def matrix(seq,frame):
        row=decimal[seq][int(frame)];return [row[:4],row[4:8],row[8:12],[Decimal(0),Decimal(0),Decimal(0),Decimal(1)]]
    maxima={'Q':0.,'R':0.,'t':0.,'direction':0.}
    with localcontext() as context:
        context.prec=60
        for record,row in zip(pred,rows):
            q=solve(matrix(record['sequence'],record['source_j']),matrix(record['sequence'],record['source_i']))
            delta=max(abs(q[i][j]-row['reference_Q_i_to_j'][i][j]) for i in range(4) for j in range(4));maxima['Q']=max(maxima['Q'],delta);assert delta<5e-11
            if record['status']=='POSE':
                r,t,d=metrics(record['R_i_to_j'],record['t_i_to_j_m'],q)
                maxima['R']=max(maxima['R'],abs(r-row['rotation_error_deg']));maxima['t']=max(maxima['t'],abs(t-row['translation_error_m']))
                assert abs(r-row['rotation_error_deg'])<1e-6 and abs(t-row['translation_error_m'])<1e-8
                if d is None:assert row['direction_error_deg'] is None
                else:maxima['direction']=max(maxima['direction'],abs(d-row['direction_error_deg']));assert abs(d-row['direction_error_deg'])<1e-6
            else:assert row['rotation_error_deg'] is None and row['translation_error_m'] is None and row['direction_error_deg'] is None
    groups=lib.load(lib.ROOT/'evaluate/SUMMARY.json')['groups']
    for group in groups:
        if group['group']=='all200':data=rows
        else:
            seq,name=group['group'].split('/');data=[r for r in rows if r['sequence']==seq]
            if name=='positive75':data=[r for r in data if r['stratum']!='confuser']
            elif name=='confuser25':data=[r for r in data if r['stratum']=='confuser']
            elif name!='all100':data=[r for r in data if r['stratum']==name]
        valid=[r for r in data if r['status']=='POSE'];assert group['pairs']==group['bin_denominator_all_pairs']==len(data) and group['pose_outputs']==len(valid)
        for key,rlim,tlim,dlim in [('R5_t2',5,2,None),('R10_t5',10,5,None),('R5_d15',5,None,15),('R10_d30',10,None,30)]:
            count=sum(r['rotation_error_deg']<=rlim and (tlim is None or r['translation_error_m']<=tlim) and (dlim is None or (r['direction_error_deg'] is not None and r['direction_error_deg']<=dlim)) for r in valid)
            assert group['bin_counts'][key]==count
    lib.complete(OUT,{'complete_pairs':200,'Decimal60_reference_solves':200,'scalar_projection_checks':projection_checks,
        'threshold_boundary_ambiguous':threshold_ambiguous,'max_projection_delta_px':max_projection_delta,'maximum_metric_differences':maxima,
        'summary_groups':len(groups),'prediction_reference_separation_verified':True})
    print('PR1 independent complete audit PASS')
except BaseException as error:
    lib.failure(OUT,error);raise
