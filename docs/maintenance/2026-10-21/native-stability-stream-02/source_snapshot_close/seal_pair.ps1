$ErrorActionPreference='Stop'
$root=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent;$out=Join-Path $root 'outputs/native_stability_stream_20261021'
$freeze=Get-Content -Raw (Join-Path $out 'supervision/SOURCE_FREEZE.json') | ConvertFrom-Json
foreach($file in $freeze.files.PSObject.Properties){if((Get-FileHash -LiteralPath (Join-Path $PSScriptRoot $file.Name)).Hash -ne $file.Value){throw 'N2 frozen source changed'}}
$files=@{}
foreach($stage in @('native1','native2')){
    $folder=Join-Path $out ('supervision/'+$stage)
    foreach($name in @('worker_exit.json','runner_exit.json')){if(-not (Get-Content -Raw (Join-Path $folder $name) | ConvertFrom-Json).success){throw 'Cannot compare incomplete native controls'}}
    $summary=Get-Content -Raw (Join-Path $folder 'COARSE_SUMMARY.json') | ConvertFrom-Json
    if($summary.frame_calls -ne 1101 -or $summary.fine_graph_calls -ne 0 -or $summary.GT_reads -ne 0){throw 'Wrong coarse scope'}
    foreach($name in @('coarse_poses.npy','coarse_keyposes.npy','events.jsonl.gz','COARSE_SUMMARY.json','worker_exit.json','runner_exit.json','host_exit.json')){$files[$stage+'/'+$name]=(Get-FileHash -LiteralPath (Join-Path $folder $name)).Hash}
}
$result=@{both_controls_complete=$true;frame_calls=2202;files=$files;input_seal_sha256=(Get-FileHash -LiteralPath (Join-Path $root 'outputs/native_stability_control_20261021/frontend/SEAL.json')).Hash;analysis_source_sha256=(Get-FileHash -LiteralPath (Join-Path $PSScriptRoot 'native_stage.py')).Hash;GT_reads=0;sealed_before_comparison=$true}
[IO.File]::WriteAllText((Join-Path $out 'PAIRED_SEAL.json'),($result | ConvertTo-Json -Depth 5),[Text.UTF8Encoding]::new($false))
