import gc, hashlib, json, resource, sys, time, tracemalloc
from pathlib import Path
import numpy as np
from stream_hash import array,CHUNK
from original_codec import describe
folder=Path(sys.argv[1]);start=time.monotonic();checks=[];ok=False;error=None


def check(name,value,multiset=False):
    expected=hashlib.sha256(value.tobytes(order='C')).hexdigest()
    tracemalloc.start();tracemalloc.reset_peak()
    result=array(value,'output',multiset)
    current,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
    assert peak<=16*2**20,(name,'scratch',peak)
    assert result['sha256']==expected,(name,'hash mismatch')
    assert result['shape']==list(value.shape) and result['strides']==list(value.strides)
    assert hashlib.sha256(value.tobytes(order='C')).hexdigest()==expected,'input mutated'
    checks.append(dict(name=name,passed=True,nbytes=value.nbytes,shape=list(value.shape),
        scratch_peak_bytes=peak,sha256=expected,secondary=result.get('row_multiset_status','available_or_not_requested')))


try:
    base=np.arange(128*256,dtype=np.float64).reshape(128,256)
    for name,value in [('C',base),('Fortran',np.asfortranarray(base)),('transpose',base.T),
        ('reverse',base[::-1,::-1]),('stride',base[::3,::2]),('big_endian',base.astype('>f8')),
        ('big_endian_strided',base.astype('>f8')[::2,::-1]),('empty',np.empty((0,3),np.float32)),
        ('scalar',np.asarray(3.25)),('integer',np.arange(100,dtype=np.int64)),('boolean',np.asarray([True,False]))]:
        check(name,value)
    del value
    large=np.arange(841107*3,dtype=np.float64).reshape(841107,3)
    check('N1_size_contiguous',large,True)
    check('N1_size_Fortran',np.asfortranarray(large),True)
    check('N1_size_reverse',large[::-1,::-1],True)
    original_rejected=False
    try:describe(large.tobytes(),'f8',list(large.shape),'little',list(large.strides),'input')
    except ValueError:original_rejected=True
    assert original_rejected
    checks.append(dict(name='original16MiB_cap_still_rejects',passed=True,nbytes=large.nbytes))
    del large;gc.collect()
    largest=np.zeros((8192,1024),dtype=np.float64)
    check('64MiB_C',largest)
    check('64MiB_transpose',largest.T)
    del largest;gc.collect()
    small=np.arange(3000,dtype=np.float32).reshape(1000,3)
    a=array(small,'output',True);b=array(small[::-1],'output',True)
    assert a['sha256']!=b['sha256'] and a['row_multiset_sha256']==b['row_multiset_sha256']
    check('small_multiset_scratch',small,True)
    checks.append(dict(name='small_multiset_row_order_secondary_only',passed=True))
    oversized=np.zeros((64*2**20+1,),dtype=np.uint8)
    rejected=False
    try:array(oversized,'output')
    except ValueError:rejected=True
    assert rejected
    checks.append(dict(name='over64MiB_source_rejected',passed=True))
    rejected=False
    try:array(np.asarray(['unsupported'],dtype=object),'output')
    except ValueError:rejected=True
    assert rejected
    checks.append(dict(name='object_dtype_rejected',passed=True))
    ok=True
except BaseException as caught:
    error=repr(caught)
    import traceback;traceback.print_exc()
finally:
    (folder/'worker_exit.json').write_text(json.dumps(dict(success=ok,error=error,elapsed=time.monotonic()-start,
        checks=checks,count=len(checks),raw_reads=0,GT_reads=0,SLAM_native_imports=0,numpy_imported=True,new_predictions=0,
        max_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024),indent=2))
sys.exit(0 if ok else 2)
