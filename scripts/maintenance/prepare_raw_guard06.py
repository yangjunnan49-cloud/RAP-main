"""One immutable request/response per nonce; retain all22 complete predictions."""
import time
START=time.monotonic()
import sys,resource,traceback,ast
from pathlib import Path
from datetime import datetime,timezone
import raw_input_system05 as d
def run():
    ok=False;error=None
    try:
        d.verify();assert not d.read(d.SUP/'run05/child_exit.json')['success']
        old=Path(d.__file__);source=old.read_text();original=source
        source=source.replace("('child_exit.json','exit.json','wrapper_exit.json')","('child_exit.json','exit.json','wrapper_exit.json','enclosing_upper_bound.json')")
        source=source.replace("target=SUP/'launch_guard_request.json';temporary=SUP/'launch_guard_request.tmp'","requests=SUP/'guard_requests06';requests.mkdir(exist_ok=True)\n    target=requests/(nonce+'.json');temporary=requests/(nonce+'.tmp')")
        source=source.replace("response=SUP/'launch_guard_response.json'","response=SUP/'guard_responses06'/(nonce+'.json')")
        marker="    for p,h in read(BASE/'GUARD05_FREEZE.json')['files'].items():assert sha(p)==h,p"
        source=source.replace(marker,marker+"\n    for p,h in read(BASE/'GUARD06_FREEZE.json')['files'].items():assert sha(p)==h,p")
        source=source.replace('RETAINED_RUN04_FREEZE','RETAINED_RUN05_FREEZE')
        for name in ('bank05','bank_seal05','evaluation05','results05','run05','evaluate05'):source=source.replace(name,name[:-2]+'06')
        # Retention alone references the previous completed bank and receipts.
        source=source.replace("shutil.copytree(BASE/'bank04'/key,BASE/'bank06'/key)","shutil.copytree(BASE/'bank05'/key,BASE/'bank06'/key)")
        source=source.replace("shutil.copy2(SUP/'run04'/key/'controller_exit.json'","shutil.copy2(SUP/'run05'/key/'controller_exit.json'")
        # Prepared05 evaluation-only route bug is fixed before any GT read.
        start=source.index('def evaluate():');end=source.index('def run(',start)
        source=source[:start]+source[start:end].replace("BASE/'bank04'","BASE/'bank06'")+source[end:]
        def fn(code,name):return ast.dump(next(n for n in ast.parse(code).body if isinstance(n,ast.FunctionDef) and n.name==name),include_attributes=False)
        assert fn(original.replace('bank05','bank06'),'worker')==fn(source,'worker')
        assert fn(original.replace('bank04','bank06').replace('bank_seal05','bank_seal06').replace('evaluation05','evaluation06').replace('results05','results06'),'evaluate')==fn(source,'evaluate')
        new=old.with_name('raw_input_system06.py');compile(source,str(new),'exec');new.write_text(source)
        launch=d.read(d.SUP/'run05/launch.json');begin=datetime.fromisoformat(launch['utc_start'][:26]+'+00:00');upper=datetime(2026,10,20,15,56,0,tzinfo=timezone.utc)
        d.save(d.SUP/'run05/enclosing_upper_bound.json',dict(wall_seconds=(upper-begin).total_seconds(),following_clock_utc=upper.isoformat(),kind='conservative inclusive upper bound; observer crashed before exit receipt; includes later diagnosis, not exact native duration'))
        sup=old.with_name('invoke_mgr_supervised_wsl.ps1');s=sup.read_text();token='    $taskMemory=Get-CimInstance Win32_PerfFormattedData_PerfOS_Memory\n    $taskSnapshot='
        assert s.count(token)==1
        pre="""    $taskRequests=Join-Path $taskOutput 'guard_requests06'; $taskResponses=Join-Path $taskOutput 'guard_responses06'
    if(-not(Test-Path -LiteralPath $taskResponses)){New-Item -ItemType Directory -Path $taskResponses|Out-Null}
    $taskPending=@()
    if(Test-Path -LiteralPath $taskRequests){$taskPending=@(Get-ChildItem -LiteralPath $taskRequests -Filter '*.json' | Where-Object {-not(Test-Path -LiteralPath (Join-Path $taskResponses $_.Name))} | ForEach-Object {Get-Content -LiteralPath $_.FullName -Raw|ConvertFrom-Json})}
"""
        s=s.replace(token,pre+token)
        s=s.replace('    $taskRows.Add($taskSnapshot)',"""    foreach($taskRequest in $taskPending){
        $taskResponse=[ordered]@{nonce=$taskRequest.nonce;utc=$taskSnapshot.utc;headroom_bytes=$taskSnapshot.headroom_bytes}
        $taskResponsePath=Join-Path $taskResponses ($taskRequest.nonce+'.json'); $taskResponseTmp=Join-Path $taskResponses ($taskRequest.nonce+'.tmp')
        [System.IO.File]::WriteAllText($taskResponseTmp,($taskResponse|ConvertTo-Json),[System.Text.UTF8Encoding]::new($false))
        [System.IO.File]::Move($taskResponseTmp,$taskResponsePath)
    }
    $taskRows.Add($taskSnapshot)""")
        ns=old.with_name('invoke_raw_guard06.ps1');ns.write_text(s)
        wrapper=old.with_name('launch_raw_input_run05.py');nw=wrapper.with_name('launch_raw_input_run06.py');nw.write_text(wrapper.read_text().replace('raw_input_system05','raw_input_system06').replace('run05','run06').replace('LAUNCH_BINDING05','LAUNCH_BINDING06'))
        keys=[];paths=[]
        for cell in d.read(d.BASE/'freeze.json')['schedule']:
            key=cell['key'];p=d.BASE/'bank05'/key
            if p.exists():
                assert d.read(p/'worker_exit.json')['success'];keys.append(key);paths.extend(q for q in p.rglob('*') if q.is_file());paths.append(d.SUP/'run05'/key/'controller_exit.json')
        assert len(keys)==22
        retained=d.BASE/'RETAINED_RUN05_FREEZE.json';d.save(retained,dict(utc=d.now(),keys=keys,files={str(p):d.sha(p) for p in paths},GT_numeric_read=False,no_replay=True))
        outputs=[]
        for a,b in [('audit_raw_input_bindings05.py','audit_raw_input_bindings06.py'),('deliver_raw_input_benchmark05.py','deliver_raw_input_benchmark06.py')]:
            p=old.with_name(b);t=old.with_name(a).read_text().replace('raw_input_system05','raw_input_system06')
            for name in ('bank05','bank_seal05','results05','run05'):t=t.replace(name,name[:-2]+'06')
            p.write_text(t);outputs.append(p)
        for p in [nw]+outputs:compile(p.read_text(),str(p),'exec')
        protocol=d.BASE/'GUARD06_PROTOCOL.md';protocol.write_text('''# Guard06 immutable nonce files

run05 observer crashed replacing a response pointer while it was being read (Access denied); owned controller then correctly failed the unchanged2s guard before the23rd cell. Both controller/wrapper exits are present. All22 complete predictions retained before GT,14 remaining. Failed stages and conservative run05 enclosing upper bound remain in original shared7200s. No parameter/gate/worker numerical changes or repeat selection.

Each nonce now has its own immutable request JSON and response JSON. Producer completes a private .tmp then moves to a new final filename once; consumers only read final JSON. Windows snapshots pending requests BEFORE new CIM measurement. Linux monotonic request-to-response<=2s and headroom>=12GiB remain. Completed responses are never replaced, avoiding the observed reader/replace conflict. Missing/late response still stops. No scheduler/other-process/default changes.
''')
        files=[Path(__file__),new,ns,nw,retained,protocol,d.SUP/'run05/enclosing_upper_bound.json',d.SUP/'run05/child_exit.json',d.SUP/'run05/wrapper_exit.json']+outputs
        d.save(d.BASE/'GUARD06_FREEZE.json',dict(utc=d.now(),files={str(p):d.sha(p) for p in files},numeric_worker_AST_equal=True,numeric_evaluation_AST_equal_after_route_fix=True,original2s12GiB7200s=True,retained22=True,remaining14=True,GT_numeric_read=False))
        print('Guard06 frozen:22 retained/14 new, unchanged math and caps',flush=True);ok=True
    except BaseException as e:error=repr(e);traceback.print_exc()
    finally:d.save(d.SUP/'prepare06/child_exit.json',dict(utc=d.now(),success=ok,error=error,wall_seconds=time.monotonic()-START,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,GPU_calls=0))
    if not ok:sys.exit(1)
if __name__=='__main__':assert sys.argv[1]=='prepare06';run()
