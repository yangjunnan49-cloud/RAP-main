"""Stop only the independently identified validation process group."""
import sys,json,os,signal,hashlib
from pathlib import Path
p=Path(sys.argv[1]);owned=json.loads(p.read_text());pid=owned['pid'];proc=Path(f'/proc/{pid}')
if not proc.exists():print('Owned process already exited');sys.exit(0)
tick=(proc/'stat').read_text().rsplit(')',1)[1].split()[19]
assert tick==owned['start_ticks'] and os.getpgid(pid)==owned['pgid']==pid
cmd=(proc/'cmdline').read_bytes();script=Path(__file__).with_name('validation_stage02.py')
assert str(script).encode() in cmd and hashlib.sha256(script.read_bytes()).hexdigest()==owned['script_sha256']
os.killpg(pid,signal.SIGTERM);print('Stopped exact owned validation group',pid)

