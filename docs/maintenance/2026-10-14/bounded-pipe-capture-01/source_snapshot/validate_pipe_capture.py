"""Independent BPC0 native exits, byte streams, namespace and terminal budget."""
import hashlib
import json
import os
from pathlib import Path
from validate_evidence_journal import decode

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'docs/maintenance/2026-10-14/bounded-pipe-capture-01'


def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def validate():
    f,e=read(BASE/'freeze.json'),read(BASE/'exercise.json')
    assert sha(BASE/'exercise.json')==read(BASE/'exercise_seal.json')['sha256']
    for p,r in f['files'].items():assert sha(p)==r['sha256'] and Path(p).stat().st_size==r['bytes']
    assert [r['case'] for r in e['cases']]==f['cases'] and e['inner_children']==8
    assert {p.name for p in (BASE/'fixtures').iterdir()}==set(f['cases'])
    results=[];pids=set()
    for row in e['cases']:
        name=row['case'];folder=BASE/'fixtures'/name
        assert {p.name for p in folder.iterdir()}=={'evidence.rdj','exit.json'}
        assert (folder/'exit.json').stat().st_size<=1024
        assert sum(p.stat().st_size for p in folder.iterdir())<=3072
        for entry in row['files']:
            assert sha(folder/entry['path'])==entry['sha256']
            assert (folder/entry['path']).stat().st_size==entry['bytes']
        receipt=read(folder/'exit.json');assert receipt==row['receipt']
        native=receipt['native'];pids.add(native['pid'])
        assert os.waitstatus_to_exitcode(native['wait_status'])==native['exit_code']
        assert 0<native['peak_RSS_bytes']<=64*2**20 and native['user_seconds']>=0 and native['system_seconds']>=0
        assert receipt['EOF_observed']=={'2':True,'3':True}
        assert receipt['wall_seconds']>0 and not receipt['full_intended_flood_output_claim']
        d=decode(folder/'evidence.rdj');assert d['sealed'] and d['cap']==2048
        joined={k:b''.join(body for channel,body in d['records'] if channel==k) for k in (2,3)}
        metadata=[json.loads(body) for channel,body in d['records'] if channel==4]
        assert metadata==[dict(event='launch',mode=name)]
        for k in (2,3):
            key=str(k)
            assert len(joined[k])==receipt['stored_bytes'][key]<=128
            assert receipt['observed_bytes'][key]>=len(joined[k])
            assert receipt['discarded_observed_bytes'][key]==receipt['observed_bytes'][key]-len(joined[k])
        success=name in ('normal','empty','binary')
        assert receipt['admitted'] is success and d['admitted'] is success
        if success:
            assert native['exit_code']==0 and receipt['reason'] is None
            assert not receipt['termination_requested'] and d['status']==1
            expected={2:b'',3:b''}
            if name=='normal':expected={2:b'hello-out\n',3:b'hello-err\n'}
            elif name=='binary':expected[2]=b'\xff\x00\xfe'
            assert joined==expected and not any(receipt['discarded_observed_bytes'].values())
        elif name=='nonzero':
            assert native['exit_code']==7 and receipt['reason']=='nonzero_exit' and d['status']==3
            assert joined=={2:b'',3:b'planned exit7\n'}
        elif name=='timeout':
            assert native['exit_code'] in (-15,-9) and receipt['reason']=='timeout' and d['status']==3
            assert receipt['termination_requested'] and receipt['wall_seconds']<3
        else:
            assert receipt['reason']=='log_overflow' and d['status']==2
            assert sum(receipt['discarded_observed_bytes'].values())>0
            if name=='stdout_overflow':assert receipt['observed_bytes']['2']>128
            if name=='stderr_overflow':assert receipt['observed_bytes']['3']>128
        results.append(dict(case=name,native_exit=native['exit_code'],reason=receipt['reason'],
            admitted=success,total_case_bytes=sum(p.stat().st_size for p in folder.iterdir()),
            child_RSS_bytes=native['peak_RSS_bytes'],child_wall_seconds=receipt['wall_seconds']))
    assert len(pids)==8
    result=dict(passed=True,frozen_identities=len(f['files']),cases=8,inner_children_reaped=8,
        results=results,all_native_exit_RSS_and_pipe_EOF_present=True,
        cooperating_case_envelope_bytes=3072,arbitrary_external_writer_guarantee=False,
        production_or_RAP_integration=False)
    with (BASE/'validation.json').open('x',encoding='utf-8') as out:
        json.dump(result,out,indent=2,allow_nan=False);out.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k!='results'}),flush=True)
