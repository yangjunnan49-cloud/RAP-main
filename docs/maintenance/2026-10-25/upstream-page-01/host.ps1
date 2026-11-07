$ErrorActionPreference='Stop'
$taskRoot=$PSScriptRoot
$taskOut=Join-Path $taskRoot 'run01'
if(Test-Path -LiteralPath $taskOut){throw 'Preserve original attempt; no retries'}
$taskStart=[DateTimeOffset]::UtcNow;$taskTick=[Diagnostics.Stopwatch]::GetTimestamp()
New-Item -ItemType Directory -Path $taskOut | Out-Null
function TaskWrite($Path,$Value){[IO.File]::WriteAllText($Path,($Value | ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))}
TaskWrite (Join-Path $taskOut 'ATTEMPT_ORIGIN.json') @{UTC=$taskStart.ToString('o');ticks=$taskTick;frequency=[Diagnostics.Stopwatch]::Frequency;whole_attempt_cap_seconds=120;worker_deadline_seconds=60}
$taskQueryTick=[Diagnostics.Stopwatch]::GetTimestamp()
$taskMemory=Get-CimInstance Win32_PerfFormattedData_PerfOS_Memory
$taskQuerySeconds=([Diagnostics.Stopwatch]::GetTimestamp()-$taskQueryTick)/[Diagnostics.Stopwatch]::Frequency
$taskHeadroom=[long]$taskMemory.CommitLimit-[long]$taskMemory.CommittedBytes
TaskWrite (Join-Path $taskOut 'PREFLIGHT.json') @{headroom_bytes=$taskHeadroom;query_seconds=$taskQuerySeconds;required_bytes=12884901888}
if($taskHeadroom -lt 12GB -or $taskQuerySeconds -gt 2){throw 'Original fresh host resource gate failed; stop'}
$taskExe='C:\Users\AAA\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$taskProcess=Start-Process -FilePath $taskExe -ArgumentList @('-I','-B',(Join-Path $taskRoot 'fetch.py'),$taskOut) -WindowStyle Hidden -RedirectStandardOutput (Join-Path $taskOut 'stdout.log') -RedirectStandardError (Join-Path $taskOut 'stderr.log') -PassThru
$taskPeak=0L;$taskForced=$false;$taskError=$null;$taskReplies=0
TaskWrite (Join-Path $taskOut 'OWNED_PROCESS.json') @{PID=$taskProcess.Id;start_UTC=$taskProcess.StartTime.ToUniversalTime().ToString('o');script=(Join-Path $taskRoot 'fetch.py');script_sha256=(Get-FileHash -LiteralPath (Join-Path $taskRoot 'fetch.py') -Algorithm SHA256).Hash}
try{
    while(-not $taskProcess.HasExited){
        $taskProcess.Refresh();$taskPeak=[Math]::Max($taskPeak,$taskProcess.PeakWorkingSet64)
        $taskElapsed=[Math]::Max(([DateTimeOffset]::UtcNow-$taskStart).TotalSeconds,([Diagnostics.Stopwatch]::GetTimestamp()-$taskTick)/[Diagnostics.Stopwatch]::Frequency)
        if($taskElapsed -ge 60 -or $taskPeak -gt 128MB){throw 'Owned worker deadline/RSS cap'}
        foreach($taskRequest in Get-ChildItem -LiteralPath $taskOut -Filter '*.request.json'){
            if($taskRequest.Name -notlike 'lease-*'){continue}
            $taskReply=$taskRequest.FullName.Replace('.request.json','.response.json')
            if(Test-Path -LiteralPath $taskReply){continue}
            $taskReq=Get-Content -Raw -Encoding utf8 -LiteralPath $taskRequest.FullName | ConvertFrom-Json
            $taskQueryTick=[Diagnostics.Stopwatch]::GetTimestamp();$taskMemory=Get-CimInstance Win32_PerfFormattedData_PerfOS_Memory
            $taskQuerySeconds=([Diagnostics.Stopwatch]::GetTimestamp()-$taskQueryTick)/[Diagnostics.Stopwatch]::Frequency
            $taskHeadroom=[long]$taskMemory.CommitLimit-[long]$taskMemory.CommittedBytes
            if($taskHeadroom -lt 12GB -or $taskQuerySeconds -gt 2){throw 'Fresh host resource lease failed'}
            $taskTemp=$taskReply+'.tmp';TaskWrite $taskTemp @{nonce=$taskReq.nonce;sequence=$taskReq.sequence;headroom_bytes=$taskHeadroom;query_seconds=$taskQuerySeconds}
            [IO.File]::Move($taskTemp,$taskReply);$taskReplies++
        }
        Start-Sleep -Milliseconds 25
    }
}catch{$taskError=$_.Exception.Message;if(-not $taskProcess.HasExited){$taskProcess.Kill();$taskForced=$true}}
$taskProcess.WaitForExit();$taskProcess.Refresh();$taskPeak=[Math]::Max($taskPeak,$taskProcess.PeakWorkingSet64)
$taskElapsed=[Math]::Max(([DateTimeOffset]::UtcNow-$taskStart).TotalSeconds,([Diagnostics.Stopwatch]::GetTimestamp()-$taskTick)/[Diagnostics.Stopwatch]::Frequency)
TaskWrite (Join-Path $taskOut 'HOST_EXIT.json') @{exit_code=$taskProcess.ExitCode;forced_stop=$taskForced;error=$taskError;elapsed_seconds=$taskElapsed;observed_native_peak_working_set_bytes=$taskPeak;fresh_leases=$taskReplies;no_live_owned_process=$taskProcess.HasExited;whole_attempt_cap_seconds=120;whole_attempt_time_pass=($taskElapsed -lt 120)}
if($taskProcess.ExitCode -ne 0 -or $taskError -or $taskElapsed -ge 120 -or $taskPeak -gt 128MB){throw 'Fixed page attempt failed; preserve and stop'}
