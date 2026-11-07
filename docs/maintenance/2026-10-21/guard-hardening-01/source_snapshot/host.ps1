param([Parameter(Mandatory=$true)][string]$Case)
$ErrorActionPreference='Stop'
$taskRoot=$PSScriptRoot;$taskOut=Join-Path (Split-Path (Split-Path $taskRoot -Parent) -Parent) ('outputs\guard_hardening_20261021\'+$Case)
if(Test-Path -LiteralPath $taskOut){throw 'Case exists; preserve failures'}
New-Item -ItemType Directory -Path $taskOut|Out-Null
$taskLinux='/mnt/c/Users/AAA/Documents/Codex/2026-10-21/y/work/guard_hardening_01'
$taskOrigin=Get-Content -Raw -LiteralPath (Join-Path $taskRoot 'origin.json')|ConvertFrom-Json
function Elapsed {return [Math]::Max((([Diagnostics.Stopwatch]::GetTimestamp()-$taskOrigin.initialization_ticks)/$taskOrigin.frequency+$taskOrigin.conservative_prelude),([DateTimeOffset]::UtcNow-[DateTimeOffset]$taskOrigin.start_utc).TotalSeconds)}
function Write-Once($Path,$Object){[IO.File]::WriteAllText($Path,($Object|ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))}
if((Elapsed) -ge 330){throw 'Hardening close reserve reached'}
$taskPre=[Diagnostics.Stopwatch]::GetTimestamp();$taskMem=Get-CimInstance Win32_PerfFormattedData_PerfOS_Memory
if(([long]$taskMem.CommitLimit-[long]$taskMem.CommittedBytes) -lt 12GB -or (([Diagnostics.Stopwatch]::GetTimestamp()-$taskPre)/[Diagnostics.Stopwatch]::Frequency) -gt 2){throw 'Fresh prelaunch memory guard'}
$taskHostCap=10.;$taskChildCap=10.;$taskDuration=100.
if($Case -eq 'normal'){$taskHostCap=3.;$taskChildCap=3.;$taskDuration=.6}
if($Case -eq 'host_deadline'){$taskHostCap=1.2}
if($Case -eq 'linux_deadline'){$taskChildCap=1.2}
$taskStart=[DateTimeOffset]::UtcNow;$taskTick=[Diagnostics.Stopwatch]::GetTimestamp()
$taskArgs=@('-d','Ubuntu-24.04','-u','root','--','/usr/bin/env','PYTHONDONTWRITEBYTECODE=1','CUDA_VISIBLE_DEVICES=','/root/miniconda3/envs/rap-inference/bin/python','-u','-B',($taskLinux+'/guard_child.py'),$Case,$taskChildCap,$taskDuration)
$taskProcess=Start-Process -FilePath 'wsl.exe' -ArgumentList $taskArgs -WindowStyle Hidden -RedirectStandardOutput (Join-Path $taskOut 'stdout.log') -RedirectStandardError (Join-Path $taskOut 'stderr.log') -PassThru
Write-Once (Join-Path $taskOut 'host_launch.json') @{pid=$taskProcess.Id;utc=$taskStart.ToString('o');host_cap=$taskHostCap;child_cap=$taskChildCap;fault_injection=($taskHostCap -ne $taskChildCap)}
$taskResponses=0;$taskStopped=$false;$taskIdentityTest=$null
while(-not $taskProcess.HasExited){
    $taskMono=([Diagnostics.Stopwatch]::GetTimestamp()-$taskTick)/[Diagnostics.Stopwatch]::Frequency
    $taskWall=([DateTimeOffset]::UtcNow-$taskStart).TotalSeconds
    $taskElapsed=[Math]::Max($taskMono,$taskWall)
    if((Elapsed) -ge 330 -or $taskElapsed -ge $taskHostCap){
        $taskOwned=Join-Path $taskOut 'owned.json'
        if(-not(Test-Path -LiteralPath $taskOwned)){throw 'No identity; refuse broad termination'}
        & wsl -d Ubuntu-24.04 -u root -- /root/miniconda3/envs/rap-inference/bin/python -B ($taskLinux+'/stop_owned.py') ($taskLinux.Replace('/work/guard_hardening_01','/outputs/guard_hardening_20261021')+'/'+$Case+'/owned.json')
        if($LASTEXITCODE -ne 0){throw 'Exact stop failed'};$taskStopped=$true;break
    }
    foreach($taskRequest in Get-ChildItem -LiteralPath $taskOut -Filter '*_request.json'){
        $taskResponse=$taskRequest.FullName.Replace('_request.json','_response.json')
        if(Test-Path -LiteralPath $taskResponse){continue}
        $taskReq=Get-Content -Raw -LiteralPath $taskRequest.FullName|ConvertFrom-Json
        $taskMem=Get-CimInstance Win32_PerfFormattedData_PerfOS_Memory
        $taskNonce=$taskReq.nonce
        if($Case -eq 'bad_nonce' -and $taskResponses -eq 1){$taskNonce='intentionally-wrong'}
        $taskObject=@{nonce=$taskNonce;sequence=$taskReq.sequence;host_elapsed=[Math]::Max((([Diagnostics.Stopwatch]::GetTimestamp()-$taskTick)/[Diagnostics.Stopwatch]::Frequency),([DateTimeOffset]::UtcNow-$taskStart).TotalSeconds);headroom_bytes=([long]$taskMem.CommitLimit-[long]$taskMem.CommittedBytes)}
        $taskTemp=$taskResponse+'.tmp';Write-Once $taskTemp $taskObject;[IO.File]::Move($taskTemp,$taskResponse);$taskResponses++
        if($Case -eq 'observer_loss' -and $taskResponses -eq 2){
            Write-Once (Join-Path $taskOut 'intentional_observer_exit.json') @{expected=$true;after_responses=$taskResponses;elapsed=$taskElapsed;wsl_pid=$taskProcess.Id}
            exit 17
        }
    }
    if($Case -eq 'identity_rejection' -and $taskResponses -ge 2){
        $taskOwned=Get-Content -Raw -LiteralPath (Join-Path $taskOut 'owned.json')|ConvertFrom-Json
        $taskOwned.start_ticks='-1';Write-Once (Join-Path $taskOut 'forged_owned.json') $taskOwned
        & wsl -d Ubuntu-24.04 -u root -- /root/miniconda3/envs/rap-inference/bin/python -B ($taskLinux+'/stop_owned.py') ($taskLinux.Replace('/work/guard_hardening_01','/outputs/guard_hardening_20261021')+'/'+$Case+'/forged_owned.json') 2> (Join-Path $taskOut 'expected_identity_rejection.log')
        if($LASTEXITCODE -eq 0){throw 'Forged identity accepted'}
        $taskProcess.Refresh();if($taskProcess.HasExited){throw 'Wrong identity stop killed child'}
        $taskIdentityTest=$true
        & wsl -d Ubuntu-24.04 -u root -- /root/miniconda3/envs/rap-inference/bin/python -B ($taskLinux+'/stop_owned.py') ($taskLinux.Replace('/work/guard_hardening_01','/outputs/guard_hardening_20261021')+'/'+$Case+'/owned.json')
        if($LASTEXITCODE -ne 0){throw 'Identity test cleanup failed'};$taskStopped=$true;break
    }
    Start-Sleep -Milliseconds 40;$taskProcess.Refresh()
}
if(-not $taskProcess.WaitForExit(5000)){throw 'Owned child failed to exit'}
$taskProcess.Refresh()
Write-Once (Join-Path $taskOut 'host_exit.json') @{exit_code=$taskProcess.ExitCode;host_wall_seconds=([DateTimeOffset]::UtcNow-$taskStart).TotalSeconds;host_monotonic_seconds=([Diagnostics.Stopwatch]::GetTimestamp()-$taskTick)/[Diagnostics.Stopwatch]::Frequency;responses=$taskResponses;exact_stop=$taskStopped;identity_rejection_passed=$taskIdentityTest;global_elapsed=(Elapsed)}
exit 0
