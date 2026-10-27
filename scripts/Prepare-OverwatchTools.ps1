param([string]$ToolRoot = (Join-Path $PSScriptRoot '..\.tools'))
$ErrorActionPreference = 'Stop'
$owRevision = '546efa19516d7df7ba138802d221c73ad886df28'
$tactRevision = '9b333b84211a4b95928e01be303b5ed27729c0aa'
$decoderSha = '692D45070852A35C1FA42726AA3C9DE528E44EEC925D37D99B1074256B99A229'
$root = [System.IO.Path]::GetFullPath($ToolRoot)
[System.IO.Directory]::CreateDirectory($root) | Out-Null
$repo = Join-Path $root 'owlib-source'
function Invoke-CheckedGit {
    param([string[]]$GitArguments)
    & git @GitArguments
    if ($LASTEXITCODE -ne 0) { throw ('Git failed: ' + ($GitArguments -join ' ')) }
}
if (-not (Test-Path -LiteralPath $repo)) {
    Invoke-CheckedGit -GitArguments @('clone','https://github.com/overtools/OWLib.git',$repo)
    Invoke-CheckedGit -GitArguments @('-C',$repo,'checkout','--detach',$owRevision)
    Invoke-CheckedGit -GitArguments @('-C',$repo,'submodule','update','--init','--recursive')
} elseif (-not (Test-Path -LiteralPath (Join-Path $repo '.git'))) {
    throw "Tool directory already exists without the expected Git repository: $repo"
}
$actualOw = (& git -C $repo rev-parse HEAD).Trim()
$actualRemote = (& git -C $repo remote get-url origin).Trim().TrimEnd('/')
if ($actualOw -ne $owRevision -or $actualRemote -notmatch '^https://github.com/overtools/OWLib(?:\.git)?$') {
    throw 'Existing OWLib checkout differs from the pinned source. Choose a new -ToolRoot; no checkout was reset.'
}
$overlaySource = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\tools\owlib\NuvPinnedSfx.cs'))
$overlayTarget = Join-Path $repo 'DataTool\ToolLogic\Extract\NuvPinnedSfx.cs'
$allowedPaths = @('DataTool/Program.cs','TACTLib','DataTool/ToolLogic/Extract/NuvPinnedSfx.cs')
foreach ($changed in (& git -C $repo status --porcelain --untracked-files=all)) {
    if ($changed.Substring(3) -notin $allowedPaths) { throw ('Unexpected OWLib source edit: ' + $changed) }
}
if ((Test-Path -LiteralPath $overlayTarget) -and ((Get-FileHash -LiteralPath $overlayTarget).Hash -ne (Get-FileHash -LiteralPath $overlaySource).Hash)) {
    throw 'Existing NUV SFX extension differs from this repository. Preserve your edits and choose a new -ToolRoot.'
}
$tact = Join-Path $repo 'TACTLib'
if ((& git -C $tact status --porcelain --untracked-files=all).Length -ne 0) { throw 'TACTLib has unexpected source edits.' }
$actualTact = (& git -C $tact rev-parse HEAD).Trim()
if ($actualTact -ne $tactRevision) {
    if ((& git -C $tact status --porcelain).Length -ne 0) { throw 'TACTLib has local edits; choose a new -ToolRoot.' }
    Invoke-CheckedGit -GitArguments @('-C',$tact,'fetch','origin','refs/pull/40/head')
    $fetchedRevision = (& git -C $tact rev-parse FETCH_HEAD).Trim()
    if ($fetchedRevision -ne $tactRevision) { throw 'The upstream PR revision changed; source needs review.' }
    Invoke-CheckedGit -GitArguments @('-C',$tact,'checkout','--detach',$tactRevision)
}
$revorb = Join-Path $repo 'revorbstd'
$expectedRevorb = ((& git -C $repo ls-tree HEAD revorbstd) -split '\s+')[2]
if ((& git -C $revorb rev-parse HEAD).Trim() -ne $expectedRevorb -or (& git -C $revorb status --porcelain --untracked-files=all).Length -ne 0) {
    throw 'revorbstd differs from the pinned clean source.'
}
$program = Join-Path $repo 'DataTool\Program.cs'
$code = [System.IO.File]::ReadAllText($program)
$original = 'RemoteKeyringUrl = "https://raw.githubusercontent.com/overtools/OWLib/master/TankLib/Overwatch.keyring"'
$offline = 'RemoteKeyringUrl = online ? "https://raw.githubusercontent.com/overtools/OWLib/master/TankLib/Overwatch.keyring" : null'
$upstreamCode = ((& git -C $repo show 'HEAD:DataTool/Program.cs') -join "`n").TrimStart([char]0xFEFF).TrimEnd("`r","`n")
$normalizedCode = $code.Replace("`r`n","`n").TrimStart([char]0xFEFF).TrimEnd("`r","`n")
if ($normalizedCode -ne $upstreamCode -and $normalizedCode -ne $upstreamCode.Replace($original,$offline)) {
    throw 'Program.cs contains edits beyond the exact offline-keyring change.'
}
if ($code.Contains($original)) {
    $code = $code.Replace($original,$offline)
    [System.IO.File]::WriteAllText($program,$code,(New-Object System.Text.UTF8Encoding($false)))
} elseif (-not $code.Contains($offline)) { throw 'Unexpected keyring code; source needs review.' }
Copy-Item -LiteralPath $overlaySource -Destination $overlayTarget
Push-Location $repo
try {
    & dotnet build DataTool/DataTool.csproj -c Release -v quiet
    if ($LASTEXITCODE -ne 0) { throw 'DataTool build failed. Requires the .NET 10 SDK.' }
} finally { Pop-Location }
$archive = Join-Path $root 'vgmstream-r2168.zip'
if (-not (Test-Path -LiteralPath $archive)) {
    Invoke-WebRequest -Uri 'https://github.com/vgmstream/vgmstream/releases/download/r2168/vgmstream-win64.zip' -OutFile $archive
}
if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash -ne $decoderSha) { throw 'vgmstream archive SHA-256 mismatch.' }
$decoderRoot = Join-Path $root 'vgmstream'
Expand-Archive -LiteralPath $archive -DestinationPath $decoderRoot -Force
$metadata = [ordered]@{
    overwatch_build = '2.25.0.1.154504N'
    owlib_revision = $owRevision
    tactlib_revision = $tactRevision
    tactlib_source = 'https://github.com/overtools/TACTLib/pull/40'
    tactlib_upstream_merged = $false
    offline_keyring_patch = $true
    nuv_sfx_extension_sha256 = (Get-FileHash -LiteralPath $overlaySource -Algorithm SHA256).Hash
    datatool_dll_sha256 = (Get-FileHash -LiteralPath (Join-Path $repo 'DataTool\bin\Release\net10.0\DataTool.dll') -Algorithm SHA256).Hash
    tactlib_dll_sha256 = (Get-FileHash -LiteralPath (Join-Path $repo 'DataTool\bin\Release\net10.0\TACTLib.dll') -Algorithm SHA256).Hash
    vgmstream_release = 'r2168'
    vgmstream_archive_sha256 = $decoderSha
}
$metadata | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $root 'overwatch-tools.json') -Encoding UTF8
Write-Output ('DataTool: ' + (Join-Path $repo 'DataTool\bin\Release\net10.0\DataTool.exe'))
Write-Output ('Decoder:  ' + (Join-Path $decoderRoot 'vgmstream-cli.exe'))
