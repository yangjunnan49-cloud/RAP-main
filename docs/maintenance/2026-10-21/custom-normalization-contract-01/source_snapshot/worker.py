"""Independent scalar Decimal fixture validator; no builder multiply/inverse reuse."""
import copy, json, math, resource, sys, time
from decimal import Decimal,localcontext
from pathlib import Path
from normalization import normalize,recover
folder=Path(sys.argv[1]);start=time.monotonic();ok=False;error=None;checks=[];coordinates=0;normalized_checks=0;worst=Decimal(0)
rotations=[[[1.,0.,0.],[0.,1.,0.],[0.,0.,1.]],[[0.,-1.,0.],[1.,0.,0.],[0.,0.,1.]],[[1.,0.,0.],[0.,0.,-1.],[0.,1.,0.]]]
translations=[[10.,-2.,3.],[-7.,12.,2.],[3.,-4.,9.]]
gauges=[(rotations[0],[0.,0.,0.]),([[.6,-.8,0.],[.8,.6,0.],[0.,0.,1.]],[.25,-.5,.75])]


def reject(name,fn):
    try:fn()
    except (ValueError,TypeError):checks.append(dict(name=name,passed=True))
    else:raise AssertionError(name)


try:
    for size in (1e-6,1.,1e6):
        world=[[size*((i%7)-3)/8,size*((i*3%11)-5)/16,size*((i*5%13)-6)/32] for i in range(61)]
        views={str(v):[[math.fsum(rotations[v][j][k]*p[k] for k in range(3))+translations[v][j] for j in range(3)] for p in world] for v in range(3)}
        original=copy.deepcopy(views);normalized,meta=normalize(views)
        assert original==views and list(normalized)==list(views)
        scale=meta['shared_scale'];magnitude=max(1.,scale,max(abs(x) for rows in views.values() for row in rows for x in row))
        bound=Decimal.from_float(4096*sys.float_info.epsilon*magnitude)
        with localcontext() as context:
            context.prec=60
            for key,rows in views.items():
                for point,z in zip(rows,normalized[key]):
                    for axis in range(3):
                        restored=Decimal.from_float(z[axis])*Decimal.from_float(scale)+Decimal.from_float(meta['centers'][key][axis])
                        ratio=abs(restored-Decimal.from_float(point[axis]))/bound
                        worst=max(worst,ratio);assert ratio<=1;normalized_checks+=1
        for gauge_index,(g,gt) in enumerate(gauges):
            predictions={}
            for view in range(3):
                key=str(view);r=rotations[view];t=translations[view];c=meta['centers'][key]
                # Fixture oracle only: normalized input -> W/s -> common rigid gauge.
                base_r=[[r[j][i] for j in range(3)] for i in range(3)]
                base_t=[math.fsum(r[j][i]*(c[j]-t[j]) for j in range(3))/scale for i in range(3)]
                rr=[[math.fsum(g[i][k]*base_r[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
                tt=[math.fsum(g[i][k]*base_t[k] for k in range(3))+gt[i] for i in range(3)]
                predictions[key]=[rr[i]+[tt[i]] for i in range(3)]+[[0.,0.,0.,1.]]
            for reference in range(3):
                recovered=recover(predictions,meta,str(reference))
                with localcontext() as context:
                    context.prec=60
                    for key,rows in views.items():
                        transform=recovered[key]
                        for point,world_point in zip(rows,world):
                            for axis in range(3):
                                actual=sum(Decimal.from_float(transform[axis][j])*Decimal.from_float(point[j]) for j in range(3))+Decimal.from_float(transform[axis][3])
                                expected=sum(Decimal.from_float(rotations[reference][axis][j])*Decimal.from_float(world_point[j]) for j in range(3))+Decimal.from_float(translations[reference][axis])
                                ratio=abs(actual-expected)/bound;worst=max(worst,ratio);assert ratio<=1
                                coordinates+=1
            checks.append(dict(name='all_points_all_references',coordinate_scale=size,left_gauge=gauge_index,passed=True))
    reject('empty_views',lambda:normalize({}))
    reject('empty_view',lambda:normalize({'x':[]}))
    reject('nonfinite_points',lambda:normalize({'x':[[float('nan'),0.,0.]]}))
    reject('zero_spread',lambda:normalize({'x':[[1.,2.,3.]]}))
    reject('per_view_scale_metadata',lambda:recover(predictions,dict(meta,scales=[1.,2.,3.]),'0'))
    reject('zero_shared_scale',lambda:recover(predictions,dict(meta,shared_scale=0.),'0'))
    reject('missing_view',lambda:recover({'0':predictions['0']},meta,'0'))
    bad=copy.deepcopy(predictions);bad['0'][0][0]*=1.01
    reject('nonrigid_prediction',lambda:recover(bad,meta,'0'))
    bad=copy.deepcopy(predictions);bad['0'][0]=[-x for x in bad['0'][0]]
    reject('reflected_prediction',lambda:recover(bad,meta,'0'))
    bad=copy.deepcopy(predictions);bad['0'][3][0]=1.
    reject('homogeneous_row',lambda:recover(bad,meta,'0'))
    bad=copy.deepcopy(predictions);bad['0'][0][3]=float('inf')
    reject('nonfinite_prediction',lambda:recover(bad,meta,'0'))
    ok=True
except BaseException as caught:
    error=repr(caught)
    import traceback;traceback.print_exc()
finally:
    (folder/'worker_exit.json').write_text(json.dumps(dict(success=ok,error=error,checks=checks,count=len(checks),
        scalar_coordinate_comparisons=coordinates,normalized_roundtrip_comparisons=normalized_checks,max_error_budget_ratio=str(worst),
        elapsed=time.monotonic()-start,max_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
        raw_file_decodes=0,GT_reads=0,model_calls=0,registration_solver_calls=0,
        actual_RAP_interface_authenticated=False,canonical_normalization=False,synthetic_oracle_only=True),indent=2))
sys.exit(0 if ok else 2)
