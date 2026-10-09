#Requires -Version 5.1
<#
 STEP03 P0 test-only archive inspector/stager, no Premiere automation.
 Default Inspect is read-only; Stage requires -ConfirmStage.
 NO registry modification, developer-mode change, auto-start, or network activity.
#>
[CmdletBinding()]
param(
    [ValidateSet('Inspect','Stage','Evidence')][string]$Mode = 'Inspect',
    [string]$ZipPath = (Join-Path $PSScriptRoot 'AI_JSON_Premiere_P0_Pilot_TEST_ONLY.zip'),
    [string]$ExtensionDirectory = (Join-Path $env:APPDATA 'Adobe\CEP\extensions'),
    [switch]$ConfirmStage,
    [string]$ExpectedZipSha256 = '',
    [string]$EvidenceDirectory = (Join-Path (Get-Location).Path 'P0_Evidence')
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$PilotFolder = 'AI_JSON_Premiere_P0_Pilot'
$Files = @(
    'CSXS/manifest.xml','panel/index.html','panel/styles.css',
    'panel/bridge.js','panel/helper_bridge.js','panel/validation_bridge.js',
    'panel/validation_ui.js','panel/app.js',
    'host/step03.jsx','helper/handshake.py','helper/validate_request.py',
    'core/__init__.py','core/contracts.py','core/media.py',
    'core/validate_cli.py','core/direction_registry.json',
    'P0_TEST_ONLY_README.txt','P0_SHA256SUMS.txt'
)
$Allowed = @{}
foreach ($file in $Files) { $Allowed["$PilotFolder/$file"] = $true }

if (-not [System.IO.File]::Exists($ZipPath)) {
    throw "P0_ZIP_NOT_FOUND: archive must be beside this script or supplied via -ZipPath."
}
# Optional independently sourced SHA-256 authenticates archive bytes; internal sums prove self-consistency only.
if ($ExpectedZipSha256 -and $ExpectedZipSha256 -cnotmatch '^[a-fA-F0-9]{64}$') {
    throw 'P0_EXPECTED_HASH_INVALID: 64 hexadecimal SHA-256 characters required.'
}
$zipDigest = (Get-FileHash -LiteralPath $ZipPath -Algorithm SHA256).Hash.ToLowerInvariant()
if ($ExpectedZipSha256 -and $zipDigest -cne $ExpectedZipSha256.ToLowerInvariant()) {
    throw 'P0_ARCHIVE_SHA_MISMATCH: ZIP differs from independently supplied SHA-256.'
}
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem
$archive = [System.IO.Compression.ZipFile]::OpenRead([System.IO.Path]::GetFullPath($ZipPath))
$payloads = @{}
try {
    if ($archive.Entries.Count -ne $Files.Count) {
        throw "P0_UNEXPECTED_ENTRIES: expected exactly 18 files."
    }
    foreach ($entry in $archive.Entries) {
        $name = $entry.FullName
        if (-not $Allowed.ContainsKey($name) -or $payloads.ContainsKey($name) -or
            $name.Contains('\') -or $name.StartsWith('/') -or
            $name.Contains('../') -or $entry.Length -gt 524288) {
            throw "P0_UNSAFE_ENTRY: unexpected/duplicate/oversized ZIP item."
        }
        # Reject UNIX symbolic links. All generated runtime files must be regular files.
        $modeBits = ([int]$entry.ExternalAttributes -shr 16) -band 61440
        if ($modeBits -eq 40960) { throw "P0_UNSAFE_ENTRY: symbolic link refused." }
        $stream = $entry.Open()
        $memory = New-Object System.IO.MemoryStream
        try {
            $stream.CopyTo($memory)
            $payloads[$name] = $memory.ToArray()
        } finally {
            $memory.Dispose()
            $stream.Dispose()
        }
        if ($payloads[$name].Length -ne $entry.Length) {
            throw "P0_UNSAFE_ENTRY: uncompressed length mismatch."
        }
    }
} finally {
    $archive.Dispose()
}

$sumName = "$PilotFolder/P0_SHA256SUMS.txt"
$manifestText = [System.Text.Encoding]::UTF8.GetString($payloads[$sumName])
$sumRows = @($manifestText.Trim().Split([char]10) | Where-Object { $_.Trim().Length -gt 0 })
if ($sumRows.Count -ne 17) { throw "P0_SHA_MANIFEST_INVALID: expected 9 hash records." }
$seen = @{}
$sha = [System.Security.Cryptography.SHA256]::Create()
try {
    foreach ($line in $sumRows) {
        $match = [regex]::Match($line.TrimEnd([char]13),'^([a-f0-9]{64})  ([A-Za-z0-9_./-]+)$')
        if (-not $match.Success) { throw "P0_SHA_MANIFEST_INVALID: malformed record." }
        $name = "$PilotFolder/$($match.Groups[2].Value)"
        if (-not $payloads.ContainsKey($name) -or $name -eq $sumName -or
            $seen.ContainsKey($name)) {
            throw "P0_SHA_MANIFEST_INVALID: duplicate or unlisted source."
        }
        $seen[$name] = $true
        $computed = [System.BitConverter]::ToString(
            $sha.ComputeHash([byte[]]$payloads[$name])).Replace('-','').ToLowerInvariant()
        if ($computed -cne $match.Groups[1].Value) {
            throw "P0_SHA_MISMATCH: one or more pilot files were modified."
        }
    }
} finally { $sha.Dispose() }
if ($seen.Count -ne 17) { throw "P0_SHA_MANIFEST_INVALID: missing records." }
Write-Output ('P0_ZIP_SHA256=' + $zipDigest)
Write-Output ('P0_PROVENANCE=' + $(if ($ExpectedZipSha256) {'MATCHED_EXTERNAL_SHA256'} else {'SELF_INTEGRITY_ONLY'}))
Write-Output 'P0_INSPECT=PASS'
Write-Output 'P0_FILES=18'
Write-Output 'P0_SHA256_ENTRIES=17'
Write-Output 'P0_G3=NOT_TESTED_IN_PREMIERE'

if ($Mode -eq 'Stage') {
    if (-not $ConfirmStage) {
        throw "P0_STAGE_REQUIRES_EXPLICIT_CONFIRMATION: add -ConfirmStage deliberately."
    }
    $root = [System.IO.Path]::GetFullPath($ExtensionDirectory)
    $target = Join-Path $root $PilotFolder
    if ([System.IO.Directory]::Exists($target) -or [System.IO.File]::Exists($target)) {
        throw "P0_TARGET_ALREADY_EXISTS: refusing to overwrite previous CEP extension."
    }
    [void][System.IO.Directory]::CreateDirectory($root)
    $temporary = Join-Path $root ('.p0-stage-' + [guid]::NewGuid().ToString('N'))
    try {
        [void][System.IO.Directory]::CreateDirectory($temporary)
        foreach ($file in $Files) {
            $dest = Join-Path $temporary ($file.Replace('/', [System.IO.Path]::DirectorySeparatorChar))
            [void][System.IO.Directory]::CreateDirectory([System.IO.Path]::GetDirectoryName($dest))
            [System.IO.File]::WriteAllBytes($dest, [byte[]]$payloads["$PilotFolder/$file"])
        }
        [System.IO.Directory]::Move($temporary,$target)
    } finally {
        if ([System.IO.Directory]::Exists($temporary)) {
            [System.IO.Directory]::Delete($temporary,$true)
        }
    }
    Write-Output 'P0_STAGE=PASS_USER_APPROVED'
    Write-Output 'P0_NOTICE=NO_REGISTRY_CHANGES_NO_PREMIERE_LAUNCH'
    Write-Output ('P0_STAGE_TARGET=' + $target)
} elseif ($Mode -eq 'Evidence') {
    # This is an EMPTY template only; never invent or scrape real host results.
    [void][System.IO.Directory]::CreateDirectory($EvidenceDirectory)
    $report = Join-Path $EvidenceDirectory 'G3_HOST_TEST_TEMPLATE.txt'
    if ([System.IO.File]::Exists($report)) { throw 'P0_EVIDENCE_ALREADY_EXISTS: no overwrite.' }
    $template = @'
G3 REAL PREMIERE HOST EVIDENCE — PENDING, not a PASS report
This template contains no verified Premiere results. Tester completes fields.
Tested git commit:
Windows 11 build:
Premiere Pro 2024 version (24.x):
CEP/CSXS version:
Pilot zip SHA256:
Extension menu appeared? (PASS/FAIL):
Dock/resize/focus/reopen (PASS/FAIL):
PERIKSA HOST actual response:
PERIKSA HELPER actual response (or SKIPPED):
Import/preflight/assembly remain disabled?:
Timeline/project before & after unchanged?:
Real screenshot file names and log locations (redact private data):
Observed bugs:
Tester name or alias and date:
Gate decision: NOT_VERIFIED_UNTIL_ASTRA_REVIEW
'@
    [System.IO.File]::WriteAllText($report,$template,[System.Text.Encoding]::UTF8)
    Write-Output ('P0_EVIDENCE_TEMPLATE_CREATED=' + $report)
}
