$ErrorActionPreference='Stop'
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$base=Join-Path $root 'docs/maintenance/2026-10-15/original-demo-archive-metadata-01'
$utf8=[Text.UTF8Encoding]::new($false)
function Hash([string]$p){return (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()}
function Save([string]$Name,$Value){
    $data=$utf8.GetBytes(($Value|ConvertTo-Json -Depth 20)+"`n")
    if([long]((Get-ChildItem -LiteralPath $base -Recurse -File|Measure-Object Length -Sum).Sum)+$data.Length -gt 7MB){throw 'Dossier reserve exceeded'}
    $f=[IO.FileStream]::new((Join-Path $base $Name),[IO.FileMode]::CreateNew,[IO.FileAccess]::Write)
    try{$f.Write($data)}finally{$f.Dispose()}
}
$paths=@($PSCommandPath,(Join-Path $PSScriptRoot 'original_archive_inventory_control.ps1'),
 (Join-Path $PSScriptRoot 'validate_original_archive_inventory.py'),(Join-Path $PSScriptRoot 'invoke_mgr_supervised_wsl.ps1'),
 (Join-Path $base 'freeze.json'),(Join-Path $base 'network_result.json'),(Join-Path $base 'directory_location.json'),
 (Join-Path $base 'response-01.bin'),(Join-Path $base 'response-02.bin'),
 (Join-Path $root 'docs/maintenance/2026-10-15/continuation-handoff-06/DEMO_MEMBER_REQUEST.json'))
$bindings=foreach($p in $paths){@{path=$p;bytes=(Get-Item -LiteralPath $p).Length;sha256=(Hash $p)}}
Save 'local_bindings.json' @{files=@($bindings);scope='Conditional complete metadata/local-byte inventory; no coordinates or new HTTP';before_local_byte_work_UTC=[DateTime]::UtcNow.ToString('o')}
Add-Type -TypeDefinition @'
using System;
using System.IO;
using System.Security.Cryptography;
public static class OdaLocalBytes {
  static readonly uint[] Table=Build();
  static uint[] Build(){var t=new uint[256];for(uint i=0;i<256;i++){uint c=i;for(int k=0;k<8;k++)c=(c&1)!=0?0xedb88320U^(c>>1):c>>1;t[i]=c;}return t;}
  public static uint Crc(byte[] bytes){uint c=0xffffffffU;foreach(byte b in bytes)c=Table[(c^b)&255]^(c>>8);return c^0xffffffffU;}
  public static string[] Read(string path){
    using(var f=new FileStream(path,FileMode.Open,FileAccess.Read,FileShare.Read))
    using(var h=IncrementalHash.CreateHash(HashAlgorithmName.SHA256)){
      var buf=new byte[1048576];uint c=0xffffffffU;long count=0;int n;
      while((n=f.Read(buf,0,buf.Length))>0){h.AppendData(buf,0,n);count+=n;for(int i=0;i<n;i++)c=Table[(c^buf[i])&255]^(c>>8);}
      return new string[]{count.ToString(),(c^0xffffffffU).ToString("x8"),Convert.ToHexString(h.GetHashAndReset()).ToLowerInvariant()};
    }
  }
}
'@
if([OdaLocalBytes]::Crc([Text.Encoding]::ASCII.GetBytes('123456789')) -ne 0xcbf43926 -or [OdaLocalBytes]::Crc([byte[]]::new(0)) -ne 0){throw 'CRC standard controls failed'}
$loc=Get-Content -LiteralPath (Join-Path $base 'directory_location.json') -Raw|ConvertFrom-Json
$data=[IO.File]::ReadAllBytes((Join-Path $base 'response-02.bin'))
$memory=[IO.MemoryStream]::new($data,$false);$br=[IO.BinaryReader]::new($memory)
$entries=[Collections.Generic.List[object]]::new();$seen=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
try{
    for($i=0;$i -lt $loc.entries;$i++){
        $start=$memory.Position;if($data.Length-$start -lt 46 -or $br.ReadUInt32() -ne 0x02014b50){throw 'Central entry signature/bounds'}
        $made=$br.ReadUInt16();$needed=$br.ReadUInt16();$flags=$br.ReadUInt16();$method=$br.ReadUInt16();$time=$br.ReadUInt16();$date=$br.ReadUInt16()
        $crc=$br.ReadUInt32();$compressed=$br.ReadUInt32();$size=$br.ReadUInt32();$nl=$br.ReadUInt16();$xl=$br.ReadUInt16();$cl=$br.ReadUInt16()
        $disk=$br.ReadUInt16();$internal=$br.ReadUInt16();$external=$br.ReadUInt32();$local=$br.ReadUInt32()
        if($nl -le 0 -or $memory.Position+$nl+$xl+$cl -gt $data.Length -or $disk -ne 0 -or $size -eq [uint32]::MaxValue -or $local -ge $loc.offset){throw 'Central entry layout'}
        $nameBytes=$br.ReadBytes($nl)
        if(@($nameBytes|Where-Object {$_ -gt 127}).Count -gt 0 -and ($flags -band 2048) -eq 0){throw 'NonASCII legacy encoding unsupported'}
        $name=$utf8.GetString($nameBytes);$extra=$br.ReadBytes($xl);$comment=$br.ReadBytes($cl)
        if($name.Contains('..') -or $name.Contains('\') -or $name.StartsWith('/') -or -not $seen.Add($name)){throw 'Unsafe/duplicate central name'}
        $tags=[Collections.Generic.List[object]]::new();$pos=0
        while($pos -lt $extra.Length){if($extra.Length-$pos -lt 4){throw 'Extra header truncated'};$tag=[BitConverter]::ToUInt16($extra,$pos);$len=[BitConverter]::ToUInt16($extra,$pos+2);$pos+=4;if($pos+$len -gt $extra.Length){throw 'Extra field truncated'};$hex=if($len){[Convert]::ToHexString($extra[$pos..($pos+$len-1)]).ToLowerInvariant()}else{''};$tags.Add(@{id=$tag;length=$len;hex=$hex});$pos+=$len}
        $entries.Add(@{name=$name;is_directory=$name.EndsWith('/');bytes=[long]$size;compressed_bytes=[long]$compressed;crc32=$crc.ToString('x8');flags=$flags;method=$method;local_header_offset=[long]$local;central_start=$start;central_end=$memory.Position;extra_fields=$tags.ToArray();comment_bytes=$cl;external_attributes=$external;dos_date=$date;dos_time=$time})
    }
    if($memory.Position -ne $data.Length){throw 'Unconsumed central bytes'}
}finally{$br.Dispose();$memory.Dispose()}
$request=Get-Content -LiteralPath (Join-Path $root 'docs/maintenance/2026-10-15/continuation-handoff-06/DEMO_MEMBER_REQUEST.json') -Raw|ConvertFrom-Json
$files=@($entries|Where-Object {-not $_.is_directory});$lookup=@{};foreach($e in $files){$lookup[$e.name]=$e}
$rows=foreach($member in $request.members){
    $name='demo_example_data/'+$member.path
    if(-not $lookup.ContainsKey($name)){throw ('Missing exact archive path '+$name)}
    $p=[IO.Path]::GetFullPath((Join-Path (Join-Path $root 'demo_example_data') $member.path))
    if(-not $p.StartsWith((Join-Path $root 'demo_example_data')+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)){throw 'Local path outside demo root'}
    $observed=[OdaLocalBytes]::Read($p);$entry=$lookup[$name]
    if([long]$observed[0] -ne $member.bytes -or $observed[2] -cne $member.SHA256){throw 'Current local byte identity changed'}
    @{local_path=$member.path;archive_path=$name;bytes=[long]$observed[0];sha256=$observed[2];local_crc32=$observed[1];archive_crc32=$entry.crc32;length_match=([long]$observed[0] -eq $entry.bytes);crc32_match=($observed[1] -ceq $entry.crc32)}
}
$unknown=@($files|Where-Object {$_.name -notin @($rows.archive_path)})
Save 'inventory.json' @{entries=$entries.ToArray();archive_files=$files.Count;archive_directories=$entries.Count-$files.Count;local_members=$rows;unmapped_archive_files=$unknown;all156_lengths_and_CRCs_match=(@($rows|Where-Object {-not $_.length_match -or -not $_.crc32_match}).Count -eq 0 -and $rows.Count -eq 156);CRC32_is_not_collision_resistant_authentication=$true;member_SHA256_in_standard_central_record=$false;reference_construction_authenticated=$false;point_coordinate_decodes=0;network_requests=0;utc=[DateTime]::UtcNow.ToString('o')}
Write-Output (@{archive_entries=$entries.Count;archive_files=$files.Count;local_members=$rows.Count;unmapped_files=$unknown.Count;crc_length_matches=@($rows|Where-Object {$_.length_match -and $_.crc32_match}).Count}|ConvertTo-Json -Compress)
