$ErrorActionPreference='Stop'
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$base=Join-Path $root 'docs/maintenance/2026-10-15/continuation-handoff-06'
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class H06Args {
 [DllImport("shell32.dll",SetLastError=true)] static extern IntPtr CommandLineToArgvW([MarshalAs(UnmanagedType.LPWStr)] string line,out int count);
 [DllImport("kernel32.dll")] static extern IntPtr LocalFree(IntPtr value);
 public static string[] Read(string line) {
  int n; var p=CommandLineToArgvW(line,out n); if(p==IntPtr.Zero) throw new Exception("argv parse failed");
  try {var a=new string[n];for(int i=0;i<n;i++) a[i]=Marshal.PtrToStringUni(Marshal.ReadIntPtr(p,i*IntPtr.Size));return a;}
  finally {LocalFree(p);}
 }
}
'@
$names=@('public_release_identity.py','public_release_identity_attempt02.py','demo_source_roles.py','demo_source_roles_attempt02.py',
 'release_backend_attribution.py','official_demo_metadata.py','official_demo_metadata_windows_bridge.py',
 'official_demo_metadata_windows_entry02.py','official_demo_metadata_windows.ps1','official_demo_metadata_windows_control.ps1')
$processes=@(Get-CimInstance Win32_Process);$readable=0;$argv=0;$matches=@();$nulls=0;$unknown=@()
foreach($p in $processes){
 if(-not $p.CommandLine){$nulls++;if($p.Name -match '^(python([0-9.]*)?|pwsh|powershell|wsl)\.exe$'){$unknown+=@{pid=$p.ProcessId;name=$p.Name}};continue}
 $readable++;$args=[H06Args]::Read($p.CommandLine);$argv+=$args.Count
 foreach($a in $args){if(($a -replace '\\','/').Split('/')[-1] -in $names){$matches+=@{pid=$p.ProcessId;name=$p.Name;matched_argument=$a};break}}
}
$value=@{processes=$processes.Count;readable_command_lines=$readable;argv=$argv;null_command_lines=$nulls;
 unreadable_relevant_interpreters=$unknown;scoped_payload_matches=$matches;scoped_identifiers=$names;
 unrelated_tasks_absence_claim=$false;ordinary_preparation_RSS='UNKNOWN';utc=[DateTime]::UtcNow.ToString('o')}
$bytes=[Text.UTF8Encoding]::new($false).GetBytes(($value|ConvertTo-Json -Depth 10)+"`n")
$stream=[IO.FileStream]::new((Join-Path $base 'WINDOWS_PROCESS_CENSUS.json'),[IO.FileMode]::CreateNew,[IO.FileAccess]::Write)
try{$stream.Write($bytes)}finally{$stream.Dispose()}
Write-Output ($value|Select-Object processes,readable_command_lines,argv,null_command_lines,@{N='scoped_matches';E={$_.scoped_payload_matches.Count}},@{N='unreadable_interpreters';E={$_.unreadable_relevant_interpreters.Count}}|ConvertTo-Json -Compress)
