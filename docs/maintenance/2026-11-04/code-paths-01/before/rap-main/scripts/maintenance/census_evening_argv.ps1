$ErrorActionPreference='Stop'
$taskRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$taskBase=Join-Path $taskRoot 'docs/maintenance/2026-10-15/continuation-handoff-08'
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class H08Args {
 [DllImport("shell32.dll",SetLastError=true)] static extern IntPtr CommandLineToArgvW([MarshalAs(UnmanagedType.LPWStr)] string line,out int count);
 [DllImport("kernel32.dll")] static extern IntPtr LocalFree(IntPtr value);
 public static string[] Read(string line) {
  int n; var p=CommandLineToArgvW(line,out n); if(p==IntPtr.Zero) throw new Exception("argv parse failed");
  try {var a=new string[n];for(int i=0;i<n;i++) a[i]=Marshal.PtrToStringUni(Marshal.ReadIntPtr(p,i*IntPtr.Size));return a;}
  finally {LocalFree(p);}
 }
}
'@
$taskNames=@('nonlocal_joint_connectivity.py','run_nonlocal_joint_connectivity.py','validate_nonlocal_joint_connectivity.py',
 'nonlocal_joint_comparison.py','nonlocal_joint_comparison_cpu02.py','run_nonlocal_joint_comparison.py','run_nonlocal_joint_comparison_cpu02.py',
 'validate_nonlocal_joint_comparison.py','independent_nonlocal_joint.py','run_independent_nonlocal_joint.py')
$taskProcesses=@(Get-CimInstance Win32_Process);$taskReadable=0;$taskArgvCount=0;$taskMatches=@();$taskNulls=0;$taskUnknown=@()
foreach($taskProcess in $taskProcesses){
 if(-not $taskProcess.CommandLine){
  $taskNulls++
  if($taskProcess.Name -match '^(python([0-9.]*)?|pwsh|powershell|wsl)\.exe$'){$taskUnknown+=@{pid=$taskProcess.ProcessId;name=$taskProcess.Name}}
  continue
 }
 $taskReadable++;$taskArguments=[H08Args]::Read($taskProcess.CommandLine);$taskArgvCount+=$taskArguments.Count
 foreach($taskArgument in $taskArguments){
  if(($taskArgument -replace '\\','/').Split('/')[-1] -in $taskNames){$taskMatches+=@{pid=$taskProcess.ProcessId;name=$taskProcess.Name;matched_argument=$taskArgument};break}
 }
}
$taskValue=@{processes=$taskProcesses.Count;readable_command_lines=$taskReadable;argv=$taskArgvCount;null_command_lines=$taskNulls;
 unreadable_relevant_interpreters=$taskUnknown;scoped_payload_matches=$taskMatches;scoped_identifiers=$taskNames;
 unrelated_tasks_absence_claim=$false;ordinary_preparation_RSS='UNKNOWN';utc=[DateTime]::UtcNow.ToString('o')}
$taskBytes=[Text.UTF8Encoding]::new($false).GetBytes(($taskValue|ConvertTo-Json -Depth 10)+"`n")
$taskStream=[IO.FileStream]::new((Join-Path $taskBase 'PROCESS_CENSUS_WINDOWS_ARGV.json'),[IO.FileMode]::CreateNew,[IO.FileAccess]::Write)
try{$taskStream.Write($taskBytes)}finally{$taskStream.Dispose()}
if($taskMatches.Count){throw 'Scoped payload remains'}
[ordered]@{processes=$taskProcesses.Count;readable_command_lines=$taskReadable;argv=$taskArgvCount;nulls=$taskNulls;matches=$taskMatches.Count;unreadable_relevant=$taskUnknown.Count}|ConvertTo-Json
