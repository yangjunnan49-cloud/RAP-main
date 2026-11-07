from pathlib import Path
import hashlib,json,os,signal,subprocess,time
BASE=Path(__file__).resolve().parent/'attempt02'
capture=str(BASE/'child_capture.py')
f=BASE/'external_guard_freeze.json'
assert json.loads(f.read_text())['sha256']==hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
start=time.monotonic();observations=0
while time.monotonic()-start<7500 and not (BASE/'execution.json').exists():
 host=json.loads((BASE/'supervision/host_latest.json').read_text())
 targets=[]
 for p in Path('/proc').iterdir():
  if not p.name.isdigit():continue
  try:
   args=(p/'cmdline').read_bytes().decode().split('\0')
   if capture not in args:continue
   assert any(a.startswith(str(BASE)+'/r') and a.endswith('.resource.json') for a in args)
   status=(p/'status').read_text();peak=int(next(s.split()[1] for s in status.splitlines() if s.startswith('VmHWM:')))*1024
   targets.append((int(p.name),peak))
  except (FileNotFoundError,PermissionError,StopIteration):continue
 gpu={}
 try:
  out=subprocess.check_output(['/usr/lib/wsl/lib/nvidia-smi','--query-compute-apps=pid,used_gpu_memory','--format=csv,noheader,nounits'],text=True,stderr=subprocess.DEVNULL,timeout=5)
  for line in out.strip().splitlines():
   a,b=line.split(',');gpu[int(a.strip())]=int(b.strip())*2**20
 except (OSError,ValueError,subprocess.SubprocessError):pass
 for pid,rss in targets:
  row={'unix_time':time.time(),'pid':pid,'rss_high_water_bytes':rss,'nvidia_process_gpu_bytes':gpu.get(pid),'host_headroom_bytes':host['headroom_bytes']}
  with (BASE/'external_guard.jsonl').open('a') as out:out.write(json.dumps(row)+'\n')
  observations+=1
  if rss>12*2**30 or host['headroom_bytes']<4*2**30 or (gpu.get(pid,0)>4*2**30):
   (BASE/'EXTERNAL_GUARD_STOP.json').open('x').write(json.dumps(row));os.kill(pid,signal.SIGTERM);raise RuntimeError('Scoped child cap guard stopped target')
 time.sleep(.5)
(BASE/'external_guard_completion.json').open('x').write(json.dumps({'observations':observations,'wall_s':time.monotonic()-start,'scope':'external /proc high-water and host guard; final child CUDA peaks are authoritative'}))
