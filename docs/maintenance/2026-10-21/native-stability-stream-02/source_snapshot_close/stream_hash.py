"""Exact byte fingerprints with bounded scratch; no numerical algorithm intervention."""
import hashlib, math, sys
import numpy as np
SOURCE_CAP=64*2**20
CHUNK=2**20
MULTISET_CAP=2**20
KINDS={'f4','f8','i4','i8','u1','u4','u8','b1'}


def array(value,role,multiset=False):
    a=np.asarray(value)
    kind=a.dtype.kind+str(a.dtype.itemsize)
    if kind not in KINDS or a.ndim>4 or a.nbytes>SOURCE_CAP:
        raise ValueError('unsupported dtype/rank or source array cap')
    if role not in {'input','output','prepared','derived','state'}:
        raise ValueError('unsupported role')
    h=hashlib.sha256();materialized=0
    if a.size:
        if a.flags.c_contiguous:
            view=memoryview(a).cast('B')
            for offset in range(0,a.nbytes,CHUNK):
                h.update(view[offset:offset+CHUNK])
        else:
            elements=max(1,CHUNK//a.dtype.itemsize)
            iterator=np.nditer(a,flags=['external_loop','buffered','zerosize_ok'],
                              op_flags=['readonly'],order='C',buffersize=elements)
            for block in iterator:
                for offset in range(0,block.size,elements):
                    body=block[offset:offset+elements].tobytes(order='C')
                    assert len(body)<=CHUNK
                    materialized=max(materialized,len(body));h.update(body)
    endian='na' if a.dtype.itemsize==1 else 'little' if a.dtype.byteorder=='<' else 'big' if a.dtype.byteorder=='>' else sys.byteorder
    result=dict(dtype=kind,shape=list(a.shape),endian=endian,strides=list(a.strides),role=role,
                type='array',order='C_logical',nbytes=a.nbytes,sha256=h.hexdigest())
    if multiset:
        if a.ndim!=2:raise ValueError('row multiset requires matrix')
        if a.nbytes<=MULTISET_CAP:
            body=a.tobytes(order='C');width=a.shape[1]*a.dtype.itemsize
            rows=[body[i:i+width] for i in range(0,len(body),width)] if width else []
            result['row_multiset_sha256']=hashlib.sha256(b''.join(sorted(rows))).hexdigest()
        else:
            result['row_multiset_status']='OMITTED_OVER_1MIB'
    return result
