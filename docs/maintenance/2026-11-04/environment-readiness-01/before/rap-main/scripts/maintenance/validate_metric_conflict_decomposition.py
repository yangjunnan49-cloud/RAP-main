"""Independent MDC0 full-pose error solves and Horn-alignment validation."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,resource,time,traceback
import numpy as np
MAIN=Path(__file__).resolve().parents[2];DATA=MAIN.parent/'Datasets/data_odometry_velodyne/dataset'
BASE=MAIN/'docs/maintenance/2026-10-07/metric-conflict-decomposition-01';OUT=BASE/'output';LC=MAIN/'docs/maintenance/2026-10-07/retrieval-placement-audit-01'
SEQS=['00','05','06','07','09','10'];ARMS=['N','C','P','H']
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):
    with p.open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
def utc():return datetime.now(timezone.utc).isoformat()
def load(p):
    with np.load(p,allow_pickle=False) as z:return {k:z[k] for k in z.files}
def pose(p):
    x=np.loadtxt(p).reshape(-1,3,4);t=np.repeat(np.eye(4)[None],len(x),0);t[:,:3]=x;return t
def verify():
    f=read(BASE/'freeze.json');seal=read(BASE/'output_seal.json')
    for p,h in f['files'].items():assert sha(Path(p))==h,p
    assert seal['freeze_sha256']==sha(BASE/'freeze.json') and seal['results_sha256']==sha(BASE/'results.json')
    assert set(seal['files'])=={p.name for p in OUT.iterdir()}
    for p,h in seal['files'].items():assert sha(OUT/p)==h,p
def horn(g,e):
    x=e[:,:3,3];y=g[:,:3,3];xc=x-x.mean(0);yc=y-y.mean(0);m=xc.T@yc
    n=np.array([[np.trace(m),m[1,2]-m[2,1],m[2,0]-m[0,2],m[0,1]-m[1,0]],
      [m[1,2]-m[2,1],m[0,0]-m[1,1]-m[2,2],m[0,1]+m[1,0],m[0,2]+m[2,0]],
      [m[2,0]-m[0,2],m[0,1]+m[1,0],-m[0,0]+m[1,1]-m[2,2],m[1,2]+m[2,1]],
      [m[0,1]-m[1,0],m[0,2]+m[2,0],m[1,2]+m[2,1],-m[0,0]-m[1,1]+m[2,2]]])
    _,v=np.linalg.eigh(n);w,a,b,c=v[:,-1]
    r=np.array([[1-2*(b*b+c*c),2*(a*b-w*c),2*(a*c+w*b)],
      [2*(a*b+w*c),1-2*(a*a+c*c),2*(b*c-w*a)],
      [2*(a*c-w*b),2*(b*c+w*a),1-2*(a*a+b*b)]])
    q=np.eye(4);q[:3,:3]=r;q[:3,3]=y.mean(0)-r@x.mean(0);return q
def independent(g,e,first,last,length):
    u=[];v=[];z=[]
    for a,b,l in zip(first,last,length):
        dg=np.linalg.solve(g[a],g[b]);de=np.linalg.solve(e[a],e[b]);error=np.linalg.solve(de,dg)[:3,3]/l
        chord=(g[b,:3,3]-g[a,:3,3])-(e[b,:3,3]-e[a,:3,3]);vc=np.linalg.solve(e[b,:3,:3],chord)/l
        z.append(error);v.append(vc);u.append(error-vc)
    return dict(u=np.array(u),v=np.array(v),z=np.array(z))
def statistics(d):
    u,v,z=d['u'],d['v'],d['z']
    return dict(ter=float(np.mean([np.sqrt(np.dot(t,t)) for t in z])*100),orientation_squared_pct=float(np.mean([np.dot(t,t) for t in u])*10000),chord_squared_pct=float(np.mean([np.dot(t,t) for t in v])*10000),cross_squared_pct=float(np.mean([2*np.dot(a,b) for a,b in zip(u,v)])*10000),total_squared_pct=float(np.mean([np.dot(t,t) for t in z])*10000),segments=len(z))
def main():
    start=time.perf_counter();verify();r=read(BASE/'results.json');lcr=read(LC/'results.json');actual={};maxvector=0.;maxalign=0.;maxsummary=0.;records=0
    for name in ['perfect','chord','orientation','global_gauge']:
        saved=load(OUT/f'fixture-{name}.npz');d=independent(saved['g'],saved['e'],[0],[1],[100])
        for key in ['u','v','z']:assert np.max(abs(d[key]-saved[key]))<=1e-8
        if name=='global_gauge':assert np.max(abs(d['z']))<1e-12 and np.linalg.norm(d['u'])>.09 and np.linalg.norm(d['v'])>.09
    for s in SEQS:
        cam=pose(DATA/'poses'/f'{s}.txt');gt=np.linalg.solve(cam[0],cam)
        line=next(x for x in (DATA/'sequences'/s/'calib.txt').read_text().splitlines() if x.startswith('Tr:'));tr=np.eye(4);tr[:3]=np.array([float(x) for x in line.split(':')[1].split()]).reshape(3,4);ti=np.linalg.inv(tr);actual[s]={}
        for a in ARMS:
            p=LC/(f'bank/{s}/N.npy' if a=='N' else f'evaluation/{s}/{a}.npy');est=tr@np.load(p)@ti;est=np.linalg.solve(est[0],est);q=horn(gt,est);actual[s][a]={};previous=None
            rec=read(LC/f'evaluation/{s}/{a}_segments.json');first=np.array([x['first'] for x in rec]);last=np.array([x['last'] for x in rec]);length=np.array([x['length_m'] for x in rec])
            for gauge,ee in [('F',est),('A',q@est)]:
                saved=load(OUT/f'{s}-{a}-{gauge}.npz');d=independent(gt,ee,first,last,length)
                for key,value in [('first',first),('last',last),('length',length)]:assert np.array_equal(value,saved[key])
                align_error=float(np.max(abs(q-saved['alignment'])));maxalign=max(align_error,maxalign);assert align_error<=1e-8
                for key in ['u','v','z']:
                    error=float(np.max(abs(d[key]-saved[key])));maxvector=max(error,maxvector);assert error<=1e-8
                if previous is not None:assert np.max(abs(d['z']-previous))<=1e-8
                previous=d['z'];m=statistics(d);actual[s][a][gauge]=m
                assert abs(m['orientation_squared_pct']+m['chord_squared_pct']+m['cross_squared_pct']-m['total_squared_pct'])<=1e-10
                assert np.max(abs(np.linalg.norm(d['z'],axis=1)-np.array([x['translation_fraction'] for x in rec])))<=1e-8 and abs(m['ter']-lcr['rows'][s][a]['ter'])<=1e-8
                for key,value in m.items():error=abs(value-r['rows'][s][a][gauge][key]);maxsummary=max(error,maxsummary);assert error<=1e-8
                records+=len(rec)
        print('MDC0 independent accounting',s,flush=True)
    means={g:{a:{gauge:{key:float(np.mean([actual[s][a][gauge][key] for s in ss])) for key in ['ter','orientation_squared_pct','chord_squared_pct','cross_squared_pct','total_squared_pct']} for gauge in ['F','A']} for a in ARMS} for g,ss in [('development',SEQS[:3]),('transfer_exposed',SEQS[3:])]}
    for g,m in means.items():
        for a,d in m.items():
            for gauge,values in d.items():
                for key,value in values.items():assert abs(value-r['cohort_means'][g][a][gauge][key])<=1e-8
    assert records==r['segment_vectors']==59184 and read(BASE/'freeze.json')['utc']<r['started_utc']<read(BASE/'output_seal.json')['utc'];verify()
    wall=time.perf_counter()-start;rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024;assert wall<=3600 and rss<=4*2**30
    save(BASE/'validation.json',dict(utc=utc(),passed=True,segment_vectors=records,fixtures=4,max_vector_delta=maxvector,max_alignment_delta=maxalign,max_summary_delta=maxsummary,wall_s=wall,peak_rss_bytes=rss,post_hoc_evaluator_only=True))
    save(BASE/'validation_seal.json',dict(utc=utc(),validation_sha256=sha(BASE/'validation.json'),results_sha256=sha(BASE/'results.json'),output_seal_sha256=sha(BASE/'output_seal.json')));(BASE/'INCOMPLETE').unlink();print('MDC0 fully validated',records,flush=True)
if __name__=='__main__':
    try:main()
    except Exception as e:
        p=BASE/'FAILURE_validation.json'
        if not p.exists():save(p,dict(utc=utc(),error=repr(e),traceback=traceback.format_exc()))
        raise
