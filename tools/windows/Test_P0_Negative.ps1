#Requires -Version 5.1
# CI-only adversarial ZIP checks in RUNNER_TEMP, never on user's Adobe directories.
[CmdletBinding()]
param(
 [Parameter(Mandatory)][string]$ZipPath,
 [Parameter(Mandatory)][string]$InspectorPath,
 [Parameter(Mandatory)][string]$TempDirectory
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem
$original=[System.IO.Path]::GetFullPath($ZipPath)
$script=[System.IO.Path]::GetFullPath($InspectorPath)
if(-not [System.IO.File]::Exists($original)){throw 'P0_TEST_ZIP_MISSING'}
if(-not [System.IO.File]::Exists($script)){throw 'P0_TEST_INSPECTOR_MISSING'}
[void][System.IO.Directory]::CreateDirectory($TempDirectory)
$pilot='AI_JSON_Premiere_P0_Pilot'
$sourceName="$pilot/panel/app.js"
$manifestName="$pilot/P0_SHA256SUMS.txt"
function New-Variant([string]$Kind) {
 $out=Join-Path $TempDirectory ($Kind+'.zip')
 $source=[System.IO.Compression.ZipFile]::OpenRead($original)
 $dest=[System.IO.Compression.ZipFile]::Open($out,[System.IO.Compression.ZipArchiveMode]::Create)
 try {
  foreach($entry in $source.Entries) {
   $name=$entry.FullName
   if($Kind -eq 'missing' -and $name -eq $sourceName){continue}
   if($Kind -eq 'traversal' -and $name -eq $sourceName){$name="$pilot/../../outside.js"}
   if($Kind -eq 'unexpected' -and $name -eq $sourceName){$name="$pilot/unexpected.js"}
   $inputStream=$entry.Open()
   $buffer=New-Object System.IO.MemoryStream
   try {$inputStream.CopyTo($buffer);[byte[]]$data=$buffer.ToArray()}
   finally {$buffer.Dispose();$inputStream.Dispose()}
   if($Kind -eq 'tamper' -and $name -eq $sourceName){$data[0]=$data[0] -bxor 1}
   if($Kind -eq 'oversize' -and $name -eq $sourceName){$data=New-Object byte[] 524289}
   if($name -eq $manifestName) {
     if($Kind -eq 'duplicate-hash'){
       $lines=@([System.Text.Encoding]::ASCII.GetString($data).Trim().Split([char]10))
       $lines[1]=$lines[0]
       $data=[System.Text.Encoding]::ASCII.GetBytes((($lines -join [char]10)+[char]10))
     }
     if($Kind -eq 'missing-hash'){
       $lines=@([System.Text.Encoding]::ASCII.GetString($data).Trim().Split([char]10))
       $data=[System.Text.Encoding]::ASCII.GetBytes((($lines[0..7] -join [char]10)+[char]10))
     }
   }
   $outEntry=$dest.CreateEntry($name,[System.IO.Compression.CompressionLevel]::Optimal)
   $outEntry.ExternalAttributes=$entry.ExternalAttributes
   $outputStream=$outEntry.Open()
   try {$outputStream.Write($data,0,$data.Length)}
   finally {$outputStream.Dispose()}
  }
  if($Kind -eq 'duplicate-entry') {
   $duplicate=$dest.CreateEntry($sourceName,[System.IO.Compression.CompressionLevel]::Optimal)
   $stream=$duplicate.Open()
   try {$stream.WriteByte([byte]65)} finally {$stream.Dispose()}
  }
 } finally {$dest.Dispose();$source.Dispose()}
 return $out
}
function Assert-Refused([string]$Kind,[string]$ExpectedCode) {
 $broken=New-Variant $Kind
 try {
   & $script -Mode Inspect -ZipPath $broken | Out-Null
   throw "P0_NEGATIVE_UNEXPECTED_PASS: $Kind"
 } catch {
   if($_.Exception.Message -notmatch [regex]::Escape($ExpectedCode)){throw}
 }
 $target=Join-Path $TempDirectory ("stage-"+$Kind)
 try {
  & $script -Mode Stage -ConfirmStage -ZipPath $broken -ExtensionDirectory $target | Out-Null
  throw "P0_NEGATIVE_STAGE_UNEXPECTED_PASS: $Kind"
 } catch {
  if($_.Exception.Message -notmatch [regex]::Escape($ExpectedCode)){throw}
 }
 if([System.IO.Directory]::Exists($target)){throw "P0_NEGATIVE_CREATED_STAGE_DIRECTORY: $Kind"}
 Write-Output ("P0_NEGATIVE_"+$Kind+"=PASS_REJECTED")
}
$good=& $script -Mode Inspect -ZipPath $original
if($good -notcontains 'P0_INSPECT=PASS'){throw 'P0_VALID_PACKAGE_REJECTED'}
if($good -notcontains 'P0_PROVENANCE=SELF_INTEGRITY_ONLY'){throw 'P0_SELF_INTEGRITY_LABEL_MISSING'}
$actual=(Get-FileHash -LiteralPath $original -Algorithm SHA256).Hash
$pinned=& $script -Mode Inspect -ZipPath $original -ExpectedZipSha256 $actual
if($pinned -notcontains 'P0_PROVENANCE=MATCHED_EXTERNAL_SHA256'){throw 'P0_EXTERNAL_HASH_CHECK_MISSING'}
try {
 & $script -Mode Inspect -ZipPath $original -ExpectedZipSha256 ('0' * 64) | Out-Null
 throw 'P0_WRONG_EXTERNAL_HASH_ACCEPTED'
} catch {
 if($_.Exception.Message -notmatch 'P0_ARCHIVE_SHA_MISMATCH'){throw}
}
try {
 & $script -Mode Inspect -ZipPath $original -ExpectedZipSha256 'abc' | Out-Null
 throw 'P0_BAD_EXTERNAL_HASH_ACCEPTED'
} catch {
 if($_.Exception.Message -notmatch 'P0_EXPECTED_HASH_INVALID'){throw}
}
Assert-Refused 'tamper' 'P0_SHA_MISMATCH'
Assert-Refused 'duplicate-hash' 'P0_SHA_MANIFEST_INVALID'
Assert-Refused 'missing-hash' 'P0_SHA_MANIFEST_INVALID'
Assert-Refused 'traversal' 'P0_UNSAFE_ENTRY'
Assert-Refused 'unexpected' 'P0_UNSAFE_ENTRY'
Assert-Refused 'oversize' 'P0_UNSAFE_ENTRY'
Assert-Refused 'missing' 'P0_UNEXPECTED_ENTRIES'
Assert-Refused 'duplicate-entry' 'P0_UNEXPECTED_ENTRIES'
Write-Output 'P0_NEGATIVE_SUITE=PASS'
