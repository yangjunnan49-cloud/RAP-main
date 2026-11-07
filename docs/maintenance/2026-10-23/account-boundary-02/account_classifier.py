"""Pure supplied-receipt classification; no API calls or account changes."""
import json,math
def extract(tool_result):
    if not isinstance(tool_result,dict) or tool_result.get('isError'):raise ValueError('unavailable_tool_result')
    parts=[p['text'] for p in tool_result.get('content',[]) if isinstance(p,dict) and p.get('type')=='text']
    if len(parts)!=1:raise ValueError('ambiguous_tool_content')
    result=json.loads(parts[0])
    if not isinstance(result,dict):raise ValueError('invalid_usage_payload')
    return result
def classify(payload,expected_reset):
    if type(expected_reset)is not int or expected_reset<=0:raise ValueError('expected_window_required')
    if not isinstance(payload,dict):return dict(status='READ_UNAVAILABLE_STOP',confirmed_account_disabled=False)
    ordinary=payload.get('ordinaryUsageAllowed')
    bucket=payload.get('rateLimitsByLimitId',{}).get('codex') if isinstance(payload.get('rateLimitsByLimitId',{}),dict) else None
    if not isinstance(bucket,dict):bucket=payload.get('rateLimits',{})
    primary=bucket.get('primary',{}) if isinstance(bucket,dict) else {}
    primary=primary if isinstance(primary,dict) else {}
    reset=primary.get('resetsAt');used=primary.get('usedPercent')
    fields=dict(ordinaryUsageAllowed=ordinary,usedPercent=used,resetsAt=reset,expected_reset=expected_reset,no_reset_cause_inferred=True)
    # Disabled evidence takes priority over window identity, preserving both facts.
    if ordinary is False:return dict(fields,status='ACCOUNT_ORDINARY_USAGE_DISABLED',confirmed_account_disabled=True,primary_display100=used==100)
    valid=(ordinary is True and type(reset)is int and reset>0 and type(used)in(int,float) and math.isfinite(used) and 0<=used<=100)
    if not valid:return dict(fields,status='READ_UNAVAILABLE_STOP',confirmed_account_disabled=False)
    if reset!=expected_reset:return dict(fields,status='WINDOW_CHANGED_STOP',confirmed_account_disabled=False)
    return dict(fields,status='ACTIVE',confirmed_account_disabled=False,display100_alone_not_exhaustion=used==100)
