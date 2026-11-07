$ErrorActionPreference='Stop'
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$base=Join-Path $root 'docs/maintenance/2026-10-16/regx-reference-package-01'
$clock=[Diagnostics.Stopwatch]::StartNew();$tokens=$null;$parseErrors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile((Join-Path $PSScriptRoot 'native_memory_probe.ps1'),[ref]$tokens,[ref]$parseErrors)
if($parseErrors.Count){throw 'Native definition parse failed'}
$add=$ast.FindAll({param($n) $n -is [Management.Automation.Language.CommandAst] -and $n.GetCommandName() -eq 'Add-Type'},$true)
if($add.Count -ne 1){throw 'Native definition count'}
Add-Type -TypeDefinition $add[0].CommandElements[2].Value
$p=[Diagnostics.Process]::new();$psi=[Diagnostics.ProcessStartInfo]::new()
$psi.FileName=(Get-Process -Id $PID).Path;$psi.UseShellExecute=$false;$psi.CreateNoWindow=$true
foreach($a in @('-NoLogo','-NoProfile','-NonInteractive','-File',(Join-Path $PSScriptRoot 'acquire_regx_reference_package.ps1'))){$psi.ArgumentList.Add($a)}
$p.StartInfo=$psi;$started=$false;$reaped=$false;$errorText=$null;$exitCode=$null;$first=$null;$second=$null;$childPid=$null
$queries=[Collections.Generic.List[object]]::new()
try{
 if(-not $p.Start()){throw 'Child start failed'};$started=$true;$childPid=$p.Id;$handle=$p.Handle
 while(-not $p.HasExited){
  $q=[NmqApi]::Read($handle);$queries.Add($q)
  if($q.success -and $q.peak_working_set -gt 512MB){$p.Kill();throw 'Owned child peak cap'}
  if($clock.Elapsed.TotalSeconds -gt 900){$p.Kill();throw 'Owned child timeout'}
  Start-Sleep -Milliseconds 100
 }
 $p.WaitForExit();$reaped=$true;$exitCode=$p.ExitCode
 $first=[NmqApi]::Read($handle);$second=[NmqApi]::Read($handle)
 if($exitCode -ne 0){throw "Native child exit $exitCode"}
 if($first.success -and $first.peak_working_set -gt 512MB){throw 'Final peak cap'}
}catch{$errorText=$_.Exception.ToString()}
finally{
 if($started -and -not $reaped){if(-not $p.HasExited){$p.Kill()};$p.WaitForExit();$exitCode=$p.ExitCode}
 $good=@($queries|Where-Object success);$gaps=@($queries|Where-Object {-not $_.success}).Count
 $maximum=if($good.Count){($good|Measure-Object peak_working_set -Maximum).Maximum}else{0}
 $known=$null -ne $first -and $null -ne $second -and $first.success -and $second.success -and $first.peak_working_set -gt 0 -and $first.peak_working_set -eq $second.peak_working_set -and $first.peak_working_set -ge $maximum -and $gaps -eq 0
 $r=@{native_exit_code=$exitCode;error=$errorText;child_pid=$childPid;Windows_seconds_to_observer_snapshot=$clock.Elapsed.TotalSeconds;running_queries=$queries.ToArray();final_queries=@($first,$second);running_query_gaps=$gaps;final_child_OS_peak_complete=$known;native_child_peak_cap_bytes=536870912;native_child_cap_pass=($known -and $first.peak_working_set -le 512MB);observer_to_snapshot=[NmqApi]::Read((Get-Process -Id $PID).Handle);observer_full_lifetime_peak='UNKNOWN';all_native_process_tree_cap_claim=$false}
 $b=[Text.UTF8Encoding]::new($false).GetBytes(($r|ConvertTo-Json -Depth 20 -Compress)+"`n");if($b.Length -gt 1MB){throw 'Observation record cap'}
 $s=[IO.FileStream]::new((Join-Path $base 'acquisition_execution.json'),[IO.FileMode]::CreateNew,[IO.FileAccess]::Write);try{$s.Write($b)}finally{$s.Dispose();$p.Dispose()}
}
if($errorText){Write-Error $errorText;exit 1}
