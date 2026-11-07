$ErrorActionPreference = 'Stop'
$taskRoot = $PSScriptRoot
$taskOut = Join-Path $taskRoot 'run01'
if (Test-Path -LiteralPath $taskOut) { throw 'Preserve original attempt; no retry' }
$taskStart = [DateTimeOffset]::UtcNow
$taskTick = [Diagnostics.Stopwatch]::GetTimestamp()
New-Item -ItemType Directory -Path $taskOut | Out-Null
function TaskWrite($Path, $Value) {
    $taskTemp = $Path + '.tmp-' + [Guid]::NewGuid().ToString('N')
    [IO.File]::WriteAllText($taskTemp, ($Value | ConvertTo-Json -Depth 10), [Text.UTF8Encoding]::new($false))
    [IO.File]::Move($taskTemp, $Path)
}
function TaskElapsed {
    [Math]::Max(([DateTimeOffset]::UtcNow - $taskStart).TotalSeconds,
        ([Diagnostics.Stopwatch]::GetTimestamp() - $taskTick) / [Diagnostics.Stopwatch]::Frequency)
}
function TaskMemory {
    $taskQueryTick = [Diagnostics.Stopwatch]::GetTimestamp()
    $taskMemory = Get-CimInstance Win32_PerfFormattedData_PerfOS_Memory
    $taskQuerySeconds = ([Diagnostics.Stopwatch]::GetTimestamp() - $taskQueryTick) / [Diagnostics.Stopwatch]::Frequency
    $taskHeadroom = [long]$taskMemory.CommitLimit - [long]$taskMemory.CommittedBytes
    if ($taskHeadroom -lt 12GB -or $taskQuerySeconds -gt 2) { throw 'Fresh 12GiB/2s host gate failed' }
    @{headroom_bytes=$taskHeadroom; query_seconds=$taskQuerySeconds}
}
TaskWrite (Join-Path $taskOut 'ATTEMPT_ORIGIN.json') @{UTC=$taskStart.ToString('o'); ticks=$taskTick; frequency=[Diagnostics.Stopwatch]::Frequency; complete_attempt_cap_seconds=180; worker_cap_seconds=90}
$taskProcess = $null
$taskPeak = 0L
$taskForced = $false
$taskError = $null
$taskReplies = 0
$taskExit = $null
try {
    $taskAdmission = TaskMemory
    TaskWrite (Join-Path $taskOut 'PREFLIGHT.json') $taskAdmission
    $taskExe = 'C:\Users\AAA\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
    $taskProcess = Start-Process -FilePath $taskExe -ArgumentList @('-I','-B',(Join-Path $taskRoot 'fetch.py'),$taskOut) -WindowStyle Hidden -RedirectStandardOutput (Join-Path $taskOut 'stdout.log') -RedirectStandardError (Join-Path $taskOut 'stderr.log') -PassThru
    $taskWorkerTick = [Diagnostics.Stopwatch]::GetTimestamp()
    TaskWrite (Join-Path $taskOut 'OWNED_PROCESS.json') @{PID=$taskProcess.Id; start_UTC=$taskProcess.StartTime.ToUniversalTime().ToString('o'); script=(Join-Path $taskRoot 'fetch.py'); sha256=(Get-FileHash -LiteralPath (Join-Path $taskRoot 'fetch.py') -Algorithm SHA256).Hash}
    while (-not $taskProcess.HasExited) {
        $taskProcess.Refresh()
        $taskPeak = [Math]::Max($taskPeak, $taskProcess.PeakWorkingSet64)
        $taskWorkerElapsed = ([Diagnostics.Stopwatch]::GetTimestamp() - $taskWorkerTick) / [Diagnostics.Stopwatch]::Frequency
        if ((TaskElapsed) -ge 180 -or $taskWorkerElapsed -ge 90 -or $taskPeak -gt 256MB) { throw 'Transport/owned worker time or peak cap' }
        foreach ($taskRequest in Get-ChildItem -LiteralPath $taskOut -Filter 'lease-*.request.json') {
            $taskReply = $taskRequest.FullName.Replace('.request.json','.response.json')
            if (Test-Path -LiteralPath $taskReply) { continue }
            $taskReq = Get-Content -LiteralPath $taskRequest.FullName -Raw -Encoding UTF8 | ConvertFrom-Json
            $taskMem = TaskMemory
            TaskWrite $taskReply @{nonce=$taskReq.nonce;sequence=$taskReq.sequence;headroom_bytes=$taskMem.headroom_bytes;query_seconds=$taskMem.query_seconds}
            $taskReplies++
        }
        $taskBytes = (Get-ChildItem -LiteralPath $taskRoot -File -Recurse | Measure-Object Length -Sum).Sum
        if ($taskBytes -gt 16MB) { throw 'Source dossier cap' }
        Start-Sleep -Milliseconds 25
    }
} catch {
    $taskError = $_.Exception.Message
    if ($null -ne $taskProcess -and -not $taskProcess.HasExited) {
        $taskProcess.Kill()
        $taskForced = $true
    }
} finally {
    if ($null -ne $taskProcess) {
        $taskProcess.WaitForExit()
        $taskProcess.Refresh()
        $taskPeak = [Math]::Max($taskPeak, $taskProcess.PeakWorkingSet64)
        $taskExit = $taskProcess.ExitCode
    }
    $taskElapsed = TaskElapsed
    TaskWrite (Join-Path $taskOut 'HOST_EXIT.json') @{exit_code=$taskExit; forced_stop=$taskForced; error=$taskError; elapsed_seconds=$taskElapsed; observed_peak_working_set_bytes=$taskPeak; fresh_leases=$taskReplies; no_live_owned_process=($null -eq $taskProcess -or $taskProcess.HasExited); complete_attempt_cap_seconds=180}
}
if ($taskExit -ne 0 -or $taskError -or $taskElapsed -ge 180 -or $taskPeak -gt 256MB) { throw 'Fixed source attempt failed; preserve and stop' }
