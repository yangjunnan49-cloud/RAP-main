"""Final owner-requested closing bookkeeping, no science or network."""
import ast
import json
from pathlib import Path
import physical_source_role_feasibility as s

ROOT=s.ROOT
DAY=ROOT/'docs/maintenance/2026-10-15'
BASE=DAY/'continuation-handoff-06'
OUT=BASE/'owner-close-01'


def save(name,value):
    with (OUT/name).open('x',encoding='utf-8') as f:json.dump(value,f,indent=2);f.write('\n')


def main():
    w=s.read(OUT/'WINDOWS_CHECKS.json');assert w['passed'] and w['unique_identity_paths']==552
    assert w['retained_markers']==10 and not w['scoped_payload_matches']
    assert s.repositories()==w['repositories']
    identifiers=set(w['scoped_identifiers']);processes=readable=argv=0;unreadable=[];matches=[]
    for d in Path('/proc').iterdir():
        if not d.name.isdigit():continue
        processes+=1
        try:args=[x.decode(errors='replace') for x in (d/'cmdline').read_bytes().split(b'\0') if x]
        except (FileNotFoundError,PermissionError,ProcessLookupError):unreadable.append(d.name);continue
        readable+=1;argv+=len(args)
        for arg in args:
            if Path(arg.replace('\\','/')).name in identifiers:matches.append(dict(pid=d.name,argument=arg));break
    assert not matches
    save('LINUX_CHECKS.json',dict(processes=processes,readable=readable,argv=argv,unreadable=unreadable,
        scoped_payload_matches=matches,unrelated_tasks_absence_claim=False))
    for name in ('DELIVERY_SEAL.json','FINAL_VERIFICATION_SEAL.json','ACCOUNT_STOP_SEAL.json'):
        for r in s.read(BASE/name)['files']:
            q=BASE/r['path'];assert s.sha(q)==r['sha256'] and q.stat().st_size==r['bytes']
    a=s.read(BASE/'ACCOUNT_STOP.json');assert a['primary_used_percent']==100 and a['ordinaryUsageAllowed'] is False
    assert a['closing_resume_primary_used_percent']==1 and a['observation_UTC'] is None
    assert not a['scientific_goal_complete'] and not a['automatic_quota_reset_resume']
    save('CHECKS.json',dict(passed=True,status='EXPLICIT_OWNER_ROUND_CLOSURE_COMPLETE',
        Windows_unique_identity_paths=552,old_seals_verified=dict(original=12,independent=10,account=7),
        original_repositories_preserved=True,retained_markers=10,
        current_scoped_payload_matches=0,process_absence_scoped_only=True,
        Windows_unreadable_relevant_interpreters=w['unreadable_relevant_interpreters'],
        Linux_unreadable_processes=unreadable,new_scientific_or_network_payload_calls=0,
        historical_quota_stop_recorded_retrospectively=True,scientific_goal_complete=False,
        observer_full_lifetime_peak='UNKNOWN',ordinary_closing_RSS='UNKNOWN',automatic_reset_resume=False))
    snap=OUT/'source_snapshot';snap.mkdir()
    for q in (Path(__file__),ROOT/'scripts/maintenance/verify_handoff06_owner_close.ps1',
              ROOT/'AGENTS.md',DAY/'PHASE_RECORD.md',BASE/'CLOSING_NOTE.md'):
        with (snap/q.name).open('xb') as f:f.write(q.read_bytes())
    ast.parse(Path(__file__).read_text())
    files=[dict(path=str(q.relative_to(OUT)),bytes=q.stat().st_size,sha256=s.sha(q)) for q in sorted(OUT.rglob('*')) if q.is_file()]
    save('DELIVERY_SEAL.json',dict(status='EXPLICIT_OWNER_ROUND_CLOSURE_COMPLETE',files=files))
    print(json.dumps(dict(status='EXPLICIT_OWNER_ROUND_CLOSURE_COMPLETE',entries=len(files),
        Windows_processes=w['processes'],Windows_argv=w['argv'],Linux_processes=processes,Linux_argv=argv,
        scoped_payload_matches=0,new_scientific_or_network_payload_calls=0)),flush=True)


if __name__=='__main__':main()
