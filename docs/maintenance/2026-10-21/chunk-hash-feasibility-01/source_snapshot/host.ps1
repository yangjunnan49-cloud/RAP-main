param([Parameter(Mandatory=$true)][string]$Case,[string]$Run='run01')
$ErrorActionPreference='Stop'
$root=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$out=Join-Path $root ('outputs/chunk_hash_feasibility_20261021/'+$Run+'/'+$Case)
$linuxRoot='/mnt/c/Users/AAA/Documents/Codex/2026-10-21/y/work/chunk_hash_feasibility_01'
$linuxOut='/mnt/c/Users/AAA/Documents/Codex/2026-10-21/y/outputs/chunk_hash_feasibility_20261021/'+$Run+'/'+$Case
$origin=Get-Content -Raw (Join-Path $PSScriptRoot 'origin.json') | ConvertFrom-Json
function ScopeElapsed { [Math]::Max(([DateTimeOffset]::UtcNow-[DateTimeOffset]$origin.start_utc).TotalSeconds,([Diagnostics.Stopwatch]::GetTimestamp()-[double]$origin.start_ticks)/[double]$origin.frequency) }
function WriteJson($Path,$Value) { [IO.File]::WriteAllText($Path,($Value | ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false)) }
if(Test-Path -LiteralPath $out){throw 'Preserve all earlier cases'}
New-Item -ItemType Directory -Path $out | Out-Null
if((ScopeElapsed) -ge 480){throw 'Whole-scope close reserve reached'}
$pre=[Diagnostics.Stopwatch]::GetTimestamp();$memory=Get-CimInstance Win32_PerfFormattedData_PerfOS_Memory
$headroom=[long]$memory.CommitLimit-[long]$memory.CommittedBytes
if($headroom -lt 12GB -or ([Diagnostics.Stopwatch]::GetTimestamp()-$pre)/[Diagnostics.Stopwatch]::Frequency -gt 2){throw 'Fresh prelaunch memory guard'}
$hostCap=90.;$linuxCap=90.
if($Case -eq 'host_deadline'){$hostCap=3.}
if($Case -eq 'linux_deadline'){$linuxCap=3.}
$start=[DateTimeOffset]::UtcNow;$tick=[Diagnostics.Stopwatch]::GetTimestamp();$responses=0;$forced=$false;$identityRejected=$false
$args=@('-d','Ubuntu-24.04','-u','root','--','/usr/bin/env','CUDA_VISIBLE_DEVICES=','PYTHONDONTWRITEBYTECODE=1','/root/miniconda3/envs/rap-inference/bin/python','-B',($linuxRoot+'/lease_runner.py'),$linuxOut,$Case,$linuxCap,(ScopeElapsed))
$process=Start-Process -FilePath 'wsl.exe' -ArgumentList $args -WindowStyle Hidden -RedirectStandardOutput (Join-Path $out 'stdout.log') -RedirectStandardError (Join-Path $out 'stderr.log') -PassThru
WriteJson (Join-Path $out 'host_launch.json') @{wsl_pid=$process.Id;utc=$start.ToString('o');headroom_bytes=$headroom;host_cap=$hostCap;linux_cap=$linuxCap;scope_elapsed=(ScopeElapsed)}
while(-not $process.HasExited){
    $stage=[Math]::Max(([DateTimeOffset]::UtcNow-$start).TotalSeconds,([Diagnostics.Stopwatch]::GetTimestamp()-$tick)/[Diagnostics.Stopwatch]::Frequency)
    if($stage -ge $hostCap -or (ScopeElapsed) -ge 480){
        if(-not(Test-Path -LiteralPath (Join-Path $out 'runner_owned.json'))){throw 'No owned identity; refuse broad termination'}
        & wsl -d Ubuntu-24.04 -u root -- /root/miniconda3/envs/rap-inference/bin/python -B ($linuxRoot+'/stop_identity.py') ($linuxOut+'/runner_owned.json') runner
        if($LASTEXITCODE -ne 0){throw 'Exact watcher stop failed'}
        $forced=$true;break
    }
    foreach($request in Get-ChildItem -LiteralPath $out -Filter '*_request.json'){
        $response=$request.FullName.Replace('_request.json','_response.json')
        if(Test-Path -LiteralPath $response){continue}
        $req=Get-Content -Raw -LiteralPath $request.FullName | ConvertFrom-Json
        $memory=Get-CimInstance Win32_PerfFormattedData_PerfOS_Memory
        $nonce=$req.nonce;$available=[long]$memory.CommitLimit-[long]$memory.CommittedBytes
        if($Case -eq 'bad_nonce' -and $responses -eq 1){$nonce='synthetic-wrong-nonce'}
        if($Case -eq 'headroom_fault' -and $responses -eq 1){$available=1}
        $value=@{nonce=$nonce;sequence=$req.sequence;headroom_bytes=$available;stage_elapsed=[Math]::Max(([DateTimeOffset]::UtcNow-$start).TotalSeconds,([Diagnostics.Stopwatch]::GetTimestamp()-$tick)/[Diagnostics.Stopwatch]::Frequency);scope_elapsed=(ScopeElapsed);labelled_fault=$Case}
        $temp=$response+'.tmp';WriteJson $temp $value;[IO.File]::Move($temp,$response);$responses++
        if($Case -eq 'observer_loss' -and $responses -eq 2){WriteJson (Join-Path $out 'intentional_observer_exit.json') @{expected=$true;after_responses=$responses};exit 17}
    }
    if($Case -eq 'identity_rejection' -and $responses -ge 2){
        $forged=Get-Content -Raw (Join-Path $out 'runner_owned.json') | ConvertFrom-Json
        $forged.start_ticks='-1';WriteJson (Join-Path $out 'forged_owned.json') $forged
        & wsl -d Ubuntu-24.04 -u root -- /root/miniconda3/envs/rap-inference/bin/python -B ($linuxRoot+'/stop_identity.py') ($linuxOut+'/forged_owned.json') runner 2> (Join-Path $out 'expected_identity_rejection.log')
        if($LASTEXITCODE -eq 0){throw 'Forged identity accepted'}
        $process.Refresh();if($process.HasExited){throw 'Forged identity killed watcher'}
        $identityRejected=$true
        & wsl -d Ubuntu-24.04 -u root -- /root/miniconda3/envs/rap-inference/bin/python -B ($linuxRoot+'/stop_identity.py') ($linuxOut+'/runner_owned.json') runner
        if($LASTEXITCODE -ne 0){throw 'Correct identity cleanup failed'}
        $forced=$true;break
    }
    Start-Sleep -Milliseconds 40;$process.Refresh()
}
if(-not $process.WaitForExit(5000)){throw 'Owned watcher did not finish cleanup'}
$process.Refresh()
WriteJson (Join-Path $out 'host_exit.json') @{exit_code=$process.ExitCode;responses=$responses;forced_stop=$forced;identity_rejection_pass=$identityRejected;stage_seconds=[Math]::Max(([DateTimeOffset]::UtcNow-$start).TotalSeconds,([Diagnostics.Stopwatch]::GetTimestamp()-$tick)/[Diagnostics.Stopwatch]::Frequency);scope_elapsed=(ScopeElapsed)}
exit 0
