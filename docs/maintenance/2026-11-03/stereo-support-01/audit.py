"""Rebuild every support decision with scalar sampling and 2x2 covariance algebra."""
import sys,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
out=Path(sys.argv[1]);rows=read(ROOT/'packet/ROWS.json');maps=read(ROOT/'packet/MAP_INDEX.json');right=read(METHOD['right_manifest'])
allowed=[ROOT/'packet/ROWS.json',ROOT/'packet/MAP_INDEX.json',METHOD['right_manifest']]+[r['path'] for r in maps]+[r['path'] for r in rows]
gate(allowed,out);lease(out,True)
map_by={(r['sequence'],r['frame']):r for r in maps}
cameras={}
for c in right['calibration']:
    p=c['P0'];cameras[c['sequence']]=(p[0],p[5],p[2],p[6],c['baseline_m'])
checks=0;cov_checks=0;max_xyz=0.;max_cov=0.
def scalar(dl,dr,uv,camera):
    u,v=map(float,uv);x=math.floor(u+.5);y=math.floor(v+.5)
    h,w=dl.shape;d=rd=error=float('nan')
    if not (0<=x<w and 0<=y<h):return False,(d,rd,error),(d,rd,error)
    d=int(dl[y,x])/16.;xr=math.floor(x-d+.5)
    if not (.5<=d<127 and 0<=xr<w):return False,(d,rd,error),(float('nan'),)*3
    rd=int(dr[y,xr])/16.;error=abs(d-rd)
    if not (.5<=rd<127 and error<=1):return False,(d,rd,error),(float('nan'),)*3
    fx,fy,cx,cy,base=camera;z=fx*base/d
    return True,(d,rd,error),((u-cx)*z/fx,(v-cy)*z/fy,z)
def covariance(points):
    if len(points)<2:return 0.
    n=len(points);mx=math.fsum(float(p[0]) for p in points)/n;my=math.fsum(float(p[1]) for p in points)/n
    a=math.fsum((float(p[0])-mx)**2 for p in points)/n
    c=math.fsum((float(p[1])-my)**2 for p in points)/n
    b=math.fsum((float(p[0])-mx)*(float(p[1])-my) for p in points)/n
    return (a+c-math.hypot(a-c,2*b))/2
for row in rows:
    lease(out);assert sha(row['path'])==row['sha256']
    with np.load(row['path'],allow_pickle=False) as z:stored={k:z[k] for k in z.files}
    reconstructed=[]
    for side,frame in (('source',row['source_i']),('target',row['source_j'])):
        entry=map_by[(row['sequence'],int(frame))];assert sha(entry['path'])==entry['sha256']
        with np.load(entry['path'],allow_pickle=False) as z:dl=z['left'];dr=z['right']
        actual=[]
        for k,uv in enumerate(stored[side+'_xy']):
            okay,detail,xyz=scalar(dl,dr,uv,cameras[row['sequence']]);checks+=1;actual.append(okay)
            assert okay==bool(stored[side+'_valid'][k])
            assert np.allclose(detail,stored[side+'_detail'][k],atol=0,rtol=0,equal_nan=True)
            assert np.allclose(xyz,stored[side+'_xyz'][k],atol=1e-12,rtol=1e-12,equal_nan=True)
            if okay:max_xyz=max(max_xyz,max(abs(float(x)-float(y)) for x,y in zip(xyz,stored[side+'_xyz'][k])))
        reconstructed.append(actual)
    joint=[a and b for a,b in zip(*reconstructed)]
    assert joint==stored['joint'].tolist() and sum(joint)==row['joint_valid']
    cv=[covariance(stored[s+'_xy'][joint]) for s in ('source','target')]
    for a,b in zip(cv,row['covariance_minimum_eigenvalues']):
        max_cov=max(max_cov,abs(a-b));assert abs(a-b)<1e-7;cov_checks+=1
    eligible=sum(joint)>=4 and min(cv)>=4
    assert eligible==row['eligible']
complete(out,complete_pair_supports=200,scalar_disparity_sample_checks=checks,independent_covariance_checks=cov_checks,max_xyz_delta=max_xyz,max_covariance_eigenvalue_delta=max_cov,all_eligibility_decisions_reproduced=True,SGBM_independently_reimplemented=False,reference_pose_reads=0)
