$ErrorActionPreference='Stop'
$root=[System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$base=Join-Path $root 'docs/maintenance/2026-10-14/native-memory-query-01'
$utf8=[System.Text.UTF8Encoding]::new($false)
$timer=[System.Diagnostics.Stopwatch]::StartNew()
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
[StructLayout(LayoutKind.Sequential)]
public struct NmqCounters {
    public uint cb, PageFaultCount;
    public UIntPtr PeakWorkingSetSize, WorkingSetSize;
    public UIntPtr QuotaPeakPagedPoolUsage, QuotaPagedPoolUsage;
    public UIntPtr QuotaPeakNonPagedPoolUsage, QuotaNonPagedPoolUsage;
    public UIntPtr PagefileUsage, PeakPagefileUsage;
}
public class NmqResult {
    public bool success;
    public int error;
    public bool error_relevant;
    public uint structure_bytes;
    public ulong peak_working_set, working_set, peak_commit;
}
public static class NmqApi {
    [DllImport("psapi.dll", SetLastError=true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool GetProcessMemoryInfo(IntPtr process, ref NmqCounters counters, uint size);
    public static NmqResult Read(IntPtr handle) {
        var c=new NmqCounters(); c.cb=(uint)Marshal.SizeOf<NmqCounters>();
        Marshal.SetLastPInvokeError(0);
        bool ok=GetProcessMemoryInfo(handle,ref c,c.cb);
        int error=Marshal.GetLastWin32Error();
        return new NmqResult {success=ok,error=error,error_relevant=!ok,
            structure_bytes=c.cb,peak_working_set=c.PeakWorkingSetSize.ToUInt64(),
            working_set=c.WorkingSetSize.ToUInt64(),peak_commit=c.PeakPagefileUsage.ToUInt64()};
    }
}
'@

function Run-Probe([string]$Mode){
    $process=[System.Diagnostics.Process]::new()
    $psi=[System.Diagnostics.ProcessStartInfo]::new()
    $psi.FileName=(Get-Process -Id $PID).Path;$psi.UseShellExecute=$false;$psi.CreateNoWindow=$true
    foreach($arg in @('-NoLogo','-NoProfile','-NonInteractive','-File',(Join-Path $PSScriptRoot 'native_memory_fixture.ps1'),'-Mode',$Mode)){$psi.ArgumentList.Add($arg)}
    $process.StartInfo=$psi;$started=$false;$reaped=$false
    $clock=[System.Diagnostics.Stopwatch]::StartNew()
    $queries=[System.Collections.Generic.List[object]]::new()
    try{
        if(-not $process.Start()){throw 'Start failed'}
        $started=$true;$childPid=$process.Id;$handle=$process.Handle
        while(-not $process.HasExited){
            $queries.Add([NmqApi]::Read($handle))
            if($clock.Elapsed.TotalSeconds -gt 10){$process.Kill();throw 'Owned child timeout'}
            Start-Sleep -Milliseconds 5
        }
        $process.WaitForExit();$reaped=$true
        $first=[NmqApi]::Read($handle)
        $process.Refresh()
        try{$dotnet=@{success=$true;peak_working_set=$process.PeakWorkingSet64;error=$null}}
        catch{$dotnet=@{success=$false;peak_working_set=$null;error=$_.Exception.Message}}
        $second=[NmqApi]::Read($handle)
        $successful=@($queries|Where-Object success)
        $maximum=if($successful.Count){($successful|Measure-Object peak_working_set -Maximum).Maximum}else{0}
        $available=$first.success -and $second.success -and $first.peak_working_set -gt 0 -and $first.peak_working_set -eq $second.peak_working_set -and $first.peak_working_set -ge $maximum
        if($process.ExitCode -ne 0){throw 'Unexpected native child exit'}
        if($available -and $first.peak_working_set -gt 256MB){throw 'Final native child cap'}
        return [ordered]@{mode=$Mode;pid=$childPid;native_exit_code=$process.ExitCode;
            wall_seconds=$clock.Elapsed.TotalSeconds;handle_retained_through_final_queries=$true;
            running_queries=$queries.ToArray();post_exit_queries=@($first,$second);refreshed_dotnet=$dotnet;
            running_query_count=$queries.Count;running_query_failures=@($queries|Where-Object {-not $_.success}).Count;
            final_OS_peak_available=$available;final_native_cap_proven=$available;
            final_native_cap_exceedance_proven=$false}
    }finally{
        if($started -and -not $reaped){if(-not $process.HasExited){$process.Kill()};$process.WaitForExit()}
        $process.Dispose()
    }
}

$rows=@();$ok=$false;$errorText=$null
try{
    $baseline=Run-Probe 'baseline';$rows+=$baseline
    if($baseline.final_OS_peak_available){$rows+=Run-Probe 'early_burst';$rows+=Run-Probe 'late_burst'}
    $ok=$true
}catch{$errorText=$_.Exception.ToString();Write-Error $errorText -ErrorAction Continue}
finally{
    $self=Get-Process -Id $PID
    $selfObservation=[NmqApi]::Read($self.Handle)
    $result=[ordered]@{observation_execution_complete=$ok;error=$errorText;observer_pid=$PID;
        observer_wall_seconds=$timer.Elapsed.TotalSeconds;observer_to_snapshot=$selfObservation;
        observer_full_lifetime_peak_known=$false;pointer_bytes=[IntPtr]::Size;
        native_children=$rows.Count;cases=$rows;old_WPC0_resource_gap_repaired=$false}
    $body=$utf8.GetBytes(($result|ConvertTo-Json -Depth 20 -Compress)+"`n")
    if($body.Length -gt 512KB){throw 'Observation metadata cap'}
    $stream=[System.IO.FileStream]::new((Join-Path $base 'native_queries.json'),[System.IO.FileMode]::CreateNew,[System.IO.FileAccess]::Write)
    try{$stream.Write($body)}finally{$stream.Dispose()}
}
if(-not $ok){exit 1}
Write-Output 'NMQ0 direct native query observations retained'
exit 0
