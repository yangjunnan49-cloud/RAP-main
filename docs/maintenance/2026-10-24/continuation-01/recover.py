"""New additive recovery, preserving all prior closed authority and payloads."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent;DAY23=ROOT.parent.parent/'2026-10-23'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def write(name,value):
    with (ROOT/name).open('x') as f:json.dump(value,f,indent=2)
old=json.loads((DAY23/'continuation-02/CLOSED_SCOPES.json').read_text())
assert old['scope_count']==15
for row in old['scopes']:assert sha(DAY23/row['scope']/'COSTS_FINAL.json')==row['SHA256']
zipreceipt=json.loads((DAY23/'handoff-02/ZIP_CHECKS.json').read_text())
assert sha(DAY23/'handoff-02/RAP_20261023_closed_scopes.zip')==zipreceipt['ZIP_sha256']
write('PRIOR_CLOSED_SCOPES.json',old)
write('PRIOR_ACCOUNT_STOP_ADDITIVE.json',dict(classification='EXPLICIT_QUOTA_REVIEW_FAILURE',
    source='Prior conversation tool result; recovered after new explicit owner authorization',
    last_conversation_API=dict(usedPercent=99,ordinaryUsageAllowed=True,resetsAt=1792763091,following_clock='2026-10-23 09:56:34 UTC'),
    last_persisted_record=json.loads((DAY23/'continuation-02/CURRENT_ACCOUNT.json').read_text()),
    exact_review_failure_utc=None,API_ordinary_false_receipt_captured=False,
    failed_action='Composite attempt to save99% observation, update local pointer and read quota; review rejected before execution',
    review_message_summary='You have hit your usage limit; action not executed because automatic approval review could not be completed, not a determination that the action was unsafe',
    no_reset_cause_inferred=True,old_authoritative_files_untouched=True,no_automatic_resume=True))
write('RECOVERY_CHECKS.json',dict(passed=True,prior15_closed_cost_hashes_match=True,prior_ZIP_hash_matches=True,
    prior_scientific_failures_and_closed_costs_unchanged=True,prior_open_numeric_scope=False,
    old_gap_in_an_open_budget_not_excluded=True,old_authorities_not_written=True))
print(json.dumps(dict(prior_closed_costs=15,ZIP_matches=True,old_authorities_unchanged=True)))
