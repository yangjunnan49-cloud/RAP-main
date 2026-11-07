"""Independent NMQ0 ABI/query result and conditional denominator validation."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'docs/maintenance/2026-10-14/native-memory-query-01'


def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def validate():
    f,n=read(BASE/'freeze.json'),read(BASE/'native_queries.json')
    seal=read(BASE/'observation_seal.json')
    assert sha(BASE/'native_queries.json')==seal['sha256']
    assert sha(BASE/'interop_exit.json')==seal['interop_exit_sha256']
    assert read(BASE/'interop_exit.json')['exit_code']==0 and n['observation_execution_complete']
    for path,row in f['files'].items():assert sha(path)==row['sha256'] and Path(path).stat().st_size==row['bytes']
    assert n['pointer_bytes']==8 and not n['observer_full_lifetime_peak_known']
    assert not n['old_WPC0_resource_gap_repaired']
    assert n['observer_to_snapshot']['success'] and 0<n['observer_to_snapshot']['peak_working_set']<=256*2**20
    cases=n['cases'];assert cases and cases[0]['mode']=='baseline'
    expected=f['potential_cases'] if cases[0]['final_OS_peak_available'] else ['baseline']
    assert [r['mode'] for r in cases]==expected and n['native_children']==len(cases)
    assert len({r['pid'] for r in cases})==len(cases)
    results=[]
    for row in cases:
        assert row['native_exit_code']==0 and row['handle_retained_through_final_queries']
        assert row['running_query_count']==len(row['running_queries'])>0
        assert row['running_query_failures']==sum(not q['success'] for q in row['running_queries'])
        assert len(row['post_exit_queries'])==2
        for q in row['running_queries']+row['post_exit_queries']:
            assert q['structure_bytes']==2*4+8*8==72
            assert q['error_relevant'] is (not q['success'])
            assert all(isinstance(q[k],int) and q[k]>=0 for k in ('peak_working_set','working_set','peak_commit'))
        a,b=row['post_exit_queries']
        observed=max((q['peak_working_set'] for q in row['running_queries'] if q['success']),default=0)
        available=a['success'] and b['success'] and a['peak_working_set']>0 and a['peak_working_set']==b['peak_working_set'] and a['peak_working_set']>=observed
        assert row['final_OS_peak_available'] is available and row['final_native_cap_proven'] is available
        if available:assert a['peak_working_set']<=256*2**20
        dotnet=row['refreshed_dotnet']
        if dotnet['success']:assert dotnet['peak_working_set']>=0 and dotnet['error'] is None
        else:assert dotnet['error'] and dotnet['peak_working_set'] is None
        results.append(dict(mode=row['mode'],native_exit=0,running_queries=row['running_query_count'],
            running_query_failures=row['running_query_failures'],post_exit_query_successes=[a['success'],b['success']],
            post_exit_peaks=[a['peak_working_set'],b['peak_working_set']],
            post_exit_errors=[a['error'],b['error']],final_peak_available=available,
            refreshed_dotnet_success=dotnet['success']))
    decision='DIRECT_FINAL_NATIVE_PEAK_AVAILABLE_IN_FIXED_CONTROLS' if all(r['final_peak_available'] for r in results) else 'DIRECT_FINAL_NATIVE_PEAK_UNAVAILABLE_RESOURCE_EVIDENCE_STOP'
    result=dict(passed=True,decision=decision,frozen_identities=len(f['files']),native_children=len(cases),
        results=results,all_recorded_queries_including_failures_accounted=True,
        original_WPC0_resource_gate_repaired=False,complete_native_observer_lifetime_peak_known=False,
        production_integration_or_old_retry=False)
    with (BASE/'validation.json').open('x',encoding='utf-8') as out:
        json.dump(result,out,indent=2,allow_nan=False);out.write('\n')
    print(json.dumps(result),flush=True)
