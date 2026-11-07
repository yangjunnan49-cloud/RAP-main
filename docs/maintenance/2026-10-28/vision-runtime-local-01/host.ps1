$ErrorActionPreference='Stop'
$taskRoot=$PSScriptRoot
if(Test-Path -LiteralPath (Join-Path $taskRoot 'LOCAL_WHEEL_RESULT.json')){throw 'No retry: download receipt already exists'}
$plan=Get-Content -LiteralPath (Join-Path $taskRoot 'REQUEST_PLAN.json') -Raw | ConvertFrom-Json
$exe=$plan.python
function RunStage($name,$arguments,$seconds){
    $timer=[Diagnostics.Stopwatch]::StartNew();$query=[Diagnostics.Stopwatch]::StartNew();$m=Get-CimInstance Win32_PerfFormattedData_PerfOS_Memory;$query.Stop();$headroom=[long]$m.CommitLimit-[long]$m.CommittedBytes
    if($headroom -lt 12GB -or $query.Elapsed.TotalSeconds -gt 2){throw 'Fresh resource gate'}
    $p=Start-Process -FilePath $exe -ArgumentList $arguments -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $taskRoot ($name+'.stdout.log')) -RedirectStandardError (Join-Path $taskRoot ($name+'.stderr.log'))
    $peak=0L;$forced=$false;$errorText=$null
    try{while(-not $p.HasExited){$p.Refresh();$peak=[Math]::Max($peak,$p.PeakWorkingSet64);if($timer.Elapsed.TotalSeconds -ge $seconds -or $peak -gt 1GB){throw 'Stage wall/RSS limit'};Start-Sleep -Milliseconds 25}}
    catch{$errorText=$_.Exception.Message;if(-not $p.HasExited){$p.Kill();$forced=$true}}
    $p.WaitForExit();$p.Refresh();$peak=[Math]::Max($peak,$p.PeakWorkingSet64)
    @{exit_code=$p.ExitCode;elapsed_seconds=$timer.Elapsed.TotalSeconds;peak_bytes=$peak;error=$errorText;forced_stop=$forced;no_live_owned_process=$p.HasExited;headroom_bytes=$headroom;query_seconds=$query.Elapsed.TotalSeconds} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskRoot ($name+'.HOST_EXIT.json')) -Encoding UTF8
    if($p.ExitCode -ne 0 -or $errorText){throw ('Stage failed: '+$name)}
    $size=(Get-ChildItem -LiteralPath $taskRoot -Recurse -File | Measure-Object Length -Sum).Sum;if($size -gt 1GB){throw 'Dossier cap'}
}
RunStage 'validate' @('-I','-B',(Join-Path $taskRoot 'prepare_local.py')) 60
$wheel=Join-Path $taskRoot $plan.filename
if((Get-FileHash -LiteralPath $wheel -Algorithm SHA256).Hash.ToLowerInvariant() -ne $plan.sha256){throw 'Wheel hash before install'}
if(Test-Path -LiteralPath $plan.target){throw 'Preserve any existing target'}
$tmp=Join-Path $taskRoot 'tmp';New-Item -ItemType Directory -Path $tmp | Out-Null
$oldTemp=$env:TEMP;$oldTmp=$env:TMP
try{$env:TEMP=$tmp;$env:TMP=$tmp;RunStage 'install' @('-I','-B','-m','pip','--isolated','--disable-pip-version-check','--no-cache-dir','install','--no-index','--no-deps','--no-compile','--target',$plan.target,$wheel) 180}
finally{$env:TEMP=$oldTemp;$env:TMP=$oldTmp}
RunStage 'probe' @('-I','-B',(Join-Path $taskRoot 'probe.py')) 60
