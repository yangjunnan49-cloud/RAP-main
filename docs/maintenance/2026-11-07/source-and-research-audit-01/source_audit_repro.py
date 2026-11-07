import ast, pathlib, random, itertools, json, hashlib, typing
source=pathlib.Path(__file__).resolve().parent/'source/RAP-main/rectified_point_flow/data/datamodule.py'
tree=ast.parse(source.read_text()); names={'DynamicBatchSampler','RandomSampledDataset'}
class Sampler:
 def __class_getitem__(cls,item):return cls
class Dist:
 rank=0;world_size=2
 def is_initialized(self):return True
 def get_rank(self):return self.rank
 def get_world_size(self):return self.world_size
class Dataset:
 def __init__(self,sizes):self.sizes=sizes
 def __len__(self):return len(self.sizes)
 def estimate_num_points(self,i):return self.sizes[i]
 def __getitem__(self,i):return i
namespace={'Sampler':Sampler,'ConcatPointCloudDataset':Dataset,'Dataset':Dataset,'dist':Dist(),'random':random,'Optional':typing.Optional}
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.ClassDef) and n.name in names],type_ignores=[]),str(source),'exec'),namespace)
results={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest()}
for drop in [True,False]:
 found=None
 for n in range(4,9):
  for sizes in itertools.product([2000,4000,6000,8000],repeat=n):
   sampler=namespace['DynamicBatchSampler'](Dataset(sizes),max_points_per_batch=10000,shuffle=True,drop_last=drop,seed=0)
   batches=[];lens=[]
   for rank in [0,1]:
    namespace['dist'].rank=rank;batches.append(list(sampler));lens.append(len(sampler))
   if len(batches[0])!=len(batches[1]):
    found={'sizes':sizes,'max_points':10000,'seed':0,'shuffle':True,'drop_last':drop,'len_reported_by_rank':lens,'batches_by_rank':batches,'actual_steps_by_rank':[len(b) for b in batches]};break
  if found:break
 results['ddp_drop_last_'+str(drop)]=found
sampled=namespace['RandomSampledDataset'](Dataset(list(range(20))),num_samples=5,seed=42)
rows=[]
for epoch in range(4):
 sampled.set_epoch(epoch);rows.append({'epoch':epoch,'indices':sampled._current_indices[:]})
results['random_subset_by_epoch']=rows
namespace['dist'].world_size=1
namespace['dist'].rank=0
sampler=namespace['DynamicBatchSampler'](Dataset([5000,5000]),max_points_per_batch=10000,shuffle=False)
results['validation_default_full_final_batch']={'sizes':[5000,5000],'max_points':10000,'default_drop_last':sampler.drop_last,'actual_batches':list(sampler),'reported_len':len(sampler)}
print(json.dumps(results,indent=2))
(pathlib.Path(__file__).resolve().parent/'source_audit_repro.json').write_text(json.dumps(results,indent=2))
