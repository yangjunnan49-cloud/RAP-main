param([Parameter(Mandatory=$true)][ValidateSet('freeze','fetch','validate')][string]$Stage)
$ErrorActionPreference='Stop'
$taskClock=[Diagnostics.Stopwatch]::StartNew()
$taskRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$taskBase=Join-Path $taskRoot 'docs/maintenance/2026-10-17/regx-canonical-source-01'
$taskOut=Join-Path $taskBase ('supervision-'+$Stage)
if(Test-Path -LiteralPath $taskOut){throw 'Existing attempt must be retained; no automatic retry'}
$taskPrevious=0.0
foreach($r in Get-ChildItem -LiteralPath $taskBase -Directory -Filter 'supervision-*'){
 $receipt=Join-Path $r.FullName 'execution.json'
 if(-not(Test-Path -LiteralPath $receipt)){throw 'Existing incomplete enclosing attempt'}
 $taskPrevious+=(Get-Content -LiteralPath $receipt -Raw|ConvertFrom-Json).enclosing_seconds
}
if($taskPrevious -ge 300){throw 'Combined enclosing deadline already used'}
New-Item -ItemType Directory -Path $taskOut|Out-Null
$taskUtf8=[Text.UTF8Encoding]::new($false)
$tokens=$null;$parseErrors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile((Join-Path $PSScriptRoot 'native_memory_probe.ps1'),[ref]$tokens,[ref]$parseErrors)
if($parseErrors.Count){throw 'Native query definition parse failure'}
$definitions=$ast.FindAll({param($n)$n -is [Management.Automation.Language.CommandAst] -and $n.GetCommandName() -eq 'Add-Type'},$true)
if($definitions.Count -ne 1){throw 'Native query definition count'}
Add-Type -TypeDefinition $definitions[0].CommandElements[2].Value
$process=[Diagnostics.Process]::new();$start=[Diagnostics.ProcessStartInfo]::new()
$start.FileName=(Get-Process -Id $PID).Path;$start.UseShellExecute=$false;$start.CreateNoWindow=$true
$start.RedirectStandardOutput=$true;$start.RedirectStandardError=$true
foreach($a in @('-NoLogo','-NoProfile','-NonInteractive','-File',(Join-Path $PSScriptRoot 'regx_batch_source_query.ps1'),'-Stage',$Stage)){$start.ArgumentList.Add($a)}
$process.StartInfo=$start;$queries=[Collections.Generic.List[object]]::new()
$started=$false;$reaped=$false;$errorText=$null;$nativeExit=$null;$childPid=$null;$final=@();$stdout=$null;$stderr=$null
try{
 if(-not $process.Start()){throw 'Scoped child did not start'}
 $started=$true;$childPid=$process.Id;$handle=$process.Handle
 $stdout=$process.StandardOutput.ReadToEndAsync();$stderr=$process.StandardError.ReadToEndAsync()
 while(-not $process.HasExited){
  $q=[NmqApi]::Read($handle);$queries.Add($q)
  if(-not $q.success){throw 'OS query failure, retained in execution receipt'}
  if($q.peak_working_set -gt 512MB){throw 'Scoped native child peak stop'}
  if($taskPrevious+$taskClock.Elapsed.TotalSeconds -gt 300){throw 'Combined enclosing time stop'}
  Start-Sleep -Milliseconds 100
 }
 $process.WaitForExit();$reaped=$true;$nativeExit=$process.ExitCode
 $final=@([NmqApi]::Read($handle),[NmqApi]::Read($handle))
 if($nativeExit -ne 0){throw "Scoped child exit $nativeExit"}
 if(@($final|Where-Object {-not $_.success -or $_.peak_working_set -gt 512MB}).Count){throw 'Final OS peak not admitted'}
}catch{$errorText=$_.Exception.ToString()}
finally{
 if($started -and -not $reaped){if(-not $process.HasExited){$process.Kill()};$process.WaitForExit();$nativeExit=$process.ExitCode;$final=@([NmqApi]::Read($handle),[NmqApi]::Read($handle))}
 $textOut=if($stdout){$stdout.GetAwaiter().GetResult()}else{''};$textErr=if($stderr){$stderr.GetAwaiter().GetResult()}else{''}
 if($taskUtf8.GetByteCount($textOut)+$taskUtf8.GetByteCount($textErr) -gt 256KB){$errorText='Controlled transcript reserve exceeded';$textOut=$textOut.Substring(0,[Math]::Min($textOut.Length,65536));$textErr=$textErr.Substring(0,[Math]::Min($textErr.Length,65536))}
 [IO.File]::WriteAllText((Join-Path $taskOut 'stdout.log'),$textOut,$taskUtf8)
 [IO.File]::WriteAllText((Join-Path $taskOut 'stderr.log'),$textErr,$taskUtf8)
 $gaps=@($queries|Where-Object {-not $_.success}).Count
 $maximum=if($queries.Count){($queries|Measure-Object peak_working_set -Maximum).Maximum}else{0}
 $known=$final.Count -eq 2 -and $final[0].success -and $final[1].success -and $final[0].peak_working_set -gt 0 -and $final[0].peak_working_set -eq $final[1].peak_working_set -and $final[0].peak_working_set -ge $maximum -and $gaps -eq 0
 $receipt=[ordered]@{stage=$Stage;utc=[DateTime]::UtcNow.ToString('o');native_exit_code=$nativeExit;child_pid=$childPid;error=$errorText;enclosing_seconds=$taskClock.Elapsed.TotalSeconds;previous_enclosing_seconds=$taskPrevious;running_queries=$queries.ToArray();final_queries=$final;running_query_gaps=$gaps;final_child_OS_peak_known=$known;child_peak_cap_bytes=536870912;observer_to_snapshot=[NmqApi]::Read((Get-Process -Id $PID).Handle);observer_full_lifetime_peak='UNKNOWN';ordinary_preparation_RSS='UNKNOWN';all_native_process_tree_claim=$false}
 [IO.File]::WriteAllText((Join-Path $taskOut 'execution.json'),($receipt|ConvertTo-Json -Depth 14),$taskUtf8)
 $process.Dispose()
}
if($errorText){throw $errorText}
if($taskPrevious+$taskClock.Elapsed.TotalSeconds -gt 300 -or -not $known){throw 'Final admission fails; preserve attempt'}
Write-Output ([pscustomobject]$receipt|Select-Object stage,native_exit_code,enclosing_seconds,final_child_OS_peak_known|ConvertTo-Json -Compress)
