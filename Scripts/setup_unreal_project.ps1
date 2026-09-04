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
$campaignAuditScript = Join-Path $projectRoot 'Content\Python\audit_campaign.py'
$levelExportScript = Join-Path $projectRoot 'Scripts\export_canvas_levels.mjs'
$importScript = Join-Path $projectRoot 'Content\Python\import_chibi_models.py'
$vfxScript = Join-Path $projectRoot 'Content\Python\create_vfx_assets.py'
$vfxAuditScript = Join-Path $projectRoot 'Content\Python\audit_vfx_assets.py'
$worldArtScript = Join-Path $projectRoot 'Content\Python\upgrade_world_art.py'
$worldArtAuditScript = Join-Path $projectRoot 'Content\Python\audit_world_art.py'
$modelScript = Join-Path $projectRoot 'Scripts\create_chibi_models.py'
$animationAuditScript = Join-Path $projectRoot 'Scripts\audit_hero_animation_bounds.py'
$heroAuditScript = Join-Path $projectRoot 'Content\Python\audit_hero_assets.py'

foreach ($requiredPath in @(
    $projectFile, $buildBat, $editorCmd, $pythonScript, $campaignAuditScript,
    $importScript, $vfxScript, $vfxAuditScript, $worldArtScript,
    $worldArtAuditScript, $modelScript, $animationAuditScript,
    $heroAuditScript, $levelExportScript, $BlenderExe
)) {
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
& $BlenderExe --background --python-exit-code 1 --python $modelScript
if ($LASTEXITCODE -ne 0) {
    throw "Blender model generation failed with exit code $LASTEXITCODE."
}

Write-Host 'Auditing complete animation tracks and 2.5D pose bounds...'
& $BlenderExe --background (Join-Path $projectRoot 'SourceAssets\Blender\CF_Character_Workfile.blend') --python-exit-code 1 --python $animationAuditScript
if ($LASTEXITCODE -ne 0) {
    throw "Hero animation bounds audit failed with exit code $LASTEXITCODE."
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

Write-Host 'Auditing imported hero, animations and presentation materials...'
& $editorCmd $projectFile -run=pythonscript "-script=$heroAuditScript" -unattended -nop4 -nosplash
if ($LASTEXITCODE -ne 0) {
    throw "Imported hero audit failed with exit code $LASTEXITCODE."
}

Write-Host 'Generating the nine-act campaign...'
& $editorCmd $projectFile -run=pythonscript "-script=$pythonScript" -unattended -nop4 -nosplash
if ($LASTEXITCODE -ne 0) {
    throw "Campaign generation failed with exit code $LASTEXITCODE."
}

Write-Host 'Applying the World Art V3 pass after campaign reconstruction...'
& $editorCmd $projectFile -run=pythonscript "-script=$worldArtScript" -unattended -nop4 -nosplash
if ($LASTEXITCODE -ne 0) {
    throw "World Art V3 upgrade failed with exit code $LASTEXITCODE."
}

Write-Host 'Auditing campaign structure and World Art V3...'
& $editorCmd $projectFile -run=pythonscript "-script=$campaignAuditScript" -unattended -nop4 -nosplash
if ($LASTEXITCODE -ne 0) {
    throw "Campaign audit failed with exit code $LASTEXITCODE."
}
& $editorCmd $projectFile -run=pythonscript "-script=$worldArtAuditScript" -unattended -nop4 -nosplash
if ($LASTEXITCODE -ne 0) {
    throw "World Art V3 audit failed with exit code $LASTEXITCODE."
}

Write-Host 'Generating runtime Niagara combat effects...'
& $editorCmd $projectFile -run=pythonscript "-script=$vfxScript" -unattended -nop4 -nosplash
if ($LASTEXITCODE -ne 0) {
    throw "Niagara VFX generation failed with exit code $LASTEXITCODE."
}

Write-Host 'Auditing runtime Niagara effects...'
& $editorCmd $projectFile -run=pythonscript "-script=$vfxAuditScript" -unattended -nop4 -nosplash
if ($LASTEXITCODE -ne 0) {
    throw "Niagara VFX audit failed with exit code $LASTEXITCODE."
}

Write-Host 'Unreal project compiled; hero, campaign, World Art V3 and runtime VFX audited.'
if ($OpenEditor) {
    Start-Process -FilePath $editor -ArgumentList @($projectFile)
}
