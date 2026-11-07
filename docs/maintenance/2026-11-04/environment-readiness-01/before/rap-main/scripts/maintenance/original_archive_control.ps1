param([Parameter(Mandatory=$true)][ValidateSet('freeze','network')][string]$Stage)
$ErrorActionPreference='Stop'
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$base=Join-Path $root 'docs/maintenance/2026-10-15/original-demo-archive-metadata-01'
$out=Join-Path $base ('supervision-'+$Stage)
if(Test-Path -LiteralPath $out){throw 'Existing stage preserved'}
New-Item -ItemType Directory -Path $out|Out-Null
$utf8=[Text.UTF8Encoding]::new($false);$clock=[Diagnostics.Stopwatch]::StartNew()
$tokens=$null;$errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile((Join-Path $PSScriptRoot 'native_memory_probe.ps1'),[ref]$tokens,[ref]$errors)
if($errors.Count){throw 'Native query source parse failure'}
$add=$ast.FindAll({param($n)$n -is [Management.Automation.Language.CommandAst] -and $n.GetCommandName() -eq 'Add-Type'},$true)
if($add.Count -ne 1){throw 'Native query definition count'}
Add-Type -TypeDefinition $add[0].CommandElements[2].Value
$p=[Diagnostics.Process]::new();$psi=[Diagnostics.ProcessStartInfo]::new()
$psi.FileName=(Get-Process -Id $PID).Path;$psi.UseShellExecute=$false;$psi.CreateNoWindow=$true
$psi.RedirectStandardOutput=$true;$psi.RedirectStandardError=$true
foreach($a in @('-NoLogo','-NoProfile','-NonInteractive','-File',(Join-Path $PSScriptRoot 'original_archive_metadata.ps1'),'-Stage',$Stage)){$psi.ArgumentList.Add($a)}
$p.StartInfo=$psi;$rows=[Collections.Generic.List[object]]::new();$started=$false;$done=$false;$errorText=$null;$exitCode=$null;$final=@()
try{
    if(-not $p.Start()){throw 'Owned metadata child start failed'};$started=$true;$childPid=$p.Id;$handle=$p.Handle
    $stdout=$p.StandardOutput.ReadToEndAsync();$stderr=$p.StandardError.ReadToEndAsync()
    while(-not $p.HasExited){
        $q=[NmqApi]::Read($handle);$rows.Add($q)
        if(-not $q.success){throw 'Native query failure recorded'}
        if($q.peak_working_set -gt 512MB -or $clock.Elapsed.TotalSeconds -gt 240){$p.Kill();throw 'Prospective child resource stop'}
        Start-Sleep -Milliseconds 100
    }
    $p.WaitForExit();$done=$true;$exitCode=$p.ExitCode
    $final=@([NmqApi]::Read($handle),[NmqApi]::Read($handle))
    $outText=$stdout.GetAwaiter().GetResult();$errText=$stderr.GetAwaiter().GetResult()
    if($utf8.GetByteCount($outText)+$utf8.GetByteCount($errText) -gt 64KB){throw 'Controlled transcript reserve exceeded'}
    [IO.File]::WriteAllText((Join-Path $out 'stdout.log'),$outText,$utf8)
    [IO.File]::WriteAllText((Join-Path $out 'stderr.log'),$errText,$utf8)
}catch{$errorText=$_.Exception.ToString()}
finally{
    if($started -and -not $done){if(-not $p.HasExited){$p.Kill()};$p.WaitForExit();$exitCode=$p.ExitCode}
    $self=[NmqApi]::Read((Get-Process -Id $PID).Handle)
    $known=$final.Count -eq 2 -and $final[0].success -and $final[1].success -and $final[0].peak_working_set -eq $final[1].peak_working_set -and $final[0].peak_working_set -gt 0
    $result=@{stage=$Stage;pid=$childPid;native_exit_code=$exitCode;error=$errorText;enclosing_seconds=$clock.Elapsed.TotalSeconds;running_queries=$rows.ToArray();final_queries=$final;final_child_peak_known=$known;child_cap_bytes=536870912;observer_to_snapshot=$self;observer_full_lifetime_peak='UNKNOWN';ordinary_preparation_RSS='UNKNOWN';utc=[DateTime]::UtcNow.ToString('o')}
    [IO.File]::WriteAllText((Join-Path $out 'execution.json'),($result|ConvertTo-Json -Depth 12),$utf8);$p.Dispose()
}
if($errorText){throw $errorText}
Write-Output ($result|Select-Object stage,native_exit_code,enclosing_seconds,final_child_peak_known|ConvertTo-Json -Compress)
exit $exitCode
