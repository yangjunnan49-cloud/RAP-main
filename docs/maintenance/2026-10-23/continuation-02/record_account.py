"""Record one supplied actual receipt; no network, scheduler or old-file edits."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
CLASSIFIER=ROOT.parent/'account-boundary-02'
POLICY=ROOT.parent/'account-ledger-01'
classifier_freeze=json.loads((CLASSIFIER/'SOURCE_FREEZE.json').read_text())
policy_freeze=json.loads((POLICY/'SOURCE_FREEZE.json').read_text())
assert hashlib.sha256((CLASSIFIER/'account_classifier.py').read_bytes()).hexdigest().upper()==classifier_freeze['account_classifier.py']
assert hashlib.sha256((POLICY/'ledger_policy.py').read_bytes()).hexdigest().upper()==policy_freeze['ledger_policy.py']
sys.path.insert(0,str(CLASSIFIER))
sys.path.insert(0,str(POLICY))
from account_classifier import classify,extract
from ledger_policy import decide
p=Path(sys.argv[1]).resolve();assert p.is_relative_to(ROOT.resolve())
raw=json.loads(p.read_text());payload=extract(raw['usage_tool_result'])
result=classify(payload,1792763091)
record=dict(classification=result,raw_observation=p.name,raw_SHA256=hashlib.sha256(p.read_bytes()).hexdigest().upper(),following_clock=raw['following_clock'],no_pending_experiment=True,no_automatic_resume=True,research='UNRESOLVED',manuscript='PAUSED',classifier_sha256=hashlib.sha256((CLASSIFIER/'account_classifier.py').read_bytes()).hexdigest().upper())
current=ROOT/'CURRENT_ACCOUNT.json'
previous=json.loads(current.read_text()) if current.exists() else None
markers=[ROOT/n for n in ('ACCOUNT_STOP.json','OBSERVATION_STOP.json') if (ROOT/n).exists()]
decision=decide(previous,record,bool(markers))
if decision in ('RETAIN_TERMINAL','REJECT_STALE_ACTIVE'):
    if markers:current.write_bytes(markers[0].read_bytes())
    print(json.dumps(dict(decision=decision,previous_state_retained=True)));sys.exit(0)
record['ledger_policy_sha256']=hashlib.sha256((POLICY/'ledger_policy.py').read_bytes()).hexdigest().upper()
record['ledger_decision']=decision
if decision=='WRITE_CLOCK_UNCERTAINTY_STOP':
    record['source_classification']=result
    record['classification']=dict(status='CLOCK_UNCERTAINTY_STOP',confirmed_account_disabled=False)
if decision=='WRITE_DISABLED':
    stop=ROOT/'ACCOUNT_STOP.json'
    if not stop.exists():
        with stop.open('x') as f:json.dump(record,f,indent=2)
elif decision in ('WRITE_OBSERVATION_STOP','WRITE_CLOCK_UNCERTAINTY_STOP'):
    stop=ROOT/'OBSERVATION_STOP.json'
    if not stop.exists():
        with stop.open('x') as f:json.dump(record,f,indent=2)
current.write_text(json.dumps(record,indent=2))
print(json.dumps(result))
