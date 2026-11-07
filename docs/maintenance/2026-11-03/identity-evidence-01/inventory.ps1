$ErrorActionPreference = 'Stop'
$taskDir = $PSScriptRoot
$origin = [DateTimeOffset]::Parse('2026-11-03T04:30:00Z')
if (([DateTimeOffset]::UtcNow - $origin).TotalSeconds -ge 3300) { throw 'EIA1 reporting reserve' }
function Write-NewJson($name, $value) {
    $path = Join-Path $taskDir $name
    if (Test-Path -LiteralPath $path) { throw "Output already exists: $path" }
    [IO.File]::WriteAllText($path, (ConvertTo-Json -InputObject $value -Depth 15), [Text.UTF8Encoding]::new($false))
}
function File-Identity($path) {
    $item = Get-Item -LiteralPath $path
    [ordered]@{path=$item.FullName; bytes=$item.Length; sha256=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()}
}
$paths = [ordered]@{
    input='C:\Users\AAA\Documents\Codex\2026-10-31\agetns-md\outputs\provenance_time_20261031\INPUT_BINDING.json'
    image='E:\githouse\RAP-main\docs\maintenance\2026-10-28\image-packet-verification-01\IMAGE_MANIFEST.json'
    image_archive='E:\githouse\RAP-main\docs\maintenance\2026-10-28\image-archive-admission-01\RESULTS.json'
    graph_rows='C:\Users\AAA\Documents\Codex\2026-10-31\agetns-md\outputs\graph_candidate_20261031\integration02\evaluate\ROWS.json'
    gate_rows='C:\Users\AAA\Documents\Codex\2026-10-31\agetns-md\outputs\graph_gate_20261031\evaluate\ROWS.json'
}
$bindings = @($paths.Values | ForEach-Object { File-Identity $_ })
$bindings += File-Identity $PSCommandPath
$bindings += File-Identity (Join-Path $taskDir 'INVENTORY_PROTOCOL.md')
Write-NewJson 'INVENTORY_INPUT_BINDING.json' ([ordered]@{utc=[DateTime]::UtcNow.ToString('o'); files=$bindings; point_arrays_read=$false; pose_values_read=$false})
$inputDoc = Get-Content -Raw -LiteralPath $paths.input | ConvertFrom-Json
if (@($inputDoc.pairs).Count -ne 200 -or @($inputDoc.raw).Count -ne 273) { throw 'Input census mismatch' }
$generation = [Collections.Generic.HashSet[string]]::new()
foreach ($r in $inputDoc.raw) { [void]$generation.Add(('{0}/{1:d6}' -f $r.sequence,[int]$r.frame)) }
$images = @{}
$imageDoc = Get-Content -Raw -LiteralPath $paths.image | ConvertFrom-Json
foreach ($im in $imageDoc.rows) {
    $frame = [int][IO.Path]::GetFileNameWithoutExtension($im.member)
    $images[('{0}/{1:d6}' -f $im.sequence,$frame)] = $im
}
$rows = @()
foreach ($pair in $inputDoc.pairs) {
    $endpoints = @()
    foreach ($frame in @([int]$pair.source_i,[int]$pair.source_j)) {
        $id = '{0}/{1:d6}' -f $pair.sequence,$frame
        $witnesses = @()
        foreach ($offset in @(-10,-1)) {
            $wframe = $frame + $offset
            $wid = '{0}/{1:d6}' -f $pair.sequence,$wframe
            $wpath = 'E:/githouse/Datasets/data_odometry_velodyne/dataset/sequences/{0}/velodyne/{1:d6}.bin' -f $pair.sequence,$wframe
            $exists = $wframe -ge 0 -and (Test-Path -LiteralPath $wpath -PathType Leaf)
            $witnesses += [ordered]@{offset=$offset; id=$wid; path=$wpath; exists=$exists; bytes=if($exists){(Get-Item -LiteralPath $wpath).Length}else{$null}; in_generation_bank=$generation.Contains($wid); acquisition_identity_only=$true}
        }
        $im = $images[$id]
        $endpoints += [ordered]@{id=$id;frame=$frame;image0_in_prior_packet=($null -ne $im);image0_identity=$im;additional_scans=$witnesses}
    }
    $rows += [ordered]@{key=$pair.key;sequence=$pair.sequence;endpoints=$endpoints;new_physical_identity_evidence_admitted=$false}
}
$probes = @()
foreach ($root in @('E:/githouse/Datasets/data_odometry_velodyne/dataset/sequences','E:/githouse/RAP-SLAM/data/kitti/dataset/sequences')) {
    foreach ($sequence in @('00','08')) {
        foreach ($name in @('oxts','timestamps.txt','timestamps_start.txt','timestamps_end.txt','velodyne_points','per_point_timestamps','calibration_provenance.json','source_archive_manifest.json')) {
            $path = "$root/$sequence/$name"
            $probes += [ordered]@{path=$path;exists=(Test-Path -LiteralPath $path)}
        }
    }
}
$archive = Get-Content -Raw -LiteralPath $paths.image_archive | ConvertFrom-Json
$archiveItem = Get-Item -LiteralPath $archive.archive_path
$archiveStatus = [ordered]@{path=$archive.archive_path;bytes=$archiveItem.Length;mtime_utc=$archiveItem.LastWriteTimeUtc.ToString('o');prior_bytes=$archive.archive_bytes;size_matches=($archiveItem.Length -eq $archive.archive_bytes);prior_full_sha256=$archive.archive_sha256;current_full_hash_checked=$false;prior_index_camera_counts=$archive.camera_counts;new_index_checked=$false;new_image_decodes=0}
Write-NewJson 'SOURCE_CENSUS.json' ([ordered]@{utc=[DateTime]::UtcNow.ToString('o');pairs=$rows;source_probes=$probes;archive=$archiveStatus;physical_identity_evidence_admitted=$false;full_machine_absence_claim=$false})
Write-NewJson 'SOURCE_CENSUS_SEAL.json' (File-Identity (Join-Path $taskDir 'SOURCE_CENSUS.json'))
# Join exposed diagnostic membership only after the source census is sealed.
$graph = Get-Content -Raw -LiteralPath $paths.graph_rows | ConvertFrom-Json
$gate = Get-Content -Raw -LiteralPath $paths.gate_rows | ConvertFrom-Json
$gm=@{}; $tm=@{}
foreach ($r in $graph) { $gm[$r.key]=$r }
foreach ($r in $gate) { $tm[$r.key]=$r }
$joined=@()
foreach ($r in $rows) {
    $g=$gm[$r.key]; $t=$tm[$r.key]
    if ($null -eq $g -or $null -eq $t) { throw 'Join missing ID' }
    $w = @($r.endpoints | ForEach-Object { $_.additional_scans })
    $joined += [ordered]@{key=$r.key;sequence=$r.sequence;positive=(-not $g.confuser);oldunique27=[bool]$g.old_RAP_unique;missing64=[bool]$g.missing64;oldwrong9=[bool]$t.J_wrong_accept;currentwrong8=[bool]$t.wrong_accepted;all_4_witnesses_exist=(@($w | Where-Object { -not $_.exists }).Count -eq 0);both_endpoint_minus10_unseen=(@($w | Where-Object { $_.offset -eq -10 -and $_.exists -and -not $_.in_generation_bank }).Count -eq 2);both_endpoint_minus1_unseen=(@($w | Where-Object { $_.offset -eq -1 -and $_.exists -and -not $_.in_generation_bank }).Count -eq 2);both_image0_in_packet=(@($r.endpoints | Where-Object { $_.image0_in_prior_packet }).Count -eq 2)}
}
$summaries=@()
foreach ($group in @('all200','positive','oldunique27','missing64','oldwrong9','currentwrong8')) {
    $selected=if($group -eq 'all200'){@($joined)}else{@($joined | Where-Object { $_[$group] })}
    $summaries += [ordered]@{group=$group;n=$selected.Count;all_4_witnesses_exist=@($selected | Where-Object { $_.all_4_witnesses_exist }).Count;both_minus10_outside_generation=@($selected | Where-Object { $_.both_endpoint_minus10_unseen }).Count;both_minus1_outside_generation=@($selected | Where-Object { $_.both_endpoint_minus1_unseen }).Count;both_image0_in_packet=@($selected | Where-Object { $_.both_image0_in_packet }).Count}
}
Write-NewJson 'COVERAGE_GROUPS.json' ([ordered]@{utc=[DateTime]::UtcNow.ToString('o');rows=$joined;groups=$summaries;groups_not_disjoint=$true;new_numerical_result=$false;new_evidence_source_admitted=$false;all_source_census_sealed_before_join=$true})
$summaries | ConvertTo-Json -Depth 4
