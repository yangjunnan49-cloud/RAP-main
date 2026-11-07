"""Bounded exact-identity stop; deliberately rejects a forged start tick."""
import json,sys,os,signal,hashlib
from pathlib import Path
record=json.loads(Path(sys.argv[1]).read_text());pid=record['pid'];proc=Path(f'/proc/{pid}')
if not proc.exists():print('Original owned process already exited');sys.exit(0)
assert (proc/'stat').read_text().rsplit(')',1)[1].split()[19]==record['start_ticks'],'start_tick_mismatch'
assert os.getpgid(pid)==record['pgid']==pid,'group_mismatch'
script=Path(__file__).with_name('guard_child02.py').resolve()
assert record['script']==str(script) and hashlib.sha256(script.read_bytes()).hexdigest()==record['script_sha256']
assert str(script).encode() in (proc/'cmdline').read_bytes()
os.killpg(pid,signal.SIGTERM);print('Stopped exact owned synthetic group',pid)

