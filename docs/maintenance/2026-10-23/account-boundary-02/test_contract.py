"""Independent classification truth table and saved-observation replay."""
import copy,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT));START=time.monotonic()
from account_classifier import classify,extract
def write(name,value):
    with (ROOT/name).open('x') as f:json.dump(value,f,indent=2)
RESET=1792763091
base=dict(ordinaryUsageAllowed=True,rateLimits=dict(primary=dict(usedPercent=0,resetsAt=RESET),secondary=dict(usedPercent=0)))
def fixture(ordinary=True,used=0,reset=RESET):
    x=copy.deepcopy(base);x['ordinaryUsageAllowed']=ordinary;x['rateLimits']['primary'].update(usedPercent=used,resetsAt=reset);return x
cases=[('allowed0',fixture(),'ACTIVE',False),('allowed99',fixture(used=99),'ACTIVE',False),('display100_allowed',fixture(used=100),'ACTIVE',False),('disabled100',fixture(False,100),'ACCOUNT_ORDINARY_USAGE_DISABLED',True),('disabled_changed_reset_priority',fixture(False,100,RESET+1),'ACCOUNT_ORDINARY_USAGE_DISABLED',True),('allowed_changed_reset',fixture(True,100,RESET+1),'WINDOW_CHANGED_STOP',False),('missing_boolean',fixture(None,100),'READ_UNAVAILABLE_STOP',False),('string_false_not_boolean',fixture('false',100),'READ_UNAVAILABLE_STOP',False),('invalid_percent',fixture(True,101),'READ_UNAVAILABLE_STOP',False),('NaN_percent',fixture(True,float('nan')),'READ_UNAVAILABLE_STOP',False),('bool_percent',fixture(True,True),'READ_UNAVAILABLE_STOP',False),('missing_primary_allowed',dict(ordinaryUsageAllowed=True),'READ_UNAVAILABLE_STOP',False),('disabled_missing_primary',dict(ordinaryUsageAllowed=False),'ACCOUNT_ORDINARY_USAGE_DISABLED',True),('disabled_primary0_no_cause_inference',fixture(False,0),'ACCOUNT_ORDINARY_USAGE_DISABLED',True)]
x=fixture(used=50);x['rateLimits']['secondary']['usedPercent']=100;cases.append(('weekly_display100_ordinary_allowed',x,'ACTIVE',False))
x=fixture(used=50);x['rateLimitsByLimitId']={'codex':{'primary':{'usedPercent':100,'resetsAt':RESET}}};cases.append(('current_bucket_preferred',x,'ACTIVE',False))
results=[]
for name,payload,status,disabled in cases:
    result=classify(payload,RESET);assert result['status']==status and result['confirmed_account_disabled']==disabled,name
    results.append(dict(case=name,passed=True,expected_status=status))
for label,result in [('error_result',dict(isError=True,content=[])),('ambiguous',dict(content=[dict(type='text',text='{}'),dict(type='text',text='{}')])),('malformed_json',dict(content=[dict(type='text',text='broken')]))]:
    try:extract(result)
    except ValueError:pass
    else:raise AssertionError('Invalid tool result accepted:'+label)
    results.append(dict(case=label,passed=True))
try:classify(base,True)
except ValueError:pass
else:raise AssertionError('Boolean expected window accepted')
results.append(dict(case='invalid_expected_window',passed=True))
observations=[]
for p in sorted((ROOT.parent/'continuation-02').glob('*OBSERVATION*.json')):
    raw=json.loads(p.read_text());payload=extract(raw['usage_tool_result']);classified=classify(payload,RESET)
    assert classified['status']=='ACTIVE' and not classified['confirmed_account_disabled'],p.name
    observations.append(dict(file=p.name,classification=classified,following_clock=raw['following_clock']))
assert len(observations)>=7
assert not any(k in sys.modules for k in ('numpy','torch'))
write('RESULTS.json',dict(passed=True,synthetic_controls=len(results),controls=results,saved_actual_observations=observations,actual_boundary_observed=False,numeric_imports=False))
write('worker_exit.json',dict(success=True,elapsed_seconds=time.monotonic()-START))
print(json.dumps(dict(passed=True,synthetic_controls=len(results),saved_observations=len(observations))))
