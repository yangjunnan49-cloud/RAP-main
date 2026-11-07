"""Independent Windows prototype bytes/native process/envelope validation."""
import hashlib
import json
from pathlib import Path
from validate_evidence_journal import decode

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'docs/maintenance/2026-10-14/windows-pipe-capture-01'


def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def validate():
    f,e,n,interop=[read(BASE/name) for name in ('freeze.json','exercise.json','native_controller.json','interop_exit.json')]
    seal=read(BASE/'exercise_seal.json')
    assert sha(BASE/'exercise.json')==seal['sha256']
    assert sha(BASE/'native_controller.json')==seal['native_controller_sha256']
    assert sha(BASE/'interop_exit.json')==seal['interop_exit_sha256']
    for p,row in f['files'].items():assert sha(p)==row['sha256'] and Path(p).stat().st_size==row['bytes']
    assert interop['exit_code']==0 and n['success'] and n['inner_children']==8
    assert [row['mode'] for row in n['cases']]==f['cases'] and len({row['pid'] for row in n['cases']})==8
    assert 0<n['peak_working_set_bytes']<=256*2**20 and n['cpu_seconds']>=0
    assert {p.name for p in (BASE/'fixtures').iterdir()}==set(f['cases'])
    for row in e['files']:
        p=BASE/row['path'];assert sha(p)==row['sha256'] and p.stat().st_size==row['bytes']
    results=[]
    for receipt in n['cases']:
        mode=receipt['mode'];folder=BASE/'fixtures'/mode
        assert {p.name for p in folder.iterdir()}=={'evidence.rdj','exit.json'}
        assert read(folder/'exit.json')==receipt and (folder/'exit.json').stat().st_size<=1024
        total=sum(p.stat().st_size for p in folder.iterdir());assert total<=3072
        assert 0<receipt['peak_working_set_bytes']<=256*2**20 and receipt['cpu_seconds']>=0
        assert receipt['EOF_observed']=={'2':True,'3':True}
        assert not receipt['full_intended_flood_output_claim']
        journal=decode(folder/'evidence.rdj');assert journal['sealed'] and journal['cap']==2048
        outputs={k:b''.join(body for channel,body in journal['records'] if channel==k) for k in (2,3)}
        metadata=[json.loads(body) for channel,body in journal['records'] if channel==4]
        assert metadata==[dict(event='launch',mode=mode)]
        for k in (2,3):
            key=str(k);assert len(outputs[k])==receipt['stored_bytes'][key]<=128
            assert receipt['discarded_observed_bytes'][key]==receipt['observed_bytes'][key]-len(outputs[k])>=0
        success=mode in ('normal','empty','binary')
        assert receipt['admitted'] is success and journal['admitted'] is success
        if success:
            expected={2:b'',3:b''}
            if mode=='normal':expected={2:b'hello-out\n',3:b'hello-err\n'}
            if mode=='binary':expected[2]=b'\xff\x00\xfe'
            assert outputs==expected and receipt['native_exit_code']==0 and receipt['reason'] is None
            assert not receipt['termination_requested']
        elif mode=='nonzero':
            assert receipt['native_exit_code']==7 and receipt['reason']=='nonzero_exit' and journal['status']==3
            assert outputs=={2:b'',3:b'planned exit7\n'}
        elif mode=='timeout':
            assert receipt['native_exit_code']!=0 and receipt['reason']=='timeout' and journal['status']==3
            assert receipt['termination_requested'] and receipt['wall_seconds']<5
        else:
            assert receipt['reason']=='log_overflow' and journal['status']==2
            assert sum(receipt['discarded_observed_bytes'].values())>0
        results.append(dict(case=mode,native_exit=receipt['native_exit_code'],reason=receipt['reason'],
            admitted=success,total_case_bytes=total,peak_working_set_bytes=receipt['peak_working_set_bytes'],
            wall_seconds=receipt['wall_seconds']))
    result=dict(passed=True,frozen_identities=len(f['files']),cases=8,native_children=8,
        native_controller_exit=interop['exit_code'],native_controller_peak_working_set_bytes=n['peak_working_set_bytes'],
        results=results,all_native_exits_peak_working_sets_and_pipe_EOF_present=True,
        cooperating_case_envelope_bytes=3072,whole_production_dossier_guarantee=False,
        current_supervisor_or_RAP_integration=False)
    with (BASE/'validation.json').open('x',encoding='utf-8') as out:
        json.dump(result,out,indent=2,allow_nan=False);out.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k!='results'}),flush=True)
