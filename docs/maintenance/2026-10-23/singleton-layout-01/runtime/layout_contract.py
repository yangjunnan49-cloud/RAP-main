"""Future layout predicate only; no files, tensor libraries or transfer API."""
import math
def row_major_storage(shape,stride,elements,offset=0):
    if not isinstance(shape,(list,tuple)) or not isinstance(stride,(list,tuple)) or len(shape)!=len(stride) or len(shape)>8:return False
    if any(type(d)is not int or d<=0 for d in shape) or any(type(s)is not int or s<0 for s in stride):return False
    if type(elements)is not int or elements!=math.prod(shape) or type(offset)is not int or offset!=0:return False
    expected=1
    for d,s in zip(reversed(shape),reversed(stride)):
        if d>1 and s!=expected:return False
        expected*=d
    return True
