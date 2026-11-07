"""Actual-source, CPU-only synthetic interface controls; no learned model."""
import ast
from decimal import Decimal, getcontext
from functools import partial
import hashlib
import json
import logging
import os
from pathlib import Path
import resource
import sys
import time
from types import MethodType, ModuleType, SimpleNamespace
from typing import Any, Callable, Dict, Optional, Tuple

ROOT = Path(__file__).resolve().parent
SCOPE = ROOT.parent
SOURCE = SCOPE.parent / 'source-binding-01'
FOLDER = Path(sys.argv[1])
STAGE = sys.argv[2]
START = time.monotonic()
getcontext().prec = 45
U = Decimal(2) ** -23
SELECTION = {
    'rap_backend.py': ['_normalize_parts', 'register', 'register_multi'],
    'rap_precision.py': ['ieee_matmul', 'precise_registration'],
    'point_clouds.py': ['split_parts'],
    'procrustes.py': ['solve_procrustes', 'fit_transformations', 'rigidify_prediction_with_procrustes'],
    'sampler.py': ['flow_sampler', 'euler_step', 'get_sampler'],
    'modeling.py': ['_prepare_data', 'sample_rectified_flow'],
    'dataset.py': ['_transform'],
    'transform.py': ['center_pcd', 'pad_data'],
    'evaluator.py': ['_save_transformation_files'],
}

def winpath(value):
    return Path('/mnt/' + value[0].lower() + '/' + value[3:].replace('\\', '/'))

def exclusive(name, value):
    with (FOLDER / name).open('x') as stream:
        json.dump(value, stream, indent=2)

def bound_functions():
    bindings = []
    for name in ('SOURCE_BINDINGS.json', 'DEPENDENCY_BINDINGS.json'):
        bindings.extend(json.loads((SOURCE / name).read_text(encoding='utf-8-sig')))
    functions = {}
    records = []
    for binding in bindings:
        snapshot = winpath(binding['snapshot'])
        raw = snapshot.read_bytes()
        expected = binding['sha256'].lower()
        assert len(raw) <= 2 * 2**20
        assert hashlib.sha256(raw).hexdigest() == expected
        assert hashlib.sha256(winpath(binding['source']).read_bytes()).hexdigest() == expected
        if snapshot.name not in SELECTION:
            continue
        tree = ast.parse(raw.decode('utf-8-sig'), str(snapshot))
        for name in SELECTION[snapshot.name]:
            matches = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == name]
            assert len(matches) == 1, (snapshot.name, name)
            node = matches[0]
            functions[name] = node
            compile(ast.Module(body=[node], type_ignores=[]), str(snapshot), 'exec')
            records.append(dict(file=str(snapshot), sha256=expected, function=name, first_line=node.lineno, last_line=node.end_lineno, ast_sha256=hashlib.sha256(ast.dump(node, include_attributes=False).encode()).hexdigest()))
    assert len(functions) == sum(map(len, SELECTION.values()))
    return functions, records

def run_controls(functions):
    # These are the only numerical imports explicitly requested by this worker.
    import numpy as np
    import torch
    from contextlib import contextmanager
    from threading import RLock
    torch.set_num_threads(1)
    torch.manual_seed(42)
    np.random.seed(42)
    assert not torch.cuda.is_initialized()
    ns = dict(np=np, torch=torch, nn=torch.nn, time=time, Path=Path, partial=partial,
              Callable=Callable, Optional=Optional, Tuple=Tuple, Dict=Dict, Any=Any,
              contextmanager=contextmanager, wraps=__import__('functools').wraps, _LOCK=RLock())
    order = ['ieee_matmul', 'precise_registration', 'split_parts', 'solve_procrustes', 'fit_transformations',
             'rigidify_prediction_with_procrustes', 'flow_sampler', 'euler_step', 'get_sampler',
             'center_pcd', 'pad_data', '_transform', '_save_transformation_files', '_prepare_data', 'sample_rectified_flow']
    for name in order:
        exec(compile(ast.Module(body=[functions[name]], type_ignores=[]), name, 'exec'), ns)
    # Preserve the backend's local import statement while avoiding unrelated package initializers.
    assert 'rectified_point_flow' not in sys.modules
    ast_package = ModuleType('rectified_point_flow')
    ast_package.__path__ = []
    ast_fit_module = ModuleType('rectified_point_flow.procrustes')
    ast_fit_module.fit_transformations = ns['fit_transformations']
    sys.modules['rectified_point_flow'] = ast_package
    sys.modules['rectified_point_flow.procrustes'] = ast_fit_module
    backend_class = ast.ClassDef(name='SourceBackend', bases=[], keywords=[], body=[functions[n] for n in ('_normalize_parts', 'register', 'register_multi')], decorator_list=[])
    exec(compile(ast.fix_missing_locations(ast.Module(body=[backend_class], type_ignores=[])), 'source_backend', 'exec'), ns)
    Backend = ns['SourceBackend']
    results = []
    coordinate_checks = 0
    max_ratio = Decimal(0)
    fixture_calls = 0
    I = ((1,0,0),(0,1,0),(0,0,1))
    R1 = ((0,-1,0),(1,0,0),(0,0,1))
    R2 = ((1,0,0),(0,0,-1),(0,1,0))
    rotations = (I, R1, R2)

    def d(value): return Decimal.from_float(float(value))
    def mv(R, v): return [sum(Decimal(R[j][k])*v[k] for k in range(3)) for j in range(3)]
    def mtv(R, v): return [sum(Decimal(R[k][j])*v[k] for k in range(3)) for j in range(3)]

    def fixture(counts, unit):
        world, raw, features, trans = [], [], [], []
        unit = float(unit)
        for i, count in enumerate(counts):
            w = np.array([((k % 17-8)/4, ((k*k+3)%19-9)/8, ((7*k+5)%23-11)/16) for k in range(count)], dtype=np.float64)*unit
            t = np.array((3*i-2, 2-i, -i/2), dtype=np.float64)*unit
            x = ((w-t) @ np.array(rotations[i])).astype(np.float32)
            f = np.zeros((count,32), dtype=np.float32)
            f[:,0] = i+1; f[:,1] = np.arange(count); f[:,2] = np.arange(count)%23
            world.append(w); raw.append(x); features.append(f); trans.append(t)
        L = max([1.] + [float(np.max(np.abs(x))) for x in raw] + [float(np.max(np.abs(t))) for t in trans])
        return world, raw, features, trans, Decimal(256)*U*d(L)

    def evaluate(T, raw, trans, i, r, budget, require=True):
        nonlocal coordinate_checks, max_ratio
        error = Decimal(0)
        for a in range(3):
            for b in range(3):
                expected = sum(Decimal(rotations[r][k][a])*Decimal(rotations[i][k][b]) for k in range(3))
                if require: assert abs(d(T[a,b])-expected) <= 128*U
                else: error = max(error, abs(d(T[a,b])-expected)/(128*U))
        for row in raw[i]:
            w = [v+d(t) for v,t in zip(mv(rotations[i], list(map(d,row))), trans[i])]
            expected = mtv(rotations[r], [v-d(t) for v,t in zip(w,trans[r])])
            for axis in range(3):
                actual = sum(d(T[axis,k])*d(row[k]) for k in range(3))+d(T[axis,3])
                ratio = abs(actual-expected[axis])/budget
                error = max(error,ratio)
                if require:
                    assert ratio <= 1, ('coordinate_budget',i,r,float(ratio))
                    coordinate_checks += 1
        if require: max_ratio = max(max_ratio,error)
        return error

    def backend_case(counts, unit, gauge, pair=False):
        nonlocal fixture_calls
        world, raw, features, trans, budget = fixture(counts,unit)
        class EndpointStub:
            def sample_rectified_flow(self, batch, latent, return_tarjectory):
                nonlocal fixture_calls
                fixture_calls += 1
                assert set(batch) == {'pointclouds','pointclouds_gt','features','scales','anchor_indices','points_per_part','cu_seqlens'}
                assert batch['pointclouds'].dtype == torch.float32
                assert np.array_equal(batch['features'].cpu().numpy(),np.concatenate(features))
                assert np.array_equal(batch['points_per_part'].cpu().numpy(),np.array([counts]))
                expected_anchor = np.zeros(sum(counts),dtype=bool)
                a = int(np.argmax(counts)); st = sum(counts[:a]); expected_anchor[st:st+counts[a]] = True
                assert np.array_equal(batch['anchor_indices'].cpu().numpy(),expected_anchor)
                assert torch.equal(batch['pointclouds_gt'],batch['pointclouds'])
                Q = np.array(I if gauge == 0 else R1)
                shift = np.zeros(3) if gauge == 0 else np.array((5.,-7.,9.))*float(unit)
                target = (np.concatenate(world) @ Q.T + shift)/float(batch['scales'][0])
                return {'end_point_trajectory':[torch.tensor(target,dtype=torch.float32)]}
        obj = object.__new__(Backend)
        obj.device = torch.device('cpu'); obj.model = EndpointStub()
        def prep(points,max_points=None):
            i = next(i for i,x in enumerate(raw) if x is points)
            return points, features[i]
        obj.preprocess = prep
        obj._alignment_metrics = lambda *a,**k:(0.,0.)
        if pair:
            T,diag = obj.register(raw[0],raw[1],return_registered=True)
            evaluate(T,raw,trans,1,0,budget)
            Ts = diag['T_parts']
        else:
            Ts,diag = obj.register_multi(raw)
            assert diag['anchor_idx'] == int(np.argmax(counts))
        for r in range(len(counts)):
            for i in range(len(counts)):
                evaluate(np.linalg.inv(Ts[r]) @ Ts[i],raw,trans,i,r,budget)
        return Ts,raw,trans,budget

    layouts = ((207,203,201),(201,207,203),(201,203,207),(201,201,201))
    saved = None
    for layout_index, counts in enumerate(layouts):
        for unit in (.0625,1.,64.):
            for gauge in (0,1):
                saved_case = backend_case(counts,unit,gauge)
                if layout_index == 0 and unit == 1. and gauge == 0: saved = saved_case
                results.append(dict(case='backend',layout=layout_index,unit=unit,gauge=gauge,passed=True))
    backend_case((207,201),1.,0,pair=True)
    results.append(dict(case='pair_source_return_direction',passed=True,alignment_metrics='stubbed_not_measured'))

    class SerialPool:
        @staticmethod
        def map(fn, values): return list(map(fn,values))
    for dtype in (np.float32,np.float64):
        for layout_index,counts in enumerate(layouts[:3]):
            for unit in (.0625,1.,64.):
                world,raw,features,trans,budget = fixture(counts,unit)
                data = dict(pointclouds_gt=[x.astype(dtype) for x in raw],pointclouds_normals_gt=[np.zeros_like(x,dtype=dtype) for x in raw],features=features,num_parts=3,is_pre_sampled=True,index=0,name='synthetic',overlap_threshold=0.,part_filenames=['view0','view1','view2'])
                obj=SimpleNamespace(load_features=True,split='val',max_parts=5,multi_anchor=False,pool=SerialPool(),dataset_name='synthetic')
                val = ns['_transform'](obj,data)
                assert val['points_per_part'].tolist() == list(counts)+[0,0]
                assert val['anchor_parts'].tolist() == [i == int(np.argmax(counts)) for i in range(5)]
                offsets=np.cumsum([0]+list(counts))
                primary=int(np.argmax(counts))
                centers=[[sum(d(v) for v in x[:,axis])/Decimal(len(x)) for axis in range(3)] for x in raw]
                expected_scale=Decimal('1.5')*max(abs(d(row[axis])-centers[primary][axis]) for row in raw[primary] for axis in range(3))
                targets=[]
                for i in range(3):
                    st,ed=offsets[i:i+2]
                    marker=val['features'][st:ed]
                    assert np.all(marker[:,0] == i+1)
                    order=marker[:,1].astype(int)
                    assert sorted(order.tolist()) == list(range(counts[i]))
                    assert np.array_equal(marker[:,2],order%23)
                    for out_row,source_index in zip(val['pointclouds'][st:ed],order):
                        for axis in range(3):
                            expected=(d(raw[i][source_index,axis])-centers[i][axis])/expected_scale
                            assert abs(d(out_row[axis])-expected) <= 64*U*max(Decimal(1),abs(expected))
                    targets.append(world[i][order]/float(val['scales']))
                cond=torch.from_numpy(val['pointclouds'])
                pred=torch.tensor(np.concatenate(targets),dtype=torch.float32)
                ppp=torch.from_numpy(val['points_per_part'][None,:])
                rots,trs=ns['fit_transformations'](cond,pred,ppp,torch.tensor([0,sum(counts)],dtype=torch.int32))
                torchdata={key:torch.from_numpy(val[key][None,...]) for key in ('rotations','translations','points_per_part','scales')}
                torchdata['part_filenames']=[val['part_filenames']]
                outdir=FOLDER / ('export_'+np.dtype(dtype).name+'_'+str(layout_index)+'_'+str(unit))
                outdir.mkdir()
                ns['_save_transformation_files'](None,torchdata,0,outdir,'synthetic',0,0,rots,trs,torch.from_numpy(val['global_rotation']),torch.from_numpy(val['global_translation']))
                files=sorted(outdir.glob('*_transform.txt'))
                assert len(files) == 3, 'Exporter can catch exceptions; complete file count is required.'
                Ts=[np.loadtxt(outdir/('synthetic_sample00000_generation00_view'+str(i)+'_transform.txt')) for i in range(3)]
                for r in range(3):
                    for i in range(3): evaluate(np.linalg.inv(Ts[r])@Ts[i],raw,trans,i,r,budget)
                results.append(dict(case='val_transform_export',dtype=np.dtype(dtype).name,layout=layout_index,unit=unit,passed=True))

    # The sampler must retrieve the compatibility key but must not inspect its opaque contents.
    class OpaqueReference:
        def __getattr__(self,name): raise AssertionError('reference_contents_touched:'+name)
        def __array__(self,*args,**kwargs): raise AssertionError('reference_array_conversion')
    class AccessDict(dict):
        def __getitem__(self,key):
            self.accesses.append(key)
            return super().__getitem__(key)
    sampler_points=torch.tensor([[float(k%5),float((k*k)%7),float((3*k)%11)] for k in range(18)],dtype=torch.float32)
    target=sampler_points+torch.tensor([.5,-.25,1.])
    sample_outputs=[]
    for rigid in (False,True):
        for opaque_id in range(2):
            endpoint=target.clone()
            if rigid: endpoint[0,0] += .75
            batch=AccessDict(pointclouds=sampler_points,pointclouds_gt=OpaqueReference(),features=torch.zeros(18,32),scales=torch.ones(1),anchor_indices=torch.tensor([True]*6+[False]*12),points_per_part=torch.tensor([[6,6,6]]),cu_seqlens=torch.tensor([0,18]))
            batch.accesses=[]
            obj=SimpleNamespace(inference_sampling_steps=3,inference_sampler='euler',rigidity_forcing=rigid,return_end_point_trajectory=True)
            obj._sample_timesteps=lambda batch_size:torch.zeros(batch_size)
            obj._prepare_data=MethodType(ns['_prepare_data'],obj)
            def flow(**kw):
                assert kw['cond_coord'] is sampler_points
                assert 'pointclouds_gt' not in kw
                t=float(kw['timesteps'][0]);assert t>0
                return (kw['x']-endpoint)/t
            obj.flow_model=flow
            out=ns['sample_rectified_flow'](obj,batch,None,x_1=torch.zeros_like(sampler_points),return_tarjectory=True)
            assert batch.accesses.count('pointclouds_gt') == 1
            assert float(torch.max(torch.abs(out['end_point_trajectory'][-1]-endpoint))) < float(64*U)*max(1.,float(torch.max(torch.abs(endpoint))))
            if rigid: assert float(torch.max(torch.abs(out['trajectory'][-1]-out['end_point_trajectory'][-1]))) > .05
            if opaque_id == 0: sample_outputs.append(out)
            else:
                assert torch.equal(sample_outputs[-1]['end_point_trajectory'],out['end_point_trajectory'])
                assert torch.equal(sample_outputs[-1]['trajectory'],out['trajectory'])
            results.append(dict(case='sampler_placeholder',rigidity_forcing=rigid,opaque_id=opaque_id,passed=True,compatibility_key_reads=1,reference_content_reads=0))

    Ts,raw,trans,budget=saved
    good=np.linalg.inv(Ts[0])@Ts[1]
    bads={'inverse_direction':np.linalg.inv(good),'wrong_translation_scale':good.copy(),'swapped_part':np.linalg.inv(Ts[0])@Ts[2],'omitted_centering':good.copy()}
    bads['wrong_translation_scale'][:3,3] *= 2
    bads['omitted_centering'][:3,3] += np.array((2.,-3.,4.))
    for name,T in bads.items():
        ratio=evaluate(T,raw,trans,1,0,budget,require=False)
        assert ratio>1, ('negative_not_detected',name)
        results.append(dict(case=name,passed=True,expected_rejection=True,minimum_detected_ratio=float(ratio)))
    marker=np.concatenate(fixture(layouts[0],1.)[2])
    assert not np.array_equal(marker,marker[::-1])
    results.append(dict(case='feature_row_permutation',passed=True,expected_rejection=True))
    def admission(parts):
        if not parts: raise ValueError('empty')
        for x in parts:
            if x.ndim != 2 or x.shape[1] != 3 or len(x)==0 or not np.isfinite(x).all(): raise ValueError('invalid_part')
            if not float(np.max(np.abs(x-x.mean(0))))>0: raise ValueError('degenerate')
    for name,parts in [('empty',[]),('empty_part',[np.zeros((0,3))]),('nonfinite',[np.array([[0.,1.,float('nan')]])]),('degenerate',[np.ones((201,3))])]:
        try: admission(parts)
        except ValueError: pass
        else: raise AssertionError('admission_failed:'+name)
        results.append(dict(case='public_admission_'+name,passed=True,expected_rejection=True,source_normalization_calls=0))
    schema=[201,0,203]
    assert any(schema[i] == 0 and any(v>0 for v in schema[i+1:]) for i in range(len(schema)))
    results.append(dict(case='interior_zero_schema',passed=True,expected_rejection=True,source_fit_calls=0))
    assert not torch.cuda.is_initialized()
    return dict(passed=True,cases=results,case_count=len(results),independent_decimal_coordinate_checks=coordinate_checks,max_coordinate_budget_ratio=str(max_ratio),rotation_budget_factor=128,coordinate_budget_factor=256,unit_roundoff='2^-23',synthetic_endpoint_stub_calls=fixture_calls,numpy=np.__version__,torch=torch.__version__,CUDA_initialized=False,preprocessing='stubbed',neural_models='stubbed_never_loaded',fit_imports_routed_to_bound_AST=True,alignment_metrics='stubbed_not_scored',canonical_file_loaders_executed=False,external_reference_files_read=0,RAP_model_calls=0,real_point_reads=0)

success=False
error=None
try:
    functions,records=bound_functions()
    exclusive('FUNCTION_BINDINGS.json',records)
    assert sum(p.stat().st_size for p in SCOPE.rglob('*') if p.is_file()) < 16*2**20
    if STAGE == 'preflight':
        result=dict(passed=True,functions=len(records),numerical_imports_requested=0,source_functions_executed=0)
    elif STAGE == 'numeric':
        result=run_controls(functions)
    else: raise ValueError('unknown_stage')
    exclusive('RESULTS.json',result)
    success=True
except BaseException as caught:
    error=repr(caught)
    import traceback
    exclusive('FAILURE.json',dict(error=error,traceback=traceback.format_exc()))
    raise
finally:
    exclusive('worker_exit.json',dict(success=success,error=error,elapsed_seconds=time.monotonic()-START,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,data_class='synthetic_source_interface',raw_reads=0,external_reference_reads=0,RAP_model_calls=0))
print(json.dumps(dict(success=success,stage=STAGE,elapsed=time.monotonic()-START)))
