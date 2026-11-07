"""Record one supplied actual receipt; no network, scheduler or old-file edits."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
CLASSIFIER=ROOT.parent/'account-boundary-02'
sys.path.insert(0,str(CLASSIFIER))
from account_classifier import classify,extract
p=Path(sys.argv[1]).resolve();assert p.is_relative_to(ROOT.resolve())
raw=json.loads(p.read_text());payload=extract(raw['usage_tool_result'])
result=classify(payload,1792763091)
record=dict(classification=result,raw_observation=p.name,raw_SHA256=hashlib.sha256(p.read_bytes()).hexdigest().upper(),following_clock=raw['following_clock'],no_pending_experiment=True,no_automatic_resume=True,research='UNRESOLVED',manuscript='PAUSED',classifier_sha256=hashlib.sha256((CLASSIFIER/'account_classifier.py').read_bytes()).hexdigest().upper())
if result['status']=='ACCOUNT_ORDINARY_USAGE_DISABLED':
    stop=ROOT/'ACCOUNT_STOP.json'
    if not stop.exists():
        with stop.open('x') as f:json.dump(record,f,indent=2)
elif result['status']!='ACTIVE':
    stop=ROOT/'OBSERVATION_STOP.json'
    if not stop.exists():
        with stop.open('x') as f:json.dump(record,f,indent=2)
current=ROOT/'CURRENT_ACCOUNT.json'
current.write_text(json.dumps(record,indent=2))
print(json.dumps(result))
