"""MDC0 frozen evaluator-only accounting of already sealed LC0 outcomes."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,resource,sys,time,traceback
import numpy as np
MAIN=Path(__file__).resolve().parents[2];SLAM=MAIN.parent/'RAP-SLAM';DATA=MAIN.parent/'Datasets/data_odometry_velodyne/dataset'
BASE=MAIN/'docs/maintenance/2026-10-07/metric-conflict-decomposition-01';OUT=BASE/'output'
LC=MAIN/'docs/maintenance/2026-10-07/retrieval-placement-audit-01';SEQS=['00','05','06','07','09','10'];ARMS=['N','C','P','H']
sys.path.insert(0,str(SLAM/'scripts'));import metric_error_decomposition as alg
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):
    with Path(p).open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
def utc():return datetime.now(timezone.utc).isoformat()
def pose(p):
    x=np.loadtxt(p).reshape(-1,3,4);a=np.tile(np.eye(4),(len(x),1,1));a[:,:3]=x;return a
def calib(s):
    line=[x for x in (DATA/'sequences'/s/'calib.txt').read_text().splitlines() if x.split(':')[0]=='Tr'][0]
    t=np.eye(4);t[:3]=np.array([float(x) for x in line.split(':',1)[1].split()]).reshape(3,4);return t
def trajectory(s,a):return LC/(f'bank/{s}/N.npy' if a=='N' else f'evaluation/{s}/{a}.npy')
def cap(start):assert time.perf_counter()-start<=3600 and resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024<=4*2**30 and sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file())<=100*2**20
def verify():
    for p,h in read(BASE/'freeze.json')['files'].items():assert sha(p)==h,p
def freeze():
    start=time.perf_counter();assert read(LC/'validation.json')['passed'] and not (LC/'INCOMPLETE').exists()
    assert read(LC/'validation_seal.json')['results_sha256']==sha(LC/'results.json')
    files=[BASE/'PROTOCOL.md',Path(__file__),Path(__file__).with_name('validate_metric_conflict_decomposition.py'),SLAM/'scripts/metric_error_decomposition.py']
    files += [LC/n for n in ['freeze.json','bank_seal.json','bank_validation.json','bank_validation_seal.json','evaluation_seal.json','results.json','validation.json','validation_seal.json']]
    lcfreeze=read(LC/'freeze.json')['files'];bs=read(LC/'bank_seal.json')['files'];es=read(LC/'evaluation_seal.json')['files']
    for s in SEQS:
        for p in [DATA/'poses'/f'{s}.txt',DATA/'sequences'/s/'calib.txt']:
            assert sha(p)==lcfreeze[str(p)];files.append(p)
        for a in ARMS:
            p=trajectory(s,a);h=bs[str(p.relative_to(LC/'bank'))] if a=='N' else es[str(p.relative_to(LC/'evaluation'))]
            assert sha(p)==h;files.append(p)
            p=LC/f'evaluation/{s}/{a}_segments.json';assert sha(p)==es[str(p.relative_to(LC/'evaluation'))];files.append(p)
    save(BASE/'freeze.json',dict(utc=utc(),files={str(p):sha(p) for p in files},wall_s=time.perf_counter()-start,post_hoc_evaluator_only=True))
    (BASE/'INCOMPLETE').write_text('MDC0 awaiting complete independent accounting validation\n');print('MDC0 frozen',len(files),'identities',flush=True);cap(start)
def summary(d):
    u,v,z=d['u'],d['v'],d['z'];uu=np.sum(u*u,axis=1);vv=np.sum(v*v,axis=1);uv=2*np.sum(u*v,axis=1);zz=np.sum(z*z,axis=1)
    assert np.max(abs(uu+vv+uv-zz))<=1e-10
    return dict(ter=float(np.mean(np.linalg.norm(z,axis=1))*100),orientation_squared_pct=float(np.mean(uu)*10000),chord_squared_pct=float(np.mean(vv)*10000),cross_squared_pct=float(np.mean(uv)*10000),total_squared_pct=float(np.mean(zz)*10000),segments=len(z))
def fixtures():
    g=np.tile(np.eye(4),(2,1,1));g[1,0,3]=100.;theta=.1;q=np.eye(4);q[:2,:2]=[[np.cos(theta),-np.sin(theta)],[np.sin(theta),np.cos(theta)]]
    cases={'perfect':g.copy(),'chord':g.copy(),'orientation':g.copy(),'global_gauge':q@g};cases['chord'][1,0,3]=90.;cases['orientation'][:,:3,:3]=q[:3,:3]
    for name,e in cases.items():
        d=alg.decompose(g,e,[0],[1],[100]);np.savez(OUT/f'fixture-{name}.npz',g=g,e=e,**d)
        if name=='perfect':assert np.max(abs(d['z']))==0
        if name=='chord':assert np.max(abs(d['u']))==0 and abs(np.linalg.norm(d['z'])-.1)<1e-12
        if name=='orientation':assert np.max(abs(d['v']))==0 and abs(np.linalg.norm(d['z'])-2*np.sin(.05))<1e-12
        if name=='global_gauge':assert np.max(abs(d['z']))<1e-12 and np.linalg.norm(d['u'])>.09 and np.linalg.norm(d['v'])>.09
def analyze():
    start=time.perf_counter();verify();started=utc();OUT.mkdir();fixtures();rows={};records=0;largest=0.
    lcr=read(LC/'results.json')
    for s in SEQS:
        gt=alg.anchor(pose(DATA/'poses'/f'{s}.txt'));tr=calib(s);ti=np.linalg.inv(tr);rows[s]={}
        for a in ARMS:
            est=alg.anchor(tr@np.load(trajectory(s,a))@ti);q=alg.align(gt,est)
            rec=read(LC/f'evaluation/{s}/{a}_segments.json');first=np.array([r['first'] for r in rec]);last=np.array([r['last'] for r in rec]);length=np.array([r['length_m'] for r in rec]);rows[s][a]={}
            prev=None
            for gauge,ee in [('F',est),('A',q@est)]:
                d=alg.decompose(gt,ee,first,last,length);m=summary(d)
                delta=float(np.max(abs(np.linalg.norm(d['z'],axis=1)-np.array([r['translation_fraction'] for r in rec]))));largest=max(delta,largest);assert delta<=1e-8
                assert abs(m['ter']-lcr['rows'][s][a]['ter'])<=1e-8
                if prev is not None:assert np.max(abs(d['z']-prev))<=1e-8
                prev=d['z'];rows[s][a][gauge]=m;records+=len(rec)
                np.savez(OUT/f'{s}-{a}-{gauge}.npz',**d,first=first,last=last,length=length,alignment=q)
        print('MDC0 decomposed',s,flush=True);cap(start)
    means={g:{a:{gauge:{k:float(np.mean([rows[s][a][gauge][k] for s in ss])) for k in ['ter','orientation_squared_pct','chord_squared_pct','cross_squared_pct','total_squared_pct']} for gauge in ['F','A']} for a in ARMS} for g,ss in [('development',SEQS[:3]),('transfer_exposed',SEQS[3:])]}
    verify();save(BASE/'results.json',dict(utc=utc(),started_utc=started,rows=rows,cohort_means=means,segment_vectors=records,max_LC0_fraction_delta=largest,wall_s=time.perf_counter()-start,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,post_hoc_evaluator_only=True))
    save(BASE/'output_seal.json',dict(utc=utc(),freeze_sha256=sha(BASE/'freeze.json'),results_sha256=sha(BASE/'results.json'),files={p.name:sha(p) for p in OUT.iterdir()}));print('MDC0 accounting outputs sealed',records,flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['freeze','analyze']);a=p.parse_args()
    try:globals()[a.stage]()
    except Exception as e:
        path=BASE/f'FAILURE_{a.stage}.json'
        if not path.exists():save(path,dict(utc=utc(),error=repr(e),traceback=traceback.format_exc()))
        raise
