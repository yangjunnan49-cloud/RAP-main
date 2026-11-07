"""Independent normalization/rigid-fit witness for sealed outputs; no neural call."""
import json,hashlib,math,os,resource,sys,time
from decimal import Decimal as D,getcontext
from pathlib import Path
ROOT=Path(__file__).resolve().parent;SCOPE=ROOT.parent;OUT=Path(sys.argv[1]);CASE=sys.argv[2];START=time.monotonic();getcontext().prec=50
SOURCE=Path('/mnt/e/githouse/RAP-main/docs/maintenance/2026-10-24/real-interface-02/run01/real')
def write(name,value):
    with (OUT/name).open('x') as f:json.dump(value,f,indent=2)
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest().upper()
def path(p):return Path('/mnt/'+p[0].lower()+'/'+p[3:].replace('\\','/'))
def audit(event,args):
    if event=='socket.connect':raise PermissionError('OC1 network forbidden')
    if event=='open' and args and isinstance(args[0],(str,bytes)):
        p=os.fsdecode(args[0])
        if p.endswith(('.ckpt','.pth')) or 'regx-interface-contract-01' in p or 'regx-reference-' in p:raise PermissionError('OC1 weights/raw/reference forbidden')
sys.addaudithook(audit);ok=False;error=None
try:
    freeze=json.loads((OUT.parent/'SOURCE_FREEZE.json').read_text());assert sha(SCOPE/'SOURCE_INPUTS.json')==freeze['source_inputs_sha256']
    for row in json.loads((SCOPE/'SOURCE_INPUTS.json').read_text()):assert path(row['path']).stat().st_size==row['bytes'] and sha(path(row['path']))==row['sha256']
    if CASE=='preflight':
        assert not any(k in sys.modules for k in ('numpy','torch'))
        write('RESULTS.json',dict(passed=True,stdlib_only=True,input_files=19,python_version=sys.version,interpreter_sha256=sha(Path(sys.executable).resolve())))
    else:
        import numpy as np
        assert 'torch' not in sys.modules;eps=np.finfo(np.float32).eps
        def witness(cond,pred,T,c,s):
            assert np.isfinite(cond).all() and np.isfinite(pred).all() and np.isfinite(T).all()
            assert T.shape==(4,4) and np.array_equal(T[3],np.array([0.,0.,0.,1.]))
            R=T[:3,:3];assert np.max(np.abs(R.T@R-np.eye(3)))<=1e-4 and abs(np.linalg.det(R)-1)<=1e-4
            recovered=(T[:3,3]+R@c)/s
            x=cond.astype(np.float64);y=pred.astype(np.float64);mx=x.mean(0);my=y.mean(0);t=my-mx@R.T
            terr=float(np.max(np.abs(recovered-t)));tbudget=256*eps*max(1.,float(np.max(np.abs(mx))),float(np.max(np.abs(my))))
            H=(x-mx).T@(y-my);sing=np.linalg.svd(H,compute_uv=False);optimal=float(sing[0]+sing[1]+(sing[2] if np.linalg.det(H)>=0 else -sing[2]))
            realized=float(np.trace(R@H));gap=abs(optimal-realized);budget=256*eps*max(1.,float(sing.sum()))
            assert terr<=tbudget and gap<=budget,'Rigid fit numerical witness rejected'
            return dict(centroid_error=terr,centroid_budget=tbudget,trace_gap=gap,trace_budget=budget,singular_values=sing.tolist(),unique_physical_pose_certified=False)
        q=np.array([[0,0,0],[2,0,0],[0,3,0],[0,0,4],[1,1,1],[-2,1,0]],dtype=np.float64);R=np.array([[0,-1,0],[1,0,0],[0,0,1]],dtype=np.float64);t=np.array([.5,-.25,1.]);p=q@R.T+t;synthetic=[]
        for s in (.5,16.):
            c=np.array([7.,-3.,2.]);T=np.eye(4);T[:3,:3]=R;T[:3,3]=s*t-R@c;witness(q,p,T,c,s);synthetic.append(dict(case='positive',scale=s,passed=True))
            bad=[];b=T.copy();b[0,3]+=s*.25;bad.append(('translation',p,b));bad.append(('inverse',p,np.linalg.inv(T)));b=T.copy();b[:3,:3]=np.diag([-1.,1.,1.]);bad.append(('reflection',p,b));b=T.copy();b[3,3]=.9;bad.append(('homogeneous',p,b));b=p.copy();b[0,0]=np.nan;bad.append(('nonfinite',b,T));b=T.copy();b[:3,3]=s*t;bad.append(('missing_center',p,b))
            for name,yy,tt in bad:
                try:witness(q,yy,tt,c,s)
                except AssertionError:pass
                else:raise AssertionError('Corruption accepted:'+name)
                synthetic.append(dict(case='reject_'+name,scale=s,passed=True))
        assert len(synthetic)==14;write('SYNTHETIC_CONTROLS.json',dict(passed=True,count=14,controls=synthetic))
        r=json.loads((SOURCE/'RESULTS.json').read_text());assert r['passed'] and len(r['captures'])==2
        checks=[];coordinates=0;maxratio=D(0);exports=[]
        for capture in r['captures']:
            case=capture['case'];out=json.loads((SOURCE/(case+'_RAP_OUTPUT.json')).read_text());seal=json.loads((SOURCE/(case+'_RAP_SEAL.json')).read_text());assert sha(SOURCE/seal['file'])==seal['sha256']
            def array(record):
                assert sha(SOURCE/record['file'])==record['sha256'];a=np.load(SOURCE/record['file'],allow_pickle=False)
                assert list(a.shape)==record['shape'] and str(a.dtype)==record['dtype'] and a.nbytes<=64*2**20 and np.isfinite(a).all();return a
            cond=array(capture['cond']);pred=array(capture['endpoint']);assert cond.dtype==np.float32 and pred.shape==cond.shape
            xyz=[array(v['xyz']) for v in out['prepared']];features=[array(v['features']) for v in out['prepared']];counts=[len(x) for x in xyz]
            assert counts==capture['counts'] and int(np.argmax(counts))==capture['primary'] and sum(counts)==len(cond)
            centers=[[sum((D.from_float(float(v)) for v in x[:,j]),D(0))/D(len(x)) for j in range(3)] for x in xyz]
            primary=capture['primary'];scale=D('1.5')*max(abs(D.from_float(float(row[j]))-centers[primary][j]) for row in xyz[primary] for j in range(3));assert scale>0
            offset=0;parts=[]
            for i,(x,f,Tlist) in enumerate(zip(xyz,features,out['T_parts'])):
                assert f.shape==(len(x),32) and np.all(np.sum(f.astype(np.float64)**2,axis=1)>0)
                for k,row in enumerate(x):
                    for j in range(3):
                        expected=(D.from_float(float(row[j]))-centers[i][j])/scale;actual=D.from_float(float(cond[offset+k,j]));budget=D(64)*(D(2)**-23)*max(D(1),abs(expected));ratio=abs(actual-expected)/budget
                        assert ratio<=1;maxratio=max(maxratio,ratio);coordinates+=1
                T=np.array(Tlist,dtype=np.float64);proof=witness(cond[offset:offset+len(x)],pred[offset:offset+len(x)],T,np.array([float(v) for v in centers[i]]),float(scale));parts.append(dict(view=i,count=len(x),witness=proof))
                name=case+f'_view{i:02d}_original_to_common.txt';np.savetxt(OUT/name,T,fmt='%.17g');assert np.array_equal(np.loadtxt(OUT/name),T)
                exports.append(dict(case=case,view=i,file=name,sha256=sha(OUT/name),direction='estimated_original_view_to_common',input_units_not_independently_authenticated=True));offset+=len(x)
            checks.append(dict(case=case,counts=counts,primary=primary,exact_Decimal_scale=str(scale),parts=parts))
        assert len(exports)==5 and 'torch' not in sys.modules
        write('RESULTS.json',dict(passed=True,synthetic_controls=14,normalization_coordinate_checks=coordinates,max_normalization_error_budget_ratio=str(maxratio),cases=checks,exports=exports,numpy_version=np.__version__,python_version=sys.version,neural_calls=0,source_fit_calls=0,new_pose_estimates_generated=0,physical_efficacy_claim=False,claim='Sealed-output representation/optimality witness only'))
    ok=True
except BaseException as caught:
    error=repr(caught)
    import traceback
    write('FAILURE.json',dict(error=error,traceback=traceback.format_exc()));raise
finally:write('worker_exit.json',dict(success=ok,error=error,elapsed_seconds=time.monotonic()-START,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,data_class='OC1_sealed_output_only_CPU_NumPy2_witness'))
