"""Bounded WSL supervisor with reliable subprocess return codes."""
import json,os,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]


def now():return datetime.now(timezone.utc).isoformat()


def memory():
    command="$m=Get-CimInstance Win32_PerfFormattedData_PerfOS_Memory; [ordered]@{committed_bytes=[long]$m.CommittedBytes;commit_limit_bytes=[long]$m.CommitLimit;available_physical_bytes=[long]$m.AvailableBytes}|ConvertTo-Json -Compress"
    raw=subprocess.check_output(['powershell.exe','-NoProfile','-Command',command],text=True)
    row=json.loads(raw.strip())
    row['headroom_bytes']=row['commit_limit_bytes']-row['committed_bytes']
    row['utc']=now()
    return row


def main():
    script,stage,output=sys.argv[1:4]
    task_script=(ROOT/script).resolve();task_output=(ROOT/output).resolve()
    assert ROOT in task_script.parents and ROOT in task_output.parents
    before=memory();assert before['headroom_bytes']>=12*2**30,before
    folder=task_output/stage;folder.mkdir(parents=True,exist_ok=False)
    args=['wsl.exe','-d','Ubuntu-24.04','-u','root','--','/usr/bin/env',
        'OMP_NUM_THREADS=1','MKL_NUM_THREADS=1','OPENBLAS_NUM_THREADS=1',
        '/root/miniconda3/envs/rap-inference/bin/python','-u','-B',script,stage]
    start=time.monotonic()
    with (folder/'stdout.log').open('wb') as stdout,(folder/'stderr.log').open('wb') as stderr:
        process=subprocess.Popen(args,cwd=ROOT,stdout=stdout,stderr=stderr)
        (folder/'launch.json').write_text(json.dumps(dict(pid=process.pid,utc_start=now(),
            script=script,stage=stage,headroom_before_bytes=before['headroom_bytes'],
            supervisor='python_subprocess_returncode'),indent=2)+'\n')
        rows=[];next_sample=0.
        while process.poll() is None:
            if time.monotonic()-start>=next_sample:
                row=memory();rows.append(row)
                with (folder/'host_memory.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(row)+'\n')
                temporary=task_output/'host_latest.tmp'
                temporary.write_text(json.dumps(row,indent=2)+'\n');os.replace(temporary,task_output/'host_latest.json')
                next_sample=time.monotonic()-start+5.
            time.sleep(.1)
        returncode=process.wait()
    result=dict(exit_code=returncode,utc_end=now(),wall_seconds=time.monotonic()-start,
        host_memory_observations=len(rows),
        minimum_observed_headroom_bytes=min(x['headroom_bytes'] for x in rows))
    (folder/'exit.json').write_text(json.dumps(result,indent=2)+'\n')
    print((folder/'stdout.log').read_text(encoding='utf-8',errors='replace')[-8000:])
    if returncode:print((folder/'stderr.log').read_text(encoding='utf-8',errors='replace')[-8000:])
    print(json.dumps(result))
    return returncode


if __name__=='__main__':sys.exit(main())
