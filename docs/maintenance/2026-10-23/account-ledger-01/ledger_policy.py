"""Pure decision policy: preserve terminal evidence and reject stale activation."""
import datetime as dt
def stamp(record):
    try:return dt.datetime.strptime(record['following_clock']['current_time'],'%Y-%m-%d %H:%M:%S UTC')
    except (KeyError,ValueError,TypeError):return None
def decide(previous,new,terminal_exists):
    status=new['classification']['status']
    if terminal_exists or previous and previous.get('classification',{}).get('status') not in (None,'ACTIVE'):
        return 'RETAIN_TERMINAL'
    if status=='ACCOUNT_ORDINARY_USAGE_DISABLED':return 'WRITE_DISABLED'
    if status!='ACTIVE':return 'WRITE_OBSERVATION_STOP'
    now=stamp(new)
    if now is None:return 'WRITE_CLOCK_UNCERTAINTY_STOP'
    before=stamp(previous) if previous else None
    if before is not None and now<before:return 'REJECT_STALE_ACTIVE'
    return 'WRITE_ACTIVE'
