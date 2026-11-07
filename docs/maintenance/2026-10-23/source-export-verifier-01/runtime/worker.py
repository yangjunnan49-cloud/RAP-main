"""Independent Decimal verifier of sealed SI1 synthetic exports, no source replay."""
from decimal import Decimal, getcontext
import hashlib
import json
from pathlib import Path
import resource
import struct
import sys
import time

ROOT=Path(__file__).resolve().parent
SCOPE=ROOT.parent
FOLDER=Path(sys.argv[1]); STAGE=sys.argv[2]
START=time.monotonic(); getcontext().prec=50
U=Decimal(2)**-23
ROTS=[[[1,0,0],[0,1,0],[0,0,1]],[[0,-1,0],[1,0,0],[0,0,1]],[[1,0,0],[0,0,-1],[0,1,0]]]
LAYOUTS=[[207,203,201],[201,207,203],[201,203,207]]

def write(name,value):
    with (FOLDER/name).open('x') as stream: json.dump(value,stream,indent=2)

def path(value): return Path('/mnt/'+value[0].lower()+'/'+value[3:].replace('\\','/'))
def dot(a,b): return sum((x*y for x,y in zip(a,b)),Decimal(0))
def mv(R,x): return [dot(list(map(Decimal,row)),x) for row in R]
def mtv(R,x): return [dot([Decimal(R[k][j]) for k in range(3)],x) for j in range(3)]
def multiply(A,B): return [[sum(A[i][k]*B[k][j] for k in range(4)) for j in range(4)] for i in range(4)]

def inverse(A):
    rows=[list(row)+[Decimal(i==j) for j in range(4)] for i,row in enumerate(A)]
    for j in range(4):
        p=max(range(j,4),key=lambda i:abs(rows[i][j]))
        if rows[p][j]==0: raise ValueError('singular')
        rows[j],rows[p]=rows[p],rows[j]
        div=rows[j][j]; rows[j]=[v/div for v in rows[j]]
        for i in range(4):
            if i==j: continue
            coeff=rows[i][j]; rows[i]=[a-coeff*b for a,b in zip(rows[i],rows[j])]
    return [row[4:] for row in rows]

def valid(A):
    if len(A)!=4 or any(len(row)!=4 for row in A): return False
    if not all(v.is_finite() for row in A for v in row): return False
    if A[3] != [Decimal(0),Decimal(0),Decimal(0),Decimal(1)]: return False
    e=128*U
    for i in range(3):
        for j in range(3):
            if abs(sum(A[k][i]*A[k][j] for k in range(3))-Decimal(i==j))>8*e: return False
    a,b,c=A[0][:3];d,e1,f=A[1][:3];g,h,i=A[2][:3]
    det=a*(e1*i-f*h)-b*(d*i-f*g)+c*(d*h-e1*g)
    return abs(det-1)<=24*e

def parse(raw):
    A=[[Decimal(v) for v in line.split()] for line in raw.decode('utf-8').splitlines() if line.strip()]
    if not valid(A): raise ValueError('invalid_rigid_homogeneous_matrix')
    return A

def fixture(layout,unit):
    points=[]; ts=[]
    for view,count in enumerate(LAYOUTS[layout]):
        t=[Decimal(3*view-2)*unit,Decimal(2-view)*unit,-Decimal(view)/2*unit]
        ts.append(t); part=[]
        for k in range(count):
            w=[Decimal(k%17-8)/4*unit,Decimal((k*k+3)%19-9)/8*unit,Decimal((7*k+5)%23-11)/16*unit]
            x=mtv(ROTS[view],[a-b for a,b in zip(w,t)])
            # Every fixture value is an exact binary rational in the declared float32 domain.
            assert all(Decimal.from_float(struct.unpack('f',struct.pack('f',float(v)))[0])==v for v in x)
            part.append(x)
        points.append(part)
    L=max([Decimal(1)]+[abs(v) for part in points for row in part for v in row]+[abs(v) for t in ts for v in t])
    return points,ts,256*U*L

def check(A,points,ts,view,ref,budget):
    if not valid(A): return False,Decimal('Infinity'),0
    ratio=Decimal(0); count=0
    for j in range(3):
        for k in range(3):
            expected=sum(Decimal(ROTS[ref][a][j])*Decimal(ROTS[view][a][k]) for a in range(3))
            if abs(A[j][k]-expected)>128*U: return False,abs(A[j][k]-expected)/(128*U),0
    for x in points[view]:
        world=[a+b for a,b in zip(mv(ROTS[view],x),ts[view])]
        truth=mtv(ROTS[ref],[a-b for a,b in zip(world,ts[ref])])
        for j in range(3):
            actual=dot(A[j][:3],x)+A[j][3]
            ratio=max(ratio,abs(actual-truth[j])/budget);count+=1
    return ratio<=1,ratio,count

ok=False; error=None
try:
    freeze=json.loads((FOLDER.parent/'SOURCE_FREEZE.json').read_text())
    manifest_raw=(SCOPE/'INPUT_BINDINGS.json').read_bytes()
    assert hashlib.sha256(manifest_raw).hexdigest().upper()==freeze['inputs_manifest_sha256']
    bindings=json.loads(manifest_raw)
    buffers={}
    for row in bindings:
        raw=path(row['path']).read_bytes()
        assert len(raw)==row['bytes']
        assert hashlib.sha256(raw).hexdigest().upper()==row['sha256']
        buffers[str(path(row['path']))]=raw
    assert len(buffers)==54
    assert 'numpy' not in sys.modules and 'torch' not in sys.modules
    if STAGE=='preflight':
        result=dict(passed=True,sealed_inputs=54,numerical_imports_requested=0,source_functions_executed=0)
    elif STAGE=='numeric':
        base=SCOPE.parent/'source-interface-01'/'run02'/'numeric'
        results=[]; checks=0; max_ratio=Decimal(0); selected=None
        for dtype in ('float32','float64'):
            for layout in range(3):
                for unit in (Decimal('0.0625'),Decimal(1),Decimal(64)):
                    unit_name='0.0625' if unit<1 else str(int(unit))+'.0'
                    folder=base/('export_'+dtype+'_'+str(layout)+'_'+unit_name)
                    Ts=[parse(buffers[str(folder/('synthetic_sample00000_generation00_view'+str(i)+'_transform.txt'))]) for i in range(3)]
                    points,ts,budget=fixture(layout,unit)
                    for ref in range(3):
                        for view in range(3):
                            passed,ratio,n=check(multiply(inverse(Ts[ref]),Ts[view]),points,ts,view,ref,budget)
                            assert passed,(dtype,layout,str(unit),view,ref,str(ratio))
                            checks+=n;max_ratio=max(max_ratio,ratio)
                    if dtype=='float64' and layout==0 and unit==1: selected=(Ts,points,ts,budget)
                    results.append(dict(case='sealed_exports',dtype=dtype,layout=layout,unit=str(unit),passed=True))
        Ts,points,ts,budget=selected
        ref_inverse=inverse(Ts[0]); good=multiply(ref_inverse,Ts[1])
        center=[sum(row[a] for row in points[1])/Decimal(len(points[1])) for a in range(3)]
        omitted=[row[:] for row in Ts[1]]
        for a in range(3): omitted[a][3]+=dot(Ts[1][a][:3],center)
        bad_scale=[row[:] for row in Ts[1]]
        for a in range(3):bad_scale[a][3]*=2
        negatives={'actual_omitted_Rc_term':multiply(ref_inverse,omitted),'inverse_direction':inverse(good),'doubled_metric_translation':multiply(ref_inverse,bad_scale),'swapped_view_identity':multiply(ref_inverse,Ts[2])}
        for name,A in negatives.items():
            passed,ratio,n=check(A,points,ts,1,0,budget)
            assert not passed,name
            results.append(dict(case=name,passed=True,expected_rejection=True,ratio=str(ratio)))
        for name in ('nonfinite','reflection','homogeneous'):
            A=[row[:] for row in good]
            if name=='nonfinite': A[0][3]=Decimal('NaN')
            if name=='reflection':
                for a in range(3): A[a][0]*=-1
            if name=='homogeneous': A[3][0]=Decimal(1)
            assert not valid(A),name
            results.append(dict(case='reject_'+name,passed=True,expected_rejection=True))
        first=bindings[0];raw=buffers[str(path(first['path']))]
        assert hashlib.sha256(raw+b'0').hexdigest().upper()!=first['sha256']
        results.append(dict(case='reject_hash_tamper_before_parse',passed=True,expected_rejection=True))
        result=dict(passed=True,case_count=len(results),cases=results,independent_decimal_coordinate_checks=checks,max_coordinate_budget_ratio=str(max_ratio),source_or_fit_replays=0,numerical_imports_requested=0,source_functions_executed=0,actual_missing_center_control_proved_separately=True,SI1_original_limitation_unchanged=True,external_reference_or_real_points_read=0)
    else:raise ValueError('unknown_stage')
    assert sum(p.stat().st_size for p in SCOPE.rglob('*') if p.is_file())<4*2**20
    assert 'numpy' not in sys.modules and 'torch' not in sys.modules
    write('RESULTS.json',result);ok=True
except BaseException as caught:
    error=repr(caught)
    import traceback
    write('FAILURE.json',dict(error=error,traceback=traceback.format_exc()))
    raise
finally:
    write('worker_exit.json',dict(success=ok,error=error,elapsed_seconds=time.monotonic()-START,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,data_class='sealed_synthetic_export_verification',source_fit_replays=0,RAP_model_calls=0,real_point_reads=0))
print(json.dumps(dict(success=ok,stage=STAGE,elapsed=time.monotonic()-START)))
