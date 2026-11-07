"""Restricted nonexecuting opcode metadata interpreter; never deserialize globals."""
import math
import pickletools
class Symbol:
    def __init__(self,name):self.name=name
class Node:
    def __init__(self,kind,call=None,args=None):
        self.kind=kind;self.call=call;self.args=args;self.items={};self.state=None
MARK=object()
def parse(raw):
    if len(raw)>8*2**20:raise ValueError('metadata_size_cap')
    stack=[];memo={};count=0;stopped=False
    def popmark():
        for i in range(len(stack)-1,-1,-1):
            if stack[i] is MARK:
                result=stack[i+1:];del stack[i:];return result
        raise ValueError('missing_mark')
    def put(target,values):
        mapping=target.items if isinstance(target,Node) else target
        if not isinstance(mapping,dict) or len(values)%2:raise ValueError('invalid_mapping')
        for i in range(0,len(values),2):
            k,v=values[i:i+2]
            if k in mapping:raise ValueError('duplicate_mapping_key')
            mapping[k]=v
    try:
        for op,arg,pos in pickletools.genops(raw):
            count+=1;n=op.name
            if count>200000 or len(stack)>20000 or len(memo)>20000:raise ValueError('symbolic_resource_cap')
            if n in ('PROTO','FRAME'):continue
            if n=='MARK':stack.append(MARK)
            elif n=='EMPTY_DICT':stack.append({})
            elif n=='EMPTY_LIST':stack.append([])
            elif n=='EMPTY_TUPLE':stack.append(())
            elif n=='NONE':stack.append(None)
            elif n=='NEWTRUE':stack.append(True)
            elif n=='NEWFALSE':stack.append(False)
            elif n in ('BINUNICODE','SHORT_BINUNICODE','UNICODE','STRING','BINSTRING','SHORT_BINSTRING','BINBYTES','SHORT_BINBYTES','INT','BININT','BININT1','BININT2','LONG','LONG1','LONG4','FLOAT','BINFLOAT'):stack.append(arg)
            elif n=='GLOBAL':stack.append(Symbol(arg))
            elif n=='STACK_GLOBAL':
                name=stack.pop();module=stack.pop()
                if not isinstance(name,str) or not isinstance(module,str):raise ValueError('invalid_global_symbol')
                stack.append(Symbol(module+' '+name))
            elif n in ('BINPUT','LONG_BINPUT','PUT'):
                key=int(arg)
                if key in memo:raise ValueError('duplicate_memo')
                memo[key]=stack[-1]
            elif n=='MEMOIZE':memo[len(memo)]=stack[-1]
            elif n in ('BINGET','LONG_BINGET','GET'):stack.append(memo[int(arg)])
            elif n=='TUPLE':stack.append(tuple(popmark()))
            elif n in ('TUPLE1','TUPLE2','TUPLE3'):
                size=int(n[-1]);values=stack[-size:];del stack[-size:];stack.append(tuple(values))
            elif n=='LIST':stack.append(popmark())
            elif n=='DICT':
                values=popmark();target={};put(target,values);stack.append(target)
            elif n=='SETITEMS':values=popmark();put(stack[-1],values)
            elif n=='SETITEM':
                value=stack.pop();key=stack.pop();put(stack[-1],[key,value])
            elif n=='APPENDS':
                values=popmark()
                if not isinstance(stack[-1],list):raise ValueError('invalid_list')
                stack[-1].extend(values)
            elif n=='APPEND':
                value=stack.pop()
                if not isinstance(stack[-1],list):raise ValueError('invalid_list')
                stack[-1].append(value)
            elif n in ('REDUCE','NEWOBJ'):
                args=stack.pop();call=stack.pop()
                if not isinstance(args,tuple):raise ValueError('invalid_symbolic_arguments')
                stack.append(Node(n,call,args))
            elif n=='BUILD':
                state=stack.pop()
                if not isinstance(stack[-1],Node):raise ValueError('invalid_symbolic_BUILD')
                stack[-1].state=state
            elif n=='BINPERSID':stack.append(Node('persistent',args=stack.pop()))
            elif n=='POP':stack.pop()
            elif n=='POP_MARK':popmark()
            elif n=='DUP':stack.append(stack[-1])
            elif n=='STOP':
                if len(stack)!=1 or pos+1!=len(raw):raise ValueError('invalid_STOP_or_trailing_data')
                stopped=True;break
            else:raise ValueError('unsupported_opcode:'+n)
    except (IndexError,KeyError,TypeError) as e:raise ValueError('invalid_symbolic_stack_or_memo') from e
    if not stopped:raise ValueError('missing_STOP')
    return stack[0]
def mapping(obj):
    if isinstance(obj,dict):return obj
    if isinstance(obj,Node) and isinstance(obj.call,Symbol) and obj.call.name=='collections OrderedDict':return obj.items
    raise ValueError('not_state_mapping')
DTYPES={'torch FloatStorage':('torch.float32',4),'torch DoubleStorage':('torch.float64',8),'torch LongStorage':('torch.int64',8),'torch IntStorage':('torch.int32',4),'torch ByteStorage':('torch.uint8',1),'torch HalfStorage':('torch.float16',2),'torch BoolStorage':('torch.bool',1)}
def tensor_metadata(obj,storage_bytes):
    if not isinstance(obj,Node) or obj.kind!='REDUCE' or not isinstance(obj.call,Symbol) or obj.call.name!='torch._utils _rebuild_tensor_v2':raise ValueError('unsupported_tensor_rebuild')
    storage,offset,shape,stride,requires_grad,hooks=obj.args
    if not isinstance(storage,Node) or storage.kind!='persistent' or len(storage.args)!=5:raise ValueError('invalid_storage_reference')
    tag,kind,key,location,elements=storage.args
    if tag!='storage' or not isinstance(kind,Symbol) or kind.name not in DTYPES or not isinstance(key,str) or not key.isdecimal():raise ValueError('invalid_storage_type')
    dtype,width=DTYPES[kind.name]
    if type(elements)is not int or elements<0 or storage_bytes.get(key)!=elements*width:raise ValueError('storage_byte_length_mismatch')
    if not isinstance(shape,tuple) or not isinstance(stride,tuple) or len(shape)!=len(stride) or len(shape)>8:raise ValueError('invalid_tensor_rank')
    if any(type(x)is not int or x<0 for x in shape+stride) or type(offset)is not int or offset<0:raise ValueError('invalid_tensor_dimensions')
    count=math.prod(shape)
    last=offset+sum((d-1)*s for d,s in zip(shape,stride)) if count else offset-1
    if last>=elements or offset>elements:raise ValueError('storage_range_exceeded')
    return dict(shape=list(shape),stride=list(stride),dtype=dtype,elements=count,storage=key,storage_elements=elements,storage_offset=offset,serialized_location=location)
