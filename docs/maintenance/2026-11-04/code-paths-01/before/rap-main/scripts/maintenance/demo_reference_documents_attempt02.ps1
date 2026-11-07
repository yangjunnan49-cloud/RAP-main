param([ValidateSet('observe02')][string]$Stage)
$ErrorActionPreference='Stop'
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$base=Join-Path $root 'docs/maintenance/2026-10-15/demo-reference-documentation-01'
$utf8=[Text.UTF8Encoding]::new($false)
function Hash([string]$p){return (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()}
function Save([string]$Name,$Value){
 $bytes=$utf8.GetBytes(($Value|ConvertTo-Json -Depth 45)+"`n")
 if([long]((Get-ChildItem -LiteralPath $base -Recurse -File|Measure-Object Length -Sum).Sum)+$bytes.Length -gt 7MB){throw 'Dossier reserve'}
 $f=[IO.FileStream]::new((Join-Path $base $Name),[IO.FileMode]::CreateNew,[IO.FileAccess]::Write);try{$f.Write($bytes)}finally{$f.Dispose()}
}
if($Stage -eq 'freeze'){
 $paths=@($PSCommandPath,(Join-Path $PSScriptRoot 'demo_reference_documents_control.ps1'),(Join-Path $base 'PROTOCOL.md'),(Join-Path $root 'scripts/download_weights_and_demo_data.sh'),(Join-Path $root 'docs/maintenance/2026-10-15/original-demo-archive-metadata-01/DELIVERY_SEAL.json'),(Join-Path $root 'docs/maintenance/2026-10-15/continuation-handoff-06/DEMO_MEMBER_REQUEST.json'))
 Save 'freeze.json' @{files=@($paths|ForEach-Object {@{path=$_;bytes=(Get-Item -LiteralPath $_).Length;sha256=(Hash $_)}});prior_body_bytes=1296794;combined_body_cap=4194304;utc=[DateTime]::UtcNow.ToString('o')}
 Save 'INCOMPLETE' @{pending='finite author documentation observation/independent decision'};exit 0
}
$freeze=Get-Content -LiteralPath (Join-Path $base 'freeze.json') -Raw|ConvertFrom-Json
foreach($f in $freeze.files){if((Hash $f.path) -cne $f.sha256 -or (Get-Item -LiteralPath $f.path).Length -ne $f.bytes){throw 'Frozen source changed'}}
$handler=[Net.Http.HttpClientHandler]::new();$handler.AllowAutoRedirect=$false;$handler.AutomaticDecompression=[Net.DecompressionMethods]::None
$client=[Net.Http.HttpClient]::new($handler);$client.Timeout=[TimeSpan]::FromSeconds(20)
$receipts=[Collections.Generic.List[object]]::new(); foreach($previous in @(Get-ChildItem -LiteralPath $base -Filter 'receipt-*.json'|Sort-Object Name)){ $receipts.Add((Get-Content -LiteralPath $previous.FullName -Raw|ConvertFrom-Json -AsHashtable)) }; $spent=[long](($receipts|Measure-Object bytes -Sum).Sum)
function Fetch([string]$Url,[string]$Kind,[int]$Limit){
 $u=[Uri]$Url
 if($u.Scheme -ne 'https' -or $u.Host -notin @('www.ipb.uni-bonn.de','register-any-point.github.io','api.github.com')){throw 'Authority outside scope'}
 if($u.Host -eq 'api.github.com' -and $u.AbsolutePath -notmatch '^/repos/PRBonn/RAP/git/(trees/main|blobs/[a-f0-9]{40})$'){throw 'Nonmetadata GitHub route'}
 if($receipts.Count -ge 6 -or $spent+$Limit -gt 2897510){throw 'Request/body reservation cap'}
 $req=[Net.Http.HttpRequestMessage]::new([Net.Http.HttpMethod]::Get,$Url);$req.Headers.TryAddWithoutValidation('User-Agent','RAP-reference-documentation-audit')|Out-Null;$req.Headers.TryAddWithoutValidation('Accept-Encoding','identity')|Out-Null
 $response=$null;$memory=[IO.MemoryStream]::new();$headers=@{};$status=$null;$errorText=$null;$complete=$false
 try{
  $response=$client.Send($req,[Net.Http.HttpCompletionOption]::ResponseHeadersRead);$status=[int]$response.StatusCode
  foreach($h in $response.Headers){$headers[$h.Key.ToLowerInvariant()]=($h.Value -join ', ')};foreach($h in $response.Content.Headers){$headers[$h.Key.ToLowerInvariant()]=($h.Value -join ', ')}
  if($status -ne 200){throw "Non200 metadata response $status; body not read"}
  if($headers['content-encoding'] -and $headers['content-encoding'] -ne 'identity'){throw 'Encoded metadata response'}
  $length=$response.Content.Headers.ContentLength;if($null -ne $length -and $length -gt $Limit){throw 'Oversized declared body'}
  $inputStream=$response.Content.ReadAsStream()
  try{$buffer=[byte[]]::new(65536);while($memory.Length -lt $Limit){$n=$inputStream.Read($buffer,0,[int][Math]::Min($buffer.Length,$Limit-$memory.Length));if($n -eq 0){$complete=$true;break};$memory.Write($buffer,0,$n)}}finally{$inputStream.Dispose()}
  if($memory.Length -eq $Limit){$complete=($null -ne $length -and $length -eq $Limit)}
  if(-not $complete -or ($null -ne $length -and $length -ne $memory.Length)){throw 'Metadata completeness unproved'}
 }catch{$errorText=$_.Exception.ToString()}
 finally{if($response){$response.Dispose()};$req.Dispose()}
 $body=$memory.ToArray();$memory.Dispose();$script:spent+=$body.Length;$index=$receipts.Count;$name='response-{0:d2}.body' -f $index
 $f=[IO.FileStream]::new((Join-Path $base $name),[IO.FileMode]::CreateNew,[IO.FileAccess]::Write);try{$f.Write($body)}finally{$f.Dispose()}
 $r=@{index=$index;url=$Url;kind=$Kind;status=$status;headers=$headers;bytes=$body.Length;body_path=$name;sha256=(Hash (Join-Path $base $name));complete=$complete;error=$errorText;admitted=($null -eq $errorText)}
 $receipts.Add($r);Save ('receipt-{0:d2}.json' -f $index) $r
 return @{receipt=$r;body=$body}
}
try{
 # Original retained Bonn403 receipt is not replayed.
 # Original retained author HTML receipt is reused without another request.
 $tree=Fetch 'https://api.github.com/repos/PRBonn/RAP/git/trees/main?recursive=1' 'author_source_tree_metadata' 524288
 $selected=[Collections.Generic.List[object]]::new();$treeIdentity=$null
 if($tree.receipt.admitted){
  $t=$utf8.GetString($tree.body)|ConvertFrom-Json
  if($t.truncated){throw 'Truncated tree; selection stopped'};$treeIdentity=$t.sha
  $candidates=@($t.tree|Where-Object {$_.type -eq 'blob' -and ($_.path -in @('README.md','scripts/download_weights_and_demo_data.sh') -or ($_.path -match '(?i)demo' -and $_.path -match '(?i)(manifest|reference|ground_truth|pose)' -and $_.path -match '\.(md|json|yaml|txt)$'))}|Sort-Object path|Select-Object -First 3)
  foreach($entry in $candidates){
   if($entry.size -gt 131072){continue}
   $f=Fetch ('https://api.github.com/repos/PRBonn/RAP/git/blobs/'+$entry.sha) 'exact_author_document_blob_JSON' 262144
   if(-not $f.receipt.admitted){continue};$blob=$utf8.GetString($f.body)|ConvertFrom-Json
   if($blob.encoding -ne 'base64'){throw 'Unexpected blob encoding'};$decoded=[Convert]::FromBase64String($blob.content)
   $prefix=[Text.Encoding]::ASCII.GetBytes(('blob '+$decoded.Length+[char]0));$gitHasher=[Security.Cryptography.IncrementalHash]::CreateHash([Security.Cryptography.HashAlgorithmName]::SHA1)
   try{$gitHasher.AppendData($prefix);$gitHasher.AppendData($decoded);$actual=[Convert]::ToHexString($gitHasher.GetHashAndReset()).ToLowerInvariant()}finally{$gitHasher.Dispose()}
   if($actual -cne $entry.sha -or $blob.sha -cne $entry.sha -or $decoded.Length -ne $entry.size){throw 'Pinned blob identity mismatch'}
   $name='document-{0:d2}.txt' -f $selected.Count;$out=[IO.FileStream]::new((Join-Path $base $name),[IO.FileMode]::CreateNew,[IO.FileAccess]::Write);try{$out.Write($decoded)}finally{$out.Dispose()}
   $selected.Add(@{path=$entry.path;git_blob_SHA1=$actual;bytes=$decoded.Length;response_index=$f.receipt.index;decoded_path=$name})
  }
 }
 Save 'observation.json' @{requests=$receipts.Count;new_body_bytes=$spent;prior_body_bytes=1296794;combined_body_bytes=1296794+$spent;body_cap=4194304;complete_source_tree=$tree.receipt.admitted;observed_tree_SHA=$treeIdentity;documents=$selected.ToArray();reference_authenticated=$false;member_payload_requested=$false;utc=[DateTime]::UtcNow.ToString('o')}
}finally{$client.Dispose();$handler.Dispose()}
