param(
    [string]$EngineRoot = 'F:\Games\UE_5.8',
    [string]$ArchiveDirectory
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$projectFile = Join-Path $projectRoot 'Ciberfantasma3D.uproject'
$runUat = Join-Path $EngineRoot 'Engine\Build\BatchFiles\RunUAT.bat'

if ([string]::IsNullOrWhiteSpace($ArchiveDirectory)) {
    $ArchiveDirectory = Join-Path $projectRoot 'Builds\Windows-Development'
}
elseif (-not [System.IO.Path]::IsPathRooted($ArchiveDirectory)) {
    $ArchiveDirectory = Join-Path $projectRoot $ArchiveDirectory
}
$ArchiveDirectory = [System.IO.Path]::GetFullPath($ArchiveDirectory)

foreach ($requiredPath in @($projectFile, $runUat)) {
    if (-not (Test-Path -LiteralPath $requiredPath)) {
        throw "Required path not found: $requiredPath"
    }
}

Write-Host "Packaging Windows development build to $ArchiveDirectory"
& $runUat BuildCookRun `
    "-project=$projectFile" `
    -nop4 `
    -unattended `
    -utf8output `
    -platform=Win64 `
    -target=Ciberfantasma3D `
    -clientconfig=Development `
    -build `
    -cook `
    "-map=/Game/Maps/Act01_Rooftops+/Game/Maps/Act02_DataCenter+/Game/Maps/Act03_ExecutiveCore+/Game/Maps/Act04_MemoryGardens+/Game/Maps/Act05_ConsensusFactory+/Game/Maps/Act06_SingleArchive+/Game/Maps/Act07_DeadIdeasAvenue+/Game/Maps/Act08_SilenceOffice+/Game/Maps/Act09_DirectorOffice" `
    -stage `
    -pak `
    -archive `
    "-archivedirectory=$ArchiveDirectory"

if ($LASTEXITCODE -ne 0) {
    throw "Windows packaging failed with exit code $LASTEXITCODE."
}

$executable = Get-ChildItem -LiteralPath $ArchiveDirectory -Filter 'Ciberfantasma3D.exe' -File -Recurse |
    Select-Object -First 1
if (-not $executable) {
    throw "Packaging completed but Ciberfantasma3D.exe was not found in $ArchiveDirectory."
}

Write-Host "Playable build: $($executable.FullName)"
