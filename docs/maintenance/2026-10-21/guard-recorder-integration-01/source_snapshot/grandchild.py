import json, os, signal, sys, time
from pathlib import Path
folder = Path(sys.argv[1])
(folder / 'grandchild_owned.json').write_text(json.dumps(dict(pid=os.getpid(), pgid=os.getpgid(0))))
signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
try:
    time.sleep(60)
finally:
    (folder / 'grandchild_exit.json').write_text(json.dumps(dict(pid=os.getpid(), exited=True)))
