param([string]$EngineRoot = 'F:\Games\UE_5.8')

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$projectFile = Join-Path $projectRoot 'Ciberfantasma3D.uproject'
$editor = Join-Path $EngineRoot 'Engine\Binaries\Win64\UnrealEditor.exe'

if (-not (Test-Path -LiteralPath $editor)) {
    throw "Unreal Editor was not found at $editor"
}
Start-Process -FilePath $editor -ArgumentList @($projectFile)
