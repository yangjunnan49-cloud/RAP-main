"""Isolated fixed request routing; never invoke a pickle/checkpoint loader."""
from pathlib import Path
from fixed_state import decode_archive,path
def validate_request(filename,args,kwargs,weights,next_index,allowed_target='cpu'):
    if args or set(kwargs)!={'map_location','weights_only'} or kwargs['weights_only'] is not False:raise ValueError('unexpected_checkpoint_arguments')
    target=str(kwargs['map_location'])
    if target not in ('cpu',allowed_target):raise ValueError('unadmitted_map_target')
    p=Path(filename).resolve();matches=[i for i,row in enumerate(weights) if p==path(row['path']).resolve()]
    if len(matches)!=1 or matches[0]!=next_index:raise ValueError('checkpoint_path_order_or_replay')
    return matches[0]
def format_state(index,decoded):
    return {'state_dict':decoded} if index==0 else {'Desc.'+k:v for k,v in decoded.items()}
class FixedTensorBridge:
    def __init__(self,weights,inventory,archives,torch,capture_rng,allowed_target='cpu'):
        self.weights=weights;self.inventory=inventory;self.archives=archives;self.torch=torch;self.capture_rng=capture_rng;self.allowed_target=allowed_target
        self.calls=[];self.expected_hashes={}
    def __call__(self,filename,*args,**kwargs):
        index=validate_request(filename,args,kwargs,self.weights,len(self.calls),self.allowed_target)
        before=self.capture_rng('load'+str(index)+'_before')
        row=dict(index=index,path=str(filename),map_location=str(kwargs['map_location']),source_weights_only=False,original_torch_load_executed=False)
        self.calls.append(row)
        try:
            decoded,hashes,info=decode_archive(self.weights[index],self.inventory[index],self.archives[index],self.torch,descriptor_only=index==1)
            after=self.capture_rng('load'+str(index)+'_after')
            assert before['Torch_CPU_sha256']==after['Torch_CPU_sha256'] and before['NumPy_sha256']==after['NumPy_sha256']
            self.expected_hashes[index]=hashes
            row.update(success=True,tensors=len(decoded),archive=info,tracked_RNG_unchanged=True)
            return format_state(index,decoded)
        except BaseException as error:row.update(success=False,error=repr(error));raise
