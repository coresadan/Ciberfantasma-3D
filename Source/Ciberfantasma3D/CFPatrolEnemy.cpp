#include "CFPatrolEnemy.h"

#include "CFEnemyProjectile.h"
#include "CFGameState.h"
#include "CFPlayerCharacter.h"
#include "Components/CapsuleComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/DamageEvents.h"
#include "Materials/MaterialInterface.h"
#include "NiagaraFunctionLibrary.h"
#include "NiagaraSystem.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Kismet/GameplayStatics.h"
#include "UObject/ConstructorHelpers.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"

ACFPatrolEnemy::ACFPatrolEnemy()
{
    PrimaryActorTick.bCanEverTick = true;
    GetCapsuleComponent()->InitCapsuleSize(40.0f, 70.0f);
    GetCapsuleComponent()->SetCollisionResponseToChannel(ECC_Pawn, ECR_Overlap);
    GetCapsuleComponent()->OnComponentBeginOverlap.AddDynamic(this, &ACFPatrolEnemy::HandleOverlap);

    UCharacterMovementComponent* Movement = GetCharacterMovement();
    Movement->MaxWalkSpeed = PatrolSpeed;
    Movement->bConstrainToPlane = true;
    Movement->SetPlaneConstraintNormal(FVector(0.0f, 1.0f, 0.0f));
    Movement->bSnapToPlaneAtStart = true;

    DevelopmentVisual = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("DevelopmentVisual"));
    DevelopmentVisual->SetupAttachment(RootComponent);
    DevelopmentVisual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    static ConstructorHelpers::FObjectFinder<UStaticMesh> WardenMesh(
        TEXT("/Game/Art/Enemies/SM_LicenseWarden_Chibi.SM_LicenseWarden_Chibi"));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> DroneMesh(
        TEXT("/Game/Art/Enemies/SM_PanopticonDrone_Chibi.SM_PanopticonDrone_Chibi"));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> CeoMesh(
        TEXT("/Game/Art/Enemies/SM_CEO9000_Chibi.SM_CEO9000_Chibi"));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> CrawlerMesh(
        TEXT("/Game/Art/Enemies/SM_Crawler_Chibi.SM_Crawler_Chibi"));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> HarvesterMesh(
        TEXT("/Game/Art/Enemies/SM_Harvester_Chibi.SM_Harvester_Chibi"));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> EnforcerMesh(
        TEXT("/Game/Art/Enemies/SM_Enforcer_Chibi.SM_Enforcer_Chibi"));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> AuditorMesh(
        TEXT("/Game/Art/Enemies/SM_Auditor_Chibi.SM_Auditor_Chibi"));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> DirectorMesh(
        TEXT("/Game/Art/Enemies/SM_Director_Chibi.SM_Director_Chibi"));
    EnemyMeshes = {
        WardenMesh.Object,
        DroneMesh.Object,
        CeoMesh.Object,
        CrawlerMesh.Object,
        HarvesterMesh.Object,
        CeoMesh.Object,
        EnforcerMesh.Object,
        AuditorMesh.Object,
        DirectorMesh.Object,
    };
    if (WardenMesh.Succeeded())
    {
        DevelopmentVisual->SetStaticMesh(WardenMesh.Object);
        DevelopmentVisual->SetRelativeLocation(FVector(0.0f, 0.0f, -70.0f));
        DevelopmentVisual->SetRelativeScale3D(FVector::OneVector);
    }

    static ConstructorHelpers::FObjectFinder<UStaticMesh> SphereMesh(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> CubeMesh(TEXT("/Engine/BasicShapes/Cube.Cube"));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> CylinderMesh(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
    auto ConfigureAccent = [this](UStaticMeshComponent* Component)
    {
        Component->SetupAttachment(DevelopmentVisual);
        Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Component->CastShadow = false;
        Component->SetVisibility(false);
    };
    ProfileCore = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("ProfileCore"));
    ConfigureAccent(ProfileCore);
    if (SphereMesh.Succeeded()) ProfileCore->SetStaticMesh(SphereMesh.Object);
    ProfileFinLeft = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("ProfileFinLeft"));
    ConfigureAccent(ProfileFinLeft);
    if (CubeMesh.Succeeded()) ProfileFinLeft->SetStaticMesh(CubeMesh.Object);
    ProfileFinRight = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("ProfileFinRight"));
    ConfigureAccent(ProfileFinRight);
    if (CubeMesh.Succeeded()) ProfileFinRight->SetStaticMesh(CubeMesh.Object);
    ProfileCannon = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("ProfileCannon"));
    ConfigureAccent(ProfileCannon);
    if (CylinderMesh.Succeeded()) ProfileCannon->SetStaticMesh(CylinderMesh.Object);

    EnemyGlow = CreateDefaultSubobject<UPointLightComponent>(TEXT("EnemyGlow"));
    EnemyGlow->SetupAttachment(RootComponent);
    EnemyGlow->SetLightColor(FLinearColor(1.0f, 0.02f, 0.18f));
    EnemyGlow->Intensity = 500.0f;
    EnemyGlow->AttenuationRadius = 260.0f;
    EnemyProjectileClass = ACFEnemyProjectile::StaticClass();

    static ConstructorHelpers::FObjectFinder<UNiagaraSystem> DeathAsset(
        TEXT("/Game/Art/VFX/NS_EnemyDeath_Runtime.NS_EnemyDeath_Runtime"));
    static ConstructorHelpers::FObjectFinder<UNiagaraSystem> BossExplosionAsset(
        TEXT("/Game/Art/VFX/NS_BossExplosion_Runtime.NS_BossExplosion_Runtime"));
    DeathSystem = DeathAsset.Object;
    BossExplosionSystem = BossExplosionAsset.Object;
}

void ACFPatrolEnemy::BeginPlay()
{
    Super::BeginPlay();
    OriginX = GetActorLocation().X;
    OriginZ = GetActorLocation().Z;
    ApplyProfile();
    CurrentHealth = MaxHealth;
    if (FParse::Param(FCommandLine::Get(), TEXT("CFAutomatedEnemyTest")))
    {
        ShotCooldown = 0.58f;
    }
    if (ACFGameState* State = GetWorld()->GetGameState<ACFGameState>())
    {
        State->RegisterEnemy(IsBoss());
        bRegistered = true;
    }
}

void ACFPatrolEnemy::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    ACFGameState* State = GetWorld()->GetGameState<ACFGameState>();
    if (State && !State->CanPlayerAct()) return;
    ACFPlayerCharacter* Player = Cast<ACFPlayerCharacter>(UGameplayStatics::GetPlayerCharacter(this, 0));
    if (!Player) return;

    ShotCooldown -= DeltaSeconds;
    DashCooldown -= DeltaSeconds;
    AttackRecoilRemaining = FMath::Max(0.0f, AttackRecoilRemaining - DeltaSeconds);
    HitReactionRemaining = FMath::Max(0.0f, HitReactionRemaining - DeltaSeconds);
    if (bAttackQueued)
    {
        AttackWindupRemaining -= DeltaSeconds;
        if (AttackWindupRemaining <= 0.0f)
        {
            FireAtPlayer(PendingShotCount, PendingShotSpread, bPendingHeavyShot);
            bAttackQueued = false;
            AttackRecoilRemaining = IsBoss() ? 0.28f : 0.18f;
        }
    }
    const FVector ToPlayer = Player->GetActorLocation() - GetActorLocation();
    const float DistanceX = ToPlayer.X;
    const bool bSameLane = FMath::Abs(ToPlayer.Z) < 230.0f;
    if (FMath::Abs(GetActorLocation().X - OriginX) >= PatrolDistance)
    {
        PatrolDirection *= -1.0f;
    }

    if (EnemyKind == 0 && bSameLane && FMath::Abs(DistanceX) < 660.0f)
    {
        PatrolDirection = FMath::Sign(DistanceX);
        if (FMath::Abs(DistanceX) > 190.0f) AddMovementInput(FVector::ForwardVector, PatrolDirection, true);
    }
    else if (EnemyKind == 3 && bSameLane && FMath::Abs(DistanceX) < 780.0f && DashCooldown <= 0.0f)
    {
        PatrolDirection = FMath::Sign(DistanceX);
        LaunchCharacter(FVector(PatrolDirection * 900.0f, 0.0f, 0.0f), true, false);
        DashCooldown = 1.45f;
    }
    else if (IsFlying() || IsBoss())
    {
        FVector Location = GetActorLocation();
        Location.X += PatrolDirection * PatrolSpeed * DeltaSeconds;
        Location.Z = OriginZ + FMath::Sin(GetWorld()->GetTimeSeconds() * (EnemyKind == 4 ? 2.35f : 1.8f) + OriginX * 0.001f) * (EnemyKind == 4 ? 64.0f : 42.0f);
        SetActorLocation(Location, true);
    }
    else
    {
        AddMovementInput(FVector::ForwardVector, PatrolDirection, true);
    }

    const float FireRange = IsBoss() ? 2100.0f : (EnemyKind == 7 ? 1580.0f : 1220.0f);
    const bool bShooter = EnemyKind == 1 || EnemyKind == 2 || EnemyKind == 4 || EnemyKind == 5 || EnemyKind == 6 || EnemyKind == 7 || EnemyKind == 8;
    if (bShooter && !bAttackQueued && FMath::Abs(DistanceX) < FireRange && ShotCooldown <= 0.0f)
    {
        PatrolDirection = FMath::Sign(DistanceX);
        if (EnemyKind == 4) QueueAttack(3, 0.14f, false);
        else if (EnemyKind == 5) QueueAttack(CurrentHealth < MaxHealth * 0.5f ? 7 : 5, 0.16f, false);
        else if (EnemyKind == 8) QueueAttack(CurrentHealth < MaxHealth * 0.5f ? 5 : 3, 0.09f, true);
        else if (EnemyKind == 2) QueueAttack(CurrentHealth < MaxHealth * 0.5f ? 3 : 1, 0.075f, true);
        else QueueAttack(1, 0.0f, false);
        ShotCooldown = IsBoss() ? (CurrentHealth < MaxHealth * 0.5f ? 1.35f : 1.95f) : FMath::FRandRange(1.2f, 2.2f);
    }

    SetActorRotation(FRotator(0.0f, PatrolDirection > 0.0f ? 0.0f : 180.0f, 0.0f));
    UpdatePresentation(DeltaSeconds);
}

float ACFPatrolEnemy::TakeDamage(float DamageAmount, const FDamageEvent& DamageEvent,
    AController* EventInstigator, AActor* DamageCauser)
{
    if (DamageAmount <= 0.0f)
    {
        return 0.0f;
    }
    CurrentHealth -= DamageAmount;
    HitReactionRemaining = 0.24f;
    if (CurrentHealth <= 0.0f)
    {
        const bool bBoss = IsBoss();
        UNiagaraSystem* System = bBoss ? BossExplosionSystem.Get() : DeathSystem.Get();
        if (System)
        {
            const FVector Scale = bBoss ? FVector(0.44f) : FVector(0.2f * ProfileScale);
            UNiagaraFunctionLibrary::SpawnSystemAtLocation(this, System,
                GetActorLocation() + FVector(0.0f, 0.0f, 20.0f), FRotator::ZeroRotator, Scale);
        }
        if (bRegistered)
        {
            if (ACFGameState* State = GetWorld()->GetGameState<ACFGameState>()) State->EnemyDefeated(bBoss);
            bRegistered = false;
        }
        Destroy();
    }
    return DamageAmount;
}

void ACFPatrolEnemy::HandleOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor,
    UPrimitiveComponent* OtherComponent, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult)
{
    if (ACFPlayerCharacter* Player = Cast<ACFPlayerCharacter>(OtherActor))
    {
        if (!IsBoss() && Player->GetVelocity().Z < -150.0f && Player->GetActorLocation().Z > GetActorLocation().Z + 45.0f)
        {
            TakeDamage(2.0f, FDamageEvent(), Player->GetController(), Player);
            Player->LaunchCharacter(FVector(0.0f, 0.0f, 520.0f), false, true);
        }
        else
        {
            UGameplayStatics::ApplyDamage(Player, ContactDamage, nullptr, this, UDamageType::StaticClass());
        }
    }
}

bool ACFPatrolEnemy::IsBoss() const
{
    return EnemyKind == 2 || EnemyKind == 5 || EnemyKind == 8;
}

bool ACFPatrolEnemy::IsFlying() const
{
    return EnemyKind == 1 || EnemyKind == 4;
}

void ACFPatrolEnemy::ApplyProfile()
{
    // --- Select the correct hard-referenced chibi mesh for this enemy type ---
    // EnemyKind mapping:
    //   0 = bot (basic ground)      -> SM_LicenseWarden_Chibi (repurposed as grunt)
    //   1 = drone (flying)          -> SM_PanopticonDrone_Chibi
    //   2 = boss (CEO-9000 Acto I)  -> SM_CEO9000_Chibi
    //   3 = crawler (melee charger) -> SM_Crawler_Chibi
    //   4 = harvester (large drone) -> SM_Harvester_Chibi
    //   5 = boss2 (CEO Acto II)     -> SM_CEO9000_Chibi (scaled)
    //   6 = enforcer (riot police)  -> SM_Enforcer_Chibi
    //   7 = auditor (bureaucrat)    -> SM_Auditor_Chibi
    //   8 = director (final boss)   -> SM_Director_Chibi
    const int32 KindIndex = FMath::Clamp(EnemyKind, 0, 8);
    if (EnemyMeshes.IsValidIndex(KindIndex) && EnemyMeshes[KindIndex])
    {
        DevelopmentVisual->SetStaticMesh(EnemyMeshes[KindIndex]);
    }

    // --- Combat stats ---
    MaxHealth = EnemyKind == 2 ? 12.0f : EnemyKind == 5 ? 18.0f : EnemyKind == 8 ? 24.0f
        : EnemyKind == 7 || EnemyKind == 3 ? 4.0f : EnemyKind == 6 ? 5.0f : EnemyKind == 1 ? 2.0f : 3.0f;
    PatrolSpeed = EnemyKind == 3 ? 168.0f : EnemyKind == 7 ? 84.0f : EnemyKind == 6 ? 156.0f : IsBoss() ? 120.0f : 140.0f;
    PatrolDistance = IsBoss() ? 760.0f : EnemyKind == 6 ? 460.0f : 320.0f;
    if (IsFlying() || IsBoss()) GetCharacterMovement()->SetMovementMode(MOVE_Flying);

    // --- Visual scale and offset per type ---
    //   Boss kinds get larger, director gets biggest.
    ProfileScale = EnemyKind == 8 ? 2.2f : (EnemyKind == 2 || EnemyKind == 5) ? 1.8f
        : EnemyKind == 4 ? 1.3f : EnemyKind == 6 ? 1.2f : (EnemyKind == 3 ? 0.85f : 1.0f);
    DevelopmentVisual->SetRelativeScale3D(FVector(ProfileScale));
    DevelopmentVisual->SetRelativeLocation(FVector(0.0f, 0.0f, IsBoss() ? -110.0f : -70.0f));

    // --- Glow colour per type ---
    FLinearColor GlowColor;
    switch (EnemyKind)
    {
    case 1:  GlowColor = FLinearColor(0.8f, 0.01f, 1.0f); break;   // drone: magenta
    case 2:  GlowColor = FLinearColor(1.0f, 0.55f, 0.01f); break;  // CEO-9000: gold
    case 3:  GlowColor = FLinearColor(1.0f, 0.28f, 0.01f); break;  // crawler: orange
    case 4:  GlowColor = FLinearColor(0.01f, 0.9f, 0.8f); break;   // harvester: teal
    case 5:  GlowColor = FLinearColor(1.0f, 0.55f, 0.01f); break;  // boss2: gold
    case 6:  GlowColor = FLinearColor(0.05f, 0.15f, 1.0f); break;  // enforcer: blue
    case 7:  GlowColor = FLinearColor(1.0f, 0.85f, 0.01f); break;  // auditor: yellow
    case 8:  GlowColor = FLinearColor(1.0f, 0.01f, 0.01f); break;  // director: red
    default: GlowColor = FLinearColor(1.0f, 0.01f, 0.2f); break;   // bot: red
    }
    EnemyGlow->SetLightColor(GlowColor);
    EnemyGlow->Intensity = IsBoss() ? 900.0f : 500.0f;
    EnemyGlow->AttenuationRadius = IsBoss() ? 520.0f : 260.0f;

    // Accent sub-components kept for backward compatibility but hidden behind the chibi mesh.
    ProfileCore->SetVisibility(false);
    ProfileFinLeft->SetVisibility(false);
    ProfileFinRight->SetVisibility(false);
    ProfileCannon->SetVisibility(false);
}


void ACFPatrolEnemy::QueueAttack(int32 Count, float Spread, bool bHeavy)
{
    PendingShotCount = Count;
    PendingShotSpread = Spread;
    bPendingHeavyShot = bHeavy;
    bAttackQueued = true;
    AttackWindupRemaining = IsBoss() ? 0.34f : 0.2f;
}

void ACFPatrolEnemy::UpdatePresentation(float DeltaSeconds)
{
    if (!DevelopmentVisual) return;
    const float Time = GetWorld()->GetTimeSeconds() + OriginX * 0.001f;
    const float SpeedFraction = FMath::Clamp(FMath::Abs(GetVelocity().X) / FMath::Max(PatrolSpeed, 1.0f), 0.0f, 1.0f);
    const float Gait = FMath::Sin(Time * (IsFlying() ? 4.2f : 8.5f));
    const float Hover = IsFlying() || IsBoss() ? FMath::Sin(Time * 3.0f) * 4.0f : FMath::Abs(Gait) * 2.5f * SpeedFraction;
    const float WindupAlpha = bAttackQueued
        ? 1.0f - FMath::Clamp(AttackWindupRemaining / (IsBoss() ? 0.34f : 0.2f), 0.0f, 1.0f)
        : 0.0f;
    const float RecoilAlpha = FMath::Clamp(AttackRecoilRemaining / (IsBoss() ? 0.28f : 0.18f), 0.0f, 1.0f);
    const float HitWave = HitReactionRemaining > 0.0f ? FMath::Sin(HitReactionRemaining * 55.0f) : 0.0f;
    const float BaseZ = IsBoss() ? -110.0f : -70.0f;
    const float PullBack = -PatrolDirection * (WindupAlpha * 8.0f - RecoilAlpha * 13.0f);
    DevelopmentVisual->SetRelativeLocation(FVector(PullBack, 0.0f, BaseZ + Hover));
    const float Bank = IsFlying() ? -PatrolDirection * 7.0f + Gait * 2.0f : Gait * 2.8f * SpeedFraction;
    DevelopmentVisual->SetRelativeRotation(FRotator(0.0f, 0.0f, Bank + HitWave * 5.0f));
    const float Squash = WindupAlpha * 0.06f + FMath::Abs(HitWave) * 0.045f;
    DevelopmentVisual->SetRelativeScale3D(FVector(
        ProfileScale * (1.0f + Squash), ProfileScale * (1.0f - Squash * 0.4f), ProfileScale * (1.0f - Squash)));
    const float CorePulse = 1.0f + FMath::Sin(Time * 9.0f) * 0.08f + WindupAlpha * 0.38f + RecoilAlpha * 0.22f;
    ProfileCore->SetRelativeScale3D(FVector((IsBoss() ? 0.16f : 0.1f) * CorePulse));
    ProfileFinLeft->SetRelativeRotation(FRotator(0.0f, WindupAlpha * -16.0f, -18.0f - RecoilAlpha * 14.0f));
    ProfileFinRight->SetRelativeRotation(FRotator(0.0f, WindupAlpha * 16.0f, 18.0f + RecoilAlpha * 14.0f));
    ProfileCannon->SetRelativeLocation(FVector(48.0f + RecoilAlpha * -9.0f, -8.0f, 28.0f));
    EnemyGlow->SetIntensity(420.0f + WindupAlpha * 1450.0f + RecoilAlpha * 800.0f + FMath::Abs(HitWave) * 1200.0f);
}

void ACFPatrolEnemy::FireAtPlayer(int32 Count, float Spread, bool bHeavy)
{
    ACharacter* Player = UGameplayStatics::GetPlayerCharacter(this, 0);
    if (!Player || !EnemyProjectileClass) return;
    const FVector Origin = GetActorLocation() + FVector(PatrolDirection * 75.0f, 0.0f, 35.0f);
    const FVector BaseDirection = (Player->GetActorLocation() + FVector(0.0f, 0.0f, 25.0f) - Origin).GetSafeNormal();
    for (int32 Index = 0; Index < Count; ++Index)
    {
        const float Offset = (Index - (Count - 1) * 0.5f) * Spread;
        const FVector Direction = BaseDirection.RotateAngleAxis(FMath::RadiansToDegrees(Offset), FVector::YAxisVector);
        FActorSpawnParameters Params;
        Params.Owner = this;
        Params.Instigator = this;
        Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
        if (ACFEnemyProjectile* Shot = GetWorld()->SpawnActor<ACFEnemyProjectile>(EnemyProjectileClass, Origin, Direction.Rotation(), Params))
        {
            Shot->Launch(Direction, bHeavy ? 1050.0f : (EnemyKind == 7 ? 1090.0f : 720.0f), bHeavy);
        }
    }
}
