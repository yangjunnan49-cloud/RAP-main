import codecs
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import baseline_lib as lib
import kernel

OUT=lib.ROOT/'controls'
try:
    lib.verify_freeze('controls');binding=lib.load(lib.ROOT/'SOURCE_BINDING.json');_,np=lib.runtime()
    import numpy.ma
    for name in ('ascii','cp437','utf-8','latin-1'):codecs.lookup(name)
    normalize=kernel.load(np,lib.ROOT,binding)
    cache=OUT/'cold.npy';lib.read_gate([cache],OUT)
    shape=np.array([[x,y,z] for x in (-1.,1.) for y in (-1.,1.) for z in (-1.,1.)],dtype=np.float32)
    shape[-1,2]=2.;target=shape+np.array([.25,-.5,.75],dtype=np.float32);delta=np.array([2.,-1.,.5])
    records=[]
    for parts in ([target,shape[:7]],[target[:7],shape]):
        for quantized in (False,True):
            record,_=kernel.compare(np,normalize,parts,delta,quantized);records.append(record)
    assert {r['primary_part'] for r in records}=={0,1}
    base,_,_,_,_=normalize([target,shape])
    turned=shape[:,[1,0,2]].copy();turned[:,0]*=-1
    rotation_cond,_,_,_,_=normalize([target,turned])
    assert float(np.max(np.abs(base-rotation_cond)))>.01
    with cache.open('xb') as f:np.save(f,shape,allow_pickle=False)
    assert np.array_equal(np.load(cache,allow_pickle=False),shape)
    denied=False
    try:(lib.ROOT/'INPUT_BINDING.json').read_bytes()
    except PermissionError:denied=True
    assert denied
    lib.complete(OUT,{'source_AST_exact':True,'metamorphic_cases':records,'both_anchor_branches':True,'cold_array_and_read_gate':True,
        'nontranslation_changes_coordinates':True,'raw_model_or_reference_calls':0})
    print('PT1 source-bound controls PASS')
except BaseException as error:
    lib.failure(OUT,error);raise
