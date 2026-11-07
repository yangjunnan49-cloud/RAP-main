"""Additive renewal and exact prior closed-identity checks; no research execution."""
import datetime, hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
DAY=ROOT.parent
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def write(name, value):
    with (ROOT/name).open('x', encoding='utf-8') as f:
        json.dump(value,f,indent=2)

previous=json.loads((DAY/'continuation-01/CLOSED_SCOPES.json').read_text())
assert previous['scope_count']==7
for row in previous['scopes']:
    assert sha(DAY/row['scope']/'COSTS_FINAL.json')==row['sha256']
packages={
 'delivery-audit-01/RAP_public_functional_20261024.zip':'BBF7FCB2A87DBA232666F4B4B6D269A55460E2E39960E4BBD6A5996FBD254A85',
 'pose-convention-01/RAP_5_case_local_matrices_20261024.zip':'C7A1C4411ACB59A5994D58637D3A8F6C1D9D71186A18A3103A3549D41DD83AAB'}
for name, expected in packages.items(): assert sha(DAY/name)==expected
prior=DAY/'continuation-01'
assert not (prior/'ACCOUNT_STOP.json').exists()
current=json.loads((prior/'CURRENT_ACCOUNT.json').read_text())
write('PRIOR_BOUNDARY_GAP.json',dict(classification='UNOBSERVED_PREVIOUS_WINDOW_BOUNDARY',
    last_conversation_observation=dict(usedPercent=100,ordinaryUsageAllowed=True,resetsAt=1792825078,following_UTC='2026-10-24 02:33:40 UTC'),
    last_saved_record=current,exact_failure_UTC=None,API_ordinary_false_receipt_captured=False,
    explicit_quota_review_failure_verified=False,context_truncation_is_not_quota_evidence=True,
    failed_or_completed_composite_action='UNVERIFIED',no_reset_cause_inferred=True,
    previous_closed_scopes_unchanged=True,no_automatic_resume=True))
write('RECOVERY_CHECKS.json',dict(passed=True,prior_closed_cost_hashes=7,package_hashes=packages,
    previous_account_pointer_sha256=sha(prior/'CURRENT_ACCOUNT.json'),
    no_prior_account_stop=True,old_costs_reset=False,pending_real_computation=False))
start=datetime.datetime(2026,10,24,7,18,58,tzinfo=datetime.timezone.utc)
elapsed=(datetime.datetime.now(datetime.timezone.utc)-start).total_seconds()
write('COSTS_FINAL.json',dict(status='ADDITIVE_RENEWAL_RECOVERY_COMPLETE',elapsed_seconds=elapsed,
    cap_seconds=900,budget_status='PASS' if elapsed<=900 else 'FAIL',
    conservative_UTC_origin=start.isoformat(),old_scopes_closed_before_gap=True,old_caps_reset=False))
print(json.dumps(dict(prior_costs_verified=7,packages_verified=2,elapsed_seconds=elapsed)))
