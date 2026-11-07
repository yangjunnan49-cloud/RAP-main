$ErrorActionPreference='Stop'
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$base=Join-Path $root 'docs/maintenance/2026-10-15/continuation-handoff-07'
$old=Join-Path $root 'docs/maintenance/2026-10-15/continuation-handoff-06'
$checked=@{};$refs=0
function Check([string]$p,$row){
 $script:refs++
 if($p.StartsWith('/mnt/e/')){$p='E:\'+$p.Substring(7).Replace('/','\')}
 elseif(-not [IO.Path]::IsPathRooted($p)){$p=Join-Path $root $p}
 $p=[IO.Path]::GetFullPath($p)
 $expected=@{bytes=[long]$row.bytes;sha256=[string]$row.sha256}
 if($checked.ContainsKey($p)){if($checked[$p].bytes -ne $expected.bytes -or $checked[$p].sha256 -cne $expected.sha256){throw 'Conflicting expected identity'};return}
 if((Get-Item -LiteralPath $p).Length -ne $expected.bytes -or (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant() -cne $expected.sha256){throw ('Identity mismatch '+$p)}
 $checked[$p]=$expected
}
function Seal([string]$folder,[string]$name){$s=Get-Content -LiteralPath (Join-Path $folder $name) -Raw|ConvertFrom-Json;foreach($e in $s.files){Check (Join-Path $folder $e.path) $e};return $s.files.Count}
$prior=Get-Content -LiteralPath (Join-Path $old 'IDENTITY_CHECKS.json') -Raw|ConvertFrom-Json -AsHashtable
foreach($item in $prior.files.GetEnumerator()){Check $item.Key $item.Value}
$oldCounts=@{};foreach($name in @('DELIVERY_SEAL.json','FINAL_VERIFICATION_SEAL.json','ACCOUNT_STOP_SEAL.json')){$oldCounts[$name]=Seal $old $name}
$oldCounts['owner-close-01']=Seal (Join-Path $old 'owner-close-01') 'DELIVERY_SEAL.json'
foreach($marker in $prior.retained_markers){$p='E:\'+$marker.Substring(7).Replace('/','\');if(-not (Test-Path -LiteralPath $p)){throw 'Inherited marker missing'}}
$scopes=@('original-demo-archive-metadata-01','demo-reference-documentation-01','author-demo-clarification-01','joint-mechanism-assessment-01')
$newCounts=@{}
foreach($scope in $scopes){$folder=Join-Path (Split-Path $base -Parent) $scope;$newCounts[$scope]=Seal $folder 'DELIVERY_SEAL.json'}
$bindings=@('original-demo-archive-metadata-01/freeze.json','original-demo-archive-metadata-01/local_bindings.json','original-demo-archive-metadata-01/local_bindings02.json',
 'demo-reference-documentation-01/freeze.json','demo-reference-documentation-01/CONTINUATION02.json','author-demo-clarification-01/freeze.json','joint-mechanism-assessment-01/SOURCE_INDEX.json')
foreach($binding in $bindings){$f=Get-Content -LiteralPath (Join-Path (Split-Path $base -Parent) $binding) -Raw|ConvertFrom-Json;foreach($row in $f.files){Check $row.path $row}}
$oda=Get-Content -LiteralPath (Join-Path (Split-Path $base -Parent) 'original-demo-archive-metadata-01/CHECKS.json') -Raw|ConvertFrom-Json
$drd=Get-Content -LiteralPath (Join-Path (Split-Path $base -Parent) 'demo-reference-documentation-01/CHECKS.json') -Raw|ConvertFrom-Json
$adc=Get-Content -LiteralPath (Join-Path (Split-Path $base -Parent) 'author-demo-clarification-01/CHECKS.json') -Raw|ConvertFrom-Json
$seconds=$oda.recorded_enclosing_seconds+$drd.recorded_enclosing_seconds+$adc.recorded_enclosing_seconds
if([Math]::Abs($seconds-31.2844777) -gt 1e-8 -or $adc.combined_body_bytes -ne 1357466){throw 'Resource/body scalar reconciliation'}
$result=@{passed=$true;unique_verified_paths=$checked.Count;identity_references=$refs;files=$checked;old_seal_entries=$oldCounts;new_delivery_entries=$newCounts;
 inherited_retained_markers=$prior.retained_markers.Count;new_enclosing_attempts=12;successes=9;retained_failures=3;recorded_enclosing_seconds=$seconds;
 combined_body_bytes=1357466;body_cap=4194304;original_DRD_syntax_failure_peak_RSS='UNKNOWN';observer_full_lifetime_peak='UNKNOWN';ordinary_setup_RSS='UNKNOWN';
 all_attempt_memory_cap_certified=$false;no_new_model_fit_pose_or_network_calls_in_this_verification=$true;UTC=[DateTime]::UtcNow.ToString('o')}
$utf8=[Text.UTF8Encoding]::new($false);$path=Join-Path $base 'IDENTITY_CHECKS.json';if(Test-Path -LiteralPath $path){throw 'Existing closure preserved'}
[IO.File]::WriteAllText($path,($result|ConvertTo-Json -Depth 12),$utf8)
Write-Output (@{passed=$true;unique_verified_paths=$checked.Count;identity_references=$refs;old_seal_entries=$oldCounts;new_delivery_entries=$newCounts}|ConvertTo-Json -Depth 5)
