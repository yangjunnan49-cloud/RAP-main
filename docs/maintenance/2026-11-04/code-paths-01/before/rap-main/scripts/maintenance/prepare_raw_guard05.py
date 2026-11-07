"""Preserve run04; replace cross-host wall-clock freshness with nonce round trip."""
import time
START=time.monotonic()
import sys,resource,traceback,ast
from pathlib import Path
import raw_input_system04 as d
BASE=d.BASE;SUP=d.SUP
def run():
    ok=False;error=None
    try:
        d.verify();assert d.used()<7200
        assert not d.read(SUP/'run04/child_exit.json')['success']
        source=Path(d.__file__).read_text();original=source
        start=source.index('def guard():');end=source.index('def module(',start)
        source=source[:start]+'''def guard():
    import uuid
    nonce=uuid.uuid4().hex;begin=time.monotonic()
    target=SUP/'launch_guard_request.json';temporary=SUP/'launch_guard_request.tmp'
    save(temporary,dict(nonce=nonce,utc=now()));os.replace(temporary,target)
    while time.monotonic()-begin<=2.:
        response=SUP/'launch_guard_response.json'
        if response.exists():
            data=read(response)
            if data['nonce']==nonce:
                elapsed=time.monotonic()-begin
                assert 0<=elapsed<=2.,('stale launch challenge',elapsed)
                assert data['headroom_bytes']>=12*2**30,('launch guard',data['headroom_bytes'])
                return dict(utc=now(),observed_utc=data['utc'],roundtrip_seconds=elapsed,nonce=nonce,headroom_bytes=data['headroom_bytes'],freshness_basis='request before host CIM; response before consume; Linux monotonic <=2s')
        time.sleep(.01)
    raise TimeoutError('No fresh host response within original 2 seconds')

'''+source[end:]
        # Shared account includes all enclosing clocks, including a failed wrapper.
        source=source.replace("('child_exit.json','exit.json')","('child_exit.json','exit.json','wrapper_exit.json')")
        marker="    for p,h in read(BASE/'S1_EXECUTION_FREEZE.json')['files'].items():assert sha(p)==h,p"
        assert source.count(marker)==1
        source=source.replace(marker,marker+"\n    for p,h in read(BASE/'GUARD05_FREEZE.json')['files'].items():assert sha(p)==h,p")
        start=source.index("    retained=read(BASE/'RETAINED_K1_FREEZE.json')");end=source.index('        launch=guard();',start)
        source=source[:start]+'''    retained=read(BASE/'RETAINED_RUN04_FREEZE.json')
    for p,h in retained['files'].items():assert sha(p)==h,p
    import shutil
    for key in retained['keys']:
        shutil.copytree(BASE/'bank04'/key,BASE/'bank05'/key)
        folder=SUP/'run05'/key;folder.mkdir()
        shutil.copy2(SUP/'run04'/key/'controller_exit.json',folder/'controller_exit.json')
        save(folder/'retained.json',dict(original_complete_cell=True,no_rerun=True,clock_already_charged=True))
    for cell in f['schedule']:
        if cell['key'] in retained['keys']:continue
'''+source[end:]
        for a,b in [('bank04','bank05'),('bank_seal04','bank_seal05'),('evaluation04','evaluation05'),('results04','results05'),('run04','run05'),('evaluate04','evaluate05')]:
            # Retained source bank and receipts must still refer to run04.
            if a in ('bank04','run04'):continue
            source=source.replace(a,b)
        source=source.replace("dest=BASE/'bank04'","dest=BASE/'bank05'").replace("dest=BASE/'bank04'/key","dest=BASE/'bank05'/key").replace("BASE/'bank04'/p","BASE/'bank05'/p").replace("BASE/'bank04'/cell['key']","BASE/'bank05'/cell['key']").replace("(BASE/'bank04').mkdir()","(BASE/'bank05').mkdir()")
        source=source.replace("SUP/'run04'/cell['key']","SUP/'run05'/cell['key']").replace("'run04':run_bank","'run05':run_bank")
        def fn(code,name):return ast.dump(next(n for n in ast.parse(code).body if isinstance(n,ast.FunctionDef) and n.name==name),include_attributes=False)
        # Worker must change only its output route, not numerical work.
        assert fn(original.replace("BASE/'bank04'","BASE/'bank05'"),'worker')==fn(source,'worker')
        assert fn(original,'config')==fn(source,'config')
        new=Path(__file__).with_name('raw_input_system05.py');compile(source,str(new),'exec');new.write_text(source)
        sup=Path(__file__).with_name('invoke_mgr_supervised_wsl.ps1');s=sup.read_text()
        token='    $taskMemory=Get-CimInstance Win32_PerfFormattedData_PerfOS_Memory\n    $taskSnapshot='
        assert s.count(token)==1
        s=s.replace(token,"    $taskRequestPath=Join-Path $taskOutput 'launch_guard_request.json'\n    $taskRequest=$null\n    if(Test-Path -LiteralPath $taskRequestPath){$taskRequest=Get-Content -LiteralPath $taskRequestPath -Raw|ConvertFrom-Json}\n"+token)
        token='    $taskRows.Add($taskSnapshot)'
        s=s.replace(token,"    if($null -ne $taskRequest){\n        $taskResponse=[ordered]@{nonce=$taskRequest.nonce;utc=$taskSnapshot.utc;headroom_bytes=$taskSnapshot.headroom_bytes}\n        $taskResponsePath=Join-Path $taskOutput 'launch_guard_response.json';$taskResponseTmp=Join-Path $taskOutput 'launch_guard_response.tmp'\n        [System.IO.File]::WriteAllText($taskResponseTmp,($taskResponse|ConvertTo-Json),[System.Text.UTF8Encoding]::new($false))\n        [System.IO.File]::Move($taskResponseTmp,$taskResponsePath,$true)\n    }\n"+token)
        newsup=sup.with_name('invoke_raw_guard05.ps1');newsup.write_text(s)
        wrapper=Path(__file__).with_name('launch_raw_input_run04.py');ws=wrapper.read_text().replace('raw_input_system04','raw_input_system05').replace('run04','run05').replace('LAUNCH_BINDING04','LAUNCH_BINDING05')
        nw=wrapper.with_name('launch_raw_input_run05.py');compile(ws,str(nw),'exec');nw.write_text(ws)
        retained=[];paths=[]
        for cell in d.read(BASE/'freeze.json')['schedule']:
            key=cell['key'];p=BASE/'bank04'/key
            if p.exists():
                assert d.read(p/'worker_exit.json')['success'];retained.append(key);paths.extend(q for q in p.rglob('*') if q.is_file());paths.append(SUP/'run04'/key/'controller_exit.json')
        assert len(retained)==5
        d.save(BASE/'RETAINED_RUN04_FREEZE.json',dict(utc=d.now(),keys=retained,files={str(p):d.sha(p) for p in paths},GT_numeric_read=False,no_rerun=True))
        audit=Path(__file__).with_name('audit_raw_input_bindings04.py');na=audit.with_name('audit_raw_input_bindings05.py');na.write_text(audit.read_text().replace('raw_input_system04','raw_input_system05').replace('bank_seal04','bank_seal05').replace('bank04','bank05'))
        delivery=Path(__file__).with_name('deliver_raw_input_benchmark.py');nd=delivery.with_name('deliver_raw_input_benchmark05.py');nd.write_text(delivery.read_text().replace('raw_input_system04','raw_input_system05').replace('results04','results05').replace('bank_seal04','bank_seal05').replace('bank04','bank05').replace('run04','run05'))
        for p in (na,nd):compile(p.read_text(),str(p),'exec')
        explanation='''# Guard05: bounded challenge response, no protection relaxation

run04 completed five cells and stopped before G06 launch because Windows UTC observation was 0.045564 seconds ahead of Linux UTC. The original implementation already reads the file before sampling Linux UTC; an ordinary Python read-order fix would be incorrect. Cross-host clock discrepancy is observed; its OS cause is UNKNOWN.

Preserve failed run04 source/receipts and all five complete cells byte-for-byte; no metric read, no replay or best-run selection. New run05 continues the original remaining31 cells under the same7200s shared account, including the773.4728936s failed enclosing run04. New output routes do not overwrite old files. Algorithm/config/prepared byte/source-E0 gates unchanged.

Linux issues a unique nonce, then Windows reads that nonce BEFORE a new CIM memory measurement and publishes the response. Linux accepts matching nonce only when its local monotonic request-to-consume interval is <=2s and the measured headroom is >=12GiB. Thus actual measurement-to-consume time is bounded by the original2s even with different UTC clocks. No absolute clock-offset epsilon, negative-age clamp, cached response acceptance, relaxed freshness/headroom or process control. A missing/late response fails the guard.
'''
        ep=BASE/'GUARD05_PROTOCOL.md';ep.write_text(explanation)
        files=[Path(__file__),new,newsup,nw,na,nd,ep,BASE/'RETAINED_RUN04_FREEZE.json',BASE/'S1_EXECUTION_FREEZE.json',SUP/'run04/child_exit.json',SUP/'run04/exit.json',SUP/'run04/wrapper_exit.json']
        d.save(BASE/'GUARD05_FREEZE.json',dict(utc=d.now(),files={str(p):d.sha(p) for p in files},retained=5,remaining=31,GT_numeric_read=False,numeric_worker_AST_unchanged=True,original_2s_and_12GiB=True,shared_charged_before_prepare=d.used()))
        print('Guard05 frozen:5 retained/31 new, no GT, unchanged2s/12GiB/7200s',flush=True);ok=True
    except BaseException as e:error=repr(e);traceback.print_exc()
    finally:d.save(SUP/'prepare05/child_exit.json',dict(utc=d.now(),success=ok,error=error,wall_seconds=time.monotonic()-START,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,GPU_calls=0))
    if not ok:sys.exit(1)
if __name__=='__main__':assert sys.argv[1]=='prepare05';run()
