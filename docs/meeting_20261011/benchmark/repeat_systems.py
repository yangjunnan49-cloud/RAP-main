from pathlib import Path
import hashlib,json,os,subprocess,sys,time,traceback,zipfile
MAIN=Path(__file__).resolve().parents[3]
BASE=Path(__file__).resolve().parent
SLAM=MAIN.parent/'RAP-SLAM'
DATA=MAIN.parent/'Datasets/data_odometry_velodyne/dataset'
E0=MAIN/'docs/maintenance/2026-09-26/e0-frontend-01'
H1=MAIN/'docs/maintenance/2026-09-27/e0-heldout-01'
HC=MAIN/'docs/maintenance/2026-09-19/horizontal-comparison-01/b-kiss-slam'
COUNTS={'00':4541,'05':2761,'06':1101,'07':1101,'09':1591,'10':1201}
KISS='/root/venvs/kiss-slam-hc1/bin/kiss_slam_pipeline'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(p,x):
 with Path(p).open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False)
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(2**20),b''):h.update(b)
 return h.hexdigest()
def freeze():
 sources=dict(read(E0/'freeze.json')['sources'])
 inputs=dict(read(E0/'freeze.json')['inputs'])
 inputs.update(read(H1/'freeze.json')['inputs'])
 for p,h in sources.items():assert sha(p)==h,('historical source changed',p)
 for p,h in inputs.items():assert sha(p)==h,('historical input changed',p)
 current=subprocess.check_output(['/root/venvs/kiss-slam-hc1/bin/pip','freeze'],text=True)
 assert current.strip().splitlines()==(HC/'env/pip_freeze.txt').read_text().strip().splitlines(),'KISS environment changed'
 extras=[Path(__file__),BASE/'child_capture.py',BASE/'PROTOCOL.md',E0/'command-00.json',HC/'config/default_config.yaml',HC/'env/pip_freeze.txt',MAIN/'scripts/maintenance/invoke_supervised_wsl_current.ps1']
 sources.update({str(p):sha(p) for p in extras})
 save(BASE/'freeze.json',{'sources':sources,'inputs':inputs,'repetitions':3,'counts':COUNTS,'unix_time':time.time()})
 with zipfile.ZipFile(BASE/'source_snapshot.zip','x',zipfile.ZIP_DEFLATED) as z:
  for p in sources:
   if Path(p).suffix in ['.py','.ps1','.md','.yaml','.json']:z.write(p,str(Path(p).relative_to(MAIN.parent)))
 print('Frozen sources',len(sources),'inputs',len(inputs),flush=True)
def verify(raw=False):
 d=read(BASE/'freeze.json')
 for group in (['sources','inputs'] if raw else ['sources']):
  for p,h in d[group].items():assert sha(p)==h,p
def run():
 verify();(BASE/'INCOMPLETE').write_text('36-run benchmark pending validation\n')
 start=time.monotonic();rows=[]
 for rep in range(1,4):
  for seq,n in COUNTS.items():
   for model in ['RAP-SLAM','KISS-SLAM']:
    verify();name=f'r{rep:02d}-{seq}-{model}';dest=BASE/name
    if model=='RAP-SLAM':
     cmd=read(E0/'command-00.json')
     for opt,val in [('--output',str(dest)),('--real-seq',seq),('--real-end',str(n-1))]:cmd[cmd.index(opt)+1]=val
     cwd=SLAM
    else:
     dest.mkdir(exist_ok=False);cmd=[KISS,str(DATA),'--dataloader','kitti','--sequence',seq];cwd=dest
    timeout=7200-(time.monotonic()-start);assert timeout>0
    receipt=BASE/f'{name}.resource.json'
    payload=cmd[1:] if model=='RAP-SLAM' else [KISS,*cmd[1:]]
    wrapped=[cmd[0] if model=='RAP-SLAM' else '/root/venvs/kiss-slam-hc1/bin/python','-u','-B',str(BASE/'child_capture.py'),str(receipt),*payload]
    save(BASE/f'{name}.command.json',{'target':cmd,'wrapper':wrapped,'cwd':str(cwd)})
    print('START',name,flush=True);t=time.monotonic()
    with (BASE/f'{name}.stdout.log').open('x') as out,(BASE/f'{name}.stderr.log').open('x') as err:
     result=subprocess.run(wrapped,cwd=cwd,stdout=out,stderr=err,timeout=timeout)
    row={'name':name,'rep':rep,'sequence':seq,'model':model,'exit':result.returncode,'wall_s':time.monotonic()-t,'resource':read(receipt) if receipt.exists() else None}
    rows.append(row)
    with (BASE/'ledger.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
    print('END',name,'exit',result.returncode,'wall',round(row['wall_s'],1),flush=True)
    assert result.returncode==0,row
    assert row['resource'] and row['resource']['complete']
    assert row['resource']['rss_bytes']<=12*2**30 and row['resource']['gpu_allocated_bytes']<=4*2**30 and row['resource']['gpu_reserved_bytes']<=4*2**30
    if model=='RAP-SLAM':assert not (dest/'INCOMPLETE').exists()
    else:assert len(list(dest.rglob(f'{seq}_poses_kitti.txt')))==1
    assert sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file())<20*2**30
 save(BASE/'execution.json',{'rows':rows,'wall_s':time.monotonic()-start,'complete_runs':len(rows),'unix_end':time.time()})
 verify(raw=True);print('All 36 trajectories complete; separate evaluation pending',flush=True)
if __name__=='__main__':
 try:{'freeze':freeze,'run':run}[sys.argv[1]]()
 except BaseException:
  with (BASE/f'FAILURE-{sys.argv[1]}-{time.time_ns()}.txt').open('x') as f:f.write(traceback.format_exc())
  raise
