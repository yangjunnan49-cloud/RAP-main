$ErrorActionPreference='Stop'
$root=[System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$output=Join-Path $root 'docs/maintenance/2026-10-14/continuation-handoff-05/PROCESS_CENSUS_WINDOWS.json'
if(Test-Path -LiteralPath $output){throw 'Existing process evidence preserved'}
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class Handoff05Argv {
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
$names=@('poss_outcome_provenance.py','validate_poss_outcome_provenance.py','poss_outcome_layout02.py',
    'close_poss_outcome_provenance.py','frame_time_identifiability.py','validate_frame_time_identifiability.py',
    'close_frame_time_identifiability.py','bounded_evidence_journal.py','evidence_journal_control.py',
    'validate_evidence_journal.py','close_evidence_journal.py','bounded_pipe_capture.py','pipe_capture_fixture.py',
    'pipe_capture_control.py','validate_pipe_capture.py','close_pipe_capture.py','windows_pipe_fixture.ps1',
    'windows_pipe_capture_control.ps1','windows_pipe_control.py','validate_windows_pipe.py','audit_windows_pipe_stop.py',
    'native_memory_fixture.ps1','native_memory_probe.ps1','native_memory_control.py','validate_native_memory.py',
    'native_memory_validation02.py','close_native_memory_query.py')
$matches=[System.Collections.Generic.List[object]]::new()
$unavailable=[System.Collections.Generic.List[object]]::new()
$processes=Get-CimInstance Win32_Process
$readable=0;$arguments=0;$nullLines=0
foreach($process in $processes){
    if([string]::IsNullOrWhiteSpace($process.CommandLine)){
        $nullLines++
        if($process.Name -match '^(python.*|wsl|pwsh|powershell)\.exe$'){$unavailable.Add(@{pid=$process.ProcessId;name=$process.Name})}
        continue
    }
    $argv=[Handoff05Argv]::Parse($process.CommandLine);$readable++;$arguments+=$argv.Count
    foreach($arg in $argv){
        $leaf=[System.IO.Path]::GetFileName($arg.Replace('/','\'))
        if($names -contains $leaf){$matches.Add(@{pid=$process.ProcessId;name=$process.Name;matched_argument=$arg})}
    }
}
$result=[ordered]@{utc=[DateTime]::UtcNow.ToString('o');processes_seen=$processes.Count;
    readable_command_lines=$readable;arguments_checked=$arguments;null_command_lines=$nullLines;
    all_available_arguments_checked=$true;unreadable_relevant_interpreters=$unavailable.ToArray();
    owned_payload_matches=$matches.ToArray();scope='27 current resumed-scope driver/helper/closure/fixture basenames; no unrelated command lines retained'}
$body=[System.Text.UTF8Encoding]::new($false).GetBytes(($result|ConvertTo-Json -Depth 8))
$stream=[System.IO.FileStream]::new($output,[System.IO.FileMode]::CreateNew,[System.IO.FileAccess]::Write)
try{$stream.Write($body)}finally{$stream.Dispose()}
Write-Output ($result|ConvertTo-Json -Depth 8 -Compress)
if($matches.Count -or $unavailable.Count){exit 1}
