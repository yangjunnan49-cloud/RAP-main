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
    timeout=6940-(time.monotonic()-start);assert timeout>0
    receipt=BASE/f'{name}.resource.json'
    payload=cmd[2:] if model=='RAP-SLAM' else [KISS,*cmd[1:]]
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
    assert row['resource']['rss_bytes']<=18*2**30 and row['resource']['gpu_allocated_bytes']<=6*2**30 and row['resource']['gpu_reserved_bytes']<=10*2**30
    if model=='RAP-SLAM':assert not (dest/'INCOMPLETE').exists()
    else:assert len(list(dest.rglob(f'{seq}_poses_kitti.txt')))==1
    assert sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file())<20*2**30
 save(BASE/'execution.json',{'rows':rows,'wall_s':time.monotonic()-start,'complete_runs':len(rows),'unix_end':time.time()})
 verify(raw=True);print('All 36 trajectories complete; separate evaluation pending',flush=True)
