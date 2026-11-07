"""Fixed contiguous storage decoder, with no pickle or checkpoint object loading."""
import hashlib,math,sys
from layout_contract import row_major_storage
DTYPES={'torch.float32':('float32',4),'torch.float64':('float64',8),'torch.int64':('int64',8),'torch.uint8':('uint8',1)}
def byte_hash(raw):
    h=hashlib.sha256();v=memoryview(raw)
    for i in range(0,len(v),1024*1024):h.update(v[i:i+1024*1024])
    return h.hexdigest().upper()
def decode(raw,meta,expected_hash,torch):
    if sys.byteorder!='little':raise ValueError('host_byteorder')
    if len(raw)>64*2**20 or byte_hash(raw)!=expected_hash:raise ValueError('storage_hash_or_size_cap')
    if meta['dtype'] not in DTYPES:raise ValueError('unsupported_dtype')
    shape=meta['shape'];stride=meta['stride'];count=math.prod(shape)
    if any(type(x)is not int or x<=0 for x in shape) or meta['storage_offset']!=0 or meta['storage_elements']!=count or meta['elements']!=count:raise ValueError('nonzero_offset_or_view_layout')
    if not row_major_storage(shape,stride,count,meta['storage_offset']):raise ValueError('unsupported_row_major_layout')
    name,width=DTYPES[meta['dtype']]
    if len(raw)!=count*width:raise ValueError('storage_byte_length')
    a=torch.frombuffer(bytearray(raw),dtype=getattr(torch,name)).reshape(shape)
    if a.is_floating_point() and not torch.isfinite(a).all():raise ValueError('nonfinite_weight')
    return a
def tensor_hash(a):
    if a.device.type!='cpu' or not a.is_contiguous():raise ValueError('loaded_tensor_layout')
    raw=memoryview(a.detach().numpy()).cast('B')
    return byte_hash(raw)
