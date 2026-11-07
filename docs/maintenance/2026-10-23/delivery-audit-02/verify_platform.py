"""Compare fresh read-only platform receipts to the earlier context review."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
old=json.loads((ROOT.parent/'context-wsl-review-01/LIVE_CHECKS.json').read_text())
git=json.loads((ROOT.parent/'context-wsl-review-01/GIT_STATE.json').read_text())
new=json.loads((ROOT/'PLATFORM_CHECKS.json').read_text())
assert new['registration']['BasePath']=='E:\\WSL\\Ubuntu-24.04'
assert new['registration']['DefaultUid']==1000 and new['registration']['Version']==2
assert new['junction']['type']=='Junction' and new['junction']['target']=='E:\\WSL\\Ubuntu-24.04'
assert new['file_id_E']==new['file_id_C_compatibility']
assert new['WSL_list_exit']==0 and 'Stopped' in new['WSL_listing'] and 'Running' not in new['WSL_listing']
assert new['RAP_main_HEAD']==git[0]['head'] and new['RAP_SLAM_HEAD']==git[1]['head']
backup=next(x for x in old['storage'] if 'WSL-Backup' in x['FullName'])
assert new['backup']['bytes']==backup['Length'] and new['backup']['LastWriteTimeUtc']==backup['LastWriteTimeUtc']
hashes=[v for v in old['wslconfig'].values() if isinstance(v,str) and len(v)==64]
assert new['wslconfig_sha256'] in hashes
with (ROOT/'PLATFORM_COMPARISON.json').open('x') as f:json.dump(dict(passed=True,selected_registration_matches=True,same_physical_active_file=True,compatibility_junction_retained=True,backup_metadata_unchanged=True,backup_full_hash_repeated=False,wslconfig_hash_matches=True,local_HEADs_unchanged=True,WSL_stopped=True,direct_boot_without_junction_tested=False,stale_reference_cause='UNKNOWN'),f,indent=2)
print('Platform comparison PASS')
