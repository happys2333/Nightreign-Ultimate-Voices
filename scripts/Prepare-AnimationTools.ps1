param([string]$ToolRoot = (Join-Path $PSScriptRoot '..\.tools'))
$ErrorActionPreference = 'Stop'
$revision = '9e1c36f54962f80c143e3c1fe8a709204aefacf9'
$remote = 'https://github.com/soulsmods/SoulsFormatsNEXT.git'
$root = [System.IO.Path]::GetFullPath($ToolRoot)
$workspace = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
[System.IO.Directory]::CreateDirectory($root) | Out-Null
$repo = Join-Path $root 'soulsformats'

function Invoke-CheckedGit {
    param([string[]]$GitArguments)
    $result = @(& git @GitArguments 2>&1)
    if ($LASTEXITCODE -ne 0) { throw ('Git failed: ' + ($GitArguments -join ' ')) }
    return $result
}

function Get-Sha256File {
    param([string]$Path)
    $stream = [System.IO.File]::OpenRead($Path)
    $hasher = [System.Security.Cryptography.SHA256]::Create()
    try { return [BitConverter]::ToString($hasher.ComputeHash($stream)).Replace('-', '').ToLowerInvariant() }
    finally { $hasher.Dispose(); $stream.Dispose() }
}

if (-not (Test-Path -LiteralPath $repo)) {
    Invoke-CheckedGit -GitArguments @('clone', '--quiet', $remote, $repo) | Out-Null
    Invoke-CheckedGit -GitArguments @('-C', $repo, 'checkout', '--quiet', '--detach', $revision) | Out-Null
} elseif (-not (Test-Path -LiteralPath (Join-Path $repo '.git'))) {
    throw "Tool directory exists without the expected Git repository: $repo"
}
$actualRevision = (@(Invoke-CheckedGit -GitArguments @('-C', $repo, 'rev-parse', 'HEAD')))[0].Trim()
$actualRemote = (@(Invoke-CheckedGit -GitArguments @('-C', $repo, 'remote', 'get-url', 'origin')))[0].Trim().TrimEnd('/')
$changes = @(Invoke-CheckedGit -GitArguments @('-C', $repo, 'status', '--porcelain', '--untracked-files=all'))
if ($actualRevision -ne $revision -or $actualRemote -notmatch '^https://github.com/soulsmods/SoulsFormatsNEXT(?:\.git)?$' -or $changes.Count -ne 0) {
    throw 'SoulsFormats checkout differs from the pinned clean source. Preserve local edits and choose a new -ToolRoot; no checkout was reset.'
}
$project = Join-Path $workspace 'tools\tae\Nuv.TaePatcher.csproj'
$libraryProject = Join-Path $repo 'SoulsFormats\SoulsFormats.csproj'
$publish = Join-Path $root 'tae-patcher'
& dotnet publish $project -c Release -o $publish "-p:SoulsFormatsProject=$libraryProject" --nologo -v quiet
if ($LASTEXITCODE -ne 0) { throw 'TAE helper build failed. Install a .NET SDK supporting net9.0.' }

$sourceFiles = [ordered]@{}
$manifest = ''
foreach ($relative in @('tools/tae/Nuv.TaePatcher.csproj', 'tools/tae/Program.cs')) {
    $digest = Get-Sha256File -Path (Join-Path $workspace $relative)
    $sourceFiles[$relative] = $digest
    $manifest += $relative + ':' + $digest + "`n"
}
$sha = [System.Security.Cryptography.SHA256]::Create()
try { $sourceDigest = [BitConverter]::ToString($sha.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($manifest))).Replace('-', '').ToLowerInvariant() }
finally { $sha.Dispose() }
$metadata = [ordered]@{
    schema_version = 1
    helper_format_version = 1
    soulsformats_revision = $revision
    soulsformats_remote = $remote
    helper_source_files = $sourceFiles
    helper_source_sha256 = $sourceDigest
    helper_dll_sha256 = Get-Sha256File -Path (Join-Path $publish 'Nuv.TaePatcher.dll')
    soulsformats_dll_sha256 = Get-Sha256File -Path (Join-Path $publish 'SoulsFormats.dll')
}
[System.IO.File]::WriteAllText((Join-Path $root 'animation-tools.json'), ($metadata | ConvertTo-Json -Depth 4), [System.Text.UTF8Encoding]::new($false))
Write-Output ('TAE helper: ' + (Join-Path $publish 'Nuv.TaePatcher.dll'))
Write-Output ('Metadata:   ' + (Join-Path $root 'animation-tools.json'))
