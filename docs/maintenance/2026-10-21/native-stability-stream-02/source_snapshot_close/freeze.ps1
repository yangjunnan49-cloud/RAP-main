$ErrorActionPreference='Stop'
$root=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent;$out=Join-Path $root 'outputs/native_stability_stream_20261021'
New-Item -ItemType Directory -Path (Join-Path $out 'supervision') | Out-Null
$files=@{};foreach($file in Get-ChildItem -LiteralPath $PSScriptRoot -File){$files[$file.Name]=(Get-FileHash -LiteralPath $file.FullName).Hash}
$inputRoot=Join-Path $root 'outputs/native_stability_control_20261021'
$inputs=@{};foreach($name in @('frontend/SEAL.json','frontend/poses.npy','frontend/packets.json','INPUT_BINDINGS.json','RUNTIME_BINDING.json','COSTS_FINAL.json','DELIVERY_SEAL.json')){$inputs[$name]=(Get-FileHash -LiteralPath (Join-Path $inputRoot $name)).Hash}
$freeze=@{files=$files;readonly_N1_inputs=$inputs;protocol_sha256=(Get-FileHash -LiteralPath (Join-Path $out 'PROTOCOL.md')).Hash;chunk_controls_receipt_sha256=(Get-FileHash -LiteralPath (Join-Path $root 'outputs/chunk_hash_feasibility_20261021/run01/normal/worker_exit.json')).Hash;N1_remains_incomplete=$true;whole_scope_cap=1800;work_output_growth_cap=14MB;native_retry_after_N2_failure=$false}
[IO.File]::WriteAllText((Join-Path $out 'supervision/SOURCE_FREEZE.json'),($freeze | ConvertTo-Json -Depth 5),[Text.UTF8Encoding]::new($false))
