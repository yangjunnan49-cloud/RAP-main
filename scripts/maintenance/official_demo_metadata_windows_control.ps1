$ErrorActionPreference='Stop'
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$base=Join-Path $root 'docs/maintenance/2026-10-15/official-demo-metadata-01'
$clock=[Diagnostics.Stopwatch]::StartNew();$utf8=[Text.UTF8Encoding]::new($false)
$tokens=$null;$parseErrors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile((Join-Path $PSScriptRoot 'native_memory_probe.ps1'),[ref]$tokens,[ref]$parseErrors)
if($parseErrors.Count){throw 'Frozen native query source parse failure'}
$add=$ast.FindAll({param($n) $n -is [Management.Automation.Language.CommandAst] -and $n.GetCommandName() -eq 'Add-Type'},$true)
if($add.Count -ne 1){throw 'Native query definition count'}
Add-Type -TypeDefinition $add[0].CommandElements[2].Value
$p=[Diagnostics.Process]::new();$psi=[Diagnostics.ProcessStartInfo]::new()
$psi.FileName=(Get-Process -Id $PID).Path;$psi.UseShellExecute=$false;$psi.CreateNoWindow=$true
foreach($a in @('-NoLogo','-NoProfile','-NonInteractive','-File',(Join-Path $PSScriptRoot 'official_demo_metadata_windows.ps1'))){$psi.ArgumentList.Add($a)}
$p.StartInfo=$psi;$started=$false;$reaped=$false;$errorText=$null;$exitCode=$null;$first=$null;$second=$null
$queries=[Collections.Generic.List[object]]::new()
try{
    if(-not $p.Start()){throw 'Windows metadata child start failed'};$started=$true;$childPid=$p.Id;$handle=$p.Handle
    while(-not $p.HasExited){
        $q=[NmqApi]::Read($handle);$queries.Add($q)
        if($q.success -and $q.peak_working_set -gt 512MB){$p.Kill();throw 'Windows child peak cap'}
        if($clock.Elapsed.TotalSeconds -gt 600){$p.Kill();throw 'Windows metadata timeout'}
        Start-Sleep -Milliseconds 100
    }
    $p.WaitForExit();$reaped=$true;$exitCode=$p.ExitCode
    $first=[NmqApi]::Read($handle);$second=[NmqApi]::Read($handle)
    if($exitCode -ne 0){throw "Windows metadata native exit $exitCode"}
    if($first.success -and $first.peak_working_set -gt 512MB){throw 'Final Windows child peak cap'}
}catch{$errorText=$_.Exception.ToString()}
finally{
    if($started -and -not $reaped){if(-not $p.HasExited){$p.Kill()};$p.WaitForExit();$exitCode=$p.ExitCode}
    $success=@($queries|Where-Object success);$gaps=@($queries|Where-Object {-not $_.success}).Count
    $maximum=if($success.Count){($success|Measure-Object peak_working_set -Maximum).Maximum}else{0}
    $known=$null -ne $first -and $null -ne $second -and $first.success -and $second.success -and $first.peak_working_set -gt 0 -and $first.peak_working_set -eq $second.peak_working_set -and $first.peak_working_set -ge $maximum -and $gaps -eq 0
    $self=[NmqApi]::Read((Get-Process -Id $PID).Handle)
    $result=@{native_exit_code=$exitCode;error=$errorText;child_pid=$childPid;Windows_seconds_to_observer_snapshot=$clock.Elapsed.TotalSeconds;
        running_queries=$queries.ToArray();final_queries=@($first,$second);running_query_gaps=$gaps;final_child_OS_peak_complete=$known;
        native_child_peak_cap_bytes=536870912;native_child_cap_pass=($known -and $first.peak_working_set -le 512MB);
        observer_to_snapshot=$self;observer_full_lifetime_peak='UNKNOWN';interval_enclosed_in_Linux_bridge=$true;old_gaps_repaired=$false}
    $bytes=$utf8.GetBytes(($result|ConvertTo-Json -Depth 20 -Compress)+"`n")
    if($bytes.Length -gt 1MB){throw 'Windows observation record cap'}
    $stream=[IO.FileStream]::new((Join-Path $base 'windows_execution.json'),[IO.FileMode]::CreateNew,[IO.FileAccess]::Write)
    try{$stream.Write($bytes)}finally{$stream.Dispose()};$p.Dispose()
}
if($errorText){exit 1}
