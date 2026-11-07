import atexit,json,os,resource,runpy,sys,threading,time,traceback
from pathlib import Path
receipt=Path(sys.argv[1]);target=sys.argv[2];args=sys.argv[2:];start=time.monotonic();done=False
def peaks(complete):
 t=sys.modules.get('torch');allocated=reserved=0
 if t is not None and t.cuda.is_initialized():allocated=t.cuda.max_memory_allocated();reserved=t.cuda.max_memory_reserved()
 return {'complete':complete,'wall_s':time.monotonic()-start,'rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,'gpu_allocated_bytes':allocated,'gpu_reserved_bytes':reserved}
def finish():
 with receipt.open('x') as f:json.dump(peaks(done),f)
atexit.register(finish)
def guard():
 host=receipt.parent/'supervision/host_latest.json'
 while True:
  time.sleep(1);p=peaks(False)
  try:
   h=json.loads(host.read_text());assert h['headroom_bytes']>=4*2**30
   assert p['rss_bytes']<=12*2**30 and max(p['gpu_allocated_bytes'],p['gpu_reserved_bytes'])<=4*2**30
  except (AssertionError,):
   with receipt.open('x') as f:json.dump(p,f)
   os._exit(137)
  except (OSError,ValueError):pass
threading.Thread(target=guard,daemon=True).start()
sys.argv=args
sys.path.insert(0,str(Path(target).resolve().parent))
try:runpy.run_path(target,run_name='__main__');done=True
except SystemExit as e:
 done=e.code in (None,0);raise
