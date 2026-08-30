param(
    [string]$EngineRoot = 'F:\Games\UE_5.8',
    [string]$BlenderExe = 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe',
    [switch]$OpenEditor
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$projectFile = Join-Path $projectRoot 'Ciberfantasma3D.uproject'
$buildBat = Join-Path $EngineRoot 'Engine\Build\BatchFiles\Build.bat'
$editorCmd = Join-Path $EngineRoot 'Engine\Binaries\Win64\UnrealEditor-Cmd.exe'
$editor = Join-Path $EngineRoot 'Engine\Binaries\Win64\UnrealEditor.exe'
$pythonScript = Join-Path $projectRoot 'Content\Python\build_campaign.py'
$levelExportScript = Join-Path $projectRoot 'Scripts\export_canvas_levels.mjs'
$importScript = Join-Path $projectRoot 'Content\Python\import_chibi_models.py'
$vfxScript = Join-Path $projectRoot 'Content\Python\create_vfx_assets.py'
$modelScript = Join-Path $projectRoot 'Scripts\create_chibi_models.py'

foreach ($requiredPath in @($projectFile, $buildBat, $editorCmd, $pythonScript, $importScript, $vfxScript, $modelScript, $levelExportScript, $BlenderExe)) {
    if (-not (Test-Path -LiteralPath $requiredPath)) {
        throw "Required path not found: $requiredPath"
    }
}

Write-Host 'Exporting the nine Canvas acts to campaign data...'
& node $levelExportScript
if ($LASTEXITCODE -ne 0) {
    throw "Canvas level export failed with exit code $LASTEXITCODE."
}

Write-Host 'Generating chibi character and enemy models in Blender...'
& $BlenderExe --background --python $modelScript
if ($LASTEXITCODE -ne 0) {
    throw "Blender model generation failed with exit code $LASTEXITCODE."
}

Write-Host 'Compiling Ciberfantasma3DEditor...'
& $buildBat Ciberfantasma3DEditor Win64 Development "-Project=$projectFile" -WaitMutex
if ($LASTEXITCODE -ne 0) {
    throw "Unreal compilation failed with exit code $LASTEXITCODE."
}

Write-Host 'Importing chibi meshes and PBR materials...'
& $editorCmd $projectFile -run=pythonscript "-script=$importScript" -unattended -nop4 -nosplash
if ($LASTEXITCODE -ne 0) {
    throw "Chibi asset import failed with exit code $LASTEXITCODE."
}

Write-Host 'Generating the nine-act campaign...'
& $editorCmd $projectFile -run=pythonscript "-script=$pythonScript" -unattended -nop4 -nosplash
if ($LASTEXITCODE -ne 0) {
    throw "Campaign generation failed with exit code $LASTEXITCODE."
}

Write-Host 'Generating runtime Niagara combat effects...'
& $editorCmd $projectFile -run=pythonscript "-script=$vfxScript" -unattended -nop4 -nosplash
if ($LASTEXITCODE -ne 0) {
    throw "Niagara VFX generation failed with exit code $LASTEXITCODE."
}

Write-Host 'Unreal project compiled; campaign and runtime VFX generated.'
if ($OpenEditor) {
    Start-Process -FilePath $editor -ArgumentList @($projectFile)
}
