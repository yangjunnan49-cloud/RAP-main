"""Actual17-translation source-kernel metamorphic audit, no model or reference."""
import codecs
from decimal import Decimal,localcontext
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import baseline_lib as lib
import kernel

OUT=lib.ROOT/'features'
try:
    lib.verify_freeze('prediction');lib.verify_seal(lib.ROOT/'controls')
    binding=lib.load(lib.ROOT/'INPUT_BINDING.json');source_binding=lib.load(lib.ROOT/'SOURCE_BINDING.json')
    assert lib.sha(binding['predictions']['path'])==binding['predictions']['sha256']
    predictions=lib.load(Path(binding['predictions']['path']));assert len(predictions)==200 and sum(p['status']=='POSE' for p in predictions)==17
    _,np=lib.runtime()
    import numpy.ma
    for name in ('ascii','cp437','utf-8','latin-1'):codecs.lookup(name)
    normalize=kernel.load(np,lib.ROOT,source_binding)
    lib.read_gate([e['path'] for e in binding['raw']+binding['calibrations']],OUT)
    raw={(e['sequence'],e['frame']):e for e in binding['raw']};calibrations={}
    for item in binding['calibrations']:
        assert lib.sha(item['path'])==item['sha256'];values={}
        for line in Path(item['path']).read_text(encoding='ascii').splitlines():
            key,value=line.split(':',1);values[key]=[float(v) for v in value.split()]
        tr=np.eye(4);tr[:3]=np.asarray(values['Tr']).reshape(3,4);calibrations[item['sequence']]=tr
    rows=[];cases=[];decimal_checks=0;point_occurrences=0
    for pred in predictions:
        record={k:pred[k] for k in ('key','sequence','source_i','source_j')}
        if pred['status']!='POSE':
            rows.append({**record,'status':'NO_CAMERA_INITIALIZER','cases':[]});continue
        clouds=[]
        for frame in (pred['source_j'],pred['source_i']):
            item=raw[(pred['sequence'],frame.zfill(6))];payload=Path(item['path']).read_bytes()
            assert len(payload)==item['bytes'] and lib.hashlib.sha256(payload).hexdigest()==item['sha256']
            points=np.frombuffer(payload,dtype='<f4').reshape(-1,4)[:,:3]
            assert len(points)>=4000 and np.isfinite(points).all();clouds.append(points);point_occurrences+=len(points)
        tr=calibrations[pred['sequence']];q=np.eye(4);q[:3,:3]=pred['R_i_to_j'];q[:3,3]=pred['t_i_to_j_m']
        raw_affine=np.linalg.solve(tr,q@tr);assert np.isfinite(raw_affine).all();delta=raw_affine[:3,3].copy()
        paircases=[];indices_to_save={}
        for name,ntarget,nsource in (('target_anchor',4000,3999),('source_anchor',3999,4000)):
            target_ids=np.linspace(0,len(clouds[0])-1,ntarget,dtype=np.int64);source_ids=np.linspace(0,len(clouds[1])-1,nsource,dtype=np.int64)
            assert len(np.unique(target_ids))==ntarget and len(np.unique(source_ids))==nsource
            parts=[clouds[0][target_ids],clouds[1][source_ids]]
            indices_to_save[name+'_target_ids']=target_ids;indices_to_save[name+'_source_ids']=source_ids
            for quantized in (False,True):
                result,states=kernel.compare(np,normalize,parts,delta,quantized)
                assert result['primary_part']==(0 if name=='target_anchor' else 1)
                base,changed,c0,c1,s0,s1,shifted=states
                with localcontext() as context:
                    context.prec=60
                    for values,centers,scale,actual in ((parts,c0,s0,base),(shifted,c1,s1,changed)):
                        stacked=np.concatenate(values).astype(np.float64);offset=len(values[0])
                        for index in sorted({0,len(stacked)//3,2*len(stacked)//3,len(stacked)-1}):
                            part=0 if index<offset else 1
                            for coord in range(3):
                                exact=(Decimal.from_float(float(stacked[index,coord]))-Decimal.from_float(float(centers[part][coord])))/Decimal.from_float(float(scale))
                                error=abs(exact-Decimal.from_float(float(actual[index,coord])))
                                assert error<=Decimal.from_float(result['representation_budget']);decimal_checks+=1
                result.update(key=pred['key'],count_branch=name);paircases.append(result);cases.append(result)
        with (OUT/(pred['key']+'.npz')).open('xb') as f:np.savez(f,**indices_to_save)
        rows.append({**record,'status':'SOURCE_NORMALIZATION_AUDITED','derived_raw_translation':delta.tolist(),
            'raw_affine_rotation_orthogonality_deviation':float(np.max(np.abs(raw_affine[:3,:3].T@raw_affine[:3,:3]-np.eye(3)))),
            'cases':paircases})
    assert len(rows)==200 and len(cases)==68
    lib.save(OUT/'ROWS.json',rows)
    groups=[]
    for quantized in (False,True):
        data=[r for r in cases if r['quantized_source_float32']==quantized]
        groups.append({'quantized_source_float32':quantized,'cases':len(data),'byte_equal_cases':sum(r['condition_byte_equal'] for r in data),
            'maximum_condition_difference':max(r['max_condition_difference'] for r in data),
            'maximum_scale_difference':max(r['scale_difference'] for r in data),
            'maximum_closed_form_error':max(r['independent_closed_form_error'] for r in data),
            'maximum_budget_use_ratio':max(r['max_condition_difference']/r['representation_budget'] for r in data)})
    lib.save(OUT/'SUMMARY.json',{'groups':groups,'role':'Source-bound conditional translation-centering audit, not actual preprocessor/model/pipeline invariance or efficacy'})
    lib.complete(OUT,{'complete_pair_slots':200,'actual_camera_initializers':17,'metamorphic_cases':68,'raw_point_occurrences_read':point_occurrences,
        'Decimal60_normalization_scalar_checks':decimal_checks,'model_or_registration_or_reference_calls':0,
        'actual_voxel_features_or_full_pipeline_invariance_claimed':False})
    print('PT1 complete68 source-kernel cases,all200 slots,no model')
except BaseException as error:
    lib.failure(OUT,error);raise
