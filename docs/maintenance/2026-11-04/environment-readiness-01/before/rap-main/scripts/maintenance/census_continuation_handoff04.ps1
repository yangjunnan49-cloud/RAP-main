param()
$ErrorActionPreference='Stop'
$taskRoot=[System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$taskOutput=Join-Path $taskRoot 'docs\maintenance\2026-10-14\continuation-handoff-04\PROCESS_CENSUS_WINDOWS.json'
if(Test-Path -LiteralPath $taskOutput){throw 'Existing census must be preserved'}
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class Handoff04Argv {
    [DllImport("shell32.dll", SetLastError=true)]
    private static extern IntPtr CommandLineToArgvW([MarshalAs(UnmanagedType.LPWStr)] string cmd, out int argc);
    [DllImport("kernel32.dll")] private static extern IntPtr LocalFree(IntPtr value);
    public static string[] Parse(string cmd) {
        int count; IntPtr ptr=CommandLineToArgvW(cmd,out count);
        if(ptr==IntPtr.Zero) throw new System.ComponentModel.Win32Exception();
        try {
            string[] args=new string[count];
            for(int i=0;i<count;i++) args[i]=Marshal.PtrToStringUni(Marshal.ReadIntPtr(ptr,i*IntPtr.Size));
            return args;
        } finally { LocalFree(ptr); }
    }
}
'@
$taskNames=@('physical_source_role_feasibility.py','physical_comparison_contract.py',
    'physical_comparison_layout02.py','bounded_native_residual_feasibility.py',
    'poss_exposure_lineage.py','close_physical_source_roles.py',
    'close_physical_comparison_contract.py','close_bounded_native_residual.py',
    'close_poss_exposure_lineage.py')
$taskMatches=[System.Collections.Generic.List[object]]::new()
$taskUnavailable=[System.Collections.Generic.List[object]]::new()
$taskProcesses=Get-CimInstance Win32_Process
$taskReadable=0;$taskArguments=0;$taskNull=0
foreach($taskProcess in $taskProcesses){
    if([string]::IsNullOrWhiteSpace($taskProcess.CommandLine)){
        $taskNull++
        if($taskProcess.Name -match '^(python.*|wsl|pwsh|powershell)\.exe$'){
            $taskUnavailable.Add([ordered]@{pid=$taskProcess.ProcessId;name=$taskProcess.Name})
        }
        continue
    }
    $taskArgv=[Handoff04Argv]::Parse($taskProcess.CommandLine)
    $taskReadable++;$taskArguments+=$taskArgv.Count
    foreach($taskArg in $taskArgv){
        $taskLeaf=[System.IO.Path]::GetFileName($taskArg.Replace('/','\'))
        if($taskNames -contains $taskLeaf){
            $taskMatches.Add([ordered]@{pid=$taskProcess.ProcessId;name=$taskProcess.Name;matched_argument=$taskArg})
        }
    }
}
$taskResult=[ordered]@{utc=[DateTime]::UtcNow.ToString('o');processes_seen=$taskProcesses.Count;
    readable_command_lines=$taskReadable;arguments_checked=$taskArguments;null_command_lines=$taskNull;
    all_available_arguments_checked=$true;unreadable_relevant_interpreters=@($taskUnavailable);
    owned_payload_matches=@($taskMatches);scope='Nine current-continuation driver/closure filenames; no unrelated command lines retained'}
$taskBody=$taskResult|ConvertTo-Json -Depth 8
$taskStream=[System.IO.File]::Open($taskOutput,[System.IO.FileMode]::CreateNew)
try{$taskBytes=[System.Text.UTF8Encoding]::new($false).GetBytes($taskBody);$taskStream.Write($taskBytes,0,$taskBytes.Length)}finally{$taskStream.Dispose()}
Write-Output ($taskResult|ConvertTo-Json -Depth 8 -Compress)
if($taskMatches.Count -ne 0 -or $taskUnavailable.Count -ne 0){exit 1}
