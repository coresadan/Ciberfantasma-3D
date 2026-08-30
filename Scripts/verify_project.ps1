$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $PSScriptRoot
$mapNames = @(
    'Act01_Rooftops',
    'Act02_DataCenter',
    'Act03_ExecutiveCore',
    'Act04_MemoryGardens',
    'Act05_ConsensusFactory',
    'Act06_SingleArchive',
    'Act07_DeadIdeasAvenue',
    'Act08_SilenceOffice',
    'Act09_DirectorOffice'
)

$requiredFiles = @(
    'Ciberfantasma3D.uproject',
    'Config\DefaultEngine.ini',
    'Config\DefaultGame.ini',
    'Config\DefaultInput.ini',
    'Design\campaign_levels.json',
    'Scripts\export_canvas_levels.mjs',
    'Content\Python\build_campaign.py',
    'Content\Python\audit_campaign.py',
    'Content\Python\audit_hero_assets.py',
    'Content\Python\audit_vfx_assets.py',
    'Content\Python\create_vfx_assets.py',
    'Content\Python\import_chibi_models.py',
    'SourceAssets\FBX\SK_Ciberfantasma_Chibi_Pro.fbx',
    'SourceAssets\FBX\A_Ciberfantasma_Pro_Idle.fbx',
    'SourceAssets\FBX\A_Ciberfantasma_Pro_Run.fbx',
    'SourceAssets\FBX\A_Ciberfantasma_Pro_JumpStart.fbx',
    'SourceAssets\FBX\A_Ciberfantasma_Pro_JumpRise.fbx',
    'SourceAssets\FBX\A_Ciberfantasma_Pro_JumpFall.fbx',
    'SourceAssets\FBX\A_Ciberfantasma_Pro_Land.fbx',
    'SourceAssets\FBX\A_Ciberfantasma_Pro_Crouch.fbx',
    'SourceAssets\FBX\A_Ciberfantasma_Pro_Fire.fbx',
    'SourceAssets\FBX\A_Ciberfantasma_Pro_Shield.fbx',
    'SourceAssets\FBX\A_Ciberfantasma_Pro_Hit.fbx',
    'SourceAssets\FBX\SM_LicenseWarden_Chibi.fbx',
    'SourceAssets\FBX\SM_PanopticonDrone_Chibi.fbx',
    'SourceAssets\FBX\SM_BotGround_Chibi.fbx',
    'SourceAssets\FBX\SM_Crawler_Chibi.fbx',
    'SourceAssets\FBX\SM_Harvester_Chibi.fbx',
    'SourceAssets\FBX\SM_Enforcer_Chibi.fbx',
    'SourceAssets\FBX\SM_Auditor_Chibi.fbx',
    'SourceAssets\FBX\SM_CEO9000_Chibi.fbx',
    'SourceAssets\FBX\SM_Director_Chibi.fbx',
    'Content\Art\Characters\SK_Ciberfantasma_Chibi_Pro.uasset',
    'Content\Art\Characters\Animations\A_Ciberfantasma_Pro_Idle.uasset',
    'Content\Art\Characters\Animations\A_Ciberfantasma_Pro_Run.uasset',
    'Content\Art\Characters\Animations\A_Ciberfantasma_Pro_JumpStart.uasset',
    'Content\Art\Characters\Animations\A_Ciberfantasma_Pro_JumpRise.uasset',
    'Content\Art\Characters\Animations\A_Ciberfantasma_Pro_JumpFall.uasset',
    'Content\Art\Characters\Animations\A_Ciberfantasma_Pro_Land.uasset',
    'Content\Art\Characters\Animations\A_Ciberfantasma_Pro_Crouch.uasset',
    'Content\Art\Characters\Animations\A_Ciberfantasma_Pro_Fire.uasset',
    'Content\Art\Characters\Animations\A_Ciberfantasma_Pro_Shield.uasset',
    'Content\Art\Characters\Animations\A_Ciberfantasma_Pro_Hit.uasset',
    'Content\Art\Enemies\SM_LicenseWarden_Chibi.uasset',
    'Content\Art\Enemies\SM_PanopticonDrone_Chibi.uasset',
    'Content\Art\Enemies\SM_BotGround_Chibi.uasset',
    'Content\Art\Enemies\SM_Crawler_Chibi.uasset',
    'Content\Art\Enemies\SM_Harvester_Chibi.uasset',
    'Content\Art\Enemies\SM_Enforcer_Chibi.uasset',
    'Content\Art\Enemies\SM_Auditor_Chibi.uasset',
    'Content\Art\Enemies\SM_CEO9000_Chibi.uasset',
    'Content\Art\Enemies\SM_Director_Chibi.uasset',
    'Content\Art\VFX\NS_PulseImpact_Runtime.uasset',
    'Content\Art\VFX\NS_EnemyDeath_Runtime.uasset',
    'Content\Art\VFX\NS_MuzzleFlash_Runtime.uasset',
    'Content\Art\VFX\NS_ShieldAbsorb_Runtime.uasset',
    'Content\Art\VFX\NS_BossExplosion_Runtime.uasset',
    'Source\Ciberfantasma3D\CFGameInstance.cpp',
    'Source\Ciberfantasma3D\CFGameState.cpp',
    'Source\Ciberfantasma3D\CFHUD.cpp',
    'Source\Ciberfantasma3D\CFPlayerCharacter.cpp',
    'Source\Ciberfantasma3D\CFPulseProjectile.cpp',
    'Source\Ciberfantasma3D\CFEnemyProjectile.cpp',
    'Source\Ciberfantasma3D\CFPatrolEnemy.cpp',
    'Source\Ciberfantasma3D\CFShard.cpp',
    'Source\Ciberfantasma3D\CFTerminal.cpp',
    'Source\Ciberfantasma3D\CFHazard.cpp',
    'Source\Ciberfantasma3D\CFMovingPlatform.cpp',
    'Source\Ciberfantasma3D\CFExitPortal.cpp',
    'Docs\ART_DIRECTION.md',
    'Docs\TECHNICAL_PLAN.md'
)
$requiredFiles += $mapNames | ForEach-Object { "Content\Maps\$_.umap" }

foreach ($relativePath in $requiredFiles) {
    $fullPath = Join-Path $projectRoot $relativePath
    if (-not (Test-Path -LiteralPath $fullPath)) {
        throw "Missing required file: $relativePath"
    }
}

$project = Get-Content -Raw -LiteralPath (Join-Path $projectRoot 'Ciberfantasma3D.uproject') | ConvertFrom-Json
$campaign = Get-Content -Raw -LiteralPath (Join-Path $projectRoot 'Design\campaign_levels.json') | ConvertFrom-Json
$engineConfig = Get-Content -Raw -LiteralPath (Join-Path $projectRoot 'Config\DefaultEngine.ini')
$inputConfig = Get-Content -Raw -LiteralPath (Join-Path $projectRoot 'Config\DefaultInput.ini')
$playerSource = Get-Content -Raw -LiteralPath (Join-Path $projectRoot 'Source\Ciberfantasma3D\CFPlayerCharacter.cpp')
$projectileSource = Get-Content -Raw -LiteralPath (Join-Path $projectRoot 'Source\Ciberfantasma3D\CFPulseProjectile.cpp')
$enemySource = Get-Content -Raw -LiteralPath (Join-Path $projectRoot 'Source\Ciberfantasma3D\CFPatrolEnemy.cpp')

if ($project.Modules[0].Name -ne 'Ciberfantasma3D') {
    throw 'Unexpected Unreal module name.'
}
if ($campaign.levels.Count -ne 9) {
    throw "Expected 9 campaign levels, found $($campaign.levels.Count)."
}
foreach ($level in $campaign.levels) {
    if ($level.shards.Count -ne 3 -or $level.enemies.Count -lt 1 -or $level.platforms.Count -lt 1) {
        throw "Incomplete gameplay data in level $($level.name): $($level.title)"
    }
}
if ($engineConfig -notmatch [regex]::Escape('GlobalDefaultGameMode=/Script/Ciberfantasma3D.CFGameMode')) {
    throw 'CFGameMode is not configured in DefaultEngine.ini.'
}
if ($engineConfig -notmatch [regex]::Escape('GameDefaultMap=/Game/Maps/Act01_Rooftops')) {
    throw 'The campaign does not start in Act01_Rooftops.'
}
if ($engineConfig -notmatch [regex]::Escape('GameInstanceClass=/Script/Ciberfantasma3D.CFGameInstance')) {
    throw 'CFGameInstance is not configured for persistent campaign progress.'
}
foreach ($mapping in @('FireLeft', 'FireRight', 'Shield', 'Pause', 'Restart', 'RestartCampaign')) {
    if ($inputConfig -notmatch [regex]::Escape(('ActionName="{0}"' -f $mapping))) {
        throw "Missing input mapping: $mapping"
    }
}
if ($playerSource -notmatch [regex]::Escape('SK_Ciberfantasma_Chibi_Pro.SK_Ciberfantasma_Chibi_Pro')) {
    throw 'The player is not configured to use the professional generated skeletal mesh.'
}
foreach ($animation in @(
    'A_Ciberfantasma_Pro_Idle',
    'A_Ciberfantasma_Pro_Run',
    'A_Ciberfantasma_Pro_JumpStart',
    'A_Ciberfantasma_Pro_JumpRise',
    'A_Ciberfantasma_Pro_JumpFall',
    'A_Ciberfantasma_Pro_Land',
    'A_Ciberfantasma_Pro_Crouch',
    'A_Ciberfantasma_Pro_Fire',
    'A_Ciberfantasma_Pro_Shield',
    'A_Ciberfantasma_Pro_Hit'
)) {
    if ($playerSource -notmatch [regex]::Escape($animation)) {
        throw "The player is missing animation reference: $animation"
    }
}
foreach ($vfxReference in @('NS_MuzzleFlash_Runtime', 'NS_ShieldAbsorb_Runtime')) {
    if ($playerSource -notmatch [regex]::Escape($vfxReference)) {
        throw "The player is missing runtime VFX reference: $vfxReference"
    }
}
if ($projectileSource -notmatch [regex]::Escape('NS_PulseImpact_Runtime')) {
    throw 'The pulse projectile is missing its impact VFX reference.'
}
foreach ($vfxReference in @('NS_EnemyDeath_Runtime', 'NS_BossExplosion_Runtime')) {
    if ($enemySource -notmatch [regex]::Escape($vfxReference)) {
        throw "Enemies are missing runtime VFX reference: $vfxReference"
    }
}
foreach ($enemyMesh in @(
    'SM_LicenseWarden_Chibi',
    'SM_PanopticonDrone_Chibi',
    'SM_CEO9000_Chibi',
    'SM_Crawler_Chibi',
    'SM_Harvester_Chibi',
    'SM_Enforcer_Chibi',
    'SM_Auditor_Chibi',
    'SM_Director_Chibi'
)) {
    if ($enemySource -notmatch [regex]::Escape($enemyMesh)) {
        throw "Enemies are missing hard mesh reference: $enemyMesh"
    }
}
if ($enemySource -match 'LoadObject<UStaticMesh>') {
    throw 'Enemy meshes must be hard references so the cooker can discover them.'
}
foreach ($vfxAsset in @('NS_PulseImpact_Runtime', 'NS_EnemyDeath_Runtime', 'NS_MuzzleFlash_Runtime', 'NS_ShieldAbsorb_Runtime', 'NS_BossExplosion_Runtime')) {
    $vfxPath = Join-Path $projectRoot "Content\Art\VFX\$vfxAsset.uasset"
    if ((Get-Item -LiteralPath $vfxPath).Length -lt 100KB) {
        throw "Niagara system is still an empty stub: $vfxAsset"
    }
}

$levels = @($campaign.levels)
[pscustomobject]@{
    Project = $projectRoot
    Module = $project.Modules[0].Name
    Levels = $levels.Count
    Platforms = ($levels | ForEach-Object { $_.platforms.Count } | Measure-Object -Sum).Sum
    Enemies = ($levels | ForEach-Object { $_.enemies.Count } | Measure-Object -Sum).Sum
    Shards = ($levels | ForEach-Object { $_.shards.Count } | Measure-Object -Sum).Sum
    Terminals = ($levels | ForEach-Object { $_.terminals.Count } | Measure-Object -Sum).Sum
    Status = 'Nine-act campaign, hero animation and five runtime Niagara effects valid'
}
