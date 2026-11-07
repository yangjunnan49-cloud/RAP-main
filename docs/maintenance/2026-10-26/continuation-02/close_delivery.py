"""Document-only final binding; no data, source execution, model or network API."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
BASE = HERE.parent

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(name, obj):
    (HERE / name).write_text(json.dumps(obj, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

scopes = [
    'appearance-source-feasibility-01', 'camera-contract-review-01',
    'kitti-camera-source-request-01', 'camera-support-upper-bound-01',
    'camera-strategy-reachability-01', 'camera-coupling-readiness-01',
]
verified = []
for scope in scopes:
    directory = BASE / scope
    seal = directory / 'DELIVERY_SEAL.json'
    obj = json.loads(seal.read_text(encoding='utf-8-sig'))
    entries = obj['files']
    for row in entries:
        p = directory / row['path']
        assert p.is_file(), str(p)
        assert p.stat().st_size == row['bytes'], str(p)
        assert sha(p).lower() == row['sha256'].lower(), str(p)
    checks = json.loads((directory / 'CLOSE_CHECKS.json').read_text(encoding='utf-8-sig'))
    verified.append({'scope': scope, 'sealed_files': len(entries), 'seal_sha256': sha(seal), 'closed_checks': checks})
save('CLOSED_SCOPES_VERIFIED.json', {'all_sealed_entries_match': True, 'scopes': verified, 'overlapping_accounts_must_not_be_summed': True})

agent = ROOT / 'AGENTS.md'
assert agent.is_file(), str(ROOT)
old = agent.read_bytes()
backup = HERE / 'AGENTS.completed.before.md'
assert not backup.exists(), 'Do not overwrite an earlier authority backup'
backup.write_bytes(old)
header = '''# October26 complete camera feasibility: conditional auxiliary only

Read docs/maintenance/2026-10-26/continuation-02/REPORT.md, NEXT_STRATEGY.md and CLOSED_SCOPES_VERIFIED.json. All six finite scopes are closed; no image/model/training/pose experiment is pending. Owner explicitly renewed this current-window continuation until actual quota exhaustion; last saved95%/ordinaryTRUE/reset1793013248 followed07:13:23UTC is NOT exhaustion. Prior window actual boundary UNOBSERVED. Later actual account receipts supersede availability text only; no automatic reset resume.

AF1 all200 F2 pairs require273 camera0 frames; both known22-sequence trees lack images and owner says no other path. Original devkit/readme identity matches; intended calibration/sync/raw mapping does not authenticate local acquisition accuracy. KCS1 authorized one official page:1GET/141461bytes/200/EOF; six download links point to login, no links/login/archive/image access. Saved parser stdout GBK failure retained and outputs independently checked. KC0 original614.570725/600s documentary cap FAIL retained without retry; other source limits unchanged.

CU1 complete all273 frozen raw hashes/200pairs/400directions/48742169 point occurrences:12304243 joint positive-depth occurrences, two affine routes/12800 Decimal depth checks PASS. This is supplied-reference optimistic support only, no image/frustum/occlusion/correspondence/information/pose accuracy. Original positive75 per sequence include00 two/08 sixteen both-zero pairs. New diagnostic1317.520552/1800s inclusive; numerical11.625s/peak103002112bytes, exited0. All200 retained, no supported-subset rescue.

CR1 categorical join:08 no-support occurs7/17 historically correct accepted versus2/10 wrong accepted; no-support is not an incorrectness label. Of41 missing-correct-proposal pairs,6 both-zero and35 only optimistic potential. Fixed-pair global image similarity cannot create missing poses. CC1 static AST/source algebra: existing0.205-degree correction axis depends on point direction, not one SE(3); no exact constant camera conjugation or inferred RAP inverse. Keep raw point identities and distinct camera/RAP geometry roles. Does not negate E0 measured benefits.

Next conditional route requires legitimate complete273-frame imagery with dimensions/calibration/time/source contract, ordinary visual-geometry controls and explicit no-evidence fallback before any RAP contribution claim. No automatic22GB download, login, model/package selection or new training. SR1 approximately1.98% fit loss improvement/all four noise cells FAIL remains fitting feasibility only; old native/HFIT0/NJE0/RLP2/BRF0/P0 and all caps/stops unchanged. RegX extraction authentication still absent. Research UNRESOLVED/manuscript PAUSED. WSL remained Stopped, E image/backup/Junction retained. No production/default/install/Git/outreach/scheduler/goal-status change. Exact preceding AGENTS bytes backed up and retained below.

---

'''.encode('utf-8')
agent.write_bytes(header + old)
assert agent.read_bytes()[len(header):] == backup.read_bytes()
save('AGENTS_COMPLETION_PROOF.json', {'before_sha256': sha(backup), 'after_sha256': sha(agent), 'prior_bytes': len(old), 'prefix_bytes': len(header), 'prior_bytes_exact_suffix': True})
save('STATUS.json', {'status': 'ALL_FINITE_SCOPES_COMPLETE_CONDITIONAL_CAMERA_STRATEGY', 'owner_continuation': 'ACTIVE_CURRENT_WINDOW_DELIVERY_ACCOUNT_CHECKS', 'no_pending_scientific_payload': True, 'original_goal': 'UNRESOLVED', 'manuscript': 'PAUSED', 'quota_exhaustion_observed': False, 'latest_saved_account': 'ACCOUNT_02.json', 'ordinary_usage_allowed_at_last_observation': True, 'automatic_resume': False, 'goal_status_tool_changed': False})
now = datetime.now(timezone.utc)
origin = datetime(2026,10,26,7,13,23,tzinfo=timezone.utc)
elapsed = (now-origin).total_seconds()
save('DELIVERY_CHECKS.json', {'utc': now.isoformat(), 'documentary_origin_utc': origin.isoformat(), 'cap_seconds': 600, 'inclusive_seconds': elapsed, 'cap_pass': elapsed <=600, 'all_six_scope_seals_verified': True, 'old_agents_exact_suffix': True, 'new_scientific_payload': False, 'account_boundary_observed': False, 'wsl_last_observed': 'Stopped', 'local_heads': ['4055d929c594b0033aafc6eed339c910369eef55','6d3f2d22cedfe1f807deb11fd8796b9f5bf17cd6'], 'known_tracked_dirty_path_sets_retained': True})
files = [{'path': p.relative_to(HERE).as_posix(), 'bytes': p.stat().st_size, 'sha256': sha(p)} for p in sorted(HERE.rglob('*')) if p.is_file() and p.name != 'DELIVERY_SEAL.json']
save('DELIVERY_SEAL.json', {'scope': 'current-window-strategy-delivery', 'files': files, 'account_receipts_created_later_are_additive_not_covered_by_this_seal': True})
print(json.dumps({'verified_scopes': len(verified), 'sealed_scope_entries': sum(x['sealed_files'] for x in verified), 'delivery_files':len(files), 'delivery_seconds':elapsed, 'cap_pass':elapsed<=600, 'agents_suffix_preserved':True}))
