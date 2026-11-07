param([ValidateSet('freeze','fetch','validate')][string]$Stage)
$ErrorActionPreference='Stop'
$taskRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$taskBase=Join-Path $taskRoot 'docs/maintenance/2026-10-17/regx-canonical-source-01'
$taskUtf8=[Text.UTF8Encoding]::new($false)
$taskTreeUrl='https://api.github.com/repos/PRBonn/RAP/git/trees/main?recursive=1'
$taskCandidates=@('batch_regx.py','scripts/batch_regx.py')
function Hash([string]$p){(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()}
function Raw([string]$name,[byte[]]$data){
 if([long]((Get-ChildItem -LiteralPath $taskBase -Recurse -File|Measure-Object Length -Sum).Sum)+$data.Length+131072 -gt 8MB){throw 'Dossier write reservation'}
 $f=[IO.FileStream]::new((Join-Path $taskBase $name),[IO.FileMode]::CreateNew,[IO.FileAccess]::Write)
 try{$f.Write($data)}finally{$f.Dispose()}
}
function Save([string]$name,$obj){Raw $name ($taskUtf8.GetBytes(($obj|ConvertTo-Json -Depth 30)+[Environment]::NewLine))}
function BlobIdentity([byte[]]$data){
 $prefix=[Text.Encoding]::ASCII.GetBytes('blob '+$data.Length+[char]0)
 $all=[byte[]]::new($prefix.Length+$data.Length);[Array]::Copy($prefix,0,$all,0,$prefix.Length);[Array]::Copy($data,0,$all,$prefix.Length,$data.Length)
 [Convert]::ToHexString([Security.Cryptography.SHA1]::HashData($all)).ToLowerInvariant()
}
if($Stage -eq 'freeze'){
 $paths=@($PSCommandPath,(Join-Path $PSScriptRoot 'regx_batch_source_query_control.ps1'),(Join-Path $PSScriptRoot 'native_memory_probe.ps1'),(Join-Path $taskBase 'OWNER_SCOPE.md'),(Join-Path $taskBase 'PROTOCOL.md'),(Join-Path $taskRoot 'docs/maintenance/2026-10-16/regx-reference-code-01/transfer-01/00-01.body'),(Join-Path $taskRoot 'docs/maintenance/2026-10-15/demo-reference-documentation-01/response-02.body'),(Join-Path $taskRoot 'docs/maintenance/2026-10-15/official-demo-metadata-01/payload/006.body'))
 New-Item -ItemType Directory -Path (Join-Path $taskBase 'source_snapshot')|Out-Null
 $rows=@();$i=0
 foreach($p in $paths){$name=('source_snapshot/{0:d2}-' -f $i)+[IO.Path]::GetFileName($p);$bytes=[IO.File]::ReadAllBytes($p);Raw $name $bytes;$rows+=[ordered]@{path=$p;bytes=$bytes.Length;sha256=(Hash $p);snapshot_file=$name};$i++}
 Save 'SOURCE_FREEZE.json' ([ordered]@{utc=[DateTime]::UtcNow.ToString('o');tree_url=$taskTreeUrl;candidate_paths=$taskCandidates;body_cap_bytes=196608;old_separate_metadata_body_bytes=1359461;files=$rows})
 Save 'INCOMPLETE' @{pending='Fixed tree/blob metadata and independent local validation'}
 exit 0
}
$freeze=Get-Content -LiteralPath (Join-Path $taskBase 'SOURCE_FREEZE.json') -Raw|ConvertFrom-Json
foreach($row in $freeze.files){foreach($p in @($row.path,(Join-Path $taskBase $row.snapshot_file))){if((Get-Item -LiteralPath $p).Length -ne $row.bytes -or (Hash $p) -ne $row.sha256){throw 'Frozen source identity differs'}}}
function ReadTree(){
 $t=Get-Content -LiteralPath (Join-Path $taskBase 'tree.body') -Raw -Encoding utf8|ConvertFrom-Json
 if($t.truncated -ne $false -or $t.sha -notmatch '^[0-9a-f]{40}$' -or $null -eq $t.tree){throw 'Tree schema/completeness'}
 return $t
}
function SelectFixed($t){@($t.tree|Where-Object {$_.path -in $taskCandidates})}
if($Stage -eq 'validate'){
 $ledger=Get-Content -LiteralPath (Join-Path $taskBase 'QUERY_RESULT.json') -Raw|ConvertFrom-Json
 $receiptNames=@('tree_receipt.json');if(Test-Path -LiteralPath (Join-Path $taskBase 'blob_receipt.json')){$receiptNames+='blob_receipt.json'}
 $actualNames=@(Get-ChildItem -LiteralPath $taskBase -Filter '*_receipt.json' -File|ForEach-Object {$_.Name})
 if(@(Compare-Object ($receiptNames|Sort-Object) ($actualNames|Sort-Object)).Count){throw 'Unexpected HTTP receipt set'}
 $receipts=@($receiptNames|ForEach-Object {Get-Content -LiteralPath (Join-Path $taskBase $_) -Raw|ConvertFrom-Json})
 $total=0L
 foreach($r in $receipts){$p=Join-Path $taskBase $r.body_file;if(-not $r.admitted -or -not $r.complete -or $r.status -ne 200 -or (Hash $p) -ne $r.sha256 -or (Get-Item -LiteralPath $p).Length -ne $r.delivered_body_bytes -or $r.delivered_body_bytes -gt $r.body_cap_bytes){throw 'HTTP receipt identity/admission'};$total+=$r.delivered_body_bytes}
 if($total -ne $ledger.delivered_body_bytes -or $total -gt 196608 -or $receipts.Count -gt 2 -or $receipts[0].url -ne $taskTreeUrl){throw 'Combined request/body ledger'}
 $t=ReadTree;$selected=@(SelectFixed $t)
 $expected=if($selected.Count -eq 0){'SOURCE_NOT_PRESENT_IN_THIS_OBSERVED_TREE'}elseif($selected.Count -ne 1){'AMBIGUOUS_FIXED_SOURCE_PATHS'}elseif($selected[0].type -ne 'blob' -or $selected[0].size -gt 65536){'FIXED_SOURCE_OVERSIZE_OR_NONBLOB'}else{'EXACT_BATCH_SOURCE_BODY_ACQUIRED'}
 if($ledger.status -ne $expected -or $ledger.observed_tree_SHA -ne $t.sha){throw 'Fixed source decision differs'}
 if($expected -eq 'EXACT_BATCH_SOURCE_BODY_ACQUIRED'){
  if($receipts.Count -ne 2 -or $receipts[1].url -ne ('https://api.github.com/repos/PRBonn/RAP/git/blobs/'+$selected[0].sha)){throw 'Unexpected blob route'}
  $b=Get-Content -LiteralPath (Join-Path $taskBase 'blob.body') -Raw -Encoding utf8|ConvertFrom-Json
  if($b.encoding -ne 'base64' -or $b.sha -ne $selected[0].sha){throw 'Blob schema'}
  $decoded=[Convert]::FromBase64String($b.content)
  if($decoded.Length -ne $selected[0].size -or $decoded.Length -ne $b.size -or (BlobIdentity $decoded) -ne $selected[0].sha){throw 'Decoded Git identity'}
  $saved=[IO.File]::ReadAllBytes((Join-Path $taskBase 'CANONICAL_BATCH_SOURCE.py.txt'))
  if([Convert]::ToBase64String($saved) -ne [Convert]::ToBase64String($decoded)){throw 'Decoded source output differs'}
 }elseif($receipts.Count -ne 1){throw 'Unexpected additional request'}
 Save 'VALIDATION.json' ([ordered]@{status='VALIDATED_FIXED_CANONICAL_SOURCE_QUERY';query_status=$expected;observed_tree_SHA=$t.sha;complete_tree_entries=@($t.tree).Count;selected_paths=@($selected.path);delivered_body_bytes=$total;requests=$receipts.Count;old_separate_metadata_body_bytes=1359461;arithmetic_subtotal_metadata_body_bytes=(1359461+$total);old_ledger_unchanged=$true;independent_local_validation=$true;additional_HTTP=0;downloaded_code_executed=$false;numeric_point_pose_model_or_solver=$false;all_history_absence_claim=$false})
 Write-Output ('Validated: '+$expected)
 exit 0
}
if(Test-Path -LiteralPath (Join-Path $taskBase 'REQUEST_STARTED.json')){throw 'No HTTP replay allowed'}
Save 'REQUEST_STARTED.json' ([ordered]@{utc=[DateTime]::UtcNow.ToString('o');tree_url=$taskTreeUrl;candidate_paths=$taskCandidates;maximum_requests=2})
$script:taskDelivered=0L
function Fetch([string]$url,[string]$label,[int]$cap){
 $handler=[Net.Http.HttpClientHandler]::new();$handler.AllowAutoRedirect=$false;$handler.AutomaticDecompression=[Net.DecompressionMethods]::None
 $client=[Net.Http.HttpClient]::new($handler);$client.Timeout=[TimeSpan]::FromSeconds(30)
 $request=[Net.Http.HttpRequestMessage]::new([Net.Http.HttpMethod]::Get,$url)
 $request.Headers.TryAddWithoutValidation('User-Agent','RAP-fixed-canonical-source-query')|Out-Null
 $request.Headers.TryAddWithoutValidation('Accept-Encoding','identity')|Out-Null
 $memory=[IO.MemoryStream]::new();$response=$null;$headers=@{};$status=$null;$complete=$false;$errorText=$null;$clock=[Diagnostics.Stopwatch]::StartNew()
 $cancel=[Threading.CancellationTokenSource]::new([TimeSpan]::FromSeconds(60))
 try{
  $response=$client.Send($request,[Net.Http.HttpCompletionOption]::ResponseHeadersRead);$status=[int]$response.StatusCode
  foreach($h in $response.Headers){$headers[$h.Key.ToLowerInvariant()]=($h.Value -join ', ')}
  foreach($h in $response.Content.Headers){$headers[$h.Key.ToLowerInvariant()]=($h.Value -join ', ')}
  if($status -ne 200){throw "Non200 HTTP $status; body not read"}
  if($headers['content-encoding'] -and $headers['content-encoding'] -ne 'identity'){throw 'Encoded body not admitted'}
  $length=$response.Content.Headers.ContentLength
  if($null -ne $length -and $length -gt $cap){throw 'Declared source body cap'}
  $stream=$response.Content.ReadAsStream()
  try{$buffer=[byte[]]::new(8192);while($memory.Length -lt $cap){$n=$stream.ReadAsync($buffer,0,[int][Math]::Min($buffer.Length,$cap-$memory.Length),$cancel.Token).GetAwaiter().GetResult();if($n -eq 0){$complete=$true;break};$memory.Write($buffer,0,$n)}}finally{$stream.Dispose()}
  if($memory.Length -eq $cap){$complete=($null -ne $length -and $length -eq $cap)}
  if(-not $complete -or ($null -ne $length -and $length -ne $memory.Length)){throw 'Incomplete bounded source body'}
 }catch{$errorText=$_.Exception.ToString()}
 finally{
  if($response){$response.Dispose()};$request.Dispose();$client.Dispose();$handler.Dispose();$cancel.Dispose()
  $body=$memory.ToArray();$memory.Dispose();$script:taskDelivered+=$body.Length
  Raw ($label+'.body') $body
  Save ($label+'_receipt.json') ([ordered]@{utc=[DateTime]::UtcNow.ToString('o');url=$url;status=$status;headers=$headers;body_file=($label+'.body');body_cap_bytes=$cap;delivered_body_bytes=$body.Length;sha256=(Hash (Join-Path $taskBase ($label+'.body')));complete=$complete;admitted=($null -eq $errorText);error=$errorText;transport_seconds=$clock.Elapsed.TotalSeconds;retries=0;redirects_followed=0})
 }
 if($script:taskDelivered -gt 196608){throw 'Combined source body cap'}
 if($errorText){throw $errorText}
}
Fetch $taskTreeUrl 'tree' 65536
$tree=ReadTree;$selected=@(SelectFixed $tree)
$decision=if($selected.Count -eq 0){'SOURCE_NOT_PRESENT_IN_THIS_OBSERVED_TREE'}elseif($selected.Count -ne 1){'AMBIGUOUS_FIXED_SOURCE_PATHS'}elseif($selected[0].type -ne 'blob' -or $selected[0].size -gt 65536){'FIXED_SOURCE_OVERSIZE_OR_NONBLOB'}else{'EXACT_BATCH_SOURCE_BODY_ACQUIRED'}
if($decision -eq 'EXACT_BATCH_SOURCE_BODY_ACQUIRED'){
 if($selected[0].sha -notmatch '^[0-9a-f]{40}$'){throw 'Selected blob SHA invalid'}
 Fetch ('https://api.github.com/repos/PRBonn/RAP/git/blobs/'+$selected[0].sha) 'blob' 131072
 $blob=Get-Content -LiteralPath (Join-Path $taskBase 'blob.body') -Raw -Encoding utf8|ConvertFrom-Json
 if($blob.encoding -ne 'base64' -or $blob.sha -ne $selected[0].sha){throw 'Blob schema'}
 $data=[Convert]::FromBase64String($blob.content)
 if($data.Length -ne $selected[0].size -or $data.Length -ne $blob.size -or (BlobIdentity $data) -ne $selected[0].sha){throw 'Decoded Git identity'}
 Raw 'CANONICAL_BATCH_SOURCE.py.txt' $data
}
Save 'QUERY_RESULT.json' ([ordered]@{status=$decision;observed_tree_SHA=$tree.sha;complete_tree_entries=@($tree.tree).Count;selected_paths=@($selected.path);delivered_body_bytes=$script:taskDelivered;downloaded_code_executed=$false;physical_reference_authenticated=$false;canonical_runtime_reproduced=$false;new_efficacy_admitted=$false})
Write-Output $decision
