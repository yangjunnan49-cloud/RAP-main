"""RPC0 final read-only Git/handoff bookkeeping; no numerical imports."""
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

root=Path(__file__).resolve().parents[2]
base=root/'docs/maintenance/2026-10-12/reference-physical-consistency-01'
frozen=json.loads((base/'freeze.json').read_text()); actual={}
for name,path in [('main',root),('slam',root.parent/'RAP-SLAM')]:
    def git(*args): return subprocess.check_output(['git','--no-optional-locks','-C',str(path),*args],text=True).strip()
    actual[name]=dict(head=git('rev-parse','HEAD'),branch=git('branch','--show-current'),tracked_status=git('status','--short','--untracked-files=no').splitlines())
assert actual==frozen['repositories']
markers=[root/'docs/maintenance/2026-10-10/native-conditioned-comparison-01/INCOMPLETE',root/'docs/maintenance/2026-10-10/native-conditioned-comparison-01/attempt-02/INCOMPLETE']
assert all(p.exists() for p in markers) and not (base/'INCOMPLETE').exists()
value=dict(utc=datetime.now(timezone.utc).isoformat(),passed=True,repositories=actual,old_NOC4_markers_preserved=True,new_RPC0_marker_closed=True,
    Windows_sibling_status_limitation='HEAD/branch read succeeds; status reports must be run in work tree; fresh WSL status matches original freeze',
    final_command_preparation_failure='Nested PowerShell/Python quoting caused SyntaxError before any statement executed; corrected standalone standard-library helper',
    helper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),new_raw_model_optimizer_calls=0,commit_or_sync=False)
path=root/'docs/maintenance/2026-10-12/RPC0_FINAL_HANDOFF_CHECK.json'
with path.open('x') as f: json.dump(value,f,indent=2); f.write('\n')
print(json.dumps(value,indent=2))
