#include "CFPlayerCharacter.h"

#include "CFGameInstance.h"
#include "CFGameState.h"
#include "CFHeroAnimInstance.h"
#include "CFPulseProjectile.h"
#include "CFPatrolEnemy.h"
#include "Camera/CameraComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Animation/AnimSequence.h"
#include "Materials/MaterialInterface.h"
#include "NiagaraFunctionLibrary.h"
#include "NiagaraSystem.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/SpringArmComponent.h"
#include "Engine/DamageEvents.h"
#include "Engine/World.h"
#include "Kismet/GameplayStatics.h"
#include "UObject/ConstructorHelpers.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "HAL/PlatformMisc.h"
#include "UnrealClient.h"
#include "EngineUtils.h"

ACFPlayerCharacter::ACFPlayerCharacter()
{
    PrimaryActorTick.bCanEverTick = true;

    GetCapsuleComponent()->InitCapsuleSize(42.0f, 92.0f);

    UCharacterMovementComponent* Movement = GetCharacterMovement();
    Movement->GravityScale = 1.0f;
    Movement->AirControl = 0.72f;
    Movement->JumpZVelocity = 700.0f;
    Movement->MaxWalkSpeed = 720.0f;
    Movement->MaxWalkSpeedCrouched = 320.0f;
    Movement->GroundFriction = 9.0f;
    Movement->BrakingDecelerationWalking = 2200.0f;
    Movement->bOrientRotationToMovement = false;
    Movement->bConstrainToPlane = true;
    Movement->SetPlaneConstraintNormal(FVector(0.0f, 1.0f, 0.0f));
    Movement->bSnapToPlaneAtStart = true;
    Movement->GetNavAgentPropertiesRef().bCanCrouch = true;
    Movement->SetCrouchedHalfHeight(55.0f);

    JumpMaxCount = 2;
    JumpMaxHoldTime = 0.12f;
    bUseControllerRotationYaw = false;

    CameraBoom = CreateDefaultSubobject<USpringArmComponent>(TEXT("CameraBoom"));
    CameraBoom->SetupAttachment(RootComponent);
    CameraBoom->SetUsingAbsoluteRotation(true);
    CameraBoom->SetRelativeRotation(FRotator(0.0f, -90.0f, 0.0f));
    // Match the original Canvas game's generous 2D read distance: the player
    // occupies roughly one sixth of the frame instead of dominating it.
    CameraBoom->TargetArmLength = 1400.0f;
    CameraBoom->bDoCollisionTest = false;
    CameraBoom->bEnableCameraLag = true;
    CameraBoom->CameraLagSpeed = 6.5f;

    SideViewCamera = CreateDefaultSubobject<UCameraComponent>(TEXT("SideViewCamera"));
    SideViewCamera->SetupAttachment(CameraBoom, USpringArmComponent::SocketName);
    SideViewCamera->bUsePawnControlRotation = false;
    SideViewCamera->FieldOfView = 44.0f;

    ShieldVisual = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("ShieldVisual"));
    ShieldVisual->SetupAttachment(RootComponent);
    ShieldVisual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    ShieldVisual->SetRelativeScale3D(FVector(0.62f, 0.055f, 1.20f));
    ShieldVisual->SetVisibility(false);
    ShieldVisual->CastShadow = false;
    ShieldVisual->SetTranslucentSortPriority(2);
    static ConstructorHelpers::FObjectFinder<UStaticMesh> ShieldCube(TEXT("/Engine/BasicShapes/Cube.Cube"));
    if (ShieldCube.Succeeded())
    {
        ShieldVisual->SetStaticMesh(ShieldCube.Object);
    }
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> ShieldMaterial(
        TEXT("/Game/Art/Materials/M_CF_Shield_V9.M_CF_Shield_V9"));
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> ShieldFrameMaterial(
        TEXT("/Game/Art/Materials/M_CF_Pulse_V9.M_CF_Pulse_V9"));
    if (ShieldMaterial.Succeeded())
    {
        ShieldVisual->SetMaterial(0, ShieldMaterial.Object);
    }

    // A second rounded energy layer gives the shield volume and a softer
    // silhouette. The outer cuboid remains the stable gameplay-readable pane.
    ShieldInnerVisual = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("ShieldInnerVisual"));
    ShieldInnerVisual->SetupAttachment(RootComponent);
    ShieldInnerVisual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    ShieldInnerVisual->SetVisibility(false);
    ShieldInnerVisual->CastShadow = false;
    ShieldInnerVisual->SetTranslucentSortPriority(2);
    static ConstructorHelpers::FObjectFinder<UStaticMesh> ShieldSphere(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
    if (ShieldSphere.Succeeded()) ShieldInnerVisual->SetStaticMesh(ShieldSphere.Object);
    if (ShieldMaterial.Succeeded()) ShieldInnerVisual->SetMaterial(0, ShieldMaterial.Object);

    ShieldScanLine = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("ShieldScanLine"));
    ShieldScanLine->SetupAttachment(RootComponent);
    ShieldScanLine->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    ShieldScanLine->SetVisibility(false);
    ShieldScanLine->CastShadow = false;
    ShieldScanLine->SetTranslucentSortPriority(4);
    if (ShieldCube.Succeeded()) ShieldScanLine->SetStaticMesh(ShieldCube.Object);
    if (ShieldFrameMaterial.Succeeded()) ShieldScanLine->SetMaterial(0, ShieldFrameMaterial.Object);

    ShieldFrameTop = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("ShieldFrameTop"));
    ShieldFrameBottom = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("ShieldFrameBottom"));
    ShieldFrameLeft = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("ShieldFrameLeft"));
    ShieldFrameRight = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("ShieldFrameRight"));
    for (UStaticMeshComponent* Frame : {ShieldFrameTop.Get(), ShieldFrameBottom.Get(),
        ShieldFrameLeft.Get(), ShieldFrameRight.Get()})
    {
        Frame->SetupAttachment(RootComponent);
        Frame->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Frame->SetVisibility(false);
        Frame->CastShadow = false;
        Frame->SetTranslucentSortPriority(3);
        if (ShieldCube.Succeeded()) Frame->SetStaticMesh(ShieldCube.Object);
        if (ShieldFrameMaterial.Succeeded()) Frame->SetMaterial(0, ShieldFrameMaterial.Object);
    }
    ShieldFrameTop->SetRelativeScale3D(FVector(0.65f, 0.035f, 0.028f));
    ShieldFrameBottom->SetRelativeScale3D(FVector(0.65f, 0.035f, 0.028f));
    ShieldFrameLeft->SetRelativeScale3D(FVector(0.028f, 0.035f, 1.20f));
    ShieldFrameRight->SetRelativeScale3D(FVector(0.028f, 0.035f, 1.20f));

    ShieldLight = CreateDefaultSubobject<UPointLightComponent>(TEXT("ShieldLight"));
    ShieldLight->SetupAttachment(RootComponent);
    ShieldLight->SetLightColor(FLinearColor(0.0f, 1.0f, 0.08f));
    ShieldLight->SetAttenuationRadius(330.0f);
    ShieldLight->SetIntensity(0.0f);
    ShieldLight->CastShadows = false;

    MuzzleLight = CreateDefaultSubobject<UPointLightComponent>(TEXT("MuzzleLight"));
    MuzzleLight->SetupAttachment(RootComponent);
    MuzzleLight->SetLightColor(FLinearColor(0.05f, 1.0f, 0.18f));
    MuzzleLight->SetAttenuationRadius(240.0f);
    MuzzleLight->SetIntensity(0.0f);
    MuzzleLight->CastShadows = false;

    MuzzleFlashVisual = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("MuzzleFlashVisual"));
    MuzzleFlashVisual->SetupAttachment(RootComponent);
    MuzzleFlashVisual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    MuzzleFlashVisual->SetVisibility(false);
    MuzzleFlashVisual->CastShadow = false;
    static ConstructorHelpers::FObjectFinder<UStaticMesh> MuzzleCone(TEXT("/Engine/BasicShapes/Cone.Cone"));
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> PulseCoreMaterial(
        TEXT("/Game/Art/Materials/M_CF_Pulse_V9.M_CF_Pulse_V9"));
    if (MuzzleCone.Succeeded()) MuzzleFlashVisual->SetStaticMesh(MuzzleCone.Object);
    if (PulseCoreMaterial.Succeeded()) MuzzleFlashVisual->SetMaterial(0, PulseCoreMaterial.Object);

    static ConstructorHelpers::FObjectFinder<UNiagaraSystem> ShieldAbsorbAsset(
        TEXT("/Game/Art/VFX/NS_ShieldAbsorb_Runtime.NS_ShieldAbsorb_Runtime"));
    ShieldAbsorbSystem = ShieldAbsorbAsset.Object;

    USkeletalMeshComponent* CharacterVisual = GetMesh();
    CharacterVisual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    static ConstructorHelpers::FObjectFinder<USkeletalMesh> CharacterMesh(
        TEXT("/Game/Art/Characters/SK_Ciberfantasma_Chibi_Pro.SK_Ciberfantasma_Chibi_Pro"));
    if (CharacterMesh.Succeeded())
    {
        CharacterVisual->SetSkeletalMeshAsset(CharacterMesh.Object);
        CharacterVisual->SetRelativeLocation(FVector(0.0f, 0.0f, -92.0f));
        CharacterVisual->SetRelativeRotation(FRotator::ZeroRotator);
        CharacterVisual->SetRelativeScale3D(FVector::OneVector);
        CharacterVisual->SetAnimationMode(EAnimationMode::AnimationBlueprint);
        CharacterVisual->SetAnimInstanceClass(UCFHeroAnimInstance::StaticClass());
    }

    static ConstructorHelpers::FObjectFinder<UAnimSequence> IdleAsset(
        TEXT("/Game/Art/Characters/Animations/A_Ciberfantasma_Pro_Idle.A_Ciberfantasma_Pro_Idle"));
    static ConstructorHelpers::FObjectFinder<UAnimSequence> RunStartAsset(
        TEXT("/Game/Art/Characters/Animations/A_Ciberfantasma_Pro_RunStart.A_Ciberfantasma_Pro_RunStart"));
    static ConstructorHelpers::FObjectFinder<UAnimSequence> RunAsset(
        TEXT("/Game/Art/Characters/Animations/A_Ciberfantasma_Pro_Run.A_Ciberfantasma_Pro_Run"));
    static ConstructorHelpers::FObjectFinder<UAnimSequence> RunStopAsset(
        TEXT("/Game/Art/Characters/Animations/A_Ciberfantasma_Pro_RunStop.A_Ciberfantasma_Pro_RunStop"));
    static ConstructorHelpers::FObjectFinder<UAnimSequence> JumpStartAsset(
        TEXT("/Game/Art/Characters/Animations/A_Ciberfantasma_Pro_JumpStart.A_Ciberfantasma_Pro_JumpStart"));
    static ConstructorHelpers::FObjectFinder<UAnimSequence> JumpRiseAsset(
        TEXT("/Game/Art/Characters/Animations/A_Ciberfantasma_Pro_JumpRise.A_Ciberfantasma_Pro_JumpRise"));
    static ConstructorHelpers::FObjectFinder<UAnimSequence> JumpFallAsset(
        TEXT("/Game/Art/Characters/Animations/A_Ciberfantasma_Pro_JumpFall.A_Ciberfantasma_Pro_JumpFall"));
    static ConstructorHelpers::FObjectFinder<UAnimSequence> LandAsset(
        TEXT("/Game/Art/Characters/Animations/A_Ciberfantasma_Pro_Land.A_Ciberfantasma_Pro_Land"));
    static ConstructorHelpers::FObjectFinder<UAnimSequence> CrouchAsset(
        TEXT("/Game/Art/Characters/Animations/A_Ciberfantasma_Pro_Crouch.A_Ciberfantasma_Pro_Crouch"));
    static ConstructorHelpers::FObjectFinder<UAnimSequence> CrouchWalkAsset(
        TEXT("/Game/Art/Characters/Animations/A_Ciberfantasma_Pro_CrouchWalk.A_Ciberfantasma_Pro_CrouchWalk"));
    static ConstructorHelpers::FObjectFinder<UAnimSequence> FireAsset(
        TEXT("/Game/Art/Characters/Animations/A_Ciberfantasma_Pro_Fire.A_Ciberfantasma_Pro_Fire"));
    static ConstructorHelpers::FObjectFinder<UAnimSequence> FireBackAsset(
        TEXT("/Game/Art/Characters/Animations/A_Ciberfantasma_Pro_FireBack.A_Ciberfantasma_Pro_FireBack"));
    static ConstructorHelpers::FObjectFinder<UAnimSequence> ShieldAsset(
        TEXT("/Game/Art/Characters/Animations/A_Ciberfantasma_Pro_Shield.A_Ciberfantasma_Pro_Shield"));
    static ConstructorHelpers::FObjectFinder<UAnimSequence> HitAsset(
        TEXT("/Game/Art/Characters/Animations/A_Ciberfantasma_Pro_Hit.A_Ciberfantasma_Pro_Hit"));
    IdleAnimation = IdleAsset.Object;
    RunStartAnimation = RunStartAsset.Object;
    RunAnimation = RunAsset.Object;
    RunStopAnimation = RunStopAsset.Object;
    JumpStartAnimation = JumpStartAsset.Object;
    JumpRiseAnimation = JumpRiseAsset.Object;
    JumpFallAnimation = JumpFallAsset.Object;
    LandAnimation = LandAsset.Object;
    CrouchAnimation = CrouchAsset.Object;
    CrouchWalkAnimation = CrouchWalkAsset.Object;
    FireAnimation = FireAsset.Object;
    FireBackAnimation = FireBackAsset.Object;
    ShieldAnimation = ShieldAsset.Object;
    HitAnimation = HitAsset.Object;

    ProjectileClass = ACFPulseProjectile::StaticClass();
}

void ACFPlayerCharacter::BeginPlay()
{
    Super::BeginPlay();
    SetActorRotation(FRotator::ZeroRotator);
    CurrentHealth = MaxHealth;
    CheckpointLocation = GetActorLocation();
    bWasGrounded = GetCharacterMovement()->IsMovingOnGround();
    bAutomatedAnimationTest = FParse::Param(FCommandLine::Get(), TEXT("CFAutomatedAnimationTest"));
    bAutomatedEnemyTest = FParse::Param(FCommandLine::Get(), TEXT("CFAutomatedEnemyTest"));
    bAutomatedCrouchWalkTest = FParse::Param(FCommandLine::Get(), TEXT("CFAutomatedCrouchWalkTest"));
    bAutomatedReverseFireTest = FParse::Param(FCommandLine::Get(), TEXT("CFAutomatedReverseFireTest"));
    bAutomatedLocomotionTransitionTest = FParse::Param(
        FCommandLine::Get(), TEXT("CFAutomatedLocomotionTransitionTest"));
    bAutomatedFootIKTest = FParse::Param(FCommandLine::Get(), TEXT("CFAutomatedFootIKTest"));
    SetShieldPresentation(false);
    SetBaseAnimation(IdleAnimation, true, 1.0f, 0.0f);
}

void ACFPlayerCharacter::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);

    FireCooldownRemaining = FMath::Max(0.0f, FireCooldownRemaining - DeltaSeconds);
    ShieldCooldownRemaining = FMath::Max(0.0f, ShieldCooldownRemaining - DeltaSeconds);
    DamageInvulnerabilityRemaining = FMath::Max(0.0f, DamageInvulnerabilityRemaining - DeltaSeconds);
    AnimationLockRemaining = FMath::Max(0.0f, AnimationLockRemaining - DeltaSeconds);
    MuzzleFlashRemaining = FMath::Max(0.0f, MuzzleFlashRemaining - DeltaSeconds);

    if (bAutomatedAnimationTest)
    {
        UpdateAutomatedAnimationTest(DeltaSeconds);
    }
    if (bAutomatedEnemyTest)
    {
        UpdateAutomatedEnemyTest(DeltaSeconds);
    }
    if (bAutomatedCrouchWalkTest)
    {
        UpdateAutomatedCrouchWalkTest(DeltaSeconds);
    }
    if (bAutomatedReverseFireTest)
    {
        UpdateAutomatedReverseFireTest(DeltaSeconds);
    }
    if (bAutomatedLocomotionTransitionTest)
    {
        UpdateAutomatedLocomotionTransitionTest(DeltaSeconds);
    }
    if (bAutomatedFootIKTest)
    {
        UpdateAutomatedFootIKTest(DeltaSeconds);
    }

    const bool bShieldWasActive = IsShieldActive();
    ShieldRemaining = FMath::Max(0.0f, ShieldRemaining - DeltaSeconds);
    if (bShieldWasActive && !IsShieldActive())
    {
        SetShieldPresentation(false);
        OnShieldVisualChanged(false);
    }

    UpdateCharacterPresentation(DeltaSeconds);

    if (GetActorLocation().Z < -500.0f)
    {
        TakeDamage(1.0f, FDamageEvent(), nullptr, nullptr);
    }
}

void ACFPlayerCharacter::UpdateAutomatedEnemyTest(float DeltaSeconds)
{
    AutomatedEnemyTestTime += DeltaSeconds;
    if (AutomatedEnemyTestStage == 0 && AutomatedEnemyTestTime >= 0.2f)
    {
        for (TActorIterator<ACFPatrolEnemy> It(GetWorld()); It; ++It)
        {
            const FVector EnemyLocation = It->GetActorLocation();
            SetActorLocation(FVector(EnemyLocation.X - 470.0f, GetActorLocation().Y, GetActorLocation().Z),
                false, nullptr, ETeleportType::TeleportPhysics);
            FacingDirection = 1.0f;
            AutomatedEnemyTestStage = 1;
            break;
        }
    }
    else if (AutomatedEnemyTestStage == 1 && AutomatedEnemyTestTime >= 0.78f)
    {
        FScreenshotRequest::RequestScreenshot(TEXT("CFAutomation_EnemyWindup.png"), false, false);
        UE_LOG(LogTemp, Display, TEXT("CF_ENEMY_TEST Windup screenshot requested"));
        AutomatedEnemyTestStage = 2;
    }
    else if (AutomatedEnemyTestStage == 2 && AutomatedEnemyTestTime >= 1.08f)
    {
        FScreenshotRequest::RequestScreenshot(TEXT("CFAutomation_EnemyRecoil.png"), false, false);
        UE_LOG(LogTemp, Display, TEXT("CF_ENEMY_TEST Recoil screenshot requested"));
        AutomatedEnemyTestStage = 3;
    }
    else if (AutomatedEnemyTestStage == 3 && AutomatedEnemyTestTime >= 2.2f)
    {
        UE_LOG(LogTemp, Display, TEXT("CF_ENEMY_TEST PASS"));
        bAutomatedEnemyTest = false;
        FPlatformMisc::RequestExit(false);
    }
}

void ACFPlayerCharacter::UpdateAutomatedCrouchWalkTest(float DeltaSeconds)
{
    AutomatedCrouchWalkTestTime += DeltaSeconds;
    if (AutomatedCrouchWalkTestStage == 0 && AutomatedCrouchWalkTestTime >= 0.15f)
    {
        FacingDirection = 1.0f;
        Crouch();
        AutomatedCrouchWalkTestStage = 1;
    }
    if (AutomatedCrouchWalkTestTime >= 0.25f && AutomatedCrouchWalkTestTime < 1.45f)
    {
        AddMovementInput(FVector::ForwardVector, 0.72f);
    }
    if (AutomatedCrouchWalkTestStage == 1 && AutomatedCrouchWalkTestTime >= 0.78f)
    {
        const bool bCorrectState = bIsCrouched && CurrentBaseAnimation == CrouchWalkAnimation
            && GetVelocity().X > 30.0f;
        if (!bCorrectState)
        {
            UE_LOG(LogTemp, Error,
                TEXT("CF_CROUCH_WALK_TEST FAIL activation (crouched %d, animation %s, velocity X %.3f)"),
                bIsCrouched, CurrentBaseAnimation == CrouchWalkAnimation ? TEXT("crouch-walk") : TEXT("other"),
                GetVelocity().X);
            bAutomatedCrouchWalkTest = false;
            FPlatformMisc::RequestExitWithStatus(false, 1);
            return;
        }
        AutomatedCrouchWalkSampleTime = CurrentBaseTime;
        FScreenshotRequest::RequestScreenshot(TEXT("CFAutomation_CrouchWalk.png"), false, false);
        UE_LOG(LogTemp, Display, TEXT("CF_CROUCH_WALK_TEST gait active at animation time %.3f"),
            CurrentBaseTime);
        AutomatedCrouchWalkTestStage = 2;
    }
    else if (AutomatedCrouchWalkTestStage == 2 && AutomatedCrouchWalkTestTime >= 1.18f)
    {
        const bool bCycleAdvanced = CurrentBaseAnimation == CrouchWalkAnimation
            && FMath::Abs(CurrentBaseTime - AutomatedCrouchWalkSampleTime) > 0.08f;
        if (bCycleAdvanced)
        {
            UE_LOG(LogTemp, Display,
                TEXT("CF_CROUCH_WALK_TEST PASS (cycle %.3f -> %.3f, velocity X %.3f)"),
                AutomatedCrouchWalkSampleTime, CurrentBaseTime, GetVelocity().X);
            UnCrouch();
            bAutomatedCrouchWalkTest = false;
            FPlatformMisc::RequestExitWithStatus(false, 0);
        }
        else
        {
            UE_LOG(LogTemp, Error,
                TEXT("CF_CROUCH_WALK_TEST FAIL cycle did not advance (%.3f -> %.3f)"),
                AutomatedCrouchWalkSampleTime, CurrentBaseTime);
            bAutomatedCrouchWalkTest = false;
            FPlatformMisc::RequestExitWithStatus(false, 1);
        }
    }
}

void ACFPlayerCharacter::UpdateAutomatedReverseFireTest(float DeltaSeconds)
{
    AutomatedReverseFireTestTime += DeltaSeconds;
    if (AutomatedReverseFireTestTime >= 0.12f && AutomatedReverseFireTestTime < 0.90f)
    {
        FacingDirection = 1.0f;
        AddMovementInput(FVector::ForwardVector, 0.82f);
    }
    else if (AutomatedReverseFireTestTime >= 0.90f && AutomatedReverseFireTestTime < 2.30f)
    {
        FacingDirection = -1.0f;
        AddMovementInput(FVector::ForwardVector, -0.82f);
    }

    if (AutomatedReverseFireTestStage == 0 && AutomatedReverseFireTestTime >= 0.48f)
    {
        FireInDirection(-1.0f);
        const bool bCorrectActivation = FacingDirection > 0.0f
            && ActiveFireDirection < 0.0f
            && bLastShotContralateral
            && AdditiveAnimation == FireBackAnimation
            && GetVelocity().X > 30.0f;
        if (!bCorrectActivation)
        {
            UE_LOG(LogTemp, Error,
                TEXT("CF_REVERSE_FIRE_TEST FAIL activation (travel %.1f, shot %.1f, reverse %d, animation %s, velocity X %.3f)"),
                FacingDirection, ActiveFireDirection, bLastShotContralateral,
                AdditiveAnimation == FireBackAnimation ? TEXT("fire-back") : TEXT("other"),
                GetVelocity().X);
            bAutomatedReverseFireTest = false;
            FPlatformMisc::RequestExitWithStatus(false, 1);
            return;
        }
        FScreenshotRequest::RequestScreenshot(TEXT("CFAutomation_ReverseFire.png"), false, false);
        UE_LOG(LogTemp, Display,
            TEXT("CF_REVERSE_FIRE_TEST contralateral pose active while velocity X %.3f"), GetVelocity().X);
        AutomatedReverseFireTestStage = 1;
    }
    else if (AutomatedReverseFireTestStage == 1 && AutomatedReverseFireTestTime >= 0.60f)
    {
        const bool bLayerAdvanced = AdditiveAnimation == FireBackAnimation && AdditiveTime > 0.07f;
        const bool bTravelPreserved = FacingDirection > 0.0f && GetVelocity().X > 30.0f;
        if (bLayerAdvanced && bTravelPreserved)
        {
            UE_LOG(LogTemp, Display,
                TEXT("CF_REVERSE_FIRE_TEST right-to-left PASS (travel %.1f, shot %.1f, layer time %.3f, velocity X %.3f)"),
                FacingDirection, ActiveFireDirection, AdditiveTime, GetVelocity().X);
            AutomatedReverseFireTestStage = 2;
        }
        else
        {
            UE_LOG(LogTemp, Error,
                TEXT("CF_REVERSE_FIRE_TEST FAIL persistence (layer %.3f, travel %.1f, velocity X %.3f)"),
                AdditiveTime, FacingDirection, GetVelocity().X);
            bAutomatedReverseFireTest = false;
            FPlatformMisc::RequestExitWithStatus(false, 1);
        }
    }
    else if (AutomatedReverseFireTestStage == 2 && AutomatedReverseFireTestTime >= 1.55f
        && GetVelocity().X < -30.0f)
    {
        FireInDirection(1.0f);
        const bool bMirroredActivation = FacingDirection < 0.0f
            && ActiveFireDirection > 0.0f
            && bLastShotContralateral
            && AdditiveAnimation == FireBackAnimation;
        if (!bMirroredActivation)
        {
            UE_LOG(LogTemp, Error,
                TEXT("CF_REVERSE_FIRE_TEST FAIL mirrored activation (travel %.1f, shot %.1f, reverse %d, velocity X %.3f)"),
                FacingDirection, ActiveFireDirection, bLastShotContralateral, GetVelocity().X);
            bAutomatedReverseFireTest = false;
            FPlatformMisc::RequestExitWithStatus(false, 1);
            return;
        }
        AutomatedReverseFireTestStage = 3;
    }
    else if (AutomatedReverseFireTestStage == 2 && AutomatedReverseFireTestTime >= 2.15f)
    {
        UE_LOG(LogTemp, Error,
            TEXT("CF_REVERSE_FIRE_TEST FAIL could not establish leftward run (velocity X %.3f)"),
            GetVelocity().X);
        bAutomatedReverseFireTest = false;
        FPlatformMisc::RequestExitWithStatus(false, 1);
    }
    else if (AutomatedReverseFireTestStage == 3 && AutomatedReverseFireTestTime >= 1.68f)
    {
        const bool bMirroredLayerAdvanced = AdditiveAnimation == FireBackAnimation && AdditiveTime > 0.07f;
        const bool bMirroredTravelPreserved = FacingDirection < 0.0f && GetVelocity().X < -30.0f;
        if (bMirroredLayerAdvanced && bMirroredTravelPreserved)
        {
            UE_LOG(LogTemp, Display,
                TEXT("CF_REVERSE_FIRE_TEST PASS both directions (left travel %.1f, right shot %.1f, layer time %.3f, velocity X %.3f)"),
                FacingDirection, ActiveFireDirection, AdditiveTime, GetVelocity().X);
            bAutomatedReverseFireTest = false;
            FPlatformMisc::RequestExitWithStatus(false, 0);
        }
        else
        {
            UE_LOG(LogTemp, Error,
                TEXT("CF_REVERSE_FIRE_TEST FAIL mirrored persistence (layer %.3f, travel %.1f, velocity X %.3f)"),
                AdditiveTime, FacingDirection, GetVelocity().X);
            bAutomatedReverseFireTest = false;
            FPlatformMisc::RequestExitWithStatus(false, 1);
        }
    }
}

void ACFPlayerCharacter::UpdateAutomatedLocomotionTransitionTest(float DeltaSeconds)
{
    AutomatedLocomotionTransitionTestTime += DeltaSeconds;
    // Let the generated map's initial floor-settle/landing finish before the
    // locomotion sample, otherwise the intentionally locked Land clip wins.
    if (AutomatedLocomotionTransitionTestTime >= 0.65f
        && AutomatedLocomotionTransitionTestTime < 1.18f)
    {
        MovementInputValue = 0.86f;
        FacingDirection = 1.0f;
        AddMovementInput(FVector::ForwardVector, MovementInputValue);
    }
    else
    {
        MovementInputValue = 0.0f;
    }

    if (AutomatedLocomotionTransitionTestStage == 0
        && AutomatedLocomotionTransitionTestTime >= 0.78f)
    {
        if (CurrentBaseAnimation != RunStartAnimation)
        {
            UE_LOG(LogTemp, Error,
                TEXT("CF_LOCOMOTION_TRANSITION_TEST FAIL start clip was not selected (velocity X %.3f)"),
                GetVelocity().X);
            bAutomatedLocomotionTransitionTest = false;
            FPlatformMisc::RequestExitWithStatus(false, 1);
            return;
        }
        FScreenshotRequest::RequestScreenshot(TEXT("CFAutomation_RunStart.png"), false, false);
        AutomatedLocomotionTransitionTestStage = 1;
    }
    else if (AutomatedLocomotionTransitionTestStage == 1
        && AutomatedLocomotionTransitionTestTime >= 1.04f)
    {
        if (CurrentBaseAnimation != RunAnimation)
        {
            UE_LOG(LogTemp, Error,
                TEXT("CF_LOCOMOTION_TRANSITION_TEST FAIL run loop was not reached (velocity X %.3f)"),
                GetVelocity().X);
            bAutomatedLocomotionTransitionTest = false;
            FPlatformMisc::RequestExitWithStatus(false, 1);
            return;
        }
        AutomatedLocomotionTransitionTestStage = 2;
    }
    else if (AutomatedLocomotionTransitionTestStage == 2
        && AutomatedLocomotionTransitionTestTime >= 1.28f)
    {
        if (CurrentBaseAnimation != RunStopAnimation)
        {
            UE_LOG(LogTemp, Error,
                TEXT("CF_LOCOMOTION_TRANSITION_TEST FAIL stop clip was not selected (velocity X %.3f)"),
                GetVelocity().X);
            bAutomatedLocomotionTransitionTest = false;
            FPlatformMisc::RequestExitWithStatus(false, 1);
            return;
        }
        FScreenshotRequest::RequestScreenshot(TEXT("CFAutomation_RunStop.png"), false, false);
        AutomatedLocomotionTransitionTestStage = 3;
    }
    else if (AutomatedLocomotionTransitionTestStage == 3
        && AutomatedLocomotionTransitionTestTime >= 1.64f)
    {
        const bool bSettled = CurrentBaseAnimation == IdleAnimation
            && FMath::Abs(GetVelocity().X) < 30.0f;
        if (!bSettled)
        {
            UE_LOG(LogTemp, Error,
                TEXT("CF_LOCOMOTION_TRANSITION_TEST FAIL did not settle to idle (velocity X %.3f)"),
                GetVelocity().X);
            bAutomatedLocomotionTransitionTest = false;
            FPlatformMisc::RequestExitWithStatus(false, 1);
            return;
        }
        UE_LOG(LogTemp, Display,
            TEXT("CF_LOCOMOTION_TRANSITION_TEST PASS start -> run -> stop -> idle"));
        bAutomatedLocomotionTransitionTest = false;
        FPlatformMisc::RequestExitWithStatus(false, 0);
    }
}

void ACFPlayerCharacter::UpdateAutomatedAnimationTest(float DeltaSeconds)
{
    AutomatedTestTime += DeltaSeconds;
    if (AutomatedTestTime >= 0.65f && AutomatedTestTime < 2.45f)
    {
        FacingDirection = 1.0f;
        AddMovementInput(FVector::ForwardVector, 0.72f);
    }
    else if (AutomatedTestTime >= 5.25f && AutomatedTestTime < 6.75f)
    {
        FacingDirection = -1.0f;
        AddMovementInput(FVector::ForwardVector, -0.72f);
    }

    if (AutomatedTestStage == 0 && AutomatedTestTime >= 1.25f)
    {
        FScreenshotRequest::RequestScreenshot(TEXT("CFAutomation_Run.png"), false, false);
        UE_LOG(LogTemp, Display, TEXT("CF_ANIMATION_TEST Run screenshot requested"));
        const USkeletalMeshComponent* CharacterVisual = GetMesh();
        const float VisualFacingX = CharacterVisual ? CharacterVisual->GetRightVector().X : 0.0f;
        bAutomatedDirectionTestPassed =
            FacingDirection > 0.0f && GetVelocity().X > 0.0f && VisualFacingX > 0.25f;
        if (!bAutomatedDirectionTestPassed)
        {
            UE_LOG(LogTemp, Error,
                TEXT("CF_ANIMATION_TEST right-facing check failed (facing %.1f, velocity X %.3f, visual facing X %.3f)"),
                FacingDirection, GetVelocity().X, VisualFacingX);
        }
        AutomatedTestStage = 1;
    }
    else if (AutomatedTestStage == 1 && AutomatedTestTime >= 1.65f)
    {
        FireInDirection(1.0f);
        AutomatedTestStage = 2;
    }
    else if (AutomatedTestStage == 2 && AutomatedTestTime >= 1.76f)
    {
        FScreenshotRequest::RequestScreenshot(TEXT("CFAutomation_FireLayer.png"), false, false);
        UE_LOG(LogTemp, Display, TEXT("CF_ANIMATION_TEST Fire layer screenshot requested"));
        AutomatedTestStage = 3;
    }
    else if (AutomatedTestStage == 3 && AutomatedTestTime >= 2.65f)
    {
        StartJump();
        AutomatedTestStage = 4;
    }
    else if (AutomatedTestStage == 4 && AutomatedTestTime >= 2.9f)
    {
        FScreenshotRequest::RequestScreenshot(TEXT("CFAutomation_JumpBlend.png"), false, false);
        UE_LOG(LogTemp, Display, TEXT("CF_ANIMATION_TEST Jump screenshot requested"));
        AutomatedTestStage = 5;
    }
    else if (AutomatedTestStage == 5 && AutomatedTestTime >= 3.75f)
    {
        ActivateShield();
        AutomatedTestStage = 6;
    }
    else if (AutomatedTestStage == 6 && AutomatedTestTime >= 4.02f)
    {
        FScreenshotRequest::RequestScreenshot(TEXT("CFAutomation_Shield.png"), false, false);
        UE_LOG(LogTemp, Display, TEXT("CF_ANIMATION_TEST Shield screenshot requested"));
        AutomatedTestStage = 7;
    }
    else if (AutomatedTestStage == 7 && AutomatedTestTime >= 6.05f)
    {
        FScreenshotRequest::RequestScreenshot(TEXT("CFAutomation_RunLeft.png"), false, false);
        UE_LOG(LogTemp, Display, TEXT("CF_ANIMATION_TEST Left run screenshot requested"));
        AutomatedTestStage = 8;
    }
    else if (AutomatedTestStage == 8 && AutomatedTestTime >= 6.75f)
    {
        const USkeletalMeshComponent* CharacterVisual = GetMesh();
        // FBX conversion maps the authored facial normal to component-local +Y,
        // hence GetRightVector() is the actual on-screen facing vector.
        const float VisualFacingX = CharacterVisual ? CharacterVisual->GetRightVector().X : 0.0f;
        if (bAutomatedDirectionTestPassed
            && FacingDirection < 0.0f && GetVelocity().X < 0.0f && VisualFacingX < -0.25f)
        {
            UE_LOG(LogTemp, Display,
                TEXT("CF_ANIMATION_TEST PASS (both directions verified, left visual facing X %.3f)"),
                VisualFacingX);
            bAutomatedAnimationTest = false;
            FPlatformMisc::RequestExitWithStatus(false, 0);
        }
        else
        {
            UE_LOG(LogTemp, Error,
                TEXT("CF_ANIMATION_TEST FAIL (right passed %d, left facing %.1f, velocity X %.3f, visual facing X %.3f)"),
                bAutomatedDirectionTestPassed, FacingDirection, GetVelocity().X, VisualFacingX);
            bAutomatedAnimationTest = false;
            FPlatformMisc::RequestExitWithStatus(false, 1);
        }
    }
}

UCFHeroAnimInstance* ACFPlayerCharacter::GetHeroAnimInstance() const
{
    return GetMesh() ? Cast<UCFHeroAnimInstance>(GetMesh()->GetAnimInstance()) : nullptr;
}

void ACFPlayerCharacter::SetBaseAnimation(UAnimSequence* Animation, bool bLooping, float PlayRate,
    float BlendDuration)
{
    if (!Animation)
    {
        return;
    }

    if (Animation == CurrentBaseAnimation)
    {
        CurrentBasePlayRate = PlayRate;
        bCurrentBaseLooping = bLooping;
        return;
    }

    PreviousBaseAnimation = CurrentBaseAnimation;
    PreviousBaseTime = CurrentBaseTime;
    PreviousBasePlayRate = CurrentBasePlayRate;
    bPreviousBaseLooping = bCurrentBaseLooping;
    CurrentBaseAnimation = Animation;
    CurrentBaseTime = 0.0f;
    CurrentBasePlayRate = PlayRate;
    bCurrentBaseLooping = bLooping;
    CurrentBaseTrack = 1 - CurrentBaseTrack;
    BaseBlendElapsed = 0.0f;
    BaseBlendDuration = PreviousBaseAnimation ? FMath::Max(0.01f, BlendDuration) : 0.0f;
}

void ACFPlayerCharacter::TriggerAdditiveAnimation(UAnimSequence* Animation, float Duration, float PlayRate)
{
    if (!Animation)
    {
        return;
    }
    AdditiveAnimation = Animation;
    AdditiveTime = 0.0f;
    AdditiveDuration = FMath::Max(0.01f, Duration);
    AdditivePlayRate = PlayRate;
}

void ACFPlayerCharacter::TriggerCharacterAnimation(UAnimSequence* Animation, float LockDuration, float PlayRate)
{
    if (!Animation)
    {
        return;
    }
    AnimationLockRemaining = LockDuration;
    SetBaseAnimation(Animation, false, PlayRate, 0.08f);
}

void ACFPlayerCharacter::UpdateAnimationGraph(float DeltaSeconds)
{
    UCFHeroAnimInstance* AnimInstance = GetHeroAnimInstance();
    if (!AnimInstance || !CurrentBaseAnimation)
    {
        return;
    }

    auto AdvanceTime = [DeltaSeconds](float& Time, UAnimSequence* Animation, float Rate, bool bLooping)
    {
        if (!Animation)
        {
            return;
        }
        const float Length = FMath::Max(Animation->GetPlayLength(), KINDA_SMALL_NUMBER);
        Time += DeltaSeconds * Rate;
        Time = bLooping ? FMath::Fmod(Time, Length) : FMath::Min(Time, Length);
    };

    AdvanceTime(CurrentBaseTime, CurrentBaseAnimation, CurrentBasePlayRate, bCurrentBaseLooping);
    AdvanceTime(PreviousBaseTime, PreviousBaseAnimation, PreviousBasePlayRate, bPreviousBaseLooping);
    BaseBlendElapsed += DeltaSeconds;
    const float BlendAlpha = BaseBlendDuration <= KINDA_SMALL_NUMBER
        ? 1.0f
        : FMath::Clamp(BaseBlendElapsed / BaseBlendDuration, 0.0f, 1.0f);

    AnimInstance->ResetNodes();
    const int32 PreviousTrack = 1 - CurrentBaseTrack;
    if (PreviousBaseAnimation && BlendAlpha < 1.0f)
    {
        AnimInstance->UpdateAnimTrack(PreviousBaseAnimation, PreviousTrack, PreviousBaseTime,
            1.0f - FMath::InterpEaseInOut(0.0f, 1.0f, BlendAlpha, 2.0f), false);
    }
    const float CurrentWeight = PreviousBaseAnimation
        ? FMath::InterpEaseInOut(0.0f, 1.0f, BlendAlpha, 2.0f)
        : 1.0f;
    AnimInstance->UpdateAnimTrack(CurrentBaseAnimation, CurrentBaseTrack, CurrentBaseTime, CurrentWeight, false);

    if (BlendAlpha >= 1.0f)
    {
        PreviousBaseAnimation = nullptr;
    }

    if (AdditiveAnimation)
    {
        AdditiveTime += DeltaSeconds * AdditivePlayRate;
        const float Remaining = AdditiveDuration - AdditiveTime;
        constexpr float BlendIn = 0.045f;
        constexpr float BlendOut = 0.075f;
        const float InWeight = FMath::Clamp(AdditiveTime / BlendIn, 0.0f, 1.0f);
        const float OutWeight = FMath::Clamp(Remaining / BlendOut, 0.0f, 1.0f);
        const float ActionWeight = FMath::Min(InWeight, OutWeight);
        if (Remaining > 0.0f)
        {
            const float SampleTime = FMath::Min(AdditiveTime, AdditiveAnimation->GetPlayLength());
            AnimInstance->UpdateAnimTrack(AdditiveAnimation, 2, SampleTime, ActionWeight, false);
        }
        else
        {
            AdditiveAnimation = nullptr;
            AdditiveTime = 0.0f;
        }
    }
}

bool ACFPlayerCharacter::SampleFootGround(const FName FootBone, FVector& OutOffset,
    FQuat& OutRotation) const
{
    const USkeletalMeshComponent* CharacterVisual = GetMesh();
    const UCapsuleComponent* Capsule = GetCapsuleComponent();
    const UWorld* World = GetWorld();
    if (!CharacterVisual || !Capsule || !World || !CharacterVisual->DoesSocketExist(FootBone))
    {
        return false;
    }

    const FVector FootWorldLocation = CharacterVisual->GetSocketLocation(FootBone);
    const float ActorHeight = GetActorLocation().Z;
    const FVector TraceStart(FootWorldLocation.X, FootWorldLocation.Y, ActorHeight + 52.0f);
    const FVector TraceEnd(FootWorldLocation.X, FootWorldLocation.Y, ActorHeight - 138.0f);
    FCollisionQueryParams QueryParams(SCENE_QUERY_STAT(CiberfantasmaFootIK), false, this);
    QueryParams.AddIgnoredActor(this);

    FHitResult GroundHit;
    if (!World->LineTraceSingleByChannel(GroundHit, TraceStart, TraceEnd,
        ECC_Visibility, QueryParams) || GroundHit.ImpactNormal.Z < 0.38f)
    {
        return false;
    }

    // CharacterMovement already places the capsule on the floor below its
    // centre. The difference beneath each ankle is therefore the terrain delta,
    // not a command to drag the animated swing foot back to the ground.
    const float CapsuleFloorZ = ActorHeight - Capsule->GetScaledCapsuleHalfHeight();
    const float SurfaceDelta = FMath::Clamp(GroundHit.ImpactPoint.Z - CapsuleFloorZ, -20.0f, 18.0f);
    const FVector WorldOffset(0.0f, 0.0f, SurfaceDelta);
    OutOffset = CharacterVisual->GetComponentTransform().InverseTransformVectorNoScale(WorldOffset);

    FVector ComponentNormal = CharacterVisual->GetComponentTransform()
        .InverseTransformVectorNoScale(GroundHit.ImpactNormal).GetSafeNormal();
    const float SlopeAngle = FMath::Acos(FMath::Clamp(
        FVector::DotProduct(ComponentNormal, FVector::UpVector), -1.0f, 1.0f));
    constexpr float MaxSlopeRadians = 32.0f * PI / 180.0f;
    if (SlopeAngle > MaxSlopeRadians)
    {
        ComponentNormal = FMath::Lerp(FVector::UpVector, ComponentNormal,
            MaxSlopeRadians / FMath::Max(SlopeAngle, KINDA_SMALL_NUMBER)).GetSafeNormal();
    }
    OutRotation = FQuat::FindBetweenNormals(FVector::UpVector, ComponentNormal).GetNormalized();
    return true;
}

void ACFPlayerCharacter::UpdateFootIK(const float DeltaSeconds)
{
    UCFHeroAnimInstance* AnimInstance = GetHeroAnimInstance();
    UCharacterMovementComponent* Movement = GetCharacterMovement();
    if (!AnimInstance || !Movement)
    {
        return;
    }

    FVector LeftTargetOffset = FVector::ZeroVector;
    FVector RightTargetOffset = FVector::ZeroVector;
    FQuat LeftTargetRotation = FQuat::Identity;
    FQuat RightTargetRotation = FQuat::Identity;
    const bool bCanGround = Movement->IsMovingOnGround();
    bLeftFootHasGround = bCanGround
        && SampleFootGround(TEXT("foot_l"), LeftTargetOffset, LeftTargetRotation);
    bRightFootHasGround = bCanGround
        && SampleFootGround(TEXT("foot_r"), RightTargetOffset, RightTargetRotation);

    if (!bLeftFootHasGround)
    {
        LeftTargetOffset = FVector::ZeroVector;
        LeftTargetRotation = FQuat::Identity;
    }
    if (!bRightFootHasGround)
    {
        RightTargetOffset = FVector::ZeroVector;
        RightTargetRotation = FQuat::Identity;
    }

    const float HorizontalSpeed = FMath::Abs(GetVelocity().X);
    float TargetAlpha = bCanGround && (bLeftFootHasGround || bRightFootHasGround) ? 1.0f : 0.0f;
    if (TargetAlpha > 0.0f && HorizontalSpeed > 35.0f)
    {
        // Keep the authored stride readable while still conforming to ramps and
        // platform seams. Crouch receives more weight because its centre is low.
        TargetAlpha = bIsCrouched ? 0.86f : 0.68f;
    }

    const float LeftHeight = bLeftFootHasGround ? LeftTargetOffset.Z : 0.0f;
    const float RightHeight = bRightFootHasGround ? RightTargetOffset.Z : 0.0f;
    const float TargetPelvisOffset = FMath::Clamp(
        FMath::Min(0.0f, FMath::Min(LeftHeight, RightHeight)), -15.0f, 0.0f);

    FootIKAlpha = FMath::FInterpTo(FootIKAlpha, TargetAlpha, DeltaSeconds, 12.0f);
    PelvisIKOffset = FMath::FInterpTo(PelvisIKOffset, TargetPelvisOffset, DeltaSeconds, 15.0f);
    LeftFootIKOffset = FMath::VInterpTo(LeftFootIKOffset, LeftTargetOffset, DeltaSeconds, 18.0f);
    RightFootIKOffset = FMath::VInterpTo(RightFootIKOffset, RightTargetOffset, DeltaSeconds, 18.0f);
    const float RotationAlpha = 1.0f - FMath::Exp(-16.0f * DeltaSeconds);
    LeftFootIKRotation = FQuat::Slerp(LeftFootIKRotation, LeftTargetRotation, RotationAlpha).GetNormalized();
    RightFootIKRotation = FQuat::Slerp(RightFootIKRotation, RightTargetRotation, RotationAlpha).GetNormalized();

    // Pelvis translation moves both feet already. Give each leg only its residual
    // correction so the solve cannot double the vertical displacement.
    const FVector PelvisTranslation(0.0f, 0.0f, PelvisIKOffset);
    AnimInstance->SetFootGrounding(FootIKAlpha, PelvisIKOffset,
        LeftFootIKOffset - PelvisTranslation, LeftFootIKRotation,
        RightFootIKOffset - PelvisTranslation, RightFootIKRotation);
}

void ACFPlayerCharacter::UpdateAutomatedFootIKTest(const float DeltaSeconds)
{
    AutomatedFootIKTestTime += DeltaSeconds;
    if (AutomatedFootIKTestTime < 1.05f)
    {
        return;
    }

    const bool bFinite = FMath::IsFinite(FootIKAlpha) && FMath::IsFinite(PelvisIKOffset)
        && !LeftFootIKOffset.ContainsNaN() && !RightFootIKOffset.ContainsNaN()
        && !LeftFootIKRotation.ContainsNaN() && !RightFootIKRotation.ContainsNaN();
    const bool bBounded = LeftFootIKOffset.Size() <= 24.0f
        && RightFootIKOffset.Size() <= 24.0f
        && PelvisIKOffset >= -15.1f && PelvisIKOffset <= 0.1f;
    const bool bPipelineActive = GetHeroAnimInstance() != nullptr
        && bLeftFootHasGround && bRightFootHasGround && FootIKAlpha >= 0.82f;
    if (bFinite && bBounded && bPipelineActive)
    {
        UE_LOG(LogTemp, Display,
            TEXT("CF_FOOT_IK_TEST PASS (alpha %.3f pelvis %.3f left %.3f right %.3f)"),
            FootIKAlpha, PelvisIKOffset, LeftFootIKOffset.Size(), RightFootIKOffset.Size());
        bAutomatedFootIKTest = false;
        FPlatformMisc::RequestExitWithStatus(false, 0);
    }
    else
    {
        UE_LOG(LogTemp, Error,
            TEXT("CF_FOOT_IK_TEST FAIL (finite %d bounded %d active %d contacts %d/%d alpha %.3f pelvis %.3f)"),
            bFinite, bBounded, bPipelineActive, bLeftFootHasGround, bRightFootHasGround,
            FootIKAlpha, PelvisIKOffset);
        bAutomatedFootIKTest = false;
        FPlatformMisc::RequestExitWithStatus(false, 1);
    }
}

void ACFPlayerCharacter::SetShieldPresentation(bool bActive)
{
    if (ShieldVisual)
    {
        ShieldVisual->SetVisibility(bActive, true);
    }
    if (ShieldInnerVisual) ShieldInnerVisual->SetVisibility(bActive, true);
    if (ShieldScanLine) ShieldScanLine->SetVisibility(bActive, true);
    for (UStaticMeshComponent* Frame : {ShieldFrameTop.Get(), ShieldFrameBottom.Get(),
        ShieldFrameLeft.Get(), ShieldFrameRight.Get()})
    {
        if (Frame) Frame->SetVisibility(bActive, true);
    }
    if (ShieldLight)
    {
        ShieldLight->SetIntensity(bActive ? 2600.0f : 0.0f);
    }
}

void ACFPlayerCharacter::UpdateCharacterPresentation(float DeltaSeconds)
{
    USkeletalMeshComponent* CharacterVisual = GetMesh();
    UCharacterMovementComponent* Movement = GetCharacterMovement();
    if (!CharacterVisual || !Movement)
    {
        return;
    }

    const FVector Velocity = GetVelocity();
    const float HorizontalSpeed = FMath::Abs(Velocity.X);
    const bool bGrounded = Movement->IsMovingOnGround();
    const bool bHasMoveIntent = FMath::Abs(MovementInputValue) > 0.08f
        || !GetPendingMovementInputVector().IsNearlyZero(0.08f)
        || !Movement->GetCurrentAcceleration().IsNearlyZero(8.0f);
    if (bGrounded && !bWasGrounded)
    {
        CameraLandingOffset = -24.0f;
        if (!IsShieldActive())
        {
            TriggerCharacterAnimation(LandAnimation, 0.26f, 1.0f);
        }
    }
    bWasGrounded = bGrounded;

    if (IsShieldActive())
    {
        GroundLocomotionPhase = EGroundLocomotionPhase::Idle;
        GroundLocomotionPhaseTime = 0.0f;
        SetBaseAnimation(ShieldAnimation, true, 1.0f, 0.1f);
    }
    else if (AnimationLockRemaining <= 0.0f)
    {
        if (!bGrounded)
        {
            GroundLocomotionPhase = EGroundLocomotionPhase::Idle;
            GroundLocomotionPhaseTime = 0.0f;
            SetBaseAnimation(Velocity.Z > 40.0f ? JumpRiseAnimation.Get() : JumpFallAnimation.Get(), true, 1.0f, 0.1f);
        }
        else if (bIsCrouched)
        {
            GroundLocomotionPhase = EGroundLocomotionPhase::Idle;
            GroundLocomotionPhaseTime = 0.0f;
            if (HorizontalSpeed > 20.0f)
            {
                const float CrouchSpeedRatio = FMath::Clamp(
                    HorizontalSpeed / FMath::Max(Movement->MaxWalkSpeedCrouched, 1.0f), 0.0f, 1.0f);
                SetBaseAnimation(CrouchWalkAnimation, true,
                    FMath::Lerp(0.78f, 1.24f, CrouchSpeedRatio), 0.11f);
            }
            else
            {
                SetBaseAnimation(CrouchAnimation, true, 1.0f, 0.14f);
            }
        }
        else
        {
            GroundLocomotionPhaseTime += DeltaSeconds;
            const float StartDuration = RunStartAnimation
                ? FMath::Max(0.12f, RunStartAnimation->GetPlayLength() * 0.92f)
                : 0.22f;
            const float StopDuration = RunStopAnimation
                ? FMath::Max(0.14f, RunStopAnimation->GetPlayLength() * 0.92f)
                : 0.26f;

            switch (GroundLocomotionPhase)
            {
            case EGroundLocomotionPhase::Idle:
                if (bHasMoveIntent || HorizontalSpeed > 30.0f)
                {
                    GroundLocomotionPhase = EGroundLocomotionPhase::Starting;
                    GroundLocomotionPhaseTime = 0.0f;
                }
                break;
            case EGroundLocomotionPhase::Starting:
                if (!bHasMoveIntent && HorizontalSpeed <= 30.0f)
                {
                    GroundLocomotionPhase = EGroundLocomotionPhase::Stopping;
                    GroundLocomotionPhaseTime = 0.0f;
                }
                else if (GroundLocomotionPhaseTime >= StartDuration)
                {
                    GroundLocomotionPhase = EGroundLocomotionPhase::Running;
                    GroundLocomotionPhaseTime = 0.0f;
                }
                break;
            case EGroundLocomotionPhase::Running:
                if (!bHasMoveIntent)
                {
                    GroundLocomotionPhase = EGroundLocomotionPhase::Stopping;
                    GroundLocomotionPhaseTime = 0.0f;
                }
                break;
            case EGroundLocomotionPhase::Stopping:
                if (bHasMoveIntent)
                {
                    GroundLocomotionPhase = EGroundLocomotionPhase::Starting;
                    GroundLocomotionPhaseTime = 0.0f;
                }
                else if (GroundLocomotionPhaseTime >= StopDuration)
                {
                    GroundLocomotionPhase = EGroundLocomotionPhase::Idle;
                    GroundLocomotionPhaseTime = 0.0f;
                }
                break;
            }

            const float SpeedRatio = FMath::Clamp(HorizontalSpeed / Movement->MaxWalkSpeed, 0.0f, 1.0f);
            switch (GroundLocomotionPhase)
            {
            case EGroundLocomotionPhase::Starting:
                SetBaseAnimation(RunStartAnimation ? RunStartAnimation.Get() : RunAnimation.Get(),
                    false, 1.0f, 0.10f);
                break;
            case EGroundLocomotionPhase::Running:
                SetBaseAnimation(RunAnimation, true,
                    FMath::Lerp(0.72f, 1.28f, SpeedRatio), 0.10f);
                break;
            case EGroundLocomotionPhase::Stopping:
                SetBaseAnimation(RunStopAnimation ? RunStopAnimation.Get() : IdleAnimation.Get(),
                    false, 1.0f, 0.08f);
                break;
            default:
                SetBaseAnimation(IdleAnimation, true, 1.0f, 0.14f);
                break;
            }
        }
    }
    else
    {
        GroundLocomotionPhase = EGroundLocomotionPhase::Idle;
        GroundLocomotionPhaseTime = 0.0f;
    }

    UpdateAnimationGraph(DeltaSeconds);

    const float SpeedRatio = FMath::Clamp(HorizontalSpeed / Movement->MaxWalkSpeed, 0.0f, 1.0f);
    const float GroundLean = -4.0f * SpeedRatio;
    const float AirLean = FMath::Clamp(-Velocity.Z / 180.0f, -7.0f, 7.0f);
    const float Lean = bGrounded ? GroundLean : AirLean;
    // Preserve the front-biased mask in idle, then rotate toward the stronger
    // three-quarter angle used by the Canvas run sheet.  The extra turn gives
    // the sagittal arm/leg motion enough screen-space separation to read.
    float PresentationYaw = FMath::Lerp(24.0f, 52.0f, SpeedRatio);
    if (!bGrounded)
    {
        PresentationYaw = 48.0f;
    }
    else if (bIsCrouched || IsShieldActive())
    {
        PresentationYaw = 30.0f;
    }
    else if (MuzzleFlashRemaining > 0.0f)
    {
        PresentationYaw = bLastShotContralateral ? 56.0f : 68.0f;
    }
    // FBX conversion leaves the facial normal on component-local +Y. Rotate that
    // axis toward travel; the previous sign made the mask look opposite to input.
    // A real rotation with positive scale also keeps gait handedness and tangents.
    const float DirectionalYaw = -FacingDirection * PresentationYaw;
    const FRotator DesiredVisualRotation(0.0f, DirectionalYaw, Lean);
    CharacterVisual->SetRelativeLocation(FVector(0.0f, 0.0f, -92.0f));
    // This is a real 3D turn, never a negative skeletal scale. Besides keeping
    // animation handedness intact it also preserves tangent space and lighting.
    CharacterVisual->SetRelativeScale3D(FVector(1.04f));
    CharacterVisual->SetRelativeRotation(FMath::RInterpTo(
        CharacterVisual->GetRelativeRotation(), DesiredVisualRotation, DeltaSeconds, 12.0f));
    UpdateFootIK(DeltaSeconds);

    CameraLandingOffset = FMath::FInterpTo(CameraLandingOffset, 0.0f, DeltaSeconds, 9.0f);
    const float HorizontalSpeedRatio = FMath::Clamp(
        FMath::Abs(Velocity.X) / FMath::Max(Movement->MaxWalkSpeed, 1.0f), 0.0f, 1.0f);
    const float DirectionalSpeed = FMath::Clamp(
        Velocity.X / FMath::Max(Movement->MaxWalkSpeed, 1.0f), -1.0f, 1.0f);
    const float AirborneZoom = Movement->IsMovingOnGround() ? 0.0f : 90.0f;
    const float DesiredArmLength = 1400.0f + HorizontalSpeedRatio * 80.0f + AirborneZoom;
    CameraBoom->TargetArmLength = FMath::FInterpTo(
        CameraBoom->TargetArmLength, DesiredArmLength, DeltaSeconds, 3.25f);

    const float LookAhead = DirectionalSpeed * 240.0f;
    const float VerticalLookAhead = FMath::Clamp(Velocity.Z * 0.14f, -75.0f, 115.0f);
    const FVector DesiredCameraOffset(
        LookAhead, 0.0f, 58.0f + VerticalLookAhead + CameraLandingOffset);
    CameraBoom->TargetOffset = FMath::VInterpTo(
        CameraBoom->TargetOffset, DesiredCameraOffset, DeltaSeconds, 4.25f);

    if (ShieldVisual && ShieldInnerVisual && ShieldScanLine && ShieldLight && IsShieldActive())
    {
        const float Pulse = 0.5f + 0.5f * FMath::Sin(GetWorld()->GetTimeSeconds() * 9.0f);
        const float ScanPhase = 0.5f + 0.5f * FMath::Sin(GetWorld()->GetTimeSeconds() * 3.4f);
        const float ShieldCenter = FacingDirection * 54.0f;
        const float ShieldWidth = 60.0f;
        const float ShieldCenterZ = 31.0f;
        const float ShieldHalfHeight = 63.0f;
        const float BreathingScale = 1.0f + Pulse * 0.014f;
        ShieldVisual->SetRelativeLocation(FVector(ShieldCenter, -18.0f, ShieldCenterZ));
        ShieldVisual->SetRelativeScale3D(FVector(0.60f, 0.045f, 1.26f) * BreathingScale);
        ShieldInnerVisual->SetRelativeLocation(FVector(ShieldCenter, -20.0f, ShieldCenterZ));
        ShieldInnerVisual->SetRelativeScale3D(FVector(0.54f, 0.055f, 1.08f) * BreathingScale);
        ShieldScanLine->SetRelativeLocation(FVector(
            ShieldCenter, -25.5f, ShieldCenterZ + FMath::Lerp(-46.0f, 46.0f, ScanPhase)));
        ShieldScanLine->SetRelativeScale3D(FVector(0.52f, 0.018f, 0.010f));
        ShieldFrameTop->SetRelativeLocation(FVector(ShieldCenter, -24.0f, ShieldCenterZ + ShieldHalfHeight));
        ShieldFrameBottom->SetRelativeLocation(FVector(ShieldCenter, -24.0f, ShieldCenterZ - ShieldHalfHeight));
        ShieldFrameLeft->SetRelativeLocation(FVector(ShieldCenter - ShieldWidth, -24.0f, ShieldCenterZ));
        ShieldFrameRight->SetRelativeLocation(FVector(ShieldCenter + ShieldWidth, -24.0f, ShieldCenterZ));
        const float FramePulse = 0.96f + Pulse * 0.07f;
        ShieldFrameTop->SetRelativeScale3D(FVector(0.62f, 0.025f, 0.020f) * FramePulse);
        ShieldFrameBottom->SetRelativeScale3D(FVector(0.62f, 0.025f, 0.020f) * FramePulse);
        ShieldFrameLeft->SetRelativeScale3D(FVector(0.020f, 0.025f, 1.26f) * FramePulse);
        ShieldFrameRight->SetRelativeScale3D(FVector(0.020f, 0.025f, 1.26f) * FramePulse);
        ShieldLight->SetRelativeLocation(FVector(ShieldCenter, -12.0f, ShieldCenterZ));
        ShieldLight->SetIntensity(1350.0f + 360.0f * Pulse);
    }
    if (MuzzleLight)
    {
        MuzzleLight->SetIntensity(MuzzleFlashRemaining > 0.0f ? 3200.0f : 0.0f);
    }
    if (MuzzleFlashVisual)
    {
        const bool bFlashVisible = MuzzleFlashRemaining > 0.0f;
        MuzzleFlashVisual->SetVisibility(bFlashVisible);
        if (bFlashVisible)
        {
            const float LifeAlpha = FMath::Clamp(MuzzleFlashRemaining / 0.14f, 0.0f, 1.0f);
            MuzzleFlashVisual->SetRelativeLocation(FVector(ActiveFireDirection * 88.0f, -24.0f, -28.0f));
            MuzzleFlashVisual->SetRelativeRotation(
                FRotator(ActiveFireDirection > 0.0f ? 90.0f : -90.0f, 0.0f, 0.0f));
            MuzzleFlashVisual->SetRelativeScale3D(
                FVector(0.11f, 0.11f, FMath::Lerp(0.30f, 0.52f, LifeAlpha)));
        }
    }
}

float ACFPlayerCharacter::TakeDamage(float DamageAmount, const FDamageEvent& DamageEvent,
    AController* EventInstigator, AActor* DamageCauser)
{
    if (DamageAmount <= 0.0f || DamageInvulnerabilityRemaining > 0.0f || !CanAct())
    {
        return 0.0f;
    }

    const float AppliedDamage = Super::TakeDamage(DamageAmount, DamageEvent, EventInstigator, DamageCauser);
    CurrentHealth = FMath::Max(0, CurrentHealth - FMath::Max(1, FMath::RoundToInt(DamageAmount)));
    DamageInvulnerabilityRemaining = 0.9f;
    TriggerCharacterAnimation(HitAnimation, 0.24f, 1.0f);
    OnHealthChanged(CurrentHealth, MaxHealth);
    if (CurrentHealth <= 0)
    {
        if (ACFGameState* State = GetWorld()->GetGameState<ACFGameState>()) State->PlayerDefeated();
    }
    else
    {
        ResetAtCheckpoint();
    }
    return AppliedDamage > 0.0f ? AppliedDamage : DamageAmount;
}

void ACFPlayerCharacter::ResetAtCheckpoint()
{
    GetCharacterMovement()->StopMovementImmediately();
    SetActorLocation(CheckpointLocation, false, nullptr, ETeleportType::TeleportPhysics);
}

void ACFPlayerCharacter::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
    Super::SetupPlayerInputComponent(PlayerInputComponent);

    PlayerInputComponent->BindAxis(TEXT("MoveRight"), this, &ACFPlayerCharacter::MoveRight);
    PlayerInputComponent->BindAction(TEXT("Jump"), IE_Pressed, this, &ACFPlayerCharacter::StartJump);
    PlayerInputComponent->BindAction(TEXT("Jump"), IE_Released, this, &ACFPlayerCharacter::StopJump);
    PlayerInputComponent->BindAction(TEXT("Crouch"), IE_Pressed, this, &ACFPlayerCharacter::StartCrouch);
    PlayerInputComponent->BindAction(TEXT("Crouch"), IE_Released, this, &ACFPlayerCharacter::StopCrouch);
    PlayerInputComponent->BindAction(TEXT("Fire"), IE_Pressed, this, &ACFPlayerCharacter::FirePulse);
    PlayerInputComponent->BindAction(TEXT("FireLeft"), IE_Pressed, this, &ACFPlayerCharacter::FireLeft);
    PlayerInputComponent->BindAction(TEXT("FireRight"), IE_Pressed, this, &ACFPlayerCharacter::FireRight);
    PlayerInputComponent->BindAction(TEXT("Shield"), IE_Pressed, this, &ACFPlayerCharacter::ActivateShield);
    FInputActionBinding& PauseBinding = PlayerInputComponent->BindAction(TEXT("Pause"), IE_Pressed, this, &ACFPlayerCharacter::TogglePause);
    PauseBinding.bExecuteWhenPaused = true;
    FInputActionBinding& RestartBinding = PlayerInputComponent->BindAction(TEXT("Restart"), IE_Pressed, this, &ACFPlayerCharacter::RestartLevel);
    RestartBinding.bExecuteWhenPaused = true;
    FInputActionBinding& CampaignBinding = PlayerInputComponent->BindAction(TEXT("RestartCampaign"), IE_Pressed, this, &ACFPlayerCharacter::RestartCampaign);
    CampaignBinding.bExecuteWhenPaused = true;
}

void ACFPlayerCharacter::MoveRight(float Value)
{
    MovementInputValue = Value;
    if (FMath::IsNearlyZero(Value) || IsShieldActive() || !CanAct())
    {
        return;
    }

    FacingDirection = FMath::Sign(Value);
    AddMovementInput(FVector::ForwardVector, Value);
}

void ACFPlayerCharacter::StartJump()
{
    if (!IsShieldActive() && CanAct())
    {
        TriggerCharacterAnimation(JumpStartAnimation, 0.19f, 1.0f);
        Jump();
    }
}

void ACFPlayerCharacter::StopJump()
{
    StopJumping();
}

void ACFPlayerCharacter::StartCrouch()
{
    if (!IsShieldActive() && CanAct())
    {
        Crouch();
    }
}

void ACFPlayerCharacter::StopCrouch()
{
    UnCrouch();
}

void ACFPlayerCharacter::FirePulse()
{
    FireInDirection(FacingDirection);
}

void ACFPlayerCharacter::FireLeft()
{
    FireInDirection(-1.0f);
}

void ACFPlayerCharacter::FireRight()
{
    FireInDirection(1.0f);
}

void ACFPlayerCharacter::FireInDirection(float Direction)
{
    if (FireCooldownRemaining > 0.0f || IsShieldActive() || ProjectileClass == nullptr || !CanAct())
    {
        return;
    }

    const float ShotDirection = FMath::Sign(Direction);
    const float HorizontalVelocity = GetVelocity().X;
    const bool bMovingHorizontally = FMath::Abs(HorizontalVelocity) > 30.0f;
    const float TravelDirection = bMovingHorizontally ? FMath::Sign(HorizontalVelocity) : FacingDirection;
    bLastShotContralateral = bMovingHorizontally && ShotDirection * TravelDirection < 0.0f;
    ActiveFireDirection = ShotDirection;
    // A reverse shot must not flip locomotion. When stationary, or firing along
    // travel, the shot still establishes the natural facing direction.
    if (!bLastShotContralateral)
    {
        FacingDirection = ShotDirection;
    }
    FireCooldownRemaining = FireCooldown;
    MuzzleFlashRemaining = 0.14f;
    TriggerAdditiveAnimation(bLastShotContralateral ? FireBackAnimation.Get() : FireAnimation.Get(),
        bLastShotContralateral ? 0.28f : 0.22f, 1.0f);
    // The capsule origin is at the character's mid-height; the authored wrist
    // emitter sits below it after the skeletal mesh's -92 cm presentation offset.
    const FVector SpawnLocation = GetActorLocation() + FVector(ShotDirection * 90.0f, 0.0f, -28.0f);
    const FRotator SpawnRotation(0.0f, ShotDirection > 0.0f ? 0.0f : 180.0f, 0.0f);
    if (MuzzleLight)
    {
        MuzzleLight->SetRelativeLocation(FVector(ShotDirection * 72.0f, -24.0f, -28.0f));
    }

    FActorSpawnParameters SpawnParameters;
    SpawnParameters.Owner = this;
    SpawnParameters.Instigator = this;
    SpawnParameters.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    GetWorld()->SpawnActor<ACFPulseProjectile>(ProjectileClass, SpawnLocation, SpawnRotation, SpawnParameters);
    // The authored muzzle core is attached to the character root and follows
    // every frame. A world-space burst visibly lagged behind while sprinting.
    OnPulseFired();
}

void ACFPlayerCharacter::ActivateShield()
{
    if (ShieldCooldownRemaining > 0.0f || IsShieldActive() || !CanAct())
    {
        return;
    }

    ShieldRemaining = ShieldDuration;
    ShieldCooldownRemaining = ShieldCooldown;
    AnimationLockRemaining = 0.0f;
    SetShieldPresentation(true);
    SetBaseAnimation(ShieldAnimation, true, 1.0f, 0.1f);
    OnShieldVisualChanged(true);
}

bool ACFPlayerCharacter::AbsorbProjectile(const FVector& ImpactLocation)
{
    if (!IsShieldActive()) return false;
    if (ShieldAbsorbSystem)
    {
        const FVector SpawnLocation = ImpactLocation.IsNearlyZero()
            ? GetActorLocation() + FVector(0.0f, 0.0f, 25.0f)
            : ImpactLocation;
        UNiagaraFunctionLibrary::SpawnSystemAtLocation(this, ShieldAbsorbSystem, SpawnLocation,
            FRotator::ZeroRotator, FVector(0.22f));
    }
    if (ACFGameState* State = GetWorld()->GetGameState<ACFGameState>())
    {
        if (UCFGameInstance* Instance = Cast<UCFGameInstance>(State->GetGameInstance())) Instance->AddBits(10);
    }
    return true;
}

float ACFPlayerCharacter::GetShieldReadyFraction() const
{
    return IsShieldActive() ? ShieldRemaining / ShieldDuration : 1.0f - ShieldCooldownRemaining / ShieldCooldown;
}

bool ACFPlayerCharacter::CanAct() const
{
    const ACFGameState* State = GetWorld() ? GetWorld()->GetGameState<ACFGameState>() : nullptr;
    return !State || State->CanPlayerAct();
}

void ACFPlayerCharacter::TogglePause()
{
    const bool bPaused = UGameplayStatics::IsGamePaused(this);
    UGameplayStatics::SetGamePaused(this, !bPaused);
}

void ACFPlayerCharacter::RestartLevel()
{
    if (ACFGameState* State = GetWorld()->GetGameState<ACFGameState>()) State->RestartCurrentLevel();
}

void ACFPlayerCharacter::RestartCampaign()
{
    if (ACFGameState* State = GetWorld()->GetGameState<ACFGameState>()) State->RestartCampaign();
}
