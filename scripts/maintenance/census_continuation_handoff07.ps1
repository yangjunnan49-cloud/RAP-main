$ErrorActionPreference='Stop'
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$base=Join-Path $root 'docs/maintenance/2026-10-15/continuation-handoff-07'
$names=@('original_archive_metadata.ps1','original_archive_inventory.ps1','original_archive_inventory_attempt02.ps1',
 'validate_original_archive_inventory.py','validate_original_archive_inventory_attempt02.py','demo_reference_documents.ps1',
 'demo_reference_documents_attempt02.ps1','validate_demo_reference_documents.py','validate_demo_reference_documents_attempt02.py',
 'validate_demo_reference_driver.py','author_demo_clarification.ps1')
$rows=@(Get-CimInstance Win32_Process);$readable=0;$nulls=0;$relevantUnknown=@();$matches=@()
foreach($r in $rows){
 if(-not $r.CommandLine){$nulls++;if($r.Name -match '^(python|python3|pwsh|powershell|wsl)(\.exe)?$'){$relevantUnknown+=@{pid=$r.ProcessId;name=$r.Name}};continue}
 $readable++
 if($r.ProcessId -eq $PID){continue}
 foreach($name in $names){if($r.CommandLine.Contains($name)){$matches+=@{pid=$r.ProcessId;name=$r.Name;identifier=$name;command_line=$r.CommandLine};break}}
}
$result=@{processes=$rows.Count;readable_command_lines=$readable;null_command_lines=$nulls;relevant_unreadable=$relevantUnknown;scoped_matches=$matches;
 identifiers=$names;unrelated_process_absence_claim=$false;scope_only=$true;ordinary_setup_RSS='UNKNOWN';UTC=[DateTime]::UtcNow.ToString('o')}
$path=Join-Path $base 'WINDOWS_PROCESS_CENSUS.json';if(Test-Path -LiteralPath $path){throw 'Existing census preserved'}
[IO.File]::WriteAllText($path,($result|ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))
Write-Output (@{processes=$rows.Count;scoped_matches=$matches.Count;relevant_unreadable=$relevantUnknown.Count}|ConvertTo-Json)
