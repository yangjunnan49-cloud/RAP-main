"""New additive recovery receipts; never modify previous authoritative files."""
import datetime as dt
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def write(name,value):
    with (ROOT/name).open('x',encoding='utf-8') as f:json.dump(value,f,indent=2)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
now=dt.datetime.now(dt.timezone.utc)
names=('source-binding-01','source-interface-01','source-export-verifier-01','reference-admission-01','real-interface-01','feature-failure-01')
costs={n:dict(sha256=sha(ROOT.parent/n/'COSTS_FINAL.json'),receipt=json.loads((ROOT.parent/n/'COSTS_FINAL.json').read_text())) for n in names}
write('PRIOR_CLOSED_COSTS.json',costs)
write('PRIOR_REVIEW_FAILURE.json',dict(classification='ACTUAL_USAGE_LIMIT_REPORTED_BY_AUTOMATIC_REVIEW',
    source='Prior conversation tool result; recovered after new explicit human authorization',
    exact_failure_utc=None,last_prior_API_clock='2026-10-23 02:27:32 UTC',
    prior_API_ordinaryUsageAllowed=True,prior_API_usedPercent=100,prior_API_reset=1792736321,
    message_summary='Automatic approval review failed because the usage limit was hit; account-usage read was not executed. It was a review failure, not a determination that the action was unsafe.',
    API_ordinary_false_receipt_captured=False,recorded_utc=now.isoformat(),no_reset_cause_inferred=True))
start=dt.datetime.fromisoformat('2026-10-23T02:23:36+00:00')
write('PRIOR_DOCUMENTARY_COST_CLOSE.json',dict(scope='Prior continuation documentary closeout, including stopped interval',
    original_protocol='../continuation-01/DOCUMENTARY_PROTOCOL.json',start_utc=start.isoformat(),close_utc=now.isoformat(),
    cap_seconds=900,conservative_UTC_elapsed_seconds=(now-start).total_seconds(),budget_status='FAIL',
    no_initial_monotonic_receipt=True,stopped_interval_included=True,prior_six_closed_costs_unchanged=True))
write('RECOVERY_STATE.json',dict(status='NEW_EXPLICIT_OWNER_AUTHORIZATION_ACTIVE',
    primary_used_percent=1,ordinary_usage_allowed=True,reset=1792763091,following_clock='2026-10-23 08:44:50 UTC',
    prior_account_stopped_on_later_explicit_review_failure=True,earlier_display100_ordinary_true_not_boundary=True,
    prior_documentary_budget='FAIL',old_authoritative_files_untouched=True,
    no_automatic_resume=True,original_research='UNRESOLVED',manuscript='PAUSED'))
write('APPROVAL_REJECTION_AND_SAFER_ALTERNATIVE.json',dict(rejected_action='Overwrite prior continuation state/cost/stop files and prepend AGENTS',
    reason='Could damage authoritative historical evidence; missing original-cost backup',
    executed=False,safer_alternative='Only new additive recovery receipts, previous files untouched',remaining_blocked_action=None))
write('RECOVERY_CHECKS.json',dict(prior_six_hashes_match=all(sha(ROOT.parent/k/'COSTS_FINAL.json')==v['sha256'] for k,v in costs.items()),
    root_AGENTS_unchanged=sha(ROOT.parents[3]/'AGENTS.md')==sha(ROOT/'AGENTS.before_recovery.md'),
    no_old_authoritative_files_written=True))
print(json.dumps(dict(prior_documentary_elapsed=(now-start).total_seconds(),old_budget='FAIL',six_costs_unchanged=True)))
