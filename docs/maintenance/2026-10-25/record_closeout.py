"""Post-closure account/ledger bookkeeping; no reopening any finite scope."""
import hashlib,json,sys
from pathlib import Path
DAY=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def write(p,v):
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,indent=2)
classifier=DAY.parent/'2026-10-23/account-boundary-02'
cf=json.loads((classifier/'SOURCE_FREEZE.json').read_text(encoding='utf-8'))
assert sha(classifier/'account_classifier.py')==cf['account_classifier.py']
sys.path.insert(0,str(classifier))
from account_classifier import extract,classify
raw=json.loads((DAY/'POST_CLOSE_ACCOUNT_OBSERVATION.json').read_text(encoding='utf-8'))
classification=classify(extract(raw['usage_tool_result']),1792911572)
write(DAY/'POST_CLOSE_ACCOUNT_CHECK.json',dict(round_status='CLOSED_BY_OWNER_BEFORE_QUOTA_EXHAUSTION',
    post_close_account_classification=classification,following_clock=raw['following_clock'],
    actual_account_exhaustion_observed=classification['confirmed_account_disabled'],
    finite_scope_costs_not_modified=True,record_is_additive_post_closure_bookkeeping=True,
    pending_real_computation=False,pending_acquisition_or_permission=False,no_automatic_reset_resume=True,
    scheduler_or_goal_status_changed=False,closed_scope='upstream-page-01/FINAL_STATUS.json'))
old=DAY.parent/'2026-10-24'
prior=json.loads((old/'continuation-02/CLOSED_SCOPES_WITH_SOURCE_REQUEST.json').read_text(encoding='utf-8'))
rows=[]
for r in prior['scopes']:
    p=old/r['scope']/'COSTS_FINAL.json';assert sha(p)==r['sha256']
    rows.append(dict(scope='2026-10-24/'+r['scope'],cost_sha256=r['sha256'],receipt=r['receipt']))
p=DAY/'upstream-page-01/COSTS_FINAL.json';cost=json.loads(p.read_text(encoding='utf-8'))
assert cost['budget_status']=='PASS'
rows.append(dict(scope='2026-10-25/upstream-page-01',cost_sha256=sha(p),receipt=cost))
write(DAY/'CLOSED_SCOPES.json',dict(scopes=rows,scope_count=13,
    scope_population='Twelve previously closed October24 scopes plus this one finite authorized October25 scope; earlier history retained separately',
    all_original_time_budgets_pass=True,original_failures_preserved=True,
    pending_payload_or_permission=False,owner_requested_prequota_closeout=True,
    no_automatic_reset_resume=True,research='UNRESOLVED',manuscript='PAUSED'))
print(json.dumps(dict(round_closed=True,post_close_quota=classification,following_clock=raw['following_clock'],closed_scope_count=13)))
