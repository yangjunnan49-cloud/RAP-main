"""Independent BEJ0 binary decoding, complete census and admission rules."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'docs/maintenance/2026-10-14/bounded-evidence-journal-01'


def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def decode(path):
    data=path.read_bytes()
    if len(data)<80 or data[:8]!=b'RAPBEJ01':return dict(sealed=False)
    cap=int.from_bytes(data[8:12],'little')
    if int.from_bytes(data[12:16],'little')!=4 or len(data)>cap:return dict(sealed=False)
    tail=data[-64:];body=data[16:-64]
    if tail[:8]!=b'RAPEND01' or any(tail[61:]):return dict(sealed=False)
    status=tail[8]
    charged=int.from_bytes(tail[9:17],'little')
    count=int.from_bytes(tail[17:21],'little')
    actual=int.from_bytes(tail[21:29],'little')
    if (status not in (1,2,3,4) or actual!=len(body) or charged<len(body)
            or charged>cap-80 or tail[29:61]!=hashlib.sha256(body).digest()):
        return dict(sealed=False)
    cursor=0;records=[];torn=False
    while cursor<len(body):
        if len(body)-cursor<5:torn=True;break
        channel=body[cursor];length=int.from_bytes(body[cursor+1:cursor+5],'little')
        end=cursor+5+length
        if channel not in (1,2,3,4) or end>len(body):torn=True;break
        records.append((channel,body[cursor+5:end]));cursor=end
    if len(records)!=count or (torn and status!=3) or (status==1 and charged!=actual):
        return dict(sealed=False)
    return dict(sealed=True,cap=cap,status=status,charged=charged,actual=actual,
                count=count,torn=torn,records=records,admitted=status==1 and not torn)


def validate():
    f,e=read(BASE/'freeze.json'),read(BASE/'exercise.json')
    assert sha(BASE/'exercise.json')==read(BASE/'exercise_seal.json')['sha256']
    for p,row in f['files'].items():
        assert sha(p)==row['sha256'] and Path(p).stat().st_size==row['bytes']
    assert [r['case'] for r in e['cases']]==f['cases'] and len(e['cases'])==15
    assert {p.name for p in (BASE/'fixtures').iterdir()}==set(f['cases'])
    results=[]
    negative_caps={'stdout_overflow','stderr_overflow','metadata_overflow','global_cap'}
    errors={name:'BufferError' for name in negative_caps}
    errors.update(collision='FileExistsError',short_write='OSError',invalid_type='ValueError',
                  after_close='RuntimeError',concurrent_open='FileExistsError',invalid_channel='ValueError')
    for row in e['cases']:
        name=row['case'];folder=BASE/'fixtures'/name
        assert row['expected_exception']==errors.get(name)
        expected={r['path'] for r in row['files']}
        assert expected=={p.name for p in folder.iterdir()}
        for entry in row['files']:
            p=folder/entry['path']
            assert sha(p)==entry['sha256'] and p.stat().st_size==entry['bytes']
        path=folder/'evidence.rdj';d=decode(path)
        if name=='collision':
            assert path.read_bytes()==b'PREEXISTING' and not d['sealed']
            results.append(dict(case=name,collision_preserved=True));continue
        assert d['sealed']
        obs=row['observation']
        for key,other in (('cap','cap'),('status','status'),('charged','reserved_body_bytes'),
                          ('actual','actual_body_bytes'),('count','complete_records')):
            assert d[key]==obs[other]
        assert obs['closed'] and path.stat().st_size==80+d['actual']<=d['cap']
        if name in negative_caps:
            assert d['status']==2 and d['actual']==d['charged']==d['count']==0 and not d['admitted']
        elif name in ('invalid_type','invalid_channel'):
            assert d['status']==4 and d['actual']==d['charged']==d['count']==0 and not d['admitted']
        elif name=='short_write':
            assert d['status']==3 and d['actual']==3 and d['charged']==5+len(b'preserve-full-reservation')
            assert d['torn'] and not d['admitted'] and d['count']==0
        else:
            assert d['admitted'] and d['status']==1 and not d['torn']
            if name=='normal':
                assert d['records']==[(i,b'channel'+str(i).encode()) for i in range(1,5)]
            elif name=='exact_fill':
                assert path.stat().st_size==d['cap']==256 and d['records']==[(1,b'x'*171)]
            elif name=='concurrent_open':assert d['records']==[(1,b'first-owner')]
            else:assert d['records']==[(1,b'fixed payload')]
        if name in ('corruption','truncated_footer'):
            assert not decode(folder/'invalid_copy.rdj')['sealed']
        namespace_complete=expected=={'evidence.rdj'}
        if name=='external_file':
            assert d['admitted'] and not namespace_complete
            assert sum(p.stat().st_size for p in folder.iterdir())>d['cap']
        elif name not in ('corruption','truncated_footer'):
            assert namespace_complete
        results.append(dict(case=name,single_file_sealed=d['sealed'],single_file_admitted=d['admitted'],
            bytes=path.stat().st_size,cap=d['cap'],charged=d['charged'],actual=d['actual'],
            namespace_complete=namespace_complete,
            whole_namespace_admitted=d['admitted'] and namespace_complete))
    result=dict(passed=True,frozen_identities=len(f['files']),cases=15,results=results,
        single_cooperating_file_bound_verified=True,arbitrary_external_writer_cap_guarantee=False,
        production_or_supervisor_integration=False,old_archive_or_fit_retry=False)
    with (BASE/'validation.json').open('x',encoding='utf-8') as stream:
        json.dump(result,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k!='results'}),flush=True)
