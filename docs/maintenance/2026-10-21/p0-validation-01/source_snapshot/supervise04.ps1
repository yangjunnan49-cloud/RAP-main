param([string]$Stage,[switch]$Test)
$ErrorActionPreference='Stop'
$taskRoot=$PSScriptRoot
$taskOut=Join-Path (Split-Path (Split-Path $taskRoot -Parent) -Parent) 'outputs\overlap_validation_20261021'
$taskOrigin=Get-Content -Raw -LiteralPath (Join-Path $taskRoot 'budget_origin.json')|ConvertFrom-Json
function Get-Elapsed {
    $taskMono=([Diagnostics.Stopwatch]::GetTimestamp()-$taskOrigin.initialization_ticks)/$taskOrigin.frequency+$taskOrigin.conservative_prelude_seconds
    $taskUtc=([DateTimeOffset]::UtcNow-[DateTimeOffset]$taskOrigin.start_utc).TotalSeconds
    return [Math]::Max($taskMono,$taskUtc)
}
function Get-StopReason($HostElapsed,$LinuxElapsed,$Limit,$Age,$Identity) {
    if(-not $Identity){return 'identity'}
    if($Age -gt 5){return 'heartbeat'}
    if([Math]::Max($HostElapsed,$LinuxElapsed) -ge $Limit){return 'deadline'}
    return ''
}
function Write-Atomic($Path,$Value) {
    $taskTemp=$Path+'.tmp'
    [IO.File]::WriteAllText($taskTemp,($Value|ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))
    [IO.File]::Move($taskTemp,$Path,$true)
}
if($Test){
    $taskCases=@(
        @{h=91;l=80;limit=90;age=0;identity=$true;expect='deadline'},
        @{h=80;l=91;limit=90;age=0;identity=$true;expect='deadline'},
        @{h=80;l=80;limit=90;age=6;identity=$true;expect='heartbeat'},
        @{h=80;l=80;limit=90;age=0;identity=$false;expect='identity'},
        @{h=80;l=80;limit=90;age=0;identity=$true;expect=''}
    )
    foreach($taskCase in $taskCases){if((Get-StopReason $taskCase.h $taskCase.l $taskCase.limit $taskCase.age $taskCase.identity) -ne $taskCase.expect){throw 'Guard fixture failed'}}
    Write-Atomic (Join-Path $taskRoot 'guard_fixtures.json') @{passed=$true;cases=$taskCases;elapsed=(Get-Elapsed)}
    Write-Output 'Five guard decision fixtures PASS';exit 0
}
if((Get-Elapsed) -ge 1140){throw 'Validation reserve reached before launch'}
$taskLog=Join-Path $taskOut ('supervision\'+$Stage)
if(Test-Path -LiteralPath $taskLog){throw 'Stage exists; preserve original failure'}
New-Item -ItemType Directory -Path $taskLog -Force|Out-Null
$taskMemTick=[Diagnostics.Stopwatch]::GetTimestamp()
$taskMemory=Get-CimInstance Win32_PerfFormattedData_PerfOS_Memory
$taskHeadroom=[long]$taskMemory.CommitLimit-[long]$taskMemory.CommittedBytes
if($taskHeadroom -lt 12GB -or (([Diagnostics.Stopwatch]::GetTimestamp()-$taskMemTick)/[Diagnostics.Stopwatch]::Frequency) -gt 2){throw 'Host prelaunch memory guard failed'}
Write-Atomic (Join-Path $taskRoot 'live_host.json') @{elapsed=(Get-Elapsed);utc=[DateTimeOffset]::UtcNow.ToString('o')}
$taskLinuxRoot='/mnt/c/Users/AAA/Documents/Codex/2026-10-21/y/work/overlap_validation_01'
$taskArgs=@('-d','Ubuntu-24.04','-u','root','--','/usr/bin/env','OMP_NUM_THREADS=1','MKL_NUM_THREADS=1','OPENBLAS_NUM_THREADS=1','CUDA_VISIBLE_DEVICES=','PYTHONDONTWRITEBYTECODE=1','/root/miniconda3/envs/rap-inference/bin/python','-u','-B',($taskLinuxRoot+'/validation_stage03.py'),$Stage)
$taskStart=[DateTimeOffset]::UtcNow;$taskTicks=[Diagnostics.Stopwatch]::GetTimestamp();$taskGlobalStart=Get-Elapsed
$taskProcess=Start-Process -FilePath 'wsl.exe' -ArgumentList $taskArgs -WindowStyle Hidden -RedirectStandardOutput (Join-Path $taskLog 'stdout.log') -RedirectStandardError (Join-Path $taskLog 'stderr.log') -PassThru
Write-Atomic (Join-Path $taskLog 'host_launch.json') @{pid=$taskProcess.Id;utc=$taskStart.ToString('o');global_elapsed=$taskGlobalStart;headroom_bytes=$taskHeadroom}
$taskReason='';$taskLastHB=[Diagnostics.Stopwatch]::GetTimestamp();$taskHBValue=-1;$taskHasResponse=$false
while(-not $taskProcess.HasExited){
    $taskElapsed=Get-Elapsed
    Write-Atomic (Join-Path $taskRoot 'live_host.json') @{elapsed=$taskElapsed;utc=[DateTimeOffset]::UtcNow.ToString('o')}
    $taskRequest=Join-Path $taskLog 'memory_request.json'
    if((Test-Path -LiteralPath $taskRequest) -and -not $taskHasResponse){
        $taskChallenge=Get-Content -Raw -LiteralPath $taskRequest|ConvertFrom-Json
        $taskFresh=Get-CimInstance Win32_PerfFormattedData_PerfOS_Memory
        Write-Atomic (Join-Path $taskLog 'memory_response.json') @{nonce=$taskChallenge.nonce;headroom_bytes=([long]$taskFresh.CommitLimit-[long]$taskFresh.CommittedBytes);utc=[DateTimeOffset]::UtcNow.ToString('o')}
        $taskHasResponse=$true
    }
    $taskLinuxElapsed=$taskGlobalStart
    $taskHBPath=Join-Path $taskLog 'linux_heartbeat.json'
    if(Test-Path -LiteralPath $taskHBPath){
        $taskHB=Get-Content -Raw -LiteralPath $taskHBPath|ConvertFrom-Json
        $taskLinuxElapsed=$taskHB.global_elapsed
        if($taskHB.monotonic -ne $taskHBValue){$taskLastHB=[Diagnostics.Stopwatch]::GetTimestamp();$taskHBValue=$taskHB.monotonic}
    }
    $taskAge=([Diagnostics.Stopwatch]::GetTimestamp()-$taskLastHB)/[Diagnostics.Stopwatch]::Frequency
    $taskLimit=1140
    if($Stage -like 'probe*'){$taskLimit=[Math]::Min(1140,$taskGlobalStart+2)}
    $taskReason=Get-StopReason $taskElapsed $taskLinuxElapsed $taskLimit $taskAge $true
    if($taskReason){
        $taskOwned=Join-Path $taskLog 'owned_session.json'
        if(-not(Test-Path -LiteralPath $taskOwned)){throw 'No identified owned process; refusing broad stop'}
        & wsl -d Ubuntu-24.04 -u root -- /root/miniconda3/envs/rap-inference/bin/python -B ($taskLinuxRoot+'/stop_owned03.py') ($taskLinuxRoot.Replace('/work/overlap_validation_01','/outputs/overlap_validation_20261021')+'/supervision/'+$Stage+'/owned_session.json')
        if($LASTEXITCODE -ne 0){throw 'Owned stop failed'}
        break
    }
    Start-Sleep -Milliseconds 100;$taskProcess.Refresh()
}
if(-not $taskProcess.WaitForExit(5000)){throw 'Identified stop did not finish within reserve'}
$taskProcess.Refresh();$taskWall=([DateTimeOffset]::UtcNow-$taskStart).TotalSeconds
$taskMono=([Diagnostics.Stopwatch]::GetTimestamp()-$taskTicks)/[Diagnostics.Stopwatch]::Frequency
$taskExit=@{exit_code=$taskProcess.ExitCode;host_wall_seconds=$taskWall;host_monotonic_seconds=$taskMono;global_elapsed=(Get-Elapsed);stop_reason=$taskReason;expected_probe_stop=($Stage -like 'probe*' -and $taskReason -eq 'deadline')}
Write-Atomic (Join-Path $taskLog 'host_exit.json') $taskExit
Get-Content -LiteralPath (Join-Path $taskLog 'stdout.log') -Tail 4
if($taskProcess.ExitCode -ne 0 -and -not $taskExit.expected_probe_stop){Get-Content -LiteralPath (Join-Path $taskLog 'stderr.log') -Tail 25}
Write-Output ($taskExit|ConvertTo-Json -Compress)
if($taskExit.expected_probe_stop){exit 0};exit $taskProcess.ExitCode



